from decimal import Decimal


def _setup(auth_client):
    resp = auth_client.post("/api/products", json={
        "sku": "AREIA01", "name": "Areia media m3", "base_unit": "UN",
        "cost_price": "50.00", "sale_price": "80.00",
    })
    product = resp.get_json()["product"]

    resp = auth_client.post("/api/inventory/locations", json={"code": "C1"})
    location = resp.get_json()["location"]

    resp = auth_client.post("/api/purchasing/suppliers", json={"name": "Fornecedor Areia LTDA"})
    supplier = resp.get_json()["supplier"]

    return product, location, supplier


def test_purchase_receive_updates_stock_cost_and_payable(auth_client):
    product, location, supplier = _setup(auth_client)

    resp = auth_client.post("/api/purchasing/orders", json={
        "supplier_id": supplier["id"],
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 10, "unit_price": "55.00"}],
    })
    assert resp.status_code == 201, resp.get_json()
    po = resp.get_json()["purchase_order"]
    assert po["status"] == "sent"
    po_item_id = po["items"][0]["id"]

    # recebimento parcial: 4 de 10
    resp = auth_client.post(f"/api/purchasing/orders/{po['id']}/receive", json={
        "location_id": location["id"],
        "items": [{"purchase_order_item_id": po_item_id, "quantity": 4}],
    })
    assert resp.status_code == 201, resp.get_json()
    assert resp.get_json()["purchase_order"]["status"] == "partially_received"

    # custo medio: (0 estoque anterior * 50 + 4 * 55) / 4 = 55.00
    resp = auth_client.get(f"/api/products/{product['id']}")
    assert Decimal(resp.get_json()["product"]["cost_price"]) == Decimal("55.0000")

    resp = auth_client.get(f"/api/inventory/balance?product_id={product['id']}")
    assert Decimal(resp.get_json()["balances"][0]["quantity"]) == Decimal("4")

    resp = auth_client.get("/api/finance/payables")
    payables = resp.get_json()["payables"]
    assert len(payables) == 1
    assert Decimal(payables[0]["amount"]) == Decimal("220.00")
    assert payables[0]["status"] == "open"

    # recebimento do restante: 6
    resp = auth_client.post(f"/api/purchasing/orders/{po['id']}/receive", json={
        "location_id": location["id"],
        "items": [{"purchase_order_item_id": po_item_id, "quantity": 6}],
    })
    assert resp.get_json()["purchase_order"]["status"] == "received"

    # custo medio agora: (4*55 + 6*55)/10 = 55.00 (mesmo preco, so confirma consistencia)
    resp = auth_client.get(f"/api/products/{product['id']}")
    assert Decimal(resp.get_json()["product"]["cost_price"]) == Decimal("55.0000")


def test_receive_more_than_pending_fails(auth_client):
    product, location, supplier = _setup(auth_client)
    resp = auth_client.post("/api/purchasing/orders", json={
        "supplier_id": supplier["id"],
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 5, "unit_price": "10.00"}],
    })
    po = resp.get_json()["purchase_order"]

    resp = auth_client.post(f"/api/purchasing/orders/{po['id']}/receive", json={
        "location_id": location["id"],
        "items": [{"purchase_order_item_id": po["items"][0]["id"], "quantity": 999}],
    })
    assert resp.status_code == 400
    assert "maior que o pendente" in resp.get_json()["error"]


def test_payable_partial_and_full_settlement(auth_client):
    product, location, supplier = _setup(auth_client)
    resp = auth_client.post("/api/purchasing/orders", json={
        "supplier_id": supplier["id"],
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 2, "unit_price": "100.00"}],
    })
    po = resp.get_json()["purchase_order"]
    auth_client.post(f"/api/purchasing/orders/{po['id']}/receive", json={
        "location_id": location["id"],
        "items": [{"purchase_order_item_id": po["items"][0]["id"], "quantity": 2}],
    })

    payable_id = auth_client.get("/api/finance/payables").get_json()["payables"][0]["id"]

    resp = auth_client.post(f"/api/finance/payables/{payable_id}/settle", json={"amount": "100.00", "method": "pix"})
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["payable"]["status"] == "partially_paid"
    assert resp.get_json()["payable"]["amount_open"] == "100.00"

    resp = auth_client.post(f"/api/finance/payables/{payable_id}/settle", json={"amount": "100.00", "method": "pix"})
    assert resp.get_json()["payable"]["status"] == "paid"
    assert resp.get_json()["payable"]["amount_open"] == "0.00"

    resp = auth_client.post(f"/api/finance/payables/{payable_id}/settle", json={"amount": "1.00"})
    assert resp.status_code == 400
    assert "já está totalmente paga" in resp.get_json()["error"]
