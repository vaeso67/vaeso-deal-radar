
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


    # VAESO_AFFILIATE_IMPORT_V1
    import csv

    affiliate_path = BASE_DIR / "data" / "affiliate_products.csv"

    if affiliate_path.exists():
        with affiliate_path.open(
            newline="", encoding="utf-8-sig"
        ) as f:
            reader = csv.DictReader(f)

            for item in reader:
                price = float(item["price"])

                deals.append({
                    "code": item["product_code"],
                    "name": item["product_name"],
                    "currency": item["currency"],
                    "best_merchant": item["merchant"],
                    "best_price": price,
                    "affiliate": True,
                    "demo": False,
                    "offers": [{
                        "merchant": item["merchant"],
                        "price": price,
                        "url": item["product_url"]
                    }]
                })
    # Escludi i prodotti dimostrativi dal catalogo
    deals = [
        p for p in deals
        if p.get("affiliate") is True
    ]
    output = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "demo": False,
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
