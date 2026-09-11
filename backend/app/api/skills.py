from flask import Blueprint, jsonify, request

from ..services import analytics
from ..services.nlp import default_extractor

bp = Blueprint("skills", __name__, url_prefix="/api/skills")


@bp.get("")
def list_skills():
    limit = min(request.args.get("limit", 35, type=int), 100)
    return jsonify(analytics.top_skills(limit=limit))


@bp.get("/cooccurrence")
def cooccurrence():
    top_n = min(request.args.get("top", 12, type=int), 20)
    return jsonify(analytics.skill_cooccurrence(top_n=top_n))


@bp.post("/extract")
def extract_skills():
    """NLP demo endpoint: extract skills from arbitrary job-description text."""
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    return jsonify({"skills": default_extractor.extract(text)})
