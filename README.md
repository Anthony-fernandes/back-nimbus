# Stratos Suite Backend

Backend enterprise-ready utilizando Django + DRF + PostgreSQL + Celery + Redis.

## Stack
- Python 3.12
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Docker
- JWT
- Swagger/OpenAPI

## Execução

```bash
docker-compose up --build
```

## Swagger

```txt
http://localhost:8000/api/docs/
```

## Render

Variaveis principais para configurar no servico:

```txt
SECRET_KEY=sua-chave
DEBUG=False
ALLOWED_HOSTS=seu-app.onrender.com
CSRF_TRUSTED_ORIGINS=https://seu-app.onrender.com
DATABASE_URL=postgresql://...
```

Se for subir sem Docker no Render:

```txt
Build Command: pip install -r requirements.txt
Start Command: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```
