"""Selectores de lectura de la aplicación pedidos (Carrito en sesión, Pedido público y WhatsApp)."""
from decimal import Decimal
from typing import Any
from urllib.parse import quote

from django.contrib.sessions.backends.base import SessionBase
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from apps.catalogo.models import ImagenProducto, ReglaPrecio, Variante
from apps.catalogo.selectores import calcular_precio_unitario_aplicado
from apps.nucleo.models import TipoMetodoPago
from apps.nucleo.selectores import listar_metodos_pago_activos, obtener_configuracion_tienda
from apps.nucleo.validadores import limpiar_texto_seguro

from .models import EstadoPedido, ItemPedido, Pedido, RegistroEstadoPedido, TipoEntrega

CLAVE_SESION_CARRITO = "emuna_carrito_v1"


def obtener_carrito_detallado(sesion: SessionBase | dict[str, Any]) -> dict[str, Any]:
    """Lee el carrito de la sesión y recalcula los precios por mayor sumando tallas del mismo producto.

    Qué hace:      Agrupa variantes por producto, calcula el precio unitario aplicado y el ahorro.
    Va hacia:      Retorna un diccionario con items, total_unidades, subtotal y ahorro_mayorista.
    Depende de:    Variante, calcular_precio_unitario_aplicado y la sesión del usuario.
    Cuándo usarla: En el context_processor, cajón lateral HTMX, página /carrito/ y checkout.
    Si no opera:   Si la sesión está vacía o una variante ya no existe, la omite de forma segura.
    """
    mapa_crudo = sesion.get(CLAVE_SESION_CARRITO, {})
    config = obtener_configuracion_tienda()
    numero_whatsapp = config.numero_whatsapp if config else "999888777"
    url_whatsapp_base = f"https://api.whatsapp.com/send?phone=51{numero_whatsapp}&text="

    if not isinstance(mapa_crudo, dict) or not mapa_crudo:
        mensaje_vacio = "Hola Richard, estuve revisando tu página web de *Emuná Sport* y quiero hacer una consulta."
        return {
            "items": [],
            "total_unidades": 0,
            "subtotal": Decimal("0.00"),
            "subtotal_sin_descuento": Decimal("0.00"),
            "ahorro_mayorista": Decimal("0.00"),
            "tiene_descuento_mayorista": False,
            "esta_vacio": True,
            "url_whatsapp_consulta": f"{url_whatsapp_base}{quote(mensaje_vacio)}",
        }

    ids_variantes: list[int] = []
    cantidades_por_variante: dict[int, int] = {}
    for var_id_str, cant in mapa_crudo.items():
        try:
            var_id = int(var_id_str)
            cantidad_int = int(cant)
            if cantidad_int >= 1:
                ids_variantes.append(var_id)
                cantidades_por_variante[var_id] = cantidad_int
        except (TypeError, ValueError):
            continue

    if not ids_variantes:
        return {
            "items": [],
            "total_unidades": 0,
            "subtotal": Decimal("0.00"),
            "subtotal_sin_descuento": Decimal("0.00"),
            "ahorro_mayorista": Decimal("0.00"),
            "tiene_descuento_mayorista": False,
            "esta_vacio": True,
        }

    variantes = list(
        Variante.objects.filter(
            id__in=ids_variantes,
            activa=True,
            producto__activo=True,
            producto__categoria__activa=True,
        )
        .select_related("producto", "producto__categoria")
        .prefetch_related(
            Prefetch(
                "producto__imagenes",
                queryset=ImagenProducto.objects.order_by("-es_principal", "orden", "id"),
            ),
            Prefetch(
                "producto__reglas_precio",
                queryset=ReglaPrecio.objects.order_by("cantidad_minima"),
            ),
        )
    )

    # 1. Sumar unidades totales por Producto (combinando tallas S, M, L, XL)
    unidades_por_producto: dict[int, int] = {}
    for var in variantes:
        cant_solicitada = cantidades_por_variante.get(var.id, 0)
        cant_efectiva = min(cant_solicitada, var.cantidad_stock)
        if cant_efectiva >= 1:
            unidades_por_producto[var.producto_id] = (
                unidades_por_producto.get(var.producto_id, 0) + cant_efectiva
            )

    # 2. Construir líneas detalladas con el precio unitario recalculado en el servidor
    items_detallados: list[dict[str, Any]] = []
    total_unidades = 0
    subtotal = Decimal("0.00")
    subtotal_sin_descuento = Decimal("0.00")

    for var in variantes:
        cant_solicitada = cantidades_por_variante.get(var.id, 0)
        cant_efectiva = min(cant_solicitada, var.cantidad_stock)
        if cant_efectiva < 1:
            continue

        producto = var.producto
        total_prod = unidades_por_producto.get(producto.id, cant_efectiva)
        precio_aplicado = calcular_precio_unitario_aplicado(
            producto=producto,
            cantidad_total_producto=total_prod,
        )
        precio_base = producto.precio_unidad
        subtotal_linea = (precio_aplicado * Decimal(cant_efectiva)).quantize(Decimal("0.01"))
        subtotal_base_linea = (precio_base * Decimal(cant_efectiva)).quantize(Decimal("0.01"))
        ahorro_linea = (subtotal_base_linea - subtotal_linea).quantize(Decimal("0.01"))

        imagenes_prod = list(producto.imagenes.all())
        miniatura = (
            imagenes_prod[0].ruta_miniatura
            if imagenes_prod
            else "logo_emuna_transparente.png"
        )

        items_detallados.append(
            {
                "variante": var,
                "variante_id": var.id,
                "producto": producto,
                "nombre_producto": producto.nombre,
                "slug_producto": producto.slug,
                "sku": var.sku,
                "talla": var.talla,
                "color": var.color,
                "cantidad": cant_efectiva,
                "stock_disponible": var.cantidad_stock,
                "precio_base": precio_base,
                "precio_unidad": precio_aplicado,
                "es_precio_mayorista": precio_aplicado < precio_base,
                "cantidad_total_mismo_producto": total_prod,
                "subtotal": subtotal_linea,
                "ahorro_linea": ahorro_linea,
                "ruta_miniatura": miniatura,
            }
        )

        total_unidades += cant_efectiva
        subtotal += subtotal_linea
        subtotal_sin_descuento += subtotal_base_linea

    ahorro_mayorista = (subtotal_sin_descuento - subtotal).quantize(Decimal("0.01"))

    # Construir mensaje de consulta detallado con las prendas en carrito para Richard
    if items_detallados:
        lineas_items = [
            f"• {item['cantidad']}x {item['nombre_producto']} (Talla {item['talla']}) – S/ {item['subtotal']}"
            for item in items_detallados
        ]
        detalle_prendas = "\n".join(lineas_items)
        mensaje_carrito = (
            f"Hola Richard, estuve revisando tu página web de *Emuná Sport* y quiero consultar por este pedido:\n\n"
            f"{detalle_prendas}\n\n"
            f"*Total camisetas:* S/ {subtotal:.2f}\n\n"
            f"¿Tienes stock disponible y los precios son correctos?"
        )
    else:
        mensaje_carrito = "Hola Richard, estuve revisando tu página web de *Emuná Sport* y quiero hacer una consulta."

    url_whatsapp_consulta = f"{url_whatsapp_base}{quote(mensaje_carrito)}"

    return {
        "items": items_detallados,
        "total_unidades": total_unidades,
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "subtotal_sin_descuento": subtotal_sin_descuento.quantize(Decimal("0.01")),
        "ahorro_mayorista": ahorro_mayorista,
        "tiene_descuento_mayorista": ahorro_mayorista > Decimal("0.00"),
        "esta_vacio": len(items_detallados) == 0,
        "url_whatsapp_consulta": url_whatsapp_consulta,
    }


