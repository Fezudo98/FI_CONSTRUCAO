"""Configuração central da aplicação, lida via variáveis de ambiente."""
import os


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-troque-em-producao")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///fi_construcao.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ENABLE_STOREFRONT = _env_bool("ENABLE_STOREFRONT", False)

    BRAND_NAME = os.environ.get("BRAND_NAME", "F.I Construção")
    BRAND_TAGLINE = os.environ.get("BRAND_TAGLINE", "Tudo para sua obra")
    BRAND_PRIMARY_COLOR = os.environ.get("BRAND_PRIMARY_COLOR", "#08299B")
    BRAND_PRIMARY_DARK = os.environ.get("BRAND_PRIMARY_DARK", "#051D70")
    BRAND_ACCENT_COLOR = os.environ.get("BRAND_ACCENT_COLOR", "#FFA20A")

    APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "America/Sao_Paulo")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "16")) * 1024 * 1024

    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per minute")

    CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(os.getcwd(), "uploads"))

    LICENSE_KEY = os.environ.get("LICENSE_KEY", "")
    LICENSE_CHECK_URL = os.environ.get("LICENSE_CHECK_URL", "")


class DevConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


CONFIG_MAP = {
    "development": DevConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "production")
    return CONFIG_MAP.get(env, ProductionConfig)
