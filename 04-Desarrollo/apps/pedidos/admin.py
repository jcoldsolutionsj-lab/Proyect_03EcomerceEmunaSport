"""Configuración del panel administrativo para Pedidos, Envíos, Ítems y Bitácora de Estados."""
from decimal import Decimal, InvalidOperation
from typing import Any

from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.views.decorators.http import require_POST
from simple_history.admin import SimpleHistoryAdmin

from apps.catalogo.models import Variante
from apps.nucleo.admin_helpers import encabezado_con_tooltip
from apps.nucleo.excepciones import ErrorDominioEmuna

from .models import (
    AgenciaEnvio,
    Envio,
    EstadoPedido,
    ItemPedido,
    Pedido,
    QuienPagaFlete,
    RegistroEstadoPedido,
    TipoEntrega,
)
from .servicios import (
    cambiar_estado,
    cancelar_o_rechazar,
    confirmar_pago,
    confirmar_pago_y_entregar,
    construir_enlace_whatsapp_notificacion_cliente,
    cotizar_envio,
    registrar_envio_agencia,
    registrar_venta_presencial,
)


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

    def has_add_permission(self, request: HttpRequest, obj: Pedido | None = None) -> bool:
        """Impide agregar ítems manuales sueltos sobre un pedido ya creado.

        Qué hace:      Deshabilita filas nuevas manuales en ItemPedidoInline.
        Va hacia:      Protege la consistencia entre subtotal, stock e ítems del pedido.
        Depende de:    django.contrib.admin.TabularInline.
        Cuándo usarla: Al visualizar un Pedido en el panel administrativo.
        Si no opera:   No aplica.
        """
        return False


class EnvioInline(admin.StackedInline):
    """Muestra el despacho en agencia (Shalom/Olva) dentro de la ficha del pedido."""

    model = Envio
    extra = 0
    fields = (
        "agencia",
        "numero_orden_agencia",
        "clave_recojo",
        "costo_flete",
        "quien_paga",
        "cobrado",
        "fecha_despacho",
        "imagen_boleta",
        "enlace_boleta",
        "notas",
    )
    readonly_fields = ("enlace_boleta",)

    def has_add_permission(self, request: HttpRequest, obj: Pedido | None = None) -> bool:
        """Exige usar el botón 'Registrar Despacho en Agencia' para crear un envío.

        Qué hace:      Desactiva la creación directa en el inline sin pasar por el servicio.
        Va hacia:      Garantiza que todo envío registrado dispare PAGADO -> ENVIADO y bitácora.
        Depende de:    django.contrib.admin.StackedInline.
        Cuándo usarla: Al renderizar la ficha de Pedido en el admin de Django.
        Si no opera:   No aplica.
        """
        return False

    def enlace_boleta(self, obj: Envio | None) -> str:
        """Genera un enlace seguro para visualizar la boleta de despacho privada.

        Qué hace:      Retorna botón HTML que apunta a la vista autenticada ver_boleta_privada.
        Va hacia:      Renderiza etiqueta <a> segura dentro del formulario administrativo.
        Depende de:    Atributo imagen_boleta e ID de la instancia Envio.
        Cuándo usarla: Al visualizar los datos del envío registrado en el panel de Richard.
        Si no opera:   Retorna 'Sin boleta adjunta' si el envío no tiene foto aún.
        """
        if obj and obj.pk and obj.imagen_boleta:
            url = reverse("pedidos:ver_boleta_privada", args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" style="background:#0F172A;color:#10B981;font-weight:bold;padding:5px 10px;border-radius:4px;text-decoration:none;">📄 Ver boleta privada</a>',
                url,
            )
        return "Sin boleta adjunta"

    enlace_boleta.short_description = "Comprobante Privado"


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


