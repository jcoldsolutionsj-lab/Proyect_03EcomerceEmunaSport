"""Configuración de la app catálogo."""
from django.apps import AppConfig


class CatalogoConfig(AppConfig):
    """Configuración de la app catálogo de Emuná Sport."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalogo"
    verbose_name = "Catálogo de Camisetas"
