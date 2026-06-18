import logging
from config.celery import app

logger = logging.getLogger(__name__)


@app.task(name='apps.webhooks.tasks.deliver_webhook', bind=True, max_retries=3)
def deliver_webhook(self, webhook_id: str, event: str, payload: dict):
    from .models import Webhook
    try:
        webhook = Webhook.objects.get(id=webhook_id)
    except Webhook.DoesNotExist:
        return

    from .services import _deliver
    _deliver(webhook, event, payload)
