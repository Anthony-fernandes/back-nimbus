#!/usr/bin/env python
"""
Seed script — popula o banco com dados realistas seguindo o fluxo completo do sistema.

Uso:
    python manage.py shell < seed.py
  ou
    python seed.py  (se DJANGO_SETTINGS_MODULE estiver configurado)

Cria:
  - 1 empresa (Nimbus Tech)
  - 1 superadmin global  (anthony.dn05@gmail.com / Admin@1234)
  - 1 admin da empresa   (admin@nimbus.tech / Admin@1234)
  - 4 técnicos
  - 3 clientes (empresas-cliente)
  - 5 usuários CLIENT vinculados aos clientes
  - 3 departamentos + 3 cargos
  - 2 equipes
  - 6 categorias de ticket com SLA
  - 5 políticas de SLA
  - 30 tickets em vários status/prioridade/tipo ITIL
  - Comentários e histórico nos tickets
  - 2 projetos com membros
  - 3 sprints (concluída, ativa, planejada)
  - 20 atividades distribuídas entre sprints/projetos
  - Sprint review + retrospectiva para sprint concluída
  - Planos de atividade e ticket nas sprints
"""

import os
import sys
import django
from datetime import date, timedelta, datetime
from decimal import Decimal

# ── bootstrap Django se executado fora do manage.py shell ──────────────────────
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    django.setup()

from django.utils import timezone
from django.db import transaction

# ── imports dos models ─────────────────────────────────────────────────────────
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

now = timezone.now()
today = date.today()

print("═" * 60)
print("  SEED — Nimbus Tech")
print("═" * 60)


# ══════════════════════════════════════════════════════════════
# EMPRESA
# ══════════════════════════════════════════════════════════════
print("\n[1/12] Empresa …")
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
# SUPERADMIN GLOBAL
# ══════════════════════════════════════════════════════════════
print("\n[2/12] Superadmin global …")
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
    print("   ✓ anthony.dn05@gmail.com criado (senha: Admin@1234)")
else:
    print("   ✓ anthony.dn05@gmail.com já existia")


# ══════════════════════════════════════════════════════════════
# DEPARTAMENTOS E CARGOS
# ══════════════════════════════════════════════════════════════
print("\n[3/12] Departamentos e Cargos …")
dept_data = [
    ("TI", "Tecnologia da Informação"),
    ("Suporte", "Suporte ao cliente e helpdesk"),
    ("Desenvolvimento", "Engenharia de software"),
]
depts = {}
for name, desc in dept_data:
    d, _ = Department.objects.get_or_create(
        company=company, name=name, defaults={"description": desc}
    )
    depts[name] = d
print(f"   ✓ {len(depts)} departamentos")

pos_data = [
    ("Analista de Suporte", False),
    ("Desenvolvedor Pleno", False),
    ("Gestor de TI", True),
]
positions = {}
for name, auto in pos_data:
    p, _ = Position.objects.get_or_create(
        company=company, name=name, defaults={"auto_approval": auto}
    )
    positions[name] = p
print(f"   ✓ {len(positions)} cargos")


# ══════════════════════════════════════════════════════════════
# USUÁRIOS (admin empresa + técnicos)
# ══════════════════════════════════════════════════════════════
print("\n[4/12] Usuários internos …")

def make_user(username, email, first, last, role, dept=None, pos=None, job="", hourly=0):
    u, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": username,
            "first_name": first,
            "last_name": last,
            "role": role,
            "company": company,
            "department": dept,
            "position": pos,
            "job_title": job,
            "hourly_cost": Decimal(str(hourly)),
            "is_active": True,
        },
    )
    if created:
        u.set_password("Admin@1234")
        u.save()
    return u

admin = make_user(
    "admin@nimbus.tech", "admin@nimbus.tech",
    "Mariana", "Costa", "ADMIN",
    dept=depts["TI"], pos=positions["Gestor de TI"],
    job="Gestora de TI", hourly=120,
)

