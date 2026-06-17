DEFAULT_EMAIL_TEMPLATES = {
    "ticket_created": {
        "subject": "Novo chamado: {{ticket_title}}",
        "body": "<p>Olá, {{user_name}}!</p><p>Novo chamado: <strong>{{ticket_title}}</strong> ({{ticket_code}}).</p><p><a href='{{ticket_url}}'>Ver chamado</a></p>",
    },
    "ticket_status_changed": {
        "subject": "Chamado {{ticket_code}} atualizado: {{new_status}}",
        "body": "<p>Olá, {{user_name}}!</p><p>Status de <strong>{{ticket_title}}</strong> alterado para <strong>{{new_status}}</strong>.</p><p><a href='{{ticket_url}}'>Ver chamado</a></p>",
    },
    "ticket_approval_requested": {
        "subject": "Aprovação solicitada: {{ticket_title}}",
        "body": "<p>Olá, {{user_name}}!</p><p>O chamado <strong>{{ticket_title}}</strong> aguarda sua aprovação.</p><p><a href='{{ticket_url}}'>Revisar e decidir</a></p>",
    },
    "ticket_approved": {
        "subject": "Chamado aprovado: {{ticket_title}}",
        "body": "<p>Olá, {{user_name}}!</p><p>O chamado <strong>{{ticket_title}}</strong> foi <strong>aprovado</strong>.</p><p><a href='{{ticket_url}}'>Ver chamado</a></p>",
    },
    "ticket_rejected": {
        "subject": "Chamado reprovado: {{ticket_title}}",
        "body": "<p>Olá, {{user_name}}!</p><p>O chamado <strong>{{ticket_title}}</strong> foi <strong>reprovado</strong>.</p><p><a href='{{ticket_url}}'>Ver chamado</a></p>",
    },
    "ticket_comment": {
        "subject": "Novo comentário em {{ticket_title}}",
        "body": "<p>Olá, {{user_name}}!</p><p>Novo comentário no chamado <strong>{{ticket_title}}</strong>.</p><p><a href='{{ticket_url}}'>Ver chamado</a></p>",
    },
    "activity_assigned": {
        "subject": "Nova atividade: {{activity_title}}",
        "body": "<p>Olá, {{user_name}}!</p><p>A atividade <strong>{{activity_title}}</strong> foi atribuída a você.</p>",
    },
}

EVENT_LABEL = {
    "ticket_created": "Chamado criado",
    "ticket_status_changed": "Status do chamado alterado",
    "ticket_approval_requested": "Aprovação solicitada",
    "ticket_approved": "Chamado aprovado",
    "ticket_rejected": "Chamado reprovado",
    "ticket_comment": "Comentário em chamado",
    "activity_assigned": "Atividade atribuída",
}


def render_template(template_str: str, context: dict) -> str:
    for key, value in context.items():
        template_str = template_str.replace(f"{{{{{key}}}}}", str(value or ""))
    return template_str


def get_email_template(company, event: str) -> dict:
    try:
        from apps.notifications.models import EmailTemplate
        tmpl = EmailTemplate.objects.get(company=company, event=event, active=True)
        return {"subject": tmpl.subject, "body": tmpl.body}
    except Exception:
        pass
    return DEFAULT_EMAIL_TEMPLATES.get(event, {"subject": "", "body": ""})
