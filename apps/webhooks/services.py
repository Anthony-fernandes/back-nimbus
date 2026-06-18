import hashlib
import hmac
import json
import logging
import threading
import time

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)


def dispatch_webhook(company, event: str, payload: dict) -> None:
    """Fire all active webhooks for this company+event in a background thread."""
    from .models import Webhook
    webhooks = Webhook.objects.filter(
        company=company,
        active=True,
        deleted_at__isnull=True,
    )
    webhooks = [w for w in webhooks if event in (w.events or [])]
    if not webhooks:
        return
    for webhook in webhooks:
        t = threading.Thread(target=_deliver, args=(webhook, event, payload), daemon=True)
        t.start()


def _deliver(webhook, event: str, payload: dict) -> None:
    from .models import WebhookDelivery
    body = json.dumps({"event": event, "timestamp": timezone.now().isoformat(), "data": payload})
    headers = {"Content-Type": "application/json", "X-Nimbus-Event": event}

    if webhook.secret:
        sig = hmac.new(webhook.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        headers["X-Nimbus-Signature"] = f"sha256={sig}"

    status_code = None
    response_body = ""
    success = False
    error = ""

    for attempt in range(3):
        try:
            resp = requests.post(webhook.url, data=body, headers=headers, timeout=10)
            status_code = resp.status_code
            response_body = resp.text[:2000]
            success = 200 <= resp.status_code < 300
            if success:
                break
            error = f"HTTP {status_code}"
        except Exception as exc:
            error = str(exc)
            logger.warning("Webhook delivery attempt %d failed for %s: %s", attempt + 1, webhook.url, exc)
        if not success and attempt < 2:
            time.sleep(2 ** attempt)

    WebhookDelivery.objects.create(
        webhook=webhook,
        event=event,
        payload=payload,
        status_code=status_code,
        response_body=response_body,
        success=success,
        error=error,
    )
    webhook.last_triggered_at = timezone.now()
    webhook.last_status_code = status_code
    webhook.save(update_fields=["last_triggered_at", "last_status_code", "updated_at"])
