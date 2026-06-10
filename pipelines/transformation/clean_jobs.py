import pandas as pd
import os
import glob
from datetime import datetime, timezone

def load_latest_raw() -> pd.DataFrame:
    files = glob.glob("data/raw/jobs_*.csv")
    if not files:
        raise FileNotFoundError("No raw job files found in data/raw/")
    latest = max(files, key=os.path.getctime)
    print(f"Loading: {latest}")
    return pd.read_csv(latest)

def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    print(f"Raw shape: {df.shape}")

    # Drop duplicates
    df.drop_duplicates(subset=["id"], inplace=True)

    # Clean title
    df["title"] = df["title"].str.strip().str.title()

    # Clean company
    df["company"] = df["company"].str.strip()

    # Extract state from location
    df["state"] = df["location"].str.extract(r",\s*([A-Z]{2})$")

    # Clean salary — fill missing with 0
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce").fillna(0)
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce").fillna(0)

    # Create salary_avg column
    df["salary_avg"] = df.apply(
        lambda r: (r["salary_min"] + r["salary_max"]) / 2
        if r["salary_min"] > 0 and r["salary_max"] > 0
        else 0,
        axis=1
    )

    # Flag remote jobs
    df["is_remote"] = df["title"].str.contains(
        "remote|hybrid", case=False, na=False
    ) | df["location"].str.contains(
        "remote|hybrid", case=False, na=False
    )

    # Classify seniority
    def get_seniority(title):
        title = str(title).lower()
        if any(w in title for w in ["senior", "sr.", "lead", "principal", "staff"]):
            return "senior"
        elif any(w in title for w in ["junior", "jr.", "entry", "associate"]):
            return "junior"
        elif any(w in title for w in ["manager", "director", "head", "vp", "chief"]):
            return "management"
        else:
            return "mid"

    df["seniority"] = df["title"].apply(get_seniority)

    # Parse created date
    df["created"] = pd.to_datetime(df["created"], errors="coerce")
    df["created_date"] = df["created"].dt.date

    # Drop rows with no title or company
    df.dropna(subset=["title", "company"], inplace=True)

    # Reset index
    df.reset_index(drop=True, inplace=True)

    print(f"Cleaned shape: {df.shape}")
    print(f"Seniority breakdown:\n{df['seniority'].value_counts()}")
    print(f"Remote jobs: {df['is_remote'].sum()}")
    print(f"Jobs with salary: {(df['salary_avg'] > 0).sum()}")

    return df

def save_staging(df: pd.DataFrame):
    os.makedirs("data/staging", exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = f"data/staging/jobs_clean_{timestamp}.csv"
    df.to_csv(path, index=False)
    print(f"\nSaved to staging: {path}")
    return path

if __name__ == "__main__":
    df_raw = load_latest_raw()
    df_clean = clean_jobs(df_raw)
    save_staging(df_clean)
    print("\nSample:")
    print(df_clean[["title", "company", "state", "seniority", "is_remote", "salary_avg"]].head(10))