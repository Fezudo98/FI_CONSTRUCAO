def test_create_list_update_customer(auth_client):
    resp = auth_client.post("/api/customers", json={"name": "João da Obra", "phone": "11999990000"})
    assert resp.status_code == 201, resp.get_json()
    customer = resp.get_json()["customer"]

    resp = auth_client.get("/api/customers")
    assert any(c["id"] == customer["id"] for c in resp.get_json()["customers"])

    resp = auth_client.put(f"/api/customers/{customer['id']}", json={"phone": "11988887777"})
    assert resp.get_json()["customer"]["phone"] == "11988887777"


def test_delete_customer_without_history_hard_deletes(auth_client):
    resp = auth_client.post("/api/customers", json={"name": "Cliente Sem Historico"})
    customer_id = resp.get_json()["customer"]["id"]

    resp = auth_client.delete(f"/api/customers/{customer_id}")
    assert resp.status_code == 200

    resp = auth_client.get("/api/customers")
    assert not any(c["id"] == customer_id for c in resp.get_json()["customers"])


def test_delete_customer_with_history_soft_deletes(auth_client):
    resp = auth_client.post("/api/customers", json={"name": "Obra Recorrente"})
    customer = resp.get_json()["customer"]

    resp = auth_client.post("/api/products", json={
        "sku": "PROD_CLI", "name": "Produto Teste", "base_unit": "UN", "sale_price": "10.00",
    })
    product = resp.get_json()["product"]
    resp = auth_client.post("/api/inventory/locations", json={"code": "LOC_CLI"})
    location = resp.get_json()["location"]
    auth_client.post("/api/pdv/cash-session/open", json={"opening_amount": "0"})
    auth_client.post("/api/inventory/adjust", json={
        "product_id": product["id"], "location_id": location["id"], "new_quantity": "10",
    })
    resp = auth_client.post("/api/pdv/sales", json={
        "location_id": location["id"], "customer_id": customer["id"],
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 1, "unit_price": 10}],
        "payments": [{"method": "pix", "amount": 10}],
    })
    assert resp.status_code == 201

    resp = auth_client.delete(f"/api/customers/{customer['id']}")
    assert resp.status_code == 200

    # nao aparece mais na listagem (is_active=False), mas nao foi apagado do banco
    resp = auth_client.get("/api/customers")
    assert not any(c["id"] == customer["id"] for c in resp.get_json()["customers"])


def test_audit_log_records_sensitive_actions(auth_client):
    auth_client.post("/api/products", json={
        "sku": "AUDIT_SKU", "name": "Produto Auditado", "base_unit": "UN", "sale_price": "5.00",
    })
    resp = auth_client.get("/api/audit/logs")
    assert resp.status_code == 200
    actions = [log["action"] for log in resp.get_json()["logs"]]
    assert "produto.criado" in actions


def test_get_sale_detail_for_receipt(auth_client):
    resp = auth_client.post("/api/products", json={
        "sku": "RECIBO_SKU", "name": "Produto Recibo", "base_unit": "UN", "sale_price": "20.00",
    })
    product = resp.get_json()["product"]
    resp = auth_client.post("/api/inventory/locations", json={"code": "LOC_RECIBO"})
    location = resp.get_json()["location"]
    auth_client.post("/api/pdv/cash-session/open", json={"opening_amount": "0"})
    auth_client.post("/api/inventory/adjust", json={
        "product_id": product["id"], "location_id": location["id"], "new_quantity": "5",
    })
    resp = auth_client.post("/api/pdv/sales", json={
        "location_id": location["id"], "customer_name": "Cliente Balcao",
        "items": [{"product_id": product["id"], "unit": "UN", "quantity": 2, "unit_price": 20}],
        "payments": [{"method": "dinheiro", "amount": 40}],
    })
    sale_id = resp.get_json()["sale"]["id"]

    resp = auth_client.get(f"/api/pdv/sales/{sale_id}")
    assert resp.status_code == 200
    sale = resp.get_json()["sale"]
    assert sale["customer_name"] == "Cliente Balcao"
    assert sale["items"][0]["product_name"] == "Produto Recibo"
    assert sale["payments"][0]["method"] == "dinheiro"
