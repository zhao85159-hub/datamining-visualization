"""Application configuration.

The database backend is selected through the ``DATABASE_URL`` environment
variable so the same code runs against MySQL (production, as specified in the
project plan) or SQLite (zero-configuration local development / automated
tests).  Example MySQL URL::

    mysql+pymysql://root:<password>@127.0.0.1:3306/linkedin_jobs?charset=utf8mb4
"""
from __future__ import annotations

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Load a local .env (if present) so DATABASE_URL and secrets can be supplied
# without exporting environment variables manually.
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(BASE_DIR, ".env"))
except Exception:  # python-dotenv is optional; ignore if unavailable
    pass


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "data", "app.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = True

    # Pagination guard rails
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)


def get_config(name: str | None = None) -> type[Config]:
    return {"test": TestConfig}.get(name or os.environ.get("FLASK_ENV", ""), Config)
