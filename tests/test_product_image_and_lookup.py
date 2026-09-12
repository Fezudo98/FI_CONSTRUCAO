import io


def _create_product(auth_client, sku="IMG01", barcode=None):
    resp = auth_client.post("/api/products", json={
        "sku": sku, "name": "Produto com Imagem", "base_unit": "UN",
        "sale_price": "10.00", "barcode": barcode,
    })
    return resp.get_json()["product"]


def test_upload_product_image(auth_client):
    product = _create_product(auth_client)
    assert product["image_url"] is None

    fake_image = (io.BytesIO(b"fake-jpeg-bytes"), "foto.jpg")
    resp = auth_client.post(
        f"/api/products/{product['id']}/image",
        data={"image": fake_image},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201, resp.get_json()
    updated = resp.get_json()["product"]
    assert updated["image_url"] is not None
    assert updated["image_url"].startswith("/api/products/uploads/")

    resp = auth_client.get(updated["image_url"])
    assert resp.status_code == 200
    assert resp.data == b"fake-jpeg-bytes"


def test_upload_rejects_invalid_extension(auth_client):
    product = _create_product(auth_client, sku="IMG02")
    fake_file = (io.BytesIO(b"not an image"), "arquivo.txt")
    resp = auth_client.post(
        f"/api/products/{product['id']}/image",
        data={"image": fake_file},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert "não suportado" in resp.get_json()["error"]


def test_replacing_image_removes_old_file(auth_client):
    product = _create_product(auth_client, sku="IMG03")
    first = (io.BytesIO(b"imagem-1"), "a.jpg")
    resp = auth_client.post(f"/api/products/{product['id']}/image", data={"image": first}, content_type="multipart/form-data")
    first_url = resp.get_json()["product"]["image_url"]

    second = (io.BytesIO(b"imagem-2"), "b.png")
    resp = auth_client.post(f"/api/products/{product['id']}/image", data={"image": second}, content_type="multipart/form-data")
    second_url = resp.get_json()["product"]["image_url"]

    assert first_url != second_url
    resp = auth_client.get(first_url)
    assert resp.status_code == 404  # arquivo antigo foi removido


def test_lookup_by_exact_barcode(auth_client):
    product = _create_product(auth_client, sku="LOOK01", barcode="7891234567890")

    resp = auth_client.get("/api/products/lookup?code=7891234567890")
    assert resp.status_code == 200
    assert resp.get_json()["product"]["id"] == product["id"]


def test_lookup_by_exact_sku(auth_client):
    product = _create_product(auth_client, sku="LOOK02")

    resp = auth_client.get("/api/products/lookup?code=LOOK02")
    assert resp.status_code == 200
    assert resp.get_json()["product"]["id"] == product["id"]


def test_lookup_not_found(auth_client):
    resp = auth_client.get("/api/products/lookup?code=NAOEXISTE")
    assert resp.status_code == 404


def test_lookup_does_not_partial_match(auth_client):
    """Ao contrario da busca normal (?q=), o lookup de leitor de codigo de
    barras deve ser exato -- nao pode confundir produtos com SKU parecido."""
    _create_product(auth_client, sku="ABC", barcode="111")
    _create_product(auth_client, sku="ABCD", barcode="1112")

    resp = auth_client.get("/api/products/lookup?code=ABC")
    assert resp.get_json()["product"]["sku"] == "ABC"

    resp = auth_client.get("/api/products/lookup?code=111")
    assert resp.get_json()["product"]["barcode"] == "111"


def test_barcode_must_be_unique(auth_client):
    _create_product(auth_client, sku="BAR01", barcode="7890000000001")
    resp = auth_client.post("/api/products", json={
        "sku": "BAR02", "name": "Outro produto", "base_unit": "UN",
        "sale_price": "12.00", "barcode": "7890000000001",
    })
    assert resp.status_code == 409
    assert "código de barras" in resp.get_json()["error"]
