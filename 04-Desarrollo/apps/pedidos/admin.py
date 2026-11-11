"""Configuración del panel administrativo para Pedidos, Envíos, Ítems y Bitácora de Estados."""
from typing import Any

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from apps.catalogo.models import Variante
from apps.nucleo.excepciones import ErrorDominioEmuna

from .models import Envio, EstadoPedido, ItemPedido, Pedido, RegistroEstadoPedido, TipoEntrega
from .servicios import (
    cambiar_estado,
    cancelar_o_rechazar,
    confirmar_pago,
    confirmar_pago_y_entregar,
    construir_enlace_whatsapp_notificacion_cliente,
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


class EnvioInline(admin.StackedInline):
    """Permite registrar y consultar el despacho en agencia (Shalom/Olva) dentro del pedido."""

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
        "pedido",
        "agencia",
        "numero_orden_agencia",
        "clave_recojo",
        "quien_paga",
        "cobrado",
        "costo_flete",
        "fecha_despacho",
        "ver_boleta_link",
    )
    list_filter = ("agencia", "quien_paga", "cobrado", "fecha_despacho")
    search_fields = ("numero_orden_agencia", "pedido__codigo", "pedido__cliente_nombre")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion", "ver_boleta_link")

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

    ver_boleta_link.short_description = "Boleta de Despacho"


@admin.register(Pedido)
class PedidoAdmin(SimpleHistoryAdmin):
    """Administración de pedidos web y ventas presenciales para Richard y Jonathan."""

    change_list_template = "admin/pedidos/pedido/change_list.html"

    list_display = (
        "codigo",
        "estado",
        "tipo_entrega",
        "cliente_nombre",
        "cliente_telefono",
        "subtotal",
        "costo_envio",
        "total",
        "notificacion_whatsapp",
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
        "notificacion_whatsapp",
    )
    inlines = [ItemPedidoInline, EnvioInline, RegistroEstadoPedidoInline]
    actions = [
        "accion_confirmar_pago",
        "accion_confirmar_pago_y_entregar",
        "accion_marcar_entregado",
        "accion_cancelar_pedido",
    ]

    def notificacion_whatsapp(self, obj: Pedido) -> str:
        """Construye un botón dinámico con enlace directo a WhatsApp para notificar al cliente.

        Qué hace:      Determina el estado del pedido y construye el mensaje prellenado en WhatsApp.
        Va hacia:      Abre api.whatsapp.com en una nueva pestaña con el texto formateado.
        Depende de:    construir_enlace_whatsapp_notificacion_cliente y estado del pedido.
        Cuándo usarla: En la tabla changelist para que Richard avise con 1 solo clic.
        Si no opera:   Muestra botón genérico de contacto si no tiene estado de flujo específico.
        """
        url_pedido = f"http://127.0.0.1:8000{reverse('pedidos:detalle_pedido', args=[obj.codigo])}"
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

    notificacion_whatsapp.short_description = "Avisar por WhatsApp"

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
        """Agrega la ruta personalizada de venta presencial (POS) dentro del admin de pedidos.

        Qué hace:      Inyecta la URL admin:pedidos_pedido_venta_presencial antes de las rutas estándar.
        Va hacia:      Resuelve la vista administrativa de venta presencial directa (Flujo C).
        Depende de:    self.admin_site.admin_view y vista_venta_presencial.
        Cuándo usarla: Al registrar las URLs del ModelAdmin de Pedido en Django.
        Si no opera:   Retorna la lista de URLs padrão de ModelAdmin.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "venta-presencial/",
                self.admin_site.admin_view(self.vista_venta_presencial),
                name="pedidos_pedido_venta_presencial",
            ),
        ]
        return custom_urls + urls

    def vista_venta_presencial(self, request: HttpRequest) -> HttpResponse:
        """Renderiza y procesa el formulario de venta presencial directa en mostrador (Flujo C).

        Qué hace:      Permite a Richard seleccionar prendas, cobrar en efectivo/Yape y descontar stock.
        Va hacia:      Crea Pedido con origen PRESENCIAL y redirige al detalle en el admin.
        Depende de:    registrar_venta_presencial y Variante.
        Cuándo usarla: Al pulsar el botón '+ Registrar Venta Presencial' en la cabecera de pedidos.
        Si no opera:   Muestra alertas de validación o stock insuficiente sin perder los datos ingresados.
        """
        variantes = (
            Variante.objects.select_related("producto")
            .filter(activa=True, producto__activo=True, cantidad_stock__gt=0)
            .order_by("producto__nombre", "talla")
        )
        form_error = ""

        if request.method == "POST":
            cliente_nombre = request.POST.get("cliente_nombre", "").strip()
            cliente_telefono = request.POST.get("cliente_telefono", "").strip()
            metodo_pago = request.POST.get("metodo_pago", "YAPE").strip()
            marcar_entregado = request.POST.get("marcar_entregado") == "1"
            notas = request.POST.get("notas", "").strip()

            lineas: list[dict[str, Any]] = []
            for var in variantes:
                campo_cant = f"cant_{var.id}"
                cant_str = request.POST.get(campo_cant, "0").strip()
                try:
                    cant = int(cant_str)
                    if cant > 0:
                        lineas.append({"variante_id": var.id, "cantidad": cant})
                except ValueError:
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
            "variantes": variantes,
            "form_error": form_error,
            "post_data": request.POST if request.method == "POST" else None,
        }
        return render(request, "admin/pedidos/venta_presencial.html", contexto)
