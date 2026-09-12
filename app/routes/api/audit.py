from flask import Blueprint, request, jsonify

from app.models.audit import AuditLog
from app.services.auth import permission_required, current_user
from app.services.permissions import PERM_AUDITORIA

bp = Blueprint("api_audit", __name__, url_prefix="/api/audit")


@bp.get("/logs")
@permission_required(PERM_AUDITORIA)
def list_logs():
    user = current_user()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)

    query = AuditLog.query.order_by(AuditLog.timestamp.desc())
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify(
        {
            "logs": [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "user_name": log.user_name,
                    "action": log.action,
                    "details": log.details,
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )
