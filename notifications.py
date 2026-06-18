import os
from twilio.rest import Client
from database import get_db, utc_now

def _record(order_id, channel, recipient, status, sid=None, error=None):
    with get_db() as db:
        db.execute(
            """
            INSERT INTO notifications
                (order_id, channel, recipient, provider_sid, status, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (order_id, channel, recipient, sid, status, error, utc_now()),
        )
    if error:
        # quick console log for debugging
        print(f"Notification error [{channel}] to {recipient}: {error}")


def send_order_notifications(order: dict, items: list[dict]) -> None:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID") or os.getenv("account_sid")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN") or os.getenv("auth_token")
    owner_phone = os.getenv("OWNER_PHONE")
    sms_from = os.getenv("TWILIO_SMS_FROM") or os.getenv("sms_from")
    whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM") or os.getenv("whatsapp_from")
    whatsapp_content_sid = os.getenv("TWILIO_WHATSAPP_CONTENT_SID")

    if not account_sid or not auth_token:
        print("Twilio credentials missing; skipping notifications")
        return

    client = Client(account_sid, auth_token)
    item_summary = ", ".join(
        f"{item['quantity']}x {item['item_name']}" for item in items
    )
    owner_body = (
        f"New order {order['order_number']} from {order['customer_name']} "
        f"({order['customer_phone']}): {item_summary}. "
        f"Total Rs {order['total_paise'] / 100:.2f}."
    )
    customer_body = (
        f"Hi {order['customer_name']}, your Buttermelow order "
        f"{order['order_number']} was received. We will confirm it shortly."
    )

    # Send SMS to owner
    if owner_phone and sms_from:
        try:
            msg = client.messages.create(from_=sms_from, to=owner_phone, body=owner_body)
            _record(order["id"], "sms", owner_phone, "sent", sid=msg.sid)
        except Exception as e:
            _record(order["id"], "sms", owner_phone, "failed", error=str(e))


        # Send SMS to customer (if phone present)
    try:
        cust_phone = order.get("customer_phone")
        if cust_phone and sms_from:
            try:
                msg = client.messages.create(from_=sms_from, to=cust_phone, body=customer_body)
                _record(order["id"], "sms", cust_phone, "sent", sid=msg.sid)
            except Exception as e:
                _record(order["id"], "sms", cust_phone, "failed", error=str(e))
    except Exception:
        pass


    if whatsapp_from:
        if not whatsapp_from.startswith("whatsapp:"):
            whatsapp_from = f"whatsapp:{whatsapp_from}"
        for recipient in (owner_phone, order.get("customer_phone")):
            if not recipient:
                continue
            whatsapp_to = recipient if recipient.startswith("whatsapp:") else f"whatsapp:{recipient}"
            try:
                msg = client.messages.create(from_=whatsapp_from, to=whatsapp_to, body=owner_body if recipient == owner_phone else customer_body)
                _record(order["id"], "whatsapp", recipient, "sent", sid=msg.sid)
            except Exception as e:
                _record(order["id"], "whatsapp", recipient, "failed", error=str(e))
