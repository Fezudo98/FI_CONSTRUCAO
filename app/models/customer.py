"""Cadastro de clientes do depósito (pessoa física ou jurídica)."""
from app.extensions import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class Customer(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    document = db.Column(db.String(20))  # CPF ou CNPJ
    phone = db.Column(db.String(20))
    email = db.Column(db.String(150))

    address_street = db.Column(db.String(200))
    address_number = db.Column(db.String(20))
    address_district = db.Column(db.String(100))
    address_city = db.Column(db.String(100))
    address_state = db.Column(db.String(2))
    address_zip = db.Column(db.String(10))
    address_complement = db.Column(db.String(100))

    note = db.Column(db.String(255))

    def full_address(self):
        parts = [
            f"{self.address_street}, {self.address_number}" if self.address_street else None,
            self.address_complement,
            self.address_district,
            f"{self.address_city}/{self.address_state}" if self.address_city else None,
            self.address_zip,
        ]
        return " - ".join(p for p in parts if p)
