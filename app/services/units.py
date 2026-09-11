"""Conversão de quantidades entre unidades de venda e a unidade base do produto."""
from decimal import Decimal

from app.services.errors import ServiceError


def to_base_unit(product, unit: str, quantity: Decimal) -> Decimal:
    """Converte `quantity` de `unit` para a unidade base do produto.
    Ex.: produto com base_unit='UN' e conversão CX->12: to_base_unit(produto, 'CX', 2) == 24
    """
    quantity = Decimal(quantity)
    if unit == product.base_unit:
        return quantity

    conversion = next((c for c in product.conversions if c.unit == unit), None)
    if conversion is None:
        raise ServiceError(
            f"Produto '{product.name}' não tem conversão cadastrada para a unidade '{unit}'."
        )
    return quantity * Decimal(conversion.factor_to_base)


def from_base_unit(product, unit: str, base_quantity: Decimal) -> Decimal:
    base_quantity = Decimal(base_quantity)
    if unit == product.base_unit:
        return base_quantity

    conversion = next((c for c in product.conversions if c.unit == unit), None)
    if conversion is None:
        raise ServiceError(
            f"Produto '{product.name}' não tem conversão cadastrada para a unidade '{unit}'."
        )
    return base_quantity / Decimal(conversion.factor_to_base)
