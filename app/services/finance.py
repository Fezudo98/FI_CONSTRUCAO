"""Contas a pagar: baixa total ou parcial."""
from datetime import datetime, timezone
from decimal import Decimal

from app.extensions import db
from app.models.finance import Payable, PayableSettlement, PAYABLE_OPEN, PAYABLE_PARTIAL, PAYABLE_PAID
from app.services.errors import ServiceError


def settle_payable(payable: Payable, user_id, amount: Decimal, method=None) -> PayableSettlement:
    if payable.status == PAYABLE_PAID:
        raise ServiceError("Esta conta já está totalmente paga.")

    amount = Decimal(str(amount))
    if amount <= 0:
        raise ServiceError("O valor da baixa precisa ser maior que zero.")
    if amount > payable.amount_open:
        raise ServiceError(f"Valor ({amount}) maior que o saldo em aberto ({payable.amount_open}).")

    settlement = PayableSettlement(
        paid_by_id=user_id,
        amount=amount,
        method=method,
        paid_at=datetime.now(timezone.utc),
    )
    # Anexa via a relacao (nao so payable_id direto) para que a colecao
    # payable.settlements ja fique atualizada em memoria, mesmo que tenha
    # sido carregada/cacheada antes nesta mesma sessao/request.
    payable.settlements.append(settlement)
    db.session.flush()

    payable.status = PAYABLE_PAID if payable.amount_open <= 0 else PAYABLE_PARTIAL
    return settlement
