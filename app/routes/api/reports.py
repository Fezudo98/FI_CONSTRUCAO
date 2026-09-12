from datetime import date, timedelta

from flask import Blueprint, request, jsonify

from app.services import reports as reports_service
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_RELATORIOS, PERM_ESTOQUE_VER

bp = Blueprint("api_reports", __name__, url_prefix="/api/reports")


def _parse_date(value, default):
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        return default


@bp.get("/dashboard")
@permission_required(PERM_RELATORIOS)
def dashboard():
    user = current_user()
    today = date.today()
    date_end = _parse_date(request.args.get("date_end"), today)
    date_start = _parse_date(request.args.get("date_start"), today - timedelta(days=30))

    return jsonify(
        {
            "kpis": reports_service.summary_kpis(date_start, date_end),
            "sales_by_day": reports_service.sales_by_day(date_start, date_end),
            "top_products": reports_service.top_products(date_start, date_end),
            "payment_breakdown": reports_service.payment_breakdown(date_start, date_end),
        }
    )


@bp.get("/low-stock")
@permission_required(PERM_ESTOQUE_VER)
def low_stock():
    user = current_user()
    return jsonify({"products": reports_service.low_stock_products()})
