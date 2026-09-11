# -*- coding: utf-8 -*-
"""Render the architecture, ER, use-case and schedule diagrams for the report."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Ellipse, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "figures"))
os.makedirs(OUT, exist_ok=True)

BLUE = "#0a66c2"; GREEN = "#0e8a5f"; AMBER = "#b45309"; PURPLE = "#7c3aed"
GREY = "#475569"; LIGHT = "#eef2f7"


def box(ax, x, y, w, h, text, fc="#ffffff", ec=BLUE, fs=9, bold=False, tc="#0f172a"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                       linewidth=1.4, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, wrap=True)


def arrow(ax, x1, y1, x2, y2, color=GREY, style="-|>", lw=1.6, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                 mutation_scale=14, color=color, lw=lw, linestyle=ls,
                 shrinkA=2, shrinkB=2))


# ============================= ARCHITECTURE =================================
fig, ax = plt.subplots(figsize=(9.2, 7.4))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.text(50, 97, "Three-Tier Architecture (Browser / Server)", ha="center",
        fontsize=14, fontweight="bold")

# Presentation tier
ax.add_patch(Rectangle((4, 74), 92, 20, facecolor=LIGHT, edgecolor=BLUE, lw=1.2))
ax.text(6, 91, "Presentation Tier  -  Vue.js 3 SPA (browser)", fontsize=10,
        fontweight="bold", color=BLUE)
for i, (t) in enumerate(["Views\n(Dashboard, Postings,\nCompanies, Skills, Login)",
                          "Reusable Components\n(StatCard, EChart)",
                          "Vue Router\n+ Pinia store",
                          "Axios HTTP client\n(JWT interceptor)"]):
    box(ax, 6 + i * 23, 76, 20, 12, t, fc="#ffffff", ec=BLUE, fs=8)

# Application tier
ax.add_patch(Rectangle((4, 40), 92, 28, facecolor=LIGHT, edgecolor=GREEN, lw=1.2))
ax.text(6, 64.5, "Application Tier  -  Flask 3 REST API (WSGI)", fontsize=10,
        fontweight="bold", color=GREEN)
for i, t in enumerate(["API Blueprints\npostings / companies /\nskills / analytics / auth",
                       "Business Services\nNLP extractor /\nJob classifier / Analytics",
                       "SQLAlchemy ORM\n+ Marshmallow",
                       "JWT auth\n+ CORS + RBAC"]):
    box(ax, 6 + i * 23, 50, 20, 12, t, fc="#ffffff", ec=GREEN, fs=8)
box(ax, 6, 42, 43, 6.5, "ETL pipeline (pandas): extract - clean - normalise - load", fc="#ffffff", ec=AMBER, fs=8)
box(ax, 53, 42, 43, 6.5, "Model artefact: TF-IDF + Logistic Regression (.pkl)", fc="#ffffff", ec=AMBER, fs=8)

# Data tier
ax.add_patch(Rectangle((4, 16), 92, 18, facecolor=LIGHT, edgecolor=PURPLE, lw=1.2))
ax.text(6, 31, "Data Tier", fontsize=10, fontweight="bold", color=PURPLE)
box(ax, 8, 18, 38, 10, "MySQL  (production, 5.7/8.0)\nnormalised 3NF schema, indexes, FULLTEXT", fc="#ffffff", ec=PURPLE, fs=8.0)
box(ax, 54, 18, 38, 10, "SQLite  (zero-config dev / test)\nselected via DATABASE_URL", fc="#ffffff", ec=PURPLE, fs=8.5)

# Kaggle source
box(ax, 32, 3, 36, 8, "Kaggle LinkedIn Job Postings (2023-2024)\n5 source CSV files", fc="#fff7ed", ec=AMBER, fs=8.5)

arrow(ax, 50, 74, 50, 68, color=BLUE)
ax.text(52, 71, "HTTPS / JSON", fontsize=8, color=BLUE)
arrow(ax, 50, 40, 50, 34, color=GREEN)
ax.text(52, 37, "SQL (ORM)", fontsize=8, color=GREEN)
arrow(ax, 50, 16, 50, 11, color=AMBER, style="-|>")
ax.text(52, 13.4, "ETL load", fontsize=8, color=AMBER)
# docker note
ax.text(95, 1.5, "Packaged with Docker / Nginx reverse proxy", ha="right",
        fontsize=8, style="italic", color=GREY)
fig.savefig(os.path.join(OUT, "fig_architecture.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ================================= ER ======================================
fig, ax = plt.subplots(figsize=(9.6, 7.0))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.text(50, 97, "Entity-Relationship Diagram (3NF)", ha="center", fontsize=14, fontweight="bold")


def entity(ax, x, y, w, title, pk, cols, ec=BLUE):
    h = 7 + 4.6 * (len(cols) + 1)
    ax.add_patch(Rectangle((x, y - h), w, h, facecolor="#ffffff", edgecolor=ec, lw=1.6))
    ax.add_patch(Rectangle((x, y - 7), w, 7, facecolor=ec, edgecolor=ec))
    ax.text(x + w / 2, y - 3.5, title, ha="center", va="center", color="white",
            fontsize=9.5, fontweight="bold")
    ax.text(x + 2, y - 11, "PK  " + pk, fontsize=7.6, fontweight="bold", color="#0f172a")
    for i, c in enumerate(cols):
        ax.text(x + 2, y - 15.2 - i * 4.4, c, fontsize=7.4, color="#334155")
    return (x, y, w, h)


companies = entity(ax, 4, 92, 30, "companies", "company_id",
                   ["name, country, city", "company_size", "employee_count",
                    "follower_count, url"], ec=GREEN)
postings = entity(ax, 40, 92, 30, "postings", "job_id",
                  ["FK company_id", "title, description", "location", "normalized_salary",
                   "work_type, experience", "remote_allowed", "job_category (derived)",
                   "listed_time"], ec=BLUE)
skills = entity(ax, 76, 92, 20, "skills", "skill_abr", ["skill_name"], ec=AMBER)
jobskills = entity(ax, 40, 40, 30, "job_skills", "job_id + skill_abr",
                   ["FK job_id", "FK skill_abr"], ec=PURPLE)
spec = entity(ax, 4, 46, 30, "company_specialities", "id",
              ["FK company_id", "speciality"], ec=GREEN)
users = entity(ax, 76, 40, 20, "users", "user_id",
               ["username (unique)", "password_hash", "role, created_at"], ec=GREY)

# relationships with cardinality (clean orthogonal/straight connectors)
# companies (1) --- (N) postings
arrow(ax, 34, 78, 40, 78, color=GREEN, style="-", lw=1.6)
ax.text(37, 80, "1        N", fontsize=8, color=GREEN, ha="center")
# postings (1) --- (N) job_skills
arrow(ax, 55, 43.4, 55, 40, color=PURPLE, style="-", lw=1.6)
ax.text(57.5, 41.6, "1 .. N", fontsize=8, color=PURPLE)
# job_skills (N) --- (1) skills
arrow(ax, 70, 30, 83, 75.8, color=AMBER, style="-", lw=1.6)
ax.text(79, 52, "N .. 1", fontsize=8, color=AMBER)
# companies (1) --- (N) company_specialities
arrow(ax, 12, 62, 12, 46, color=GREEN, style="-", lw=1.6)
ax.text(13.5, 54, "1 .. N", fontsize=8, color=GREEN)
ax.text(50, 9, "postings (N) to (M) skills is resolved through the job_skills bridge table",
        ha="center", fontsize=8.6, style="italic", color="#475569")
fig.savefig(os.path.join(OUT, "fig_er.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ============================== USE CASE ===================================
fig, ax = plt.subplots(figsize=(9.6, 7.2))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.text(50, 97, "Use-Case Diagram", ha="center", fontsize=14, fontweight="bold")
# system boundary
ax.add_patch(Rectangle((26, 6), 48, 86, facecolor="#fafbfc", edgecolor=GREY, lw=1.3))
ax.text(50, 89, "Job Postings Analysis System", ha="center", fontsize=10, fontweight="bold", color=GREY)

ucs = ["Browse / search postings", "View posting detail", "Browse companies",
       "View analytics dashboard", "Explore skills analysis", "Classify job title (ML)",
       "Extract skills from text (NLP)", "Register / Login", "Manage data import (ETL)"]
ys = [83, 75, 67, 59, 51, 43, 35, 25, 15]
for t, y in zip(ucs, ys):
    e = Ellipse((50, y), 40, 6.4, facecolor="#e8f1fb", edgecolor=BLUE, lw=1.2)
    ax.add_patch(e)
    ax.text(50, y, t, ha="center", va="center", fontsize=8.2)


def actor(ax, x, y, label):
    ax.add_patch(Circle((x, y + 4), 1.6, fill=False, lw=1.6, edgecolor="#0f172a"))
    ax.plot([x, x], [y + 2.4, y - 2], color="#0f172a", lw=1.6)
    ax.plot([x - 2.4, x + 2.4], [y + 1, y + 1], color="#0f172a", lw=1.6)
    ax.plot([x, x - 2], [y - 2, y - 5], color="#0f172a", lw=1.6)
    ax.plot([x, x + 2], [y - 2, y - 5], color="#0f172a", lw=1.6)
    ax.text(x, y - 8, label, ha="center", fontsize=8.6, fontweight="bold")


actor(ax, 9, 64, "Visitor /\nJob Seeker")
actor(ax, 9, 34, "Registered\nUser")
actor(ax, 91, 24, "Administrator")
for y in [83, 75, 67, 59, 51]:
    arrow(ax, 12, 64, 30, y, color=BLUE, style="-", lw=1.0)
for y in [43, 35, 25]:
    arrow(ax, 12, 34, 30, y, color=GREEN, style="-", lw=1.0)
arrow(ax, 88, 24, 70, 15, color=AMBER, style="-", lw=1.1)
arrow(ax, 88, 24, 70, 25, color=AMBER, style="-", lw=1.1)
fig.savefig(os.path.join(OUT, "fig_usecase.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ============================== GANTT ======================================
fig, ax = plt.subplots(figsize=(9.6, 5.2))
tasks = [
    ("Requirements & system design", 1, 1, BLUE),
    ("Database schema & ER design", 2, 1, BLUE),
    ("ETL pipeline (CSV->DB)", 3, 1, BLUE),
    ("Flask REST API", 4, 2, GREEN),
    ("Vue.js frontend & routing", 5, 2, GREEN),
    ("Dashboard & ECharts", 7, 1, AMBER),
    ("Skills/NLP & classifier module", 8, 1, AMBER),
    ("Testing & bug fixing", 8, 2, PURPLE),
    ("Documentation & report", 9, 1, PURPLE),
]
for i, (name, start, dur, c) in enumerate(tasks):
    ax.barh(i, dur, left=start, height=0.55, color=c, edgecolor="white")
    ax.text(start + dur + 0.05, i, name, va="center", fontsize=8.6)
ax.set_yticks([]); ax.invert_yaxis()
ax.set_xlim(1, 13); ax.set_xticks(range(1, 10))
ax.set_xticklabels([f"W{w}" for w in range(1, 10)])
ax.set_xlabel("Project week")
ax.set_title("Project Schedule - 3 Agile sprints over 9 weeks", fontweight="bold")
ax.grid(axis="y", alpha=0)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=BLUE, label="Sprint 1"), Patch(color=GREEN, label="Sprint 2"),
                   Patch(color=AMBER, label="Sprint 3 (build)"), Patch(color=PURPLE, label="Sprint 3 (QA)")],
          loc="lower right", fontsize=8)
fig.savefig(os.path.join(OUT, "fig_gantt.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("Diagrams written:", sorted(f for f in os.listdir(OUT) if f.endswith(".png")))
