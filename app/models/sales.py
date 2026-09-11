"""PDV/caixa (venda imediata) e orçamentos/pedidos (venda com acompanhamento)."""
from app.extensions import db
from app.models.base import TimestampMixin

# ---------- Caixa e PDV ----------

CASH_OPEN = "open"
CASH_CLOSED = "closed"


class CashSession(db.Model, TimestampMixin):
    __tablename__ = "cash_sessions"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    opened_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    closed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    opening_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    closing_amount = db.Column(db.Numeric(12, 2))
    opened_at = db.Column(db.DateTime(timezone=True))
    closed_at = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(10), nullable=False, default=CASH_OPEN)

    sales = db.relationship("Sale", back_populates="cash_session")


SALE_STATUS_COMPLETED = "completed"
SALE_STATUS_CANCELLED = "cancelled"


class Sale(db.Model, TimestampMixin):
    """Venda de pronta entrega no balcão (PDV)."""
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    cash_session_id = db.Column(db.Integer, db.ForeignKey("cash_sessions.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    customer_name = db.Column(db.String(150))
    customer_document = db.Column(db.String(20))

    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(15), nullable=False, default=SALE_STATUS_COMPLETED)

    cash_session = db.relationship("CashSession", back_populates="sales")
    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(db.Model):
    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    unit = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    unit_price = db.Column(db.Numeric(12, 4), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)

    sale = db.relationship("Sale", back_populates="items")


PAYMENT_METHODS = ["dinheiro", "pix", "cartao_debito", "cartao_credito", "boleto", "transferencia"]


class Payment(db.Model, TimestampMixin):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    method = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)

    sale = db.relationship("Sale", back_populates="payments")


# ---------- Orçamentos e pedidos ----------

QUOTE_DRAFT = "draft"
QUOTE_SENT = "sent"
QUOTE_APPROVED = "approved"
QUOTE_REJECTED = "rejected"
QUOTE_CONVERTED = "converted"


class Quote(db.Model, TimestampMixin):
    __tablename__ = "quotes"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    customer_name = db.Column(db.String(150), nullable=False)
    customer_document = db.Column(db.String(20))
    customer_phone = db.Column(db.String(20))

    status = db.Column(db.String(15), nullable=False, default=QUOTE_DRAFT)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    valid_until = db.Column(db.Date)

    items = db.relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    order = db.relationship("Order", back_populates="quote", uselist=False)


class QuoteItem(db.Model):
    __tablename__ = "quote_items"

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey("quotes.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    unit = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    unit_price = db.Column(db.Numeric(12, 4), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)

    quote = db.relationship("Quote", back_populates="items")


ORDER_RESERVED = "reserved"
ORDER_SEPARATED = "separated"
ORDER_PICKED_UP = "picked_up"
ORDER_DELIVERED = "delivered"
ORDER_CANCELLED = "cancelled"
ORDER_STATUS_FLOW = [ORDER_RESERVED, ORDER_SEPARATED, ORDER_PICKED_UP, ORDER_DELIVERED]


class Order(db.Model, TimestampMixin):
    """Pedido: nasce de um orçamento aprovado ou é criado direto, reserva
    estoque e é acompanhado até a retirada/entrega."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey("quotes.id"), unique=True, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    customer_name = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(15), nullable=False, default=ORDER_RESERVED)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    is_delivery = db.Column(db.Boolean, default=False, nullable=False)

    quote = db.relationship("Quote", back_populates="order")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery = db.relationship("Delivery", back_populates="order", uselist=False)


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    unit = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    unit_price = db.Column(db.Numeric(12, 4), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
