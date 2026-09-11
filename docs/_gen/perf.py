# -*- coding: utf-8 -*-
"""Measure real API response times against the full populated database."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app import create_app  # default config -> sqlite app.db (full dataset)

app = create_app()
c = app.test_client()

ENDPOINTS = [
    ("GET", "/api/postings?page=1&size=20", None),
    ("GET", "/api/postings?q=engineer&size=20", None),
    ("GET", "/api/postings/3884428798", None),  # may 404; replaced below
    ("GET", "/api/companies?size=20", None),
    ("GET", "/api/skills", None),
    ("GET", "/api/analytics/dashboard", None),
    ("GET", "/api/analytics/salary", None),
    ("GET", "/api/analytics/skills-matrix", None),
    ("POST", "/api/analytics/classify", {"title": "Senior Data Scientist"}),
    ("POST", "/api/skills/extract", {"text": "We need Python, SQL, Docker and AWS"}),
]

# pick a real job_id for the detail endpoint
with app.app_context():
    from app.models import Posting
    jid = app.test_client()  # noqa
    from app.extensions import db
    real_id = db.session.query(Posting.job_id).first()[0]
ENDPOINTS[2] = ("GET", f"/api/postings/{real_id}", None)


def bench(method, url, payload, runs=6):
    times = []
    status = None
    for _ in range(runs):
        t = time.perf_counter()
        if method == "GET":
            r = c.get(url)
        else:
            r = c.post(url, json=payload)
        times.append((time.perf_counter() - t) * 1000)
        status = r.status_code
    warm = times[1:]  # drop first (cold) run
    return {
        "endpoint": f"{method} {url}",
        "status": status,
        "cold_ms": round(times[0], 1),
        "avg_ms": round(sum(warm) / len(warm), 1),
        "min_ms": round(min(warm), 1),
        "max_ms": round(max(warm), 1),
    }


import os as _os
print("DB:", _os.environ.get("DATABASE_URL", "sqlite (default)"))
results = [bench(m, u, p) for (m, u, p) in ENDPOINTS]
print(f"{'Endpoint':<44}{'Status':>7}{'Cold(ms)':>10}{'Warm(ms)':>10}")
for r in results:
    ep = r["endpoint"] if len(r["endpoint"]) <= 42 else r["endpoint"][:41] + "..."
    print(f"{ep:<44}{r['status']:>7}{r['cold_ms']:>10}{r['avg_ms']:>10}")

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "figures", "perf.json"))
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("\nSaved", OUT)
