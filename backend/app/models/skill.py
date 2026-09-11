from ..extensions import db


class Skill(db.Model):
    __tablename__ = "skills"

    skill_abr = db.Column(db.String(16), primary_key=True)
    skill_name = db.Column(db.String(128), index=True)

    job_links = db.relationship("JobSkill", back_populates="skill", lazy="dynamic")

    def to_dict(self) -> dict:
        return {"skill_abr": self.skill_abr, "skill_name": self.skill_name}
