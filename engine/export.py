
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "deals.db"
OUTPUT_PATH = BASE_DIR / "deals.json"


def export_deals():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT product_code, product_name,
                   merchant, price, currency, product_url
            FROM products
            ORDER BY product_code, price
        """).fetchall()

    products = {}

    for code, name, merchant, price, currency, url in rows:
        key = (code, currency)

        if key not in products:
            products[key] = {
                "code": code,
                "name": name,
                "currency": currency,
                "offers": []
            }

        products[key]["offers"].append({
            "merchant": merchant,
            "price": round(price, 2),
            "url": url
        })

    deals = []

    for product in products.values():
        offers = product["offers"]
        best = min(offers, key=lambda x: x["price"])

        deals.append({
            "code": product["code"],
            "name": product["name"],
            "currency": product["currency"],
            "best_merchant": best["merchant"],
            "best_price": best["price"],
            "offers": offers
        })

    output = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "demo": True,
        "products": deals
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("VAESO Deal Radar - Export OK")
    print(f"Prodotti esportati: {len(deals)}")
    print(f"File generato: {OUTPUT_PATH}")


if __name__ == "__main__":
    export_deals()
