from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.sales import Sale
from app.services import pdv
from app.services.audit import log_action
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_PDV
from app.services.errors import ServiceError

bp = Blueprint("api_pdv", __name__, url_prefix="/api/pdv")


@bp.get("/cash-session")
@permission_required(PERM_PDV)
def get_cash_session():
    user = current_user()
    session_obj = pdv.get_open_cash_session()
    if session_obj is None:
        return jsonify({"cash_session": None})
    return jsonify(
        {
            "cash_session": {
                "id": session_obj.id,
                "opening_amount": str(session_obj.opening_amount),
                "opened_at": session_obj.opened_at.isoformat() if session_obj.opened_at else None,
            }
        }
    )


@bp.post("/cash-session/open")
@permission_required(PERM_PDV)
def open_cash_session():
    user = current_user()
    data = request.get_json(silent=True) or {}
    try:
        session_obj = pdv.open_cash_session(user.id, data.get("opening_amount", 0))
        log_action(user, "caixa.aberto", f"Abertura: R$ {data.get('opening_amount', 0)}")
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify({"cash_session": {"id": session_obj.id}}), 201


@bp.post("/cash-session/<int:session_id>/close")
@permission_required(PERM_PDV)
def close_cash_session(session_id):
    from app.models.sales import CashSession

    user = current_user()
    session_obj = CashSession.query.get_or_404(session_id)
    data = request.get_json(silent=True) or {}
    try:
        pdv.close_cash_session(session_obj, user.id, data.get("closing_amount", 0))
        log_action(user, "caixa.fechado", f"Fechamento: R$ {data.get('closing_amount', 0)}")
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify({"ok": True})


@bp.post("/sales")
@permission_required(PERM_PDV)
def create_sale():
    user = current_user()
    data = request.get_json(silent=True) or {}

    cash_session = pdv.get_open_cash_session()
    if cash_session is None:
        return jsonify({"error": "Nenhum caixa aberto. Abra o caixa antes de vender."}), 400

    location_id = data.get("location_id")
    if not location_id:
        return jsonify({"error": "Campo obrigatório: location_id"}), 400

    try:
        sale = pdv.create_sale(
            user.id,
            cash_session.id,
            location_id,
            data.get("items", []),
            data.get("payments", []),
            customer_name=data.get("customer_name"),
            customer_document=data.get("customer_document"),
            customer_id=data.get("customer_id"),
        )
        db.session.flush()
        log_action(user, "venda.registrada", f"Venda #{sale.id} - R$ {sale.total}")
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify({"sale": {"id": sale.id, "total": str(sale.total)}}), 201


@bp.get("/sales/<int:sale_id>")
@permission_required(PERM_PDV)
def get_sale(sale_id):
    user = current_user()
    sale = Sale.query.get_or_404(sale_id)
    return jsonify(
        {
            "sale": {
                "id": sale.id,
                "customer_name": sale.customer_name,
                "customer_document": sale.customer_document,
                "total": str(sale.total),
                "created_at": sale.created_at.isoformat(),
                "created_by": sale.created_by_id,
                "items": [
                    {
                        "product_name": item.product.name if item.product else "",
                        "unit": item.unit,
                        "quantity": str(item.quantity),
                        "unit_price": str(item.unit_price),
                        "total": str(item.total),
                    }
                    for item in sale.items
                ],
                "payments": [
                    {"method": p.method, "amount": str(p.amount), "card_reference": p.card_reference}
                    for p in sale.payments
                ],
            }
        }
    )
