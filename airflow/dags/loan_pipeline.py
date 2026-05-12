from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import psycopg2

# Ścieżki w Dockerze (Airflow będzie miał dostęp dzięki volume)
DATA_RAW = "/opt/airflow/data/raw/accepted_2007_to_2018.csv"
DATA_PROCESSED = "/opt/airflow/data/processed/loans_transformed.csv"

def extract():
    df = pd.read_csv(DATA_RAW)
    df.to_csv(DATA_PROCESSED, index=False)
    print("Extracted data:", df.shape)

def transform():
    df = pd.read_csv(DATA_PROCESSED)
    df.columns = [c.lower() for c in df.columns]  # zmiana kolumn na małe litery
    df.to_csv(DATA_PROCESSED, index=False)
    print("Transformed data:", df.shape)

def load():
    df = pd.read_csv(DATA_PROCESSED)
    conn = psycopg2.connect(
        dbname="finrisk",
        user="admin",
        password="admin",
        host="host.docker.internal",  # dla lokalnego PostgreSQL z Dockera
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS fact_loans;")
    cur.execute("""
        CREATE TABLE fact_loans (
            id SERIAL PRIMARY KEY,
            loan_amnt NUMERIC,
            term TEXT,
            int_rate NUMERIC,
            installment NUMERIC,
            grade TEXT,
            emp_length TEXT,
            home_ownership TEXT,
            annual_inc NUMERIC,
            issue_d DATE,
            loan_status TEXT
        );
    """)
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO fact_loans (
                loan_amnt, term, int_rate, installment, grade, emp_length, home_ownership, annual_inc, issue_d, loan_status
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            row['loan_amnt'], row['term'], float(str(row['int_rate']).replace('%','')),
            row['installment'], row['grade'], row['emp_length'],
            row['home_ownership'], row['annual_inc'], row['issue_d'], row['loan_status']
        ))
    conn.commit()
    cur.close()
    conn.close()
    print("Loaded data into PostgreSQL")

with DAG(
    dag_id='loan_pipeline',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:

    extract_task = PythonOperator(task_id='extract', python_callable=extract)
    transform_task = PythonOperator(task_id='transform', python_callable=transform)
    load_task = PythonOperator(task_id='load', python_callable=load)

    extract_task >> transform_task >> load_task
