"""Contas a pagar: geradas no recebimento de compras, com baixa total ou parcial."""
from app.extensions import db
from app.models.base import TimestampMixin

PAYABLE_OPEN = "open"
PAYABLE_PARTIAL = "partially_paid"
PAYABLE_PAID = "paid"
PAYABLE_CANCELLED = "cancelled"


class Payable(db.Model, TimestampMixin):
    __tablename__ = "payables"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"))

    description = db.Column(db.String(200))
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=PAYABLE_OPEN)

    supplier = db.relationship("Supplier")
    settlements = db.relationship("PayableSettlement", back_populates="payable", cascade="all, delete-orphan")

    @property
    def amount_paid(self):
        return sum((s.amount for s in self.settlements), start=0)

    @property
    def amount_open(self):
        return self.amount - self.amount_paid


class PayableSettlement(db.Model, TimestampMixin):
    """Uma baixa (total ou parcial) de uma conta a pagar."""
    __tablename__ = "payable_settlements"

    id = db.Column(db.Integer, primary_key=True)
    payable_id = db.Column(db.Integer, db.ForeignKey("payables.id"), nullable=False)
    paid_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.String(20))
    paid_at = db.Column(db.DateTime(timezone=True))

    payable = db.relationship("Payable", back_populates="settlements")
