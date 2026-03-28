"""
main.py

Beginner-friendly automation script.

Run this (from the job_automation folder):
    python main.py

What it does:
1) Scrapes UI/UX/Product Design jobs from RemoteOK
2) Saves them into jobs.csv
3) Generates a personalized cover letter for each job using OpenAI
4) Updates the same jobs.csv with the cover letters

This file is intentionally simple so a non-developer can run it.
"""

from __future__ import annotations

import os
from typing import List, Dict

import pandas as pd

from scraper import scrape_jobs
from cover_letter_generator import generate_cover_letter


CSV_PATH = os.path.join(os.path.dirname(__file__), "jobs.csv")


def save_jobs_to_csv(jobs: List[Dict[str, str]], csv_path: str) -> None:
    """
    Save jobs to CSV using the required columns.

    If jobs is empty, we still create an empty CSV with the right headers.
    """
    columns = ["company", "role", "location", "description", "apply_link", "cover_letter"]
    df = pd.DataFrame(jobs, columns=columns)
    # utf-8-sig makes the CSV open more cleanly in Excel on Windows.
    try:
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"[main] Saved {len(df)} jobs to {csv_path}")
    except PermissionError:
        # If jobs.csv is open in Excel, fall back to a timestamped file.
        folder = os.path.dirname(csv_path)
        alt_path = os.path.join(folder, f"jobs_{int(__import__('time').time())}.csv")
        df.to_csv(alt_path, index=False, encoding="utf-8-sig")
        print(
            "[main] Could not overwrite jobs.csv (it is probably open in Excel). "
            f"Saved results instead as {os.path.basename(alt_path)}"
        )


def load_jobs_from_csv(csv_path: str) -> pd.DataFrame:
    """
    Load jobs from CSV. If the file doesn't exist yet, return an empty DataFrame.
    """
    if not os.path.exists(csv_path):
        return pd.DataFrame(columns=["company", "role", "location", "description", "apply_link", "cover_letter"])
    return pd.read_csv(csv_path, keep_default_na=False)  # keep_default_na=False keeps empty strings as empty strings


def generate_cover_letters_and_update_csv(csv_path: str) -> None:
    """
    For each row in jobs.csv, generate a cover letter if it doesn't already exist,
    then write the updated CSV back to disk.
    """
    df = load_jobs_from_csv(csv_path)
    if df.empty:
        print("[main] No jobs found in CSV. Nothing to generate.")
        return

    updated = 0

    for i in range(len(df)):
        company = str(df.at[i, "company"]).strip()
        role = str(df.at[i, "role"]).strip()
        description = str(df.at[i, "description"]).strip()
        existing = str(df.at[i, "cover_letter"]).strip()

        # Skip generation if we already have a letter for this job.
        if existing:
            continue

        # If required data is missing, skip gracefully.
        if not company or not role or not description:
            print(f"[main] Skipping row {i}: missing company/role/description.")
            continue

        print(f"[main] Generating cover letter ({i + 1}/{len(df)}) for {company} — {role} ...")
        letter = generate_cover_letter(company=company, role=role, description=description)

        # If the API fails (letter == ""), keep going without crashing.
        df.at[i, "cover_letter"] = letter
        updated += 1 if letter else 0

    try:
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"[main] Done. Added {updated} cover letters. Updated file: {csv_path}")
    except PermissionError:
        folder = os.path.dirname(csv_path)
        alt_path = os.path.join(folder, f"jobs_{int(__import__('time').time())}.csv")
        df.to_csv(alt_path, index=False, encoding="utf-8-sig")
        print(
            "[main] Could not update jobs.csv (it is probably open in Excel). "
            f"Saved updated results instead as {os.path.basename(alt_path)}"
        )


def main() -> None:
    # 1) Scrape jobs
    keywords = ["UX Designer", "Product Designer", "UI Designer"]

    # Keep this small for beginners (fast runs). You can increase this later.
    # Here we use:
    # - boards=None  -> defaults to RemoteOK
    # - experience_min=0 -> show all jobs (no filtering by years)
    jobs = scrape_jobs(
        keywords=keywords,
        max_jobs_per_keyword=10,
        location_filter="All",
        boards=None,
        experience_min=0,
    )

    # 2) Save jobs into jobs.csv
    save_jobs_to_csv(jobs, CSV_PATH)

    # 3) Generate cover letters and update the same CSV
    generate_cover_letters_and_update_csv(CSV_PATH)


if __name__ == "__main__":
    main()

