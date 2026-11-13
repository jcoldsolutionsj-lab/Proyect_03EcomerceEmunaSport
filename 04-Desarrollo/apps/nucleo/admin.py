"""Configuración del panel administrativo para los modelos de la app núcleo."""
from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.nucleo.admin_helpers import encabezado_con_tooltip

from .models import ConfiguracionTienda, MetodoPago


@admin.register(ConfiguracionTienda)
class ConfiguracionTiendaAdmin(admin.ModelAdmin):
    """Panel de administración para el registro único de Configuración de la Tienda."""

    list_display = (
        "nombre_col",
        "whatsapp_col",
        "umbral_col",
        "marcas_col",
        "actualizacion_col",
    )
    search_fields = ("nombre", "numero_whatsapp")
    list_per_page = 15

    @admin.display(
        description=encabezado_con_tooltip(
            "Tienda", "Nombre comercial mostrado en el encabezado, catálogo y comprobantes PDF."
        ),
        ordering="nombre",
    )
    def nombre_col(self, obj: ConfiguracionTienda) -> str:
        """Retorna el nombre comercial de la tienda con tooltip de ayuda.

        Qué hace:      Devuelve obj.nombre.
        Va hacia:      Columna Tienda en ConfiguracionTiendaAdmin.
        Depende de:    obj.nombre.
        Cuándo usarla: En el listado de configuración general.
        Si no opera:   Retorna cadena vacía.
        """
        return obj.nombre

    @admin.display(
        description=encabezado_con_tooltip(
            "WhatsApp Oficial", "Número de atención al cliente usado en los botones de pedido."
        ),
        ordering="numero_whatsapp",
    )
    def whatsapp_col(self, obj: ConfiguracionTienda) -> str:
        """Retorna el número WhatsApp oficial con tooltip de ayuda.

        Qué hace:      Devuelve obj.numero_whatsapp.
        Va hacia:      Columna WhatsApp Oficial en ConfiguracionTiendaAdmin.
        Depende de:    obj.numero_whatsapp.
        Cuándo usarla: En el listado de configuración general.
        Si no opera:   Retorna cadena vacía.
        """
        return obj.numero_whatsapp

    @admin.display(
        description=encabezado_con_tooltip(
            "Umbral Stock Bajo",
            "Cantidad mínima por talla a partir de la cual el sistema dispara alerta amarilla.",
        ),
        ordering="umbral_stock_bajo",
    )
    def umbral_col(self, obj: ConfiguracionTienda) -> int:
        """Retorna el umbral de alerta de stock bajo con tooltip.

        Qué hace:      Devuelve obj.umbral_stock_bajo.
        Va hacia:      Columna Umbral Stock Bajo en ConfiguracionTiendaAdmin.
        Depende de:    obj.umbral_stock_bajo.
        Cuándo usarla: En el listado de configuración general.
        Si no opera:   Retorna 0.
        """
        return obj.umbral_stock_bajo

    @admin.display(
        description=encabezado_con_tooltip(
            "Mostrar Marcas", "Controla si se muestran etiquetas de marcas deportivas en la web."
        ),
        ordering="mostrar_marcas",
        boolean=True,
    )
    def marcas_col(self, obj: ConfiguracionTienda) -> bool:
        """Retorna si se muestran referencias de marcas en la web.

        Qué hace:      Devuelve el booleano obj.mostrar_marcas.
        Va hacia:      Columna Mostrar Marcas en ConfiguracionTiendaAdmin.
        Depende de:    obj.mostrar_marcas.
        Cuándo usarla: En el listado de configuración general.
        Si no opera:   Retorna False.
        """
        return obj.mostrar_marcas

    @admin.display(
        description=encabezado_con_tooltip(
            "Última Edición", "Fecha y hora en que se modificaron los ajustes por última vez."
        ),
        ordering="fecha_actualizacion",
    )
    def actualizacion_col(self, obj: ConfiguracionTienda) -> Any:
        """Retorna la fecha de última actualización con tooltip.

        Qué hace:      Devuelve obj.fecha_actualizacion.
        Va hacia:      Columna Última Edición en ConfiguracionTiendaAdmin.
        Depende de:    obj.fecha_actualizacion.
        Cuándo usarla: En el listado de configuración general.
        Si no opera:   Retorna None.
        """
        return obj.fecha_actualizacion

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

    list_display = (
        "tipo_col",
        "titular_col",
        "numero_col",
        "activo_col",
        "orden_col",
        "actualizacion_col",
    )
    list_filter = ("activo", "tipo")
    search_fields = ("tipo", "titular", "numero_cuenta")
    list_per_page = 15
    ordering = ("orden", "id")

    @admin.display(
        description=encabezado_con_tooltip(
            "Medio de Pago", "Tipo de medio habilitado (Yape, Plin, Efectivo o Transferencia)."
        ),
        ordering="tipo",
    )
    def tipo_col(self, obj: MetodoPago) -> str:
        """Retorna el tipo de método de pago legible.

        Qué hace:      Devuelve obj.get_tipo_display().
        Va hacia:      Columna Medio de Pago en MetodoPagoAdmin.
        Depende de:    obj.get_tipo_display.
        Cuándo usarla: En el listado de métodos de pago.
        Si no opera:   Retorna código plano.
        """
        return obj.get_tipo_display()

    @admin.display(
        description=encabezado_con_tooltip(
            "Titular", "Nombre del titular que recibe el abono en Yape/cuenta."
        ),
        ordering="titular",
    )
    def titular_col(self, obj: MetodoPago) -> str:
        """Retorna el titular de la cuenta con tooltip.

        Qué hace:      Devuelve obj.titular.
        Va hacia:      Columna Titular en MetodoPagoAdmin.
        Depende de:    obj.titular.
        Cuándo usarla: En el listado de métodos de pago.
        Si no opera:   Retorna guion si está vacío.
        """
        return obj.titular or "—"

    @admin.display(
        description=encabezado_con_tooltip(
            "Número / Cuenta", "Celular de Yape o número de cuenta mostrado al cliente."
        ),
        ordering="numero_cuenta",
    )
    def numero_col(self, obj: MetodoPago) -> str:
        """Retorna el número de celular o cuenta bancaria con tooltip.

        Qué hace:      Devuelve obj.numero_cuenta.
        Va hacia:      Columna Número / Cuenta en MetodoPagoAdmin.
        Depende de:    obj.numero_cuenta.
        Cuándo usarla: En el listado de métodos de pago.
        Si no opera:   Retorna guion si está vacío.
        """
        return obj.numero_cuenta or "—"

    @admin.display(
        description=encabezado_con_tooltip(
            "Activo", "Indica si este método está habilitado para cobros."
        ),
        ordering="activo",
        boolean=True,
    )
    def activo_col(self, obj: MetodoPago) -> bool:
        """Retorna el estado activo del método de pago.

        Qué hace:      Devuelve obj.activo.
        Va hacia:      Columna Activo en MetodoPagoAdmin.
        Depende de:    obj.activo.
        Cuándo usarla: En el listado de métodos de pago.
        Si no opera:   Retorna False.
        """
        return obj.activo

    @admin.display(
        description=encabezado_con_tooltip(
            "Orden", "Prioridad visual en checkout y panel (menor número aparece primero)."
        ),
        ordering="orden",
    )
    def orden_col(self, obj: MetodoPago) -> int:
        """Retorna el orden de prioridad con tooltip.

        Qué hace:      Devuelve obj.orden.
        Va hacia:      Columna Orden en MetodoPagoAdmin.
        Depende de:    obj.orden.
        Cuándo usarla: En el listado de métodos de pago.
        Si no opera:   Retorna 0.
        """
        return obj.orden

    @admin.display(
        description=encabezado_con_tooltip(
            "Actualizado", "Última fecha y hora en que se editó este método de pago."
        ),
        ordering="fecha_actualizacion",
    )
    def actualizacion_col(self, obj: MetodoPago) -> Any:
        """Retorna la fecha de última actualización con tooltip.

        Qué hace:      Devuelve obj.fecha_actualizacion.
        Va hacia:      Columna Actualizado en MetodoPagoAdmin.
        Depende de:    obj.fecha_actualizacion.
        Cuándo usarla: En el listado de métodos de pago.
        Si no opera:   Retorna None.
        """
        return obj.fecha_actualizacion
