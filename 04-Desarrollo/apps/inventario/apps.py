"""Configuración de la app inventario."""
from django.apps import AppConfig


class InventarioConfig(AppConfig):
    """Configuración de la app inventario de Emuná Sport."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inventario"
    verbose_name = "Inventario y Movimientos de Stock"