tec1 = make_user(
    "carlos.oliveira", "carlos.oliveira@nimbus.tech",
    "Carlos", "Oliveira", "TECHNICIAN",
    dept=depts["Suporte"], pos=positions["Analista de Suporte"],
    job="Analista de Suporte N1", hourly=80,
)
tec2 = make_user(
    "julia.santos", "julia.santos@nimbus.tech",
    "Júlia", "Santos", "TECHNICIAN",
    dept=depts["Suporte"], pos=positions["Analista de Suporte"],
    job="Analista de Suporte N2", hourly=90,
)
tec3 = make_user(
    "rafael.lima", "rafael.lima@nimbus.tech",
    "Rafael", "Lima", "TECHNICIAN",
    dept=depts["Desenvolvimento"], pos=positions["Desenvolvedor Pleno"],
    job="Desenvolvedor Backend", hourly=110,
)
tec4 = make_user(
    "beatriz.mendes", "beatriz.mendes@nimbus.tech",
    "Beatriz", "Mendes", "TECHNICIAN",
    dept=depts["Desenvolvimento"], pos=positions["Desenvolvedor Pleno"],
    job="Desenvolvedora Frontend", hourly=110,
)

technicians = [tec1, tec2, tec3, tec4]
print(f"   ✓ admin@nimbus.tech + {len(technicians)} técnicos")


# ══════════════════════════════════════════════════════════════
# CLIENTES
# ══════════════════════════════════════════════════════════════
print("\n[5/12] Clientes …")
clients_data = [
    ("Varejo Rápido S.A.", "varejo@varejora.com.br", "João Mendonça", "Varejo", "Pro", Decimal("5000")),
    ("Construtora Horizonte", "ti@horizonteconstrucoes.com", "Fernanda Rocha", "Construção Civil", "Enterprise", Decimal("12000")),
    ("HealthPlus Planos", "suporte@healthplus.com.br", "Marco Aurélio", "Saúde", "Pro", Decimal("8000")),
]
clients = []
for name, email, contact, sector, plan, mrr in clients_data:
    c, _ = Client.objects.get_or_create(
        company=company, name=name,
        defaults={
            "email": email,
            "contact_name": contact,
            "sector": sector,
            "plan": plan,
            "mrr": mrr,
            "status": "Ativo",
            "health": "Bom",
        },
    )
    clients.append(c)
print(f"   ✓ {len(clients)} clientes")

# Usuários CLIENT vinculados
client_users = []
client_user_data = [
    ("joao.mendonca", "joao@varejora.com.br", "João", "Mendonça", clients[0]),
    ("fernanda.rocha", "fernanda@horizonteconstrucoes.com", "Fernanda", "Rocha", clients[1]),
    ("marco.aurelio", "marco@healthplus.com.br", "Marco", "Aurélio", clients[2]),
    ("ana.varejo", "ana@varejora.com.br", "Ana", "Souza", clients[0]),
    ("lucas.health", "lucas@healthplus.com.br", "Lucas", "Ferreira", clients[2]),
]
for username, email, first, last, client_obj in client_user_data:
    u = User.objects.filter(email=email).first()
    if not u:
        u = User.objects.filter(username=username).first()
    if not u:
        u = User(
            username=username,
            email=email,
            first_name=first,
            last_name=last,
            role="CLIENT",
            company=company,
            client=client_obj,
            is_active=True,
        )
        u.set_password("Admin@1234")
        u.save()
    client_users.append(u)
print(f"   ✓ {len(client_users)} usuários CLIENT")


# ══════════════════════════════════════════════════════════════
# EQUIPES
# ══════════════════════════════════════════════════════════════
print("\n[6/12] Equipes …")
team_suporte, _ = Team.objects.get_or_create(
    company=company, name="Equipe de Suporte",
    defaults={
        "description": "Helpdesk e atendimento ao cliente",
        "leader": tec1,
        "color": "#6366f1",
        "tipo": "suporte",
        "default_capacity": Decimal("40"),
    },
)
team_dev, _ = Team.objects.get_or_create(
    company=company, name="Equipe de Desenvolvimento",
    defaults={
        "description": "Engenharia e entrega de software",
        "leader": tec3,
        "color": "#22c55e",
        "tipo": "equipe",
        "default_capacity": Decimal("80"),
    },
)
for user, team in [(tec1, team_suporte), (tec2, team_suporte), (tec3, team_dev), (tec4, team_dev)]:
    TeamMember.objects.get_or_create(
        company=company, team=team, user=user,
        defaults={"default_hours_per_day": Decimal("8"), "default_capacity": Decimal("40")},
    )
print("   ✓ 2 equipes + membros")


