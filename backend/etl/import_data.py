"""ETL pipeline: Kaggle CSV  ->  cleaned / normalised  ->  relational database.

Run from the ``backend`` directory::

    python -m etl.import_data            # load the full dataset
    python -m etl.import_data --limit 5000   # quick subset for development

The pipeline performs:
  * extraction of the five source tables (postings, companies, skills,
    job_skills, company_specialities) plus the employee-counts side table;
  * transformation - timestamp parsing, salary normalisation to an annual
    equivalent, boolean coercion, deduplication, weak-label job categorisation;
  * loading - batched ``bulk_insert_mappings`` for throughput;
  * training and persistence of the TF-IDF + Logistic-Regression job classifier;
  * seeding of default application users.
"""
from __future__ import annotations
import argparse
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.models import Company, CompanySpeciality, JobSkill, Posting, Skill, User
from app.services.classifier import JobClassifier, rule_label
#data cleaning
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PERIOD_TO_ANNUAL = {
    "HOURLY": 2080, "WEEKLY": 52, "BIWEEKLY": 26,
    "MONTHLY": 12, "YEARLY": 1, "ONCE": 1,
}


# Plausible annual-salary band; values outside are treated as data errors
# (the raw dataset contains placeholders like $1 and corrupt values >$5x10^8).
SALARY_MIN, SALARY_MAX = 10_000, 500_000


def _clean_salary(annual: float | None) -> float | None:
    if annual is None:
        return None
    return annual if SALARY_MIN <= annual <= SALARY_MAX else None


def _annualise(row) -> float | None:
    val = row.get("normalized_salary")
    if pd.notna(val) and val and val > 0:
        return _clean_salary(float(val))
    period = str(row.get("pay_period") or "YEARLY").upper()
    factor = PERIOD_TO_ANNUAL.get(period, 1)
    for col in ("med_salary", "max_salary", "min_salary"):
        v = row.get(col)
        if pd.notna(v) and v and v > 0:
            return _clean_salary(float(v) * factor)
    return None


def _to_dt(epoch_ms) -> datetime | None:
    if pd.isna(epoch_ms) or not epoch_ms:
        return None
    try:
        return datetime.utcfromtimestamp(float(epoch_ms) / 1000.0)
    except (ValueError, OverflowError, OSError):
        return None


def _speedups():
    if db.engine.dialect.name == "sqlite":
        db.session.execute(db.text("PRAGMA journal_mode=MEMORY"))
        db.session.execute(db.text("PRAGMA synchronous=OFF"))


def load_skills() -> int:
    df = pd.read_csv(os.path.join(RAW, "mappings", "skills.csv"))
    db.session.bulk_insert_mappings(Skill, [
        {"skill_abr": r.skill_abr, "skill_name": r.skill_name}
        for r in df.itertuples()
    ])
    db.session.commit()
    return len(df)


def load_companies() -> int:
    df = pd.read_csv(
        os.path.join(RAW, "companies", "companies.csv"),
        usecols=["company_id", "name", "description", "company_size",
                 "state", "country", "city", "address", "url"],
    )
    df = df.dropna(subset=["company_id"]).drop_duplicates(subset=["company_id"]) #把空值去掉  company ——id == null
    try:
        ec = pd.read_csv(os.path.join(RAW, "companies", "employee_counts.csv"))
        ec = ec.sort_values("time_recorded").drop_duplicates("company_id", keep="last")
        df = df.merge(ec[["company_id", "employee_count", "follower_count"]],
                      on="company_id", how="left")
    except FileNotFoundError:
        df["employee_count"] = None
        df["follower_count"] = None

    mappings = []
    for r in df.itertuples(): #Convert the data to the column names and corresponding formats required by MySQL.
        mappings.append({
            "company_id": int(r.company_id),
            "name": (str(r.name)[:255] if pd.notna(r.name) else None),
            "description": (str(r.description)[:4000] if pd.notna(r.description) else None),
            "company_size": (int(r.company_size) if pd.notna(r.company_size) else None),
            "state": (str(r.state)[:128] if pd.notna(r.state) else None),
            "country": (str(r.country)[:64] if pd.notna(r.country) else None),
            "city": (str(r.city)[:128] if pd.notna(r.city) else None),
            "address": (str(r.address)[:255] if pd.notna(r.address) else None),
            "url": (str(r.url)[:512] if pd.notna(r.url) else None),
            "employee_count": (int(r.employee_count) if pd.notna(r.employee_count) else None),
            "follower_count": (int(r.follower_count) if pd.notna(r.follower_count) else None),
        })
    for i in range(0, len(mappings), 5000):
        db.session.bulk_insert_mappings(Company, mappings[i:i + 5000])
        db.session.commit()
    return len(mappings)


