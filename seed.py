#!/usr/bin/env python
"""
Seed script — 6 meses de dados realistas cobrindo o fluxo completo.

Uso:
    python manage.py shell < seed.py
  ou (com env vars):
    DEBUG=True SECRET_KEY=xxx python manage.py shell < seed.py

Cobre:
  - Empresa Nimbus Tech + superadmin anthony.dn05@gmail.com
  - 1 admin + 6 técnicos + 4 clientes + 8 usuários CLIENT
  - 6 meses de tickets (~200) em todos os status/tipos/prioridades ITIL
  - Comentários, histórico de status, avaliações CSAT, reaberturas
  - 3 projetos com 6 sprints cada (concluídas, ativa, planejada)
  - ~120 atividades distribuídas por sprints
  - Sprint reviews + retrospectivas para cada sprint concluída
  - Time entries diários de trabalho
  - Relatórios com variação semanal de volume
"""

import os, sys, django, random
from datetime import date, timedelta
from decimal import Decimal

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    django.setup()

from django.utils import timezone
from django.db import transaction

from apps.companies.models import Company
from apps.users.models import User, Department, Position
from apps.clients.models import Client
from apps.teams.models import Team, TeamMember
from apps.tickets.models import (
    Ticket, TicketComment, TicketCategory, TicketStatusHistory, SLAPolicy,
)
from apps.projects.models import Project, ProjectMember
from apps.activities.models import Activity, ActivityComment, ActivityTimeEntry
from apps.sprints.models import (
    Sprint, SprintParticipant, SprintActivityPlan, SprintTicketPlan,
    SprintRetrospective, SprintReview,
)

random.seed(42)
now = timezone.now()
today = date.today()

# ─── helper: data relativa ────────────────────────────────────────────────────
def days_ago(n): return today - timedelta(days=n)
def ago(n):      return now - timedelta(days=n)

print("═" * 65)
print("  SEED — 6 meses de dados  ·  Nimbus Tech")
print("═" * 65)


# ══════════════════════════════════════════════════════════════
# 1. EMPRESA
# ══════════════════════════════════════════════════════════════
print("\n[1/14] Empresa …")
company, _ = Company.objects.get_or_create(
    name="Nimbus Tech",
    defaults={
        "document": "12.345.678/0001-99",
        "email": "contato@nimbustech.com.br",
        "phone": "(11) 4002-8922",
        "is_active": True,
        "usage_type": "hibrido",
        "email_domain": "nimbustech.com.br",
        "timezone": "America/Sao_Paulo",
        "locale": "pt-BR",
        "currency": "BRL",
    },
)
print(f"   ✓ {company.name}")


# ══════════════════════════════════════════════════════════════
# 2. SUPERADMIN GLOBAL
# ══════════════════════════════════════════════════════════════
print("\n[2/14] Superadmin global …")
superadmin, created = User.objects.get_or_create(
    email="anthony.dn05@gmail.com",
    defaults={
        "username": "anthony.dn05@gmail.com",
        "first_name": "Anthony",
        "last_name": "Fernandes",
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
        "role": "ADMIN",
        "job_title": "CTO",
    },
)
if created:
    superadmin.set_password("Admin@1234")
    superadmin.save()
    print("   ✓ anthony.dn05@gmail.com criado  (senha: Admin@1234)")
else:
    superadmin.is_staff = True
    superadmin.is_superuser = True
    superadmin.save(update_fields=["is_staff", "is_superuser"])
    print("   ✓ anthony.dn05@gmail.com já existia (permissões garantidas)")


# ══════════════════════════════════════════════════════════════
# 3. DEPARTAMENTOS E CARGOS
# ══════════════════════════════════════════════════════════════
print("\n[3/14] Departamentos e Cargos …")
dept_specs = [
    ("TI & Infraestrutura", "Manutenção de sistemas e rede"),
    ("Suporte ao Cliente", "Helpdesk N1/N2 e atendimento"),
    ("Engenharia de Software", "Desenvolvimento e QA"),
    ("Gestão de Projetos", "PMO e coordenação de entregas"),
]
depts = {}
for name, desc in dept_specs:
    d, _ = Department.objects.get_or_create(company=company, name=name, defaults={"description": desc})
    depts[name] = d

pos_specs = [
    ("Analista de Suporte N1", False),
    ("Analista de Suporte N2", False),
    ("Desenvolvedor Pleno", False),
    ("Desenvolvedor Sênior", False),
    ("Gestor de TI", True),
    ("Gerente de Projetos", True),
]
positions = {}
for name, auto in pos_specs:
    p, _ = Position.objects.get_or_create(company=company, name=name, defaults={"auto_approval": auto})
    positions[name] = p
print(f"   ✓ {len(depts)} departamentos · {len(positions)} cargos")


# ══════════════════════════════════════════════════════════════
# 4. USUÁRIOS INTERNOS
# ══════════════════════════════════════════════════════════════
print("\n[4/14] Usuários internos …")

def make_user(username, email, first, last, role, dept=None, pos=None, job="", hourly=0, total_hours=40):
    u = User.objects.filter(email=email).first() or User.objects.filter(username=username).first()
    if not u:
        u = User(
            username=username, email=email,
            first_name=first, last_name=last,
            role=role, company=company,
            department=dept, position=pos,
            job_title=job,
            hourly_cost=Decimal(str(hourly)),
            total_hours=total_hours,
            is_active=True,
        )
        u.set_password("Admin@1234")
        u.save()
    return u

admin = make_user("admin@nimbus.tech", "admin@nimbus.tech",
                  "Mariana", "Costa", "ADMIN",
                  dept=depts["Gestão de Projetos"], pos=positions["Gestor de TI"],
                  job="Gestora de TI", hourly=130, total_hours=40)

tec1 = make_user("carlos.oliveira", "carlos.oliveira@nimbus.tech",
                 "Carlos", "Oliveira", "TECHNICIAN",
                 dept=depts["Suporte ao Cliente"], pos=positions["Analista de Suporte N1"],
                 job="Analista de Suporte N1", hourly=75)
