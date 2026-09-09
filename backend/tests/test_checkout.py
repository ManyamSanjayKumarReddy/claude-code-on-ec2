import uuid


def unique_email():
    return f"checkout-user-{uuid.uuid4().hex}@example.com"


def register_and_login(client):
    client.cookies.clear()
    payload = {
        "email": unique_email(),
        "password": "supersecret123",
        "full_name": "Checkout Tester",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    return payload


def make_product(client, **overrides):
    payload = {
        "name": "Checkout Widget",
        "description": "A widget used in checkout tests",
        "price": "10.00",
        "stock_quantity": 5,
    }
    payload.update(overrides)
    return client.post("/products", json=payload).json()


def checkout_payload(**overrides):
    payload = {
        "recipient_name": "Jane Doe",
        "address_line1": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "postal_code": "62701",
        "country": "USA",
        "shipping_method": "standard",
    }
    payload.update(overrides)
    return payload


def test_list_shipping_methods(client):
    response = client.get("/checkout/shipping-methods")

    assert response.status_code == 200
    codes = [m["code"] for m in response.json()]
    assert "standard" in codes
    assert "express" in codes


def test_checkout_requires_authentication(client):
    client.cookies.clear()

    response = client.post("/checkout", json=checkout_payload())

    assert response.status_code == 401


def test_checkout_rejects_empty_cart(client):
    register_and_login(client)

    response = client.post("/checkout", json=checkout_payload())

    assert response.status_code == 400


def test_checkout_rejects_unknown_shipping_method(client):
    register_and_login(client)
    product = make_product(client)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1})

    response = client.post("/checkout", json=checkout_payload(shipping_method="teleport"))

    assert response.status_code == 400


def test_checkout_creates_order_and_clears_cart(client):
    register_and_login(client)
    product = make_product(client, name="Order Widget", price="10.00", stock_quantity=5)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 2})

    response = client.post("/checkout", json=checkout_payload(shipping_method="standard"))

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "placed"
    assert body["subtotal"] == "20.00"
    assert body["shipping_cost"] == "5.00"
    assert body["total"] == "25.00"
    assert len(body["items"]) == 1
    assert body["items"][0]["product_name"] == "Order Widget"
    assert body["items"][0]["quantity"] == 2

    cart_response = client.get("/cart")
    assert cart_response.json()["items"] == []


def test_checkout_decrements_product_stock(client):
    register_and_login(client)
    product = make_product(client, name="Stock Widget", stock_quantity=5)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 3})

    client.post("/checkout", json=checkout_payload())

    updated = client.get(f"/products/{product['id']}").json()
    assert updated["stock_quantity"] == 2


def test_checkout_rejects_quantity_over_stock(client):
    register_and_login(client)
    product = make_product(client, name="Overselling Widget", stock_quantity=2)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 2})
    # Someone else's order (simulated by shrinking stock directly) undercuts availability.
    client.put(f"/products/{product['id']}", json={"name": "Overselling Widget", "price": "10.00", "stock_quantity": 1})

    response = client.post("/checkout", json=checkout_payload())

    assert response.status_code == 400


def test_list_orders_returns_created_order(client):
    register_and_login(client)
    product = make_product(client, name="List Order Widget", stock_quantity=5)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1})
    created = client.post("/checkout", json=checkout_payload()).json()

    response = client.get("/orders")

    assert response.status_code == 200
    ids = [o["id"] for o in response.json()]
    assert created["id"] in ids


def test_get_order_by_id(client):
    register_and_login(client)
    product = make_product(client, name="Get Order Widget", stock_quantity=5)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1})
    created = client.post("/checkout", json=checkout_payload()).json()

    response = client.get(f"/orders/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_order_not_found(client):
    register_and_login(client)

    response = client.get("/orders/999999")

    assert response.status_code == 404


def test_orders_are_scoped_per_user(client):
    register_and_login(client)
    product = make_product(client, name="Scoped Order Widget", stock_quantity=5)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1})
    created = client.post("/checkout", json=checkout_payload()).json()

    register_and_login(client)
    response = client.get(f"/orders/{created['id']}")

    assert response.status_code == 404
