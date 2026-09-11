"""API blueprint registration."""
from . import admin, analytics, auth, companies, postings, skills


def register_blueprints(app):
    app.register_blueprint(postings.bp)
    app.register_blueprint(companies.bp)
    app.register_blueprint(skills.bp)
    app.register_blueprint(analytics.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
