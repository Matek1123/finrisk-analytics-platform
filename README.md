# FinRisk Analytics Platform

Financial risk analytics platform built with Python, PostgreSQL, Streamlit, FastAPI and machine learning.

## Business Problem

Fintech companies and lending institutions need to monitor loan portfolio risk, analyze borrower segments, and identify loans with higher probability of default.

This project simulates an end-to-end financial risk analytics platform using historical LendingClub loan data.

## Advanced Features

- End-to-end ETL pipeline
- PostgreSQL data warehouse
- Star schema data model
- Analytics marts
- Streamlit executive dashboard
- CSV upload and automatic analysis
- ML-based credit risk scoring
- FastAPI prediction endpoint
- Pipeline monitoring logs
- Data quality tests
- GitHub Actions CI
- Docker deployment

## Tech Stack

- Python
- Pandas
- PostgreSQL
- SQLAlchemy
- Streamlit
- Plotly
- Scikit-learn
- FastAPI
- Pytest
- Docker
- GitHub Actions

## Project Structure

```text
finrisk-analytics-platform/
│
├── app/
│   └── dashboard.py
│
├── api/
│   └── main.py
│
├── scripts/
│   ├── etl_pipeline.py
│   ├── build_warehouse.py
│   ├── train_risk_model.py
│   ├── score_loans.py
│   └── pipeline_monitoring.py
│
├── tests/
│   └── test_data_quality.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── requirements.txt
├── Dockerfile
├── docker-compose.prod.yml
├── README.md
└── .gitignore
