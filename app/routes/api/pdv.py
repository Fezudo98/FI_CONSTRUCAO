from flask import Blueprint, request, jsonify

from app.extensions import db
from app.services import pdv
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_PDV
from app.services.errors import ServiceError

bp = Blueprint("api_pdv", __name__, url_prefix="/api/pdv")


@bp.get("/cash-session")
@permission_required(PERM_PDV)
def get_cash_session():
    user = current_user()
    session_obj = pdv.get_open_cash_session(user.company_id)
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
        session_obj = pdv.open_cash_session(user.company_id, user.id, data.get("opening_amount", 0))
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

    cash_session = pdv.get_open_cash_session(user.company_id)
    if cash_session is None:
        return jsonify({"error": "Nenhum caixa aberto. Abra o caixa antes de vender."}), 400

    location_id = data.get("location_id")
    if not location_id:
        return jsonify({"error": "Campo obrigatório: location_id"}), 400

    try:
        sale = pdv.create_sale(
            user.company_id,
            user.id,
            cash_session.id,
            location_id,
            data.get("items", []),
            data.get("payments", []),
            customer_name=data.get("customer_name"),
            customer_document=data.get("customer_document"),
        )
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify({"sale": {"id": sale.id, "total": str(sale.total)}}), 201
