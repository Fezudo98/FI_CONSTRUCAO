"""Cadastro de clientes. Exclusão só é permitida se o cliente nunca teve
movimento (venda/orçamento/pedido); caso contrário, apenas inativa — preserva
o histórico de vendas já registrado."""
from app.extensions import db
from app.models.customer import Customer
from app.models.sales import Sale, Quote, Order
from app.services.errors import ServiceError


def create_customer(company_id, data) -> Customer:
    if not data.get("name"):
        raise ServiceError("Campo obrigatório: name")

    customer = Customer(
        company_id=company_id,
        name=data["name"],
        document=data.get("document"),
        phone=data.get("phone"),
        email=data.get("email"),
        address_street=data.get("address_street"),
        address_number=data.get("address_number"),
        address_district=data.get("address_district"),
        address_city=data.get("address_city"),
        address_state=data.get("address_state"),
        address_zip=data.get("address_zip"),
        address_complement=data.get("address_complement"),
        note=data.get("note"),
    )
    db.session.add(customer)
    return customer


def update_customer(customer: Customer, data):
    for field in (
        "name", "document", "phone", "email", "address_street", "address_number",
        "address_district", "address_city", "address_state", "address_zip",
        "address_complement", "note",
    ):
        if field in data:
            setattr(customer, field, data[field])
    return customer


def _has_history(customer: Customer) -> bool:
    return (
        Sale.query.filter_by(customer_id=customer.id).first() is not None
        or Quote.query.filter_by(customer_id=customer.id).first() is not None
        or Order.query.filter_by(customer_id=customer.id).first() is not None
    )


def delete_customer(customer: Customer):
    if _has_history(customer):
        customer.is_active = False
    else:
        db.session.delete(customer)
