"""Configuración de la app catálogo."""
from django.apps import AppConfig


class CatalogoConfig(AppConfig):
    """Configuración de la app catálogo de Emuná Sport."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalogo"
    verbose_name = "Catálogo de Camisetas"

    def ready(self) -> None:
        """Registra señales de invalidación de caché cuando arranca la aplicación catálogo.

        Qué hace:      Importa apps.catalogo.signals al iniciar Django.
        Va hacia:      Activa la invalidación automática al guardar productos, equipos o variantes.
        Depende de:    apps.catalogo.signals.
        Cuándo usarla: Automáticamente durante el arranque de Django.
        Si no opera:   No invalida la caché en memoria al cambiar el inventario.
        """
        from . import signals  # noqa: F401