# ══════════════════════════════════════════════════════════════
# CATEGORIAS DE TICKET
# ══════════════════════════════════════════════════════════════
print("\n[7/12] Categorias de Ticket …")
cat_data = [
    ("Suporte Geral", "8h", "Incidente", "Media", False),
    ("Infraestrutura", "4h", "Incidente", "Alta", True),
    ("Desenvolvimento", "24h", "Requisição", "Baixa", True),
    ("Acesso e Permissões", "2h", "Requisição", "Alta", False),
    ("Problema Crítico", "1h", "Problema", "Critica", True),
    ("Mudança de Sistema", "48h", "Mudança", "Media", True),
]
categories = {}
for name, sla, def_type, def_prio, approval in cat_data:
    c, _ = TicketCategory.objects.get_or_create(
        company=company, name=name,
        defaults={
            "sla": sla,
            "default_type": def_type,
            "default_priority": def_prio,
            "approval_required": approval,
        },
    )
    categories[name] = c
print(f"   ✓ {len(categories)} categorias")


# ══════════════════════════════════════════════════════════════
# POLÍTICAS DE SLA
# ══════════════════════════════════════════════════════════════
print("\n[8/12] Políticas de SLA …")
sla_policies = [
    ("SLA Critica - 1h", "Critica", "Suporte Geral", "1h", 10),
    ("SLA Alta - 4h", "Alta", "Suporte Geral", "4h", 8),
    ("SLA Media - 8h", "Media", "Suporte Geral", "8h", 5),
    ("SLA Baixa - 24h", "Baixa", "Suporte Geral", "24h", 2),
    ("SLA Infra Critica - 2h", "Critica", "Infraestrutura", "2h", 10),
]
for name, priority, cat_name, response_time, weight in sla_policies:
    SLAPolicy.objects.get_or_create(
        company=company, name=name,
        defaults={
            "priority": priority,
            "category": cat_name,
            "response_time": response_time,
            "priority_weight": weight,
            "active": True,
        },
    )
print(f"   ✓ {len(sla_policies)} políticas SLA")


# ══════════════════════════════════════════════════════════════
# TICKETS
# ══════════════════════════════════════════════════════════════
print("\n[9/12] Tickets …")

def make_ticket(title, description, client, requester_user, technician, category_name,
                ticket_type, impact, urgency, status, days_ago=None, finished=False,
                rating=None, reopen_count=0):
    opened = today - timedelta(days=days_ago or 0)
    finished_at = now - timedelta(days=max(0, (days_ago or 1) - 1)) if finished else None
    sla_due_at = now + timedelta(hours=8) if not finished else now - timedelta(hours=1)

    t, created = Ticket.objects.get_or_create(
        company=company,
        title=title,
        defaults={
            "description": description,
            "client": client,
            "requester_user": requester_user,
            "requester": f"{requester_user.first_name} {requester_user.last_name}",
            "responsible_technician": technician,
            "category": category_name,
            "type": ticket_type,
            "impact": impact,
            "urgency": urgency,
            "status": status,
            "opened_at": opened,
            "sla_due_at": sla_due_at,
            "finished_at": finished_at,
            "est_hours": Decimal("4"),
            "sla": "8h",
            "rating": rating,
            "rated_at": finished_at if rating else None,
            "reopen_count": reopen_count,
            "last_reopened_at": now - timedelta(days=1) if reopen_count else None,
        },
    )
    if created:
        t.technicians.add(technician)
    return t

