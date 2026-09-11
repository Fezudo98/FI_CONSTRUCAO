"""Geração de código de barras (Code128) a partir do SKU do produto."""
import os

import barcode
from barcode.writer import SVGWriter
from flask import current_app

from app.extensions import db
from app.models.catalog import Product

CODE128 = barcode.get_barcode_class("code128")


def generate_barcode(product: Product) -> str:
    """Gera (ou regenera) o SVG do código de barras do produto e retorna o
    nome do arquivo salvo em BARCODE_FOLDER."""
    folder = current_app.config["BARCODE_FOLDER"]
    os.makedirs(folder, exist_ok=True)

    filename = f"{product.sku}"
    generated = CODE128(product.sku, writer=SVGWriter())
    saved_path = generated.save(os.path.join(folder, filename))

    product.barcode = product.barcode or product.sku
    db.session.add(product)

    return os.path.basename(saved_path)
