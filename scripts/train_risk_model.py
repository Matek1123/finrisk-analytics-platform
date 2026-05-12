import pandas as pd
import joblib
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

DB_URL = "postgresql+psycopg2://admin:admin@localhost:5432/finrisk"
engine = create_engine(DB_URL)

print("Loading data...")

df = pd.read_sql("SELECT * FROM fact_loans", engine)

risky_statuses = [
    "Charged Off",
    "Default",
    "Late (31-120 days)",
    "Late (16-30 days)"
]

df["default_flag"] = df["loan_status"].isin(risky_statuses).astype(int)

features = [
    "loan_amnt",
    "int_rate",
    "installment",
    "annual_inc",
    "grade",
    "home_ownership",
    "term"
]

df = df[features + ["default_flag"]].dropna()

X = df[features]
y = df["default_flag"]

categorical_features = ["grade", "home_ownership", "term"]
numeric_features = ["loan_amnt", "int_rate", "installment", "annual_inc"]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ("num", "passthrough", numeric_features)
    ]
)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight="balanced"
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training model...")
pipeline.fit(X_train, y_train)

preds = pipeline.predict(X_test)
probs = pipeline.predict_proba(X_test)[:, 1]

print("Classification report:")
print(classification_report(y_test, preds))

print("ROC AUC:", roc_auc_score(y_test, probs))

joblib.dump(pipeline, "models/risk_model.joblib")

print("Model saved to models/risk_model.joblib")
