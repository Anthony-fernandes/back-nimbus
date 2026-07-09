"""Detecta (e opcionalmente corrige) inconsistências de dados do NimbusDesk.

Fontes únicas de verdade:
  - common/project_metrics.compute_project_metrics  (progresso/status/saúde do projeto)
  - common/active_sprint                            (uma sprint ativa por técnico)

Uso:
  python manage.py validate_consistency          # apenas relatório
  python manage.py validate_consistency --fix     # aplica correções seguras
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Detecta inconsistências (progresso/status/sprint) e opcionalmente corrige com --fix."

    def add_arguments(self, parser):
        parser.add_argument("--fix", action="store_true", help="Aplica correções seguras.")

    def handle(self, *args, **options):
        from apps.projects.models import Project
        from apps.sprints.models import Sprint, SprintParticipant
        from common.project_metrics import compute_project_metrics
        from common.active_sprint import ACTIVE_SPRINT_STATUS

        fix = options["fix"]
        issues = 0
        fixed = 0

        self.stdout.write(self.style.MIGRATE_HEADING("== Consistência: Projetos =="))

        # 1) Projeto 'Concluido' sem base de cálculo ou com itens pendentes.
        # 2) progress salvo diverge do progress calculado.
        for project in Project.objects.filter(deleted_at__isnull=True):
            m = compute_project_metrics(project)

            if project.status == "Concluido":
                if not m["has_calculation_basis"]:
                    issues += 1
                    self.stdout.write(
                        f"  [Concluído sem base] {project.name}: sem atividades/etapas."
                    )
                    if fix:
                        project.status = "Planejado"
                        project.progress = 0
                        project.save(update_fields=["status", "progress", "updated_at"])
                        fixed += 1
                elif not m["can_complete"]:
                    issues += 1
                    self.stdout.write(
                        f"  [Concluído com pendências] {project.name}: "
                        f"{m['pending_activities_count']} atividade(s) pendente(s)."
                    )
                    if fix:
                        project.status = "Em andamento"
                        project.progress = m["progress"]
                        project.save(update_fields=["status", "progress", "updated_at"])
                        fixed += 1

            if project.progress != m["progress"]:
                issues += 1
                self.stdout.write(
                    f"  [Progresso divergente] {project.name}: "
                    f"salvo={project.progress}% calculado={m['progress']}%"
                )
                if fix:
                    project.progress = m["progress"]
                    project.save(update_fields=["progress", "updated_at"])
                    fixed += 1

        self.stdout.write(self.style.MIGRATE_HEADING("== Consistência: Sprints =="))

        # 3) Técnico em mais de uma sprint ativa.
        active_sprint_ids = list(
            Sprint.objects.filter(
                status=ACTIVE_SPRINT_STATUS, deleted_at__isnull=True
            ).values_list("id", flat=True)
        )
        parts = (
            SprintParticipant.objects.filter(
                sprint_id__in=active_sprint_ids, deleted_at__isnull=True
            )
            .select_related("user", "sprint")
            .order_by("user_id", "sprint__start_at", "created_at")
        )
        by_user = {}
        for p in parts:
            by_user.setdefault(p.user_id, []).append(p)

        for user_id, plist in by_user.items():
            if len(plist) <= 1:
                continue
            issues += 1
            keep = plist[0]
            extras = plist[1:]
            name = keep.user.full_name_or_username
            sprint_names = ", ".join(f"'{p.sprint.name}'" for p in plist)
            self.stdout.write(
                f"  [Técnico em várias sprints ativas] {name}: {sprint_names} "
                f"(mantendo '{keep.sprint.name}')"
            )
            if fix:
                for p in extras:
                    p.delete()  # soft-delete via BaseModel
                    fixed += 1

        self.stdout.write("")
        summary = f"Inconsistências encontradas: {issues}"
        if fix:
            summary += f" · correções aplicadas: {fixed}"
        else:
            summary += " · rode com --fix para corrigir."
        style = self.style.SUCCESS if issues == 0 else self.style.WARNING
        self.stdout.write(style(summary))