def obtener_pedido_por_codigo(*, codigo: str) -> Pedido:
    """Busca un pedido por su código público no adivinable con ítems e historial precargados.

    Qué hace:      Consulta TBL_TPEDIDO por PED_CCODIGO (insensible a mayúsculas/minúsculas).
    Va hacia:      Retorna la instancia de Pedido con items y bitácora de estados.
    Depende de:    Pedido, ItemPedido, RegistroEstadoPedido y get_object_or_404.
    Cuándo usarla: En vistas públicas de seguimiento, generador de PDF y servicios.
    Si no opera:   Lanza Http404 si el código no existe o tiene formato inválido.
    """
    codigo_limpio = limpiar_texto_seguro(codigo, longitud_maxima=20).upper()
    qs = Pedido.objects.select_related("metodo_pago").prefetch_related(
        Prefetch("items", queryset=ItemPedido.objects.select_related("variante").order_by("id")),
        Prefetch("historial_estados", queryset=RegistroEstadoPedido.objects.order_by("fecha_creacion")),
    )
    return get_object_or_404(qs, codigo=codigo_limpio)


def obtener_pedido_publico(*, codigo: str) -> dict[str, Any]:
    """Obtiene los datos públicos de un pedido excluyendo DNI completo, teléfono y claves privadas.

    Qué hace:      Construye la vista segura del pedido (Pilar 1 Anti-Hacking) y adjunta Yape si aplica.
    Va hacia:      Retorna un diccionario seguro para la plantilla /pedidos/<codigo>/ y la API pública.
    Depende de:    obtener_pedido_por_codigo y listar_metodos_pago_activos.
    Cuándo usarla: Cuando el cliente abre el enlace único de su pedido desde el celular o la web.
    Si no opera:   Lanza Http404 si el código no corresponde a ningún pedido.
    """
    pedido = obtener_pedido_por_codigo(codigo=codigo)
    items = list(pedido.items.all())
    total_prendas = sum(item.cantidad for item in items)

    metodo_yape = None
    if pedido.estado == EstadoPedido.COTIZADO:
        metodo_yape = (
            listar_metodos_pago_activos()
            .filter(tipo=TipoMetodoPago.YAPE)
            .first()
        )

    return {
        "pedido": pedido,
        "codigo": pedido.codigo,
        "estado": pedido.estado,
        "etiqueta_estado": pedido.get_estado_display(),
        "cliente_nombre": pedido.cliente_nombre,
        "dni_enmascarado": pedido.dni_enmascarado,
        "tipo_entrega": pedido.tipo_entrega,
        "etiqueta_tipo_entrega": pedido.get_tipo_entrega_display(),
        "agencia": pedido.agencia,
        "etiqueta_agencia": pedido.get_agencia_display() if pedido.agencia else "",
        "agencia_ciudad": pedido.agencia_ciudad,
        "agencia_referencia": pedido.agencia_referencia,
        "punto_encuentro": pedido.punto_encuentro,
        "entrega_programada": pedido.entrega_programada,
        "items": items,
        "total_prendas": total_prendas,
        "subtotal": pedido.subtotal,
        "costo_envio": pedido.costo_envio,
        "total": pedido.total,
        "fecha_creacion": pedido.fecha_creacion,
        "mostrar_datos_pago_yape": pedido.estado == EstadoPedido.COTIZADO,
        "metodo_yape": metodo_yape,
    }


