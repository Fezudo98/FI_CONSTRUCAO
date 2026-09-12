"""Log de auditoria mínimo: cada rota sensível chama log_action() explicitamente."""
from app.extensions import db
from app.models.audit import AuditLog


def log_action(user, action, details=None):
    db.session.add(
        AuditLog(
            user_id=user.id if user else None,
            user_name=user.name if user else "Sistema",
            action=action,
            details=details,
        )
    )
