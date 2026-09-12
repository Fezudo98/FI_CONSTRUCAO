def _create_delivery_order(auth_client):
    resp = auth_client.post("/api/products", json={
        "sku": "BLOCO01", "name": "Bloco de concreto", "base_unit": "UN",
        "cost_price": "2.00", "sale_price": "3.50",
    })
    product = resp.get_json()["product"]
    resp = auth_client.post("/api/inventory/locations", json={"code": "D1"})
    location = resp.get_json()["location"]
    auth_client.post("/api/inventory/adjust", json={
        "product_id": product["id"], "location_id": location["id"], "new_quantity": "500",
    })

    resp = auth_client.post("/api/orders", json={
        "customer_name": "Obra Delivery",
        "location_id": location["id"],
        "is_delivery": True,
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 50, "unit_price": "3.50"}],
    })
    return resp.get_json()["order"]


def test_delivery_full_flow(auth_client):
    order = _create_delivery_order(auth_client)

    resp = auth_client.post("/api/logistics/carriers", json={"name": "Frota Propria"})
    carrier = resp.get_json()["carrier"]

    resp = auth_client.post("/api/logistics/vehicles", json={"carrier_id": carrier["id"], "plate": "ABC1D23"})
    vehicle = resp.get_json()["vehicle"]

    resp = auth_client.post("/api/logistics/drivers", json={"carrier_id": carrier["id"], "name": "Joao Motorista"})
    driver = resp.get_json()["driver"]

    resp = auth_client.post("/api/logistics/deliveries", json={
        "order_id": order["id"], "address": "Rua das Obras, 123",
        "vehicle_id": vehicle["id"], "driver_id": driver["id"],
    })
    assert resp.status_code == 201, resp.get_json()
    delivery = resp.get_json()["delivery"]
    assert delivery["status"] == "scheduled"

    resp = auth_client.post(f"/api/logistics/deliveries/{delivery['id']}/advance")
    assert resp.get_json()["delivery"]["status"] == "in_route"

    resp = auth_client.post(f"/api/logistics/deliveries/{delivery['id']}/occurrences", json={
        "kind": "atraso", "description": "Transito intenso",
    })
    assert resp.status_code == 201
    assert len(resp.get_json()["delivery"]["occurrences"]) == 1

    resp = auth_client.post(f"/api/logistics/deliveries/{delivery['id']}/advance")
    assert resp.get_json()["delivery"]["status"] == "completed"

    resp = auth_client.get("/api/orders")
    order_after = next(o for o in resp.get_json()["orders"] if o["id"] == order["id"])
    assert order_after["status"] == "delivered"


def test_delivery_requires_is_delivery_order(auth_client):
    resp = auth_client.post("/api/products", json={
        "sku": "CAL01", "name": "Cal hidratada", "base_unit": "UN", "sale_price": "12.00",
    })
    product = resp.get_json()["product"]
    resp = auth_client.post("/api/inventory/locations", json={"code": "E1"})
    location = resp.get_json()["location"]
    auth_client.post("/api/inventory/adjust", json={
        "product_id": product["id"], "location_id": location["id"], "new_quantity": "10",
    })
    resp = auth_client.post("/api/orders", json={
        "customer_name": "Retirada balcao",
        "location_id": location["id"],
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 1, "unit_price": "12.00"}],
    })
    order = resp.get_json()["order"]

    resp = auth_client.post("/api/logistics/deliveries", json={"order_id": order["id"], "address": "N/A"})
    assert resp.status_code == 400
    assert "não está marcado como entrega" in resp.get_json()["error"]


def test_vehicle_and_driver_require_existing_carrier(auth_client):
    vehicle = auth_client.post("/api/logistics/vehicles", json={"carrier_id": 9999, "plate": "AAA1A11"})
    driver = auth_client.post("/api/logistics/drivers", json={"carrier_id": 9999, "name": "Motorista"})
    assert vehicle.status_code == 404
    assert driver.status_code == 404
