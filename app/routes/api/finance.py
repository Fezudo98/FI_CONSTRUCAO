from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.finance import Payable
from app.services import finance as finance_service
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_FINANCEIRO
from app.services.errors import ServiceError

bp = Blueprint("api_finance", __name__, url_prefix="/api/finance")


def _serialize(p: Payable):
    return {
        "id": p.id,
        "supplier_id": p.supplier_id,
        "supplier_name": p.supplier.name if p.supplier else None,
        "description": p.description,
        "amount": str(p.amount),
        "amount_paid": str(p.amount_paid),
        "amount_open": str(p.amount_open),
        "due_date": p.due_date.isoformat() if p.due_date else None,
        "status": p.status,
    }


@bp.get("/payables")
@permission_required(PERM_FINANCEIRO)
def list_payables():
    user = current_user()
    status = request.args.get("status")
    query = Payable.query.filter_by(company_id=user.company_id)
    if status:
        query = query.filter_by(status=status)
    payables = query.order_by(Payable.due_date).limit(200).all()
    return jsonify({"payables": [_serialize(p) for p in payables]})


@bp.post("/payables/<int:payable_id>/settle")
@permission_required(PERM_FINANCEIRO)
def settle_payable(payable_id):
    user = current_user()
    payable = db.session.get(Payable, payable_id)
    if payable is None or payable.company_id != user.company_id:
        return jsonify({"error": "Conta a pagar não encontrada."}), 404

    data = request.get_json(silent=True) or {}
    try:
        finance_service.settle_payable(payable, user.id, data.get("amount"), method=data.get("method"))
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"payable": _serialize(payable)})
