import requests
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search"

SEARCH_TERMS = [
    "data engineer",
    "machine learning engineer",
    "data scientist",
    "data analyst",
    "AI engineer",
    "deep learning engineer"
]

def fetch_jobs(search_term: str, pages: int = 3) -> list:
    jobs = []
    for page in range(1, pages + 1):
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": 50,
            "what": search_term,
            "where": "United States",
            "content-type": "application/json"
        }
        try:
            response = requests.get(
                f"{BASE_URL}/{page}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            for job in results:
                jobs.append({
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "company": job.get("company", {}).get("display_name"),
                    "location": job.get("location", {}).get("display_name"),
                    "description": job.get("description"),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "category": job.get("category", {}).get("label"),
                    "contract_type": job.get("contract_type"),
                    "created": job.get("created"),
                    "redirect_url": job.get("redirect_url"),
                    "search_term": search_term,
                    "scraped_at": datetime.utcnow().isoformat()
                })
            print(f"  Fetched page {page} for '{search_term}' — {len(results)} jobs")
        except Exception as e:
            print(f"  Error on page {page} for '{search_term}': {e}")
    return jobs

def run_ingestion():
    all_jobs = []
    for term in SEARCH_TERMS:
        print(f"\nFetching: {term}")
        jobs = fetch_jobs(term, pages=3)
        all_jobs.extend(jobs)
        print(f"  Total so far: {len(all_jobs)}")

    df = pd.DataFrame(all_jobs)
    df.drop_duplicates(subset=["id"], inplace=True)

    os.makedirs("data/raw", exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/raw/jobs_{timestamp}.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} unique jobs to {output_path}")
    return df

if __name__ == "__main__":
    df = run_ingestion()
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"Columns: {list(df.columns)}")