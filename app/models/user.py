"""Usuários, papéis e permissões do depósito."""
from app.extensions import db
from app.models.base import TimestampMixin, SoftDeleteMixin


ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_CASHIER = "cashier"
ROLE_STOCK = "stock"
ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER, ROLE_STOCK]


class User(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_CASHIER)

    permission_overrides = db.relationship("UserPermissionOverride", back_populates="user")

    def has_permission(self, code: str) -> bool:
        from app.services.permissions import ROLE_PERMISSIONS

        override = next((o for o in self.permission_overrides if o.permission_code == code), None)
        if override is not None:
            return override.allowed
        return code in ROLE_PERMISSIONS.get(self.role, set())


class UserPermissionOverride(db.Model, TimestampMixin):
    """Permissão específica concedida ou revogada para um usuário."""
    __tablename__ = "user_permission_overrides"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    permission_code = db.Column(db.String(80), nullable=False)
    allowed = db.Column(db.Boolean, nullable=False)

    user = db.relationship("User", back_populates="permission_overrides")

    __table_args__ = (db.UniqueConstraint("user_id", "permission_code", name="uq_user_permission"),)