tec2 = make_user("julia.santos", "julia.santos@nimbus.tech",
                 "Júlia", "Santos", "TECHNICIAN",
                 dept=depts["Suporte ao Cliente"], pos=positions["Analista de Suporte N2"],
                 job="Analista de Suporte N2", hourly=90)
tec3 = make_user("rafael.lima", "rafael.lima@nimbus.tech",
                 "Rafael", "Lima", "TECHNICIAN",
                 dept=depts["Engenharia de Software"], pos=positions["Desenvolvedor Sênior"],
                 job="Desenvolvedor Backend Sênior", hourly=120)
tec4 = make_user("beatriz.mendes", "beatriz.mendes@nimbus.tech",
                 "Beatriz", "Mendes", "TECHNICIAN",
                 dept=depts["Engenharia de Software"], pos=positions["Desenvolvedor Pleno"],
                 job="Desenvolvedora Frontend", hourly=105)
tec5 = make_user("gabriel.ferreira", "gabriel.ferreira@nimbus.tech",
                 "Gabriel", "Ferreira", "TECHNICIAN",
                 dept=depts["TI & Infraestrutura"], pos=positions["Analista de Suporte N2"],
                 job="Analista de Infraestrutura", hourly=95)
tec6 = make_user("larissa.rocha", "larissa.rocha@nimbus.tech",
                 "Larissa", "Rocha", "TECHNICIAN",
                 dept=depts["Engenharia de Software"], pos=positions["Desenvolvedor Pleno"],
                 job="Desenvolvedora Fullstack", hourly=108)

technicians = [tec1, tec2, tec3, tec4, tec5, tec6]
print(f"   ✓ admin + {len(technicians)} técnicos")


# ══════════════════════════════════════════════════════════════
# 5. CLIENTES
# ══════════════════════════════════════════════════════════════
print("\n[5/14] Clientes …")
client_specs = [
    ("Varejo Rápido S.A.",       "ti@varejora.com.br",             "João Mendonça",    "Varejo",          "Enterprise", Decimal("18000")),
    ("Construtora Horizonte",    "suporte@horizonteconstrucoes.com","Fernanda Rocha",   "Construção Civil","Pro",        Decimal("9500")),
    ("HealthPlus Planos",        "ti@healthplus.com.br",            "Marco Aurélio",    "Saúde",           "Enterprise", Decimal("14000")),
    ("EduTech Soluções",         "suporte@edutech.com.br",          "Camila Andrade",   "Educação",        "Pro",        Decimal("6000")),
]
clients = []
for name, email, contact, sector, plan, mrr in client_specs:
    c, _ = Client.objects.get_or_create(
        company=company, name=name,
        defaults={"email": email, "contact_name": contact, "sector": sector,
                  "plan": plan, "mrr": mrr, "status": "Ativo", "health": "Bom"},
    )
    clients.append(c)
print(f"   ✓ {len(clients)} clientes")

client_user_specs = [
    ("joao.mendonca",   "joao@varejora.com.br",              "João",    "Mendonça", clients[0]),
    ("ana.varejo",      "ana@varejora.com.br",               "Ana",     "Souza",    clients[0]),
    ("pedro.varejo",    "pedro@varejora.com.br",             "Pedro",   "Alves",    clients[0]),
    ("fernanda.rocha",  "fernanda@horizonteconstrucoes.com", "Fernanda","Rocha",    clients[1]),
    ("marco.aurelio",   "marco@healthplus.com.br",           "Marco",   "Aurélio",  clients[2]),
    ("lucas.health",    "lucas@healthplus.com.br",           "Lucas",   "Ferreira", clients[2]),
    ("camila.edu",      "camila@edutech.com.br",             "Camila",  "Andrade",  clients[3]),
    ("rodrigo.edu",     "rodrigo@edutech.com.br",            "Rodrigo", "Nunes",    clients[3]),
]
client_users = []
for username, email, first, last, client_obj in client_user_specs:
    u = User.objects.filter(email=email).first() or User.objects.filter(username=username).first()
    if not u:
        u = User(username=username, email=email, first_name=first, last_name=last,
                 role="CLIENT", company=company, client=client_obj, is_active=True)
        u.set_password("Admin@1234")
        u.save()
    client_users.append(u)
print(f"   ✓ {len(client_users)} usuários CLIENT")


# ══════════════════════════════════════════════════════════════
# 6. EQUIPES
# ══════════════════════════════════════════════════════════════
print("\n[6/14] Equipes …")
team_sup, _ = Team.objects.get_or_create(
    company=company, name="Equipe de Suporte",
    defaults={"leader": tec2, "color": "#6366f1", "tipo": "suporte", "default_capacity": Decimal("80")},
)
team_dev, _ = Team.objects.get_or_create(
    company=company, name="Equipe de Desenvolvimento",
    defaults={"leader": tec3, "color": "#22c55e", "tipo": "equipe", "default_capacity": Decimal("160")},
)
team_infra, _ = Team.objects.get_or_create(
    company=company, name="Equipe de Infraestrutura",
    defaults={"leader": tec5, "color": "#f59e0b", "tipo": "equipe", "default_capacity": Decimal("80")},
)
team_members_map = [
    (tec1, team_sup), (tec2, team_sup),
    (tec3, team_dev), (tec4, team_dev), (tec6, team_dev),
    (tec5, team_infra),
]
for user, team in team_members_map:
    TeamMember.objects.get_or_create(
        company=company, team=team, user=user,
        defaults={"default_hours_per_day": Decimal("8"), "default_capacity": Decimal("40")},
    )
print("   ✓ 3 equipes + membros")


