# -*- coding: utf-8 -*-
"""Query the populated SQLite database for real figures and render the
data-driven charts used in the Technical Report.  Read-only on app.db."""
import json
import os
import sqlite3
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.abspath(os.path.join(HERE, "..", "..", "backend", "data", "app.db"))
OUT = os.path.abspath(os.path.join(HERE, "..", "figures"))
os.makedirs(OUT, exist_ok=True)

PALETTE = ["#0a66c2", "#0e8a5f", "#b45309", "#7c3aed", "#be123c",
           "#0891b2", "#ca8a04", "#db2777", "#4338ca", "#15803d"]
plt.rcParams.update({
    "font.size": 11, "figure.dpi": 150,
    "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True,
    "savefig.bbox": "tight", "axes.edgecolor": "#888888",
})

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()


def one(sql, params=()):
    cur.execute(sql, params)
    r = cur.fetchone()
    return r[0] if r else None


def rows(sql, params=()):
    cur.execute(sql, params)
    return cur.fetchall()


stats = {}

# ---- headline counts -------------------------------------------------------
stats["postings"] = one("SELECT COUNT(*) FROM postings")
stats["companies"] = one("SELECT COUNT(*) FROM companies")
stats["skills"] = one("SELECT COUNT(*) FROM skills")
stats["job_skills"] = one("SELECT COUNT(*) FROM job_skills")
stats["specialities"] = one("SELECT COUNT(*) FROM company_specialities")
stats["users"] = one("SELECT COUNT(*) FROM users")
stats["remote"] = one("SELECT COUNT(*) FROM postings WHERE remote_allowed=1")
stats["with_salary"] = one("SELECT COUNT(*) FROM postings WHERE normalized_salary IS NOT NULL")
stats["with_company"] = one("SELECT COUNT(*) FROM postings WHERE company_id IS NOT NULL")
stats["with_desc"] = one("SELECT COUNT(*) FROM postings WHERE description IS NOT NULL AND description != ''")
stats["remote_ratio"] = round(stats["remote"] / stats["postings"], 4)
stats["salary_coverage"] = round(stats["with_salary"] / stats["postings"], 4)

# ---- salary stats ----------------------------------------------------------
sal = [r[0] for r in rows("SELECT normalized_salary FROM postings WHERE normalized_salary IS NOT NULL")]
sal_arr = np.array(sal, dtype=float)
stats["salary"] = {
    "n": int(sal_arr.size),
    "min": float(np.min(sal_arr)),
    "max": float(np.max(sal_arr)),
    "mean": float(np.mean(sal_arr)),
    "median": float(np.median(sal_arr)),
    "p25": float(np.percentile(sal_arr, 25)),
    "p75": float(np.percentile(sal_arr, 75)),
}
stats["avg_salary"] = round(stats["salary"]["mean"], 2)

# ---- breakdowns ------------------------------------------------------------
work_type = rows("SELECT COALESCE(formatted_work_type,'Unknown'), COUNT(*) c FROM postings GROUP BY 1 ORDER BY c DESC")
experience = rows("SELECT COALESCE(formatted_experience_level,'Unknown'), COUNT(*) c FROM postings GROUP BY 1 ORDER BY c DESC")
category = rows("SELECT COALESCE(job_category,'Other'), COUNT(*) c FROM postings GROUP BY 1 ORDER BY c DESC")
locations = rows("SELECT location, COUNT(*) c FROM postings WHERE location IS NOT NULL GROUP BY 1 ORDER BY c DESC LIMIT 12")
companies = rows("""SELECT co.name, COUNT(*) c FROM postings p JOIN companies co ON p.company_id=co.company_id
                    GROUP BY co.company_id ORDER BY c DESC LIMIT 10""")
top_skills = rows("""SELECT s.skill_name, COUNT(*) c FROM job_skills js JOIN skills s ON js.skill_abr=s.skill_abr
                     GROUP BY s.skill_abr ORDER BY c DESC LIMIT 15""")
sal_by_cat = rows("""SELECT COALESCE(job_category,'Other') cat, AVG(normalized_salary) a, COUNT(*) c
                     FROM postings WHERE normalized_salary IS NOT NULL GROUP BY 1 ORDER BY a DESC LIMIT 12""")

