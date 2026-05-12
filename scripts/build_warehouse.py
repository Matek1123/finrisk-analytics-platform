import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg2://admin:admin@localhost:5432/finrisk"

engine = create_engine(DB_URL)


def run_sql(sql: str):
    with engine.begin() as conn:
        conn.execute(text(sql))


def main():
    print("Building warehouse layer...")

    sql = """
    DROP TABLE IF EXISTS mart_status_distribution;
    DROP TABLE IF EXISTS mart_risk_by_grade;
    DROP TABLE IF EXISTS mart_portfolio_kpis;

    DROP TABLE IF EXISTS fact_loans_warehouse;
    DROP TABLE IF EXISTS dim_grade;
    DROP TABLE IF EXISTS dim_home_ownership;
    DROP TABLE IF EXISTS dim_loan_status;

    CREATE TABLE dim_grade AS
    SELECT
        ROW_NUMBER() OVER (ORDER BY grade) AS grade_id,
        grade
    FROM (
        SELECT DISTINCT grade
        FROM fact_loans
        WHERE grade IS NOT NULL
    ) x;

    CREATE TABLE dim_home_ownership AS
    SELECT
        ROW_NUMBER() OVER (ORDER BY home_ownership) AS home_ownership_id,
        home_ownership
    FROM (
        SELECT DISTINCT home_ownership
        FROM fact_loans
        WHERE home_ownership IS NOT NULL
    ) x;

    CREATE TABLE dim_loan_status AS
    SELECT
        ROW_NUMBER() OVER (ORDER BY loan_status) AS loan_status_id,
        loan_status
    FROM (
        SELECT DISTINCT loan_status
        FROM fact_loans
        WHERE loan_status IS NOT NULL
    ) x;

    CREATE TABLE fact_loans_warehouse AS
    SELECT
        ROW_NUMBER() OVER () AS loan_id,
        f.loan_amnt,
        f.term,
        f.int_rate,
        f.installment,
        f.emp_length,
        f.annual_inc,
        g.grade_id,
        h.home_ownership_id,
        s.loan_status_id
    FROM fact_loans f
    LEFT JOIN dim_grade g
        ON f.grade = g.grade
    LEFT JOIN dim_home_ownership h
        ON f.home_ownership = h.home_ownership
    LEFT JOIN dim_loan_status s
        ON f.loan_status = s.loan_status;

    CREATE TABLE mart_portfolio_kpis AS
    SELECT
        COUNT(*) AS total_loans,
        SUM(loan_amnt) AS total_loan_amount,
        AVG(loan_amnt) AS avg_loan_amount,
        AVG(int_rate) AS avg_interest_rate,
        AVG(annual_inc) AS avg_annual_income
    FROM fact_loans;

    CREATE TABLE mart_status_distribution AS
    SELECT
        loan_status,
        COUNT(*) AS loan_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage_share
    FROM fact_loans
    GROUP BY loan_status
    ORDER BY loan_count DESC;

    CREATE TABLE mart_risk_by_grade AS
    SELECT
        grade,
        COUNT(*) AS loan_count,
        SUM(loan_amnt) AS total_exposure,
        AVG(loan_amnt) AS avg_loan_amount,
        AVG(int_rate) AS avg_interest_rate,
        AVG(annual_inc) AS avg_annual_income,
        SUM(
            CASE
                WHEN loan_status IN (
                    'Charged Off',
                    'Default',
                    'Late (31-120 days)',
                    'Late (16-30 days)'
                )
                THEN 1 ELSE 0
            END
        ) AS risky_loans,
        ROUND(
            SUM(
                CASE
                    WHEN loan_status IN (
                        'Charged Off',
                        'Default',
                        'Late (31-120 days)',
                        'Late (16-30 days)'
                    )
                    THEN 1 ELSE 0
                END
            ) * 100.0 / COUNT(*),
            2
        ) AS risk_rate
    FROM fact_loans
    GROUP BY grade
    ORDER BY grade;
    """

    run_sql(sql)

    print("Warehouse created successfully.")

    with engine.connect() as conn:
        tables = pd.read_sql(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """,
            conn
        )

    print(tables)


if __name__ == "__main__":
    main()