# ══════════════════════════════════════════════════════════════
# 7. CATEGORIAS DE TICKET
# ══════════════════════════════════════════════════════════════
print("\n[7/14] Categorias + SLA …")
cat_specs = [
    ("Suporte Geral",          "8h",  "Incidente",  "Media",  False),
    ("Infraestrutura",         "4h",  "Incidente",  "Alta",   True),
    ("Desenvolvimento",        "24h", "Requisição", "Baixa",  True),
    ("Acesso e Permissões",    "2h",  "Requisição", "Alta",   False),
    ("Problema Crítico",       "1h",  "Problema",   "Critica",True),
    ("Mudança de Sistema",     "48h", "Mudança",    "Media",  True),
    ("Banco de Dados",         "2h",  "Problema",   "Alta",   False),
    ("Segurança e Compliance", "1h",  "Incidente",  "Critica",True),
]
categories = {}
for name, sla, def_type, def_prio, approval in cat_specs:
    c, _ = TicketCategory.objects.get_or_create(
        company=company, name=name,
        defaults={"sla": sla, "default_type": def_type,
                  "default_priority": def_prio, "approval_required": approval},
    )
    categories[name] = c

sla_pol_specs = [
    ("SLA Critica – 1h",        "Critica", "Suporte Geral",  "1h",  10),
    ("SLA Alta – 4h",           "Alta",    "Suporte Geral",  "4h",  8),
    ("SLA Media – 8h",          "Media",   "Suporte Geral",  "8h",  5),
    ("SLA Baixa – 24h",         "Baixa",   "Suporte Geral",  "24h", 2),
    ("SLA Infra Critica – 2h",  "Critica", "Infraestrutura", "2h",  10),
    ("SLA Segurança – 1h",      "Critica", "Segurança e Compliance", "1h", 10),
]
for name, priority, cat_name, rt, weight in sla_pol_specs:
    SLAPolicy.objects.get_or_create(
        company=company, name=name,
        defaults={"priority": priority, "category": cat_name,
                  "response_time": rt, "priority_weight": weight, "active": True},
    )
print(f"   ✓ {len(categories)} categorias · {len(sla_pol_specs)} políticas SLA")


# ══════════════════════════════════════════════════════════════
# 8. TICKETS – 6 MESES DE HISTÓRICO
# ══════════════════════════════════════════════════════════════
print("\n[8/14] Tickets – 6 meses …")

TICKET_TEMPLATES = [
    # (title_template, category, type, impact, urgency, client_idx, client_user_idx, tech_idx)
    # ── Incidentes frequentes
    ("Sistema ERP lento – semana {w}",         "Suporte Geral",          "Incidente",  "Alto",  "Alta",   0, [0,1,2], [0,1]),
    ("Erro ao emitir nota fiscal – lote {w}",  "Suporte Geral",          "Incidente",  "Alto",  "Alta",   0, [0,1],   [0,1]),
    ("App mobile não abre – v{w}",             "Suporte Geral",          "Incidente",  "Alto",  "Alta",   0, [2],     [0,1]),
    ("E-mails de pedido não chegam #{w}",      "Suporte Geral",          "Incidente",  "Médio", "Média",  0, [1],     [1,0]),
    ("Dashboard em branco após deploy {w}",    "Suporte Geral",          "Incidente",  "Alto",  "Alta",   0, [0],     [3,5]),
    ("VPN não conecta – escritório {w}",       "Infraestrutura",         "Incidente",  "Alto",  "Alta",   1, [3],     [4,2]),
    ("Servidor web retorna 503 – {w}",         "Problema Crítico",       "Problema",   "Alto",  "Alta",   1, [3],     [4,2]),
    ("Certificado SSL expirado #{w}",          "Infraestrutura",         "Incidente",  "Alto",  "Alta",   1, [3],     [4]),
    ("Backup automático falhou – {w}",         "Infraestrutura",         "Problema",   "Médio", "Média",  2, [4],     [4,2]),
    ("Banco de dados lento – semana {w}",      "Banco de Dados",         "Problema",   "Alto",  "Alta",   2, [4,5],   [2,4]),
    ("Storage quase cheio – {w}",             "Infraestrutura",         "Problema",   "Médio", "Alta",   2, [4],     [4]),
    ("Autenticação 2FA falha – {w}",           "Segurança e Compliance", "Incidente",  "Alto",  "Alta",   2, [5],     [1,2]),
    ("Crash na tela de relatórios – {w}",      "Suporte Geral",          "Incidente",  "Médio", "Média",  3, [6],     [0,1]),
    ("Erro de sincronização de dados – {w}",   "Banco de Dados",         "Problema",   "Alto",  "Alta",   3, [7],     [2,4]),
    ("Alerta Grafana parado – {w}",            "Infraestrutura",         "Problema",   "Médio", "Alta",   2, [4],     [4,2]),
    # ── Requisições
    ("Criar usuário para {w}",                 "Acesso e Permissões",    "Requisição", "Baixo", "Baixa",  0, [0,1,2], [1,0]),
    ("Resetar senha bloqueada – {w}",          "Acesso e Permissões",    "Requisição", "Baixo", "Baixa",  0, [1],     [0,1]),
    ("Aumento de limite de upload – {w}",      "Acesso e Permissões",    "Requisição", "Baixo", "Baixa",  1, [3],     [1]),
    ("Novo relatório gerencial – {w}",         "Desenvolvimento",        "Requisição", "Médio", "Baixa",  1, [3],     [3,5]),
    ("Ajuste no formulário de cadastro – {w}", "Desenvolvimento",        "Requisição", "Baixo", "Baixa",  3, [6,7],   [3,5]),
    ("Integração com API externa – {w}",       "Desenvolvimento",        "Requisição", "Médio", "Média",  0, [0],     [2,3]),
    ("Campo novo no cadastro – {w}",           "Desenvolvimento",        "Requisição", "Baixo", "Baixa",  3, [6],     [5,3]),
    # ── Mudanças
    ("Atualização de servidor – janela {w}",   "Mudança de Sistema",     "Mudança",    "Alto",  "Média",  2, [4],     [4,2]),
    ("Migração de dados – fase {w}",           "Mudança de Sistema",     "Mudança",    "Alto",  "Média",  1, [3],     [2,3]),
    ("Upgrade Node.js – {w}",                 "Mudança de Sistema",     "Mudança",    "Médio", "Média",  0, [0],     [3,2]),
    ("Deploy em produção – release {w}",       "Mudança de Sistema",     "Mudança",    "Alto",  "Média",  0, [0],     [3,2]),
    # ── Problemas
    ("Investigação lentidão recorrente – {w}", "Problema Crítico",       "Problema",   "Alto",  "Alta",   0, [0],     [2,4]),
    ("RCA – queda de sistema – {w}",           "Problema Crítico",       "Problema",   "Alto",  "Alta",   1, [3],     [4,2]),
    ("Vazamento de memória – {w}",             "Banco de Dados",         "Problema",   "Alto",  "Alta",   2, [4],     [2,4]),
    ("Falha intermitente no login – {w}",      "Segurança e Compliance", "Problema",   "Alto",  "Alta",   3, [6,7],   [1,2]),
]

