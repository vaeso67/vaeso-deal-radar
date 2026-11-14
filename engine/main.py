
import csv
import sqlite3
from pathlib import Path
from decimal import Decimal, InvalidOperation

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "deals.db"
CSV_PATH = BASE_DIR / "data" / "products.csv"


def initialize_database(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT NOT NULL,
            product_name TEXT NOT NULL,
            merchant TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            currency TEXT NOT NULL DEFAULT 'EUR',
            product_url TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(product_code, merchant)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)


def import_products(conn):
    count = 0

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            code = row["product_code"].strip()
            name = row["product_name"].strip()
            merchant = row["merchant"].strip()
            currency = row["currency"].strip().upper()
            url = row["product_url"].strip()

            try:
                price = float(Decimal(row["price"].strip()))
            except (InvalidOperation, ValueError):
                print(f"Prezzo non valido: {code}")
                continue

            if not code or not name or not merchant or price < 0:
                print(f"Record non valido: {row}")
                continue

            existing = conn.execute("""
                SELECT id, price FROM products
                WHERE product_code = ? AND merchant = ?
            """, (code, merchant)).fetchone()

            if existing:
                product_id, old_price = existing

                if round(old_price, 2) != round(price, 2):
                    conn.execute("""
                        UPDATE products
                        SET product_name = ?, price = ?,
                            currency = ?, product_url = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (name, price, currency, url, product_id))

                    conn.execute("""
                        INSERT INTO price_history (product_id, price)
                        VALUES (?, ?)
                    """, (product_id, price))
            else:
                cursor = conn.execute("""
                    INSERT INTO products
                    (product_code, product_name, merchant,
                     price, currency, product_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (code, name, merchant, price, currency, url))

                conn.execute("""
                    INSERT INTO price_history (product_id, price)
                    VALUES (?, ?)
                """, (cursor.lastrowid, price))

            count += 1

    print(f"Prodotti elaborati: {count}")


def compare_prices(conn):
    rows = conn.execute("""
        SELECT product_code, product_name, merchant,
               price, currency
        FROM products
        ORDER BY product_code, price ASC
    """).fetchall()

    products = {}

    for code, name, merchant, price, currency in rows:
        products.setdefault(code, []).append(
            (name, merchant, price, currency)
        )

    print("\n=== VAESO PRICE COMPARISON ===")

    for code, offers in products.items():
        name = offers[0][0]
        currency = offers[0][3]
        same_currency = [
            offer for offer in offers if offer[3] == currency
        ]

        print(f"\n{name} [{code}]")

        for _, merchant, price, curr in offers:
            print(f"  {merchant}: {price:.2f} {curr}")

        if len(same_currency) == len(offers):
            best = min(offers, key=lambda x: x[2])
            print(
                f"  MIGLIORE: {best[1]} "
                f"- {best[2]:.2f} {best[3]}"
            )
        else:
            print("  Valute differenti: confronto non disponibile")


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        initialize_database(conn)
        import_products(conn)
        compare_prices(conn)
        conn.commit()

    print("\nVAESO Deal Radar Engine: OK")


if __name__ == "__main__":
    main()
