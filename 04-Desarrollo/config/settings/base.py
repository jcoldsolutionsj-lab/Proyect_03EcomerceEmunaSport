"""Configuración base de Django para Emuná Sport compartida por todos los entornos."""
from pathlib import Path

import environ

from apps.nucleo.unfold_config import UNFOLD_CONFIG_EMUNA

# BASE_DIR apunta a 04-Desarrollo/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# REPO_DIR apunta a la raíz del proyecto EcomerceEmunaSport/
REPO_DIR = BASE_DIR.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://127.0.0.1:8000", "http://localhost:8000"]),
    CSRF_TRUSTED_ORIGINS=(list, ["http://127.0.0.1:8000", "http://localhost:8000"]),
    USE_S3_STORAGE=(bool, False),
    SITE_URL=(str, "http://127.0.0.1:8000"),
    ADMIN_URL=(str, "gestion/"),
    GA4_MEASUREMENT_ID=(str, ""),
    CLOUDFLARE_BEACON_TOKEN=(str, ""),
    TURNSTILE_SITE_KEY=(str, "1x00000000000000000000AA"),
    TURNSTILE_SECRET_KEY=(str, "1x0000000000000000000000000000000AA"),
)

# Leer archivo .env si existe en 04-Desarrollo/ o en la raíz
if (BASE_DIR / ".env").exists():
    environ.Env.read_env(BASE_DIR / ".env")
elif (REPO_DIR / ".env").exists():
    environ.Env.read_env(REPO_DIR / ".env")


def validar_variables_entorno_criticas(variables_requeridas: list[str]) -> None:
    """Verifica que las variables de entorno obligatorias estén definidas al arrancar.

    Qué hace:      Comprueba que cada variable requerida exista y no esté vacía en os.environ.
    Va hacia:      Detiene el arranque (Fail-Fast) si falta alguna clave crítica en demo/producción.
    Depende de:    django-environ y os.environ.
    Cuándo usarla: Al inicializar config.settings.demo y config.settings.production.
    Si no opera:   Lanza RuntimeError indicando exactamente qué variable de entorno falta.
    """
    faltantes = [nombre for nombre in variables_requeridas if not env(nombre, default="")]
    if faltantes:
        lista = ", ".join(faltantes)
        raise RuntimeError(
            f"Fallo de seguridad (Fail-Fast): Faltan variables de entorno críticas: {lista}"
        )


SECRET_KEY = env(
    "SECRET_KEY",
    default="clave-solo-para-entorno-local-desarrollo-emuna-sport-2026-segura",
)
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Aplicaciones instaladas (Unfold antes de contrib.admin para diseño Flat en /gestion/)
DJANGO_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.simple_history",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "django_htmx",
    "simple_history",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.nucleo",
    "apps.catalogo",
    "apps.inventario",
    "apps.pedidos",
    "apps.envios",
    "apps.tablero",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.nucleo.context_processors.contexto_tienda",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Base de datos por defecto (SQLite en local; PostgreSQL por DATABASE_URL en demo/prod)
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internacionalización y zona horaria oficial de Perú
LANGUAGE_CODE = "es-pe"
FORMAT_MODULE_PATH = ["config.formats"]
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# Archivos estáticos y multimedia
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
STATICFILES_DIRS = [
    BASE_DIR / "static",
    REPO_DIR / "03-Diseno-Tecnico" / "assets",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Pilar 2 Anti-Hacking: CORS estricto (NUNCA usar CORS_ALLOW_ALL_ORIGINS = True)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_METHODS = ["GET", "POST", "PATCH", "OPTIONS"]
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# Cabeceras de seguridad base
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Pilar 4 Anti-Hacking: Rate Limiting / Throttling en Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "120/minute",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Emuná Sport – API de Comercio Electrónico y Gestión",
    "DESCRIPTION": "API oficial de Emuná Sport (Estilo deportivo).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Variables de negocio y pre-lanzamiento
ADMIN_URL = env("ADMIN_URL")
SITE_URL = env("SITE_URL")
GA4_MEASUREMENT_ID = env("GA4_MEASUREMENT_ID")
CLOUDFLARE_BEACON_TOKEN = env("CLOUDFLARE_BEACON_TOKEN")
TURNSTILE_SITE_KEY = env("TURNSTILE_SITE_KEY")
TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY")


# Permitir nombres de índices de hasta 63 caracteres según 12-estandar-base-datos.md (PostgreSQL/SQLite)
SILENCED_SYSTEM_CHECKS = ["models.E034"]

# Tema Flat Design corporativo del panel /gestion/ (no afecta la tienda pública)
UNFOLD = UNFOLD_CONFIG_EMUNA
