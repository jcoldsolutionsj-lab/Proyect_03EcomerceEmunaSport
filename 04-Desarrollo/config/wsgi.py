"""Configuración WSGI para el proyecto Emuná Sport (usada por Gunicorn en Render)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
