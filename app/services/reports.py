"""Agregações para o painel de relatórios: vendas no período, ranking de
produtos, formas de pagamento e KPIs.

Simplificação assumida: o lucro bruto usa o custo ATUAL do produto (não um
custo histórico por venda, que exigiria um campo adicional em SaleItem).
Se o custo médio mudar depois de uma venda antiga, o relatório reflete o
custo de hoje, não o de quando a venda ocorreu."""
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models.sales import Sale, SaleItem, Payment, SALE_STATUS_COMPLETED
from app.models.catalog import Product


def sales_by_day(date_start, date_end):
    rows = (
        db.session.query(
            func.date(Sale.created_at).label("day"),
            func.sum(Sale.total).label("total"),
        )
        .filter(
            Sale.status == SALE_STATUS_COMPLETED,
            func.date(Sale.created_at) >= date_start,
            func.date(Sale.created_at) <= date_end,
        )
        .group_by("day")
        .order_by("day")
        .all()
    )
    return [{"day": str(r.day), "total": str(r.total)} for r in rows]


def top_products(date_start, date_end, limit=10):
    rows = (
        db.session.query(
            Product.id, Product.name, func.sum(SaleItem.quantity).label("qty"),
            func.sum(SaleItem.total).label("total"),
        )
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(
            Sale.status == SALE_STATUS_COMPLETED,
            func.date(Sale.created_at) >= date_start,
            func.date(Sale.created_at) <= date_end,
        )
        .group_by(Product.id, Product.name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return [{"product_id": r.id, "name": r.name, "quantity": str(r.qty), "total": str(r.total)} for r in rows]


def payment_breakdown(date_start, date_end):
    rows = (
        db.session.query(Payment.method, func.sum(Payment.amount).label("total"))
        .join(Sale, Sale.id == Payment.sale_id)
        .filter(
            Sale.status == SALE_STATUS_COMPLETED,
            func.date(Sale.created_at) >= date_start,
            func.date(Sale.created_at) <= date_end,
        )
        .group_by(Payment.method)
        .all()
    )
    return [{"method": r.method, "total": str(r.total)} for r in rows]


def summary_kpis(date_start, date_end):
    sales = (
        Sale.query.filter(
            Sale.status == SALE_STATUS_COMPLETED,
            func.date(Sale.created_at) >= date_start,
            func.date(Sale.created_at) <= date_end,
        ).all()
    )

    revenue = sum((s.total for s in sales), start=Decimal(0))
    sale_count = len(sales)
    average_ticket = (revenue / sale_count) if sale_count else Decimal(0)

    cost_total = Decimal(0)
    for sale in sales:
        for item in sale.items:
            product = db.session.get(Product, item.product_id)
            if product is not None:
                cost_total += Decimal(product.cost_price) * item.quantity

    gross_profit = revenue - cost_total

    return {
        "revenue": str(revenue),
        "sale_count": sale_count,
        "average_ticket": str(average_ticket.quantize(Decimal("0.01"))),
        "gross_profit": str(gross_profit.quantize(Decimal("0.01"))),
    }


def low_stock_products():
    """Produtos cujo saldo total (somado em todos os endereços) está no ou
    abaixo do estoque mínimo configurado."""
    from app.models.inventory import StockBalance

    totals = (
        db.session.query(
            Product.id, Product.name, Product.min_stock,
            func.coalesce(func.sum(StockBalance.quantity), 0).label("total_qty"),
        )
        .outerjoin(
            StockBalance,
            StockBalance.product_id == Product.id,
        )
        .filter(Product.is_active.is_(True))
        .group_by(Product.id, Product.name, Product.min_stock)
        .having(func.coalesce(func.sum(StockBalance.quantity), 0) <= Product.min_stock)
        .order_by(Product.name)
        .all()
    )
    return [
        {"product_id": r.id, "name": r.name, "min_stock": str(r.min_stock), "current_stock": str(r.total_qty)}
        for r in totals
    ]
