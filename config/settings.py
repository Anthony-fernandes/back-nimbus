import os
from datetime import timedelta
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

import sentry_sdk

SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[sentry_sdk.integrations.django.DjangoIntegration()],
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
        environment=os.environ.get("DJANGO_ENV", "production"),
    )

try:
    import dj_database_url
except ModuleNotFoundError:
    dj_database_url = None

try:
    import environ
except ModuleNotFoundError:
    class _FallbackEnv:
        def __init__(self, **_schema):
            self._schema = _schema

        def read_env(self, path):
            if not path or not os.path.exists(path):
                return

            with open(path, "r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

        def __call__(self, key, default=None):
            return os.environ.get(key, default)

        def bool(self, key, default=False):
            value = os.environ.get(key)
            if value is None:
                return default
            return str(value).strip().lower() in {"1", "true", "yes", "on"}

        def list(self, key, default=None):
            value = os.environ.get(key)
            if value is None:
                return default or []
            return [item.strip() for item in str(value).split(",") if item.strip()]

    class environ:  # type: ignore[no-redef]
        Env = _FallbackEnv

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))

if (BASE_DIR / ".env").exists():
    env.read_env(BASE_DIR / ".env")

DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-dev-only"
    else:
        raise ImproperlyConfigured("SECRET_KEY environment variable is required when DEBUG=False.")

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"] if DEBUG else [],
)
if not ALLOWED_HOSTS and not DEBUG:
    raise ImproperlyConfigured("ALLOWED_HOSTS environment variable is required when DEBUG=False.")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "channels",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "django_filters",
    "apps.companies",
    "apps.users",
    "apps.authentication",
    "apps.clients",
    "apps.projects",
    "apps.tickets",
    "apps.sprints",
    "apps.activities",
    "apps.dashboard",
    "apps.notifications",
    "apps.audit",
    "apps.knowledge",
    "apps.communication",
    "apps.search",
    "apps.reports",
    "apps.webhooks",
    "apps.forum",
    "apps.doubts",
    "django_celery_beat",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Celery
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Sao_Paulo"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://localhost:6379/0")],
        },
    },
}

database_url = env("DATABASE_URL", default="")

if database_url:
    if dj_database_url is None:
        raise ModuleNotFoundError("dj_database_url must be installed when DATABASE_URL is configured.")

    DATABASES = {"default": dj_database_url.config(default=database_url, conn_max_age=600)}
elif env("POSTGRES_DB", default=""):
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER", default="postgres"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="postgres"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "300/minute",
        "login": "10/minute",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=False)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# Enable in production via env var
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 0))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SPECTACULAR_SETTINGS = {
    "TITLE": "Stratos Suite API",
    "DESCRIPTION": "API REST para gestão de clientes, projetos, chamados, sprints, atividades e dashboard.",
    "VERSION": "1.0.0",
}

# Notificacao por e-mail centralizada. Em desenvolvimento usa o backend de
# console; em producao configure SMTP via variaveis de ambiente.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = int(env("EMAIL_PORT", default="587") or 587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="Stratos Suite <no-reply@stratos.local>",
)

# URL base do frontend para compor links nas notificacoes por e-mail.
PLATFORM_WEB_URL = env("PLATFORM_WEB_URL", default="")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},
        'apps': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'common': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

MFA_APP_NAME = os.environ.get('MFA_APP_NAME', 'Stratos Suite')