@admin.register(Envio)
class EnvioAdmin(admin.ModelAdmin):
    """Administración y seguimiento de despachos por agencias de transporte (Shalom / Olva)."""

    list_display = (
        "pedido_col",
        "agencia_col",
        "orden_col",
        "clave_col",
        "quien_paga_col",
        "cobrado_col",
        "flete_col",
        "despacho_col",
        "ver_boleta_link",
    )
    list_filter = ("agencia", "quien_paga", "cobrado", "fecha_despacho")
    search_fields = ("numero_orden_agencia", "pedido__codigo", "pedido__cliente_nombre")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion", "ver_boleta_link")

    @admin.display(
        description=encabezado_con_tooltip("Pedido", "Código del pedido vinculado a este envío."),
        ordering="pedido__codigo",
    )
    def pedido_col(self, obj: Envio) -> Pedido:
        """Retorna el pedido vinculado al envío con tooltip explicativo.

        Qué hace:      Devuelve obj.pedido.
        Va hacia:      Columna Pedido en EnvioAdmin.
        Depende de:    obj.pedido.
        Cuándo usarla: En el listado de envíos por agencia.
        Si no opera:   No aplica.
        """
        return obj.pedido

    @admin.display(
        description=encabezado_con_tooltip("Agencia", "Empresa de transporte (Shalom, Olva u Otra)."),
        ordering="agencia",
    )
    def agencia_col(self, obj: Envio) -> str:
        """Retorna el nombre legible de la agencia de transporte.

        Qué hace:      Devuelve obj.get_agencia_display().
        Va hacia:      Columna Agencia en EnvioAdmin.
        Depende de:    obj.get_agencia_display.
        Cuándo usarla: En el listado de envíos.
        Si no opera:   Retorna código plano.
        """
        return obj.get_agencia_display()

    @admin.display(
        description=encabezado_con_tooltip(
            "N° Orden / Guía", "Número de seguimiento impreso en el ticket de la agencia."
        ),
        ordering="numero_orden_agencia",
    )
    def orden_col(self, obj: Envio) -> str:
        """Retorna el número de orden o guía de agencia.

        Qué hace:      Formatea en negrita obj.numero_orden_agencia.
        Va hacia:      Columna N° Orden en EnvioAdmin.
        Depende de:    obj.numero_orden_agencia.
        Cuándo usarla: En el listado de envíos.
        Si no opera:   Retorna cadena vacía.
        """
        return format_html("<code>{}</code>", obj.numero_orden_agencia)

    @admin.display(
        description=encabezado_con_tooltip(
            "Clave (4 díg.)",
            "Clave privada de recojo en agencia. NUNCA se expone en la web pública.",
        ),
        ordering="clave_recojo",
    )
    def clave_col(self, obj: Envio) -> str:
        """Muestra la clave secreta de 4 dígitos solo para Richard en el admin.

        Qué hace:      Formatea obj.clave_recojo en distintivo ámbar privado.
        Va hacia:      Columna Clave en EnvioAdmin.
        Depende de:    obj.clave_recojo.
        Cuándo usarla: Cuando Richard necesita consultar o reenviar la clave al cliente.
        Si no opera:   Retorna '----'.
        """
        return format_html(
            '<span style="background:#FEF3C7;color:#92400E;padding:2px 6px;border-radius:4px;font-family:monospace;font-weight:800;">🔒 {}</span>',
            obj.clave_recojo,
        )

    @admin.display(
        description=encabezado_con_tooltip(
            "Quién paga", "Indica si el cliente pagó por adelantado, paga en destino o adelantó Richard."
        ),
        ordering="quien_paga",
    )
    def quien_paga_col(self, obj: Envio) -> str:
        """Muestra quién asume el pago del flete de la agencia.

        Qué hace:      Retorna obj.get_quien_paga_display().
        Va hacia:      Columna Quién paga en EnvioAdmin.
        Depende de:    obj.get_quien_paga_display.
        Cuándo usarla: En el listado de envíos.
        Si no opera:   Retorna valor bruto.
        """
        return obj.get_quien_paga_display()

    @admin.display(
        description=encabezado_con_tooltip(
            "Cobrado", "Marca verde si el flete ya fue cobrado/liquidado con el cliente."
        ),
        ordering="cobrado",
        boolean=True,
    )
    def cobrado_col(self, obj: Envio) -> bool:
        """Muestra si el flete ya fue cobrado al cliente.

        Qué hace:      Retorna booleano obj.cobrado.
        Va hacia:      Columna Cobrado en EnvioAdmin.
        Depende de:    obj.cobrado.
        Cuándo usarla: En el listado de envíos.
        Si no opera:   Retorna False.
        """
        return obj.cobrado

    @admin.display(
        description=encabezado_con_tooltip(
            "Flete real", "Costo real pagado en ventanilla de Shalom u Olva (en soles)."
        ),
        ordering="costo_flete",
    )
    def flete_col(self, obj: Envio) -> str:
        """Muestra el costo del flete formateado en soles.

        Qué hace:      Formatea S/ {costo_flete}.
        Va hacia:      Columna Flete real en EnvioAdmin.
        Depende de:    obj.costo_flete.
        Cuándo usarla: En el listado de envíos.
        Si no opera:   Retorna S/ 0.00.
        """
        return f"S/ {obj.costo_flete:.2f}"

    @admin.display(
        description=encabezado_con_tooltip(
            "Despacho", "Fecha y hora en que se dejó el paquete en la agencia."
        ),
        ordering="fecha_despacho",
    )
    def despacho_col(self, obj: Envio) -> Any:
        """Retorna fecha de despacho con tooltip explicativo.

        Qué hace:      Devuelve obj.fecha_despacho.
        Va hacia:      Columna Despacho en EnvioAdmin.
        Depende de:    obj.fecha_despacho.
        Cuándo usarla: En el listado de envíos.
        Si no opera:   Retorna None.
        """
        return obj.fecha_despacho

    @admin.display(
        description=encabezado_con_tooltip(
            "Boleta privada",
            "Archivo de guía adjunto. Solo accesible con sesión de Richard o staff (403 al público).",
        ),
    )
    def ver_boleta_link(self, obj: Envio) -> str:
        """Retorna enlace HTML al archivo privado de la boleta de agencia.

        Qué hace:      Construye el enlace a la vista privada de descarga de boleta.
        Va hacia:      Columna en el changelist y campo en el formulario de Envio.
        Depende de:    obj.imagen_boleta e ID de obj.
        Cuándo usarla: Al auditar o consultar los despachos por agencia.
        Si no opera:   Muestra 'Sin archivo' si aún no se adjuntó la foto.
        """
        if obj.pk and obj.imagen_boleta:
            url = reverse("pedidos:ver_boleta_privada", args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" style="background:#0F172A;color:#10B981;font-weight:bold;padding:4px 8px;border-radius:4px;text-decoration:none;">📄 Ver boleta</a>',
                url,
            )
        return "Sin archivo"


