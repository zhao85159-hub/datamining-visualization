from ..extensions import db


class Posting(db.Model):
    __tablename__ = "postings"

    job_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    title = db.Column(db.String(512), index=True)
    description = db.Column(db.Text)
    company_id = db.Column(
        db.BigInteger, db.ForeignKey("companies.company_id"), index=True
    )
    location = db.Column(db.String(255), index=True)

    # Salary fields normalised to an annual equivalent during ETL.
    min_salary = db.Column(db.Float)
    med_salary = db.Column(db.Float)
    max_salary = db.Column(db.Float)
    normalized_salary = db.Column(db.Float, index=True)
    pay_period = db.Column(db.String(32))
    currency = db.Column(db.String(8))

    formatted_work_type = db.Column(db.String(64), index=True)
    formatted_experience_level = db.Column(db.String(64), index=True)
    remote_allowed = db.Column(db.Boolean, default=False, index=True)
    views = db.Column(db.Integer)
    applies = db.Column(db.Integer)
    listed_time = db.Column(db.DateTime, index=True)

    # Derived by the NLP / classification services.
    job_category = db.Column(db.String(64), index=True)

    company = db.relationship("Company", back_populates="postings")
    skill_links = db.relationship(
        "JobSkill", back_populates="posting",
        cascade="all, delete-orphan", lazy="select",
    )

    def to_dict(self, detail: bool = False) -> dict:
        data = {
            "job_id": self.job_id,
            "title": self.title,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "location": self.location,
            "normalized_salary": self.normalized_salary,
            "formatted_work_type": self.formatted_work_type,
            "formatted_experience_level": self.formatted_experience_level,
            "remote_allowed": bool(self.remote_allowed),
            "job_category": self.job_category,
            "listed_time": self.listed_time.isoformat() if self.listed_time else None,
        }

        if detail:
            data.update({
                "description": self.description,
                "min_salary": self.min_salary,
                "med_salary": self.med_salary,
                "max_salary": self.max_salary,
                "pay_period": self.pay_period,
                "currency": self.currency,
                "views": self.views,
                "applies": self.applies,
                "skills": [
                    {"skill_abr": l.skill_abr,
                     "skill_name": l.skill.skill_name if l.skill else l.skill_abr}
                    for l in self.skill_links
                ],
            })
        return data


class JobSkill(db.Model):
    """Association table between postings and skills (many-to-many)."""

    __tablename__ = "job_skills"

    job_id = db.Column(
        db.BigInteger, db.ForeignKey("postings.job_id"), primary_key=True
    )
    skill_abr = db.Column(
        db.String(16), db.ForeignKey("skills.skill_abr"), primary_key=True
    )

    posting = db.relationship("Posting", back_populates="skill_links")
    skill = db.relationship("Skill", back_populates="job_links")
