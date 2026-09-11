"""Compras: fornecedores, pedidos de compra e recebimentos (parciais).
Ao confirmar um recebimento: dá entrada no estoque, atualiza o custo médio
do produto e gera uma conta a pagar."""
from datetime import date, timedelta
from decimal import Decimal

from app.extensions import db
from app.models.catalog import Product
from app.models.inventory import StockBalance
from app.models.purchasing import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReceipt,
    PurchaseReceiptItem,
    PO_DRAFT,
    PO_SENT,
    PO_PARTIALLY_RECEIVED,
    PO_RECEIVED,
)
from app.models.finance import Payable
from app.services import inventory
from app.services.errors import ServiceError


def create_purchase_order(company_id, user_id, supplier_id, items) -> PurchaseOrder:
    if not items:
        raise ServiceError("O pedido de compra precisa ter ao menos um item.")

    po = PurchaseOrder(
        company_id=company_id,
        supplier_id=supplier_id,
        created_by_id=user_id,
        status=PO_SENT,
        total=Decimal(0),
    )
    db.session.add(po)
    db.session.flush()

    total = Decimal(0)
    for item in items:
        product = db.session.get(Product, item["product_id"])
        if product is None:
            raise ServiceError(f"Produto {item['product_id']} não encontrado.")

        quantity = Decimal(str(item["quantity"]))
        unit_price = Decimal(str(item["unit_price"]))
        total += (quantity * unit_price).quantize(Decimal("0.01"))

        db.session.add(
            PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=product.id,
                unit=item["unit"],
                quantity=quantity,
                unit_price=unit_price,
            )
        )

    po.total = total
    return po


def _update_average_cost(company_id, product: Product, received_quantity_base: Decimal, unit_price_base: Decimal):
    """Atualiza o custo médio ponderado do produto considerando o saldo total
    já em estoque (em todas as localizações) mais a quantidade recebida agora."""
    current_total = db.session.query(db.func.coalesce(db.func.sum(StockBalance.quantity), 0)).filter_by(
        company_id=company_id, product_id=product.id
    ).scalar()
    current_total = Decimal(current_total or 0)

    old_cost = Decimal(product.cost_price)
    new_total = current_total + received_quantity_base
    if new_total <= 0:
        return

    product.cost_price = (
        (current_total * old_cost + received_quantity_base * unit_price_base) / new_total
    ).quantize(Decimal("0.0001"))


def receive_purchase_order(purchase_order: PurchaseOrder, items_received, location_id, user_id,
                            note=None, payable_due_days=30) -> PurchaseReceipt:
    """items_received: [{purchase_order_item_id, quantity}]"""
    if purchase_order.status not in (PO_SENT, PO_PARTIALLY_RECEIVED, PO_DRAFT):
        raise ServiceError(f"Pedido de compra em status '{purchase_order.status}' não pode receber itens.")
    if not items_received:
        raise ServiceError("Informe ao menos um item recebido.")

    receipt = PurchaseReceipt(purchase_order_id=purchase_order.id, received_by_id=user_id, note=note)
    db.session.add(receipt)
    db.session.flush()

    receipt_total = Decimal(0)
    order_items_by_id = {i.id: i for i in purchase_order.items}

    from app.services.units import to_base_unit

    for entry in items_received:
        po_item = order_items_by_id.get(entry["purchase_order_item_id"])
        if po_item is None:
            raise ServiceError("Item do pedido de compra não encontrado.")

        quantity = Decimal(str(entry["quantity"]))
        remaining = po_item.quantity - po_item.quantity_received
        if quantity > remaining:
            raise ServiceError(
                f"Quantidade recebida ({quantity}) maior que o pendente ({remaining}) para este item."
            )

        db.session.add(
            PurchaseReceiptItem(receipt_id=receipt.id, purchase_order_item_id=po_item.id, quantity=quantity)
        )
        po_item.quantity_received += quantity
        receipt_total += (quantity * po_item.unit_price).quantize(Decimal("0.01"))

        product = db.session.get(Product, po_item.product_id)
        base_quantity = to_base_unit(product, po_item.unit, quantity)
        base_unit_price = po_item.unit_price / to_base_unit(product, po_item.unit, Decimal(1))

        _update_average_cost(purchase_order.company_id, product, base_quantity, base_unit_price)
        inventory.receive_stock(
            purchase_order.company_id, product, location_id, base_quantity,
            reference_type="purchase_receipt", reference_id=receipt.id, user_id=user_id,
        )

    all_received = all(i.quantity_received >= i.quantity for i in purchase_order.items)
    purchase_order.status = PO_RECEIVED if all_received else PO_PARTIALLY_RECEIVED

    db.session.add(
        Payable(
            company_id=purchase_order.company_id,
            supplier_id=purchase_order.supplier_id,
            purchase_order_id=purchase_order.id,
            description=f"Recebimento #{receipt.id} do pedido de compra #{purchase_order.id}",
            amount=receipt_total,
            due_date=date.today() + timedelta(days=payable_due_days),
        )
    )

    return receipt
