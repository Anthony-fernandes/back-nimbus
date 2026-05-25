from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from apps.companies.models import Company
from apps.clients.models import Client
from apps.projects.models import Project
from apps.tickets.models import Ticket
from apps.sprints.models import Sprint
from apps.activities.models import Activity

class Command(BaseCommand):
    help = "Cria dados demonstrativos para rodar o sistema completo localmente."

    def handle(self, *args, **options):
        User = get_user_model()
        company, _ = Company.objects.get_or_create(name="Nimbus Workspace", defaults={"email":"contato@nimbus.local", "phone":"(00) 0000-0000"})
        admin, created = User.objects.get_or_create(username="admin", defaults={"email":"admin@stratos.local", "first_name":"Alex", "last_name":"Admin", "role":"ADMIN", "company": company, "is_staff": True, "is_superuser": True})
        if created:
            admin.set_password("admin123")
            admin.save()
        names = [
            ("Marina","Duarte","Tech Lead","Backend / Infra",32,28,"Backend"),
            ("Diego","Ribeiro","Senior Dev","Full-stack",40,36,"Full-stack"),
            ("Lucas","Pereira","DevOps","Cloud / Kubernetes",40,38,"DevOps"),
            ("Júlia","Mendes","Designer","UI / UX",32,24,"Design"),
            ("Rafa","Souza","QA Lead","Automação",40,34,"QA"),
            ("Bia","Lima","Suporte N2","Atendimento técnico",40,39,"Suporte"),
        ]
        users=[]
        for first,last,job,spec,total,used,grp in names:
            u,_=User.objects.get_or_create(username=f"{first.lower()}.{last.lower()}", defaults={"email":f"{first.lower()}.{last.lower()}@stratos.local","first_name":first,"last_name":last,"role":"TECHNICIAN","job_title":job,"specialty":spec,"total_hours":total,"used_hours":used,"technical_group":grp,"company":company})
            users.append(u)
        client_defs=[("Acme Corp","Enterprise",48000,"Ótimo"),("Globex","Pro",22000,"Bom"),("Initech","Pro",18000,"Atenção"),("Umbrella Co","Enterprise",36000,"Ótimo"),("Wayne Ent.","Pro",14000,"Bom"),("Stark Ind.","Enterprise",52000,"Ótimo")]
        clients=[]
        for idx,(n,plan,mrr,health) in enumerate(client_defs,1):
            c,_=Client.objects.get_or_create(company=company,name=n, defaults={"email":f"contato{idx}@example.com","phone":"(83) 99999-0000","sector":"TI","contact_name":"Responsável TI","plan":plan,"mrr":Decimal(mrr),"health":health,"status":"Ativo"})
            clients.append(c)
        project_defs=[("Migração Cloud — Acme",clients[0],"Em risco",78,120000,84200),("Portal do Cliente v2",clients[1],"Em andamento",64,80000,31200),("Integração SAP",clients[2],"Em risco",52,95000,52400),("Onboarding Mobile",clients[5],"Planejado",18,45000,5000)]
        projects=[]
        for i,(name,client,status,progress,budget,cost) in enumerate(project_defs):
            p,_=Project.objects.get_or_create(company=company,client=client,name=name, defaults={"description":"Projeto operacional integrado ao Stratos Suite.","status":status,"progress":progress,"budget":Decimal(budget),"real_cost":Decimal(cost),"owner":users[i%len(users)],"start_at":date.today()-timedelta(days=10+i),"due_at":date.today()+timedelta(days=12+i*7),"tags":["cloud","integração"],"checklist":[{"text":"Kickoff","done":True},{"text":"Homologação","done":False}]})
            p.team.set(users[:3])
            projects.append(p)
        ticket_defs=[
            ("Falha no login SSO do cliente Acme",clients[0],projects[0],"Alta","Em atendimento","2h"),
            ("Erro 500 no endpoint /invoices",clients[1],projects[1],"Crítica","Em atendimento","30m"),
            ("Solicitação: novo usuário admin",clients[2],None,"Baixa","Triagem","1d"),
            ("Lentidão no relatório financeiro",clients[3],None,"Média","Aguardando cliente","4h"),
            ("Backup noturno falhou — DB-02",clients[4],projects[2],"Alta","Em atendimento","1h"),
        ]
        tickets=[]
        for i,(title,client,project,priority,status,sla) in enumerate(ticket_defs,1):
            t,_=Ticket.objects.get_or_create(company=company,client=client,title=title, defaults={"project":project,"description":"Chamado criado automaticamente na carga de demonstração.","requester":"Cliente","category":"Atendimento","type":"Incidente","priority":priority,"impact":"Médio","urgency":"Média","status":status,"team":"Suporte N2","sla":sla,"opened_at":date.today(),"due_at":date.today()+timedelta(days=i),"est_hours":Decimal("4"),"done_hours":Decimal("1"),"tags":["demo"],"checklist":[{"text":"Analisar","done":True},{"text":"Resolver","done":False}]})
            t.technicians.set([users[i%len(users)]])
            tickets.append(t)
        sprint,_=Sprint.objects.get_or_create(company=company,name="Sprint 24", defaults={"project":projects[0],"goal":"Estabilizar principais entregas.","lead":users[0],"status":"Em andamento","start_at":date.today()-timedelta(days=6),"end_at":date.today()+timedelta(days=4),"capacity":80,"story_points":34,"backlog":[t.code for t in tickets],"tasks":["Refatorar módulo X","Implementar endpoint Y"]})
        for i,t in enumerate(tickets):
            Activity.objects.get_or_create(company=company,title=f"Atividade para {t.code}", defaults={"description":t.title,"type":"Tarefa","status":"Em progresso" if i%2 else "Backlog","priority":t.priority,"assignee":users[i%len(users)],"project":t.project,"sprint":sprint,"ticket":t,"start_at":date.today(),"due_at":date.today()+timedelta(days=3),"est_hours":Decimal("2"),"story_points":3,"tags":["ticket"],"checklist":[{"text":"Executar","done":False}]})
        self.stdout.write(self.style.SUCCESS("Demo criada. Login: admin / admin123"))
