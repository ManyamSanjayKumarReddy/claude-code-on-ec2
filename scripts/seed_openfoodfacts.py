"""
One-off admin script: replaces the product catalog with real grocery
products pulled from Open Food Facts' bulk data export
(https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz -
freely licensed, real product names/images - not synthetic data).

Uses the bulk export (a plain streamed static file), not their live search
API - the search API rate-limits far more aggressively than documented and
proved unusable for pulling more than a handful of pages in practice. The
export is ~12.8GB compressed, but we stream-decompress it and stop reading
the moment we have enough qualifying rows - no need to download it in full.

Open Food Facts is a nutrition database, not a store, so it has no price or
stock data - those are generated here (random, clearly not real prices).

Not part of the shipped app - run manually, once, against a target database:

    DATABASE_URL=postgres://user:pass@host:5432/dbname python3 seed_openfoodfacts.py [--dry-run] [--count 100]
"""

import argparse
import asyncio
import gzip
import json
import os
import random
import re
import sys
import urllib.request

from tortoise import Tortoise

EXPORT_URL = "https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz"
IMAGE_BASE_URL = "https://images.openfoodfacts.org/images/products"
USER_AGENT = "ClaudeCodeStoreDemo/1.0 (learning project; store catalog seed script)"
MAX_LINES_SCANNED = 1_500_000

# Matched against the free-text `brands` field with word-boundary regex (not
# substring `in`, which false-matches e.g. bare "itc" against "kitchen").
# Multi-word phrases used for generic-sounding brands (catch, fortune,
# everest, real, tata) to avoid collisions with unrelated common words.
INDIAN_BRANDS = [
    "amul", "parle", "haldiram", "mdh", "patanjali", "dabur", "britannia",
    "bikaji", "bikanervala", "aashirvaad", "ashirvaad", "kurkure", "sunfeast",
    "frooti", "nirma", "wagh bakri", "kissan", "godrej", "parachute",
    "saffola", "everest masala", "catch masala", "fortune oil", "tata tea",
    "tata salt", "mother dairy", "vadilal",
    "chings", "ching's", "gits", "priya gold", "lijjat",
]
BRAND_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(b) for b in INDIAN_BRANDS) + r")\b", re.IGNORECASE
)


def code_path(code: str) -> str:
    if len(code) > 8:
        groups = [code[0:3], code[3:6], code[6:9], code[9:]]
        return "/".join(g for g in groups if g)
    return code


def front_image_url(product: dict) -> str | None:
    front = (product.get("images") or {}).get("selected", {}).get("front")
    code = product.get("code")
    if not front or not code:
        return None
    lang = next(iter(front), None)
    if not lang:
        return None
    rev = front[lang].get("rev")
    if not rev:
        return None
    return f"{IMAGE_BASE_URL}/{code_path(code)}/front_{lang}.{rev}.400.jpg"


def clean_categories(tags: list[str]) -> str:
    cleaned = []
    for tag in tags:
        name = tag.split(":", 1)[1] if ":" in tag else tag
        name = name.replace("-", " ").strip()
        if name and name.lower() != "null" and name not in cleaned:
            cleaned.append(name)
    return ", ".join(cleaned[:3])


def build_description(product: dict) -> str | None:
    bits = []
    brands = (product.get("brands") or "").strip()
    if brands:
        bits.append(brands.split(",")[0].strip())
    quantity = (product.get("quantity") or "").strip()
    if quantity:
        bits.append(quantity)
    categories = clean_categories(product.get("categories_tags") or [])
    if categories:
        bits.append(categories)
    return " · ".join(bits)[:2000] or None


def fetch_products(target_count: int) -> list[dict]:
    seen_codes: set[str] = set()
    results: list[dict] = []

    req = urllib.request.Request(EXPORT_URL, headers={"User-Agent": USER_AGENT})
    resp = urllib.request.urlopen(req, timeout=30)
    try:
        gz = gzip.GzipFile(fileobj=resp)
        for line_num, raw_line in enumerate(gz, start=1):
            if line_num % 20_000 == 0:
                print(f"  scanned {line_num} records, found {len(results)}/{target_count}...")
            if line_num > MAX_LINES_SCANNED:
                print(f"  hit scan limit ({MAX_LINES_SCANNED} lines), stopping with what we have.")
                break

            try:
                p = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            code = p.get("code")
            name = (p.get("product_name") or "").strip()
            image_url = front_image_url(p)
            is_indian_brand = bool(BRAND_PATTERN.search(p.get("brands") or ""))
            if not code or not name or not image_url or not is_indian_brand or code in seen_codes:
                continue

            seen_codes.add(code)
            p["_image_url"] = image_url
            results.append(p)
            if len(results) >= target_count:
                break
    finally:
        resp.close()

    return results


def to_row(product: dict) -> dict:
    name = product["product_name"].strip()[:200]
    price = round(random.uniform(1.5, 45.0), 2)
    stock_quantity = 0 if random.random() < 0.05 else random.randint(1, 300)
    return {
        "name": name,
        "description": build_description(product),
        "price": price,
        "stock_quantity": stock_quantity,
        "image_url": product["_image_url"][:1000],
    }


async def run(count: int, dry_run: bool) -> None:
    print(f"Streaming Open Food Facts' bulk export, looking for {count} usable products...")
    raw_products = fetch_products(count)
    print(f"Found {len(raw_products)} usable products (had name + image + unique code).")

    rows = [to_row(p) for p in raw_products]

    print("\nSample rows:")
    for row in rows[:5]:
        print(f"  - {row['name']!r} | ${row['price']} | stock={row['stock_quantity']} | {row['image_url']}")
        print(f"    desc: {row['description']}")

    if dry_run:
        print("\n--dry-run set: not touching the database.")
        return

    database_url = os.environ["DATABASE_URL"]
    await Tortoise.init(
        db_url=database_url,
        modules={"models": ["app.models.product"]},
    )
    from app.models.product import Product

    existing_count = await Product.all().count()
    deleted = await Product.all().delete()
    print(f"\nDeleted {deleted} existing product(s) (were {existing_count}).")

    await Product.bulk_create([Product(**row) for row in rows])
    total = await Product.all().count()
    print(f"Inserted {len(rows)} products. Table now has {total} rows.")

    await Tortoise.close_connections()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and "DATABASE_URL" not in os.environ:
        print("DATABASE_URL is required unless --dry-run is set.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(run(args.count, args.dry_run))
