import os

from flask import Blueprint, request, jsonify, send_from_directory, current_app

from app.extensions import db
from app.models.catalog import Product, UnitConversion
from app.services import barcode_service
from app.services.audit import log_action
from app.services.auth import login_required, permission_required, current_user
from app.services.permissions import PERM_CONFIGURACOES

bp = Blueprint("api_catalog", __name__, url_prefix="/api/products")


def _serialize_product(p: Product):
    return {
        "id": p.id,
        "sku": p.sku,
        "barcode": p.barcode,
        "name": p.name,
        "category": p.category,
        "base_unit": p.base_unit,
        "cost_price": str(p.cost_price),
        "sale_price": str(p.sale_price),
        "min_stock": str(p.min_stock),
        "conversions": [
            {"unit": c.unit, "factor_to_base": str(c.factor_to_base)} for c in p.conversions
        ],
    }


@bp.get("")
@login_required
def list_products():
    query = Product.query.filter_by(is_active=True)
    search = request.args.get("q")
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(Product.name.ilike(like), Product.sku.ilike(like), Product.barcode.ilike(like)))
    products = query.order_by(Product.name).limit(200).all()
    return jsonify({"products": [_serialize_product(p) for p in products]})


@bp.get("/<int:product_id>")
@login_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({"product": _serialize_product(product)})


@bp.post("")
@permission_required(PERM_CONFIGURACOES)
def create_product():
    data = request.get_json(silent=True) or {}
    for field in ("sku", "name", "base_unit"):
        if not data.get(field):
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400

    product = Product(
        sku=data["sku"],
        barcode=data.get("barcode"),
        name=data["name"],
        description=data.get("description"),
        category=data.get("category"),
        base_unit=data["base_unit"],
        cost_price=data.get("cost_price", 0),
        sale_price=data.get("sale_price", 0),
        min_stock=data.get("min_stock", 0),
    )
    db.session.add(product)
    db.session.flush()

    for conv in data.get("conversions", []):
        db.session.add(
            UnitConversion(
                product_id=product.id,
                unit=conv["unit"],
                factor_to_base=conv["factor_to_base"],
            )
        )

    log_action(current_user().company_id, current_user(), "produto.criado", f"{product.sku} - {product.name}")
    db.session.commit()
    return jsonify({"product": _serialize_product(product)}), 201


@bp.post("/<int:product_id>/barcode")
@permission_required(PERM_CONFIGURACOES)
def generate_barcode(product_id):
    product = Product.query.get_or_404(product_id)
    filename = barcode_service.generate_barcode(product)
    db.session.commit()
    return jsonify(
        {"product": _serialize_product(product), "barcode_url": f"/api/products/barcodes/{filename}"}
    ), 201


@bp.get("/barcodes/<path:filename>")
def serve_barcode(filename):
    return send_from_directory(current_app.config["BARCODE_FOLDER"], filename)
