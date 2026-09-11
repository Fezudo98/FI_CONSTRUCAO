"""Popula o sistema com dados de exemplo para teste: endereços de estoque,
catálogo de produtos de depósito de construção com conversão de unidades,
saldo inicial de estoque, um fornecedor e um caixa já aberto.

Uso: python scripts/seed_demo_data.py
Idempotente: pode rodar mais de uma vez sem duplicar produtos/endereços já
existentes (por SKU/código); sempre abre um novo caixa se não houver um aberto.
"""
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.company import Company, User  # noqa: E402
from app.models.catalog import Product, UnitConversion  # noqa: E402
from app.models.inventory import StockLocation, StockBalance  # noqa: E402
from app.models.purchasing import Supplier  # noqa: E402
from app.services import inventory, pdv  # noqa: E402

LOCATIONS = [
    ("A1", "Pátio de agregados (areia, brita)"),
    ("A2", "Galpão de cimento e argamassa"),
    ("B1", "Depósito de ferragens e elétrica"),
    ("B2", "Depósito de acabamento (tintas, pisos)"),
]

# (sku, nome, categoria, base_unit, custo, venda, min_estoque, conversoes, endereco, saldo_inicial)
PRODUCTS = [
    ("CIM50", "Cimento CP-II 50kg", "Cimento", "UN", "25.00", "34.90", 40,
     [("PL", 40)], "A2", 480),
    ("CAL20", "Cal hidratada 20kg", "Cimento", "UN", "9.50", "14.90", 20,
     [("PL", 60)], "A2", 180),
    ("ARGAM20", "Argamassa ACII 20kg", "Cimento", "UN", "16.00", "23.90", 20,
     [("PL", 50)], "A2", 250),
    ("CIMCOLA20", "Cimento cola AC-I 20kg", "Cimento", "UN", "14.00", "21.90", 15,
     [("PL", 50)], "A2", 120),
    ("AREIA_M3", "Areia média lavada (m³)", "Agregados", "UN", "65.00", "95.00", 5,
     [], "A1", 40),
    ("BRITA1_M3", "Brita 1 (m³)", "Agregados", "UN", "70.00", "105.00", 5,
     [], "A1", 35),
    ("TIJOLO6", "Tijolo 6 furos", "Alvenaria", "UN", "0.55", "0.85", 500,
     [("MIL", 1000)], "A1", 12000),
    ("BLOCO14", "Bloco de concreto 14x19x39", "Alvenaria", "UN", "2.80", "4.20", 200,
     [("PL", 60)], "A1", 3600),
    ("VERG10", "Vergalhão CA-50 10mm 12m", "Ferragem", "UN", "38.00", "52.00", 20,
     [("FD", 10)], "B1", 200),
    ("VERG63", "Vergalhão CA-60 6.3mm 12m", "Ferragem", "UN", "14.00", "19.90", 30,
     [("FD", 20)], "B1", 400),
    ("ARAME18", "Arame recozido 18 rolo 1kg", "Ferragem", "UN", "9.00", "14.90", 20,
     [], "B1", 60),
    ("PVC100_6M", "Tubo PVC esgoto 100mm 6m", "Hidráulica", "UN", "42.00", "62.00", 10,
     [("FD", 10)], "B1", 80),
    ("FIO25_100M", "Fio elétrico 2,5mm rolo 100m", "Elétrica", "UN", "115.00", "159.90", 8,
     [], "B1", 45),
    ("TINTA18L_BR", "Tinta látex premium 18L branca", "Acabamento", "UN", "165.00", "229.90", 6,
     [("CX", 4)], "B2", 32),
    ("MASSA25", "Massa corrida PVA 25kg", "Acabamento", "UN", "38.00", "54.90", 10,
     [], "B2", 55),
    ("PORC60", "Porcelanato polido 60x60 (caixa 2,16m²)", "Acabamento", "CX", "48.00", "69.90", 30,
     [], "B2", 210),
]

SUPPLIER_NAME = "Distribuidora Central de Materiais LTDA"

CASH_OPENING_AMOUNT = Decimal("300.00")


def main():
    app = create_app()
    with app.app_context():
        company = Company.query.filter_by(is_headquarters=True).first()
        if company is None:
            print("Nenhuma empresa encontrada. Rode create_dev_admin.py primeiro.")
            sys.exit(1)

        admin = User.query.filter_by(company_id=company.id).first()
        if admin is None:
            print("Nenhum usuário encontrado. Rode create_dev_admin.py primeiro.")
            sys.exit(1)

        # --- endereços de estoque ---
        location_by_code = {}
        for code, description in LOCATIONS:
            loc = StockLocation.query.filter_by(company_id=company.id, code=code).first()
            if loc is None:
                loc = StockLocation(company_id=company.id, code=code, description=description)
                db.session.add(loc)
                db.session.flush()
                print(f"[endereco] criado {code} - {description}")
            location_by_code[code] = loc

        # --- fornecedor de exemplo ---
        supplier = Supplier.query.filter_by(company_id=company.id, name=SUPPLIER_NAME).first()
        if supplier is None:
            supplier = Supplier(company_id=company.id, name=SUPPLIER_NAME, phone="(11) 4002-8922")
            db.session.add(supplier)
            print(f"[fornecedor] criado {SUPPLIER_NAME}")

        # --- produtos + conversoes + estoque inicial ---
        for sku, name, category, base_unit, cost, price, min_stock, conversions, loc_code, initial_qty in PRODUCTS:
            product = Product.query.filter_by(sku=sku).first()
            if product is None:
                product = Product(
                    sku=sku, name=name, category=category, base_unit=base_unit,
                    cost_price=Decimal(cost), sale_price=Decimal(price), min_stock=min_stock,
                )
                db.session.add(product)
                db.session.flush()
                for unit, factor in conversions:
                    db.session.add(UnitConversion(product_id=product.id, unit=unit, factor_to_base=factor))
                print(f"[produto] criado {sku} - {name}")

            location = location_by_code[loc_code]
            existing_balance = StockBalance.query.filter_by(
                company_id=company.id, product_id=product.id, location_id=location.id
            ).first()
            if existing_balance is None or existing_balance.quantity == 0:
                inventory.receive_stock(
                    company.id, product, location.id, Decimal(initial_qty),
                    reference_type="seed", note="Carga inicial de demonstração", user_id=admin.id,
                )
                print(f"  -> estoque inicial: {initial_qty} {base_unit} em {loc_code}")

        db.session.commit()

        # --- caixa aberto ---
        open_session = pdv.get_open_cash_session(company.id)
        if open_session is None:
            pdv.open_cash_session(company.id, admin.id, CASH_OPENING_AMOUNT)
            db.session.commit()
            print(f"[caixa] aberto com R$ {CASH_OPENING_AMOUNT}")
        else:
            print(f"[caixa] já havia um caixa aberto (#{open_session.id})")

        total_products = Product.query.count()
        total_locations = StockLocation.query.filter_by(company_id=company.id).count()
        print(f"\nConcluído: {total_products} produtos, {total_locations} endereços, "
              f"fornecedor '{SUPPLIER_NAME}' e caixa aberto.")


if __name__ == "__main__":
    main()
