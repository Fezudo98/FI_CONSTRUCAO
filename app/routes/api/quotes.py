from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.sales import Quote
from app.services import quotes as quotes_service
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_ORCAMENTOS
from app.services.errors import ServiceError

bp = Blueprint("api_quotes", __name__, url_prefix="/api/quotes")


def _serialize(q: Quote):
    return {
        "id": q.id,
        "customer_id": q.customer_id,
        "customer_name": q.customer_name,
        "customer_document": q.customer_document,
        "customer_phone": q.customer_phone,
        "status": q.status,
        "total": str(q.total),
        "valid_until": q.valid_until.isoformat() if q.valid_until else None,
        "has_order": q.order is not None,
        "items": [
            {
                "product_id": i.product_id,
                "unit": i.unit,
                "quantity": str(i.quantity),
                "unit_price": str(i.unit_price),
                "total": str(i.total),
            }
            for i in q.items
        ],
    }


@bp.get("")
@permission_required(PERM_ORCAMENTOS)
def list_quotes():
    user = current_user()
    status = request.args.get("status")
    query = Quote.query.filter_by(company_id=user.company_id)
    if status:
        query = query.filter_by(status=status)
    quotes = query.order_by(Quote.id.desc()).limit(200).all()
    return jsonify({"quotes": [_serialize(q) for q in quotes]})


@bp.post("")
@permission_required(PERM_ORCAMENTOS)
def create_quote():
    user = current_user()
    data = request.get_json(silent=True) or {}
    try:
        quote = quotes_service.create_quote(
            user.company_id, user.id,
            data.get("customer_name"),
            data.get("items", []),
            customer_document=data.get("customer_document"),
            customer_phone=data.get("customer_phone"),
            customer_id=data.get("customer_id"),
        )
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"quote": _serialize(quote)}), 201


def _get_quote_or_404(quote_id, user):
    quote = db.session.get(Quote, quote_id)
    if quote is None or quote.company_id != user.company_id:
        return None
    return quote


@bp.post("/<int:quote_id>/send")
@permission_required(PERM_ORCAMENTOS)
def send_quote(quote_id):
    user = current_user()
    quote = _get_quote_or_404(quote_id, user)
    if quote is None:
        return jsonify({"error": "Orçamento não encontrado."}), 404
    try:
        quotes_service.send_quote(quote)
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"quote": _serialize(quote)})


@bp.post("/<int:quote_id>/approve")
@permission_required(PERM_ORCAMENTOS)
def approve_quote(quote_id):
    user = current_user()
    quote = _get_quote_or_404(quote_id, user)
    if quote is None:
        return jsonify({"error": "Orçamento não encontrado."}), 404
    try:
        quotes_service.approve_quote(quote)
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"quote": _serialize(quote)})


@bp.post("/<int:quote_id>/reject")
@permission_required(PERM_ORCAMENTOS)
def reject_quote(quote_id):
    user = current_user()
    quote = _get_quote_or_404(quote_id, user)
    if quote is None:
        return jsonify({"error": "Orçamento não encontrado."}), 404
    try:
        quotes_service.reject_quote(quote)
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"quote": _serialize(quote)})


@bp.post("/<int:quote_id>/convert")
@permission_required(PERM_ORCAMENTOS)
def convert_quote(quote_id):
    user = current_user()
    quote = _get_quote_or_404(quote_id, user)
    if quote is None:
        return jsonify({"error": "Orçamento não encontrado."}), 404

    data = request.get_json(silent=True) or {}
    location_id = data.get("location_id")
    if not location_id:
        return jsonify({"error": "Campo obrigatório: location_id"}), 400

    try:
        order = quotes_service.convert_quote_to_order(
            quote, user.id, location_id, is_delivery=data.get("is_delivery", False)
        )
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"order_id": order.id}), 201
