from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.catalog import Product
from app.models.inventory import StockLocation, StockBalance
from app.services import inventory
from app.services.audit import log_action
from app.services.auth import login_required, permission_required, current_user
from app.services.permissions import PERM_ESTOQUE_VER, PERM_ESTOQUE_AJUSTAR
from app.services.errors import ServiceError

bp = Blueprint("api_inventory", __name__, url_prefix="/api/inventory")


@bp.get("/locations")
@login_required
def list_locations():
    user = current_user()
    locations = StockLocation.query.order_by(StockLocation.code).all()
    return jsonify({"locations": [{"id": l.id, "code": l.code, "description": l.description} for l in locations]})


@bp.post("/locations")
@permission_required(PERM_ESTOQUE_AJUSTAR)
def create_location():
    user = current_user()
    data = request.get_json(silent=True) or {}
    if not data.get("code"):
        return jsonify({"error": "Campo obrigatório: code"}), 400

    location = StockLocation(code=data["code"], description=data.get("description"))
    db.session.add(location)
    db.session.commit()
    return jsonify({"location": {"id": location.id, "code": location.code}}), 201


@bp.get("/balance")
@permission_required(PERM_ESTOQUE_VER)
def get_balance():
    user = current_user()
    product_id = request.args.get("product_id", type=int)
    query = StockBalance.query
    if product_id:
        query = query.filter_by(product_id=product_id)

    balances = query.all()
    return jsonify(
        {
            "balances": [
                {
                    "product_id": b.product_id,
                    "location_id": b.location_id,
                    "lot_id": b.lot_id,
                    "quantity": str(b.quantity),
                    "reserved": str(b.reserved),
                    "available": str(b.available),
                }
                for b in balances
            ]
        }
    )


@bp.post("/adjust")
@permission_required(PERM_ESTOQUE_AJUSTAR)
def adjust():
    user = current_user()
    data = request.get_json(silent=True) or {}
    product = db.session.get(Product, data.get("product_id"))
    if product is None:
        return jsonify({"error": "Produto não encontrado."}), 404

    try:
        balance = inventory.adjust_stock(
            product,
            data["location_id"],
            data["new_quantity"],
            lot_id=data.get("lot_id"),
            note=data.get("note"),
            user_id=user.id,
        )
        log_action(
            user, "estoque.ajustado",
            f"{product.sku}: novo saldo {data['new_quantity']} (endereço #{data['location_id']})",
        )
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify({"balance": {"quantity": str(balance.quantity), "reserved": str(balance.reserved)}})
