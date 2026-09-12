from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.purchasing import Supplier, PurchaseOrder
from app.services import purchasing as purchasing_service
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_COMPRAS
from app.services.errors import ServiceError

bp = Blueprint("api_purchasing", __name__, url_prefix="/api/purchasing")


def _serialize_supplier(s: Supplier):
    return {"id": s.id, "name": s.name, "document": s.document, "phone": s.phone, "email": s.email}


def _serialize_po(po: PurchaseOrder):
    return {
        "id": po.id,
        "supplier_id": po.supplier_id,
        "supplier_name": po.supplier.name if po.supplier else None,
        "status": po.status,
        "total": str(po.total),
        "items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "unit": i.unit,
                "quantity": str(i.quantity),
                "unit_price": str(i.unit_price),
                "quantity_received": str(i.quantity_received),
            }
            for i in po.items
        ],
    }


@bp.get("/suppliers")
@permission_required(PERM_COMPRAS)
def list_suppliers():
    user = current_user()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return jsonify({"suppliers": [_serialize_supplier(s) for s in suppliers]})


@bp.post("/suppliers")
@permission_required(PERM_COMPRAS)
def create_supplier():
    user = current_user()
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Campo obrigatório: name"}), 400

    supplier = Supplier(
        name=data["name"],
        document=data.get("document"),
        phone=data.get("phone"),
        email=data.get("email"),
    )
    db.session.add(supplier)
    db.session.commit()
    return jsonify({"supplier": _serialize_supplier(supplier)}), 201


@bp.get("/orders")
@permission_required(PERM_COMPRAS)
def list_purchase_orders():
    user = current_user()
    status = request.args.get("status")
    query = PurchaseOrder.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(PurchaseOrder.id.desc()).limit(200).all()
    return jsonify({"purchase_orders": [_serialize_po(po) for po in orders]})


@bp.post("/orders")
@permission_required(PERM_COMPRAS)
def create_purchase_order():
    user = current_user()
    data = request.get_json(silent=True) or {}
    supplier_id = data.get("supplier_id")
    if not supplier_id:
        return jsonify({"error": "Campo obrigatório: supplier_id"}), 400

    try:
        po = purchasing_service.create_purchase_order(user.id, supplier_id, data.get("items", []))
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"purchase_order": _serialize_po(po)}), 201


@bp.post("/orders/<int:po_id>/receive")
@permission_required(PERM_COMPRAS)
def receive_purchase_order(po_id):
    user = current_user()
    po = db.session.get(PurchaseOrder, po_id)
    if po is None:
        return jsonify({"error": "Pedido de compra não encontrado."}), 404

    data = request.get_json(silent=True) or {}
    location_id = data.get("location_id")
    if not location_id:
        return jsonify({"error": "Campo obrigatório: location_id"}), 400

    try:
        receipt = purchasing_service.receive_purchase_order(
            po, data.get("items", []), location_id, user.id, note=data.get("note")
        )
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"receipt_id": receipt.id, "purchase_order": _serialize_po(po)}), 201
