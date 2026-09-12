"""Fornecedores, cotações de compra, pedidos de compra e recebimentos."""
from app.extensions import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class Supplier(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    document = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(150))


class PurchaseQuoteRequest(db.Model, TimestampMixin):
    """Pedido de cotação enviado a um ou mais fornecedores."""
    __tablename__ = "purchase_quote_requests"

    id = db.Column(db.Integer, primary_key=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    note = db.Column(db.String(255))

    offers = db.relationship("SupplierOffer", back_populates="quote_request", cascade="all, delete-orphan")


class SupplierOffer(db.Model, TimestampMixin):
    """Oferta de um fornecedor específico para um pedido de cotação."""
    __tablename__ = "supplier_offers"

    id = db.Column(db.Integer, primary_key=True)
    quote_request_id = db.Column(db.Integer, db.ForeignKey("purchase_quote_requests.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    unit = db.Column(db.String(10), nullable=False)
    unit_price = db.Column(db.Numeric(12, 4), nullable=False)
    lead_time_days = db.Column(db.Integer)
    is_selected = db.Column(db.Boolean, default=False, nullable=False)

    quote_request = db.relationship("PurchaseQuoteRequest", back_populates="offers")


PO_DRAFT = "draft"
PO_SENT = "sent"
PO_PARTIALLY_RECEIVED = "partially_received"
PO_RECEIVED = "received"
PO_CANCELLED = "cancelled"


class PurchaseOrder(db.Model, TimestampMixin):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    status = db.Column(db.String(20), nullable=False, default=PO_DRAFT)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    supplier = db.relationship("Supplier")
    items = db.relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    receipts = db.relationship("PurchaseReceipt", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_items"

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    unit = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    unit_price = db.Column(db.Numeric(12, 4), nullable=False)
    quantity_received = db.Column(db.Numeric(12, 4), nullable=False, default=0)

    purchase_order = db.relationship("PurchaseOrder", back_populates="items")


class PurchaseReceipt(db.Model, TimestampMixin):
    """Um recebimento (pode ser parcial) de um pedido de compra. Ao confirmar,
    dá entrada no estoque e atualiza o custo médio do produto, e gera uma
    conta a pagar (Payable)."""
    __tablename__ = "purchase_receipts"

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    received_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    note = db.Column(db.String(255))

    purchase_order = db.relationship("PurchaseOrder", back_populates="receipts")
    items = db.relationship("PurchaseReceiptItem", back_populates="receipt", cascade="all, delete-orphan")


class PurchaseReceiptItem(db.Model):
    __tablename__ = "purchase_receipt_items"

    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey("purchase_receipts.id"), nullable=False)
    purchase_order_item_id = db.Column(db.Integer, db.ForeignKey("purchase_order_items.id"), nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)

    receipt = db.relationship("PurchaseReceipt", back_populates="items")