# Status para tickets antigos (terminados) vs recentes
STATUS_FINISHED = [
    ("Finalizado", 0.65),
    ("Cancelado",  0.10),
    ("Finalizado", 0.25),  # pesado para finalizado
]
STATUS_RECENT = [
    ("Aberto",               0.15),
    ("Triagem",              0.10),
    ("Aguardando atendimento",0.10),
    ("Em atendimento",        0.35),
    ("Aguardando cliente",    0.10),
    ("Validacao",             0.10),
    ("Pausado",               0.05),
    ("Aguardando Aprovacao",  0.05),
]

COMMENTS_POOL = [
    ("tech", "Iniciando investigação. Reproduzindo em ambiente de homologação."),
    ("tech", "Identificado o problema. Aplicando correção."),
    ("tech", "Correção aplicada e testada. Aguardando validação do cliente."),
    ("tech", "Deploy realizado com sucesso. Monitorando por 24h."),
    ("tech", "Confirmado em produção. Chamado pode ser fechado."),
    ("tech", "Preciso de acesso ao servidor para continuar a análise."),
    ("tech", "Logs indicam timeout na consulta ao banco. Otimizando query."),
    ("tech", "Índice adicionado. Performance melhorou 80%. Aguardando cliente."),
    ("tech", "Rollback realizado. Analisando causa raiz."),
    ("tech", "Atualizando certificado SSL. Previsão: 30min."),
    ("client", "Precisamos resolver com urgência, está impactando as vendas."),
    ("client", "Problema persiste. Vocês já identificaram a causa?"),
    ("client", "Confirmado! O problema foi resolvido. Obrigado pela agilidade."),
    ("client", "Problema voltou a ocorrer hoje às 14h."),
    ("client", "Ok, aguardamos. Por favor nos avisem quando concluir."),
    ("client", "Nosso time validou e está funcionando corretamente agora."),
]

STATUS_FLOW = [
    ("Aberto", "Triagem"),
    ("Triagem", "Em atendimento"),
    ("Em atendimento", "Validacao"),
    ("Validacao", "Finalizado"),
]

created_tickets = []
ticket_count = 0

# Gerar tickets semana a semana pelos últimos 26 semanas (~6 meses)
for week_offset in range(26, 0, -1):  # 26 semanas atrás até hoje
    week_start_offset = week_offset * 7
    # Quantos tickets nessa semana (varia realisticamente: 6–14/semana)
    week_volume = random.randint(6, 14)
    templates_this_week = random.sample(TICKET_TEMPLATES, min(week_volume, len(TICKET_TEMPLATES)))

    for tmpl in templates_this_week:
        title_tmpl, cat_name, ttype, impact, urgency, client_idx, client_user_idxs, tech_idxs = tmpl

        week_label = f"W{26 - week_offset + 1}"
        title = title_tmpl.format(w=week_label)

        # Escolher requester e técnico aleatoriamente dentro dos permitidos
        cui = random.choice(client_user_idxs)
        ti  = random.choice(tech_idxs)
        req_user = client_users[cui] if cui < len(client_users) else client_users[0]
        tech = technicians[ti] if ti < len(technicians) else technicians[0]
        client = clients[client_idx] if client_idx < len(clients) else clients[0]

        # Ticket mais antigo → tende a estar finalizado
        is_old = week_offset > 4
        if is_old:
            status_pool = [("Finalizado", 7), ("Cancelado", 1), ("Finalizado", 2)]
            status = random.choices(["Finalizado", "Cancelado"], weights=[9, 1])[0]
            finished = (status == "Finalizado")
        else:
            statuses = ["Aberto", "Triagem", "Aguardando atendimento", "Em atendimento",
                        "Aguardando cliente", "Validacao", "Pausado", "Aguardando Aprovacao",
                        "Finalizado", "Finalizado"]
            status = random.choice(statuses)
            finished = (status == "Finalizado")

        # Datas
        open_offset = week_start_offset + random.randint(0, 6)
        opened_date = days_ago(open_offset)
        finished_at = None
        if finished:
            resolve_days = random.randint(1, 5)
            finished_at = ago(open_offset - resolve_days) if open_offset > resolve_days else ago(1)

        sla_hours = {"Critica": 1, "Alta": 4, "Media": 8, "Baixa": 24}.get(
            {"Alto": "Critica", "Médio": "Media", "Baixo": "Baixa"}.get(impact, "Media"), 8
        )
        sla_due = timezone.make_aware(
            __import__("datetime").datetime.combine(opened_date, __import__("datetime").time(9, 0))
        ) + __import__("datetime").timedelta(hours=sla_hours)

        # Rating apenas em finalizados (60% têm avaliação)
        rating = None
        rated_at = None
        if finished and random.random() < 0.60:
            # Distribuição realista: maioria 4-5
            rating = random.choices([1, 2, 3, 4, 5], weights=[3, 5, 12, 35, 45])[0]
            rated_at = finished_at

        reopen_count = 0
        last_reopened_at = None
        if finished and random.random() < 0.08:  # 8% reabertos
            reopen_count = random.randint(1, 3)
            last_reopened_at = ago(open_offset - 1)

        # Evitar duplicata por title+company
        if Ticket.objects.filter(company=company, title=title).exists():
            title = title + f" [{random.randint(100,999)}]"

        t = Ticket(
            company=company,
            title=title,
            description=f"Descrição detalhada: {title}. Impacto reportado pelo cliente {client.name}.",
            client=client,
            requester_user=req_user,
            requester=f"{req_user.first_name} {req_user.last_name}",
            responsible_technician=tech,
            category=cat_name,
            type=ttype,
            impact=impact,
            urgency=urgency,
            status=status,
            opened_at=opened_date,
            sla_due_at=sla_due,
            finished_at=finished_at,
            est_hours=Decimal(str(random.choice([2, 4, 6, 8, 12]))),
            done_hours=Decimal(str(random.choice([1, 2, 4, 6]))) if finished else Decimal("0"),
            sla=f"{sla_hours}h",
            rating=rating,
            rated_at=rated_at,
            reopen_count=reopen_count,
            last_reopened_at=last_reopened_at,
        )
        t.save()
        t.technicians.add(tech)
        created_tickets.append(t)
        ticket_count += 1

