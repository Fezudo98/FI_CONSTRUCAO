from decimal import Decimal


def _create_product(auth_client, sku="CIM50", conversions=None):
    payload = {
        "sku": sku,
        "name": "Cimento CP-II 50kg",
        "base_unit": "UN",
        "cost_price": "28.00",
        "sale_price": "35.00",
        "conversions": conversions or [{"unit": "PL", "factor_to_base": 40}],
    }
    resp = auth_client.post("/api/products", json=payload)
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["product"]


def _create_location(auth_client, code="A1"):
    resp = auth_client.post("/api/inventory/locations", json={"code": code, "description": "Galpão A"})
    assert resp.status_code == 201
    return resp.get_json()["location"]


def test_create_and_list_product(auth_client):
    product = _create_product(auth_client)
    resp = auth_client.get("/api/products")
    skus = [p["sku"] for p in resp.get_json()["products"]]
    assert product["sku"] in skus


def test_full_sale_flow_with_unit_conversion(auth_client):
    product = _create_product(auth_client)
    location = _create_location(auth_client)

    # abre caixa
    resp = auth_client.post("/api/pdv/cash-session/open", json={"opening_amount": "100.00"})
    assert resp.status_code == 201
    session_id = resp.get_json()["cash_session"]["id"]

    # entrada manual de estoque via ajuste (simula carga inicial)
    resp = auth_client.post(
        "/api/inventory/adjust",
        json={"product_id": product["id"], "location_id": location["id"], "new_quantity": "200"},
    )
    assert resp.status_code == 200

    # venda: 1 pallet (40 UN) + 5 UN avulsas
    resp = auth_client.post(
        "/api/pdv/sales",
        json={
            "location_id": location["id"],
            "items": [
                {"product_id": product["id"], "unit": "PL", "quantity": 1, "unit_price": 1400},
                {"product_id": product["id"], "unit": "UN", "quantity": 5, "unit_price": 35},
            ],
            "payments": [{"method": "pix", "amount": 1575}],
            "customer_name": "Obra do João",
        },
    )
    assert resp.status_code == 201, resp.get_json()
    assert resp.get_json()["sale"]["total"] == "1575.00"

    # saldo esperado: 200 - 40 - 5 = 155
    resp = auth_client.get(f"/api/inventory/balance?product_id={product['id']}")
    balances = resp.get_json()["balances"]
    assert Decimal(balances[0]["quantity"]) == Decimal("155")

    # fecha caixa
    resp = auth_client.post(f"/api/pdv/cash-session/{session_id}/close", json={"closing_amount": "1675.00"})
    assert resp.status_code == 200


def test_sale_fails_when_payment_mismatch(auth_client):
    product = _create_product(auth_client)
    location = _create_location(auth_client)
    auth_client.post("/api/pdv/cash-session/open", json={"opening_amount": "0"})
    auth_client.post(
        "/api/inventory/adjust",
        json={"product_id": product["id"], "location_id": location["id"], "new_quantity": "10"},
    )

    resp = auth_client.post(
        "/api/pdv/sales",
        json={
            "location_id": location["id"],
            "items": [{"product_id": product["id"], "unit": "UN", "quantity": 1, "unit_price": 35}],
            "payments": [{"method": "pix", "amount": 10}],
        },
    )
    assert resp.status_code == 400
    assert "diferente do total" in resp.get_json()["error"]


def test_sale_fails_when_insufficient_stock(auth_client):
    product = _create_product(auth_client)
    location = _create_location(auth_client)
    auth_client.post("/api/pdv/cash-session/open", json={"opening_amount": "0"})

    resp = auth_client.post(
        "/api/pdv/sales",
        json={
            "location_id": location["id"],
            "items": [{"product_id": product["id"], "unit": "UN", "quantity": 5, "unit_price": 35}],
            "payments": [{"method": "pix", "amount": 175}],
        },
    )
    assert resp.status_code == 400
    assert "Estoque insuficiente" in resp.get_json()["error"]


def test_sale_without_open_cash_session(auth_client):
    product = _create_product(auth_client)
    location = _create_location(auth_client)
    resp = auth_client.post(
        "/api/pdv/sales",
        json={
            "location_id": location["id"],
            "items": [{"product_id": product["id"], "unit": "UN", "quantity": 1, "unit_price": 35}],
            "payments": [{"method": "pix", "amount": 35}],
        },
    )
    assert resp.status_code == 400
    assert "caixa aberto" in resp.get_json()["error"]
