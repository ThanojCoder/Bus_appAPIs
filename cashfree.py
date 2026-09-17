import json
import logging
import os
import requests

logger = logging.getLogger(__name__)

CASHFREE_URL = os.getenv("CASHFREE_URL", "https://sandbox.cashfree.com/pg")
CASHFREE_CLIENT_ID = os.getenv("CASHFREE_CLIENT_ID", "")
CASHFREE_CLIENT_SECRET = os.getenv("CASHFREE_CLIENT_SECRET", "")
CASHFREE_API_VERSION = os.getenv("CASHFREE_API_VERSION", "2023-08-01")


def create_cashfree_order(
    order_id: str, amount: float, customer_phone: str = "9999999999"
) -> str:
    url = f"{CASHFREE_URL}/orders"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-version": CASHFREE_API_VERSION,
        "x-client-id": CASHFREE_CLIENT_ID,
        "x-client-secret": CASHFREE_CLIENT_SECRET,
    }

    data = {
        "customer_details": {
            "customer_id": "cust_" + order_id,
            "customer_phone": customer_phone,
            "customer_name": "User",
        },
        "order_meta": {
            "return_url": "http://localhost:8000/return?order_id={order_id}",
            "notify_url": "http://localhost:8000/webhook",
        },
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"Cashfree Create Order Response: {response_data}")
        return response_data.get("payment_session_id")
    except Exception as e:
        logger.error(f"Error creating Cashfree order: {e}")
        return None


def get_upi_qr(payment_session_id: str) -> str:
    url = f"{CASHFREE_URL}/orders/sessions"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-version": CASHFREE_API_VERSION,
    }
    data = {
        "payment_session_id": payment_session_id,
        "payment_method": {"upi": {"channel": "qrcode"}},
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"Cashfree Get QR Response: {response_data}")
        payload = response_data.get("data", {}).get("payload", {})
        return payload.get("qrcode") if isinstance(payload, dict) else str(payload)
    except Exception as e:
        logger.error(f"Error fetching Cashfree QR: {e}")
        return None


def get_cashfree_order(order_id: str) -> dict:
    url = f"{CASHFREE_URL}/orders/{order_id}"
    headers = {
        "accept": "application/json",
        "x-api-version": CASHFREE_API_VERSION,
        "x-client-id": CASHFREE_CLIENT_ID,
        "x-client-secret": CASHFREE_CLIENT_SECRET,
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"Cashfree Get Order Response: {response_data}")
        return response_data
    except Exception as e:
        logger.error(f"Error fetching Cashfree order {order_id}: {e}")
        return None