print(f"   ✓ {ticket_count} tickets criados (26 semanas)")


# ── Comentários ──────────────────────────────────────────────
print("   → Comentários …")
comment_count = 0
for ticket in created_tickets:
    num_comments = random.choices([0, 1, 2, 3, 4], weights=[10, 25, 30, 25, 10])[0]
    used_comments = random.sample(COMMENTS_POOL, min(num_comments, len(COMMENTS_POOL)))
    for kind, body in used_comments:
        if kind == "tech":
            author = ticket.responsible_technician
            is_internal = random.random() < 0.7
        else:
            author = ticket.requester_user
            is_internal = False
        if author:
            TicketComment.objects.get_or_create(
                company=company, ticket=ticket, author=author, body=body,
                defaults={"is_internal": is_internal},
            )
            comment_count += 1

print(f"   ✓ {comment_count} comentários")


# ── Histórico de status ──────────────────────────────────────
print("   → Histórico de status …")
hist_count = 0
for ticket in created_tickets:
    if ticket.status == "Finalizado":
        prev = "Aberto"
        for from_s, to_s in STATUS_FLOW:
            TicketStatusHistory.objects.get_or_create(
                company=company, ticket=ticket, status_from=from_s, status_to=to_s,
                defaults={"changed_by": ticket.responsible_technician,
                          "reason": "Progressão normal do atendimento."},
            )
            hist_count += 1
    elif ticket.status in ("Em atendimento", "Validacao", "Aguardando cliente"):
        TicketStatusHistory.objects.get_or_create(
            company=company, ticket=ticket, status_from="Aberto", status_to="Em atendimento",
            defaults={"changed_by": ticket.responsible_technician, "reason": "Técnico assumiu o chamado."},
        )
        hist_count += 1

print(f"   ✓ {hist_count} registros de histórico")


# ══════════════════════════════════════════════════════════════
# 9. PROJETOS
# ══════════════════════════════════════════════════════════════
print("\n[9/14] Projetos …")
proj1, _ = Project.objects.get_or_create(
    company=company, name="Portal do Cliente v3",
    defaults={
        "client": clients[0],
        "department": depts["Engenharia de Software"],
        "tipo": "cliente", "metodologia": "scrum",
        "description": "Redesign completo do portal com nova UX/UI e APIs REST.",
        "status": "Em andamento", "owner": admin,
        "budget": Decimal("220000"), "real_cost": Decimal("95000"),
        "progress": 48,
        "start_at": days_ago(180), "due_at": days_ago(-90),
        "health": "on_track", "tags": ["portal", "react", "api"],
    },
)
proj2, _ = Project.objects.get_or_create(
    company=company, name="Infraestrutura Cloud AWS",
    defaults={
        "department": depts["TI & Infraestrutura"],
        "tipo": "interno", "metodologia": "kanban",
        "description": "Migração de toda infraestrutura on-premise para AWS multi-AZ.",
        "status": "Em andamento", "owner": tec5,
        "budget": Decimal("120000"), "real_cost": Decimal("58000"),
        "progress": 55,
        "start_at": days_ago(150), "due_at": days_ago(-60),
        "health": "at_risk", "tags": ["aws", "terraform", "devops"],
    },
)
proj3, _ = Project.objects.get_or_create(
    company=company, name="Sistema de BI e Relatórios",
    defaults={
        "client": clients[1],
        "department": depts["Engenharia de Software"],
        "tipo": "cliente", "metodologia": "scrum",
        "description": "Plataforma de Business Intelligence com dashboards interativos.",
        "status": "Planejado", "owner": admin,
        "budget": Decimal("85000"), "real_cost": Decimal("0"),
        "progress": 0,
        "start_at": days_ago(-7), "due_at": days_ago(-180),
        "health": "on_track", "tags": ["bi", "metabase", "etl"],
    },
)
projects = [proj1, proj2, proj3]

for user, role in [(tec3,"DESENVOLVEDOR"),(tec4,"DESENVOLVEDOR"),(tec6,"DESENVOLVEDOR"),(tec1,"QA"),(admin,"GERENTE")]:
    ProjectMember.objects.get_or_create(company=company, project=proj1, user=user, defaults={"role":role,"active":True})
for user, role in [(tec5,"GERENTE"),(tec2,"ANALISTA"),(tec3,"DESENVOLVEDOR")]:
    ProjectMember.objects.get_or_create(company=company, project=proj2, user=user, defaults={"role":role,"active":True})
for user, role in [(tec3,"ARQUITETO"),(tec6,"DESENVOLVEDOR"),(tec4,"DESENVOLVEDOR"),(admin,"GERENTE")]:
    ProjectMember.objects.get_or_create(company=company, project=proj3, user=user, defaults={"role":role,"active":True})
