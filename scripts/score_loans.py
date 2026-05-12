import pandas as pd
import joblib
from scripts.pipeline_monitoring import log_pipeline_run
from sqlalchemy import create_engine

DB_URL = "postgresql+psycopg2://admin:admin@localhost:5432/finrisk"
MODEL_PATH = "models/risk_model.joblib"

engine = create_engine(DB_URL)

print("Loading model...")
model = joblib.load(MODEL_PATH)

print("Loading loans...")
df = pd.read_sql("SELECT * FROM fact_loans", engine)

features = [
    "loan_amnt",
    "int_rate",
    "installment",
    "annual_inc",
    "grade",
    "home_ownership",
    "term"
]

score_df = df[features].dropna().copy()

print("Scoring loans...")

score_df["default_probability"] = model.predict_proba(
    score_df[features]
)[:, 1]

score_df["risk_score"] = (
    score_df["default_probability"] * 100
).round(2)

score_df["risk_segment"] = pd.cut(
    score_df["risk_score"],
    bins=[-1, 20, 50, 100],
    labels=["Low Risk", "Medium Risk", "High Risk"]
)

print("Saving scores to PostgreSQL...")

score_df.to_sql(
    "loan_risk_scores",
    engine,
    if_exists="replace",
    index=False
)

print("Saved scores to loan_risk_scores")
print(score_df.head())
