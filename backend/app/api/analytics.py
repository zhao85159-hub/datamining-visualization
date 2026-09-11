from flask import Blueprint, jsonify, request

from ..services import analytics
from ..services.classifier import default_classifier

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@bp.get("/dashboard")
def dashboard():
    return jsonify({
        "summary": analytics.dashboard_summary(),
        "work_type": analytics.work_type_breakdown(),
        "experience": analytics.experience_breakdown(),
        "categories": analytics.category_breakdown(),
        "top_locations": analytics.top_locations(),
        "top_companies": analytics.top_companies(),
        "top_skills": analytics.top_skills(limit=15),
    })


@bp.get("/salary")
def salary():
    return jsonify({
        "distribution": analytics.salary_distribution(),
        "by_category": analytics.salary_by_category(),
    })


@bp.get("/trends")
def trends():
    """Daily hiring trends: overall volume, avg salary and per-category series."""
    return jsonify(analytics.time_trends())


@bp.get("/mining")
def mining():
    """Data-mining views for the dashboard (增加功能):

    * ``position_trends`` — hiring volume over time where each *position*
      (by location and by job category) shows its own distinct trend line.
    * ``market`` — per-category bubble profile (avg salary x avg applies x volume).
    """
    return jsonify({
        "position_trends": analytics.position_time_trends(),
        "market": analytics.category_market(),
    })


@bp.get("/skills-matrix")
def skills_matrix():
    return jsonify(analytics.skill_cooccurrence(top_n=12))


@bp.post("/classify")
def classify():
    """Predict the job category of a free-text title (ML model demo)."""
    payload = request.get_json(silent=True) or {}
    title = payload.get("title", "")
    category, confidence = default_classifier.predict_proba(title)
    return jsonify({"title": title, "category": category, "confidence": round(confidence, 4)})
