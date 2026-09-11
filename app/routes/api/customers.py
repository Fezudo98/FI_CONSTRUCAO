from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.customer import Customer
from app.services import customers as customers_service
from app.services.audit import log_action
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_CLIENTES
from app.services.errors import ServiceError

bp = Blueprint("api_customers", __name__, url_prefix="/api/customers")


def _serialize(c: Customer):
    return {
        "id": c.id,
        "name": c.name,
        "document": c.document,
        "phone": c.phone,
        "email": c.email,
        "address_street": c.address_street,
        "address_number": c.address_number,
        "address_district": c.address_district,
        "address_city": c.address_city,
        "address_state": c.address_state,
        "address_zip": c.address_zip,
        "address_complement": c.address_complement,
        "full_address": c.full_address(),
        "note": c.note,
    }


@bp.get("")
@permission_required(PERM_CLIENTES)
def list_customers():
    user = current_user()
    query = Customer.query.filter_by(company_id=user.company_id, is_active=True)
    search = request.args.get("q")
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Customer.name.ilike(like), Customer.document.ilike(like), Customer.phone.ilike(like))
        )
    customers = query.order_by(Customer.name).limit(200).all()
    return jsonify({"customers": [_serialize(c) for c in customers]})


@bp.get("/<int:customer_id>")
@permission_required(PERM_CLIENTES)
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify({"customer": _serialize(customer)})


@bp.post("")
@permission_required(PERM_CLIENTES)
def create_customer():
    user = current_user()
    data = request.get_json(silent=True) or {}
    try:
        customer = customers_service.create_customer(user.company_id, data)
        db.session.flush()
        log_action(user.company_id, user, "cliente.criado", f"{customer.name} (#{customer.id})")
        db.session.commit()
    except ServiceError as exc:
        db.session.rollback()
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"customer": _serialize(customer)}), 201


@bp.put("/<int:customer_id>")
@permission_required(PERM_CLIENTES)
def update_customer(customer_id):
    user = current_user()
    customer = Customer.query.get_or_404(customer_id)
    data = request.get_json(silent=True) or {}
    customers_service.update_customer(customer, data)
    log_action(user.company_id, user, "cliente.editado", f"{customer.name} (#{customer.id})")
    db.session.commit()
    return jsonify({"customer": _serialize(customer)})


@bp.delete("/<int:customer_id>")
@permission_required(PERM_CLIENTES)
def delete_customer(customer_id):
    user = current_user()
    customer = Customer.query.get_or_404(customer_id)
    name = customer.name
    customers_service.delete_customer(customer)
    log_action(user.company_id, user, "cliente.removido", f"{name} (#{customer_id})")
    db.session.commit()
    return jsonify({"ok": True})
