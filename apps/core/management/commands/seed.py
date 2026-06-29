"""
Management command: seed
Populates the database with realistic demo data for NimbusDesk.
Usage:
    python manage.py seed
    python manage.py seed --flush   # clear existing data first
"""
import random
from datetime import date, timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.companies.models import Company
from apps.clients.models import Client
from apps.users.models import User
from apps.teams.models import Team, TeamMember
from apps.tickets.models import Ticket, TicketCategory, TicketComment
from apps.projects.models import Project, ProjectMember
from apps.activities.models import Activity, ActivityComment, ActivityTimeEntry
from apps.sprints.models import Sprint, SprintParticipant, SprintActivityPlan, SprintTicketPlan


def rand_date(days_ago_max=90, days_future_max=0):
    offset = random.randint(-days_ago_max, days_future_max)
    return date.today() + timedelta(days=offset)


def rand_past(days_ago_min=1, days_ago_max=60):
    offset = random.randint(days_ago_min, days_ago_max)
    return date.today() - timedelta(days=offset)


def rand_future(days_min=1, days_max=60):
    offset = random.randint(days_min, days_max)
    return date.today() + timedelta(days=offset)


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
    "Configurar rate limiting na API pública",
    "Implementar funcionalidade de clone de chamados",
    "Criar painel de KPIs para gestores",
    "Adicionar campo de SLA customizável por categoria",
    "Implementar sistema de escalação automática",
    "Criar integração com Microsoft Teams",
    "Desenvolver chatbot para triagem inicial de chamados",
    "Implementar assinatura digital em aprovações",
    "Criar módulo de base de conhecimento com IA",
    "Configurar ambiente de staging com dados anonimizados",
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
    "SLA não está pausando quando chamado vai para 'Aguardando cliente'",
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
    "Fix aplicado na branch feature/fix-ticket-timeout. Aguardando aprovação do PR.",
    "Workaround temporário: limpar o cache do navegador.",
    "Atualizado para alta prioridade pois está afetando múltiplos usuários.",
    "Documentação de referência: https://docs.interno/troubleshooting",
]


