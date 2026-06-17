from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.activities.models import Activity, ActivityTag
from apps.clients.models import Client
from apps.companies.models import Company
from apps.projects.models import Project, ProjectMember
from apps.sprints.models import Sprint
from apps.tickets.models import Ticket, TicketCategory
from apps.users.models import PermissionBlock, UserOrganization
from common.access import INITIAL_PERMISSION_BLOCKS, flatten_granted_permissions


class Command(BaseCommand):
    help = "Cria dados demonstrativos coerentes com organizacoes, usuarios e workflow atual."

    def handle(self, *args, **options):
        User = get_user_model()

        company, _ = Company.objects.get_or_create(
            name="Nimbus Workspace",
            defaults={
                "email": "contato@nimbus.local",
                "phone": "(83) 3020-0000",
            },
        )

        admin, admin_created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@nimbus.local",
                "first_name": "Alex",
                "last_name": "Admin",
                "role": "ADMIN",
                "company": company,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.email = "admin@nimbus.local"
        admin.first_name = "Alex"
        admin.last_name = "Admin"
        admin.role = "ADMIN"
        admin.company = company
        admin.is_staff = True
        admin.is_superuser = True
        if admin_created:
            admin.set_password("admin123")
        admin.save()

        organizations = self._create_organizations(company)
        users = self._create_users(User, company, organizations)
        permission_blocks = self._create_permission_blocks(company)
        self._apply_user_permissions(users, permission_blocks)
        self._create_user_links(company, organizations, users)
        self._create_tags(company)
        categories = self._create_ticket_categories(company)
        projects = self._create_projects(company, organizations, users)
        sprint = self._create_sprint(company, projects, users)
        tickets = self._create_tickets(company, organizations, users, projects, sprint, categories)
        self._create_activities(company, users, sprint, tickets)

        self.stdout.write(self.style.SUCCESS("Base demo recriada. Login: admin / admin123"))

    def _create_organizations(self, company):
        organization_defs = [
            {
                "name": "Cliente ABC",
                "organization_type": "CLIENTE_EMPRESA",
                "email": "contato@clienteabc.com",
                "phone": "(11) 4000-1000",
                "contact_name": "Maria Souza",
                "plan": "Enterprise",
                "health": "Otimo",
            },
            {
                "name": "Financeiro",
                "organization_type": "DEPARTAMENTO",
                "email": "financeiro@nimbus.local",
                "phone": "(83) 4000-2000",
                "contact_name": "Roberto Lima",
                "plan": "Interno",
                "health": "Bom",
            },
            {
                "name": "RH",
                "organization_type": "DEPARTAMENTO",
                "email": "rh@nimbus.local",
                "phone": "(83) 4000-3000",
                "contact_name": "Patricia Alves",
                "plan": "Interno",
                "health": "Bom",
            },
        ]

        organizations = {}
        for payload in organization_defs:
            organization, _ = Client.objects.get_or_create(
                company=company,
                name=payload["name"],
                defaults={
                    **payload,
                    "status": "Ativo",
                    "active": True,
                    "sector": payload["name"],
                    "address": "",
                    "notes": "",
                    "mrr": Decimal("0"),
                },
            )
            organizations[payload["name"]] = organization

        return organizations

    def _create_users(self, User, company, organizations):
        user_defs = [
            {
                "username": "pedro.tecnico",
                "email": "pedro.tecnico@nimbus.local",
                "first_name": "Pedro",
                "last_name": "Silva",
                "role": "TECHNICIAN",
                "job_title": "Tecnico Senior",
                "specialty": "Infra / Suporte",
                "phone": "(83) 99999-1001",
                "total_hours": 40,
                "used_hours": 24,
                "hourly_cost": Decimal("95"),
                "technical_group": "Suporte N2",
            },
            {
                "username": "bia.analista",
                "email": "bia.analista@nimbus.local",
                "first_name": "Bia",
                "last_name": "Lima",
                "role": "TECHNICIAN",
                "job_title": "Analista de Sistemas",
                "specialty": "Backend / API",
                "phone": "(83) 99999-1002",
                "total_hours": 40,
                "used_hours": 20,
                "hourly_cost": Decimal("110"),
                "technical_group": "Desenvolvimento",
            },
            {
                "username": "lucas.gestor",
                "email": "lucas.gestor@nimbus.local",
                "first_name": "Lucas",
                "last_name": "Pereira",
                "role": "TECHNICIAN",
                "job_title": "Gestor de Operacoes",
                "specialty": "Projetos / Atendimento",
                "phone": "(83) 99999-1003",
                "total_hours": 40,
                "used_hours": 18,
                "hourly_cost": Decimal("140"),
                "technical_group": "Gestao",
            },
            {
                "username": "joao.abc",
                "email": "joao@clienteabc.com",
                "first_name": "Joao",
                "last_name": "Martins",
                "role": "CLIENT",
                "job_title": "Solicitante",
                "specialty": "Cliente ABC",
                "phone": "(11) 98888-1000",
                "client": organizations["Cliente ABC"],
            },
            {
                "username": "maria.abc",
                "email": "maria@clienteabc.com",
                "first_name": "Maria",
                "last_name": "Souza",
                "role": "CLIENT",
                "job_title": "Gerente de TI",
                "specialty": "Cliente ABC",
                "phone": "(11) 97777-1000",
                "client": organizations["Cliente ABC"],
            },
            {
                "username": "carla.financeiro",
                "email": "carla.financeiro@nimbus.local",
                "first_name": "Carla",
                "last_name": "Oliveira",
                "role": "CLIENT",
                "job_title": "Analista Financeiro",
                "specialty": "Financeiro",
                "phone": "(83) 98888-2000",
                "client": organizations["Financeiro"],
            },
            {
                "username": "roberto.financeiro",
                "email": "roberto.financeiro@nimbus.local",
                "first_name": "Roberto",
                "last_name": "Lima",
                "role": "CLIENT",
                "job_title": "Coordenador Financeiro",
                "specialty": "Financeiro",
                "phone": "(83) 97777-2000",
                "client": organizations["Financeiro"],
            },
        ]

        users = {}
        for payload in user_defs:
            defaults = {
                "company": company,
                "email": payload["email"],
                "first_name": payload["first_name"],
                "last_name": payload["last_name"],
                "role": payload["role"],
                "job_title": payload.get("job_title", ""),
                "specialty": payload.get("specialty", ""),
                "phone": payload.get("phone", ""),
                "total_hours": payload.get("total_hours", 40),
                "used_hours": payload.get("used_hours", 0),
                "hourly_cost": payload.get("hourly_cost", Decimal("0")),
                "technical_group": payload.get("technical_group", ""),
                "client": payload.get("client"),
            }
            user, created = User.objects.get_or_create(
                username=payload["username"],
                defaults=defaults,
            )
            for key, value in defaults.items():
                setattr(user, key, value)
            if created:
                user.set_password("admin123")
            user.save()
            users[payload["username"]] = user

        return users

    def _create_permission_blocks(self, company):
        blocks = {}

        for definition in INITIAL_PERMISSION_BLOCKS:
            block, _ = PermissionBlock.objects.get_or_create(
                company=company,
                name=definition["name"],
                defaults={
                    "description": definition.get("description", ""),
                    "permissions": definition.get("permissions", {}),
                    "active": True,
                },
            )
            block.description = definition.get("description", "")
            block.permissions = definition.get("permissions", {})
            block.active = True
            block.save()
            blocks[block.name] = block

        return blocks

    def _apply_user_permissions(self, users, permission_blocks):
        users["pedro.tecnico"].permission_blocks.set([permission_blocks["Suporte N2"]])
        users["bia.analista"].permission_blocks.set([permission_blocks["Dev"]])
        users["joao.abc"].permission_blocks.clear()
        users["maria.abc"].permission_blocks.set([permission_blocks["Gestor Cliente"]])
        users["carla.financeiro"].permission_blocks.clear()
        users["roberto.financeiro"].permission_blocks.set([permission_blocks["Gestor Cliente"]])

        lucas = users["lucas.gestor"]
        lucas.permission_blocks.set([permission_blocks["Administrador de permissoes"]])
        lucas.granted_permissions = {
            "projects": {"create": True, "edit": True, "manage": True},
            "sprints": {"create": True, "edit": True, "manage": True},
            "reports": {"view": True},
            "tickets": {"assign": True, "approve": True},
        }
        lucas.denied_permissions = {}
        lucas.permissions_json = flatten_granted_permissions(lucas.granted_permissions)
        lucas.save(update_fields=["granted_permissions", "denied_permissions", "permissions_json"])

        for username in ["pedro.tecnico", "bia.analista", "joao.abc", "maria.abc", "carla.financeiro", "roberto.financeiro"]:
            user = users[username]
            user.denied_permissions = {}
            if not user.granted_permissions:
                user.granted_permissions = {}
            user.permissions_json = flatten_granted_permissions(user.granted_permissions)
            user.save(update_fields=["granted_permissions", "denied_permissions", "permissions_json"])

    def _create_user_links(self, company, organizations, users):
        link_defs = [
            ("joao.abc", "Cliente ABC", "SOLICITANTE"),
            ("maria.abc", "Cliente ABC", "APROVADOR"),
            ("carla.financeiro", "Financeiro", "SOLICITANTE"),
            ("roberto.financeiro", "Financeiro", "APROVADOR"),
        ]

        for username, organization_name, role in link_defs:
            UserOrganization.objects.get_or_create(
                company=company,
                user=users[username],
                organization=organizations[organization_name],
                defaults={"role": role, "active": True},
            )

    def _create_tags(self, company):
        tag_defs = [
            ("Bug", "#ef4444"),
            ("Melhoria", "#22c55e"),
            ("Backend", "#38bdf8"),
            ("Urgente", "#f97316"),
            ("Cliente", "#a855f7"),
            ("Interno", "#64748b"),
        ]

        for name, color in tag_defs:
            ActivityTag.objects.get_or_create(
                company=company,
                name=name,
                defaults={
                    "color": color,
                    "description": f"Tag demo: {name}",
                    "active": True,
                },
            )

    def _create_ticket_categories(self, company):
        category_defs = [
            {
                "name": "Suporte geral",
                "default_type": "Incidente",
                "default_priority": "Media",
                "default_impact": "Pendente",
                "default_team": "Suporte N2",
                "sla": "8h",
            },
            {
                "name": "Infraestrutura",
                "default_type": "Incidente",
                "default_priority": "Alta",
                "default_impact": "Alto",
                "default_team": "Infra",
                "sla": "4h",
            },
            {
                "name": "Melhoria interna",
                "default_type": "Solicitacao",
                "default_priority": "Media",
                "default_impact": "Medio",
                "default_team": "Projetos",
                "sla": "16h",
            },
        ]

        categories = {}
        for payload in category_defs:
            category, _ = TicketCategory.objects.get_or_create(
                company=company,
                name=payload["name"],
                defaults={
                    "description": f"Categoria demo: {payload['name']}",
                    "active": True,
                    "default_type": payload["default_type"],
                    "default_priority": payload["default_priority"],
                    "default_impact": payload["default_impact"],
                    "default_team": payload["default_team"],
                    "sla": payload["sla"],
                    "requires_client_validation": True,
                },
            )
            categories[payload["name"]] = category

        return categories

    def _create_projects(self, company, organizations, users):
        project_defs = [
            {
                "name": "Implantacao Portal Cliente ABC",
                "organization": organizations["Cliente ABC"],
                "status": "Em andamento",
                "owner": users["lucas.gestor"],
                "contact": users["maria.abc"],
                "team": [
                    (users["lucas.gestor"], "LIDER"),
                    (users["pedro.tecnico"], "SUPORTE"),
                    (users["bia.analista"], "DESENVOLVEDOR"),
                ],
            },
            {
                "name": "Automacao de relatorios internos",
                "organization": organizations["Financeiro"],
                "status": "Planejado",
                "owner": users["lucas.gestor"],
                "contact": users["roberto.financeiro"],
                "team": [
                    (users["lucas.gestor"], "LIDER"),
                    (users["bia.analista"], "ANALISTA"),
                    (users["pedro.tecnico"], "SUPORTE"),
                ],
            },
        ]

        projects = {}
        for index, payload in enumerate(project_defs, start=1):
            project, _ = Project.objects.get_or_create(
                company=company,
                client=payload["organization"],
                name=payload["name"],
                defaults={
                    "description": f"Projeto demo: {payload['name']}",
                    "status": payload["status"],
                    "owner": payload["owner"],
                    "contact_principal": payload["contact"],
                    "budget": Decimal("75000"),
                    "real_cost": Decimal("18500"),
                    "progress": 20 * index,
                    "start_at": date.today() - timedelta(days=10 * index),
                    "due_at": date.today() + timedelta(days=25 * index),
                    "tags": ["Cliente" if payload["organization"].name == "Cliente ABC" else "Interno"],
                    "checklist": [
                        {"text": "Kickoff", "done": True},
                        {"text": "Escopo aprovado", "done": index == 1},
                    ],
                },
            )
            project.team.set([user for user, _role in payload["team"]])

            for user, role in payload["team"]:
                ProjectMember.objects.get_or_create(
                    company=company,
                    project=project,
                    user=user,
                    defaults={"role": role, "active": True},
                )

            projects[payload["name"]] = project

        return projects

    def _create_sprint(self, company, projects, users):
        sprint, _ = Sprint.objects.get_or_create(
            company=company,
            name="Sprint 24",
            defaults={
                "project": projects["Implantacao Portal Cliente ABC"],
                "goal": "Concluir backlog prioritario do portal.",
                "lead": users["lucas.gestor"],
                "status": "Em andamento",
                "start_at": date.today() - timedelta(days=5),
                "end_at": date.today() + timedelta(days=9),
                "capacity": 80,
                "story_points": 34,
                "backlog": [],
                "tasks": [],
            },
        )
        return sprint

    def _create_tickets(self, company, organizations, users, projects, sprint, categories):
        ticket_defs = [
            {
                "title": "Erro 500 no endpoint /invoices",
                "organization": organizations["Cliente ABC"],
                "requester_user": users["joao.abc"],
                "contact_user": users["maria.abc"],
                "project": projects["Implantacao Portal Cliente ABC"],
                "priority": "Alta",
                "impact": "Alto",
                "urgency": "Alta",
                "status": "Em atendimento",
                "category": categories["Infraestrutura"],
                "responsible_technician": users["pedro.tecnico"],
                "tags": ["Bug", "Backend", "Cliente"],
            },
            {
                "title": "Automacao do fechamento mensal",
                "organization": organizations["Financeiro"],
                "requester_user": users["carla.financeiro"],
                "contact_user": users["roberto.financeiro"],
                "project": projects["Automacao de relatorios internos"],
                "priority": "Media",
                "impact": "Medio",
                "urgency": "Media",
                "status": "Triagem",
                "category": categories["Melhoria interna"],
                "responsible_technician": users["bia.analista"],
                "tags": ["Melhoria", "Interno"],
            },
            {
                "title": "Lentidao no portal de atendimento",
                "organization": organizations["Cliente ABC"],
                "requester_user": users["joao.abc"],
                "contact_user": users["maria.abc"],
                "project": projects["Implantacao Portal Cliente ABC"],
                "priority": "Alta",
                "impact": "Alto",
                "urgency": "Alta",
                "status": "Aguardando cliente",
                "category": categories["Suporte geral"],
                "responsible_technician": users["pedro.tecnico"],
                "tags": ["Urgente", "Cliente"],
            },
        ]

        tickets = []
        for index, payload in enumerate(ticket_defs, start=1):
            ticket, _ = Ticket.objects.get_or_create(
                company=company,
                client=payload["organization"],
                title=payload["title"],
                defaults={
                    "project": payload["project"],
                    "sprint": sprint if payload["project"] == projects["Implantacao Portal Cliente ABC"] else None,
                    "description": f"Chamado demo: {payload['title']}",
                    "requester": payload["requester_user"].full_name_or_username,
                    "requester_user": payload["requester_user"],
                    "contact_responsible": payload["contact_user"],
                    "contact_responsible_name": payload["contact_user"].full_name_or_username,
                    "contact_responsible_phone": payload["contact_user"].phone,
                    "responsible_technician": payload["responsible_technician"],
                    "category": payload["category"].name,
                    "type": payload["category"].default_type or "Solicitacao",
                    "priority": payload["priority"],
                    "impact": payload["impact"],
                    "urgency": payload["urgency"],
                    "status": payload["status"],
                    "team": payload["category"].default_team or "Suporte",
                    "sla": payload["category"].sla or "8h",
                    "opened_at": date.today() - timedelta(days=index),
                    "due_at": date.today() + timedelta(days=index),
                    "est_hours": Decimal("6"),
                    "done_hours": Decimal("2"),
                    "tags": payload["tags"],
                    "checklist": [
                        {"text": "Analisar demanda", "done": True},
                        {"text": "Executar ajuste", "done": False},
                    ],
                },
            )
            ticket.technicians.set([payload["responsible_technician"]])
            tickets.append(ticket)

        return tickets

    def _create_activities(self, company, users, sprint, tickets):
        for index, ticket in enumerate(tickets, start=1):
            Activity.objects.get_or_create(
                company=company,
                title=f"Atividade de {ticket.code}",
                defaults={
                    "description": ticket.title,
                    "type": "Tarefa",
                    "status": "Backlog" if index % 2 else "Em progresso",
                    "priority": ticket.priority,
                    "assignee": users["bia.analista"] if index % 2 else users["pedro.tecnico"],
                    "project": ticket.project,
                    "sprint": sprint if ticket.sprint_id else None,
                    "ticket": ticket,
                    "start_at": date.today(),
                    "due_at": date.today() + timedelta(days=5),
                    "est_hours": Decimal("4"),
                    "calculate_hourly_cost": True,
                    "story_points": 3,
                    "tags": ["Backend"] if index == 1 else ["Interno"],
                    "checklist": [{"text": "Executar atividade", "done": False}],
                },
            )
