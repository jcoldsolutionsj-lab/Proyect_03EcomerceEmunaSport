"""Configuración blindada para Producción oficial de Emuná Sport."""
from .base import *  # noqa: F403
from .base import env, validar_variables_entorno_criticas

validar_variables_entorno_criticas(
    [
        "SECRET_KEY",
        "DATABASE_URL",
        "ALLOWED_HOSTS",
        "CSRF_TRUSTED_ORIGINS",
        "TURNSTILE_SECRET_KEY",
    ]
)

if env.bool("DEBUG", default=False):
    raise RuntimeError("Seguridad crítica: DEBUG no puede estar activo en producción.")

DEBUG = False

# Requisito #4 Antes de lanzar: HTTPS obligatorio y HSTS por 1 año
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
