import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import glob
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://postgres:postgres@localhost:5432/job_market"

def create_table(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jobs_raw (
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
                created_date DATE,
                scraped_at TIMESTAMP,
                inserted_at TIMESTAMP DEFAULT NOW()
            );
        """))
        conn.commit()
    print("Table created or already exists.")

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
        "search_term", "created_date", "scraped_at"
    ]
    df_load = df[cols].copy()
    df_load["id"] = pd.to_numeric(df_load["id"], errors="coerce")
    df_load.dropna(subset=["id"], inplace=True)
    df_load["id"] = df_load["id"].astype(int)

    inserted = 0
    skipped = 0
    with engine.connect() as conn:
        for _, row in df_load.iterrows():
            try:
                conn.execute(text("""
                    INSERT INTO jobs_raw (
                        id, title, company, location, state,
                        description, salary_min, salary_max, salary_avg,
                        category, contract_type, seniority, is_remote,
                        search_term, created_date, scraped_at
                    ) VALUES (
                        :id, :title, :company, :location, :state,
                        :description, :salary_min, :salary_max, :salary_avg,
                        :category, :contract_type, :seniority, :is_remote,
                        :search_term, :created_date, :scraped_at
                    ) ON CONFLICT (id) DO NOTHING;
                """), row.to_dict())
                inserted += 1
            except Exception as e:
                skipped += 1
        conn.commit()

    print(f"Inserted: {inserted} | Skipped duplicates: {skipped}")

if __name__ == "__main__":
    engine = create_engine(DB_URL)
    create_table(engine)
    df = load_latest_staging()
    load_to_postgres(df, engine)
    print("\nDatabase load complete!")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM jobs_raw;"))
        count = result.scalar()
        print(f"Total jobs in database: {count}")