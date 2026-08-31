import re

from langchain_core.messages import HumanMessage, SystemMessage
from tortoise.expressions import Q

from app.core.llm import get_chat_model
from app.models.product import Product

SYSTEM_PROMPT = (
    "You are a shopping assistant for this store. Answer the user's question "
    "using only the product information listed below - never invent products, "
    "prices, or stock levels. If nothing relevant is listed, say the store "
    "doesn't seem to have that. If asked something unrelated to shopping for "
    "products in this store, say you can only help with product questions."
)

STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "does", "have", "has", "any", "you",
    "your", "i", "want", "need", "looking", "for", "what", "whats", "price",
    "of", "in", "stock", "find", "show", "me", "please", "can", "could",
    "would", "like", "this", "that", "and", "or", "with",
}


def _extract_keywords(message: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]+", message.lower())
    keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return keywords or [message]


async def search_products(message: str) -> list[Product]:
    """Look up catalog products relevant to a free-text message."""
    keywords = _extract_keywords(message)
    q = Q(name__icontains=keywords[0]) | Q(description__icontains=keywords[0])
    for kw in keywords[1:]:
        q |= Q(name__icontains=kw) | Q(description__icontains=kw)
    return await Product.filter(q).limit(8)


def _format_context(products: list[Product]) -> str:
    if not products:
        return "No matching products were found in the catalog."
    lines = []
    for p in products:
        stock = f"{p.stock_quantity} in stock" if p.stock_quantity else "out of stock"
        line = f"- {p.name} — ${p.price} ({stock})"
        if p.description:
            line += f" — {p.description}"
        lines.append(line)
    return "Matching products from the catalog:\n" + "\n".join(lines)


async def run_chat(message: str) -> str:
    products = await search_products(message)
    context = _format_context(products)
    model = get_chat_model()
    response = await model.ainvoke(
        [
            SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{context}"),
            HumanMessage(content=message),
        ]
    )
    return response.content
