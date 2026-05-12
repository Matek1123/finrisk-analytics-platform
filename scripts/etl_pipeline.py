import pandas as pd
from sqlalchemy import create_engine

# Ścieżka do CSV
CSV_PATH = "data/raw/accepted_2007_to_2018Q4.csv"

# Ładujemy tylko część danych na start
print("Loading CSV...")

df = pd.read_csv(
    CSV_PATH,
    nrows=500000,
    low_memory=False
)

print("Rows loaded:", len(df))

# Czyszczenie kolumn
df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]

# Wybór najważniejszych kolumn
selected_columns = [
    'loan_amnt',
    'term',
    'int_rate',
    'installment',
    'grade',
    'emp_length',
    'home_ownership',
    'annual_inc',
    'loan_status'
]

df = df[selected_columns]

# Czyszczenie interest rate
df['int_rate'] = (
    df['int_rate']
    .astype(str)
    .str.replace('%', '', regex=False)
    .astype(float)
)

print(df.head())

# Połączenie PostgreSQL
engine = create_engine(
    "postgresql+psycopg2://admin:admin@localhost:5432/finrisk"
)

# Ładowanie do PostgreSQL
print("Loading to PostgreSQL...")

df.to_sql(
    "fact_loans",
    engine,
    if_exists="replace",
    index=False
)

print("DONE")