tickets_spec = [
    # title, desc, client_idx, client_user_idx, tech_idx, category, type, impact, urgency, status, days_ago, finished, rating, reopen
    ("Sistema lento durante pico de acesso", "Usuários relatam lentidão extrema no ERP entre 9h e 11h.", 0, 0, 0, "Suporte Geral", "Incidente", "Alto", "Alta", "Finalizado", 20, True, 5, 0),
    ("Erro ao emitir nota fiscal", "Tela de NF-e retorna código 500 ao salvar.", 0, 3, 1, "Suporte Geral", "Incidente", "Alto", "Alta", "Em atendimento", 5, False, None, 0),
    ("Solicitar criação de novo usuário", "Preciso criar acesso para o colaborador Pedro Alves.", 0, 0, 0, "Acesso e Permissões", "Requisição", "Baixo", "Baixa", "Finalizado", 15, True, 4, 0),
    ("Integração com API de pagamento falhou", "Webhook do gateway retorna 401 desde ontem.", 0, 3, 2, "Desenvolvimento", "Problema", "Alto", "Alta", "Em atendimento", 3, False, None, 1),
    ("Relatório mensal não exporta PDF", "Botão de exportar PDF não funciona no Firefox.", 1, 1, 1, "Suporte Geral", "Incidente", "Médio", "Média", "Finalizado", 10, True, 3, 0),
    ("Atualização de servidor de produção", "Solicitar janela de manutenção para atualização do SO.", 1, 1, 0, "Mudança de Sistema", "Mudança", "Alto", "Média", "Aguardando Aprovacao", 2, False, None, 0),
    ("VPN não conecta em home office", "Colaboradores não conseguem conectar à VPN após update do Windows.", 1, 1, 0, "Infraestrutura", "Incidente", "Alto", "Alta", "Triagem", 1, False, None, 0),
    ("Banco de dados fora do ar", "PostgreSQL parou após falha de energia.", 2, 2, 2, "Problema Crítico", "Problema", "Alto", "Alta", "Finalizado", 30, True, 5, 0),
    ("Resetar senha de usuário bloqueado", "Usuário maria@healthplus.com.br está bloqueado.", 2, 4, 1, "Acesso e Permissões", "Requisição", "Baixo", "Baixa", "Finalizado", 8, True, 5, 0),
    ("Certificado SSL expirado", "Site retorna ERR_CERT_EXPIRED para os clientes.", 2, 2, 0, "Infraestrutura", "Incidente", "Alto", "Alta", "Em atendimento", 0, False, None, 0),
    ("Backup automático não rodou", "Job do cron de backup não executou na sexta.", 0, 0, 2, "Infraestrutura", "Problema", "Médio", "Média", "Validacao", 4, False, None, 0),
    ("Implementar módulo de relatórios", "Novo módulo de BI conforme especificação v2.", 1, 1, 3, "Desenvolvimento", "Requisição", "Médio", "Baixa", "Finalizado", 45, True, 4, 0),
    ("Crash no app mobile iOS 17", "App fecha sozinho ao abrir tela de pedidos no iOS 17.", 0, 3, 3, "Suporte Geral", "Incidente", "Alto", "Alta", "Em atendimento", 2, False, None, 0),
    ("Permissão de administrador solicitada", "Usuário precisa de acesso admin no painel financeiro.", 2, 2, 1, "Acesso e Permissões", "Requisição", "Baixo", "Baixa", "Finalizado", 12, True, 4, 0),
    ("Migração de dados para nova plataforma", "Migrar 50k registros do legado para o novo sistema.", 1, 1, 3, "Mudança de Sistema", "Mudança", "Alto", "Média", "Aprovado", 7, False, None, 0),
    ("Erro na sincronização de estoque", "Estoque do ERP diverge do WMS após sync.", 0, 0, 2, "Problema Crítico", "Problema", "Alto", "Alta", "Em atendimento", 1, False, None, 0),
    ("Configurar firewall para novo servidor", "Liberar portas 443 e 8443 no FW para IP 10.0.1.50.", 2, 4, 0, "Infraestrutura", "Requisição", "Médio", "Média", "Finalizado", 22, True, 5, 0),
    ("Dashboard carrega em branco", "Após deploy, dashboard retorna tela branca.", 0, 3, 3, "Suporte Geral", "Incidente", "Alto", "Alta", "Finalizado", 18, True, 3, 2),
    ("Novo campo obrigatório no cadastro", "Adicionar campo CPF como obrigatório no formulário.", 1, 1, 3, "Desenvolvimento", "Requisição", "Baixo", "Baixa", "Aberto", 0, False, None, 0),
    ("Alertas de monitoramento parados", "Grafana não envia alertas de CPU/memória.", 2, 2, 2, "Infraestrutura", "Problema", "Médio", "Alta", "Triagem", 1, False, None, 0),
    ("Lentidão na consulta de clientes", "Query de busca de clientes demora +10s.", 0, 0, 2, "Problema Crítico", "Problema", "Médio", "Alta", "Finalizado", 25, True, 4, 0),
    ("Solicitar aumento de limite de upload", "Limite atual de 5MB é insuficiente, precisa de 50MB.", 1, 1, 1, "Acesso e Permissões", "Requisição", "Baixo", "Baixa", "Finalizado", 35, True, 5, 0),
    ("Autenticação 2FA não funciona", "Código TOTP sempre inválido para novos usuários.", 2, 4, 1, "Suporte Geral", "Incidente", "Alto", "Alta", "Aberto", 0, False, None, 0),
    ("Upgrade de versão do Node.js", "Atualizar Node 16 → 20 LTS em todos os servidores.", 0, 0, 3, "Mudança de Sistema", "Mudança", "Médio", "Média", "Aguardando Aprovacao", 3, False, None, 0),
    ("Notificações por e-mail não chegam", "E-mails de confirmação de pedido não são enviados.", 0, 3, 1, "Suporte Geral", "Incidente", "Alto", "Alta", "Finalizado", 14, True, 4, 0),
    ("Criar relatório de comissões", "Relatório mensal de comissões por vendedor.", 1, 1, 3, "Desenvolvimento", "Requisição", "Médio", "Média", "Em atendimento", 2, False, None, 0),
    ("Storage S3 quase cheio", "Bucket de produção em 92% de capacidade.", 2, 2, 2, "Infraestrutura", "Problema", "Alto", "Alta", "Em atendimento", 0, False, None, 0),
    ("App web offline para clientes", "Site institucional retorna 503 para usuários externos.", 0, 0, 0, "Problema Crítico", "Problema", "Alto", "Alta", "Finalizado", 60, True, 5, 0),
    ("Perfil de usuário não salva foto", "Upload de avatar retorna erro 413.", 1, 1, 3, "Suporte Geral", "Incidente", "Baixo", "Baixa", "Finalizado", 9, True, 3, 0),
    ("Regras de automação de chamados", "Configurar automação para escalar tickets críticos.", 2, 2, 1, "Desenvolvimento", "Requisição", "Médio", "Média", "Aberto", 0, False, None, 0),
]

