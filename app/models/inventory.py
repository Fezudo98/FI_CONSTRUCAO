"""Estoque por endereço e lote, saldo reservado/disponível e movimentações."""
from app.extensions import db
from app.models.base import TimestampMixin


class StockLocation(db.Model, TimestampMixin):
    """Endereço físico no depósito (ex.: 'Galpão A - Rua 3 - Prateleira 2')."""
    __tablename__ = "stock_locations"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(200))

    __table_args__ = (db.UniqueConstraint("code", name="uq_location_code"),)


class Lot(db.Model, TimestampMixin):
    __tablename__ = "lots"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    code = db.Column(db.String(60), nullable=False)
    expires_at = db.Column(db.Date)

    __table_args__ = (db.UniqueConstraint("product_id", "code", name="uq_lot_code"),)


class StockBalance(db.Model, TimestampMixin):
    """Saldo consolidado de um produto em um endereço/lote (em base_unit).
    quantity = saldo físico; reserved = comprometido em pedidos ainda não retirados."""
    __tablename__ = "stock_balances"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("stock_locations.id"), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey("lots.id"), nullable=True)

    quantity = db.Column(db.Numeric(14, 4), nullable=False, default=0)
    reserved = db.Column(db.Numeric(14, 4), nullable=False, default=0)

    @property
    def available(self):
        return self.quantity - self.reserved

    __table_args__ = (
        db.UniqueConstraint(
            "product_id", "location_id", "lot_id", name="uq_stock_balance"
        ),
    )


MOVEMENT_IN = "in"
MOVEMENT_OUT = "out"
MOVEMENT_ADJUST = "adjust"
MOVEMENT_RESERVE = "reserve"
MOVEMENT_RELEASE = "release"


class StockMovement(db.Model, TimestampMixin):
    """Histórico imutável de toda alteração de estoque, para auditoria."""
    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("stock_locations.id"), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey("lots.id"), nullable=True)

    kind = db.Column(db.String(10), nullable=False)  # in/out/adjust/reserve/release
    quantity = db.Column(db.Numeric(14, 4), nullable=False)  # sempre positivo; kind define o sentido
    reference_type = db.Column(db.String(40))  # 'sale', 'purchase_receipt', 'order', 'manual'
    reference_id = db.Column(db.Integer)
    note = db.Column(db.String(255))
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
