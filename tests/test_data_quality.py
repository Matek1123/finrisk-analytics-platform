import pandas as pd
from sqlalchemy import create_engine

DB_URL = "postgresql+psycopg2://admin:admin@localhost:5432/finrisk"
engine = create_engine(DB_URL)


def test_fact_loans_not_empty():
    df = pd.read_sql("SELECT COUNT(*) AS row_count FROM fact_loans", engine)
    assert df["row_count"].iloc[0] > 0


def test_loan_amount_positive():
    df = pd.read_sql(
        "SELECT COUNT(*) AS invalid_count FROM fact_loans WHERE loan_amnt <= 0",
        engine
    )
    assert df["invalid_count"].iloc[0] == 0


def test_interest_rate_positive():
    df = pd.read_sql(
        "SELECT COUNT(*) AS invalid_count FROM fact_loans WHERE int_rate <= 0",
        engine
    )
    assert df["invalid_count"].iloc[0] == 0


def test_risk_scores_exist():
    df = pd.read_sql(
        "SELECT COUNT(*) AS row_count FROM loan_risk_scores",
        engine
    )
    assert df["row_count"].iloc[0] > 0
