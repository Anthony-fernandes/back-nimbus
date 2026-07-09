"""Hooks de pré/pós-processamento do schema OpenAPI (drf-spectacular)."""

# Rótulo amigável (singular) por módulo/tag — usado para montar o resumo de cada rota.
TAG_LABELS = {
    "auth": "autenticação", "users": "usuário", "departments": "departamento",
    "positions": "cargo", "permission-blocks": "bloco de permissões",
    "clients": "cliente", "organizations": "organização", "teams": "equipe",
    "team-members": "membro de equipe", "tickets": "chamado",
    "ticket-categories": "categoria de chamado",
    "ticket-workflow-statuses": "status do workflow",
    "ticket-comments": "comentário de chamado",
    "ticket-time-entries": "apontamento de horas do chamado",
    "ticket-attachments": "anexo de chamado", "ticket-approvals": "aprovação de chamado",
    "work-items": "ações do item", "activities": "atividade",
    "activity-comments": "comentário de atividade",
    "activity-time-entries": "apontamento de horas da atividade",
    "activity-attachments": "anexo de atividade", "activity-tags": "tag de atividade",
    "backlog": "item do backlog", "sprints": "sprint",
    "sprint-activity-plans": "plano de atividade da sprint",
    "sprint-ticket-plans": "plano de chamado da sprint",
    "sprint-participants": "participante da sprint", "projects": "projeto",
    "knowledge": "artigo da base de conhecimento", "communication": "recurso de comunicação",
    "reports": "relatório", "dashboards": "dashboard", "dashboard": "dashboard",
    "dashboard-data": "dado do dashboard", "admin-dashboard": "estatística administrativa",
    "notifications": "notificação", "notification-preferences": "preferência de notificação",
    "email-templates": "modelo de e-mail", "sla-policies": "política de SLA",
    "audit-logs": "log de auditoria", "search": "busca", "companies": "empresa",
    "webhooks": "webhook", "superadmin": "recurso de superadmin", "health": "saúde do serviço",
}

# Verbo por método HTTP; a variante "de item" (com {id}) é escolhida no hook.
_VERB_COLLECTION = {"get": "Listar", "post": "Criar"}
_VERB_ITEM = {"get": "Detalhar", "put": "Substituir", "patch": "Atualizar", "delete": "Remover"}


def add_operation_summaries(result, generator, request, public):
    """Pós-processamento: dá um resumo legível a cada operação que não tem um.

    Ex.: GET /api/users/ → 'Listar usuário'; DELETE /api/users/{id}/ → 'Remover usuário'.
    Rotas de @action (ex.: convert-to-ticket) e as já anotadas com @extend_schema
    mantêm o resumo próprio.
    """
    for path, path_item in (result.get("paths") or {}).items():
        is_item = "{" in path  # rota de detalhe (tem parâmetro, ex.: {id})
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            if operation.get("summary"):
                continue  # respeita summaries definidos manualmente
            tags = operation.get("tags") or []
            label = TAG_LABELS.get(tags[0], tags[0] if tags else "recurso")
            verb = (_VERB_ITEM if is_item else _VERB_COLLECTION).get(method)
            if not verb:
                # POST/PUT/PATCH/DELETE em coleção ou @action sem verbo padrão
                verb = {"post": "Criar", "put": "Substituir", "patch": "Atualizar",
                        "delete": "Remover"}.get(method, "")
            if verb:
                operation["summary"] = f"{verb} {label}"
    return result


def exclude_v1_duplicates(endpoints):
    """Remove as rotas duplicadas sob /api/v1/ — o frontend usa /api/.

    O projeto monta os mesmos viewsets em /api/ e /api/v1/ (compat.), o que
    duplicaria cada endpoint na documentação. Mantemos só a família /api/.
    """
    return [
        (path, path_regex, method, callback)
        for (path, path_regex, method, callback) in endpoints
        if not path.startswith("/api/v1/")
    ]
