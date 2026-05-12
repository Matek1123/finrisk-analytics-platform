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

    df = df.dropna(
        subset=["loan_amnt", "int_rate", "annual_inc", "loan_status"]
    )

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


def safe_load_table(table_name):
    try:
        return load_table(table_name)
    except Exception:
        return pd.DataFrame()


loans = safe_load_table("fact_loans")
risk_scores = safe_load_table("loan_risk_scores")

st.title("FinRisk Analytics Platform")
st.markdown("Advanced credit risk, portfolio monitoring and ML scoring dashboard")

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

if loans.empty:
    st.warning("No loan data found. Upload a CSV file or run the ETL pipeline.")
    st.stop()

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
col5.metric("Historical Risk Rate", f"{risk_rate:.2f}%")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Loan Status Distribution")
    status_df = filtered["loan_status"].value_counts().reset_index()
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

    risk_grade = (
        filtered.assign(
            is_risky=filtered["loan_status"].isin(risky_statuses)
        )
        .groupby("grade", as_index=False)
        .agg(
            loan_count=("loan_amnt", "count"),
            risky_loans=("is_risky", "sum")
        )
    )

    risk_grade["risk_rate"] = (
        risk_grade["risky_loans"] / risk_grade["loan_count"] * 100
    )

    fig_risk_rate = px.bar(
        risk_grade,
        x="grade",
        y="risk_rate",
        title="Historical Risk Rate by Grade",
        text_auto=".2f"
    )

    st.plotly_chart(fig_risk_rate, width="stretch")

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
    segment_risk["risky_loans"] / segment_risk["loan_count"] * 100
)

segment_risk = segment_risk.sort_values(
    ["risk_rate", "total_exposure"],
    ascending=False
)

st.dataframe(segment_risk.head(20), width="stretch")

st.subheader("Loan Amount Distribution")

fig_box = px.box(
    filtered,
    x="grade",
    y="loan_amnt",
    title="Loan Amount Distribution by Grade"
)

st.plotly_chart(fig_box, width="stretch")

st.divider()
st.header("ML Credit Risk Scoring")

if risk_scores.empty:
    st.warning(
        "No ML risk scores found. Run: python scripts/score_loans.py"
    )
else:
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Average Risk Score",
        f"{risk_scores['risk_score'].mean():.2f}"
    )

    col2.metric(
        "High Risk Loans",
        f"{(risk_scores['risk_segment'] == 'High Risk').sum():,}"
    )

    col3.metric(
        "Average Default Probability",
        f"{risk_scores['default_probability'].mean() * 100:.2f}%"
    )

    risk_segment_counts = (
        risk_scores["risk_segment"]
        .value_counts()
        .reset_index()
    )

    risk_segment_counts.columns = ["risk_segment", "loan_count"]

    fig_segments = px.bar(
        risk_segment_counts,
        x="risk_segment",
        y="loan_count",
        title="ML Risk Segment Distribution",
        text_auto=True
    )

    st.plotly_chart(fig_segments, width="stretch")

    fig_score_dist = px.histogram(
        risk_scores,
        x="risk_score",
        nbins=50,
        title="ML Risk Score Distribution"
    )

    st.plotly_chart(fig_score_dist, width="stretch")

    st.subheader("Risk Score Data Preview")
    st.dataframe(risk_scores.head(100), width="stretch")

st.subheader("Loan Data Preview")
st.dataframe(filtered.head(100), width="stretch")
