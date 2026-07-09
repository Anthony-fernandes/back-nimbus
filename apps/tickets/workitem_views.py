"""Endpoint unificado de ações disponíveis por item/status (workflow dinâmico)."""
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.status_rules import ALL_PERMS, resolve_status_rule

ACTION_LABELS = {
    "allows_edit": "Editar",
    "allows_comment": "Comentar",
    "allows_attachment": "Anexar",
    "allows_assignment": "Alterar responsável",
    "allows_priority_change": "Alterar prioridade",
    "allows_send_to_sprint": "Enviar para sprint",
    "allows_backlog": "Enviar para backlog",
    "allows_start_work": "Iniciar atendimento",
    "allows_pause": "Pausar",
    "allows_resume": "Retomar",
    "allows_send_to_validation": "Enviar para validação",
    "allows_finish": "Finalizar",
    "allows_cancel": "Cancelar",
    "allows_reopen": "Reabrir",
}


@extend_schema(
    tags=["work-items"],
    summary="Ações disponíveis por item e status (workflow dinâmico)",
    description="Retorna as ações permitidas/bloqueadas, transições e exigências do "
    "status atual de um chamado ou atividade, segundo o workflow configurável.",
    parameters=[
        OpenApiParameter("item_type", str, OpenApiParameter.PATH, enum=["ticket", "activity"]),
        OpenApiParameter("pk", str, OpenApiParameter.PATH, description="UUID do item"),
    ],
    responses={200: dict},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def available_actions(request, item_type, pk):
    if item_type not in ("ticket", "activity"):
        return Response({"detail": "Tipo inválido. Use ticket ou activity."}, status=400)

    company = request.user.company
    if item_type == "ticket":
        from apps.tickets.models import Ticket
        try:
            item = Ticket.objects.get(pk=pk, company=company)
        except Ticket.DoesNotExist:
            return Response({"detail": "Chamado não encontrado."}, status=404)
        status_name = item.status or "Aberto"
    else:
        from apps.activities.models import Activity
        try:
            item = Activity.objects.get(pk=pk, company=company)
        except Activity.DoesNotExist:
            return Response({"detail": "Atividade não encontrada."}, status=404)
        status_name = item.status or "Backlog"

    rule = resolve_status_rule(company, item_type, status_name)
    if not rule["found"]:
        return Response({
            "status": status_name,
            "configured": False,
            "detail": f"O status '{status_name}' não possui regras configuradas. "
                      "Configure o workflow em Configurações.",
            "actions": {}, "blocked": {}, "transitions": [],
            "permissions": {}, "requirements": {},
        })

    actions = {}
    blocked = {}
    for perm in ALL_PERMS:
        label = ACTION_LABELS[perm]
        if rule["permissions"].get(perm):
            actions[perm] = label
        else:
            blocked[perm] = f"'{label}' não é permitido com o item em '{status_name}'."

    return Response({
        "status": status_name,
        "configured": True,
        "phase": rule["phase"],
        "is_final": rule["is_final"],
        "custom": rule["custom"],
        "actions": actions,
        "blocked": blocked,
        "transitions": rule["transitions"],
        "permissions": rule["permissions"],
        "requirements": rule["requirements"],
    })
