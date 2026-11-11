"""Configuración del panel administrativo para Pedidos, Ítems y Bitácora de Estados."""
from django.contrib import admin
from django.http import HttpRequest
from simple_history.admin import SimpleHistoryAdmin

from .models import ItemPedido, Pedido, RegistroEstadoPedido


class ItemPedidoInline(admin.TabularInline):
    """Muestra las líneas de camisetas compradas dentro de la ficha del pedido."""

    model = ItemPedido
    extra = 0
    readonly_fields = (
        "variante",
        "nombre_producto",
        "sku",
        "talla",
        "color",
        "precio_unidad",
        "cantidad",
        "subtotal",
    )
    can_delete = False


class RegistroEstadoPedidoInline(admin.TabularInline):
    """Muestra la bitácora inmutable de cambios de estado del pedido."""

    model = RegistroEstadoPedido
    extra = 0
    readonly_fields = (
        "estado_anterior",
        "estado_nuevo",
        "cambiado_por",
        "nota",
        "fecha_creacion",
    )
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: Pedido | None = None) -> bool:
        """Impide agregar registros manuales en la bitácora fuera de los servicios.

        Qué hace:      Deshabilita el botón de añadir filas manuales en el inline.
        Va hacia:      Retorna False siempre para preservar la integridad de TBL_LPEDIDO_ESTADO.
        Depende de:    django.contrib.admin.TabularInline.
        Cuándo usarla: Al renderizar el detalle de un Pedido en el admin.
        Si no opera:   No aplica.
        """
        return False


@admin.register(Pedido)
class PedidoAdmin(SimpleHistoryAdmin):
    """Administración de pedidos web y ventas presenciales para Richard y Jonathan."""

    list_display = (
        "codigo",
        "estado",
        "tipo_entrega",
        "cliente_nombre",
        "cliente_telefono",
        "subtotal",
        "costo_envio",
        "total",
        "fecha_creacion",
    )
    list_filter = ("estado", "tipo_entrega", "origen", "agencia", "fecha_creacion")
    search_fields = ("codigo", "cliente_nombre", "cliente_telefono", "cliente_dni")
    readonly_fields = (
        "codigo",
        "subtotal",
        "total",
        "fecha_cotizado",
        "fecha_pagado",
        "fecha_enviado",
        "fecha_entregado",
        "fecha_cierre",
        "fecha_creacion",
        "fecha_actualizacion",
    )
    inlines = [ItemPedidoInline, RegistroEstadoPedidoInline]
