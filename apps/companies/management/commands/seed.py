"""
Management command: seed
Populates the database with realistic demo data for NimbusDesk.
Usage:
    python manage.py seed
    python manage.py seed --flush   # clear existing data first
"""
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.companies.models import Company
from apps.clients.models import Client
from apps.users.models import User
from apps.teams.models import Team, TeamMember
from apps.tickets.models import Ticket, TicketCategory, TicketComment
from apps.projects.models import Project, ProjectMember
from apps.activities.models import Activity, ActivityComment, ActivityTimeEntry
from apps.sprints.models import Sprint, SprintParticipant, SprintActivityPlan, SprintTicketPlan, SprintReview


def rand_past(days_min=1, days_max=60):
    return date.today() - timedelta(days=random.randint(days_min, days_max))


def rand_future(days_min=1, days_max=60):
    return date.today() + timedelta(days=random.randint(days_min, days_max))


ALL_PERMS = {
    "sprints.view": True, "users.view": True,
    "tickets.viewAll": True, "tickets.create": True,
    "tickets.viewAssigned": True, "tickets.viewTeam": True,
    "projects.view": True, "activities.view": True,
    "reports.view": True, "categories.view": True,
    "settings.view": True, "clients.view": True,
    "teams.view": True, "teams.manage": True,
}

LOREM = [
    "Implementar autenticação OAuth2 com Google e Microsoft",
    "Corrigir bug no cálculo de SLA para chamados de alta prioridade",
    "Migrar base de dados para PostgreSQL 15",
    "Criar tela de relatório de performance por técnico",
    "Refatorar módulo de notificações para usar WebSockets",
    "Adicionar suporte a múltiplos idiomas no portal do cliente",
    "Implementar exportação de chamados para CSV e PDF",
    "Revisar e atualizar documentação da API REST",
    "Criar pipeline CI/CD no GitHub Actions",
    "Otimizar queries N+1 no endpoint de listagem de chamados",
    "Implementar busca full-text com Elasticsearch",
    "Criar dashboard de monitoramento em tempo real",
    "Configurar alertas de SLA por e-mail e Slack",
    "Integrar com sistema ERP via webhooks",
    "Desenvolver aplicativo mobile para técnicos de campo",
    "Implementar autenticação de dois fatores (2FA)",
    "Criar módulo de gestão de contratos de suporte",
    "Configurar backup automático do banco de dados",
    "Implementar sistema de tags para categorização de chamados",
    "Criar relatório de satisfação do cliente (CSAT)",
]

DESCRIPTIONS = [
    "Analisar os requisitos técnicos e implementar a solução seguindo as melhores práticas.",
    "Identificar a causa raiz do problema e aplicar a correção adequada com testes de regressão.",
    "Documentar todas as etapas do processo e validar com o time antes de ir para produção.",
    "Seguir o padrão de código estabelecido no projeto e garantir cobertura de testes mínima de 80%.",
    "Coordenar com o time de infraestrutura para garantir disponibilidade durante a manutenção.",
]

TICKET_TITLES = [
    "Sistema lento ao carregar a lista de chamados",
    "Erro 500 ao tentar aprovar chamado de mudança",
    "Botão de salvar não funciona no Firefox",
    "Notificações de e-mail não estão sendo enviadas",
    "Relatório de SLA mostrando dados incorretos",
    "Usuário não consegue fazer login após redefinição de senha",
    "Dashboard não carrega no celular",
    "Exportação de PDF gerando arquivo corrompido",
    "Chamado não está sendo atribuído automaticamente",
    "Integração com ERP parou de sincronizar",
    "Timeout ao carregar lista de usuários com mais de 1000 registros",
    "Campos customizados não aparecem no formulário de novo chamado",
    "Erro ao fazer upload de anexo maior que 10MB",
    "Categorias de chamado duplicadas após migração",
    "Widget do dashboard mostrando total errado",
    "Usuário removido ainda consegue acessar o sistema",
    "Aprovação enviada para o fluxo errado",
    "SLA não está pausando quando chamado vai para Aguardando cliente",
    "Pesquisa não retorna resultados com acentuação",
    "Histórico de status não está sendo registrado",
    "Prioridade calculada incorretamente pelo sistema",
    "Webhook não está disparando ao fechar chamado",
    "Portal do cliente mostrando chamados de outras organizações",
    "Permissões de equipe não estão sendo respeitadas",
    "Campo de data aceita datas inválidas",
]

