"""Configuración para desarrollo local y pruebas automatizadas en la máquina de Jonathan."""
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

# En local no forzamos redirección SSL para poder probar en http://127.0.0.1:8000
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
