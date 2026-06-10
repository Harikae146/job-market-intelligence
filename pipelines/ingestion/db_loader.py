import pandas as pd
import glob
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = "postgresql://postgres:postgres@localhost:5432/job_market"

def create_table(engine):
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS jobs_raw;"))
        conn.execute(text("""
            CREATE TABLE jobs_raw (
                id BIGINT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                state VARCHAR(5),
                description TEXT,
                salary_min FLOAT,
                salary_max FLOAT,
                salary_avg FLOAT,
                category TEXT,
                contract_type TEXT,
                seniority VARCHAR(20),
                is_remote BOOLEAN,
                search_term TEXT,
                redirect_url TEXT,
                created_date DATE,
                scraped_at TIMESTAMP,
                inserted_at TIMESTAMP DEFAULT NOW()
            );
        """))
        conn.commit()
    print("Table created fresh with all columns.")

def load_latest_staging() -> pd.DataFrame:
    files = glob.glob("data/staging/jobs_clean_*.csv")
    if not files:
        raise FileNotFoundError("No staging files found.")
    latest = max(files, key=os.path.getctime)
    print(f"Loading: {latest}")
    return pd.read_csv(latest)

def load_to_postgres(df: pd.DataFrame, engine):
    cols = [
        "id", "title", "company", "location", "state",
        "description", "salary_min", "salary_max", "salary_avg",
        "category", "contract_type", "seniority", "is_remote",
        "search_term", "redirect_url", "created_date", "scraped_at"
    ]
    # Add missing columns with None
    for col in cols:
        if col not in df.columns:
            df[col] = None

    df_load = df[cols].copy()
    df_load["id"] = pd.to_numeric(df_load["id"], errors="coerce")
    df_load.dropna(subset=["id"], inplace=True)
    df_load["id"] = df_load["id"].astype(int)
    df_load["is_remote"] = df_load["is_remote"].fillna(False).astype(bool)

    inserted = 0
    with engine.connect() as conn:
        for _, row in df_load.iterrows():
            try:
                conn.execute(text("""
                    INSERT INTO jobs_raw (
                        id, title, company, location, state,
                        description, salary_min, salary_max, salary_avg,
                        category, contract_type, seniority, is_remote,
                        search_term, redirect_url, created_date, scraped_at
                    ) VALUES (
                        :id, :title, :company, :location, :state,
                        :description, :salary_min, :salary_max, :salary_avg,
                        :category, :contract_type, :seniority, :is_remote,
                        :search_term, :redirect_url, :created_date, :scraped_at
                    ) ON CONFLICT (id) DO NOTHING;
                """), row.to_dict())
                inserted += 1
            except Exception as e:
                print(f"Error: {e}")
        conn.commit()
    print(f"Inserted: {inserted} rows")

if __name__ == "__main__":
    engine = create_engine(DB_URL)
    create_table(engine)
    df = load_latest_staging()
    load_to_postgres(df, engine)

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM jobs_raw;")).scalar()
        cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='jobs_raw' ORDER BY ordinal_position;")).fetchall()
    print(f"\nTotal jobs: {count}")
    print(f"Columns: {[c[0] for c in cols]}")