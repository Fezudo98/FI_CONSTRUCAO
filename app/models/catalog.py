"""Produtos e conversões de unidade (unidade, caixa, fardo, metro, quilo etc.)."""
from app.extensions import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class Product(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(40), unique=True, nullable=False, index=True)
    barcode = db.Column(db.String(40), index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))

    base_unit = db.Column(db.String(10), nullable=False, default="UN")
    cost_price = db.Column(db.Numeric(12, 4), nullable=False, default=0)
    sale_price = db.Column(db.Numeric(12, 4), nullable=False, default=0)
    min_stock = db.Column(db.Numeric(12, 4), nullable=False, default=0)

    conversions = db.relationship(
        "UnitConversion", back_populates="product", cascade="all, delete-orphan"
    )


class UnitConversion(db.Model, TimestampMixin):
    """Ex.: 1 CX = 12 UN, 1 FARDO = 20 UN, 1 M = 1/3 barra etc."""
    __tablename__ = "unit_conversions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    factor_to_base = db.Column(db.Numeric(12, 6), nullable=False)  # quantas base_unit tem 1 desta unidade

    product = db.relationship("Product", back_populates="conversions")

    __table_args__ = (db.UniqueConstraint("product_id", "unit", name="uq_product_unit"),)
