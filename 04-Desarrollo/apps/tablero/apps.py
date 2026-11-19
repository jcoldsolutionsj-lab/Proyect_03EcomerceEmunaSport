"""Configuración de la app tablero."""
from django.apps import AppConfig


class TableroConfig(AppConfig):
    """Configuración de la app tablero de Emuná Sport."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tablero"
    verbose_name = "Tablero y Alertas"