created_tickets = []
for spec in tickets_spec:
    title, desc, ci, cui, ti, cat, ttype, impact, urgency, status, days, finished, rating, reopen = spec
    t = make_ticket(
        title=title, description=desc,
        client=clients[ci],
        requester_user=client_users[cui],
        technician=technicians[ti],
        category_name=cat,
        ticket_type=ttype,
        impact=impact,
        urgency=urgency,
        status=status,
        days_ago=days,
        finished=finished,
        rating=rating,
        reopen_count=reopen,
    )
    created_tickets.append(t)

print(f"   ✓ {len(created_tickets)} tickets")

# Comentários nos tickets
print("   → Adicionando comentários …")
comment_data = [
    (0, tec1, "Investigando o servidor de aplicação. CPU em 98%.", True),
    (0, client_users[0], "Por favor resolvam com urgência, está impactando vendas.", False),
    (0, tec1, "Identificada query sem índice. Aplicando correção.", True),
    (1, tec2, "Reproduzindo o erro em ambiente de homologação.", True),
    (1, tec2, "Erro na lib de geração de XML da NF-e. Atualizando versão.", True),
    (3, tec3, "Verificando logs do gateway. Token de autenticação expirou.", True),
    (3, tec3, "Renovado token. Aguardando confirmação do cliente.", True),
    (6, tec1, "Verificando configuração de DNS e roteamento VPN.", True),
    (9, tec1, "Acionando equipe de infra para renovação emergencial do certificado.", True),
    (11, tec3, "Módulo entregue e em validação pelo cliente.", True),
    (11, client_users[1], "Módulo aprovado! Excelente trabalho.", False),
]
for ticket_idx, author, body, is_internal in comment_data:
    TicketComment.objects.get_or_create(
        company=company,
        ticket=created_tickets[ticket_idx],
        author=author,
        body=body,
        defaults={"is_internal": is_internal},
    )
print(f"   ✓ {len(comment_data)} comentários")

# Histórico de status (para tickets finalizados)
print("   → Histórico de status …")
status_flow = [
    ("Aberto", "Em atendimento"),
    ("Em atendimento", "Validacao"),
    ("Validacao", "Finalizado"),
]
for ticket in created_tickets[:8]:
    prev_status = "Aberto"
    for from_s, to_s in status_flow:
        TicketStatusHistory.objects.get_or_create(
            company=company,
            ticket=ticket,
            status_from=from_s,
            status_to=to_s,
            defaults={
                "changed_by": technicians[0],
                "reason": "Avanço no fluxo de atendimento.",
            },
        )
print("   ✓ Histórico de status criado")


