"""Aggregated analytics queries powering the Dashboard and Skills views.

These are dataset-wide aggregations that are expensive to recompute on every
request, so each is wrapped in a short-lived TTL cache.  The cache is process
local and can be disabled for testing.
"""
from __future__ import annotations

from sqlalchemy import func

from ..extensions import db
from ..models import Company, JobSkill, Posting, Skill
from .cache import ttl_cache


@ttl_cache()
def dashboard_summary() -> dict:
    total_postings = db.session.query(func.count(Posting.job_id)).scalar() or 0
    total_companies = db.session.query(func.count(Company.company_id)).scalar() or 0
    total_skills = db.session.query(func.count(Skill.skill_abr)).scalar() or 0
    remote = db.session.query(func.count(Posting.job_id)).filter(
        Posting.remote_allowed.is_(True)
    ).scalar() or 0
    avg_salary = db.session.query(func.avg(Posting.normalized_salary)).filter(
        Posting.normalized_salary.isnot(None)
    ).scalar()
    return {
        "total_postings": int(total_postings),
        "total_companies": int(total_companies),
        "total_skills": int(total_skills),
        "remote_postings": int(remote),
        "remote_ratio": round(remote / total_postings, 4) if total_postings else 0,
        "avg_salary": round(float(avg_salary), 2) if avg_salary else None,
    }


@ttl_cache()
def work_type_breakdown() -> list[dict]:
    rows = (
        db.session.query(Posting.formatted_work_type, func.count(Posting.job_id))
        .group_by(Posting.formatted_work_type)
        .order_by(func.count(Posting.job_id).desc())
        .all()
    )
    return [{"name": r[0] or "Unknown", "value": int(r[1])} for r in rows]


@ttl_cache()
def experience_breakdown() -> list[dict]:
    rows = (
        db.session.query(Posting.formatted_experience_level, func.count(Posting.job_id))
        .group_by(Posting.formatted_experience_level)
        .order_by(func.count(Posting.job_id).desc())
        .all()
    )
    return [{"name": r[0] or "Unknown", "value": int(r[1])} for r in rows]


@ttl_cache()
def category_breakdown() -> list[dict]:
    rows = (
        db.session.query(Posting.job_category, func.count(Posting.job_id))
        .group_by(Posting.job_category)
        .order_by(func.count(Posting.job_id).desc())
        .all()
    )
    return [{"name": r[0] or "Other", "value": int(r[1])} for r in rows]


@ttl_cache()
def top_locations(limit: int = 12) -> list[dict]:
    rows = (
        db.session.query(Posting.location, func.count(Posting.job_id))
        .filter(Posting.location.isnot(None))
        .group_by(Posting.location)
        .order_by(func.count(Posting.job_id).desc())
        .limit(limit)
        .all()
    )
    return [{"name": r[0], "value": int(r[1])} for r in rows]


@ttl_cache()
def top_companies(limit: int = 10) -> list[dict]:
    rows = (
        db.session.query(
            Company.name, func.count(Posting.job_id).label("n")
        )
        .join(Posting, Posting.company_id == Company.company_id)
        .group_by(Company.company_id, Company.name)
        .order_by(func.count(Posting.job_id).desc())
        .limit(limit)
        .all()
    )
    return [{"name": r[0], "value": int(r.n)} for r in rows]


@ttl_cache()
def top_skills(limit: int = 20) -> list[dict]:
    rows = (
        db.session.query(
            Skill.skill_name, func.count(JobSkill.job_id).label("n")
        )
        .join(JobSkill, JobSkill.skill_abr == Skill.skill_abr)
        .group_by(Skill.skill_abr, Skill.skill_name)
        .order_by(func.count(JobSkill.job_id).desc())
        .limit(limit)
        .all()
    )
    return [{"name": r[0], "value": int(r.n)} for r in rows]


