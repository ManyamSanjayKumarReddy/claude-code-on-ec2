import uuid


def unique_email():
    return f"cart-user-{uuid.uuid4().hex}@example.com"


def register_and_login(client):
    client.cookies.clear()
    payload = {
        "email": unique_email(),
        "password": "supersecret123",
        "full_name": "Cart Tester",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    return payload


def make_product(client, **overrides):
    payload = {
        "name": "Cart Widget",
        "description": "A widget used in cart tests",
        "price": "9.99",
        "stock_quantity": 5,
    }
    payload.update(overrides)
    return client.post("/products", json=payload).json()


def test_get_cart_requires_authentication(client):
    client.cookies.clear()

    response = client.get("/cart")

    assert response.status_code == 401


def test_get_empty_cart(client):
    register_and_login(client)

    response = client.get("/cart")

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == "0"
    assert body["item_count"] == 0


def test_add_item_to_cart(client):
    register_and_login(client)
    product = make_product(client, name="Add Widget", price="12.50", stock_quantity=10)

    response = client.post("/cart/items", json={"product_id": product["id"], "quantity": 2})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["product_id"] == product["id"]
    assert item["quantity"] == 2
    assert item["line_total"] == "25.00"
    assert body["total"] == "25.00"
    assert body["item_count"] == 2


def test_add_same_item_twice_merges_quantity(client):
    register_and_login(client)
    product = make_product(client, name="Merge Widget", stock_quantity=10)

    client.post("/cart/items", json={"product_id": product["id"], "quantity": 2})
    response = client.post("/cart/items", json={"product_id": product["id"], "quantity": 3})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 5


def test_add_item_rejects_quantity_over_stock(client):
    register_and_login(client)
    product = make_product(client, name="Scarce Widget", stock_quantity=1)

    response = client.post("/cart/items", json={"product_id": product["id"], "quantity": 2})

    assert response.status_code == 400


def test_add_item_rejects_unknown_product(client):
    register_and_login(client)

    response = client.post("/cart/items", json={"product_id": 999999, "quantity": 1})

    assert response.status_code == 404


def test_update_item_quantity(client):
    register_and_login(client)
    product = make_product(client, name="Update Widget", stock_quantity=10)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1})

    response = client.put(f"/cart/items/{product['id']}", json={"quantity": 4})

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["quantity"] == 4


def test_update_item_rejects_quantity_over_stock(client):
    register_and_login(client)
    product = make_product(client, name="Update Over Widget", stock_quantity=3)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1})

    response = client.put(f"/cart/items/{product['id']}", json={"quantity": 4})

    assert response.status_code == 400


def test_update_item_not_in_cart(client):
    register_and_login(client)
    product = make_product(client, name="Never Added Widget")

    response = client.put(f"/cart/items/{product['id']}", json={"quantity": 1})

    assert response.status_code == 404


def test_remove_item_from_cart(client):
    register_and_login(client)
    product = make_product(client, name="Remove Widget", stock_quantity=10)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1})

    response = client.delete(f"/cart/items/{product['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []


def test_remove_item_not_in_cart(client):
    register_and_login(client)
    product = make_product(client, name="Never In Cart Widget")

    response = client.delete(f"/cart/items/{product['id']}")

    assert response.status_code == 404


def test_cart_is_scoped_per_user(client):
    register_and_login(client)
    product = make_product(client, name="Scoped Widget", stock_quantity=10)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1})

    register_and_login(client)
    response = client.get("/cart")

    assert response.status_code == 200
    assert response.json()["items"] == []
