import functools

from langchain.agents import create_agent
from langchain_core.tools import tool

from app.core.llm import get_chat_model
from app.models.product import Product

SYSTEM_PROMPT = (
    "You are a shopping assistant for this store. Only answer questions about "
    "products in the store's catalog, using the search_products tool to look "
    "them up rather than guessing. If asked something unrelated to the store's "
    "products, say you can only help with questions about products in this store."
)


@tool
async def search_products(query: str) -> list[dict]:
    """Search the store's product catalog by name or description keyword."""
    products = await Product.filter(name__icontains=query).limit(5)
    if not products:
        products = await Product.filter(description__icontains=query).limit(5)
    return [
        {
            "name": p.name,
            "price": str(p.price),
            "stock_quantity": p.stock_quantity,
            "description": p.description,
        }
        for p in products
    ]


@functools.lru_cache
def _get_agent():
    return create_agent(get_chat_model(), [search_products], system_prompt=SYSTEM_PROMPT)


async def run_chat(message: str) -> str:
    agent = _get_agent()
    result = await agent.ainvoke({"messages": [("user", message)]})
    return result["messages"][-1].content
