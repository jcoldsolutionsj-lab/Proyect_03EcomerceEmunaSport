"""Configuración para desarrollo local y pruebas automatizadas en la máquina de Jonathan."""
import os
import sys

from .base import *  # noqa: F403
from .base import BASE_DIR

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

# En local no forzamos redirección SSL para poder probar en http://127.0.0.1:8000
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Durante pytest usar SQLite aislado por defecto para no exigir permiso CREATEDB en Render remoto
if "pytest" in sys.modules and os.environ.get("PYTEST_USE_POSTGRES") != "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
