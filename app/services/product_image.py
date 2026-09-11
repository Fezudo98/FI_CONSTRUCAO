"""Upload da foto de um produto (uma imagem por produto)."""
import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.catalog import Product
from app.services.errors import ServiceError

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def _products_folder():
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "products")
    os.makedirs(folder, exist_ok=True)
    return folder


def save_product_image(product: Product, file_storage) -> str:
    if not file_storage or not file_storage.filename:
        raise ServiceError("Nenhum arquivo enviado.")

    original_name = secure_filename(file_storage.filename)
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ServiceError("Formato de imagem não suportado. Use JPG, PNG ou WEBP.")

    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > MAX_BYTES:
        raise ServiceError("Imagem maior que 5 MB.")

    old_filename = product.image_filename
    filename = f"{product.id}-{uuid.uuid4().hex[:8]}.{ext}"
    file_storage.save(os.path.join(_products_folder(), filename))

    product.image_filename = filename
    db.session.add(product)

    if old_filename:
        old_path = os.path.join(_products_folder(), old_filename)
        if os.path.isfile(old_path):
            os.remove(old_path)

    return filename