def load_postings(limit: int | None) -> tuple[int, list[str]]:
    path = os.path.join(RAW, "postings.csv")
    cols = ["job_id", "company_id", "title", "description", "location",
            "min_salary", "med_salary", "max_salary", "normalized_salary",
            "pay_period", "currency", "formatted_work_type",
            "formatted_experience_level", "remote_allowed", "views", "applies",
            "listed_time"]
    valid_company_ids = {c[0] for c in db.session.query(Company.company_id).all()}
    titles: list[str] = []
    total = 0
    reader = pd.read_csv(path, usecols=cols, chunksize=20000)
    for chunk in reader:
        chunk = chunk.dropna(subset=["job_id"]).drop_duplicates(subset=["job_id"])
        mappings = []
        for r in chunk.itertuples(index=False):
            row = r._asdict()
            cid = row.get("company_id")
            cid = int(cid) if pd.notna(cid) and cid in valid_company_ids else None
            title = str(row["title"])[:512] if pd.notna(row["title"]) else None
            desc = str(row["description"])[:8000] if pd.notna(row["description"]) else None
            if title:
                titles.append(title)
            mappings.append({
                "job_id": int(row["job_id"]),
                "company_id": cid,
                "title": title,
                "description": desc,
                "location": str(row["location"])[:255] if pd.notna(row["location"]) else None,
                "min_salary": float(row["min_salary"]) if pd.notna(row["min_salary"]) else None,
                "med_salary": float(row["med_salary"]) if pd.notna(row["med_salary"]) else None,
                "max_salary": float(row["max_salary"]) if pd.notna(row["max_salary"]) else None,
                "normalized_salary": _annualise(row),
                "pay_period": str(row["pay_period"])[:32] if pd.notna(row["pay_period"]) else None,
                "currency": str(row["currency"])[:8] if pd.notna(row["currency"]) else None,
                "formatted_work_type": str(row["formatted_work_type"])[:64] if pd.notna(row["formatted_work_type"]) else None,
                "formatted_experience_level": str(row["formatted_experience_level"])[:64] if pd.notna(row["formatted_experience_level"]) else None,
                "remote_allowed": bool(row["remote_allowed"]) if pd.notna(row["remote_allowed"]) else False,
                "views": int(row["views"]) if pd.notna(row["views"]) else None,
                "applies": int(row["applies"]) if pd.notna(row["applies"]) else None,
                "listed_time": _to_dt(row["listed_time"]),
                "job_category": rule_label(title, desc),
            })
            total += 1
            if limit and total >= limit:
                break
        db.session.bulk_insert_mappings(Posting, mappings)
        db.session.commit()
        print(f"  ... postings loaded: {total}")
        if limit and total >= limit:
            break
    return total, titles


def load_job_skills() -> int:
    df = pd.read_csv(os.path.join(RAW, "jobs", "job_skills.csv"))
    valid_jobs = {j[0] for j in db.session.query(Posting.job_id).all()}
    valid_skills = {s[0] for s in db.session.query(Skill.skill_abr).all()}
    seen = set()
    mappings = []
    for r in df.itertuples():
        key = (r.job_id, r.skill_abr)
        if r.job_id in valid_jobs and r.skill_abr in valid_skills and key not in seen:
            seen.add(key)
            mappings.append({"job_id": int(r.job_id), "skill_abr": str(r.skill_abr)})
    for i in range(0, len(mappings), 5000):
        db.session.bulk_insert_mappings(JobSkill, mappings[i:i + 5000])
        db.session.commit()
    return len(mappings)


def load_specialities() -> int:
    path = os.path.join(RAW, "companies", "company_specialities.csv")
    df = pd.read_csv(path)
    valid = {c[0] for c in db.session.query(Company.company_id).all()}
    mappings = [
        {"company_id": int(r.company_id), "speciality": str(r.speciality)[:255]}
        for r in df.itertuples()
        if pd.notna(r.company_id) and r.company_id in valid and pd.notna(r.speciality)
    ]
    for i in range(0, len(mappings), 5000):
        db.session.bulk_insert_mappings(CompanySpeciality, mappings[i:i + 5000])
        db.session.commit()
    return len(mappings)


def train_classifier(titles: list[str]) -> dict:
    if not titles:
        return {}
    clf = JobClassifier()
    sample = titles if len(titles) <= 60000 else list(np.random.choice(titles, 60000, replace=False))
    clf.train(sample)
    clf.save()
    # quick holdout accuracy on weak labels
    from sklearn.model_selection import cross_val_score
    labels = [rule_label(t) for t in sample[:8000]]
    try:
        scores = cross_val_score(clf._pipeline, sample[:8000], labels, cv=3)
        acc = float(scores.mean())
    except Exception:
        acc = None
    return {"trained_on": len(sample), "cv_accuracy": acc}


def seed_users():
    if User.query.filter_by(username="admin").first():
        return
    admin = User(username="admin", role="admin")
    admin.set_password("admin123")
    demo = User(username="demo", role="user")
    demo.set_password("demo123")
    db.session.add_all([admin, demo])
    db.session.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--reset", action="store_true", help="drop & recreate tables")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.reset:
            db.drop_all()
        db.create_all()
        _speedups()
        if db.session.query(Posting).count() > 0:
            print("Database already populated. Use --reset to rebuild.")
            return
        print("[1/6] skills ...");        ns = load_skills()
        print("[2/6] companies ...");     nc = load_companies()
        print("[3/6] postings ...");      np_, titles = load_postings(args.limit)
        print("[4/6] job_skills ...");    njs = load_job_skills()
        print("[5/6] specialities ...");  nsp = load_specialities()
        print("[6/6] classifier + users ...")
        metrics = train_classifier(titles)
        seed_users()
        print("\n=== ETL complete ===")
        print(f"skills={ns} companies={nc} postings={np_} job_skills={njs} specialities={nsp}")
        print(f"classifier={metrics}")


if __name__ == "__main__":
    main()
