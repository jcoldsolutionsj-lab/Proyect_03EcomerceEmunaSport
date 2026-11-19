"""Configuración para el entorno de demostración (Piloto en Render para Richard)."""
from .base import *  # noqa: F403
from .base import validar_variables_entorno_criticas

validar_variables_entorno_criticas(["SECRET_KEY", "ALLOWED_HOSTS"])

DEBUG = False

# Requisito #4 Antes de lanzar: Forzar HTTPS detrás del proxy de Render/Cloudflare
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
