"""Orçamentos: criação, aprovação/rejeição e conversão em pedido."""
from decimal import Decimal

from app.extensions import db
from app.models.catalog import Product
from app.models.sales import Quote, QuoteItem, QUOTE_DRAFT, QUOTE_SENT, QUOTE_APPROVED, QUOTE_REJECTED, QUOTE_CONVERTED
from app.services.errors import ServiceError
from app.services import orders as orders_service


def create_quote(company_id, user_id, customer_name, items, customer_document=None,
                  customer_phone=None, valid_until=None, customer_id=None) -> Quote:
    if not items:
        raise ServiceError("O orçamento precisa ter ao menos um item.")

    quote = Quote(
        company_id=company_id,
        created_by_id=user_id,
        customer_id=customer_id,
        customer_name=customer_name,
        customer_document=customer_document,
        customer_phone=customer_phone,
        valid_until=valid_until,
        status=QUOTE_DRAFT,
        total=Decimal(0),
    )
    db.session.add(quote)
    db.session.flush()

    total = Decimal(0)
    for item in items:
        product = db.session.get(Product, item["product_id"])
        if product is None:
            raise ServiceError(f"Produto {item['product_id']} não encontrado.")

        quantity = Decimal(str(item["quantity"]))
        unit_price = Decimal(str(item["unit_price"]))
        line_total = (quantity * unit_price).quantize(Decimal("0.01"))
        total += line_total

        db.session.add(
            QuoteItem(
                quote_id=quote.id,
                product_id=product.id,
                unit=item["unit"],
                quantity=quantity,
                unit_price=unit_price,
                total=line_total,
            )
        )

    quote.total = total
    return quote


def _transition(quote: Quote, allowed_from, to_status):
    if quote.status not in allowed_from:
        raise ServiceError(f"Orçamento não pode ir de '{quote.status}' para '{to_status}'.")
    quote.status = to_status


def send_quote(quote: Quote):
    _transition(quote, [QUOTE_DRAFT], QUOTE_SENT)
    return quote


def approve_quote(quote: Quote):
    _transition(quote, [QUOTE_SENT, QUOTE_DRAFT], QUOTE_APPROVED)
    return quote


def reject_quote(quote: Quote):
    _transition(quote, [QUOTE_SENT, QUOTE_DRAFT], QUOTE_REJECTED)
    return quote


def convert_quote_to_order(quote: Quote, user_id, location_id, is_delivery=False):
    if quote.status != QUOTE_APPROVED:
        raise ServiceError("Só é possível converter orçamentos aprovados em pedido.")
    if quote.order is not None:
        raise ServiceError("Este orçamento já foi convertido em pedido.")

    items = [
        {"product_id": i.product_id, "unit": i.unit, "quantity": i.quantity, "unit_price": i.unit_price}
        for i in quote.items
    ]
    order = orders_service.create_order(
        quote.company_id, user_id, quote.customer_name, items, location_id,
        is_delivery=is_delivery, quote_id=quote.id, customer_id=quote.customer_id,
    )
    quote.status = QUOTE_CONVERTED
    return order
