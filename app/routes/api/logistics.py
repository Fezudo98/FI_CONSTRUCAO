from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.logistics import Carrier, Vehicle, Driver, Delivery
from app.models.sales import Order
from app.services import logistics as logistics_service
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_ENTREGAS
from app.services.errors import ServiceError

bp = Blueprint("api_logistics", __name__, url_prefix="/api/logistics")


@bp.get("/carriers")
@permission_required(PERM_ENTREGAS)
def list_carriers():
    user = current_user()
    carriers = Carrier.query.filter_by(company_id=user.company_id, is_active=True).order_by(Carrier.name).all()
    return jsonify({"carriers": [{"id": c.id, "name": c.name, "is_own_fleet": c.is_own_fleet} for c in carriers]})


@bp.post("/carriers")
@permission_required(PERM_ENTREGAS)
def create_carrier():
    user = current_user()
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Campo obrigatório: name"}), 400
    carrier = Carrier(company_id=user.company_id, name=data["name"], is_own_fleet=data.get("is_own_fleet", True))
    db.session.add(carrier)
    db.session.commit()
    return jsonify({"carrier": {"id": carrier.id, "name": carrier.name}}), 201


@bp.get("/vehicles")
@permission_required(PERM_ENTREGAS)
def list_vehicles():
    user = current_user()
    vehicles = (
        Vehicle.query.join(Carrier)
        .filter(Carrier.company_id == user.company_id, Vehicle.is_active.is_(True))
        .order_by(Vehicle.plate)
        .all()
    )
    return jsonify({"vehicles": [{"id": v.id, "plate": v.plate, "model": v.model} for v in vehicles]})


@bp.post("/vehicles")
@permission_required(PERM_ENTREGAS)
def create_vehicle():
    data = request.get_json(silent=True) or {}
    if not data.get("carrier_id") or not data.get("plate"):
        return jsonify({"error": "Campos obrigatórios: carrier_id, plate"}), 400
    vehicle = Vehicle(carrier_id=data["carrier_id"], plate=data["plate"], model=data.get("model"))
    db.session.add(vehicle)
    db.session.commit()
    return jsonify({"vehicle": {"id": vehicle.id, "plate": vehicle.plate}}), 201


@bp.get("/drivers")
@permission_required(PERM_ENTREGAS)
def list_drivers():
    user = current_user()
    drivers = (
        Driver.query.join(Carrier)
        .filter(Carrier.company_id == user.company_id, Driver.is_active.is_(True))
        .order_by(Driver.name)
        .all()
    )
    return jsonify({"drivers": [{"id": d.id, "name": d.name} for d in drivers]})


@bp.post("/drivers")
@permission_required(PERM_ENTREGAS)
def create_driver():
    data = request.get_json(silent=True) or {}
    if not data.get("carrier_id") or not data.get("name"):
        return jsonify({"error": "Campos obrigatórios: carrier_id, name"}), 400
    driver = Driver(carrier_id=data["carrier_id"], name=data["name"], phone=data.get("phone"))
    db.session.add(driver)
    db.session.commit()
    return jsonify({"driver": {"id": driver.id, "name": driver.name}}), 201


def _serialize_delivery(d: Delivery):
    return {
        "id": d.id,
        "order_id": d.order_id,
        "customer_name": d.order.customer_name if d.order else None,
        "vehicle_id": d.vehicle_id,
        "driver_id": d.driver_id,
        "address": d.address,
        "status": d.status,
        "scheduled_at": d.scheduled_at.isoformat() if d.scheduled_at else None,
        "occurrences": [
            {"id": o.id, "kind": o.kind, "description": o.description} for o in d.occurrences
        ],
    }


@bp.get("/deliveries")
@permission_required(PERM_ENTREGAS)
def list_deliveries():
    user = current_user()
    deliveries = (
        Delivery.query.join(Order).filter(Order.company_id == user.company_id).order_by(Delivery.id.desc()).all()
    )
    return jsonify({"deliveries": [_serialize_delivery(d) for d in deliveries]})


@bp.post("/deliveries")
@permission_required(PERM_ENTREGAS)
def create_delivery():
    user = current_user()
    data = request.get_json(silent=True) or {}
    order = db.session.get(Order, data.get("order_id"))
    if order is None or order.company_id != user.company_id:
        return jsonify({"error": "Pedido não encontrado."}), 404

    try:
        delivery = logistics_service.schedule_delivery(
            order, data.get("address"), vehicle_id=data.get("vehicle_id"), driver_id=data.get("driver_id"),
        )
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"delivery": _serialize_delivery(delivery)}), 201


@bp.post("/deliveries/<int:delivery_id>/advance")
@permission_required(PERM_ENTREGAS)
def advance_delivery(delivery_id):
    user = current_user()
    delivery = db.session.get(Delivery, delivery_id)
    if delivery is None or delivery.order.company_id != user.company_id:
        return jsonify({"error": "Entrega não encontrada."}), 404
    try:
        logistics_service.advance_delivery_status(delivery)
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"delivery": _serialize_delivery(delivery)})


@bp.post("/deliveries/<int:delivery_id>/occurrences")
@permission_required(PERM_ENTREGAS)
def add_occurrence(delivery_id):
    user = current_user()
    delivery = db.session.get(Delivery, delivery_id)
    if delivery is None or delivery.order.company_id != user.company_id:
        return jsonify({"error": "Entrega não encontrada."}), 404

    data = request.get_json(silent=True) or {}
    if not data.get("kind"):
        return jsonify({"error": "Campo obrigatório: kind"}), 400

    logistics_service.add_occurrence(delivery, data["kind"], data.get("description"), user.id)
    db.session.commit()
    return jsonify({"delivery": _serialize_delivery(delivery)}), 201
