from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.sales import Order
from app.services import orders as orders_service
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_PEDIDOS
from app.services.errors import ServiceError

bp = Blueprint("api_orders", __name__, url_prefix="/api/orders")


def _serialize(o: Order):
    return {
        "id": o.id,
        "customer_name": o.customer_name,
        "status": o.status,
        "total": str(o.total),
        "is_delivery": o.is_delivery,
        "location_id": o.location_id,
        "quote_id": o.quote_id,
        "has_delivery": o.delivery is not None,
        "items": [
            {
                "product_id": i.product_id,
                "unit": i.unit,
                "quantity": str(i.quantity),
                "unit_price": str(i.unit_price),
                "total": str(i.total),
            }
            for i in o.items
        ],
    }


@bp.get("")
@permission_required(PERM_PEDIDOS)
def list_orders():
    user = current_user()
    status = request.args.get("status")
    query = Order.query.filter_by(company_id=user.company_id)
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.id.desc()).limit(200).all()
    return jsonify({"orders": [_serialize(o) for o in orders]})


@bp.post("")
@permission_required(PERM_PEDIDOS)
def create_order():
    user = current_user()
    data = request.get_json(silent=True) or {}
    location_id = data.get("location_id")
    if not location_id:
        return jsonify({"error": "Campo obrigatório: location_id"}), 400

    try:
        order = orders_service.create_order(
            user.company_id, user.id,
            data.get("customer_name"),
            data.get("items", []),
            location_id,
            is_delivery=data.get("is_delivery", False),
        )
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"order": _serialize(order)}), 201


def _get_order_or_404(order_id, user):
    order = db.session.get(Order, order_id)
    if order is None or order.company_id != user.company_id:
        return None
    return order


@bp.post("/<int:order_id>/advance")
@permission_required(PERM_PEDIDOS)
def advance_order(order_id):
    user = current_user()
    order = _get_order_or_404(order_id, user)
    if order is None:
        return jsonify({"error": "Pedido não encontrado."}), 404
    try:
        orders_service.advance_order_status(order, user.id)
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"order": _serialize(order)})


@bp.post("/<int:order_id>/cancel")
@permission_required(PERM_PEDIDOS)
def cancel_order(order_id):
    user = current_user()
    order = _get_order_or_404(order_id, user)
    if order is None:
        return jsonify({"error": "Pedido não encontrado."}), 404
    try:
        orders_service.cancel_order(order, user.id)
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"order": _serialize(order)})
