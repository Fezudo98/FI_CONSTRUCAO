from datetime import date


def _make_sale(auth_client, sku, name, qty, price):
    resp = auth_client.post("/api/products", json={
        "sku": sku, "name": name, "base_unit": "UN", "cost_price": str(price / 2), "sale_price": str(price),
    })
    product = resp.get_json()["product"]
    resp = auth_client.post("/api/inventory/locations", json={"code": f"L_{sku}"})
    location = resp.get_json()["location"]
    auth_client.post("/api/inventory/adjust", json={
        "product_id": product["id"], "location_id": location["id"], "new_quantity": "100",
    })
    auth_client.post("/api/pdv/sales", json={
        "location_id": location["id"],
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": qty, "unit_price": price}],
        "payments": [{"method": "pix", "amount": qty * price}],
    })
    return product, location


def test_reports_dashboard_aggregates_sales(auth_client):
    auth_client.post("/api/pdv/cash-session/open", json={"opening_amount": "0"})
    _make_sale(auth_client, "REL01", "Produto Relatorio 1", 3, 10)
    _make_sale(auth_client, "REL02", "Produto Relatorio 2", 1, 50)

    today = date.today().isoformat()
    resp = auth_client.get(f"/api/reports/dashboard?date_start={today}&date_end={today}")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["kpis"]["sale_count"] == 2
    assert float(data["kpis"]["revenue"]) == 80.0  # 3*10 + 1*50
    assert len(data["sales_by_day"]) == 1
    assert float(data["sales_by_day"][0]["total"]) == 80.0

    top_names = [p["name"] for p in data["top_products"]]
    assert "Produto Relatorio 1" in top_names
    assert "Produto Relatorio 2" in top_names

    methods = [p["method"] for p in data["payment_breakdown"]]
    assert "pix" in methods


def test_low_stock_endpoint(auth_client):
    resp = auth_client.post("/api/products", json={
        "sku": "BAIXO01", "name": "Produto Estoque Baixo", "base_unit": "UN",
        "sale_price": "10.00", "min_stock": 50,
    })
    product = resp.get_json()["product"]
    resp = auth_client.post("/api/inventory/locations", json={"code": "L_BAIXO"})
    location = resp.get_json()["location"]
    auth_client.post("/api/inventory/adjust", json={
        "product_id": product["id"], "location_id": location["id"], "new_quantity": "10",
    })

    resp = auth_client.get("/api/reports/low-stock")
    assert resp.status_code == 200
    skus = [p["product_id"] for p in resp.get_json()["products"]]
    assert product["id"] in skus


def test_product_not_low_stock_when_above_minimum(auth_client):
    resp = auth_client.post("/api/products", json={
        "sku": "OK01", "name": "Produto Estoque OK", "base_unit": "UN",
        "sale_price": "10.00", "min_stock": 5,
    })
    product = resp.get_json()["product"]
    resp = auth_client.post("/api/inventory/locations", json={"code": "L_OK"})
    location = resp.get_json()["location"]
    auth_client.post("/api/inventory/adjust", json={
        "product_id": product["id"], "location_id": location["id"], "new_quantity": "500",
    })

    resp = auth_client.get("/api/reports/low-stock")
    ids = [p["product_id"] for p in resp.get_json()["products"]]
    assert product["id"] not in ids