stats["work_type"] = [{"name": r[0], "value": r[1]} for r in work_type]
stats["experience"] = [{"name": r[0], "value": r[1]} for r in experience]
stats["category"] = [{"name": r[0], "value": r[1]} for r in category]
stats["locations"] = [{"name": r[0], "value": r[1]} for r in locations]
stats["companies_top"] = [{"name": r[0], "value": r[1]} for r in companies]
stats["top_skills"] = [{"name": r[0], "value": r[1]} for r in top_skills]
stats["salary_by_category"] = [{"name": r[0], "avg": round(r[1], 2), "n": r[2]} for r in sal_by_cat]

# ---- skill co-occurrence (top 12) -----------------------------------------
top12 = rows("""SELECT s.skill_abr, s.skill_name, COUNT(*) c FROM job_skills js JOIN skills s ON js.skill_abr=s.skill_abr
                GROUP BY s.skill_abr ORDER BY c DESC LIMIT 12""")
abrs = [r[0] for r in top12]
names12 = [r[1] for r in top12]
idx = {a: i for i, a in enumerate(abrs)}
M = np.zeros((12, 12), dtype=int)
qmarks = ",".join("?" * len(abrs))
job_map = {}
for job_id, abr in rows(f"SELECT job_id, skill_abr FROM job_skills WHERE skill_abr IN ({qmarks})", abrs):
    job_map.setdefault(job_id, []).append(abr)
for sk in job_map.values():
    for i in range(len(sk)):
        for j in range(i, len(sk)):
            a, b = idx[sk[i]], idx[sk[j]]
            M[a][b] += 1
            if a != b:
                M[b][a] += 1
stats["cooc_skills"] = names12

# date range
stats["date_min"] = one("SELECT MIN(listed_time) FROM postings WHERE listed_time IS NOT NULL")
stats["date_max"] = one("SELECT MAX(listed_time) FROM postings WHERE listed_time IS NOT NULL")

con.close()

# ============================ CHARTS =======================================

def hbar(data, fname, color, title, xlabel="Number of postings"):
    data = list(reversed(data))
    names = [d["name"] for d in data]
    vals = [d["value"] for d in data]
    fig, ax = plt.subplots(figsize=(7.2, max(3.2, 0.42 * len(names))))
    ax.barh(names, vals, color=color, edgecolor="white")
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontweight="bold")
    for i, v in enumerate(vals):
        ax.text(v, i, f" {v:,}", va="center", fontsize=9)
    ax.grid(axis="y", alpha=0)
    fig.savefig(os.path.join(OUT, fname))
    plt.close(fig)


def pie(data, fname, title, top=8):
    data = sorted(data, key=lambda d: -d["value"])
    if len(data) > top:
        rest = sum(d["value"] for d in data[top:])
        data = data[:top] + [{"name": "Other", "value": rest}]
    names = [d["name"] for d in data]
    vals = [d["value"] for d in data]
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    wedges, _, autotexts = ax.pie(
        vals, autopct=lambda p: f"{p:.1f}%" if p > 3 else "", startangle=90,
        colors=PALETTE + PALETTE, pctdistance=0.8,
        wedgeprops={"width": 0.42, "edgecolor": "white"})
    for t in autotexts:
        t.set_fontsize(8)
    ax.legend(wedges, names, loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9, frameon=False)
    ax.set_title(title, fontweight="bold")
    fig.savefig(os.path.join(OUT, fname))
    plt.close(fig)


hbar(stats["top_skills"], "fig_top_skills.png", PALETTE[0], "Top 15 In-Demand Skills (dataset taxonomy)")
hbar(stats["locations"], "fig_locations.png", PALETTE[1], "Top 12 Hiring Locations")
hbar(stats["companies_top"], "fig_companies.png", PALETTE[2], "Top 10 Hiring Companies")
pie(stats["category"], "fig_categories.png", "Job Category Distribution (ML classifier)")
pie(stats["work_type"], "fig_work_type.png", "Work-Type Breakdown")

# experience as vertical bar (ordered)
exp = stats["experience"]
fig, ax = plt.subplots(figsize=(7.0, 4.0))
ax.bar([e["name"] for e in exp], [e["value"] for e in exp], color=PALETTE[3], edgecolor="white")
ax.set_ylabel("Number of postings")
ax.set_title("Experience-Level Distribution", fontweight="bold")
plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
ax.grid(axis="x", alpha=0)
fig.savefig(os.path.join(OUT, "fig_experience.png"))
plt.close(fig)

