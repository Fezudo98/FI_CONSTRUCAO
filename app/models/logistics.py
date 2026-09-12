"""Transportadoras, veículos, motoristas, cargas e ocorrências de entrega."""
from app.extensions import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class Carrier(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "carriers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    document = db.Column(db.String(20))
    is_own_fleet = db.Column(db.Boolean, default=True, nullable=False)


class Vehicle(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    carrier_id = db.Column(db.Integer, db.ForeignKey("carriers.id"), nullable=False)
    plate = db.Column(db.String(10), nullable=False)
    model = db.Column(db.String(100))
    capacity_kg = db.Column(db.Numeric(10, 2))


class Driver(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)
    carrier_id = db.Column(db.Integer, db.ForeignKey("carriers.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    license_number = db.Column(db.String(20))
    phone = db.Column(db.String(20))


DELIVERY_SCHEDULED = "scheduled"
DELIVERY_IN_ROUTE = "in_route"
DELIVERY_COMPLETED = "completed"
DELIVERY_FAILED = "failed"


class Delivery(db.Model, TimestampMixin):
    """Carga/entrega associada a um pedido (Order)."""
    __tablename__ = "deliveries"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True, nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"))
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"))

    address = db.Column(db.String(255))
    scheduled_at = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(15), nullable=False, default=DELIVERY_SCHEDULED)

    order = db.relationship("Order", back_populates="delivery")
    occurrences = db.relationship(
        "DeliveryOccurrence", back_populates="delivery", cascade="all, delete-orphan"
    )


class DeliveryOccurrence(db.Model, TimestampMixin):
    """Registro de eventos durante a entrega (ex.: atraso, avaria, recusa)."""
    __tablename__ = "delivery_occurrences"

    id = db.Column(db.Integer, primary_key=True)
    delivery_id = db.Column(db.Integer, db.ForeignKey("deliveries.id"), nullable=False)
    reported_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    kind = db.Column(db.String(40), nullable=False)  # 'atraso', 'avaria', 'recusa', 'outro'
    description = db.Column(db.String(255))

    delivery = db.relationship("Delivery", back_populates="occurrences")
