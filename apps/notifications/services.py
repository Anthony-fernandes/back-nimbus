"""Servico centralizado de notificacoes (inbox interna + e-mail).

Todo evento relevante da plataforma deve passar por ``notify`` /
``notify_many`` para que o usuario receba a notificacao na caixa de
entrada interna e, conforme suas preferencias, por e-mail.
"""

from __future__ import annotations

from typing import Any, Iterable

from django.conf import settings
from django.core.mail import send_mail

from .models import Notification, NotificationPreference


EVENT_CATEGORY = {
    "ticket.created": "Chamados",
    "ticket.approval_requested": "Aprovacoes",
    "ticket.approved": "Aprovacoes",
    "ticket.rejected": "Aprovacoes",
    "ticket.changes_requested": "Aprovacoes",
    "ticket.converted": "Chamados",
    "ticket.assigned": "Chamados",
    "ticket.priority_changed": "Chamados",
    "ticket.closed": "Chamados",
    "ticket.comment": "Comentarios",
    "project.created": "Projetos",
    "activity.created": "Atividades",
    "activity.assigned": "Atividades",
    "activity.sprint_added": "Atividades",
    "activity.comment": "Comentarios",
    "comment.added": "Comentarios",
}


def _preference(user: Any) -> NotificationPreference | None:
    if user is None or not getattr(user, "pk", None):
        return None

    pref, _ = NotificationPreference.objects.get_or_create(
        user=user,
        defaults={"company": getattr(user, "company", None)},
    )
    return pref


def _send_email(recipient: Any, title: str, message: str, link: str, event: str = "", context: dict | None = None) -> None:
    subject = title
    body = message or title

    if event and context and getattr(recipient, "company", None):
        from apps.notifications.email_templates import get_email_template, render_template
        tmpl = get_email_template(recipient.company, event)
        if tmpl.get("subject"):
            subject = render_template(tmpl["subject"], context)
        if tmpl.get("body"):
            body = render_template(tmpl["body"], context)

    web = getattr(settings, "PLATFORM_WEB_URL", "")
    if link and web and "\n" not in body:
        body = f"{body}\n\nAcesse: {web.rstrip('/')}/{link.lstrip('/')}"

    try:
        send_mail(
            subject=f"[Stratos Suite] {subject}",
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[recipient.email],
            fail_silently=True,
        )
    except Exception:
        # Notificacao por e-mail nunca pode quebrar o fluxo principal.
        pass


def notify(
    recipient: Any,
    *,
    title: str,
    event: str = "",
    category: str | None = None,
    message: str = "",
    company: Any = None,
    actor: Any = None,
    link: str = "",
    entity: Any = None,
    entity_type: str = "",
    entity_id: str = "",
    origin: str = "",
    metadata: dict | None = None,
    send_email: bool = True,
) -> Notification | None:
    if recipient is None or not getattr(recipient, "pk", None):
        return None

    # Nao notificar o proprio autor da acao.
    if actor is not None and getattr(actor, "pk", None) == recipient.pk:
        return None

    category = category or EVENT_CATEGORY.get(event, "Sistema")
    company = company or getattr(recipient, "company", None)

    if entity is not None:
        entity_type = entity_type or entity.__class__.__name__
        entity_id = entity_id or str(getattr(entity, "id", "") or "")

    pref = _preference(recipient)

    notification = None
    if not pref or (pref.inbox_enabled and event not in (pref.disabled_events or [])):
        notification = Notification.objects.create(
            company=company,
            recipient=recipient,
            actor=actor if getattr(actor, "pk", None) else None,
            actor_name=getattr(actor, "full_name_or_username", "") if actor else "",
            category=category,
            event=event,
            origin=origin,
            title=title,
            message=message,
            link=link,
            entity_type=entity_type or "",
            entity_id=str(entity_id or ""),
            metadata=metadata or {},
        )

    if send_email and getattr(recipient, "email", ""):
        allow_email = True
        if pref:
            allow_email = pref.email_enabled and event not in (pref.email_disabled_events or [])
        if allow_email:
            email_context = metadata or {}
            _send_email(recipient, title, message, link, event=event, context=email_context)
            if notification:
                notification.email_sent = True
                notification.save(update_fields=["email_sent", "updated_at"])

    return notification


def notify_many(recipients: Iterable[Any], **kwargs) -> list[Notification | None]:
    results: list[Notification | None] = []
    seen: set = set()

    for recipient in recipients:
        if recipient is None or not getattr(recipient, "pk", None) or recipient.pk in seen:
            continue
        seen.add(recipient.pk)
        results.append(notify(recipient, **kwargs))

    return results
