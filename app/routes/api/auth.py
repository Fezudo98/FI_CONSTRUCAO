from flask import Blueprint, request, jsonify

from app.models.user import User
from app.extensions import db
from app.models.base import utcnow
from app.services.auth import check_password, login_user, logout_user, current_user, login_required

bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email, is_active=True).first()
    if user is None or not check_password(user, password):
        return jsonify({"error": "E-mail ou senha inválidos."}), 401

    login_user(user)
    return jsonify({"user": _serialize_user(user)})


@bp.post("/logout")
def logout():
    logout_user()
    return jsonify({"ok": True})


@bp.get("/me")
def me():
    user = current_user()
    if user is None:
        return jsonify({"user": None}), 200
    return jsonify({"user": _serialize_user(user)})


@bp.post("/onboarding/complete")
@login_required
def complete_onboarding():
    user = current_user()
    if user.onboarding_completed_at is None:
        user.onboarding_completed_at = utcnow()
        db.session.commit()
    return jsonify({"ok": True, "onboarding_completed": True})


def _serialize_user(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "onboarding_completed": user.onboarding_completed_at is not None,
    }