@ttl_cache()
def salary_distribution(bins: int = 12) -> dict:
    salaries = [
        float(s[0])                                                                                                                                                                                                  
        for s in db.session.query(Posting.normalized_salary)
        .filter(Posting.normalized_salary.isnot(None))
        .all()
    ]
    if not salaries:
        return {"bins": [], "counts": [], "stats": {}}
    salaries.sort()
    lo, hi = salaries[0], min(salaries[-1], 400000)
    width = max((hi - lo) / bins, 1)
    edges = [lo + i * width for i in range(bins + 1)]
    counts = [0] * bins
    for s in salaries:
        idx = min(int((s - lo) / width), bins - 1)
        if idx >= 0:
            counts[idx] += 1
    n = len(salaries)
    stats = {
        "count": n,
        "min": round(salaries[0], 2),
        "max": round(salaries[-1], 2),
        "median": round(salaries[n // 2], 2),
        "mean": round(sum(salaries) / n, 2),
    }
    labels = [f"{int(edges[i] / 1000)}k-{int(edges[i + 1] / 1000)}k" for i in range(bins)]
    return {"bins": labels, "counts": counts, "stats": stats}


@ttl_cache()
def salary_by_category(limit: int = 12) -> list[dict]:
    rows = (
        db.session.query(
            Posting.job_category,
            func.avg(Posting.normalized_salary),
            func.count(Posting.job_id),
        )
        .filter(Posting.normalized_salary.isnot(None))
        .group_by(Posting.job_category)
        .order_by(func.avg(Posting.normalized_salary).desc())
        .limit(limit)
        .all()
    )
    return [
        {"category": r[0] or "Other", "avg_salary": round(float(r[1]), 2), "count": int(r[2])}
        for r in rows
    ]


@ttl_cache()
def skill_cooccurrence(top_n: int = 12) -> dict:
    """Symmetric co-occurrence matrix for the most frequent skills."""
    top = top_skills(limit=top_n)
    names = [t["name"] for t in top]
    if not names:
        return {"skills": [], "matrix": []}
    name_to_abr = dict(
        db.session.query(Skill.skill_name, Skill.skill_abr)
        .filter(Skill.skill_name.in_(names))
        .all()
    )
    abrs = [name_to_abr[n] for n in names if n in name_to_abr]
    index = {a: i for i, a in enumerate(abrs)}
    size = len(abrs)
    matrix = [[0] * size for _ in range(size)]

    job_to_skills: dict[int, list[str]] = {}
    rows = (
        db.session.query(JobSkill.job_id, JobSkill.skill_abr)
        .filter(JobSkill.skill_abr.in_(abrs))
        .all()
    )
    for job_id, abr in rows:
        job_to_skills.setdefault(job_id, []).append(abr)
    for skills in job_to_skills.values():
        for i in range(len(skills)):
            for j in range(i, len(skills)):
                a, b = index[skills[i]], index[skills[j]]
                matrix[a][b] += 1
                if a != b:
                    matrix[b][a] += 1
    return {"skills": [n for n in names if n in name_to_abr], "matrix": matrix}


def _day_expr():
    """Portable ``YYYY-MM-DD`` label for ``listed_time`` (MySQL & SQLite)."""
    if db.engine.dialect.name == "mysql":
        return func.date_format(Posting.listed_time, "%Y-%m-%d")
    return func.strftime("%Y-%m-%d", Posting.listed_time)


@ttl_cache()
def time_trends(top_categories: int = 6) -> dict:
    """Daily hiring trends over the dataset's posting window.

    The LinkedIn 2023-2024 dataset's postings cluster in a single month, so
    demand is bucketed by **day**.  Returns the overall daily posting volume,
    the daily average salary, and a per-category series for the top job
    categories — so each *position* shows its own trend over time
    (i.e. "position 按时间显示不同趋势").
    """
    day = _day_expr()

    vol_rows = (
        db.session.query(
            day.label("d"),
            func.count(Posting.job_id),
            func.avg(Posting.normalized_salary),
        )
        .filter(Posting.listed_time.isnot(None))
        .group_by(day)
        .order_by(day)
        .all()
    )
    days = [r[0] for r in vol_rows]
    volume = [int(r[1]) for r in vol_rows]
    avg_salary = [round(float(r[2])) if r[2] is not None else None for r in vol_rows]

    top = [
        r[0]
        for r in (
            db.session.query(Posting.job_category, func.count(Posting.job_id))
            .filter(Posting.listed_time.isnot(None), Posting.job_category.isnot(None))
            .group_by(Posting.job_category)
            .order_by(func.count(Posting.job_id).desc())
            .limit(top_categories)
            .all()
        )
    ]

    index = {d: i for i, d in enumerate(days)}
    series = {c: [0] * len(days) for c in top}
    cat_rows = (
        db.session.query(day.label("d"), Posting.job_category, func.count(Posting.job_id))
        .filter(Posting.listed_time.isnot(None), Posting.job_category.in_(top))
        .group_by(day, Posting.job_category)
        .all()
    )
    for d, c, n in cat_rows:
        if d in index and c in series:
            series[c][index[d]] = int(n)

    return {
        "days": days,
        "volume": volume,
        "avg_salary": avg_salary,
        "categories": top,
        "series": [{"name": c, "data": series[c]} for c in top],
    }


@ttl_cache()
def position_time_trends(top_n: int = 6) -> dict:
    """Hiring volume over the dataset's posting window, broken out so that each
    *position* shows its own distinct trend line — both by hiring **location**
    (地区) and by job **category** (职位类别).  Implements the
    「position 按月份/时序显示不同趋势」 requirement.

    The LinkedIn 2023-2024 extract spans a single ~four-week window
    (2024-03 → 2024-04), so a calendar-month axis would collapse to a single
    point; demand is therefore bucketed by **day** to reveal the trend shape.
    """
    day = _day_expr()

    days = [
        r[0]
        for r in (
            db.session.query(day.label("d"))
            .filter(Posting.listed_time.isnot(None))
            .group_by(day)
            .order_by(day)
            .all()
        )
    ]
    index = {d: i for i, d in enumerate(days)}

    def _series_for(dimension):
        top = [
            r[0]
            for r in (
                db.session.query(dimension, func.count(Posting.job_id))
                .filter(Posting.listed_time.isnot(None), dimension.isnot(None))
                .group_by(dimension)
                .order_by(func.count(Posting.job_id).desc())
                .limit(top_n)
                .all()
            )
        ]
        series = {v: [0] * len(days) for v in top}
        rows = (
            db.session.query(day.label("d"), dimension, func.count(Posting.job_id))
            .filter(Posting.listed_time.isnot(None), dimension.in_(top))
            .group_by(day, dimension)
            .all()
        )
        for d, v, n in rows:
            if d in index and v in series:
                series[v][index[d]] = int(n)
        return [{"name": v, "data": series[v]} for v in top]

    return {
        "days": days,
        "by_location": _series_for(Posting.location),
        "by_category": _series_for(Posting.job_category),
    }


@ttl_cache()
def category_market(limit: int = 12) -> list[dict]:
    """Per-category market profile powering a bubble chart: average annual
    salary (x), average applicant interest (y) and posting volume (bubble
    size).  A second data-mining view added per the 增加功能 requirement.
    """
    rows = (
        db.session.query(
            Posting.job_category,
            func.avg(Posting.normalized_salary),
            func.avg(Posting.applies),
            func.avg(Posting.views),
            func.count(Posting.job_id),
        )
        .filter(Posting.job_category.isnot(None))
        .group_by(Posting.job_category)
        .order_by(func.count(Posting.job_id).desc())
        .limit(limit)
        .all()
    )
    out = []
    for cat, sal, app, vw, cnt in rows:
        out.append({
            "category": cat or "Other",
            "avg_salary": round(float(sal), 2) if sal is not None else None,
            "avg_applies": round(float(app), 2) if app is not None else None,
            "avg_views": round(float(vw), 2) if vw is not None else None,
            "count": int(cnt),
        })
    return out
