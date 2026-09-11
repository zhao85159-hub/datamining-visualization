"""SQLAlchemy ORM models.

The schema is normalised to Third Normal Form (3NF) and mirrors the structure
of the Kaggle *LinkedIn Job Postings (2023-2024)* dataset:

    companies (1) --- (N) postings (N) --- (N) skills      [via job_skills]
    companies (1) --- (N) company_specialities
    users                                              [authentication]
"""
from .company import Company, CompanySpeciality
from .skill import Skill
from .posting import Posting, JobSkill
from .user import User

__all__ = [
    "Company",
    "CompanySpeciality",
    "Skill",
    "Posting",
    "JobSkill",
    "User",
]