class Command(BaseCommand):
    help = "Seeds the database with realistic demo data"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Clear all data before seeding")

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Limpando dados existentes…")
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

        self.stdout.write("Criando empresa…")
        company, _ = Company.objects.get_or_create(
            name="NimbusDesk Demo",
            defaults={"slug": "nimbusdesk-demo", "plan": "enterprise"},
        )

        # ── Users ──────────────────────────────────────────────────────────────
        self.stdout.write("Criando usuários…")
        hashed = make_password("nimbus123")

        def make_user(username, first, last, email, role="TECNICO", **kw):
            u, _ = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    first_name=first,
                    last_name=last,
                    email=email,
                    password=hashed,
                    company=company,
                    role=role,
                    is_active=True,
                    granted_permissions={"sprints.view": True, "users.view": True,
                                         "tickets.viewAll": True, "tickets.create": True,
                                         "tickets.viewAssigned": True,
                                         "projects.view": True, "activities.view": True,
                                         "reports.view": True, "categories.view": True,
                                         "settings.view": True},
                    **kw,
                ),
            )
            return u

        admin = make_user("admin", "Admin", "NimbusDesk", "admin@nimbusdesk.com", role="ADMIN",
                          is_staff=True, is_superuser=True,
                          granted_permissions={})
        admin.set_password("nimbus123")
        admin.save()

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
        self.stdout.write("Criando clientes…")
        client_data = [
            ("Acme Tecnologia S.A.", "contato@acme.com.br", "São Paulo"),
            ("Grupo Vantagem Ltda.", "ti@grupovantagem.com", "Rio de Janeiro"),
            ("StartUp Inovação", "suporte@startup-inov.com", "Belo Horizonte"),
            ("Banco Central Digital", "infra@bcd.gov.br", "Brasília"),
            ("Logística Express", "tech@logexpress.com.br", "Curitiba"),
        ]
        clients = []
        for name, email, city in client_data:
            cl, _ = Client.objects.get_or_create(
                company=company, name=name,
                defaults={"contact_email": email, "city": city, "status": "Ativo"},
            )
            clients.append(cl)

        # Client users (portal)
        client_users = []
        for i, cl in enumerate(clients):
            cu = make_user(
                f"cliente{i+1}", f"Usuário{i+1}", "Portal", f"portal{i+1}@{cl.name.lower().replace(' ', '')[:8]}.com",
                role="CLIENT", granted_permissions={"tickets.viewOwn": True, "tickets.create": True},
            )
            cu.client = cl
            cu.save()
            client_users.append(cu)

        # ── Teams ──────────────────────────────────────────────────────────────
        self.stdout.write("Criando equipes…")
        team_defs = [
            ("Backend", "Desenvolvimento de APIs e serviços", "#6366f1", "Code2", users[0], users[:4]),
            ("Frontend", "Interfaces web e mobile", "#8b5cf6", "Layout", users[2], [users[2], users[5], users[8]]),
            ("DevOps & Infra", "Infraestrutura, CI/CD e monitoramento", "#0ea5e9", "Server", users[3], [users[3], users[4]]),
            ("QA & Testes", "Qualidade e automação de testes", "#22c55e", "ShieldCheck", users[4], [users[4], users[5]]),
            ("Suporte N1", "Atendimento inicial e triagem de chamados", "#f97316", "HeadphonesIcon", users[9], [users[9], users[10]]),
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
        self.stdout.write("Criando categorias de chamado…")
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
        self.stdout.write("Criando chamados…")
        statuses = ["Aberto", "Em andamento", "Aguardando", "Resolvido", "Fechado"]
        priorities = ["Critica", "Alta", "Media", "Baixa"]
        types = ["Incidente", "Requisição", "Problema", "Mudança"]

        tickets = []
        for i, title in enumerate(TICKET_TITLES):
            status = statuses[i % len(statuses)]
            priority = priorities[i % len(priorities)]
            assignee = users[i % len(users)]
            requester = client_users[i % len(client_users)]
            cat = categories[i % len(categories)]
            created = rand_past(1, 45)
            t = Ticket.objects.create(
                company=company,
                title=title,
                description=random.choice(DESCRIPTIONS),
                type=types[i % len(types)],
                priority=priority,
                status=status,
                category=cat,
                assignee=assignee,
                requester=requester,
                client=clients[i % len(clients)],
                impact="Alto" if priority in ("Critica", "Alta") else "Médio",
                urgency="Alta" if priority == "Critica" else "Média",
            )
            tickets.append(t)
            # comments
            for j in range(random.randint(1, 3)):
                TicketComment.objects.create(
                    company=company, ticket=t,
                    author=assignee,
                    content=random.choice(TICKET_COMMENTS),
                )

        # ── Projects ───────────────────────────────────────────────────────────
        self.stdout.write("Criando projetos…")
        proj_defs = [
            ("Portal do Cliente v2", "Redesign completo do portal com nova identidade visual e funcionalidades de autoatendimento.", "Em andamento", "on_track", users[6], rand_past(60), rand_future(30)),
            ("Migração para Cloud", "Migração da infraestrutura on-premise para AWS com zero downtime.", "Em andamento", "at_risk", users[3], rand_past(45), rand_future(45)),
            ("API Gateway Unificada", "Consolidação de todas as APIs internas em um único gateway com autenticação centralizada.", "Planejado", "on_track", users[0], rand_future(7), rand_future(90)),
            ("Sistema de BI Interno", "Dashboard de business intelligence integrado com todas as fontes de dados da empresa.", "Concluído", "on_track", users[6], rand_past(90), rand_past(10)),
            ("App Mobile Técnicos", "Aplicativo iOS/Android para técnicos de campo registrarem apontamentos.", "Em andamento", "delayed", users[2], rand_past(30), rand_future(60)),
        ]
        projects = []
        for name, desc, status, health, manager, start, end in proj_defs:
            p, _ = Project.objects.get_or_create(
                company=company, name=name,
                defaults={"description": desc, "status": status, "health": health,
                          "manager": manager, "start_at": start, "end_at": end},
            )
            # members
            ProjectMember.objects.get_or_create(company=company, project=p, user=manager,
                                                  defaults={"role": "GERENTE"})
            for u in random.sample(users, 4):
                ProjectMember.objects.get_or_create(company=company, project=p, user=u,
                                                     defaults={"role": "DESENVOLVEDOR"})
            projects.append(p)

        # ── Activities ─────────────────────────────────────────────────────────
        self.stdout.write("Criando atividades…")
        act_statuses = ["Backlog", "A fazer", "Em andamento", "Em revisão", "Concluída"]
        act_priorities = ["Alta", "Média", "Baixa"]
        activities = []
        for i, title in enumerate(LOREM[:20]):
            project = projects[i % len(projects)]
            assignee = users[i % len(users)]
            status = act_statuses[i % len(act_statuses)]
            a = Activity.objects.create(
                company=company,
                title=title,
                description=random.choice(DESCRIPTIONS),
                type="Tarefa",
                status=status,
                priority=random.choice(act_priorities),
                assignee=assignee,
                project=project,
                start_at=rand_past(30),
                due_at=rand_future(15),
                est_hours=random.choice([2, 4, 8, 13, 21]),
                story_points=random.choice([1, 2, 3, 5, 8, 13]),
            )
            activities.append(a)
            if status in ("Em andamento", "Concluída"):
                ActivityTimeEntry.objects.create(
                    company=company, activity=a, user=assignee,
                    hours=random.uniform(1, a.est_hours),
                    date=rand_past(1, 20),
                    description="Apontamento de horas",
                )
            ActivityComment.objects.create(
                company=company, activity=a, author=assignee,
                content=random.choice(DESCRIPTIONS),
            )

        # ── Sprints ────────────────────────────────────────────────────────────
        self.stdout.write("Criando sprints…")
        sprint_defs = [
            ("Sprint 1 — Fundação", rand_past(60), rand_past(46), "Concluída", "Estabelecer base do projeto e configurar ambientes."),
            ("Sprint 2 — Autenticação", rand_past(45), rand_past(31), "Concluída", "Implementar login, 2FA e gestão de sessões."),
            ("Sprint 3 — Core Features", rand_past(30), rand_past(16), "Concluída", "Desenvolver funcionalidades principais do produto."),
            ("Sprint 4 — Integrações", rand_past(15), rand_past(1), "Concluída", "Integrar com sistemas externos e ERP."),
            ("Sprint 5 — Performance", rand_past(0), rand_future(14), "Em andamento", "Otimizar performance e resolver gargalos identificados."),
            ("Sprint 6 — QA & Polimento", rand_future(15), rand_future(29), "Planejada", "Fase de qualidade, testes e refinamentos de UX."),
            ("Sprint 7 — Beta Release", rand_future(30), rand_future(44), "Planejada", "Preparação e lançamento da versão beta para clientes selecionados."),
        ]
        sprints = []
        for name, start, end, status, goal in sprint_defs:
            s, _ = Sprint.objects.get_or_create(
                company=company, name=name,
                defaults={"start_at": start, "end_at": end, "status": status,
                          "goal": goal, "observations": ""},
            )
            sprints.append(s)
            # participants
            sprint_users = random.sample(users, min(5, len(users)))
            for u in sprint_users:
                SprintParticipant.objects.get_or_create(
                    company=company, sprint=s, user=u,
                    defaults={"hours_per_day": 8, "working_days": 10,
                              "availability_factor": 0.8, "capacity": 64,
                              "inclusion_mode": "manual"},
                )
            # plan activities
            sprint_acts = random.sample(activities, min(4, len(activities)))
            for act in sprint_acts:
                SprintActivityPlan.objects.get_or_create(
                    company=company, sprint=s, activity=act,
                    defaults={"priority": random.choice(["Alta", "Média", "Baixa"]),
                              "complexity": random.choice(["Simples", "Média", "Complexa"]),
                              "story_points": random.choice([1, 2, 3, 5, 8]),
                              "estimated_hours": random.choice([4, 8, 13, 21]),
                              "user_hours": {}},
                )
            # plan tickets
            sprint_tickets = random.sample(tickets, min(3, len(tickets)))
            for tk in sprint_tickets:
                SprintTicketPlan.objects.get_or_create(
                    company=company, sprint=s, ticket=tk,
                    defaults={"priority": random.choice(["Alta", "Média", "Baixa"]),
                              "complexity": random.choice(["Simples", "Média", "Complexa"]),
                              "story_points": random.choice([1, 2, 3, 5]),
                              "estimated_hours": random.choice([2, 4, 8]),
                              "user_hours": {}},
                )

        self.stdout.write(self.style.SUCCESS("\n✓ Seed concluído! Resumo:"))
        self.stdout.write(f"  Empresa:      1")
        self.stdout.write(f"  Usuários:     {User.objects.filter(company=company).count()} internos + {len(client_users)} clientes")
        self.stdout.write(f"  Clientes:     {Client.objects.filter(company=company).count()}")
        self.stdout.write(f"  Equipes:      {Team.objects.filter(company=company).count()}")
        self.stdout.write(f"  Chamados:     {Ticket.objects.filter(company=company).count()}")
        self.stdout.write(f"  Projetos:     {Project.objects.filter(company=company).count()}")
        self.stdout.write(f"  Atividades:   {Activity.objects.filter(company=company).count()}")
        self.stdout.write(f"  Sprints:      {Sprint.objects.filter(company=company).count()}")
        self.stdout.write(f"\n  Login admin:  admin / nimbus123")
        self.stdout.write(f"  Login técnico: ana.silva / nimbus123")
        self.stdout.write(f"  Login cliente: cliente1 / nimbus123")
