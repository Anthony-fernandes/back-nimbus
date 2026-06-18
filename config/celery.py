import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("nimbus")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Periodic tasks (fallback hardcoded schedule).
# If django_celery_beat is installed, tasks can be managed via Django admin
# at /admin/django_celery_beat/ instead of editing this dict.
app.conf.beat_schedule = {
    "check-sla-every-30-minutes": {
        "task": "apps.tickets.tasks.check_sla_task",
        "schedule": 1800.0,  # 30 minutes
    },
    "send-daily-digest": {
        "task": "apps.notifications.tasks.send_daily_digest",
        "schedule": crontab(hour=8, minute=0),  # 8am daily
    },
    "send-weekly-ticket-report": {
        "task": "apps.reports.tasks.send_weekly_ticket_report",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),  # Monday 8am
    },
    "auto-close-stale-tickets": {
        "task": "apps.tickets.tasks.auto_close_stale_tickets",
        "schedule": crontab(hour=2, minute=0),  # 2am daily
    },
    "escalate-ticket-priorities": {
        "task": "apps.tickets.tasks.escalate_ticket_priorities",
        "schedule": crontab(hour="*/4", minute=0),  # every 4 hours
    },
}