# ══════════════════════════════════════════════════════════════
# PROJETOS
# ══════════════════════════════════════════════════════════════
print("\n[10/12] Projetos …")
proj1, _ = Project.objects.get_or_create(
    company=company,
    name="Portal do Cliente v3",
    defaults={
        "client": clients[0],
        "department": depts["Desenvolvimento"],
        "tipo": "cliente",
        "metodologia": "scrum",
        "description": "Redesign completo do portal do cliente com nova UX e APIs REST.",
        "status": "Em andamento",
        "owner": admin,
        "budget": Decimal("150000"),
        "real_cost": Decimal("62000"),
        "progress": 45,
        "start_at": today - timedelta(days=90),
        "due_at": today + timedelta(days=90),
        "health": "on_track",
        "tags": ["portal", "react", "api"],
    },
)
proj2, _ = Project.objects.get_or_create(
    company=company,
    name="Infraestrutura Cloud",
    defaults={
        "department": depts["TI"],
        "tipo": "interno",
        "metodologia": "kanban",
        "description": "Migração de toda infraestrutura on-premise para AWS.",
        "status": "Em andamento",
        "owner": tec2,
        "budget": Decimal("80000"),
        "real_cost": Decimal("35000"),
        "progress": 30,
        "start_at": today - timedelta(days=60),
        "due_at": today + timedelta(days=120),
        "health": "at_risk",
        "tags": ["aws", "infra", "devops"],
    },
)

for user, role in [(tec3, "DESENVOLVEDOR"), (tec4, "DESENVOLVEDOR"), (tec1, "QA"), (admin, "GERENTE")]:
    ProjectMember.objects.get_or_create(
        company=company, project=proj1, user=user,
        defaults={"role": role, "active": True},
    )
for user, role in [(tec2, "GERENTE"), (tec3, "DESENVOLVEDOR"), (tec1, "ANALISTA")]:
    ProjectMember.objects.get_or_create(
        company=company, project=proj2, user=user,
        defaults={"role": role, "active": True},
    )
print("   ✓ 2 projetos + membros")


# ══════════════════════════════════════════════════════════════
# SPRINTS
# ══════════════════════════════════════════════════════════════
print("\n[11/12] Sprints …")
sprint_concluida, _ = Sprint.objects.get_or_create(
    company=company,
    name="Sprint 1 — Fundação",
    defaults={
        "project": proj1,
        "lead": tec3,
        "goal": "Estruturar arquitetura base e autenticação do portal.",
        "status": "Concluída",
        "start_at": today - timedelta(days=56),
        "end_at": today - timedelta(days=43),
        "capacity": 80,
        "story_points": 34,
    },
)
sprint_ativa, _ = Sprint.objects.get_or_create(
    company=company,
    name="Sprint 2 — Dashboard e Módulos",
    defaults={
        "project": proj1,
        "lead": tec3,
        "goal": "Implementar dashboard principal e módulos de pedidos/finanças.",
        "status": "Ativa",
        "start_at": today - timedelta(days=14),
        "end_at": today + timedelta(days=0),
        "capacity": 80,
        "story_points": 40,
    },
)
sprint_planejada, _ = Sprint.objects.get_or_create(
    company=company,
    name="Sprint 3 — Integrações",
    defaults={
        "project": proj1,
        "lead": tec4,
        "goal": "Integrar APIs de pagamento, estoque e notificações.",
        "status": "Planejada",
        "start_at": today + timedelta(days=1),
        "end_at": today + timedelta(days=14),
        "capacity": 80,
        "story_points": 45,
    },
)

# Participantes das sprints
for sprint in [sprint_concluida, sprint_ativa, sprint_planejada]:
    for user, hours, days in [(tec3, Decimal("8"), 10), (tec4, Decimal("8"), 10)]:
        SprintParticipant.objects.get_or_create(
            company=company, sprint=sprint, user=user,
            defaults={
                "hours_per_day": hours,
                "working_days": days,
                "availability_factor": Decimal("1.0"),
                "is_available": True,
            },
        )
print("   ✓ 3 sprints + participantes")


# ══════════════════════════════════════════════════════════════
# ATIVIDADES
# ══════════════════════════════════════════════════════════════
print("\n[12/12] Atividades …")

