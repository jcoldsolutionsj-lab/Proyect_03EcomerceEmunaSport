"""Configuración del panel administrativo para los modelos de la app núcleo."""
from django.contrib import admin
from django.http import HttpRequest

from .models import ConfiguracionTienda, MetodoPago


@admin.register(ConfiguracionTienda)
class ConfiguracionTiendaAdmin(admin.ModelAdmin):
    """Panel de administración para el registro único de Configuración de la Tienda."""

    list_display = (
        "nombre",
        "numero_whatsapp",
        "umbral_stock_bajo",
        "mostrar_marcas",
        "fecha_actualizacion",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Impide agregar un segundo registro si ya existe la configuración de la tienda.

        Qué hace:      Verifica si ya hay una fila en TBL_RCONFIGURACION_TIENDA.
        Va hacia:      Retorna False si ya existe, ocultando el botón 'Añadir' en el admin.
        Depende de:    ConfiguracionTienda.objects.exists().
        Cuándo usarla: Automáticamente por el admin de Django al renderizar las vistas.
        Si no opera:   Retorna False por seguridad si ocurre algún error de consulta.
        """
        if ConfiguracionTienda.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(
        self, request: HttpRequest, obj: ConfiguracionTienda | None = None
    ) -> bool:
        """Impide borrar el registro único de configuración de la tienda desde el panel.

        Qué hace:      Bloquea la acción de eliminar sobre TBL_RCONFIGURACION_TIENDA.
        Va hacia:      Retorna siempre False para proteger los ajustes globales.
        Depende de:    admin.ModelAdmin.
        Cuándo usarla: Automáticamente por el admin de Django.
        Si no opera:   No aplica (siempre devuelve False).
        """
        return False


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    """Panel de administración para gestionar métodos de pago (Yape, Plin, Efectivo)."""

    list_display = ("tipo", "titular", "numero_cuenta", "activo", "orden", "fecha_actualizacion")
    list_filter = ("activo", "tipo")
    ordering = ("orden", "id")
