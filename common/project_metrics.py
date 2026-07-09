"""Fonte ÚNICA de verdade para métricas de projeto (progresso, status, saúde).

Usada por serializers (lista e detalhe), endpoint de métricas, dashboards e
validações. O frontend deve apenas exibir estes valores — nunca recalcular.

Regra de progresso:
  1. Se há atividades válidas → progresso = concluídas / total de atividades válidas.
  2. Senão, se há etapas (checklist) → progresso = etapas concluídas / total.
  3. Senão → 0% e has_calculation_basis = False.
"""
from datetime import date

# Status de atividade considerados CONCLUÍDOS (produtivos). Cancelada NÃO conta como
# concluída para progresso (é um encerramento, não uma entrega).
ACTIVITY_COMPLETED = {"Concluída", "Concluido", "Concluído", "Done"}
ACTIVITY_CANCELLED = {"Cancelada", "Cancelado"}
# Status pendentes que impedem conclusão do projeto.
ACTIVITY_PENDING = {"Backlog", "A fazer", "Em progresso", "Em revisao", "Em revisão", "Bloqueado"}


def _checklist_counts(project):
    items = project.checklist or []
    total = 0
    done = 0
    for it in items:
        if not isinstance(it, dict):
            continue
        total += 1
        if it.get("completed") or it.get("done"):
            done += 1
    return done, total


def compute_project_metrics(project) -> dict:
    """Retorna as métricas calculadas do projeto (fonte única)."""
    activities = list(
        project.activities.filter(deleted_at__isnull=True)
        if hasattr(project, "activities") else []
    )
    # Atividades válidas = não canceladas (canceladas não entram na base de cálculo).
    valid = [a for a in activities if (a.status or "") not in ACTIVITY_CANCELLED]
    act_total = len(valid)
    act_done = sum(1 for a in valid if (a.status or "") in ACTIVITY_COMPLETED)

    stage_done, stage_total = _checklist_counts(project)

    if act_total > 0:
        basis = "activities"
        progress = round(act_done / act_total * 100)
        has_basis = True
    elif stage_total > 0:
        basis = "stages"
        progress = round(stage_done / stage_total * 100)
        has_basis = True
    else:
        basis = "none"
        progress = 0
        has_basis = False

    pending = [a for a in valid if (a.status or "") in ACTIVITY_PENDING]
    stages_pending = stage_total - stage_done

    # Status calculado a partir do progresso e da base.
    if not has_basis:
        calculated_status = "Sem escopo"
    elif progress == 0:
        calculated_status = "Não iniciado"
    elif progress >= 100:
        calculated_status = "Concluido"
    else:
        calculated_status = "Em andamento"

    # Saúde: sem base → sem_base; senão comparar prazo x progresso.
    health = "sem_base"
    if has_basis:
        due = getattr(project, "due_at", None)
        today = date.today()
        if progress >= 100:
            health = "on_track"
        elif due and due < today:
            health = "delayed"
        elif due:
            total_days = None
            start = getattr(project, "start_at", None)
            if start:
                total_days = max(1, (due - start).days)
                elapsed = max(0, (today - start).days)
                elapsed_pct = min(100, elapsed / total_days * 100)
                if elapsed_pct > progress + 15:
                    health = "delayed"
                elif elapsed_pct > progress + 5:
                    health = "at_risk"
                else:
                    health = "on_track"
            else:
                health = "on_track"
        else:
            health = "on_track"

    can_complete = has_basis and not pending and stages_pending == 0
    if not has_basis:
        message = "Nenhuma atividade ou etapa cadastrada para calcular o progresso."
    elif pending or stages_pending:
        message = "Este projeto possui itens pendentes."
    else:
        message = "Calculado com base nas atividades." if basis == "activities" else "Calculado com base nas etapas."

    return {
        "progress": progress,
        "calculated_status": calculated_status,
        "health": health,
        "activities_count": act_total,
        "completed_activities_count": act_done,
        "pending_activities_count": len(pending),
        "stages_count": stage_total,
        "completed_stages_count": stage_done,
        "has_calculation_basis": has_basis,
        "calculation_basis": basis,
        "can_complete": can_complete,
        "calculation_message": message,
    }
