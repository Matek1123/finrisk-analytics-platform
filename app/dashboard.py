import pandas as pd
import os
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

st.set_page_config(
    page_title="FinRisk Analytics Platform",
    layout="wide"
)

DB_URL = "postgresql+psycopg2://admin:admin@localhost:5432/finrisk"
engine = create_engine(DB_URL)

def process_uploaded_file(uploaded_file):
    df = pd.read_csv(uploaded_file, low_memory=False)

    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]

    required_columns = [
        "loan_amnt",
        "term",
        "int_rate",
        "installment",
        "grade",
        "emp_length",
        "home_ownership",
        "annual_inc",
        "loan_status"
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        return None

    df = df[required_columns]

    df["int_rate"] = (
        df["int_rate"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .astype(float)
    )

    df["loan_amnt"] = pd.to_numeric(df["loan_amnt"], errors="coerce")
    df["installment"] = pd.to_numeric(df["installment"], errors="coerce")
    df["annual_inc"] = pd.to_numeric(df["annual_inc"], errors="coerce")

    df = df.dropna(subset=["loan_amnt", "int_rate", "annual_inc", "loan_status"])

    df.to_sql(
        "fact_loans",
        engine,
        if_exists="replace",
        index=False
    )

    st.cache_data.clear()

    return df

@st.cache_data
def load_table(table_name):
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)


loans = load_table("fact_loans")
kpis = load_table("mart_portfolio_kpis")
risk_by_grade = load_table("mart_risk_by_grade")
status_distribution = load_table("mart_status_distribution")

st.title("FinRisk Analytics Platform")
st.sidebar.header("Data Upload")

uploaded_file = st.sidebar.file_uploader(
    "Upload loan CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    with st.spinner("Processing uploaded file..."):
        uploaded_df = process_uploaded_file(uploaded_file)

    if uploaded_df is not None:
        st.sidebar.success(f"Uploaded {len(uploaded_df):,} rows to PostgreSQL")
        st.rerun()
st.markdown("Advanced credit risk and loan portfolio monitoring dashboard")

st.sidebar.header("Filters")

grades = sorted(loans["grade"].dropna().unique())
statuses = sorted(loans["loan_status"].dropna().unique())

selected_grades = st.sidebar.multiselect(
    "Loan Grade",
    options=grades,
    default=grades
)

selected_statuses = st.sidebar.multiselect(
    "Loan Status",
    options=statuses,
    default=statuses
)

filtered = loans[
    (loans["grade"].isin(selected_grades)) &
    (loans["loan_status"].isin(selected_statuses))
]

risky_statuses = [
    "Charged Off",
    "Default",
    "Late (31-120 days)",
    "Late (16-30 days)"
]

total_loans = len(filtered)
total_amount = filtered["loan_amnt"].sum()
avg_rate = filtered["int_rate"].mean()
avg_income = filtered["annual_inc"].mean()
risk_rate = (
    filtered["loan_status"].isin(risky_statuses).mean() * 100
    if total_loans > 0 else 0
)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Loans", f"{total_loans:,}")
col2.metric("Portfolio Exposure", f"${total_amount:,.0f}")
col3.metric("Avg Interest Rate", f"{avg_rate:.2f}%")
col4.metric("Avg Annual Income", f"${avg_income:,.0f}")
col5.metric("Risk Rate", f"{risk_rate:.2f}%")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Loan Status Distribution")
    status_df = (
        filtered["loan_status"]
        .value_counts()
        .reset_index()
    )
    status_df.columns = ["loan_status", "loan_count"]

    fig_status = px.bar(
        status_df,
        x="loan_status",
        y="loan_count",
        title="Loan Status Distribution",
        text_auto=True
    )

    st.plotly_chart(fig_status, width="stretch")

with right:
    st.subheader("Portfolio Exposure by Grade")
    exposure_df = (
        filtered.groupby("grade", as_index=False)["loan_amnt"]
        .sum()
        .sort_values("grade")
    )

    fig_exposure = px.bar(
        exposure_df,
        x="grade",
        y="loan_amnt",
        title="Total Loan Amount by Grade",
        text_auto=".2s"
    )

    st.plotly_chart(fig_exposure, width="stretch")

left, right = st.columns(2)

with left:
    st.subheader("Average Interest Rate by Grade")
    grade_rate = (
        filtered.groupby("grade", as_index=False)["int_rate"]
        .mean()
        .sort_values("grade")
    )

    fig_grade_rate = px.line(
        grade_rate,
        x="grade",
        y="int_rate",
        markers=True,
        title="Average Interest Rate by Grade"
    )

    st.plotly_chart(fig_grade_rate, width="stretch")

with right:
    st.subheader("Risk Rate by Grade")

    risk_grade_filtered = (
        filtered.assign(
            is_risky=filtered["loan_status"].isin(risky_statuses)
        )
        .groupby("grade", as_index=False)
        .agg(
            loan_count=("loan_amnt", "count"),
            risky_loans=("is_risky", "sum")
        )
    )

    risk_grade_filtered["risk_rate"] = (
        risk_grade_filtered["risky_loans"]
        / risk_grade_filtered["loan_count"]
        * 100
    )

    fig_risk_rate = px.bar(
        risk_grade_filtered,
        x="grade",
        y="risk_rate",
        title="Risk Rate by Grade",
        text_auto=".2f"
    )

    st.plotly_chart(fig_risk_rate, width="stretch")

st.subheader("Risk Profile: Income vs Interest Rate")

risk_profile = (
    filtered.groupby("grade", as_index=False)
    .agg(
        avg_income=("annual_inc", "mean"),
        avg_interest_rate=("int_rate", "mean"),
        avg_loan_amount=("loan_amnt", "mean"),
        loan_count=("loan_amnt", "count")
    )
)

fig_profile = px.scatter(
    risk_profile,
    x="avg_income",
    y="avg_interest_rate",
    size="avg_loan_amount",
    color="grade",
    hover_data=["loan_count"],
    title="Risk Profile by Loan Grade"
)

st.plotly_chart(fig_profile, width="stretch")

st.subheader("Top Risk Segments")

segment_risk = (
    filtered.assign(
        is_risky=filtered["loan_status"].isin(risky_statuses)
    )
    .groupby(["grade", "home_ownership"], as_index=False)
    .agg(
        loan_count=("loan_amnt", "count"),
        total_exposure=("loan_amnt", "sum"),
        avg_interest_rate=("int_rate", "mean"),
        risky_loans=("is_risky", "sum")
    )
)

segment_risk["risk_rate"] = (
    segment_risk["risky_loans"]
    / segment_risk["loan_count"]
    * 100
)

segment_risk = segment_risk.sort_values(
    ["risk_rate", "total_exposure"],
    ascending=False
)

st.dataframe(
    segment_risk.head(20),
    width="stretch"
)

st.subheader("Loan Amount Distribution")

fig_box = px.box(
    filtered,
    x="grade",
    y="loan_amnt",
    title="Loan Amount Distribution by Grade"
)

st.plotly_chart(fig_box, width="stretch")

st.subheader("Data Preview")

st.dataframe(
    filtered.head(100),
    width="stretch"
)
