import logging

import requests
from flask import current_app as app


def send_webhook(event_type, payload):
    webhook_url = f"{app.config['WEBHOOK_URL']}"
    data = {"event": event_type, "payload": payload}

    try:
        response = requests.post(webhook_url, json=data, timeout=5)
        response.raise_for_status()
        logging.info(f"Webhook sent successfully: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send webhook: {e}")
