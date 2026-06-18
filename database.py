import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "treats_by_mimi.db")))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    email TEXT,
    address TEXT,
    order_count INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price_paise INTEGER NOT NULL CHECK(price_paise >= 0),
    image_path TEXT,
    is_available INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE,
    customer_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    fulfillment_type TEXT NOT NULL DEFAULT 'pickup',
    requested_time TEXT,
    notes TEXT,
    total_paise INTEGER NOT NULL,
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price_paise INTEGER NOT NULL,
    subtotal_paise INTEGER NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY(menu_item_id) REFERENCES menu_items(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    channel TEXT NOT NULL,
    recipient TEXT NOT NULL,
    provider_sid TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status, is_archived);
"""


SEED_MENU = [
    (
        "Mango Tres Leches",
        "Dessert Bar",
        "Soft sponge soaked in a rich three-milk blend with mango and whipped cream.",
        45000,
        "products/🍰 1. Mango Tres Leches.jpeg",
    ),
    (
        "Strawberry Tres Leches",
        "Dessert Bar",
        "Strawberry-infused milk cake finished with fresh strawberries.",
        45000,
        "products/🍓 2. Strawberry Tres Leches.jpeg",
    ),
    (
        "Signature Cheesecake",
        "Dessert Bar",
        "A smooth cheesecake over a buttery biscuit crust.",
        55000,
        "products/🍰 8. Signature Cheesecakes.jpeg",
    ),
    (
        "Celebration Cake",
        "Celebration",
        "A custom-designed cake for birthdays, anniversaries, and special moments.",
        120000,
        "products/🎂 9. Celebration Cakes.jpeg",
    ),
    (
        "Chocolate Brownie",
        "Signature Bakes",
        "A rich dark chocolate brownie with a delicate crust and fudgy center.",
        18000,
        "products/🍫 3. Chocolate Brownie.jpeg",
    ),
    (
        "Banana Chocolate Muffins",
        "Signature Bakes",
        "Moist banana muffins generously studded with bittersweet chocolate chips.",
        16000,
        "products/🧁 4. Banana Chocolate Muffins.jpeg",
    ),
    (
        "Banana Almond Cake",
        "Signature Bakes",
        "A fragrant banana loaf topped with toasted almond flakes.",
        50000,
        "products/🍰 6. Banana Almond Cake.jpeg",
    ),
    (
        "Butter Almond Cookies",
        "Artisanal Cookies",
        "Crisp, buttery cookies packed with roasted almond pieces.",
        28000,
        "products/🍪 5. Butter Almond Cookies.jpeg",
    ),
    (
        "Chocochip Butter Cookies",
        "Artisanal Cookies",
        "Classic buttery cookies loaded with melting chocolate chips.",
        28000,
        "products/🍪 7. Chocochip Butter Cookies.jpeg",
    ),
]


def initialize_database(password_hash: str, admin_username: str) -> None:
    now = utc_now()
    with get_db() as db:
        db.executescript(SCHEMA)
        db.execute(
            """
            INSERT OR IGNORE INTO admins (username, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (admin_username, password_hash, now),
        )
        existing = db.execute("SELECT COUNT(*) AS count FROM menu_items").fetchone()
        if existing["count"] == 0:
            db.executemany(
                """
                INSERT INTO menu_items
                    (name, category, description, price_paise, image_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [(*item, now, now) for item in SEED_MENU],
            )


def rows_to_dicts(rows):
    return [dict(row) for row in rows]
