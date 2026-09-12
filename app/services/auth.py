"""Autenticação por sessão (cookie) — adequado para uso em rede local do depósito."""
from functools import wraps

from flask import session, jsonify

from app.extensions import bcrypt, db
from app.models.user import User


def hash_password(password: str) -> str:
    return bcrypt.generate_password_hash(password).decode("utf-8")


def check_password(user: User, password: str) -> bool:
    return bcrypt.check_password_hash(user.password_hash, password)


def login_user(user: User):
    session["user_id"] = user.id
    session.permanent = True


def logout_user():
    session.pop("user_id", None)


def current_user() -> User | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.session.get(User, user_id)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "Não autenticado."}), 401
        return view(*args, **kwargs)

    return wrapper


def permission_required(permission_code: str):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                return jsonify({"error": "Não autenticado."}), 401
            if not user.has_permission(permission_code):
                return jsonify({"error": "Sem permissão para esta ação."}), 403
            return view(*args, **kwargs)

        return wrapper

    return decorator
