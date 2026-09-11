"""Admin-only REST API.

Everything under ``/api/admin`` is gated by :func:`admin_required`, which checks
the ``role`` claim embedded in the JWT at login.  This is the *management* tier
of the system — distinct from the public, read-only browsing/analytics tier —
and provides content CRUD (postings, companies) plus user administration.
"""
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models import Company, CompanySpeciality, Posting, Skill, User
from ..services import cache

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if get_jwt().get("role") != "admin":
            return jsonify({"error": "administrator privileges required"}), 403
        return fn(*args, **kwargs)

    return wrapper


def _next_id(column):
    current = db.session.query(db.func.max(column)).scalar()
    return int(current or 0) + 1


# --------------------------------------------------------------------------- #
#  Overview                                                                    #
# --------------------------------------------------------------------------- #
@bp.get("/overview")
@admin_required
def overview():
    admins = User.query.filter_by(role="admin").count()
    total_users = User.query.count()
    recent = User.query.order_by(User.user_id.desc()).limit(6).all()
    return jsonify({
        "users": {"total": total_users, "admins": admins, "regular": total_users - admins},
        "content": {
            "postings": Posting.query.count(),
            "companies": Company.query.count(),
            "skills": Skill.query.count(),
        },
        "recent_users": [u.to_dict() for u in recent],
    })


# --------------------------------------------------------------------------- #
#  User administration                                                         #
# --------------------------------------------------------------------------- #
@bp.get("/users")
@admin_required
def list_users():
    page = max(request.args.get("page", 1, type=int), 1)
    size = min(request.args.get("size", 20, type=int), 100)
    query = User.query
    q = request.args.get("q", type=str)
    if q:
        query = query.filter(User.username.ilike(f"%{q}%"))
    role = request.args.get("role", type=str)
    if role in {"user", "admin"}:
        query = query.filter_by(role=role)
    query = query.order_by(User.user_id.asc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    return jsonify({
        "items": [u.to_dict() for u in pagination.items],
        "total": pagination.total, "page": page, "size": size, "pages": pagination.pages,
    })


@bp.patch("/users/<int:user_id>")
@admin_required
def update_user_role(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "not found"}), 404
    role = (request.get_json(silent=True) or {}).get("role")
    if role not in {"user", "admin"}:
        return jsonify({"error": "role must be 'user' or 'admin'"}), 400
    # Never strip the last remaining administrator of their privileges.
    if user.role == "admin" and role == "user" and User.query.filter_by(role="admin").count() <= 1:
        return jsonify({"error": "cannot demote the last administrator"}), 409
    user.role = role
    db.session.commit()
    return jsonify(user.to_dict())


@bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "not found"}), 404
    if str(user.user_id) == str(get_jwt_identity()):
        return jsonify({"error": "you cannot delete your own account"}), 409
    if user.role == "admin" and User.query.filter_by(role="admin").count() <= 1:
        return jsonify({"error": "cannot delete the last administrator"}), 409
    db.session.delete(user)
    db.session.commit()
    return jsonify({"deleted": user_id})


# --------------------------------------------------------------------------- #
#  Posting CRUD                                                                #
# --------------------------------------------------------------------------- #
_POSTING_FIELDS = (
    "title", "description", "company_id", "location", "normalized_salary",
    "min_salary", "med_salary", "max_salary", "pay_period", "currency",
    "formatted_work_type", "formatted_experience_level", "remote_allowed",
    "job_category",
)


def _apply_posting(posting, payload):
    for field in _POSTING_FIELDS:
        if field in payload:
            value = payload[field]
            if field == "remote_allowed":
                value = bool(value)
            setattr(posting, field, value)


@bp.post("/postings")
@admin_required
def create_posting():
    payload = request.get_json(silent=True) or {}
    if not (payload.get("title") or "").strip():
        return jsonify({"error": "title is required"}), 400
    if payload.get("company_id") and db.session.get(Company, payload["company_id"]) is None:
        return jsonify({"error": "company_id does not exist"}), 400
    posting = Posting(job_id=_next_id(Posting.job_id))
    _apply_posting(posting, payload)
    db.session.add(posting)
    db.session.commit()
    cache.clear_all()
    return jsonify(posting.to_dict(detail=True)), 201


@bp.put("/postings/<int:job_id>")
@admin_required
def update_posting(job_id):
    posting = db.session.get(Posting, job_id)
    if posting is None:
        return jsonify({"error": "not found"}), 404
    payload = request.get_json(silent=True) or {}
    if "company_id" in payload and payload["company_id"] and db.session.get(Company, payload["company_id"]) is None:
        return jsonify({"error": "company_id does not exist"}), 400
    _apply_posting(posting, payload)
    db.session.commit()
    cache.clear_all()
    return jsonify(posting.to_dict(detail=True))


@bp.delete("/postings/<int:job_id>")
@admin_required
def delete_posting(job_id):
    posting = db.session.get(Posting, job_id)
    if posting is None:
        return jsonify({"error": "not found"}), 404
    db.session.delete(posting)
    db.session.commit()
    cache.clear_all()
    return jsonify({"deleted": job_id})


# --------------------------------------------------------------------------- #
#  Company CRUD                                                                #
# --------------------------------------------------------------------------- #
_COMPANY_FIELDS = (
    "name", "description", "company_size", "country", "state", "city",
    "address", "url", "employee_count", "follower_count",
)


def _apply_company(company, payload):
    for field in _COMPANY_FIELDS:
        if field in payload:
            setattr(company, field, payload[field])


@bp.post("/companies")
@admin_required
def create_company():
    payload = request.get_json(silent=True) or {}
    if not (payload.get("name") or "").strip():
        return jsonify({"error": "name is required"}), 400
    company = Company(company_id=_next_id(Company.company_id))
    _apply_company(company, payload)
    db.session.add(company)
    db.session.commit()
    cache.clear_all()
    return jsonify(company.to_dict(with_specialities=True)), 201


@bp.put("/companies/<int:company_id>")
@admin_required
def update_company(company_id):
    company = db.session.get(Company, company_id)
    if company is None:
        return jsonify({"error": "not found"}), 404
    _apply_company(company, request.get_json(silent=True) or {})
    db.session.commit()
    cache.clear_all()
    return jsonify(company.to_dict(with_specialities=True))


@bp.delete("/companies/<int:company_id>")
@admin_required
def delete_company(company_id):
    company = db.session.get(Company, company_id)
    if company is None:
        return jsonify({"error": "not found"}), 404
    if company.postings.count() > 0:
        return jsonify({"error": "company still has postings; reassign or delete them first"}), 409
    db.session.delete(company)
    db.session.commit()
    cache.clear_all()
    return jsonify({"deleted": company_id})
