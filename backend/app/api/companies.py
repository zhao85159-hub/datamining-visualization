from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Company, Posting

bp = Blueprint("companies", __name__, url_prefix="/api/companies")


@bp.get("")
def list_companies():
    page = max(request.args.get("page", 1, type=int), 1)
    size = min(request.args.get("size", 20, type=int), 100)
    query = Company.query
    q = request.args.get("q", type=str)
    if q:
        query = query.filter(Company.name.ilike(f"%{q}%"))
    country = request.args.get("country", type=str)
    if country:
        query = query.filter(Company.country == country)
    query = query.order_by(Company.follower_count.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    return jsonify({
        "items": [c.to_dict() for c in pagination.items],
        "total": pagination.total,
        "page": page,
        "size": size,
        "pages": pagination.pages,
    })


@bp.get("/<int:company_id>")
def get_company(company_id):
    company = db.session.get(Company, company_id)
    if company is None:
        return jsonify({"error": "not found"}), 404
    data = company.to_dict(with_specialities=True)
    data["postings"] = [
        p.to_dict()
        for p in company.postings.order_by(Posting.listed_time.desc()).limit(10)
    ]
    data["posting_count"] = company.postings.count()
    return jsonify(data)
