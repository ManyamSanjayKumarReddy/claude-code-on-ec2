from unittest.mock import AsyncMock, patch

from app.models.product import Product
from app.services.chat import search_products


def test_search_products_finds_matching_product(client):
    async def scenario():
        await Product.create(
            name="Chocolate Spread",
            description="Hazelnut spread",
            price="5.99",
            stock_quantity=10,
        )
        return await search_products.ainvoke({"query": "Chocolate"})

    results = client.portal.call(scenario)

    assert any(r["name"] == "Chocolate Spread" for r in results)


def test_search_products_falls_back_to_description(client):
    async def scenario():
        await Product.create(
            name="Widget",
            description="Great for camping trips",
            price="9.99",
            stock_quantity=3,
        )
        return await search_products.ainvoke({"query": "camping"})

    results = client.portal.call(scenario)

    assert any(r["name"] == "Widget" for r in results)


def test_search_products_no_match_returns_empty(client):
    results = client.portal.call(search_products.ainvoke, {"query": "zzz_no_such_product_zzz"})

    assert results == []


def test_chat_endpoint_returns_agent_reply(client):
    with patch("app.api.chat.run_chat", new=AsyncMock(return_value="We have Chocolate Spread for $5.99.")):
        response = client.post("/chat", json={"message": "do you have chocolate spread?"})

    assert response.status_code == 200
    assert response.json()["reply"] == "We have Chocolate Spread for $5.99."


def test_chat_endpoint_rejects_empty_message(client):
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422