print("   ✓ 3 projetos + membros")


# ══════════════════════════════════════════════════════════════
# 10. SPRINTS – 6 por projeto
# ══════════════════════════════════════════════════════════════
print("\n[10/14] Sprints …")

SPRINT_GOALS = [
    "Estruturar arquitetura base e pipeline CI/CD.",
    "Implementar autenticação, autorização e perfil de usuário.",
    "Módulo principal: CRUD, listagens e filtros.",
    "Integrações externas e webhooks.",
    "Testes end-to-end, ajustes de performance e acessibilidade.",
    "Preparação para go-live: documentação, treinamento e deploy.",
]

SPRINT_RETROS_WENT_WELL = [
    "Comunicação entre dev e design foi excelente. Entregas no prazo.",
    "Estimativas mais precisas após o refinamento de backlog.",
    "Review bem participativo com o cliente. Feedback ótimo.",
    "Cobertura de testes aumentou de 60% para 78%.",
    "Nenhum incidente de produção durante a sprint.",
    "Integração CI/CD reduziu tempo de deploy de 40min para 8min.",
]
SPRINT_RETROS_IMPROVE = [
    "Estimativas de tarefas de infra ainda são imprecisas.",
    "Daily ficou muito longa. Objetivo: máximo 15 minutos.",
    "Muitas interrupções por chamados de suporte na sprint.",
    "Divida técnica acumulada precisa de sprint de refatoração.",
    "Documentação de API desatualizada causou retrabalho.",
    "Falta de ambiente de staging causou bugs em produção.",
]

all_sprints = []

for proj_idx, proj in enumerate(projects):
    if proj == proj3:
        # proj3 ainda não começou — só 1 sprint planejada
        s, _ = Sprint.objects.get_or_create(
            company=company, name="Sprint 1 – Kickoff",
            defaults={
                "project": proj, "lead": tec3,
                "goal": SPRINT_GOALS[0],
                "status": "Planejada",
                "start_at": days_ago(-7), "end_at": days_ago(-21),
                "capacity": 80, "story_points": 30,
            },
        )
        all_sprints.append(s)
        continue

    for sp_num in range(1, 7):
        # sprints de 2 semanas; as últimas 2 ainda não concluídas
        end_offset   = (6 - sp_num) * 14
        start_offset = end_offset + 14
        if sp_num < 5:
            status = "Concluída"
        elif sp_num == 5:
            status = "Ativa"
        else:
            status = "Planejada"

        lead = tec3 if proj_idx == 0 else tec5
        name = f"Sprint {sp_num} – {['Fundação','Auth & Perfil','Módulo Core','Integrações','Performance','Go-Live'][sp_num-1]}"
        s, _ = Sprint.objects.get_or_create(
            company=company, name=name,
            defaults={
                "project": proj, "lead": lead,
                "goal": SPRINT_GOALS[sp_num - 1],
                "status": status,
                "start_at": days_ago(start_offset),
                "end_at": days_ago(end_offset),
                "capacity": 80, "story_points": random.randint(28, 45),
            },
        )
        all_sprints.append(s)

        # Participantes
        devs = [tec3, tec4] if proj_idx == 0 else [tec5, tec2]
        for dev in devs:
            SprintParticipant.objects.get_or_create(
                company=company, sprint=s, user=dev,
                defaults={
                    "hours_per_day": Decimal("8"),
                    "working_days": 10,
                    "availability_factor": Decimal(str(round(random.uniform(0.8, 1.0), 1))),
                    "is_available": True,
                },
            )

        # Review + Retrospectiva só para sprints concluídas
        if status == "Concluída":
            planned = s.story_points
            delivered = planned - random.randint(0, 5)
            SprintReview.objects.get_or_create(
                company=company, sprint=s,
                defaults={
                    "planned_points": planned,
                    "delivered_points": delivered,
                    "planned_items": random.randint(8, 14),
                    "delivered_items": random.randint(7, 14),
                    "incomplete_activity_ids": [],
                    "notes": f"Sprint concluída com {round(delivered/planned*100)}% dos pontos entregues.",
                    "created_by": lead,
                },
            )
            SprintRetrospective.objects.get_or_create(
                company=company, sprint=s,
                defaults={
                    "went_well": random.choice(SPRINT_RETROS_WENT_WELL),
                    "to_improve": random.choice(SPRINT_RETROS_IMPROVE),
                    "action_items": [
                        {"text": "Revisar processo de estimativa no próximo refinamento", "done": bool(random.randint(0,1))},
                        {"text": "Atualizar documentação de API antes da próxima sprint", "done": bool(random.randint(0,1))},
                    ],
                    "created_by": lead,
                },
            )

print(f"   ✓ {len(all_sprints)} sprints · reviews e retrospectivas para sprints concluídas")


# ══════════════════════════════════════════════════════════════
# 11. ATIVIDADES – ~120 distribuídas pelas sprints
# ══════════════════════════════════════════════════════════════
print("\n[11/14] Atividades …")

ACT_TEMPLATES_DEV = [
    # (title, type, sp, est_hours)
    ("Configurar ambiente Docker e docker-compose",            "Tarefa",   3,  8),
    ("Setup de CI/CD com GitHub Actions",                     "Tarefa",   5,  10),
    ("Implementar autenticação JWT + refresh token",          "Historia", 8,  16),
    ("Tela de login e recuperação de senha",                  "Historia", 5,  12),
    ("CRUD de usuários com paginação e filtros",              "Historia", 8,  16),
    ("Dashboard principal – cards de métricas",               "Historia", 8,  20),
    ("API REST – endpoints de pedidos",                       "Historia", 8,  16),
    ("Módulo financeiro – extrato e resumo",                  "Historia", 5,  12),
    ("Integração com gateway de pagamento",                   "Historia", 13, 24),
    ("Notificações push e e-mail transacional",               "Tarefa",   5,  10),
    ("Sincronização de estoque via webhook",                  "Historia", 8,  16),
    ("Testes unitários – cobertura 80%",                      "Tarefa",   3,  6),
    ("Testes E2E com Cypress – fluxo principal",              "Tarefa",   5,  10),
    ("Otimização de queries SQL – N+1 eliminado",             "Tarefa",   3,  8),
    ("Documentação Swagger dos endpoints",                    "Tarefa",   2,  4),
    ("PWA – service worker e cache offline",                  "Historia", 8,  16),
    ("Refatoração – separar camada de serviços",              "Tarefa",   5,  10),
    ("Integração Sentry para monitoramento de erros",         "Tarefa",   2,  4),
    ("Auditoria de segurança – OWASP Top 10",                 "Tarefa",   5,  12),
    ("Preparar runbook de deploy e rollback",                 "Tarefa",   2,  6),
]

