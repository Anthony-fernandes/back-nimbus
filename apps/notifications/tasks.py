import logging
from config.celery import app

logger = logging.getLogger(__name__)


@app.task(name='apps.notifications.tasks.send_daily_digest')
def send_daily_digest():
    """Send daily notification digest to users who opted in."""
    from django.utils import timezone
    from datetime import timedelta
    from .models import Notification, NotificationPreference
    from .services import _send_email

    since = timezone.now() - timedelta(hours=24)

    prefs = NotificationPreference.objects.filter(
        digest_frequency='daily',
        email_enabled=True,
    ).select_related('user')

    for pref in prefs:
        user = pref.user
        if not user or not user.email:
            continue

        notifications = Notification.objects.filter(
            recipient=user,
            created_at__gte=since,
            is_read=False,
        ).order_by('-created_at')[:20]

        if not notifications.exists():
            continue

        lines = [f"Você tem {notifications.count()} notificação(ões) não lidas nas últimas 24h:\n"]
        for notif in notifications:
            lines.append(f"• [{notif.category}] {notif.title}")

        try:
            _send_email(
                user,
                title="Resumo diário de notificações",
                message="\n".join(lines),
                link="inbox",
                event="notification.digest",
            )
        except Exception as exc:
            logger.warning("Digest email failed for user %s: %s", user.id, exc)

    logger.info("Daily digest task complete for %d users", prefs.count())
