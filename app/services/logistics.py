"""Entregas: agendamento, avanço de status e registro de ocorrências."""
from app.extensions import db
from app.models.logistics import (
    Delivery,
    DeliveryOccurrence,
    DELIVERY_SCHEDULED,
    DELIVERY_IN_ROUTE,
    DELIVERY_COMPLETED,
    DELIVERY_FAILED,
)
from app.models.sales import Order, ORDER_DELIVERED
from app.services.errors import ServiceError

_NEXT_STATUS = {
    DELIVERY_SCHEDULED: DELIVERY_IN_ROUTE,
    DELIVERY_IN_ROUTE: DELIVERY_COMPLETED,
}


def schedule_delivery(order: Order, address, vehicle_id=None, driver_id=None, scheduled_at=None) -> Delivery:
    if not order.is_delivery:
        raise ServiceError("Este pedido não está marcado como entrega.")
    if order.delivery is not None:
        raise ServiceError("Este pedido já tem uma entrega agendada.")

    delivery = Delivery(
        order_id=order.id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        address=address,
        scheduled_at=scheduled_at,
        status=DELIVERY_SCHEDULED,
    )
    db.session.add(delivery)
    return delivery


def advance_delivery_status(delivery: Delivery) -> Delivery:
    next_status = _NEXT_STATUS.get(delivery.status)
    if next_status is None:
        raise ServiceError(f"Entrega em status '{delivery.status}' não pode avançar.")

    delivery.status = next_status
    if next_status == DELIVERY_COMPLETED:
        delivery.order.status = ORDER_DELIVERED
    return delivery


def mark_delivery_failed(delivery: Delivery) -> Delivery:
    if delivery.status == DELIVERY_COMPLETED:
        raise ServiceError("Esta entrega já foi concluída.")
    delivery.status = DELIVERY_FAILED
    return delivery


def add_occurrence(delivery: Delivery, kind, description, user_id) -> DeliveryOccurrence:
    occurrence = DeliveryOccurrence(
        delivery_id=delivery.id, reported_by_id=user_id, kind=kind, description=description
    )
    db.session.add(occurrence)
    return occurrence
