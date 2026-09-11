"""Shared Flask extension singletons (initialised in the app factory)."""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager #
from flask_cors import CORS
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
