"""Configuración de la app pedidos."""
from django.apps import AppConfig


class PedidosConfig(AppConfig):
    """Configuración de la app pedidos de Emuná Sport."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pedidos"
    verbose_name = "Pedidos y Ventas"
