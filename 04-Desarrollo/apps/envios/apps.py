"""Configuración de la app envíos."""
from django.apps import AppConfig


class EnviosConfig(AppConfig):
    """Configuración de la app envíos de Emuná Sport."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.envios"
    verbose_name = "Envíos por Agencia"
