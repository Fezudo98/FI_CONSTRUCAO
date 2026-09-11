"""Pedidos: criação (direta ou a partir de orçamento), reserva de estoque e
acompanhamento por status até a retirada/entrega."""
from decimal import Decimal

from app.extensions import db
from app.models.catalog import Product
from app.models.sales import (
    Order,
    OrderItem,
    ORDER_RESERVED,
    ORDER_SEPARATED,
    ORDER_PICKED_UP,
    ORDER_DELIVERED,
    ORDER_CANCELLED,
)
from app.services import inventory
from app.services.errors import ServiceError

_NEXT_STATUS = {
    ORDER_RESERVED: ORDER_SEPARATED,
    ORDER_SEPARATED: ORDER_PICKED_UP,
    ORDER_PICKED_UP: ORDER_DELIVERED,
}


def create_order(company_id, user_id, customer_name, items, location_id, is_delivery=False,
                  quote_id=None, customer_id=None) -> Order:
    if not items:
        raise ServiceError("O pedido precisa ter ao menos um item.")

    order = Order(
        company_id=company_id,
        quote_id=quote_id,
        created_by_id=user_id,
        location_id=location_id,
        customer_id=customer_id,
        customer_name=customer_name,
        status=ORDER_RESERVED,
        total=Decimal(0),
        is_delivery=is_delivery,
    )
    db.session.add(order)
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
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                unit=item["unit"],
                quantity=quantity,
                unit_price=unit_price,
                total=line_total,
            )
        )

        from app.services.units import to_base_unit

        base_quantity = to_base_unit(product, item["unit"], quantity)
        inventory.reserve_stock(
            company_id, product, location_id, base_quantity,
            reference_type="order", reference_id=order.id, user_id=user_id,
        )

    order.total = total
    return order


def _order_base_quantities(order: Order):
    """Retorna [(product, base_quantity)] de cada item do pedido."""
    from app.services.units import to_base_unit

    result = []
    for item in order.items:
        product = db.session.get(Product, item.product_id)
        result.append((product, to_base_unit(product, item.unit, item.quantity)))
    return result


def advance_order_status(order: Order, user_id):
    """Avança o pedido para o próximo status do fluxo. Ao chegar em
    'picked_up', confirma a baixa física do estoque reservado."""
    next_status = _NEXT_STATUS.get(order.status)
    if next_status is None:
        raise ServiceError(f"Pedido em status '{order.status}' não pode avançar.")

    if next_status == ORDER_PICKED_UP:
        for product, base_quantity in _order_base_quantities(order):
            inventory.fulfill_reservation(
                order.company_id, product, order.location_id, base_quantity,
                reference_type="order", reference_id=order.id, user_id=user_id,
            )

    if next_status == ORDER_DELIVERED and not order.is_delivery:
        raise ServiceError("Este pedido não é de entrega; a retirada já é o status final.")

    order.status = next_status
    return order


def cancel_order(order: Order, user_id):
    if order.status not in (ORDER_RESERVED, ORDER_SEPARATED):
        raise ServiceError("Só é possível cancelar pedidos ainda não retirados.")

    for product, base_quantity in _order_base_quantities(order):
        inventory.release_reservation(
            order.company_id, product, order.location_id, base_quantity,
            reference_type="order", reference_id=order.id, user_id=user_id,
        )

    order.status = ORDER_CANCELLED
    return order
