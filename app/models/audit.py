"""Log de auditoria: registro mínimo de ações sensíveis, não é acionado
automaticamente por middleware — cada rota sensível chama registrar_log()."""
from app.extensions import db
from app.models.base import utcnow


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user_name = db.Column(db.String(150))  # snapshot: preserva o nome mesmo se o usuário for removido depois
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.String(500))
