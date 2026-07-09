"""Fonte ÚNICA da regra 'um técnico participa de no máximo UMA sprint ativa'.

Sprint ativa = status 'Em andamento'. Usada pela validação de participantes,
pelo start da sprint e pelo endpoint /api/me/active-sprint/.
"""

ACTIVE_SPRINT_STATUS = "Em andamento"


def active_sprint_qs(company):
    """Sprints ativas (não deletadas) da empresa."""
    from apps.sprints.models import Sprint

    return Sprint.objects.filter(
        company=company,
        status=ACTIVE_SPRINT_STATUS,
        deleted_at__isnull=True,
    )


def user_active_sprint(user):
    """Retorna a sprint ativa em que o usuário participa, ou None."""
    from apps.sprints.models import SprintParticipant

    part = (
        SprintParticipant.objects.filter(
            user=user,
            deleted_at__isnull=True,
            sprint__status=ACTIVE_SPRINT_STATUS,
            sprint__deleted_at__isnull=True,
        )
        .select_related("sprint")
        .order_by("sprint__start_at")
        .first()
    )
    return part.sprint if part else None


def other_active_sprint_for_user(user, company, exclude_sprint_id=None):
    """Sprint ATIVA (≠ exclude) em que o usuário já participa, ou None.

    Usada para bloquear vínculo em uma segunda sprint ativa.
    """
    from apps.sprints.models import SprintParticipant

    qs = SprintParticipant.objects.filter(
        user=user,
        company=company,
        deleted_at__isnull=True,
        sprint__status=ACTIVE_SPRINT_STATUS,
        sprint__deleted_at__isnull=True,
    ).select_related("sprint")
    if exclude_sprint_id:
        qs = qs.exclude(sprint_id=exclude_sprint_id)
    part = qs.first()
    return part.sprint if part else None