def make_activity(title, description, project, sprint, assignee, act_type, status,
                  story_points, est_hours, start_offset, due_offset, priority="Média"):
    a, _ = Activity.objects.get_or_create(
        company=company,
        title=title,
        defaults={
            "description": description,
            "project": project,
            "sprint": sprint,
            "assignee": assignee,
            "type": act_type,
            "status": status,
            "story_points": story_points,
            "est_hours": Decimal(str(est_hours)),
            "priority": priority,
            "start_at": today + timedelta(days=start_offset),
            "due_at": today + timedelta(days=due_offset),
            "tags": ["backend"] if assignee == tec3 else ["frontend"],
        },
    )
    return a

activities_spec = [
    # Sprint Concluída
    ("Configurar ambiente Docker", "Setup de containers dev/prod com docker-compose.", proj1, sprint_concluida, tec3, "Tarefa", "Concluido", 3, 8, -56, -52, "Alta"),
    ("Implementar autenticação JWT", "Login, refresh token e guard de rotas.", proj1, sprint_concluida, tec3, "Historia", "Concluido", 8, 16, -56, -49, "Alta"),
    ("Layout base do portal", "Header, sidebar, footer responsivos.", proj1, sprint_concluida, tec4, "Historia", "Concluido", 5, 12, -55, -50, "Média"),
    ("Testes de integração auth", "Cobertura de 80% nos endpoints de autenticação.", proj1, sprint_concluida, tec3, "Tarefa", "Concluido", 3, 6, -50, -44, "Média"),
    ("Deploy pipeline CI/CD", "GitHub Actions para build e deploy automático.", proj1, sprint_concluida, tec3, "Tarefa", "Concluido", 5, 10, -50, -44, "Alta"),

    # Sprint Ativa
    ("Dashboard principal", "Cards de métricas, gráficos de pedidos e faturamento.", proj1, sprint_ativa, tec4, "Historia", "Em andamento", 8, 20, -14, 0, "Alta"),
    ("API de pedidos", "CRUD completo de pedidos com filtros e paginação.", proj1, sprint_ativa, tec3, "Historia", "Em andamento", 8, 16, -14, 0, "Alta"),
    ("Módulo financeiro — visão geral", "Tela de extrato e resumo financeiro.", proj1, sprint_ativa, tec4, "Historia", "Em revisao", 5, 12, -10, 0, "Média"),
    ("Integração Sentry", "Configurar monitoramento de erros em produção.", proj1, sprint_ativa, tec3, "Tarefa", "Backlog", 2, 4, -5, 2, "Baixa"),
    ("Testes E2E dashboard", "Cypress — fluxo de login até visualização do dashboard.", proj1, sprint_ativa, tec4, "Tarefa", "Backlog", 3, 6, -5, 2, "Média"),

    # Sprint Planejada
    ("Integração API de pagamento", "Gateway PagSeguro — checkout e webhook.", proj1, sprint_planejada, tec3, "Historia", "Backlog", 13, 24, 1, 10, "Alta"),
    ("Notificações por e-mail", "Envio automático de e-mails transacionais.", proj1, sprint_planejada, tec3, "Tarefa", "Backlog", 5, 10, 1, 8, "Média"),
    ("Sincronização de estoque", "Webhook para atualizar estoque em tempo real.", proj1, sprint_planejada, tec4, "Historia", "Backlog", 8, 16, 3, 12, "Alta"),
    ("PWA — modo offline", "Service worker e cache estratégico.", proj1, sprint_planejada, tec4, "Historia", "Backlog", 8, 20, 5, 14, "Média"),
    ("Testes de carga", "k6 — 1000 usuários simultâneos.", proj1, sprint_planejada, tec3, "Tarefa", "Backlog", 3, 8, 8, 14, "Média"),

    # Projeto Infra (sem sprint)
    ("Auditoria de segurança AWS", "Revisar IAM, Security Groups e compliance.", proj2, None, tec2, "Tarefa", "Em andamento", 5, 12, -30, -15, "Alta"),
    ("Configurar VPC e subnets", "Arquitetura de rede multi-AZ.", proj2, None, tec2, "Tarefa", "Concluido", 3, 8, -60, -50, "Alta"),
    ("RDS — configurar Multi-AZ", "Alta disponibilidade do banco de dados.", proj2, None, tec3, "Tarefa", "Concluido", 5, 10, -55, -45, "Alta"),
    ("Monitoramento CloudWatch", "Dashboards e alertas de CPU/memória/disco.", proj2, None, tec2, "Tarefa", "Em andamento", 3, 6, -20, 10, "Média"),
    ("Documentação de arquitetura", "Diagrama C4 e runbook de operações.", proj2, None, tec3, "Tarefa", "Backlog", 2, 8, 5, 30, "Baixa"),
]

