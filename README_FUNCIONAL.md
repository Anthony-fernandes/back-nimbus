# Stratos Suite Backend — Versão funcional integrada

## O que foi implementado

- Django REST Framework funcional.
- JWT com login, refresh, logout e `/api/auth/me/`.
- CORS liberado para desenvolvimento local.
- Banco SQLite local por padrão, sem depender de PostgreSQL para rodar rapidamente.
- Models, serializers, viewsets, filtros, busca e paginação para:
  - empresas;
  - usuários/equipe;
  - clientes;
  - projetos;
  - chamados/tickets;
  - sprints;
  - atividades/backlog;
  - dashboard.
- Migrations criadas e testadas.
- Comando de carga demo.
- Dados demo já carregados no `db.sqlite3` incluído no projeto.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements/base.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

## Login demo

```txt
Usuário: admin
Senha: admin123
```

## Principais endpoints

```txt
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
GET  /api/auth/me/
GET/POST/PATCH/DELETE /api/clients/
GET/POST/PATCH/DELETE /api/projects/
GET/POST/PATCH/DELETE /api/tickets/
GET/POST/PATCH/DELETE /api/users/
GET/POST/PATCH/DELETE /api/sprints/
GET/POST/PATCH/DELETE /api/activities/
GET /api/dashboard/
GET /api/docs/
```