@admin.register(Pedido)
class PedidoAdmin(SimpleHistoryAdmin):
    """Administración de pedidos web y ventas presenciales para Richard y Jonathan."""

    change_list_template = "admin/pedidos/pedido/change_list.html"
    change_form_template = "admin/pedidos/pedido/change_form.html"

    list_display = (
        "codigo_col",
        "estado_col",
        "entrega_col",
        "cliente_col",
        "telefono_col",
        "subtotal_col",
        "envio_col",
        "total_col",
        "notificacion_whatsapp",
        "fecha_col",
    )
    list_filter = ("estado", "tipo_entrega", "origen", "agencia", "fecha_creacion")
    search_fields = ("codigo", "cliente_nombre", "cliente_telefono", "cliente_dni")
    readonly_fields = (
        "codigo",
        "estado",
        "subtotal",
        "costo_envio",
        "total",
        "fecha_cotizado",
        "fecha_pagado",
        "fecha_enviado",
        "fecha_entregado",
        "fecha_cierre",
        "fecha_creacion",
        "fecha_actualizacion",
        "notificacion_whatsapp",
    )
    inlines = [ItemPedidoInline, EnvioInline, RegistroEstadoPedidoInline]
    actions = [
        "accion_confirmar_pago",
        "accion_confirmar_pago_y_entregar",
        "accion_marcar_entregado",
        "accion_cancelar_pedido",
    ]

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        """Inyecta contexto del flujo de gestión y enlaces WhatsApp en la ficha del pedido.

        Qué hace:      Calcula URL pública, enlaces WhatsApp y opciones para el panel contextual.
        Va hacia:      Renderiza templates/admin/pedidos/pedido/change_form.html.
        Depende de:    construir_enlace_whatsapp_notificacion_cliente y AgenciaEnvio/QuienPagaFlete.
        Cuándo usarla: Al abrir un pedido individual en el panel administrativo.
        Si no opera:   Delega normalmente a SimpleHistoryAdmin.change_view().
        """
        contexto = dict(extra_context or {})
        pedido = self.get_object(request, object_id)
        if pedido is not None:
            url_publica = request.build_absolute_uri(
                reverse("pedidos:detalle_pedido", args=[pedido.codigo])
            )
            envio_actual = getattr(pedido, "envio", None)
            url_boleta = (
                reverse("pedidos:ver_boleta_privada", args=[envio_actual.pk])
                if envio_actual and envio_actual.imagen_boleta
                else ""
            )
            contexto.update(
                {
                    "url_publica_pedido": url_publica,
                    "url_whatsapp_cotizado": construir_enlace_whatsapp_notificacion_cliente(
                        pedido=pedido,
                        tipo_notificacion="COTIZADO",
                        url_publica_pedido=url_publica,
                    ),
                    "url_whatsapp_enviado": construir_enlace_whatsapp_notificacion_cliente(
                        pedido=pedido,
                        tipo_notificacion="ENVIADO",
                        url_publica_pedido=url_publica,
                    ),
                    "url_whatsapp_punto": construir_enlace_whatsapp_notificacion_cliente(
                        pedido=pedido,
                        tipo_notificacion="PUNTO_ENCUENTRO",
                        url_publica_pedido=url_publica,
                    ),
                    "url_whatsapp_general": construir_enlace_whatsapp_notificacion_cliente(
                        pedido=pedido,
                        tipo_notificacion="GENERAL",
                        url_publica_pedido=url_publica,
                    ),
                    "metodos_pago_choices": [
                        ("YAPE", "🟣 Yape"),
                        ("EFECTIVO", "💵 Efectivo"),
                        ("PLIN", "🔵 Plin"),
                        ("TRANSFERENCIA", "🏦 Transferencia BCP / Interbank"),
                    ],
                    "agencias_choices": AgenciaEnvio.choices,
                    "quien_paga_choices": QuienPagaFlete.choices,
                    "envio_actual": envio_actual,
                    "url_boleta_privada": url_boleta,
                    "costo_envio_dot": str(pedido.costo_envio or Decimal("0.00")),
                }
            )
        return super().change_view(request, object_id, form_url, extra_context=contexto)

    @admin.display(
        description=encabezado_con_tooltip(
            "Código", "Código público único no adivinable del pedido (ej. EMU-XXXXXX)."
        ),
        ordering="codigo",
    )
    def codigo_col(self, obj: Pedido) -> str:
        """Muestra el código del pedido en negrita.

        Qué hace:      Resalta obj.codigo.
        Va hacia:      Columna Código en PedidoAdmin.
        Depende de:    obj.codigo.
        Cuándo usarla: En la tabla principal de pedidos.
        Si no opera:   Retorna cadena vacía.
        """
        return format_html("<strong>{}</strong>", obj.codigo)

    @admin.display(
        description=encabezado_con_tooltip(
            "Estado",
            "Ciclo de vida: Nuevo -> Cotizado -> Pagado (descuenta stock) -> Enviado -> Entregado.",
        ),
        ordering="estado",
    )
    def estado_col(self, obj: Pedido) -> str:
        """Muestra el estado actual del pedido con código de color legible.

        Qué hace:      Asigna color distinto a cada estado del flujo para lectura rápida.
        Va hacia:      Columna Estado en PedidoAdmin.
        Depende de:    obj.estado y get_estado_display().
        Cuándo usarla: En la lista de pedidos de Richard.
        Si no opera:   Retorna texto plano del estado.
        """
        estilos = {
            EstadoPedido.NUEVO: ("#1D4ED8", "#DBEAFE"),
            EstadoPedido.COTIZADO: ("#B45309", "#FEF3C7"),
            EstadoPedido.PAGADO: ("#6D28D9", "#EDE9FE"),
            EstadoPedido.ENVIADO: ("#0369A1", "#E0F2FE"),
            EstadoPedido.ENTREGADO: ("#047857", "#D1FAE5"),
            EstadoPedido.CANCELADO: ("#B91C1C", "#FEE2E2"),
            EstadoPedido.RECHAZADO: ("#991B1B", "#FEE2E2"),
        }
        fg, bg = estilos.get(obj.estado, ("#334155", "#F1F5F9"))
        return format_html(
            '<span style="color:{};background:{};padding:2px 8px;border-radius:999px;font-weight:800;font-size:11px;white-space:nowrap;">{}</span>',
            fg,
            bg,
            obj.get_estado_display(),
        )

    @admin.display(
        description=encabezado_con_tooltip(
            "Modalidad", "Agencia provincia, Punto de Encuentro Lima, Delivery o Recojo."
        ),
        ordering="tipo_entrega",
    )
    def entrega_col(self, obj: Pedido) -> str:
        """Retorna la modalidad de entrega del pedido.

        Qué hace:      Devuelve obj.get_tipo_entrega_display().
        Va hacia:      Columna Modalidad en PedidoAdmin.
        Depende de:    obj.get_tipo_entrega_display.
        Cuándo usarla: En la tabla de pedidos.
        Si no opera:   Retorna valor bruto.
        """
        return obj.get_tipo_entrega_display()

    @admin.display(
        description=encabezado_con_tooltip("Cliente", "Nombre del cliente registrado."),
        ordering="cliente_nombre",
    )
    def cliente_col(self, obj: Pedido) -> str:
        """Retorna el nombre del cliente.

        Qué hace:      Devuelve obj.cliente_nombre o 'Cliente presencial'.
        Va hacia:      Columna Cliente en PedidoAdmin.
        Depende de:    obj.cliente_nombre.
        Cuándo usarla: En la tabla de pedidos.
        Si no opera:   Retorna 'Cliente presencial'.
        """
        return obj.cliente_nombre or "Cliente presencial"

    @admin.display(
        description=encabezado_con_tooltip("Celular", "Número WhatsApp de contacto del cliente."),
        ordering="cliente_telefono",
    )
    def telefono_col(self, obj: Pedido) -> str:
        """Retorna el teléfono del cliente o guion si no tiene.

        Qué hace:      Devuelve obj.cliente_telefono o '—'.
        Va hacia:      Columna Celular en PedidoAdmin.
        Depende de:    obj.cliente_telefono.
        Cuándo usarla: En la tabla de pedidos.
        Si no opera:   Retorna '—'.
        """
        return obj.cliente_telefono or "—"

    @admin.display(
        description=encabezado_con_tooltip(
            "Camisetas", "Subtotal de prendas aplicando descuento mayorista si lleva 3+ iguales."
        ),
        ordering="subtotal",
    )
    def subtotal_col(self, obj: Pedido) -> str:
        """Retorna el subtotal de camisetas formateado en soles.

        Qué hace:      Formatea S/ {subtotal}.
        Va hacia:      Columna Camisetas en PedidoAdmin.
        Depende de:    obj.subtotal.
        Cuándo usarla: En la tabla de pedidos.
        Si no opera:   Retorna S/ 0.00.
        """
        return f"S/ {obj.subtotal:.2f}"

    @admin.display(
        description=encabezado_con_tooltip(
            "Envío", "Costo del flete o delivery (S/ 0.00 en Punto de Encuentro)."
        ),
        ordering="costo_envio",
    )
    def envio_col(self, obj: Pedido) -> str:
        """Retorna el costo de envío formateado o 'Por cotizar'.

        Qué hace:      Muestra 'Por cotizar' si es None, o el monto en soles.
        Va hacia:      Columna Envío en PedidoAdmin.
        Depende de:    obj.costo_envio.
        Cuándo usarla: En la tabla de pedidos.
        Si no opera:   Retorna 'Por cotizar'.
        """
        if obj.costo_envio is None:
            return format_html('<span style="color:#64748B;font-style:italic;">Por cotizar</span>')
        return f"S/ {obj.costo_envio:.2f}"

    @admin.display(
        description=encabezado_con_tooltip(
            "Total", "Monto total a cobrar al cliente (Camisetas + Envío)."
        ),
        ordering="total",
    )
    def total_col(self, obj: Pedido) -> str:
        """Retorna el total final del pedido en negrita.

        Qué hace:      Formatea S/ {total}.
        Va hacia:      Columna Total en PedidoAdmin.
        Depende de:    obj.total.
        Cuándo usarla: En la tabla de pedidos.
        Si no opera:   Retorna S/ 0.00.
        """
        return format_html("<strong>S/ {}</strong>", f"{obj.total:.2f}")

    @admin.display(
        description=encabezado_con_tooltip("Registrado", "Fecha y hora de creación del pedido."),
        ordering="fecha_creacion",
    )
    def fecha_col(self, obj: Pedido) -> Any:
        """Retorna la fecha de creación del pedido.

        Qué hace:      Devuelve obj.fecha_creacion.
        Va hacia:      Columna Registrado en PedidoAdmin.
        Depende de:    obj.fecha_creacion.
        Cuándo usarla: En la tabla de pedidos.
        Si no opera:   Retorna None.
        """
        return obj.fecha_creacion

    @admin.display(
        description=encabezado_con_tooltip(
            "Avisar por WhatsApp",
            "Abre WhatsApp con el mensaje prellenado según el estado (cotización, guía+clave o coordinación).",
        ),
    )
    def notificacion_whatsapp(self, obj: Pedido) -> str:
        """Construye un botón dinámico con enlace directo a WhatsApp para notificar al cliente.

        Qué hace:      Determina el estado del pedido y construye el mensaje prellenado en WhatsApp.
        Va hacia:      Abre api.whatsapp.com en una nueva pestaña con el texto formateado.
        Depende de:    construir_enlace_whatsapp_notificacion_cliente y estado del pedido.
        Cuándo usarla: En la tabla changelist para que Richard avise con 1 solo clic.
        Si no opera:   Muestra botón genérico de contacto si no tiene estado de flujo específico.
        """
        base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
        url_pedido = f"{base_url}{reverse('pedidos:detalle_pedido', args=[obj.codigo])}"
        if obj.estado == EstadoPedido.COTIZADO:
            tipo = "COTIZADO"
            texto = "💬 Avisar Cotización"
            color = "#10B981"
        elif obj.estado == EstadoPedido.ENVIADO:
            tipo = "ENVIADO"
            texto = "🚚 Enviar Guía"
            color = "#0284C7"
        elif obj.tipo_entrega == TipoEntrega.PUNTO_ENCUENTRO and obj.estado in (
            EstadoPedido.COTIZADO,
            EstadoPedido.NUEVO,
        ):
            tipo = "PUNTO_ENCUENTRO"
            texto = "📍 Coordinar Punto"
            color = "#D97706"
        else:
            tipo = "GENERAL"
            texto = "💬 WhatsApp"
            color = "#475569"

        enlace = construir_enlace_whatsapp_notificacion_cliente(
            pedido=obj,
            tipo_notificacion=tipo,
            url_publica_pedido=url_pedido,
        )
        return format_html(
            '<a href="{}" target="_blank" style="background:{};color:#FFFFFF;font-weight:bold;padding:4px 8px;border-radius:4px;text-decoration:none;font-size:12px;white-space:nowrap;">{}</a>',
            enlace,
            color,
            texto,
        )



    @admin.action(description="🟣 Confirmar Pago (Yape/Transferencia) y descontar stock")
    def accion_confirmar_pago(self, request: HttpRequest, queryset: QuerySet[Pedido]) -> None:
        """Confirma el pago recibido en pedidos cotizados y descuenta el inventario de inmediato.

        Qué hace:      Ejecuta confirmar_pago() en transacción atómica con bloqueo select_for_update().
        Va hacia:      Actualiza estado a PAGADO y crea movimientos VENTA en TBL_TMOVIMIENTO_STOCK.
        Depende de:    confirmar_pago y queryset seleccionado por Richard.
        Cuándo usarla: Cuando Richard verifica el ingreso de dinero en su aplicación de Yape o banco.
        Si no opera:   Emite mensaje de error sin descontar inventario si el stock es insuficiente.
        """
        exitos = 0
        for ped in queryset:
            if ped.estado != EstadoPedido.COTIZADO:
                self.message_user(
                    request,
                    f"El pedido {ped.codigo} no está en estado COTIZADO (estado actual: {ped.estado}).",
                    level=messages.WARNING,
                )
                continue
            try:
                confirmar_pago(
                    pedido=ped,
                    metodo_pago=ped.metodo_pago or "YAPE",
                    usuario=request.user,
                    nota="Pago confirmado por Richard desde panel de administración.",
                )
                exitos += 1
            except ErrorDominioEmuna as exc:
                self.message_user(
                    request,
                    f"Error en pedido {ped.codigo}: {exc}",
                    level=messages.ERROR,
                )
        if exitos:
            self.message_user(
                request,
                f"Se confirmaron los pagos y se descontó el stock de {exitos} pedido(s).",
                level=messages.SUCCESS,
            )

    @admin.action(description="⚡ Confirmar Pago y Entrega en Punto de Encuentro (1 solo paso)")
    def accion_confirmar_pago_y_entregar(
        self, request: HttpRequest, queryset: QuerySet[Pedido]
    ) -> None:
        """Ejecuta el flujo rápido de Lima pasando directo de COTIZADO a PAGADO y ENTREGADO.

        Qué hace:      Ejecuta confirmar_pago_y_entregar() descontando stock y cerrando el ciclo.
        Va hacia:      Genera ambos registros en TBL_LPEDIDO_ESTADO y deja el pedido en ENTREGADO.
        Depende de:    confirmar_pago_y_entregar y permisos de usuario.
        Cuándo usarla: Al concretar la entrega mano a mano en estaciones del tren o centros comerciales.
        Si no opera:   Notifica error si el pedido no estaba en COTIZADO o faltó stock.
        """
        exitos = 0
        for ped in queryset:
            if ped.estado != EstadoPedido.COTIZADO:
                self.message_user(
                    request,
                    f"El pedido {ped.codigo} debe estar en COTIZADO para entrega rápida.",
                    level=messages.WARNING,
                )
                continue
            try:
                confirmar_pago_y_entregar(
                    pedido=ped,
                    metodo_pago=ped.metodo_pago or "YAPE",
                    usuario=request.user,
                    nota=f"Entrega presencial en {ped.punto_encuentro or 'Punto de encuentro'}",
                )
                exitos += 1
            except ErrorDominioEmuna as exc:
                self.message_user(
                    request,
                    f"Error en pedido {ped.codigo}: {exc}",
                    level=messages.ERROR,
                )
        if exitos:
            self.message_user(
                request,
                f"Se completó la entrega rápida de {exitos} pedido(s) en Lima.",
                level=messages.SUCCESS,
            )

    @admin.action(description="📦 Marcar como ENTREGADO al cliente")
    def accion_marcar_entregado(self, request: HttpRequest, queryset: QuerySet[Pedido]) -> None:
        """Marca como entregado un pedido que ya se encontraba pagado o enviado por agencia.

        Qué hace:      Invoca cambiar_estado(pedido, ENTREGADO) registrando la fecha de entrega.
        Va hacia:      Actualiza estado en TBL_TPEDIDO y añade línea a la bitácora inmutable.
        Depende de:    cambiar_estado y permisos de usuario.
        Cuándo usarla: Cuando el cliente de provincia retira su paquete de Shalom/Olva.
        Si no opera:   Notifica mensaje de error si la transición no está permitida en el flujo.
        """
        exitos = 0
        for ped in queryset:
            try:
                cambiar_estado(
                    pedido=ped,
                    nuevo_estado=EstadoPedido.ENTREGADO,
                    usuario=request.user,
                    nota="Entrega final confirmada desde panel de administración.",
                )
                exitos += 1
            except ErrorDominioEmuna as exc:
                self.message_user(
                    request,
                    f"No se pudo marcar entregado {ped.codigo}: {exc}",
                    level=messages.ERROR,
                )
        if exitos:
            self.message_user(
                request,
                f"Se marcaron como entregados {exitos} pedido(s).",
                level=messages.SUCCESS,
            )

    @admin.action(description="❌ Cancelar Pedido (repone stock si estaba pagado)")
    def accion_cancelar_pedido(self, request: HttpRequest, queryset: QuerySet[Pedido]) -> None:
        """Cancela pedidos y devuelve automáticamente las prendas al inventario si ya estaban pagadas.

        Qué hace:      Ejecuta cancelar_o_rechazar() creando movimientos DEVOLUCION si aplica.
        Va hacia:      Actualiza estado a CANCELADO e incrementa cantidad_stock en variantes.
        Depende de:    cancelar_o_rechazar y permisos de usuario.
        Cuándo usarla: Por desistimiento del cliente o solicitud de anulación formal.
        Si no opera:   Notifica mensaje descriptivo del fallo si el pedido ya estaba cerrado.
        """
        exitos = 0
        for ped in queryset:
            try:
                cancelar_o_rechazar(
                    pedido=ped,
                    nuevo_estado=EstadoPedido.CANCELADO,
                    usuario=request.user,
                    nota="Cancelación solicitada desde panel de administración.",
                    devolucion_fisica=True,
                )
                exitos += 1
            except ErrorDominioEmuna as exc:
                self.message_user(
                    request,
                    f"No se pudo cancelar el pedido {ped.codigo}: {exc}",
                    level=messages.ERROR,
                )
        if exitos:
            self.message_user(
                request,
                f"Se cancelaron {exitos} pedido(s) y se repuso el inventario correspondiente.",
                level=messages.SUCCESS,
            )

    def get_urls(self) -> list[Any]:
        """Agrega rutas personalizadas de gestión y venta presencial dentro del admin de pedidos.

        Qué hace:      Registra las URLs de flujo (cotizar, pagar, enviar, entregar, cancelar, POS).
        Va hacia:      Resuelve las acciones contextuales desde change_form.html y change_list.html.
        Depende de:    self.admin_site.admin_view y los métodos de vista de PedidoAdmin.
        Cuándo usarla: Al inicializar las rutas de Django Admin para el modelo Pedido.
        Si no opera:   Retorna la lista estándar de ModelAdmin.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "venta-presencial/",
                self.admin_site.admin_view(self.vista_venta_presencial),
                name="pedidos_pedido_venta_presencial",
            ),
            path(
                "<int:pedido_id>/cotizar/",
                self.admin_site.admin_view(require_POST(self.vista_cotizar_pedido)),
                name="pedidos_pedido_cotizar",
            ),
            path(
                "<int:pedido_id>/confirmar-pago/",
                self.admin_site.admin_view(require_POST(self.vista_confirmar_pago_pedido)),
                name="pedidos_pedido_confirmar_pago",
            ),
            path(
                "<int:pedido_id>/confirmar-y-entregar/",
                self.admin_site.admin_view(require_POST(self.vista_confirmar_y_entregar_pedido)),
                name="pedidos_pedido_confirmar_y_entregar",
            ),
            path(
                "<int:pedido_id>/registrar-envio/",
                self.admin_site.admin_view(require_POST(self.vista_registrar_envio_pedido)),
                name="pedidos_pedido_registrar_envio",
            ),
            path(
                "<int:pedido_id>/marcar-entregado/",
                self.admin_site.admin_view(require_POST(self.vista_marcar_entregado_pedido)),
                name="pedidos_pedido_marcar_entregado",
            ),
            path(
                "<int:pedido_id>/cancelar/",
                self.admin_site.admin_view(require_POST(self.vista_cancelar_pedido)),
                name="pedidos_pedido_cancelar",
            ),
        ]
        return custom_urls + urls

    def _redirigir_a_ficha(self, pedido_id: int) -> HttpResponseRedirect:
        """Retorna una redirección HTTP hacia la ficha de edición del pedido indicado.

        Qué hace:      Resuelve reverse('admin:pedidos_pedido_change') con el ID del pedido.
        Va hacia:      HttpResponseRedirect tras ejecutar una acción contextual del flujo.
        Depende de:    django.urls.reverse.
        Cuándo usarla: Al finalizar cada vista POST contextual de PedidoAdmin.
        Si no opera:   Lanza NoReverseMatch si cambia el nombre de la ruta admin.
        """
        return HttpResponseRedirect(reverse("admin:pedidos_pedido_change", args=[pedido_id]))

    def vista_cotizar_pedido(self, request: HttpRequest, pedido_id: int) -> HttpResponseRedirect:
        """Procesa la cotización del costo de envío y pasa el pedido de NUEVO a COTIZADO.

        Qué hace:      Lee costo_envio del POST, valida decimal y llama a cotizar_envio().
        Va hacia:      Actualiza total, pasa a COTIZADO y recarga la ficha con aviso de éxito.
        Depende de:    cotizar_envio, Pedido y messages.
        Cuándo usarla: Al enviar el formulario Paso 1 dentro de la ficha de un pedido NUEVO.
        Si no opera:   Informa error legible (ej. monto inválido) sin alterar el pedido.
        """
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        try:
            costo = Decimal(request.POST.get("costo_envio", "").strip())
            nota = request.POST.get("nota", "").strip()
            cotizar_envio(pedido=pedido, costo_envio=costo, usuario=request.user, nota=nota)
            self.message_user(
                request,
                f"Pedido {pedido.codigo} cotizado con envío S/ {costo:.2f}. Ya puedes avisar al cliente por WhatsApp.",
                level=messages.SUCCESS,
            )
        except (InvalidOperation, ValueError):
            self.message_user(
                request,
                "Ingresa un costo de envío válido en soles (ej. 15.00).",
                level=messages.ERROR,
            )
        except (ErrorDominioEmuna, ValidationError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
        return self._redirigir_a_ficha(pedido_id)

    def vista_confirmar_pago_pedido(
        self, request: HttpRequest, pedido_id: int
    ) -> HttpResponseRedirect:
        """Confirma el pago desde la ficha del pedido y descuenta stock atómicamente.

        Qué hace:      Toma metodo_pago y nota del POST e invoca confirmar_pago().
        Va hacia:      Pasa el pedido de COTIZADO a PAGADO creando movimientos VENTA.
        Depende de:    confirmar_pago y bloqueo select_for_update().
        Cuándo usarla: Al pulsar 'Confirmar Pago' dentro de la ficha de un pedido COTIZADO.
        Si no opera:   Revierte todo y muestra alerta si falta stock o el estado no corresponde.
        """
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        metodo = request.POST.get("metodo_pago", "YAPE").strip() or "YAPE"
        nota = request.POST.get("nota", "").strip()
        try:
            confirmar_pago(pedido=pedido, metodo_pago=metodo, usuario=request.user, nota=nota)
            self.message_user(
                request,
                f"¡Pago confirmado para {pedido.codigo}! El stock de las camisetas fue descontado atómicamente.",
                level=messages.SUCCESS,
            )
        except (ErrorDominioEmuna, ValidationError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
        return self._redirigir_a_ficha(pedido_id)

    def vista_confirmar_y_entregar_pedido(
        self, request: HttpRequest, pedido_id: int
    ) -> HttpResponseRedirect:
        """Ejecuta el flujo rápido de Lima (COTIZADO -> PAGADO -> ENTREGADO) en un clic.

        Qué hace:      Invoca confirmar_pago_y_entregar() descontando stock y cerrando la entrega.
        Va hacia:      Registra PAGADO y ENTREGADO en TBL_LPEDIDO_ESTADO en la misma transacción.
        Depende de:    confirmar_pago_y_entregar.
        Cuándo usarla: En pedidos de Lima (Punto de Encuentro / Recojo) al entregar en persona.
        Si no opera:   Muestra error si no hay stock suficiente o si la transición es inválida.
        """
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        metodo = request.POST.get("metodo_pago", "YAPE").strip() or "YAPE"
        nota = f"Entrega presencial confirmada en {pedido.punto_encuentro or 'Lima'}."
        try:
            confirmar_pago_y_entregar(
                pedido=pedido,
                metodo_pago=metodo,
                usuario=request.user,
                nota=nota,
            )
            self.message_user(
                request,
                f"¡Entrega en Lima completada para {pedido.codigo}! Stock descontado y pedido ENTREGADO.",
                level=messages.SUCCESS,
            )
        except (ErrorDominioEmuna, ValidationError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
        return self._redirigir_a_ficha(pedido_id)

    def vista_registrar_envio_pedido(
        self, request: HttpRequest, pedido_id: int
    ) -> HttpResponseRedirect:
        """Registra la guía, clave de 4 dígitos y boleta privada pasando a ENVIADO.

        Qué hace:      Valida formulario multipart de despacho y llama a registrar_envio_agencia().
        Va hacia:      Crea TBL_TENVIO y transiciona el pedido de PAGADO a ENVIADO.
        Depende de:    registrar_envio_agencia y archivo en request.FILES['imagen_boleta'].
        Cuándo usarla: Cuando Richard vuelve de Shalom u Olva con la boleta física.
        Si no opera:   Muestra el error específico (ej. clave distinta de 4 dígitos o falta boleta).
        """
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        try:
            costo_flete = Decimal(request.POST.get("costo_flete", "0").strip())
            registrar_envio_agencia(
                pedido=pedido,
                agencia=request.POST.get("agencia", pedido.agencia or AgenciaEnvio.SHALOM).strip(),
                numero_orden_agencia=request.POST.get("numero_orden_agencia", "").strip(),
                clave_recojo=request.POST.get("clave_recojo", "").strip(),
                imagen_boleta=request.FILES.get("imagen_boleta"),
                costo_flete=costo_flete,
                quien_paga=request.POST.get(
                    "quien_paga", QuienPagaFlete.CLIENTE_ADELANTADO
                ).strip(),
                cobrado=request.POST.get("cobrado") == "1",
                notas=request.POST.get("notas", "").strip(),
                usuario=request.user,
            )
            self.message_user(
                request,
                f"Despacho registrado en agencia para {pedido.codigo}. Ya puedes enviarle la guía y clave al cliente por WhatsApp.",
                level=messages.SUCCESS,
            )
        except (InvalidOperation, ValueError):
            self.message_user(
                request,
                "El costo real del flete debe ser un número válido (ej. 15.00).",
                level=messages.ERROR,
            )
        except (ErrorDominioEmuna, ValidationError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
        return self._redirigir_a_ficha(pedido_id)

    def vista_marcar_entregado_pedido(
        self, request: HttpRequest, pedido_id: int
    ) -> HttpResponseRedirect:
        """Marca el pedido como ENTREGADO tras recojo en agencia o entrega de delivery.

        Qué hace:      Llama a cambiar_estado(..., ENTREGADO) actualizando fechas y bitácora.
        Va hacia:      Finaliza el ciclo operativo del pedido en estado ENTREGADO.
        Depende de:    cambiar_estado.
        Cuándo usarla: Cuando el cliente retira en Shalom/Olva o recibe el motorizado en Lima.
        Si no opera:   Informa error si el estado actual no admite pasar a ENTREGADO.
        """
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        try:
            cambiar_estado(
                pedido=pedido,
                nuevo_estado=EstadoPedido.ENTREGADO,
                usuario=request.user,
                nota="Entrega final confirmada desde la ficha del pedido.",
            )
            self.message_user(
                request,
                f"¡Pedido {pedido.codigo} marcado como ENTREGADO!",
                level=messages.SUCCESS,
            )
        except (ErrorDominioEmuna, ValidationError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
        return self._redirigir_a_ficha(pedido_id)

    def vista_cancelar_pedido(
        self, request: HttpRequest, pedido_id: int
    ) -> HttpResponseRedirect:
        """Cancela el pedido desde su ficha y repone el stock si ya había sido pagado.

        Qué hace:      Ejecuta cancelar_o_rechazar() respetando devolución física en ENVIADO.
        Va hacia:      Cambia estado a CANCELADO y genera movimientos DEVOLUCION cuando aplica.
        Depende de:    cancelar_o_rechazar.
        Cuándo usarla: Al anular un pedido desde los botones del panel superior de la ficha.
        Si no opera:   Muestra error si el pedido ya estaba cerrado o falta confirmar devolución.
        """
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        nota = request.POST.get("nota", "").strip() or "Cancelado desde la ficha del pedido."
        devolucion_fisica = request.POST.get("devolucion_fisica") == "1"
        try:
            cancelar_o_rechazar(
                pedido=pedido,
                nuevo_estado=EstadoPedido.CANCELADO,
                usuario=request.user,
                nota=nota,
                devolucion_fisica=devolucion_fisica,
            )
            self.message_user(
                request,
                f"Pedido {pedido.codigo} cancelado correctamente.",
                level=messages.SUCCESS,
            )
        except (ErrorDominioEmuna, ValidationError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
        return self._redirigir_a_ficha(pedido_id)

    def vista_venta_presencial(self, request: HttpRequest) -> HttpResponse:
        """Renderiza y procesa el formulario de venta presencial directa en mostrador (Flujo C).

        Qué hace:      Permite a Richard buscar por palabras, paginar variantes y registrar ventas POS.
        Va hacia:      Crea Pedido con origen PRESENCIAL y redirige al detalle en el admin.
        Depende de:    registrar_venta_presencial, Paginator y Variante.
        Cuándo usarla: Al pulsar el botón '+ Registrar Venta Presencial' en la cabecera de pedidos.
        Si no opera:   Muestra alertas de validación o stock insuficiente sin perder los datos ingresados.
        """
        variantes_qs = (
            Variante.objects.select_related("producto", "producto__categoria")
            .filter(activa=True, producto__activo=True, cantidad_stock__gt=0)
            .order_by("producto__nombre", "talla")
        )

        busqueda = request.GET.get("q", "").strip()
        if busqueda:
            palabras = busqueda.split()
            filtro = Q()
            for p in palabras:
                filtro &= (
                    Q(producto__nombre__icontains=p)
                    | Q(sku__icontains=p)
                    | Q(talla__icontains=p)
                    | Q(color__icontains=p)
                    | Q(producto__categoria__nombre__icontains=p)
                )
            variantes_qs = variantes_qs.filter(filtro)

        # Paginación enterprise: 15 variantes por página para proteger memoria y base de datos
        paginador = Paginator(variantes_qs, 15)
        numero_pagina = request.GET.get("page", 1)
        pagina_obj = paginador.get_page(numero_pagina)

        form_error = ""

        if request.method == "POST":
            cliente_nombre = request.POST.get("cliente_nombre", "").strip()
            cliente_telefono = request.POST.get("cliente_telefono", "").strip()
            metodo_pago = request.POST.get("metodo_pago", "YAPE").strip()
            marcar_entregado = request.POST.get("marcar_entregado") == "1"
            notas = request.POST.get("notas", "").strip()

            lineas: list[dict[str, Any]] = []
            for clave, valor in request.POST.items():
                if clave.startswith("cant_"):
                    var_id_str = clave[5:]
                    try:
                        var_id = int(var_id_str)
                        cant = int(str(valor).strip())
                        if cant > 0:
                            lineas.append({"variante_id": var_id, "cantidad": cant})
                    except (ValueError, TypeError):
                        continue

            if not lineas:
                form_error = "Debes ingresar al menos una camiseta con cantidad mayor a 0."
            else:
                try:
                    pedido_creado = registrar_venta_presencial(
                        lineas=lineas,
                        metodo_pago=metodo_pago,
                        usuario=request.user,
                        cliente_nombre=cliente_nombre,
                        cliente_telefono=cliente_telefono,
                        marcar_entregado=marcar_entregado,
                        notas=notas,
                    )
                    self.message_user(
                        request,
                        f"¡Venta presencial {pedido_creado.codigo} registrada con éxito! Total: S/ {pedido_creado.total:.2f}",
                        level=messages.SUCCESS,
                    )
                    url_detalle = reverse("admin:pedidos_pedido_change", args=[pedido_creado.pk])
                    return HttpResponseRedirect(url_detalle)
                except ErrorDominioEmuna as exc:
                    form_error = str(exc)

        contexto = {
            **self.admin_site.each_context(request),
            "title": "Registrar Venta Presencial (POS Directo)",
            "variantes": pagina_obj.object_list,
            "pagina_obj": pagina_obj,
            "paginador": paginador,
            "busqueda": busqueda,
            "total_disponibles": paginador.count,
            "form_error": form_error,
            "post_data": request.POST if request.method == "POST" else None,
        }
        return render(request, "admin/pedidos/venta_presencial.html", contexto)
