"""Regras de estoque: saldo por endereço/lote, movimentações, reserva/liberação."""
from decimal import Decimal

from app.extensions import db
from app.models.inventory import (
    StockBalance,
    StockMovement,
    MOVEMENT_IN,
    MOVEMENT_OUT,
    MOVEMENT_ADJUST,
    MOVEMENT_RESERVE,
    MOVEMENT_RELEASE,
)
from app.services.errors import InsufficientStockError


def _get_or_create_balance(product_id, location_id, lot_id=None):
    balance = StockBalance.query.filter_by(
        product_id=product_id, location_id=location_id, lot_id=lot_id
    ).first()
    if balance is None:
        balance = StockBalance(
            product_id=product_id,
            location_id=location_id,
            lot_id=lot_id,
            quantity=0,
            reserved=0,
        )
        db.session.add(balance)
        db.session.flush()
    return balance


def _record_movement(product, location_id, lot_id, kind, quantity, reference_type=None,
                      reference_id=None, note=None, user_id=None):
    db.session.add(
        StockMovement(
            product_id=product.id,
            location_id=location_id,
            lot_id=lot_id,
            kind=kind,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note,
            created_by_id=user_id,
        )
    )


def receive_stock(product, location_id, quantity: Decimal, lot_id=None,
                   reference_type=None, reference_id=None, note=None, user_id=None):
    """Entrada de estoque (compra, ajuste positivo, devolução)."""
    quantity = Decimal(str(quantity))
    balance = _get_or_create_balance(product.id, location_id, lot_id)
    balance.quantity += quantity
    _record_movement(
        product, location_id, lot_id, MOVEMENT_IN, quantity,
        reference_type, reference_id, note, user_id,
    )
    return balance


def withdraw_stock(product, location_id, quantity: Decimal, lot_id=None,
                    reference_type=None, reference_id=None, note=None, user_id=None,
                    allow_negative=False):
    """Saída de estoque (venda, ajuste negativo). Verifica disponibilidade
    (quantity - reserved) a menos que allow_negative seja True."""
    quantity = Decimal(str(quantity))
    balance = _get_or_create_balance(product.id, location_id, lot_id)
    if not allow_negative and balance.available < quantity:
        raise InsufficientStockError(product.name, balance.available, quantity)

    balance.quantity -= quantity
    _record_movement(
        product, location_id, lot_id, MOVEMENT_OUT, quantity,
        reference_type, reference_id, note, user_id,
    )
    return balance


def reserve_stock(product, location_id, quantity: Decimal, lot_id=None,
                   reference_type=None, reference_id=None, user_id=None):
    """Reserva estoque para um pedido (não sai do saldo físico, só reduz o disponível)."""
    quantity = Decimal(str(quantity))
    balance = _get_or_create_balance(product.id, location_id, lot_id)
    if balance.available < quantity:
        raise InsufficientStockError(product.name, balance.available, quantity)

    balance.reserved += quantity
    _record_movement(
        product, location_id, lot_id, MOVEMENT_RESERVE, quantity,
        reference_type, reference_id, None, user_id,
    )
    return balance


def release_reservation(product, location_id, quantity: Decimal, lot_id=None,
                         reference_type=None, reference_id=None, user_id=None):
    """Libera uma reserva sem tirar do estoque físico (pedido cancelado antes da retirada)."""
    quantity = Decimal(str(quantity))
    balance = _get_or_create_balance(product.id, location_id, lot_id)
    balance.reserved = max(Decimal(0), balance.reserved - quantity)
    _record_movement(
        product, location_id, lot_id, MOVEMENT_RELEASE, quantity,
        reference_type, reference_id, None, user_id,
    )
    return balance


def fulfill_reservation(product, location_id, quantity: Decimal, lot_id=None,
                         reference_type=None, reference_id=None, user_id=None):
    """Confirma a retirada de um item reservado: baixa do saldo físico e da
    reserva ao mesmo tempo (usado quando um pedido é efetivamente retirado)."""
    quantity = Decimal(str(quantity))
    balance = _get_or_create_balance(product.id, location_id, lot_id)
    balance.quantity -= quantity
    balance.reserved = max(Decimal(0), balance.reserved - quantity)
    _record_movement(
        product, location_id, lot_id, MOVEMENT_OUT, quantity,
        reference_type, reference_id, None, user_id,
    )
    return balance


def adjust_stock(product, location_id, new_quantity: Decimal, lot_id=None,
                  note=None, user_id=None):
    """Ajuste manual de inventário: define o saldo físico para new_quantity,
    registrando a diferença como movimentação."""
    new_quantity = Decimal(str(new_quantity))
    balance = _get_or_create_balance(product.id, location_id, lot_id)
    diff = new_quantity - balance.quantity
    balance.quantity = new_quantity
    _record_movement(
        product, location_id, lot_id, MOVEMENT_ADJUST, abs(diff),
        "manual", None, note or f"Ajuste de {diff:+}", user_id,
    )
    return balance
