"""Bundled demo dataset: a small e-commerce SQLite DB (the running example from
the design doc) so the pipeline is testable in one click. Deliberately includes
one UNDECLARED relationship (order_items.prod_id → products, no FK) so Agent 7
has something real to discover."""
from __future__ import annotations

import random
import sqlite3
from pathlib import Path

DDL = """
CREATE TABLE customers (
    cust_id INTEGER PRIMARY KEY,
    cust_nm TEXT NOT NULL,
    cust_email TEXT UNIQUE,
    cust_addr_zip TEXT,
    created_dt TEXT
);
CREATE TABLE products (
    prod_id INTEGER PRIMARY KEY,
    prod_nm TEXT NOT NULL,
    prod_cat TEXT,
    unit_price REAL
);
CREATE TABLE orders (
    ord_id INTEGER PRIMARY KEY,
    cust_id INTEGER REFERENCES customers(cust_id),
    ord_amt REAL,
    ord_status TEXT,
    ord_dt TEXT
);
CREATE TABLE order_items (
    ord_id INTEGER REFERENCES orders(ord_id),
    prod_id INTEGER,               -- deliberately NOT declared as FK → Agent 7 must find it
    qty INTEGER,
    unit_price REAL,
    PRIMARY KEY (ord_id, prod_id)
);
"""

FIRST = ["Aarav", "Diya", "Kabir", "Meera", "Rohan", "Sara", "Vikram", "Anaya", "Ishaan", "Priya"]
LAST = ["Sharma", "Patel", "Iyer", "Khan", "Das", "Mehta", "Reddy", "Singh", "Bose", "Nair"]
CATS = ["electronics", "apparel", "home", "books", "sports"]
STATUS = ["pending", "shipped", "delivered", "cancelled"]


def ensure_demo_db(settings) -> Path:
    path = settings.data_dir / "demo_ecommerce.db"
    if path.exists():
        return path
    rng = random.Random(42)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(DDL)
        customers = [(i, f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                      f"user{i}@example.com", f"{rng.randint(10000, 99999)}",
                      f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}")
                     for i in range(1, 61)]
        products = [(i, f"Product {i}", rng.choice(CATS), round(rng.uniform(5, 500), 2))
                    for i in range(1, 31)]
        orders, items = [], []
        oid = 0
        for _ in range(200):
            oid += 1
            cust = rng.randint(1, 60)
            n_items = rng.randint(1, 4)
            prods = rng.sample(range(1, 31), n_items)
            total = 0.0
            for p in prods:
                qty = rng.randint(1, 5)
                price = products[p - 1][3]
                total += qty * price
                items.append((oid, p, qty, price))
            orders.append((oid, cust, round(total, 2), rng.choice(STATUS),
                           f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"))
        conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)
        conn.executemany("INSERT INTO products VALUES (?,?,?,?)", products)
        conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)
        conn.executemany("INSERT INTO order_items VALUES (?,?,?,?)", items)
        conn.commit()
    finally:
        conn.close()
    return path