created_activities = []
for spec in activities_spec:
    title, desc, proj, sprint, assignee, atype, status, sp, hours, start, due, priority = spec
    a = make_activity(title, desc, proj, sprint, assignee, atype, status, sp, hours, start, due, priority)
    created_activities.append(a)
    a.assignees.add(assignee)

print(f"   ✓ {len(created_activities)} atividades")

# Planos de atividade na sprint ativa
print("   → SprintActivityPlan …")
for act in created_activities[5:10]:  # sprint ativa
    SprintActivityPlan.objects.get_or_create(
        company=company, sprint=sprint_ativa, activity=act,
        defaults={
            "project": proj1,
            "responsible_ids": [str(act.assignee.id)],
            "planned_hours": act.est_hours,
            "story_points": act.story_points,
            "priority": "Alta" if act.priority == "Alta" else "Média",
        },
    )

# Planos de ticket nas sprints
print("   → SprintTicketPlan …")
for ticket in created_tickets[:5]:
    SprintTicketPlan.objects.get_or_create(
        company=company, sprint=sprint_ativa, ticket=ticket,
        defaults={
            "responsible_ids": [str(ticket.responsible_technician.id)],
            "planned_hours": Decimal("4"),
            "story_points": 2,
            "priority": "Alta",
        },
    )

# Time entries
print("   → Registros de tempo …")
for i, act in enumerate(created_activities[:10]):
    if act.status in ("Concluido", "Em andamento", "Em revisao"):
        ActivityTimeEntry.objects.get_or_create(
            company=company,
            activity=act,
            collaborator=act.assignee,
            date=today - timedelta(days=i % 7 + 1),
            defaults={
                "hours": Decimal("4"),
                "work_description": f"Trabalho em '{act.title}'.",
            },
        )

# Comentários em atividades
print("   → Comentários em atividades …")
for act in created_activities[:5]:
    ActivityComment.objects.get_or_create(
        company=company, activity=act, author=act.assignee,
        body=f"Progresso em '{act.title}': implementação concluída, aguardando review.",
        defaults={"is_internal": True},
    )

# Sprint Review + Retrospectiva (sprint concluída)
print("   → Sprint Review e Retrospectiva …")
SprintReview.objects.get_or_create(
    company=company,
    sprint=sprint_concluida,
    defaults={
        "planned_points": 34,
        "delivered_points": 31,
        "planned_items": 5,
        "delivered_items": 5,
        "incomplete_activity_ids": [],
        "notes": "Sprint entregue com sucesso. 91% dos story points concluídos. Pequenos ajustes de CSS ficaram pendentes.",
        "created_by": tec3,
    },
)
SprintRetrospective.objects.get_or_create(
    company=company,
    sprint=sprint_concluida,
    defaults={
        "went_well": "Comunicação entre dev e design foi excelente. Entregas no prazo.",
        "to_improve": "Estimativas de tarefas de infra ainda são imprecisas. Precisamos de spike.",
        "action_items": [
            {"text": "Fazer spike de 1 dia para infra antes de estimar", "done": False},
            {"text": "Daily de 15min ao invés de 30min", "done": True},
        ],
        "created_by": tec3,
    },
)

print("\n" + "═" * 60)
print("  SEED CONCLUÍDO COM SUCESSO!")
print("═" * 60)
print(f"""
  Empresa:    {company.name}
  Superadmin: anthony.dn05@gmail.com  /  Admin@1234  (is_superuser)
  Admin:      admin@nimbus.tech        /  Admin@1234
  Técnicos:   carlos.oliveira, julia.santos, rafael.lima, beatriz.mendes
              senha: Admin@1234
  Clientes:   joao@varejora.com.br, fernanda@horizonteconstrucoes.com,
              marco@healthplus.com.br, ana@varejora.com.br, lucas@healthplus.com.br
              senha: Admin@1234

  Criados:
    {len(created_tickets)} tickets · {len(created_activities)} atividades
    3 sprints (Concluída, Ativa, Planejada)
    2 projetos · {len(clients)} clientes · 2 equipes
    {len(categories)} categorias · {len(sla_policies)} políticas SLA
""")
