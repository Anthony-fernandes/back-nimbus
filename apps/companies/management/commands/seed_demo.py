"""
Management command: seed_demo
Popula o sistema com um fluxo perfeito de dados cobrindo os últimos 6 meses:
empresa, departamentos, cargos, usuários, equipes, clientes, categorias,
tags, projetos, sprints (com planos, reviews e retrospectivas), atividades
(com tempo, comentários e resoluções) e chamados (com histórico de status,
comentários públicos/internos/técnicos, apontamentos, aprovações,
subchamados, avaliações CSAT e reaberturas).

Uso:
    python manage.py seed_demo
    python manage.py seed_demo --flush            # limpa os dados demo da empresa antes
    python manage.py seed_demo --company "Minha"  # empresa alvo (padrão: Nimbus Demo)

Login dos usuários criados: senha "nimbus123".
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.companies.models import Company
from apps.clients.models import Client
from apps.users.models import Department, Position, User
from apps.teams.models import Team, TeamMember
from apps.tickets.models import (
    Ticket, TicketApproval, TicketCategory, TicketComment,
    TicketRelation, TicketStatusHistory, TicketTimeEntry,
)
from apps.projects.models import Project, ProjectMember
from apps.activities.models import Activity, ActivityComment, ActivityTag, ActivityTimeEntry
from apps.sprints.models import (
    Sprint, SprintActivityPlan, SprintParticipant, SprintRetrospective,
    SprintReview, SprintTicketPlan,
)

PASSWORD = "nimbus123"
MONTHS = 6

FIRST_NAMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela", "Henrique", "Isabela", "João", "Karen", "Lucas"]
LAST_NAMES = ["Almeida", "Barbosa", "Cardoso", "Duarte", "Esteves", "Ferreira", "Gomes", "Lima", "Martins", "Nogueira"]

TICKET_TITLES = [
    "Sistema lento ao carregar a lista de chamados",
    "Erro 500 ao aprovar chamado de mudança",
    "Notificações de e-mail não estão sendo enviadas",
    "Relatório de SLA com dados incorretos",
    "Impressora do setor financeiro sem conexão",
    "Solicitação de acesso ao módulo de relatórios",
    "VPN desconectando a cada 30 minutos",
    "Backup noturno falhou por falta de espaço",
    "Criação de conta para novo colaborador",
    "Dashboard não atualiza os indicadores em tempo real",
    "Integração com ERP retornando timeout",
    "Troca de monitor com pixels queimados",
    "Atualização de certificado SSL do portal",
    "Migração de caixa de e-mail para novo domínio",
    "Lentidão no servidor de arquivos",
    "Permissão negada ao exportar relatório",
    "Configurar novo ponto de rede na recepção",
    "Erro de sincronização no aplicativo mobile",
    "Restauração de arquivo excluído acidentalmente",
    "Antivírus bloqueando sistema interno",
    "Ajuste de fuso horário nos agendamentos",
    "Falha ao anexar arquivos acima de 10MB",
    "Revisão de regras do firewall",
    "Instalação de software de design aprovado",
    "Página de login apresenta erro intermitente",
]

ACTIVITY_TITLES = [
    "Implementar autenticação OAuth2 com Google",
    "Refatorar módulo de notificações para WebSockets",
    "Criar tela de relatório de performance por técnico",
    "Otimizar queries N+1 na listagem de chamados",
    "Adicionar exportação CSV/PDF de relatórios",
    "Implementar cache Redis nos endpoints de listagem",
    "Cobrir fluxo de aprovação com testes de integração",
    "Criar pipeline de deploy automatizado",
    "Ajustar responsividade do portal do cliente",
    "Documentar API pública no Swagger",
    "Implementar busca full-text nos chamados",
    "Monitoramento com Prometheus e alertas",
    "Revisar acessibilidade dos formulários",
    "Migrar componentes legados para o design system",
    "Implementar modo escuro no portal",
    "Criar wizard de onboarding de novos clientes",
    "Automatizar rotina de faturamento mensal",
    "Reduzir bundle do frontend em 30%",
    "Adicionar auditoria de acessos administrativos",
    "Melhorar tratamento de erros da API",
]

COMMENT_BODIES = {
    "public": [
        "Olá! Estamos analisando a sua solicitação e retornamos em breve.",
        "Poderia confirmar se o problema persiste após a última atualização?",
        "Ajuste aplicado. Pode validar no seu ambiente, por favor?",
        "Obrigado pelo retorno! Seguimos acompanhando por aqui.",
    ],
    "internal": [
        "Cliente é prioridade do contrato Enterprise, atenção ao SLA.",
        "Aguardando janela de manutenção aprovada pela gestão.",
        "Alinhado com o time de infra, executar após às 18h.",
        "Reproduzi o cenário em staging, causa raiz identificada.",
    ],
    "technical": [
        "Stacktrace aponta para timeout na integração externa; aplicado retry com backoff.",
        "Ajustado índice composto em tickets(status, created_at); consulta caiu de 4s para 120ms.",
        "Corrigido race condition no worker de notificações; deploy na release 2.4.1.",
        "Migração executada com sucesso, checksum validado nas duas bases.",
    ],
}

RESOLUTION_NOTES = [
    "Causa raiz identificada e corrigida. Executados testes de regressão e validação com o solicitante.",
    "Configuração ajustada conforme procedimento padrão. Monitorado por 48h sem reincidência.",
    "Substituição realizada e ambiente validado em conjunto com o usuário.",
    "Correção aplicada em produção após aprovação. Documentação atualizada na base de conhecimento.",
]


def d(day: date, hour=9, minute=0):
    """date -> datetime timezone-aware dentro do horário comercial."""
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


class Command(BaseCommand):
    help = "Popula o sistema com 6 meses de dados demo completos"

    def add_arguments(self, parser):
        parser.add_argument("--company", default="Nimbus Demo")
        parser.add_argument("--flush", action="store_true", help="Remove dados anteriores da empresa demo")

    def handle(self, *args, **opts):
        random.seed(42)
        today = date.today()
        self.start = today - timedelta(days=MONTHS * 30)
        self.today = today

        company, _ = Company.objects.get_or_create(
            name=opts["company"],
            defaults={"email": "contato@nimbusdemo.com.br", "timezone": "America/Sao_Paulo"},
        )
        self.company = company

        if opts["flush"]:
            self.flush()

        self.users()
        self.org()
        self.clients()
        self.categories()
        self.tags()
        self.projects()
        self.sprints()
        self.activities()
        self.tickets()
        self.summary()

    # ── limpeza ──────────────────────────────────────────────────────
    def flush(self):
        c = self.company
        for model in (TicketTimeEntry, TicketComment, TicketApproval, TicketRelation,
                      TicketStatusHistory, SprintTicketPlan, SprintActivityPlan,
                      SprintParticipant, SprintRetrospective, SprintReview,
                      ActivityTimeEntry, ActivityComment, Activity, Ticket, Sprint,
                      ProjectMember, Project, ActivityTag, TicketCategory,
                      TeamMember, Team, Client):
            model.objects.filter(company=c).delete()
        User.objects.filter(company=c).exclude(is_superuser=True).delete()
        Department.objects.filter(company=c).delete()
        Position.objects.filter(company=c).delete()
        self.stdout.write("Dados anteriores removidos.")

    # ── pessoas e estrutura ──────────────────────────────────────────
    def users(self):
        c = self.company

        def mk(username, first, last, role, job, **extra):
            u, created = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    company=c, first_name=first, last_name=last, role=role,
                    email=f"{username}@nimbusdemo.com.br", job_title=job,
                    hourly_cost=Decimal(random.randint(60, 140)), **extra,
                ),
            )
            if created:
                u.set_password(PASSWORD)
                u.save()
            return u

        self.admin = mk("admin.demo", "Amanda", "Ribeiro", "ADMIN", "Head de Operações")
        self.managers = [
            mk("gestor.dev", "Marcos", "Tavares", "TECHNICIAN", "Coordenador de Desenvolvimento"),
            mk("gestor.suporte", "Paula", "Mendes", "TECHNICIAN", "Coordenadora de Suporte"),
        ]
        self.techs = [
            mk(f"tec.{FIRST_NAMES[i].lower()}", FIRST_NAMES[i], LAST_NAMES[i % len(LAST_NAMES)],
               "TECHNICIAN", random.choice(["Analista de Suporte", "Desenvolvedor Pleno", "Analista de Infra", "QA"]))
            for i in range(6)
        ]
        self.staff = [self.admin, *self.managers, *self.techs]

    def org(self):
        c = self.company
        dep_names = ["Tecnologia", "Suporte", "Infraestrutura"]
        self.departments = [Department.objects.get_or_create(company=c, name=n)[0] for n in dep_names]
        for n in ["Analista", "Desenvolvedor", "Coordenador", "Especialista"]:
            Position.objects.get_or_create(company=c, name=n)

        team_specs = [
            ("Equipe de Desenvolvimento", "#22c55e", self.managers[0], self.techs[:3]),
            ("Equipe de Suporte", "#818cf8", self.managers[1], self.techs[3:5]),
            ("Equipe de Infraestrutura", "#f59e0b", self.managers[0], self.techs[4:6]),
        ]
        self.teams = []
        for name, color, leader, members in team_specs:
            t, _ = Team.objects.get_or_create(
                company=c, name=name,
                defaults={"color": color, "leader": leader, "status": "Ativa", "default_capacity": 80},
            )
            for u in [leader, *members]:
                TeamMember.objects.get_or_create(company=c, team=t, user=u,
                                                 defaults={"role": "Líder" if u == leader else "Membro"})
            self.teams.append(t)

    def clients(self):
        c = self.company
        specs = [
            ("Acme Corporação", "Tecnologia", "Enterprise", 12500),
            ("Mercado Vitória", "Varejo", "Pro", 4200),
            ("Clínica Bem Estar", "Saúde", "Pro", 3800),
            ("Transportes Rápido", "Logística", "Business", 6900),
            ("Escola Horizonte", "Educação", "Starter", 1500),
            ("Construtora Alfa", "Construção", "Business", 7400),
        ]
        self.client_rows = []
        for i, (name, sector, plan, mrr) in enumerate(specs):
            row, _ = Client.objects.get_or_create(
                company=c, name=name,
                defaults=dict(sector=sector, plan=plan, mrr=mrr, health=random.choice(["Bom", "Bom", "Atenção"]),
                              email=f"contato@{name.split()[0].lower()}.com.br",
                              contact_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"),
            )
            self.client_rows.append(row)
        # usuários de portal para os 3 primeiros clientes
        self.client_users = []
        for i, row in enumerate(self.client_rows[:3]):
            u, created = User.objects.get_or_create(
                username=f"cliente.{row.name.split()[0].lower()}",
                defaults=dict(company=c, client=row, role="CLIENT",
                              first_name=row.contact_name.split()[0] if row.contact_name else "Cliente",
                              last_name=row.name.split()[0],
                              email=f"portal@{row.name.split()[0].lower()}.com.br"),
            )
            if created:
                u.set_password(PASSWORD)
                u.save()
            self.client_users.append(u)

    def categories(self):
        c = self.company
        specs = [
            ("Suporte Técnico", "8", "hours", False, "Incidente", "Media"),
            ("Infraestrutura", "12", "hours", False, "Incidente", "Alta"),
            ("Acessos e Contas", "4", "hours", False, "Requisição", "Media"),
            ("Mudanças", "24", "hours", True, "Mudança", "Alta"),
            ("Melhorias", "72", "hours", False, "Requisição", "Baixa"),
            ("Dúvidas", "8", "hours", False, "Outro", "Baixa"),
        ]
        self.category_rows = []
        for name, sla, unit, approval, tipo, prio in specs:
            row, _ = TicketCategory.objects.get_or_create(
                company=c, name=name,
                defaults=dict(sla=sla, sla_unit=unit, approval_required=approval,
                              default_type=tipo, default_priority=prio, active=True),
            )
            self.category_rows.append(row)

    def tags(self):
        c = self.company
        specs = [("frontend", "#38bdf8"), ("backend", "#22c55e"), ("infra", "#f59e0b"),
                 ("bug", "#ef4444"), ("melhoria", "#a78bfa"), ("urgente", "#fb7185")]
        self.tag_rows = [ActivityTag.objects.get_or_create(company=c, name=n, defaults={"color": col})[0]
                         for n, col in specs]

    # ── projetos ─────────────────────────────────────────────────────
    def projects(self):
        c = self.company
        specs = [
            ("Portal do Cliente 2.0", "cliente", self.client_rows[0], 85, "on_track"),
            ("Migração Cloud", "interno", None, 60, "at_risk"),
            ("App Mobile de Campo", "cliente", self.client_rows[3], 45, "on_track"),
            ("Automação de Faturamento", "interno", None, 100, "on_track"),
        ]
        self.project_rows = []
        for i, (name, tipo, client, progress, health) in enumerate(specs):
            start = self.start + timedelta(days=10 + i * 15)
            row, created = Project.objects.get_or_create(
                company=c, name=name,
                defaults=dict(tipo=tipo, client=client, owner=self.managers[i % 2],
                              status="Concluído" if progress == 100 else "Em andamento",
                              progress=progress, health=health,
                              budget=Decimal(random.randint(40, 180) * 1000),
                              real_cost=Decimal(random.randint(20, 120) * 1000),
                              start_at=start, due_at=start + timedelta(days=150),
                              description="Projeto estratégico acompanhado pelo comitê mensal.",
                              tags=["estratégico" if i < 2 else "operacional"]),
            )
            if created:
                members = random.sample(self.techs, 3)
                row.team.set(members)
                for u in members:
                    ProjectMember.objects.get_or_create(company=c, project=row, user=u)
            self.project_rows.append(row)

    # ── sprints ──────────────────────────────────────────────────────
    def sprints(self):
        c = self.company
        self.sprint_rows = []
        for t_idx, team in enumerate(self.teams):
            # +2 ciclos além do período para garantir uma sprint em andamento e uma planejada
            n_sprints = (14 if t_idx == 0 else 8)
            length = 14 if t_idx == 0 else 30
            cursor = self.start
            for i in range(n_sprints):
                start = cursor
                end = start + timedelta(days=length - 1)
                cursor = end + timedelta(days=1)
                if start > self.today + timedelta(days=length):
                    break
                if end < self.today:
                    status = "Finalizada"
                elif start <= self.today <= end:
                    status = "Em andamento"
                else:
                    status = "Planejada"
                sprint, _ = Sprint.objects.get_or_create(
                    company=c, team=team, name=f"{team.name.split()[-1]} Sprint {i + 1}",
                    defaults=dict(project=self.project_rows[t_idx % len(self.project_rows)],
                                  lead=self.managers[t_idx % 2], status=status,
                                  start_at=start, end_at=end,
                                  capacity=random.randint(60, 120),
                                  goal=f"Entregar o incremento {i + 1} com qualidade e sem débito técnico."),
                )
                self.sprint_rows.append(sprint)
                for u in random.sample(self.techs, 3):
                    SprintParticipant.objects.get_or_create(
                        company=c, sprint=sprint, user=u,
                        defaults={"team": team, "hours_per_day": 6, "working_days": 10},
                    )
                if status == "Finalizada":
                    planned = random.randint(20, 40)
                    delivered = planned - random.randint(0, 6)
                    SprintReview.objects.get_or_create(
                        company=c, sprint=sprint,
                        defaults=dict(planned_points=planned, delivered_points=delivered,
                                      planned_items=random.randint(6, 10), delivered_items=random.randint(5, 9),
                                      notes="Meta parcialmente atingida." if delivered < planned else "Meta atingida.",
                                      created_by=sprint.lead),
                    )
                    SprintRetrospective.objects.get_or_create(
                        company=c, sprint=sprint,
                        defaults=dict(went_well="Boa colaboração e entregas contínuas.",
                                      to_improve="Reduzir interrupções por chamados urgentes.",
                                      action_items=["Reservar 20% da capacidade para sustentação"],
                                      created_by=sprint.lead),
                    )

    # ── atividades ───────────────────────────────────────────────────
    def activities(self):
        c = self.company
        self.activity_rows = []
        title_pool = ACTIVITY_TITLES * 6
        idx = 0
        for sprint in self.sprint_rows:
            for _ in range(random.randint(4, 6)):
                title = f"{title_pool[idx % len(title_pool)]} ({sprint.name})"
                idx += 1
                finished = sprint.status == "Finalizada"
                running = sprint.status == "Em andamento"
                status = ("Concluída" if finished and random.random() < 0.85
                          else random.choice(["Em progresso", "Em revisao", "A fazer"]) if (finished or running)
                          else "A fazer")
                assignee = random.choice(self.techs)
                act = Activity.objects.create(
                    company=c, title=title, status=status,
                    priority=random.choice(["Alta", "Média", "Média", "Baixa"]),
                    assignee=assignee, project=sprint.project, sprint=sprint,
                    start_at=sprint.start_at, due_at=sprint.end_at,
                    est_hours=Decimal(random.choice([4, 6, 8, 12, 16])),
                    story_points=random.choice([1, 2, 3, 5, 8]),
                    tags=[random.choice(self.tag_rows).name],
                    description="Atividade planejada na sprint com critérios de aceite definidos.",
                )
                if status == "Concluída":
                    act.resolution_type = "Concluída"
                    act.resolution_notes = random.choice(RESOLUTION_NOTES)
                    act.resolved_by = assignee
                    act.resolved_at = d(sprint.end_at - timedelta(days=random.randint(0, 3)), 17)
                    act.save()
                SprintActivityPlan.objects.create(
                    company=c, sprint=sprint, activity=act, project=sprint.project,
                    responsible_ids=[str(assignee.id)], planned_hours=act.est_hours,
                    story_points=act.story_points, priority=act.priority if act.priority != "Média" else "Média",
                )
                # apontamentos + comentários
                if status in ("Concluída", "Em progresso", "Em revisao"):
                    for _ in range(random.randint(1, 3)):
                        day = sprint.start_at + timedelta(days=random.randint(0, max(1, (min(sprint.end_at, self.today) - sprint.start_at).days)))
                        ActivityTimeEntry.objects.create(
                            company=c, activity=act, sprint=sprint, project=sprint.project,
                            collaborator=assignee, collaborator_name=assignee.get_full_name(),
                            date=day, hours=Decimal(random.choice([1, 2, 3, 4])),
                            work_description="Desenvolvimento e testes da atividade.",
                        )
                    ActivityComment.objects.create(
                        company=c, activity=act, author=assignee,
                        author_name=assignee.get_full_name(),
                        body=random.choice(COMMENT_BODIES["technical"]), note_type="technical",
                    )
                # retroceder created_at para o início da sprint
                Activity.objects.filter(id=act.id).update(created_at=d(sprint.start_at, 9))
                self.activity_rows.append(act)

        # backlog sem sprint (demandas futuras)
        for i in range(12):
            act = Activity.objects.create(
                company=c, title=f"[Backlog] {ACTIVITY_TITLES[i % len(ACTIVITY_TITLES)]}",
                status="Backlog", priority=random.choice(["Alta", "Média", "Baixa"]),
                type=random.choice(["Tarefa", "Bug", "Melhoria", "Demanda interna"]),
                project=random.choice(self.project_rows),
                est_hours=Decimal(random.choice([4, 8, 16])),
                story_points=random.choice([2, 3, 5, 8]),
                tags=[random.choice(self.tag_rows).name],
            )
            Activity.objects.filter(id=act.id).update(
                created_at=d(self.start + timedelta(days=random.randint(0, MONTHS * 30)), 10))
            self.activity_rows.append(act)

    # ── chamados ─────────────────────────────────────────────────────
    def tickets(self):
        c = self.company
        self.ticket_rows = []
        total = 180
        finished_tickets = []
        for i in range(total):
            opened = self.start + timedelta(days=int(i * (MONTHS * 30) / total))
            if opened > self.today:
                break
            age_days = (self.today - opened).days
            category = random.choice(self.category_rows)
            client = random.choice(self.client_rows)
            tech = random.choice(self.techs)
            requester_user = random.choice(self.client_users) if random.random() < 0.4 else None

            # distribuição de status: quanto mais antigo, maior a chance de finalizado
            if age_days > 20:
                status = random.choices(
                    ["Finalizado", "Finalizado", "Finalizado", "Cancelado", "Em atendimento", "Validacao"],
                    weights=[55, 15, 10, 5, 10, 5])[0]
            else:
                status = random.choice(["Aberto", "Triagem", "Em atendimento", "Aguardando cliente",
                                        "Em atendimento", "Validacao", "Finalizado", "Pausado"])
            needs_approval = category.approval_required
            ticket = Ticket.objects.create(
                company=c, client=client, title=random.choice(TICKET_TITLES),
                description="Descrição detalhada do cenário reportado, com passos para reproduzir e impacto no negócio.",
                requester=requester_user.get_full_name() if requester_user else f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                requester_user=requester_user,
                responsible_technician=tech if status not in ("Aberto", "Triagem") else None,
                category=category.name, type=category.default_type or "Incidente",
                priority=category.default_priority or "Media",
                impact=random.choice(["Alto", "Médio", "Médio", "Baixo"]),
                urgency=random.choice(["Alta", "Média", "Média", "Baixa"]),
                status=status, source=random.choice(["portal", "email", "chat", "telefone"]),
                opened_at=opened, sla=f"{category.sla}h" if category.sla else "8h",
                sla_due_at=d(opened + timedelta(days=1), 18),
                est_hours=Decimal(random.choice([2, 4, 8])),
                tags=[random.choice(["produção", "recorrente", "vip", "hardware", "acesso"])],
                approval_status="Aprovado" if needs_approval else "Nao requerido",
                approval_route="APPROVER" if needs_approval else "NONE",
            )
            if status not in ("Aberto", "Triagem"):
                ticket.technicians.add(tech)

            # histórico de status realista
            chain = {
                "Aberto": ["Aberto"],
                "Triagem": ["Aberto", "Triagem"],
                "Em atendimento": ["Aberto", "Triagem", "Em atendimento"],
                "Aguardando cliente": ["Aberto", "Triagem", "Em atendimento", "Aguardando cliente"],
                "Pausado": ["Aberto", "Triagem", "Em atendimento", "Pausado"],
                "Validacao": ["Aberto", "Triagem", "Em atendimento", "Validacao"],
                "Finalizado": ["Aberto", "Triagem", "Em atendimento", "Validacao", "Finalizado"],
                "Cancelado": ["Aberto", "Triagem", "Cancelado"],
            }[status]
            prev = ""
            for step_idx, st in enumerate(chain):
                TicketStatusHistory.objects.create(
                    company=c, ticket=ticket, changed_by=tech,
                    changed_by_name=tech.get_full_name(), status_from=prev, status_to=st,
                    reason="Fluxo padrão de atendimento" if st not in ("Pausado", "Cancelado") else "Solicitação da gestão",
                )
                prev = st

            # comentários com as 3 visibilidades
            author = tech
            for note_type in random.sample(["public", "internal", "technical"], k=random.randint(1, 3)):
                TicketComment.objects.create(
                    company=c, ticket=ticket, author=author,
                    author_name=author.get_full_name(),
                    body=random.choice(COMMENT_BODIES[note_type]), note_type=note_type,
                )

            # apontamentos de tempo para chamados que entraram em atendimento
            if status in ("Em atendimento", "Aguardando cliente", "Validacao", "Finalizado", "Pausado"):
                done = Decimal(0)
                for _ in range(random.randint(1, 4)):
                    hours = Decimal(random.choice([1, 2, 3]))
                    done += hours
                    TicketTimeEntry.objects.create(
                        company=c, ticket=ticket, collaborator=tech,
                        collaborator_name=tech.get_full_name(),
                        date=min(opened + timedelta(days=random.randint(0, max(age_days, 1))), self.today),
                        hours=hours, work_description="Atendimento, diagnóstico e execução da solução.",
                    )
                ticket.done_hours = done

            # aprovação para categoria de mudanças
            if needs_approval:
                TicketApproval.objects.create(
                    company=c, ticket=ticket, approver=self.admin,
                    approver_name=self.admin.get_full_name(), decision="APROVADO",
                    comment="Mudança aprovada dentro da janela padrão.",
                    decided_at=d(opened, 15),
                )
                ticket.approved_by = self.admin
                ticket.approved_at = d(opened, 15)

            # resolução, CSAT e reabertura para finalizados
            if status == "Finalizado":
                closed_day = min(opened + timedelta(days=random.randint(1, 10)), self.today)
                ticket.resolution_type = random.choice(["Resolvido", "Solução de contorno", "Configuração"])
                ticket.resolution_notes = random.choice(RESOLUTION_NOTES)
                ticket.resolved_by = tech
                ticket.resolved_at = d(closed_day, 16)
                ticket.finished_at = d(closed_day, 16)
                TicketComment.objects.create(
                    company=c, ticket=ticket, author=tech, author_name=tech.get_full_name(),
                    body=ticket.resolution_notes, note_type="resolution",
                )
                if random.random() < 0.7:
                    ticket.rating = random.choices([5, 4, 3, 2], weights=[45, 35, 15, 5])[0]
                    ticket.rating_comment = "Atendimento rápido e claro." if ticket.rating >= 4 else "Poderia ter sido mais ágil."
                    ticket.rated_at = d(closed_day, 18)
                finished_tickets.append(ticket)
            ticket.save()
            Ticket.objects.filter(id=ticket.id).update(created_at=d(opened, random.randint(8, 17)))
            self.ticket_rows.append(ticket)

        # reaberturas (5 chamados finalizados voltam para atendimento)
        for ticket in random.sample(finished_tickets, min(5, len(finished_tickets))):
            ticket.reopen_count = 1
            ticket.last_reopened_at = timezone.now()
            ticket.status = "Em atendimento"
            ticket.resolution_type = ""
            ticket.save()
            TicketStatusHistory.objects.create(
                company=c, ticket=ticket, changed_by=self.admin,
                changed_by_name=self.admin.get_full_name(),
                status_from="Finalizado", status_to="Em atendimento",
                reason="Reaberto: problema voltou a ocorrer após a correção.",
            )

        # subchamados bloqueantes
        parents = random.sample(self.ticket_rows, 6)
        for parent in parents:
            child = Ticket.objects.create(
                company=c, client=parent.client, title=f"[Sub] {parent.title}",
                description=f"Subchamado derivado de {parent.code}.",
                requester=parent.requester, responsible_technician=parent.responsible_technician,
                category=parent.category, type=parent.type, priority=parent.priority,
                status=random.choice(["Em atendimento", "Finalizado"]),
                opened_at=parent.opened_at, source="portal",
            )
            TicketRelation.objects.create(
                company=c, ticket=parent, related_ticket=child,
                relation_type="subchamado", blocks_parent=random.random() < 0.7,
            )

        # chamados enviados para sprints ativas/finalizadas (plano de sprint)
        eligible = [t for t in self.ticket_rows if t.status in ("Backlog", "Triagem", "Em atendimento")]
        for sprint in [s for s in self.sprint_rows if s.status in ("Em andamento", "Finalizada")][:6]:
            for ticket in random.sample(eligible, min(2, len(eligible))):
                SprintTicketPlan.objects.get_or_create(
                    company=c, sprint=sprint, ticket=ticket,
                    defaults=dict(responsible_ids=[str((ticket.responsible_technician or self.techs[0]).id)],
                                  planned_hours=ticket.est_hours or 4, story_points=random.choice([2, 3, 5])),
                )

    # ── resumo ───────────────────────────────────────────────────────
    def summary(self):
        c = self.company
        self.stdout.write(self.style.SUCCESS(
            "\nSeed de 6 meses concluído para a empresa "
            f"'{c.name}':\n"
            f"  Usuários:    {User.objects.filter(company=c).count()} (senha: {PASSWORD})\n"
            f"  Equipes:     {Team.objects.filter(company=c).count()} / membros {TeamMember.objects.filter(company=c).count()}\n"
            f"  Clientes:    {Client.objects.filter(company=c).count()}\n"
            f"  Projetos:    {Project.objects.filter(company=c).count()}\n"
            f"  Sprints:     {Sprint.objects.filter(company=c).count()} "
            f"(reviews {SprintReview.objects.filter(company=c).count()}, retros {SprintRetrospective.objects.filter(company=c).count()})\n"
            f"  Atividades:  {Activity.objects.filter(company=c).count()} "
            f"(tempo {ActivityTimeEntry.objects.filter(company=c).count()}, comentários {ActivityComment.objects.filter(company=c).count()})\n"
            f"  Chamados:    {Ticket.objects.filter(company=c).count()} "
            f"(histórico {TicketStatusHistory.objects.filter(company=c).count()}, comentários {TicketComment.objects.filter(company=c).count()}, "
            f"tempo {TicketTimeEntry.objects.filter(company=c).count()}, aprovações {TicketApproval.objects.filter(company=c).count()}, "
            f"relações {TicketRelation.objects.filter(company=c).count()})\n"
            "\nLogin sugerido: admin.demo / nimbus123"
        ))