ACT_TEMPLATES_INFRA = [
    ("Auditoria de contas IAM e políticas AWS",               "Tarefa",   5,  12),
    ("Configurar VPC com subnets públicas e privadas",        "Tarefa",   3,  8),
    ("Setup de RDS Multi-AZ com failover automático",         "Tarefa",   5,  10),
    ("Configurar CloudFront e Route 53",                      "Tarefa",   3,  6),
    ("Implementar backup automático com S3 e Glacier",        "Tarefa",   3,  8),
    ("Monitoramento CloudWatch – dashboards e alertas",       "Tarefa",   3,  6),
    ("Configurar WAF e Shield para proteção DDoS",            "Tarefa",   5,  10),
    ("Automatizar infra com Terraform",                       "Historia", 8,  20),
    ("Migrar banco de dados on-premise para RDS",             "Historia", 13, 24),
    ("Configurar ECS para containers Docker",                 "Historia", 8,  16),
    ("Implementar Auto Scaling Group",                        "Tarefa",   5,  10),
    ("Configurar ElastiCache Redis para sessões",             "Tarefa",   3,  6),
    ("Documentação de arquitetura – diagrama C4",             "Tarefa",   2,  8),
    ("Treinamento da equipe na nova infra AWS",               "Tarefa",   3,  6),
    ("Validação de failover – testes de DR",                  "Tarefa",   5,  12),
]

STATUSES_BY_SPRINT = {
    "Concluída": lambda: random.choices(["Concluido","Concluido","Em revisao"], weights=[8,1,1])[0],
    "Ativa":     lambda: random.choices(["Backlog","Em andamento","Em revisao","Concluido"], weights=[3,4,2,1])[0],
    "Planejada": lambda: "Backlog",
}

activity_count = 0
all_activities = []
all_act_plans = []

# Projeto 1 – sprints 1-6
proj1_sprints = [s for s in all_sprints if s.project == proj1]
for i, sprint in enumerate(proj1_sprints):
    templates = ACT_TEMPLATES_DEV[i*3: i*3+4] if i*3+4 <= len(ACT_TEMPLATES_DEV) else ACT_TEMPLATES_DEV[-4:]
    status_fn = STATUSES_BY_SPRINT.get(sprint.status, lambda: "Backlog")
    for title, atype, sp, est in templates:
        act_status = status_fn()
        assignee = random.choice([tec3, tec4, tec6])
        a, _ = Activity.objects.get_or_create(
            company=company, title=f"{title} – {sprint.name[:15]}",
            defaults={
                "project": proj1, "sprint": sprint,
                "assignee": assignee, "type": atype,
                "status": act_status,
                "story_points": sp, "est_hours": Decimal(str(est)),
                "priority": random.choice(["Alta","Alta","Média","Baixa"]),
                "start_at": sprint.start_at,
                "due_at": sprint.end_at,
                "description": f"Implementar: {title}.",
                "tags": ["backend"] if assignee == tec3 else ["frontend"],
            },
        )
        a.assignees.add(assignee)
        all_activities.append(a)
        activity_count += 1

        # SprintActivityPlan
        SprintActivityPlan.objects.get_or_create(
            company=company, sprint=sprint, activity=a,
            defaults={
                "project": proj1,
                "responsible_ids": [str(assignee.id)],
                "planned_hours": Decimal(str(est)),
                "story_points": sp,
                "priority": "Alta",
            },
        )

# Projeto 2 – infra
proj2_sprints = [s for s in all_sprints if s.project == proj2]
for i, sprint in enumerate(proj2_sprints):
    templates = ACT_TEMPLATES_INFRA[i*2: i*2+3] if i*2+3 <= len(ACT_TEMPLATES_INFRA) else ACT_TEMPLATES_INFRA[-3:]
    status_fn = STATUSES_BY_SPRINT.get(sprint.status, lambda: "Backlog")
    for title, atype, sp, est in templates:
        act_status = status_fn()
        assignee = random.choice([tec5, tec2])
        a, _ = Activity.objects.get_or_create(
            company=company, title=f"{title} – {sprint.name[:15]}",
            defaults={
                "project": proj2, "sprint": sprint,
                "assignee": assignee, "type": atype,
                "status": act_status,
                "story_points": sp, "est_hours": Decimal(str(est)),
                "priority": "Alta" if sp >= 5 else "Média",
                "start_at": sprint.start_at,
                "due_at": sprint.end_at,
                "description": f"Executar: {title}.",
                "tags": ["infra", "aws"],
            },
        )
        a.assignees.add(assignee)
        all_activities.append(a)
        activity_count += 1

        SprintActivityPlan.objects.get_or_create(
            company=company, sprint=sprint, activity=a,
            defaults={
                "project": proj2,
                "responsible_ids": [str(assignee.id)],
                "planned_hours": Decimal(str(est)),
                "story_points": sp,
                "priority": "Alta" if sp >= 5 else "Média",
            },
        )

print(f"   ✓ {activity_count} atividades")


