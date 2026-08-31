from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.product import Product
from app.services.chat import run_chat, search_products


def test_search_products_finds_matching_product(client):
    async def scenario():
        await Product.create(
            name="Chocolate Spread",
            description="Hazelnut spread",
            price="5.99",
            stock_quantity=10,
        )
        return await search_products("Do you have any chocolate spread?")

    results = client.portal.call(scenario)

    assert any(r.name == "Chocolate Spread" for r in results)


def test_search_products_falls_back_to_description(client):
    async def scenario():
        await Product.create(
            name="Widget",
            description="Great for camping trips",
            price="9.99",
            stock_quantity=3,
        )
        return await search_products("anything good for camping?")

    results = client.portal.call(scenario)

    assert any(r.name == "Widget" for r in results)


def test_search_products_no_match_returns_empty(client):
    results = client.portal.call(search_products, "xqzzptlkgnonexistent")

    assert results == []


def test_run_chat_returns_matched_products(client):
    async def scenario():
        await Product.create(
            name="Ginger Tea",
            description="Spiced tea blend",
            price="4.50",
            stock_quantity=20,
            image_url="https://example.com/ginger-tea.jpg",
        )
        fake_model = MagicMock()
        fake_model.ainvoke = AsyncMock(return_value=SimpleNamespace(content="We have Ginger Tea for $4.50."))
        with patch("app.services.chat.get_chat_model", return_value=fake_model):
            return await run_chat("Do you have ginger tea?")

    reply, products = client.portal.call(scenario)

    assert "Ginger Tea" in reply
    assert any(p.name == "Ginger Tea" and p.image_url == "https://example.com/ginger-tea.jpg" for p in products)


def test_chat_endpoint_returns_reply_and_products(client):
    fake_product = SimpleNamespace(
        id=1, name="Chocolate Spread", price="5.99", image_url=None, stock_quantity=10
    )
    with patch(
        "app.api.chat.run_chat",
        new=AsyncMock(return_value=("We have Chocolate Spread for $5.99.", [fake_product])),
    ):
        response = client.post("/chat", json={"message": "do you have chocolate spread?"})

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "We have Chocolate Spread for $5.99."
    assert body["products"][0]["name"] == "Chocolate Spread"


def test_chat_endpoint_rejects_empty_message(client):
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_endpoint_returns_503_when_llm_not_configured(client):
    response = client.post("/chat", json={"message": "hi"})

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
