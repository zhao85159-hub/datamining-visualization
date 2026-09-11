from flask import Blueprint, jsonify, request
from sqlalchemy import or_, text

from ..extensions import db
from ..models import Posting

bp = Blueprint("postings", __name__, url_prefix="/api/postings")

SORT_FIELDS = {
    "listed_time": Posting.listed_time,
    "normalized_salary": Posting.normalized_salary,
    "title": Posting.title,
}


@bp.get("")
def list_postings():
    page = max(request.args.get("page", 1, type=int), 1)
    size = min(request.args.get("size", 20, type=int), 100)

    query = Posting.query
    q = request.args.get("q", type=str)
    use_fulltext = False
    if q:
        # On MySQL use the FULLTEXT index over (title, description) for an
        # indexed, relevance-ranked search; fall back to a portable LIKE scan
        # on SQLite (development / tests).
        if db.engine.dialect.name == "mysql" and len(q) >= 3:
            query = query.filter(
                text("MATCH(postings.title, postings.description) "
                     "AGAINST (:ftq IN NATURAL LANGUAGE MODE)").bindparams(ftq=q)
            )
            use_fulltext = True
        else:
            like = f"%{q}%"
            query = query.filter(or_(Posting.title.ilike(like), Posting.location.ilike(like)))
    for field, column in (
        ("work_type", Posting.formatted_work_type),
        ("experience_level", Posting.formatted_experience_level),
        ("category", Posting.job_category),
    ):
        val = request.args.get(field, type=str)
        if val:
            query = query.filter(column == val)
    location = request.args.get("location", type=str)
    if location:
        query = query.filter(Posting.location.ilike(f"%{location}%"))
    if request.args.get("remote", type=str) in {"1", "true", "True"}:
        query = query.filter(Posting.remote_allowed.is_(True))
    min_salary = request.args.get("min_salary", type=float)
    if min_salary is not None:
        query = query.filter(Posting.normalized_salary >= min_salary)

    sort = request.args.get("sort")
    if use_fulltext and not sort:
        # Relevance-ranked ordering is the natural order for a search and is
        # index-friendly, avoiding an expensive filesort of the whole match set.
        query = query.order_by(
            text("MATCH(postings.title, postings.description) "
                 "AGAINST (:ftqo IN NATURAL LANGUAGE MODE) DESC").bindparams(ftqo=q)
        )
    else:
        order = SORT_FIELDS.get(sort or "listed_time", Posting.listed_time)
        if request.args.get("dir", "desc") == "asc":
            query = query.order_by(order.asc())
        else:
            query = query.order_by(order.desc())

    pagination = query.paginate(page=page, per_page=size, error_out=False)
    return jsonify({
        "items": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "page": page,
        "size": size,
        "pages": pagination.pages,
    })


@bp.get("/<int:job_id>")
def get_posting(job_id):
    posting = db.session.get(Posting, job_id)
    if posting is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(posting.to_dict(detail=True))


@bp.get("/<int:job_id>/similar")
def similar_postings(job_id):
    posting = db.session.get(Posting, job_id)
    if posting is None:
        return jsonify({"error": "not found"}), 404
    similar = (
        Posting.query.filter(
            Posting.job_category == posting.job_category,
            Posting.job_id != job_id,
        )
        .order_by(Posting.listed_time.desc())
        .limit(6)
        .all()
    )
    return jsonify([p.to_dict() for p in similar])
