# Stratos Suite Backend

Backend Django/DRF preparado para deploy no Render com PostgreSQL do Render Postgres.

## Stack

- Python 3.12
- Django
- Django REST Framework
- PostgreSQL
- JWT
- WhiteNoise
- django-cors-headers

## Execucao local

Crie um `.env` a partir do `.env.example` e ajuste os valores locais.

```bash
python manage.py runserver 127.0.0.1:8000
```

## Render

Modulo do Gunicorn:

```txt
config.wsgi:application
```

Build Command recomendado:

```txt
bash build.sh
```

Start Command recomendado:

```txt
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Variaveis principais:

```txt
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
SECRET_KEY=replace-with-a-strong-secret
DEBUG=False
ALLOWED_HOSTS=back-nimbus.onrender.com
CORS_ALLOWED_ORIGINS=https://front-nimbus.vercel.app
CSRF_TRUSTED_ORIGINS=https://front-nimbus.vercel.app
SECURE_SSL_REDIRECT=True
```

Para desenvolvimento local, use as origens `http://localhost:5173` e
`http://localhost:3000` nas variaveis `CORS_ALLOWED_ORIGINS` e
`CSRF_TRUSTED_ORIGINS`.