def construir_enlace_whatsapp_pedido(*, pedido: Pedido, url_publica_pedido: str) -> str:
    """Construye el enlace wa.me hacia Richard con el resumen estructurado del pedido recién creado.

    Qué hace:      Formatea código, ítems, tallas, modalidad de entrega, total y link del pedido.
    Va hacia:      Retorna una URL https://wa.me/51... lista para el CTA único en verde neón.
    Depende de:    obtener_configuracion_tienda, Pedido y sus líneas ItemPedido.
    Cuándo usarla: En la página de confirmación del pedido (/pedidos/<codigo>/).
    Si no opera:   Usa el número por defecto de Emuná Sport si aún no hay configuración en BD.
    """
    config = obtener_configuracion_tienda()
    lineas_items = [
        f"• {item.cantidad}x {item.nombre_producto} (Talla {item.talla}) – S/ {item.subtotal}"
        for item in pedido.items.all()
    ]
    detalle_prendas = "\n".join(lineas_items)

    if pedido.tipo_entrega == TipoEntrega.PUNTO_ENCUENTRO:
        linea_entrega = (
            f"*Punto de encuentro en Lima:* {pedido.punto_encuentro or 'Por coordinar'} "
            "(Envío S/ 0.00 – Pago con Yape al recibir)"
        )
    elif pedido.tipo_entrega == TipoEntrega.RECOJO:
        linea_entrega = "*Modalidad:* Recojo acordado (Envío S/ 0.00)"
    elif pedido.tipo_entrega == TipoEntrega.AGENCIA:
        agencia_txt = pedido.get_agencia_display() if pedido.agencia else "Agencia"
        linea_entrega = (
            f"*Envío por {agencia_txt}:* {pedido.agencia_ciudad or ''} "
            f"({pedido.agencia_referencia or 'Sede principal'}) – Flete por cotizar"
        )
    else:
        linea_entrega = (
            f"*Delivery en Lima:* {pedido.punto_encuentro or 'Por coordinar'} "
            "– Delivery por cotizar"
        )

    mensaje = (
        f"Hola Richard, acabo de registrar mi pedido *{pedido.codigo}* en *Emuná Sport*:\n\n"
        f"*Cliente:* {pedido.cliente_nombre}\n"
        f"{linea_entrega}\n\n"
        f"*Camisetas solicitadas:*\n{detalle_prendas}\n\n"
        f"*Total camisetas:* S/ {pedido.subtotal}\n"
        f"*Ver mi pedido y PDF:* {url_publica_pedido}"
    )
    return f"https://api.whatsapp.com/send?phone=51{config.numero_whatsapp}&text={quote(mensaje)}"
