"""Serve as páginas estáticas do frontend (login, painel, PDV, operação)."""
import os

from flask import Blueprint, send_from_directory, current_app

bp = Blueprint("web", __name__)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")


@bp.get("/")
@bp.get("/index.html")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@bp.get("/login")
@bp.get("/login.html")
def login_page():
    return send_from_directory(FRONTEND_DIR, "login.html")


@bp.get("/pdv.html")
def pdv_page():
    return send_from_directory(FRONTEND_DIR, "pdv.html")


@bp.get("/operacao.html")
def operacao_page():
    return send_from_directory(FRONTEND_DIR, "operacao.html")


@bp.get("/relatorios.html")
def relatorios_page():
    return send_from_directory(FRONTEND_DIR, "relatorios.html")


@bp.get("/static/<path:filename>")
def frontend_static(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "static"), filename)
