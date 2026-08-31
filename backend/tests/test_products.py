def make_payload(**overrides):
    payload = {
        "name": "Test Widget",
        "description": "A widget used in tests",
        "price": "9.99",
        "stock_quantity": 5,
    }
    payload.update(overrides)
    return payload


def test_create_product(client):
    response = client.post("/products", json=make_payload(name="Create Widget"))

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Create Widget"
    assert body["price"] == "9.99"
    assert body["stock_quantity"] == 5
    assert "id" in body


def test_create_product_rejects_invalid_price(client):
    response = client.post("/products", json=make_payload(name="Bad Price", price="0"))

    assert response.status_code == 422


def test_get_product(client):
    created = client.post("/products", json=make_payload(name="Get Widget")).json()

    response = client.get(f"/products/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Get Widget"


def test_get_product_not_found(client):
    response = client.get("/products/999999")

    assert response.status_code == 404


def test_list_products_includes_created(client):
    created = client.post("/products", json=make_payload(name="List Widget")).json()

    response = client.get("/products", params={"page_size": 100})

    assert response.status_code == 200
    body = response.json()
    ids = [product["id"] for product in body["items"]]
    assert created["id"] in ids
    assert body["total"] >= 1


def test_list_products_paginates(client):
    for i in range(5):
        client.post("/products", json=make_payload(name=f"Page Widget {i}"))

    response = client.get("/products", params={"page": 1, "page_size": 2})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] >= 5


def test_list_products_filters_by_search(client):
    created = client.post(
        "/products", json=make_payload(name="Zzyzx Search Target", description="unique marker")
    ).json()

    response = client.get("/products", params={"search": "Zzyzx", "page_size": 100})

    assert response.status_code == 200
    body = response.json()
    ids = [p["id"] for p in body["items"]]
    assert created["id"] in ids
    assert all(
        "zzyzx" in p["name"].lower() or "zzyzx" in (p["description"] or "").lower() for p in body["items"]
    )


def test_list_products_filters_by_price_range(client):
    created = client.post("/products", json=make_payload(name="Price Filter Widget", price="123.45")).json()

    response = client.get(
        "/products", params={"min_price": "123.00", "max_price": "124.00", "page_size": 100}
    )

    assert response.status_code == 200
    body = response.json()
    ids = [p["id"] for p in body["items"]]
    assert created["id"] in ids
    assert all(123.00 <= float(p["price"]) <= 124.00 for p in body["items"])


def test_list_products_filters_by_in_stock(client):
    out_of_stock = client.post("/products", json=make_payload(name="Zero Stock Widget", stock_quantity=0)).json()

    response = client.get("/products", params={"in_stock": "false", "page_size": 100})

    assert response.status_code == 200
    body = response.json()
    ids = [p["id"] for p in body["items"]]
    assert out_of_stock["id"] in ids
    assert all(p["stock_quantity"] == 0 for p in body["items"])


def test_create_product_with_image_url(client):
    response = client.post(
        "/products", json=make_payload(name="Image Widget", image_url="https://example.com/widget.jpg")
    )

    assert response.status_code == 201
    assert response.json()["image_url"] == "https://example.com/widget.jpg"


def test_create_product_without_image_url_defaults_to_none(client):
    response = client.post("/products", json=make_payload(name="No Image Widget"))

    assert response.status_code == 201
    assert response.json()["image_url"] is None


def test_update_product(client):
    created = client.post("/products", json=make_payload(name="Old Name")).json()

    response = client.put(
        f"/products/{created['id']}",
        json=make_payload(name="New Name", stock_quantity=42),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name"
    assert body["stock_quantity"] == 42


def test_update_product_not_found(client):
    response = client.put("/products/999999", json=make_payload())

    assert response.status_code == 404


def test_delete_product(client):
    created = client.post("/products", json=make_payload(name="Delete Widget")).json()

    delete_response = client.delete(f"/products/{created['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/products/{created['id']}")
    assert get_response.status_code == 404


def test_delete_product_not_found(client):
    response = client.delete("/products/999999")

    assert response.status_code == 404
