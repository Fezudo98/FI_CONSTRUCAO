from decimal import Decimal


def _create_product_and_location(auth_client, sku="TIJ01"):
    resp = auth_client.post("/api/products", json={
        "sku": sku, "name": "Tijolo 6 furos", "base_unit": "UN",
        "cost_price": "0.80", "sale_price": "1.20",
    })
    product = resp.get_json()["product"]
    resp = auth_client.post("/api/inventory/locations", json={"code": "B1", "description": "Patio B"})
    location = resp.get_json()["location"]
    auth_client.post("/api/inventory/adjust", json={
        "product_id": product["id"], "location_id": location["id"], "new_quantity": "1000",
    })
    return product, location


def test_quote_to_order_full_flow(auth_client):
    product, location = _create_product_and_location(auth_client)

    resp = auth_client.post("/api/quotes", json={
        "customer_name": "Obra da Maria",
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 500, "unit_price": "1.20"}],
    })
    assert resp.status_code == 201, resp.get_json()
    quote = resp.get_json()["quote"]
    assert quote["status"] == "draft"
    assert quote["total"] == "600.00"

    resp = auth_client.post(f"/api/quotes/{quote['id']}/send")
    assert resp.get_json()["quote"]["status"] == "sent"

    resp = auth_client.post(f"/api/quotes/{quote['id']}/approve")
    assert resp.get_json()["quote"]["status"] == "approved"

    resp = auth_client.post(f"/api/quotes/{quote['id']}/convert", json={"location_id": location["id"]})
    assert resp.status_code == 201, resp.get_json()
    order_id = resp.get_json()["order_id"]

    # estoque deve estar reservado (nao baixado ainda)
    resp = auth_client.get(f"/api/inventory/balance?product_id={product['id']}")
    balance = resp.get_json()["balances"][0]
    assert Decimal(balance["reserved"]) == Decimal("500")
    assert Decimal(balance["quantity"]) == Decimal("1000")

    # avanca: reserved -> separated -> picked_up (confirma baixa fisica)
    resp = auth_client.post(f"/api/orders/{order_id}/advance")
    assert resp.get_json()["order"]["status"] == "separated"
    resp = auth_client.post(f"/api/orders/{order_id}/advance")
    assert resp.get_json()["order"]["status"] == "picked_up"

    resp = auth_client.get(f"/api/inventory/balance?product_id={product['id']}")
    balance = resp.get_json()["balances"][0]
    assert Decimal(balance["reserved"]) == Decimal("0")
    assert Decimal(balance["quantity"]) == Decimal("500")


def test_order_cancel_releases_reservation(auth_client):
    product, location = _create_product_and_location(auth_client)

    resp = auth_client.post("/api/orders", json={
        "customer_name": "Cliente X",
        "location_id": location["id"],
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 100, "unit_price": "1.20"}],
    })
    order_id = resp.get_json()["order"]["id"]

    resp = auth_client.post(f"/api/orders/{order_id}/cancel")
    assert resp.get_json()["order"]["status"] == "cancelled"

    resp = auth_client.get(f"/api/inventory/balance?product_id={product['id']}")
    balance = resp.get_json()["balances"][0]
    assert Decimal(balance["reserved"]) == Decimal("0")
    assert Decimal(balance["quantity"]) == Decimal("1000")


def test_order_cannot_reserve_more_than_available(auth_client):
    product, location = _create_product_and_location(auth_client)
    resp = auth_client.post("/api/orders", json={
        "customer_name": "Cliente Y",
        "location_id": location["id"],
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 5000, "unit_price": "1.20"}],
    })
    assert resp.status_code == 400
    assert "Estoque insuficiente" in resp.get_json()["error"]
