import os
os.environ["ADMIN_USERNAME"] = "owner"
os.environ["ADMIN_PASSWORD"] = "Sweety@1234"
os.environ["SESSION_SECRET"] = "test-session-secret"

from app import app
import database
from fastapi.testclient import TestClient


def setup_module():
    database.DATABASE_PATH.unlink(missing_ok=True)


def test_customer_order_and_returning_customer_tracking():
    with TestClient(app) as client:
        menu = client.get("/api/menu")
        assert menu.status_code == 200
        item = menu.json()[0]

        payload = {
            "customer": {
                "name": "Test Customer",
                "phone": "8125940747",
                "email": "test@example.com",
                "address": "",
            },
            "fulfillment_type": "pickup",
            "notes": "Test order",
            "items": [{"id": item["id"], "quantity": 2}],
        }
        first = client.post("/api/orders", json=payload)
        assert first.status_code == 200
        assert first.json()["returning_customer"] is False
        assert first.json()["order_number"] == "TBM-00001"

        second = client.post("/api/orders", json=payload)
        assert second.status_code == 200
        assert second.json()["returning_customer"] is True

        with database.get_db() as db:
            customer = db.execute(
                "SELECT * FROM customers WHERE phone = ?", ("+918125940747",)
            ).fetchone()
            assert customer["order_count"] == 2
            assert db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 2
            assert db.execute(
                "SELECT COUNT(*) FROM order_items").fetchone()[0] == 2


def test_owner_login_status_and_archive_flow():
    with TestClient(app) as client:
        login = client.post(
            "/owner/login",
            data={"username": "owner", "password": "Sweety@1234"},
            follow_redirects=False,
        )
        assert login.status_code == 303
        dashboard = client.get("/owner")
        assert dashboard.status_code == 200
        assert "TBM-00001" in dashboard.text
        assert "Returning customer" in dashboard.text

        status = client.post(
            "/owner/orders/1/status",
            data={"status": "completed"},
            follow_redirects=False,
        )
        assert status.status_code == 303
        archive = client.post("/owner/orders/1/archive",
                              follow_redirects=False)
        assert archive.status_code == 303

        with database.get_db() as db:
            order = db.execute("SELECT * FROM orders WHERE id = 1").fetchone()
            assert order["status"] == "completed"
            assert order["is_archived"] == 1


def test_delivery_requires_address():
    with TestClient(app) as client:
        item = client.get("/api/menu").json()[0]
        response = client.post(
            "/api/orders",
            json={
                "customer": {"name": "Delivery Customer", "phone": "+919999999999"},
                "fulfillment_type": "delivery",
                "items": [{"id": item["id"], "quantity": 1}],
            },
        )
        assert response.status_code == 400
        assert "address" in response.json()["detail"].lower()


def test_menu_item_update_and_delete():
    with TestClient(app) as client:
        # Login
        login = client.post(
            "/owner/login",
            data={"username": "owner", "password": "Sweety@1234"},
            follow_redirects=True,
        )
        assert login.status_code == 200

        # Get first item
        with database.get_db() as db:
            item = db.execute("SELECT * FROM menu_items LIMIT 1").fetchone()
            item_id = item["id"]

        # Update it (e.g. rename, change price and make unavailable)
        update_res = client.post(
            f"/owner/menu/{item_id}",
            data={
                "name": "Updated Name",
                "category": item["category"],
                "description": "New description text",
                "price": 99.99,
                # is_available omitted -> becomes 0 (unavailable)
            },
            follow_redirects=True,
        )
        assert update_res.status_code == 200

        # Verify update
        with database.get_db() as db:
            updated = db.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,)).fetchone()
            assert updated["name"] == "Updated Name"
            assert updated["description"] == "New description text"
            assert updated["price_paise"] == 9999
            assert updated["is_available"] == 0

        # Delete it
        delete_res = client.post(
            f"/owner/menu/{item_id}/delete",
            follow_redirects=True,
        )
        assert delete_res.status_code == 200

        # Verify deletion
        with database.get_db() as db:
            deleted = db.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,)).fetchone()
            assert deleted is None