# salary histogram
fig, ax = plt.subplots(figsize=(7.4, 4.2))
clip = sal_arr[sal_arr <= 400000]
ax.hist(clip, bins=40, color=PALETTE[0], edgecolor="white", alpha=0.9)
ax.axvline(stats["salary"]["median"], color=PALETTE[4], linestyle="--", linewidth=2,
           label=f"Median ${stats['salary']['median']:,.0f}")
ax.axvline(stats["salary"]["mean"], color=PALETTE[2], linestyle=":", linewidth=2,
           label=f"Mean ${stats['salary']['mean']:,.0f}")
ax.set_xlabel("Annualised salary (USD)")
ax.set_ylabel("Number of postings")
ax.set_title("Salary Distribution (normalised to annual equivalent)", fontweight="bold")
ax.legend()
ax.grid(axis="x", alpha=0)
fig.savefig(os.path.join(OUT, "fig_salary_hist.png"))
plt.close(fig)

# salary by category
sbc = sorted(stats["salary_by_category"], key=lambda d: d["avg"])
fig, ax = plt.subplots(figsize=(7.4, 4.6))
ax.barh([d["name"] for d in sbc], [d["avg"] for d in sbc], color=PALETTE[6], edgecolor="white")
ax.set_xlabel("Average annualised salary (USD)")
ax.set_title("Average Salary by Job Category", fontweight="bold")
for i, d in enumerate(sbc):
    ax.text(d["avg"], i, f" ${d['avg']:,.0f}", va="center", fontsize=8)
ax.grid(axis="y", alpha=0)
fig.savefig(os.path.join(OUT, "fig_salary_by_category.png"))
plt.close(fig)

# co-occurrence heatmap
fig, ax = plt.subplots(figsize=(7.8, 6.6))
logM = np.log1p(M)
im = ax.imshow(logM, cmap="YlGnBu")
ax.set_xticks(range(12)); ax.set_yticks(range(12))
ax.set_xticklabels(names12, rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(names12, fontsize=8)
ax.set_title("Skill Co-occurrence Matrix (top 12, log scale)", fontweight="bold")
for i in range(12):
    for j in range(12):
        ax.text(j, i, f"{M[i][j]//1000}k" if M[i][j] >= 1000 else str(M[i][j]),
                ha="center", va="center", fontsize=6,
                color="white" if logM[i][j] > logM.max() * 0.6 else "black")
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="log(1+count)")
fig.savefig(os.path.join(OUT, "fig_cooccurrence.png"))
plt.close(fig)

# data completeness
completeness = [
    ("Company link", 100.0 * stats["with_company"] / stats["postings"]),
    ("Description", 100.0 * stats["with_desc"] / stats["postings"]),
    ("Salary", 100.0 * stats["with_salary"] / stats["postings"]),
    ("Remote flag", 100.0 * stats["remote"] / stats["postings"]),
]
fig, ax = plt.subplots(figsize=(7.0, 3.6))
labels = [c[0] for c in completeness]
vals = [round(c[1], 1) for c in completeness]
bars = ax.bar(labels, vals, color=PALETTE[1], edgecolor="white")
ax.set_ylabel("% of postings populated")
ax.set_ylim(0, 105)
ax.set_title("Field Completeness After Cleaning", fontweight="bold")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v}%", ha="center", fontsize=9)
ax.grid(axis="x", alpha=0)
fig.savefig(os.path.join(OUT, "fig_completeness.png"))
plt.close(fig)
stats["completeness"] = {k: round(v, 1) for k, v in completeness}

with open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)

print("STATS SUMMARY")
print(json.dumps({k: v for k, v in stats.items()
                  if k not in ("top_skills", "locations", "companies_top", "category",
                               "work_type", "experience", "salary_by_category", "cooc_skills")},
                 indent=2, ensure_ascii=False))
print("\nTOP SKILLS:", [(s["name"], s["value"]) for s in stats["top_skills"]])
print("\nCATEGORIES:", [(s["name"], s["value"]) for s in stats["category"]])
print("\nWORK TYPE:", [(s["name"], s["value"]) for s in stats["work_type"]])
print("\nEXPERIENCE:", [(s["name"], s["value"]) for s in stats["experience"]])
print("\nLOCATIONS:", [(s["name"], s["value"]) for s in stats["locations"]])
print("\nCOMPANIES:", [(s["name"], s["value"]) for s in stats["companies_top"]])
print("\nSALARY BY CAT:", [(s["name"], s["avg"], s["n"]) for s in stats["salary_by_category"]])
print("\nFigures written to:", OUT)
print("PNG files:", sorted(f for f in os.listdir(OUT) if f.endswith(".png")))
