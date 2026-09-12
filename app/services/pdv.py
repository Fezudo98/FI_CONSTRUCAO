"""Frente de caixa: abertura/fechamento de caixa e venda de pronta entrega."""
from datetime import datetime, timezone
from decimal import Decimal

from app.extensions import db
from app.models.sales import CashSession, Sale, SaleItem, Payment, CASH_OPEN, CASH_CLOSED
from app.models.catalog import Product
from app.services import inventory
from app.services.units import to_base_unit
from app.services.errors import ServiceError


def open_cash_session(company_id, user_id, opening_amount: Decimal) -> CashSession:
    existing = CashSession.query.filter_by(company_id=company_id, status=CASH_OPEN).first()
    if existing is not None:
        raise ServiceError("Já existe um caixa aberto para esta empresa.")

    session = CashSession(
        company_id=company_id,
        opened_by_id=user_id,
        opening_amount=opening_amount,
        opened_at=datetime.now(timezone.utc),
        status=CASH_OPEN,
    )
    db.session.add(session)
    db.session.flush()
    return session


def close_cash_session(session: CashSession, user_id, closing_amount: Decimal) -> CashSession:
    if session.status != CASH_OPEN:
        raise ServiceError("Este caixa já está fechado.")

    session.status = CASH_CLOSED
    session.closed_by_id = user_id
    session.closing_amount = closing_amount
    session.closed_at = datetime.now(timezone.utc)
    return session


def get_open_cash_session(company_id) -> CashSession | None:
    return CashSession.query.filter_by(company_id=company_id, status=CASH_OPEN).first()


def create_sale(company_id, user_id, cash_session_id, default_location_id, items, payments,
                 customer_name=None, customer_document=None, customer_id=None) -> Sale:
    """items: lista de {product_id, unit, quantity, unit_price}
    payments: lista de {method, amount}
    Dá baixa no estoque (default_location_id) e registra a venda."""
    if not items:
        raise ServiceError("A venda precisa ter ao menos um item.")

    sale = Sale(
        company_id=company_id,
        cash_session_id=cash_session_id,
        created_by_id=user_id,
        customer_id=customer_id,
        customer_name=customer_name,
        customer_document=customer_document,
        total=Decimal(0),
    )
    db.session.add(sale)
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
            SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                unit=item["unit"],
                quantity=quantity,
                unit_price=unit_price,
                total=line_total,
            )
        )

        base_quantity = to_base_unit(product, item["unit"], quantity)
        inventory.withdraw_stock(
            company_id, product, default_location_id, base_quantity,
            reference_type="sale", reference_id=sale.id, user_id=user_id,
        )

    payments_total = Decimal(0)
    for payment in payments:
        amount = Decimal(str(payment["amount"]))
        payments_total += amount
        db.session.add(
            Payment(
                sale_id=sale.id,
                method=payment["method"],
                amount=amount,
                card_reference=payment.get("card_reference"),
            )
        )

    if payments_total != total:
        raise ServiceError(
            f"Soma dos pagamentos (R$ {payments_total}) diferente do total da venda (R$ {total})."
        )

    sale.total = total
    return sale
