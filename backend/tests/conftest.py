"""Pytest fixtures: an isolated in-memory application seeded with a small,
deterministic dataset so the API integration tests are fast and repeatable."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Company, JobSkill, Posting, Skill, User
from app.services import cache as _cache

# Disable the analytics TTL cache so each test sees its own seeded data.
_cache.ENABLED = False


def _seed():
    db.session.add_all([
        Company(company_id=1, name="Acme Corp", country="United States",
                city="New York", follower_count=1000, company_size=7),
        Company(company_id=2, name="DataWorks", country="United States",
                city="Austin", follower_count=500, company_size=4),
    ])
    db.session.add_all([
        Skill(skill_abr="IT", skill_name="Information Technology"),
        Skill(skill_abr="SALE", skill_name="Sales"),
    ])
    db.session.add_all([
        Posting(job_id=101, title="Senior Software Engineer",
                description="Python, SQL and AWS required", company_id=1,
                location="New York, NY", normalized_salary=140000,
                formatted_work_type="Full-time",
                formatted_experience_level="Mid-Senior level",
                remote_allowed=True, job_category="Software Engineering"),
        Posting(job_id=102, title="Sales Manager",
                description="Lead the regional sales team", company_id=2,
                location="Austin, TX", normalized_salary=90000,
                formatted_work_type="Full-time",
                formatted_experience_level="Associate",
                remote_allowed=False, job_category="Sales & Business"),
    ])
    db.session.add_all([
        JobSkill(job_id=101, skill_abr="IT"),
        JobSkill(job_id=102, skill_abr="SALE"),
    ])
    admin = User(username="admin", role="admin")
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        _seed()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
