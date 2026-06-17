from config.celery import app


@app.task(name="apps.tickets.tasks.check_sla_task")
def check_sla_task():
    """Celery task: check SLA deadlines and send notifications."""
    from django.core.management import call_command
    call_command("check_sla")