TICKET_COMMENTS = [
    "Reproduzido em ambiente de homologação. Trabalhando na correção.",
    "Problema identificado: índice faltando na tabela de chamados. Adicionando migration.",
    "Correção aplicada. Aguardando validação do usuário.",
    "Confirmado com o cliente que o problema foi resolvido.",
    "Escalado para o time de infraestrutura. Aguardando resposta.",
    "Necessito de acesso ao log do servidor para investigar melhor.",
    "Fix aplicado na branch de correção. Aguardando aprovação do PR.",
    "Workaround temporário: limpar o cache do navegador.",
    "Atualizado para alta prioridade pois está afetando múltiplos usuários.",
]


class Command(BaseCommand):
    help = "Seeds the database with realistic demo data"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Clear all data before seeding")

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Limpando dados existentes...")
            SprintTicketPlan.objects.all().delete()
            SprintActivityPlan.objects.all().delete()
            SprintParticipant.objects.all().delete()
            Sprint.objects.all().delete()
            ActivityTimeEntry.objects.all().delete()
            ActivityComment.objects.all().delete()
            Activity.objects.all().delete()
            ProjectMember.objects.all().delete()
            Project.objects.all().delete()
            TicketComment.objects.all().delete()
            Ticket.objects.all().delete()
            TicketCategory.objects.all().delete()
            TeamMember.objects.all().delete()
            Team.objects.all().delete()
            User.objects.all().delete()
            Client.objects.all().delete()
            Company.objects.all().delete()

        # ── Company ────────────────────────────────────────────────────────────
        self.stdout.write("Criando empresa...")
        company, _ = Company.objects.get_or_create(
            name="NimbusDesk Demo",
            defaults={"email": "contato@nimbusdesk.com", "is_active": True},
        )

        # ── Users ──────────────────────────────────────────────────────────────
        self.stdout.write("Criando usuários...")

        def make_user(username, first, last, email, role="TECNICO", perms=None, **kw):
            defaults = dict(
                first_name=first, last_name=last, email=email,
                company=company, role=role, is_active=True,
                granted_permissions=perms if perms is not None else ALL_PERMS,
            )
            defaults.update(kw)
            u, _ = User.objects.get_or_create(username=username, defaults=defaults)
            if _:
                u.set_password("nimbus123")
                u.save(update_fields=["password"])
            return u

        admin = make_user("admin", "Admin", "NimbusDesk", "admin@nimbusdesk.com",
                          role="ADMIN", perms={}, is_staff=True, is_superuser=True)

        users = [
            make_user("ana.silva", "Ana", "Silva", "ana.silva@nimbusdesk.com", job_title="Desenvolvedora Sênior"),
            make_user("carlos.santos", "Carlos", "Santos", "carlos.santos@nimbusdesk.com", job_title="Tech Lead"),
            make_user("mariana.lima", "Mariana", "Lima", "mariana.lima@nimbusdesk.com", job_title="Desenvolvedora Plena"),
            make_user("pedro.costa", "Pedro", "Costa", "pedro.costa@nimbusdesk.com", job_title="DevOps Engineer"),
            make_user("julia.ferreira", "Júlia", "Ferreira", "julia.ferreira@nimbusdesk.com", job_title="QA Engineer"),
            make_user("rafael.souza", "Rafael", "Souza", "rafael.souza@nimbusdesk.com", job_title="Desenvolvedor Júnior"),
            make_user("camila.oliveira", "Camila", "Oliveira", "camila.oliveira@nimbusdesk.com", job_title="Product Manager"),
            make_user("lucas.martins", "Lucas", "Martins", "lucas.martins@nimbusdesk.com", job_title="Scrum Master"),
            make_user("fernanda.rocha", "Fernanda", "Rocha", "fernanda.rocha@nimbusdesk.com", job_title="UX Designer"),
            make_user("gabriel.alves", "Gabriel", "Alves", "gabriel.alves@nimbusdesk.com", job_title="Analista de Suporte"),
            make_user("beatriz.nunes", "Beatriz", "Nunes", "beatriz.nunes@nimbusdesk.com", job_title="Analista de Suporte"),
            make_user("thiago.mendes", "Thiago", "Mendes", "thiago.mendes@nimbusdesk.com", job_title="Desenvolvedor Sênior"),
        ]

        # ── Clients ────────────────────────────────────────────────────────────
        self.stdout.write("Criando clientes...")
        client_data = [
            ("Acme Tecnologia S.A.", "contato@acme.com.br"),
            ("Grupo Vantagem Ltda.", "ti@grupovantagem.com"),
            ("StartUp Inovação", "suporte@startup-inov.com"),
            ("Banco Central Digital", "infra@bcd.gov.br"),
            ("Logística Express", "tech@logexpress.com.br"),
        ]
        clients = []
        for name, email in client_data:
            cl, _ = Client.objects.get_or_create(
                company=company, name=name,
                defaults={"email": email, "status": "Ativo"},
            )
            clients.append(cl)

        client_perms = {"tickets.viewOwn": True, "tickets.create": True}
        client_users = []
        for i, cl in enumerate(clients):
            slug = cl.name.lower().replace(" ", "").replace(".", "")[:8]
            cu = make_user(f"cliente{i+1}", f"Usuário{i+1}", "Portal",
                           f"portal{i+1}@{slug}.com", role="CLIENT", perms=client_perms)
            cu.client = cl
            cu.save(update_fields=["client"])
            client_users.append(cu)

        # ── Teams ──────────────────────────────────────────────────────────────
        self.stdout.write("Criando equipes...")
        team_defs = [
            ("Backend", "Desenvolvimento de APIs e serviços", "#6366f1", "Code2", users[0], users[:4]),
            ("Frontend", "Interfaces web e mobile", "#8b5cf6", "Layout", users[2], [users[2], users[5], users[8]]),
            ("DevOps & Infra", "Infraestrutura, CI/CD e monitoramento", "#0ea5e9", "Server", users[3], [users[3], users[4]]),
            ("QA & Testes", "Qualidade e automação de testes", "#22c55e", "ShieldCheck", users[4], [users[4], users[5]]),
            ("Suporte N1", "Atendimento inicial e triagem de chamados", "#f97316", "Bell", users[9], [users[9], users[10]]),
            ("Produto", "Product management e UX", "#ec4899", "Sparkles", users[6], [users[6], users[7], users[8]]),
        ]
        teams = []
        for name, desc, color, icon, leader, members in team_defs:
            t, _ = Team.objects.get_or_create(
                company=company, name=name,
                defaults={"description": desc, "color": color, "icon": icon,
                          "leader": leader, "status": "Ativa", "default_capacity": 80},
            )
            for m in members:
                TeamMember.objects.get_or_create(company=company, team=t, user=m,
                                                  defaults={"role": "Membro", "default_capacity": 80})
            teams.append(t)

        # ── Ticket Categories ──────────────────────────────────────────────────
        self.stdout.write("Criando categorias de chamado...")
        categories = []
        for name, color in [
            ("Infraestrutura", "#ef4444"), ("Bug / Erro", "#f97316"),
            ("Acesso e Permissões", "#eab308"), ("Melhoria", "#22c55e"),
            ("Dúvida", "#0ea5e9"), ("Integração", "#6366f1"),
            ("Performance", "#8b5cf6"), ("Segurança", "#ec4899"),
        ]:
            cat, _ = TicketCategory.objects.get_or_create(
                company=company, name=name,
                defaults={"color": color, "description": f"Chamados relacionados a {name.lower()}"},
            )
            categories.append(cat)

        # ── Tickets ────────────────────────────────────────────────────────────
        self.stdout.write("Criando chamados...")
        statuses = ["Aberto", "Em andamento", "Aguardando", "Resolvido", "Fechado"]
        priorities = ["Critica", "Alta", "Media", "Baixa"]
        types = ["Incidente", "Requisição", "Problema", "Mudança"]

        tickets = []
        for i, title in enumerate(TICKET_TITLES):
            assignee = users[i % len(users)]
            requester = client_users[i % len(client_users)]
            cat = categories[i % len(categories)]
            priority = priorities[i % len(priorities)]
            t = Ticket.objects.create(
                company=company,
                title=title,
                description=random.choice(DESCRIPTIONS),
                type=types[i % len(types)],
                priority=priority,
                status=statuses[i % len(statuses)],
                category=cat,
                responsible_technician=assignee, requester=requester,
                client=clients[i % len(clients)],
                impact="Alto" if priority in ("Critica", "Alta") else "Médio",
                urgency="Alta" if priority == "Critica" else "Média",
            )
            tickets.append(t)
            for _ in range(random.randint(1, 3)):
                TicketComment.objects.create(
                    company=company, ticket=t, author=assignee,
                    body=random.choice(TICKET_COMMENTS),
                )

        # ── Projects ───────────────────────────────────────────────────────────
        self.stdout.write("Criando projetos...")
        proj_defs = [
            ("Portal do Cliente v2", "Redesign completo do portal com nova identidade visual.", "Em andamento", "on_track", users[6], rand_past(60), rand_future(30)),
            ("Migração para Cloud", "Migração da infraestrutura on-premise para AWS.", "Em andamento", "at_risk", users[3], rand_past(45), rand_future(45)),
            ("API Gateway Unificada", "Consolidação de todas as APIs internas em um único gateway.", "Planejado", "on_track", users[0], rand_future(7, 60), rand_future(61, 120)),
            ("Sistema de BI Interno", "Dashboard de business intelligence integrado.", "Concluído", "on_track", users[6], rand_past(80, 90), rand_past(5, 10)),
            ("App Mobile Técnicos", "Aplicativo iOS/Android para técnicos de campo.", "Em andamento", "delayed", users[2], rand_past(30), rand_future(60)),
        ]
        projects = []
        for pi, (name, desc, status, health, manager, start, end) in enumerate(proj_defs):
            p, _ = Project.objects.get_or_create(
                company=company, name=name,
                defaults={"description": desc, "status": status, "health": health,
                          "start_at": start, "due_at": end, "client": clients[pi % len(clients)]},

            )
            ProjectMember.objects.get_or_create(company=company, project=p, user=manager,
                                                  defaults={"role": "GERENTE", "active": True})
            for u in random.sample(users, 4):
                ProjectMember.objects.get_or_create(company=company, project=p, user=u,
                                                     defaults={"role": "DESENVOLVEDOR", "active": True})
            projects.append(p)

        # ── Activities ─────────────────────────────────────────────────────────
        self.stdout.write("Criando atividades...")
        act_statuses = ["Backlog", "A fazer", "Em andamento", "Em revisão", "Concluída"]
        activities = []
        for i, title in enumerate(LOREM):
            assignee = users[i % len(users)]
            status = act_statuses[i % len(act_statuses)]
            a = Activity.objects.create(
                company=company, title=title,
                description=random.choice(DESCRIPTIONS),
                type="Tarefa", status=status,
                priority=random.choice(["Alta", "Media", "Baixa"]),
                assignee=assignee,
                project=projects[i % len(projects)],
                start_at=rand_past(30), due_at=rand_future(15),
                est_hours=random.choice([2, 4, 8, 13, 21]),
                story_points=random.choice([1, 2, 3, 5, 8, 13]),
            )
            activities.append(a)
            ActivityComment.objects.create(
                company=company, activity=a, author=assignee,
                body=random.choice(DESCRIPTIONS),
            )

        # ── Sprints ────────────────────────────────────────────────────────────
        self.stdout.write("Criando sprints...")
        sprint_defs = [
            ("Sprint 1 — Fundação", rand_past(60), rand_past(46), "Concluída", "Estabelecer base do projeto e configurar ambientes."),
            ("Sprint 2 — Autenticação", rand_past(45), rand_past(31), "Concluída", "Implementar login, 2FA e gestão de sessões."),
            ("Sprint 3 — Core Features", rand_past(30), rand_past(16), "Concluída", "Desenvolver funcionalidades principais do produto."),
            ("Sprint 4 — Integrações", rand_past(15), rand_past(1), "Concluída", "Integrar com sistemas externos e ERP."),
            ("Sprint 5 — Performance", rand_past(1), rand_future(13), "Em andamento", "Otimizar performance e resolver gargalos identificados."),
            ("Sprint 6 — QA & Polimento", rand_future(14), rand_future(28), "Planejada", "Fase de qualidade, testes e refinamentos de UX."),
            ("Sprint 7 — Beta Release", rand_future(29, 30), rand_future(40, 50), "Planejada", "Preparação e lançamento da versão beta."),
        ]
        sprints = []
        for name, start, end, status, goal in sprint_defs:
            s, _ = Sprint.objects.get_or_create(
                company=company, name=name,
                defaults={"start_at": start, "end_at": end, "status": status, "goal": goal},
            )
            sprints.append(s)
            sprint_users = random.sample(users, min(5, len(users)))
            for u in sprint_users:
                hours_exec = round(random.uniform(10, 40), 1) if status == "Concluída" else round(random.uniform(0, 20), 1)
                SprintParticipant.objects.get_or_create(
                    company=company, sprint=s, user=u,
                    defaults={"hours_per_day": 8, "working_days": 10,
                              "availability_factor": 0.8,
                              "hours_planned": 64,
                              "hours_executed": hours_exec,
                              "inclusion_mode": "manual"},
                )
            sprint_acts = random.sample(activities, min(4, len(activities)))
            sprint_pts_planned = 0
            sprint_pts_delivered = 0
            for act in sprint_acts:
                # for concluded sprints, force most activities to "Concluída"
                if status == "Concluída" and random.random() < 0.75:
                    act.status = "Concluída"
                    act.save(update_fields=["status"])
                elif status == "Em andamento" and random.random() < 0.4:
                    act.status = "Em andamento"
                    act.save(update_fields=["status"])

                # add time entry linked to this sprint
                if act.status in ("Em andamento", "Concluída"):
                    ActivityTimeEntry.objects.create(
                        company=company, activity=act, collaborator=act.assignee,
                        sprint=s,
                        hours=round(random.uniform(1, float(act.est_hours or 4)), 1),
                        date=rand_past(1, 20), work_description="Apontamento de horas",
                    )
                sp = random.choice([1, 2, 3, 5, 8])
                SprintActivityPlan.objects.get_or_create(
                    company=company, sprint=s, activity=act,
                    defaults={"priority": random.choice(["Alta", "Media", "Baixa"]),
                              "complexity": random.choice([1, 2, 3, 5]),
                              "story_points": sp,
                              "planned_hours": random.choice([4, 8, 13, 21]),
                              "user_hours": {}},
                )
                sprint_pts_planned += sp
                # link activity to sprint via FK so burndown works
                act.sprint = s
                act.save(update_fields=["sprint"])
                if act.status in ("Concluída", "Concluido", "Done"):
                    sprint_pts_delivered += sp
            for tk in random.sample(tickets, min(3, len(tickets))):
                SprintTicketPlan.objects.get_or_create(
                    company=company, sprint=s, ticket=tk,
                    defaults={"priority": random.choice(["Alta", "Media", "Baixa"]),
                              "complexity": random.choice([1, 2, 3, 5]),
                              "story_points": random.choice([1, 2, 3, 5]),
                              "planned_hours": random.choice([2, 4, 8]),
                              "user_hours": {}},
                )
            # create SprintReview for concluded sprints so Review and Velocity tabs work
            if status == "Concluída":
                delivered_count = sum(1 for a in sprint_acts if a.status in ("Concluída", "Concluido", "Done"))
                SprintReview.objects.get_or_create(
                    sprint=s, company=company,
                    defaults={
                        "planned_points": sprint_pts_planned,
                        "delivered_points": sprint_pts_delivered,
                        "planned_items": len(sprint_acts),
                        "delivered_items": delivered_count,
                        "incomplete_activity_ids": [],
                        "notes": "",
                    },
                )

        self.stdout.write(self.style.SUCCESS("\n✓ Seed concluído! Resumo:"))
        self.stdout.write(f"  Empresa:      1  →  '{company.name}'")
        self.stdout.write(f"  Usuários:     {User.objects.filter(company=company).count()} internos + {len(client_users)} clientes")
        self.stdout.write(f"  Clientes:     {Client.objects.filter(company=company).count()}")
        self.stdout.write(f"  Equipes:      {Team.objects.filter(company=company).count()}")
        self.stdout.write(f"  Chamados:     {Ticket.objects.filter(company=company).count()}")
        self.stdout.write(f"  Projetos:     {Project.objects.filter(company=company).count()}")
        self.stdout.write(f"  Atividades:   {Activity.objects.filter(company=company).count()}")
        self.stdout.write(f"  Sprints:      {Sprint.objects.filter(company=company).count()}")
        self.stdout.write(f"\n  Login admin:    admin / nimbus123")
        self.stdout.write(f"  Login técnico:  ana.silva / nimbus123")
        self.stdout.write(f"  Login cliente:  cliente1 / nimbus123")
