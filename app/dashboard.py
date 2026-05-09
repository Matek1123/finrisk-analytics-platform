import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

st.set_page_config(page_title="FinRisk Analytics Platform", layout="wide")

engine = create_engine("postgresql+psycopg2://admin:admin@localhost:5432/finrisk")

@st.cache_data
def load_data():
    return pd.read_sql("SELECT * FROM fact_loans", engine)

df = load_data()

st.sidebar.header("Filters")

selected_grade = st.sidebar.multiselect(
    "Loan Grade",
    options=sorted(df["grade"].dropna().unique()),
    default=sorted(df["grade"].dropna().unique())
)

selected_status = st.sidebar.multiselect(
    "Loan Status",
    options=sorted(df["loan_status"].dropna().unique()),
    default=sorted(df["loan_status"].dropna().unique())
)

df = df[
    (df["grade"].isin(selected_grade)) &
    (df["loan_status"].isin(selected_status))
]

st.title("FinRisk Analytics Platform")
st.markdown("Financial Risk & Loan Portfolio Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Loans", f"{len(df):,}")
col2.metric("Avg Interest Rate", f"{df['int_rate'].mean():.2f}%")
col3.metric("Total Loan Amount", f"${df['loan_amnt'].sum():,.0f}")
col4.metric("Avg Annual Income", f"${df['annual_inc'].mean():,.0f}")

st.subheader("Loan Status Distribution")
status_counts = df["loan_status"].value_counts().reset_index()
status_counts.columns = ["loan_status", "count"]
fig_status = px.bar(status_counts, x="loan_status", y="count")
st.plotly_chart(fig_status, width="stretch")

st.subheader("Average Interest Rate by Grade")
grade_rate = df.groupby("grade", as_index=False)["int_rate"].mean()
fig_grade = px.bar(grade_rate, x="grade", y="int_rate")
st.plotly_chart(fig_grade, width="stretch")

st.subheader("Risk Profile by Grade")
risk_df = df.groupby("grade", as_index=False).agg(
    avg_loan_amount=("loan_amnt", "mean"),
    avg_interest_rate=("int_rate", "mean"),
    avg_income=("annual_inc", "mean"),
    loan_count=("loan_amnt", "count")
)

fig_risk = px.scatter(
    risk_df,
    x="avg_income",
    y="avg_interest_rate",
    size="avg_loan_amount",
    color="grade",
    hover_data=["loan_count"],
    title="Risk Profile: Income vs Interest Rate"
)
st.plotly_chart(fig_risk, width="stretch")

st.subheader("Loan Amount by Home Ownership")
fig_home = px.box(df, x="home_ownership", y="loan_amnt")
st.plotly_chart(fig_home, width="stretch")

st.subheader("Raw Data Preview")
st.dataframe(df.head(100), width="stretch")
