from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib

app = FastAPI(
    title="FinRisk ML API",
    version="1.0"
)

model = joblib.load("models/risk_model.joblib")


class LoanApplication(BaseModel):
    loan_amnt: float
    int_rate: float
    installment: float
    annual_inc: float
    grade: str
    home_ownership: str
    term: str


@app.get("/")
def home():
    return {
        "message": "FinRisk ML API running"
    }


@app.post("/predict")
def predict_risk(data: LoanApplication):

    input_df = pd.DataFrame([{
        "loan_amnt": data.loan_amnt,
        "int_rate": data.int_rate,
        "installment": data.installment,
        "annual_inc": data.annual_inc,
        "grade": data.grade,
        "home_ownership": data.home_ownership,
        "term": data.term
    }])

    probability = model.predict_proba(input_df)[0][1]

    risk_score = round(probability * 100, 2)

    if risk_score < 20:
        segment = "Low Risk"
    elif risk_score < 50:
        segment = "Medium Risk"
    else:
        segment = "High Risk"

    return {
        "default_probability": round(probability, 4),
        "risk_score": risk_score,
        "risk_segment": segment
    }
