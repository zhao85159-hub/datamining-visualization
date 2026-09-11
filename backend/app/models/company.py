from ..extensions import db


class Company(db.Model):
    __tablename__ = "companies"
    # Define field ORM, ORM (Object-Relational Mapping)
    company_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    name = db.Column(db.String(255), index=True)
    description = db.Column(db.Text)
    company_size = db.Column(db.Integer)
    country = db.Column(db.String(64), index=True)
    state = db.Column(db.String(128))
    city = db.Column(db.String(128))
    address = db.Column(db.String(255))
    url = db.Column(db.String(512))
    employee_count = db.Column(db.Integer)
    follower_count = db.Column(db.Integer)

    postings = db.relationship("Posting", back_populates="company", lazy="dynamic")
    specialities = db.relationship(
        "CompanySpeciality", back_populates="company",
        cascade="all, delete-orphan", lazy="select",
    )
    # json sql -json- frondend
    def to_dict(self, with_specialities: bool = False) -> dict:
        data = {
            "company_id": self.company_id,
            "name": self.name,
            "company_size": self.company_size,
            "country": self.country,
            "state": self.state,
            "city": self.city,
            "url": self.url,
            "employee_count": self.employee_count,
            "follower_count": self.follower_count,
        }
        if with_specialities:
            data["description"] = self.description
            data["specialities"] = [s.speciality for s in self.specialities]
        return data

#In a relational database, find the values corresponding to the data tables with associated relationships
class CompanySpeciality(db.Model):
    __tablename__ = "company_specialities"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.BigInteger, db.ForeignKey("companies.company_id"), index=True, nullable=False
    )
    speciality = db.Column(db.String(255))

    company = db.relationship("Company", back_populates="specialities")