# ══════════════════════════════════════════════════════════════
# 12. COMENTÁRIOS EM ATIVIDADES
# ══════════════════════════════════════════════════════════════
print("\n[12/14] Comentários em atividades …")
act_comment_pool = [
    "Implementação concluída. Aguardando review de código.",
    "PR aberto. Link: #42. Solicito revisão até amanhã.",
    "Testes passando. Deploy em staging realizado.",
    "Ajuste necessário: refatorar validação conforme feedback.",
    "Bloqueado por tarefa de autenticação. Comunicando o time.",
    "Integração testada com sucesso em homologação.",
    "Encontrei um bug durante os testes. Abrindo sub-tarefa.",
    "Documentação atualizada no Confluence.",
    "Performance melhorou 40% após otimização do índice.",
    "Code review feito. 3 comentários para ajustar antes de merge.",
]
act_comment_count = 0
for act in all_activities:
    if act.status in ("Concluido", "Em andamento", "Em revisao"):
        num = random.choices([0, 1, 2], weights=[3, 5, 2])[0]
        for body in random.sample(act_comment_pool, min(num, len(act_comment_pool))):
            ActivityComment.objects.get_or_create(
                company=company, activity=act, author=act.assignee, body=body,
                defaults={"is_internal": True},
            )
            act_comment_count += 1
print(f"   ✓ {act_comment_count} comentários em atividades")


# ══════════════════════════════════════════════════════════════
# 13. TIME ENTRIES – registro diário de horas
# ══════════════════════════════════════════════════════════════
print("\n[13/14] Registros de tempo …")
time_entry_count = 0
work_descriptions = [
    "Desenvolvimento e testes da funcionalidade.",
    "Code review e ajustes pós-feedback.",
    "Reunião de alinhamento e documentação.",
    "Investigação de bug e correção.",
    "Deploy e monitoramento pós-release.",
    "Refatoração e melhoria de performance.",
    "Escrita de testes automatizados.",
    "Integração com serviço externo.",
]
for act in all_activities:
    if act.status in ("Concluido", "Em andamento"):
        sprint_end = act.sprint.end_at if act.sprint else today
        sprint_start = act.sprint.start_at if act.sprint else (today - timedelta(days=14))
        # Gerar 1-3 entradas de tempo por atividade
        for day_offset in range(0, min(10, (sprint_end - sprint_start).days + 1), random.randint(2, 4)):
            entry_date = sprint_start + timedelta(days=day_offset)
            if entry_date > today:
                break
            hours = Decimal(str(random.choice([2, 4, 4, 6, 8])))
            ActivityTimeEntry.objects.get_or_create(
                company=company,
                activity=act,
                collaborator=act.assignee,
                date=entry_date,
                defaults={
                    "hours": hours,
                    "work_description": random.choice(work_descriptions),
                },
            )
            time_entry_count += 1
print(f"   ✓ {time_entry_count} registros de tempo")


# ══════════════════════════════════════════════════════════════
# 14. SPRINT TICKET PLANS para sprint ativa
# ══════════════════════════════════════════════════════════════
print("\n[14/14] SprintTicketPlans …")
active_sprints = [s for s in all_sprints if s.status == "Ativa"]
sprint_ticket_count = 0
# Pegar tickets recentes (últimas 2 semanas) e associar à sprint ativa
recent_tickets = [t for t in created_tickets if t.status in ("Em atendimento","Triagem","Aberto")][-10:]
for sprint in active_sprints:
    for ticket in random.sample(recent_tickets, min(4, len(recent_tickets))):
        _, created = SprintTicketPlan.objects.get_or_create(
            company=company, sprint=sprint, ticket=ticket,
            defaults={
                "responsible_ids": [str(ticket.responsible_technician.id)] if ticket.responsible_technician else [],
                "planned_hours": Decimal(str(random.choice([2, 4, 6]))),
                "story_points": random.choice([1, 2, 3]),
                "priority": "Alta" if ticket.priority in ("Critica","Alta") else "Média",
            },
        )
        if created:
            sprint_ticket_count += 1
print(f"   ✓ {sprint_ticket_count} tickets planejados em sprints ativas")


# ══════════════════════════════════════════════════════════════
# RESUMO FINAL
# ══════════════════════════════════════════════════════════════
print("\n" + "═" * 65)
print("  SEED CONCLUÍDO COM SUCESSO!")
print("═" * 65)

total_finished = Ticket.objects.filter(company=company, status="Finalizado").count()
total_rated = Ticket.objects.filter(company=company, rating__isnull=False).count()
total_sprints_done = Sprint.objects.filter(company=company, status="Concluída").count()

print(f"""
  Empresa:    {company.name}

  ── Acessos ──────────────────────────────────────────────────
  Superadmin: anthony.dn05@gmail.com    / Admin@1234  (is_superuser)
  Admin:      admin@nimbus.tech          / Admin@1234
  Técnicos:   carlos.oliveira, julia.santos, rafael.lima,
              beatriz.mendes, gabriel.ferreira, larissa.rocha
              → senha: Admin@1234
  Clientes:   joao@varejora.com.br, ana@varejora.com.br,
              pedro@varejora.com.br, fernanda@horizonteconstrucoes.com,
              marco@healthplus.com.br, lucas@healthplus.com.br,
              camila@edutech.com.br, rodrigo@edutech.com.br
              → senha: Admin@1234

  ── Dados gerados ────────────────────────────────────────────
  Tickets:    {Ticket.objects.filter(company=company).count()} total
              · {total_finished} finalizados
              · {total_rated} com avaliação CSAT
              · {Ticket.objects.filter(company=company, reopen_count__gt=0).count()} reabertos
  Projetos:   3  (Portal v3, Infra AWS, BI & Relatórios)
  Sprints:    {Sprint.objects.filter(company=company).count()} total · {total_sprints_done} concluídas
  Atividades: {Activity.objects.filter(company=company).count()}
  Comentários (tickets):    {comment_count}
  Time entries:             {time_entry_count}
  Período:    últimos 6 meses (26 semanas)
""")
