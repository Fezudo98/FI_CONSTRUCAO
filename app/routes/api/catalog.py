import os

from flask import Blueprint, request, jsonify, send_from_directory, current_app

from app.extensions import db
from app.models.catalog import Product, UnitConversion
from app.services import barcode_service, product_image
from app.services.audit import log_action
from app.services.auth import login_required, permission_required, current_user
from app.services.permissions import PERM_CONFIGURACOES
from app.services.errors import ServiceError

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
        "image_url": f"/api/products/uploads/{p.image_filename}" if p.image_filename else None,
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


@bp.get("/lookup")
@login_required
def lookup_product():
    """Busca exata por SKU ou código de barras — usada pelo leitor de
    código de barras (PDV e ajuste rápido de estoque), onde o texto lido
    precisa resolver para um único produto, sem ambiguidade de busca parcial."""
    code = (request.args.get("code") or "").strip()
    if not code:
        return jsonify({"error": "Informe o código."}), 400

    product = Product.query.filter(
        Product.is_active.is_(True), db.or_(Product.sku == code, Product.barcode == code)
    ).first()
    if product is None:
        return jsonify({"error": "Nenhum produto encontrado para este código."}), 404

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


@bp.post("/<int:product_id>/image")
@permission_required(PERM_CONFIGURACOES)
def upload_product_image(product_id):
    product = Product.query.get_or_404(product_id)
    file_storage = request.files.get("image")
    try:
        product_image.save_product_image(product, file_storage)
        log_action(current_user().company_id, current_user(), "produto.imagem_atualizada", product.sku)
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"product": _serialize_product(product)}), 201


@bp.get("/uploads/<path:filename>")
@login_required
def serve_product_image(filename):
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "products")
    return send_from_directory(folder, filename)
