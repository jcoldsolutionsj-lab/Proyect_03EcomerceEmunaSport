"""Configuración de la aplicación núcleo para el registro de Django."""
from django.apps import AppConfig


class NucleoConfig(AppConfig):
    """Configuración de la app núcleo de Emuná Sport."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.nucleo"
    verbose_name = "Núcleo y Configuración"
