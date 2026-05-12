from datetime import datetime
from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg2://admin:admin@localhost:5432/finrisk"
engine = create_engine(DB_URL)


def init_monitoring_table():
    sql = """
    CREATE TABLE IF NOT EXISTS pipeline_run_logs (
        id SERIAL PRIMARY KEY,
        pipeline_name TEXT,
        status TEXT,
        run_timestamp TIMESTAMP,
        message TEXT
    );
    """
    with engine.begin() as conn:
        conn.execute(text(sql))


def log_pipeline_run(pipeline_name, status, message):
    init_monitoring_table()

    sql = """
    INSERT INTO pipeline_run_logs (
        pipeline_name,
        status,
        run_timestamp,
        message
    )
    VALUES (
        :pipeline_name,
        :status,
        :run_timestamp,
        :message
    );
    """

    with engine.begin() as conn:
        conn.execute(
            text(sql),
            {
                "pipeline_name": pipeline_name,
                "status": status,
                "run_timestamp": datetime.now(),
                "message": message
            }
        )
