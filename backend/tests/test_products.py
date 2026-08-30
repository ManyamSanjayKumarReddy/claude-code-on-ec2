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

    response = client.get("/products")

    assert response.status_code == 200
    ids = [product["id"] for product in response.json()]
    assert created["id"] in ids


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
