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
        url_miniatura = (
            imagenes_prod[0].url_miniatura
            if imagenes_prod
            else "/static/logo_emuna_transparente.png"
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
                "url_miniatura": url_miniatura,
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
    """Busca un pedido por su código público no adivinable con ítems, envío e historial.

    Qué hace:      Consulta TBL_TPEDIDO por PED_CCODIGO (insensible a mayúsculas/minúsculas).
    Va hacia:      Retorna la instancia de Pedido con items, envío y bitácora de estados.
    Depende de:    Pedido, ItemPedido, RegistroEstadoPedido y get_object_or_404.
    Cuándo usarla: En vistas públicas de seguimiento, generador de PDF y servicios.
    Si no opera:   Lanza Http404 si el código no existe o tiene formato inválido.
    """
    codigo_limpio = limpiar_texto_seguro(codigo, longitud_maxima=20).upper()
    qs = Pedido.objects.select_related("metodo_pago", "envio").prefetch_related(
        Prefetch("items", queryset=ItemPedido.objects.select_related("variante").order_by("id")),
        Prefetch("historial_estados", queryset=RegistroEstadoPedido.objects.order_by("fecha_creacion")),
    )
    return get_object_or_404(qs, codigo=codigo_limpio)


def _construir_siguiente_paso_publico(
    *, pedido: Pedido, envio_publico: dict[str, Any] | None
) -> dict[str, Any]:
    """Determina el título, guía y botón contextual según el estado actual del pedido.

    Qué hace:      Adapta el bloque 'Siguiente Paso' de la página pública al ciclo real de venta.
    Va hacia:      Retorna diccionario con badge, titulo, descripcion, texto_boton y es_cta_principal.
    Depende de:    EstadoPedido y TipoEntrega.
    Cuándo usarla: En obtener_pedido_publico() al renderizar /pedidos/<codigo>/.
    Si no opera:   Retorna mensaje genérico de consulta por WhatsApp.
    """
    est = pedido.estado
    if est == EstadoPedido.NUEVO:
        return {
            "badge": "⚡ Siguiente Paso Recomendado",
            "titulo": "Envía tu Pedido a Richard por WhatsApp",
            "descripcion": (
                f"Haz clic en el botón verde neón para enviarle a Richard el resumen automático "
                f"de tu pedido {pedido.codigo} y que te cotice el envío al instante."
            ),
            "texto_boton": "ENVIAR A RICHARD POR WHATSAPP →",
            "es_cta_principal": True,
        }
    if est == EstadoPedido.COTIZADO:
        if pedido.tipo_entrega in (TipoEntrega.PUNTO_ENCUENTRO, TipoEntrega.RECOJO):
            return {
                "badge": "📍 Siguiente Paso: Coordinar Entrega",
                "titulo": "Coordina punto y hora con Richard",
                "descripcion": (
                    f"Tu pedido {pedido.codigo} está listo (Envío S/ 0.00). Coordina la hora exacta "
                    "con Richard por WhatsApp; puedes yapearle usando el QR o al recibir tu prenda."
                ),
                "texto_boton": "COORDINAR ENTREGA POR WHATSAPP →",
                "es_cta_principal": True,
            }
        return {
            "badge": "🟣 Siguiente Paso: Pago con Yape",
            "titulo": "Realiza el Yape y envía tu captura",
            "descripcion": (
                f"Tu envío ya fue cotizado. Realiza el Yape por S/ {pedido.total:.2f} usando el QR "
                f"de abajo y envíale la captura a Richard para separar tus camisetas al instante."
            ),
            "texto_boton": "ENVIAR CAPTURA DE PAGO POR WHATSAPP →",
            "es_cta_principal": True,
        }
    if est == EstadoPedido.PAGADO:
        if pedido.tipo_entrega in (TipoEntrega.PUNTO_ENCUENTRO, TipoEntrega.RECOJO):
            return {
                "badge": "✅ Pago Confirmado · Prenda Separada",
                "titulo": "¡Tus camisetas ya están separadas!",
                "descripcion": (
                    f"¡Gracias! Tu pago por S/ {pedido.total:.2f} fue confirmado y tus camisetas "
                    "quedaron separadas en almacén. Coordina o confirma con Richard la entrega en mano por WhatsApp."
                ),
                "texto_boton": "COORDINAR ENTREGA POR WHATSAPP",
                "es_cta_principal": False,
            }
        return {
            "badge": "✅ Pago Confirmado · Separado",
            "titulo": "Richard está preparando tu paquete",
            "descripcion": (
                f"¡Gracias! Tu pago por S/ {pedido.total:.2f} fue verificado y tus camisetas ya están "
                "separadas del almacén. Te avisaremos apenas salgan a despacho."
            ),
            "texto_boton": "CONSULTAR SOBRE MI PEDIDO POR WHATSAPP",
            "es_cta_principal": False,
        }
    if est == EstadoPedido.ENVIADO:
        detalle_guia = (
            f"Despachado por {envio_publico['agencia']} (N° Orden/Guía: {envio_publico['numero_orden_agencia']}). "
            if envio_publico
            else "Tu paquete ya salió hacia tu destino. "
        )
        return {
            "badge": "🚚 Pedido en Camino",
            "titulo": "¡Tu paquete ya fue despachado!",
            "descripcion": (
                f"{detalle_guia}Por seguridad, Richard te envió tu clave secreta de recojo de 4 dígitos "
                "directamente a tu WhatsApp."
            ),
            "texto_boton": "CONSULTAR CLAVE DE RECOJO POR WHATSAPP",
            "es_cta_principal": False,
        }
    if est == EstadoPedido.ENTREGADO:
        return {
            "badge": "🎉 Pedido Entregado",
            "titulo": "¡Gracias por tu compra en Emuná Sport!",
            "descripcion": (
                f"Tu pedido {pedido.codigo} fue entregado con éxito. ¡Disfruta tus camisetas! "
                "Si necesitas algo más, escríbenos por WhatsApp."
            ),
            "texto_boton": "ESCRIBIR A RICHARD POR WHATSAPP",
            "es_cta_principal": False,
        }
    etiqueta = pedido.get_estado_display()
    return {
        "badge": f"⚠️ Pedido {etiqueta}",
        "titulo": f"Pedido {etiqueta}",
        "descripcion": (
            f"El pedido {pedido.codigo} se encuentra cerrado como {etiqueta.lower()}. "
            "Si tienes alguna duda o deseas retomarlo, escríbenos."
        ),
        "texto_boton": "CONSULTAR CON RICHARD POR WHATSAPP",
        "es_cta_principal": False,
    }


def _construir_pasos_seguimiento_publico(*, pedido: Pedido) -> list[dict[str, Any]]:
    """Construye los pasos de la barra de progreso pública adaptados a la modalidad del pedido.

    Qué hace:      Define las etapas reales según TipoEntrega (4 en Lima/Recojo, 5 en Agencia).
    Va hacia:      Retorna la lista ordenada para templates/pedidos/parcial_seguimiento_pedido.html.
    Depende de:    EstadoPedido y TipoEntrega.
    Cuándo usarla: En obtener_pedido_publico() al renderizar /pedidos/<codigo>/.
    Si no opera:   Si un pedido llegara a ENVIADO de forma excepcional, agrega el paso En Camino.
    """
    estado = pedido.estado
    tipo = pedido.tipo_entrega

    if tipo == TipoEntrega.AGENCIA:
        pasos_def = [
            (EstadoPedido.NUEVO, "Recibido"),
            (EstadoPedido.COTIZADO, "Cotizado / Listo"),
            (EstadoPedido.PAGADO, "Pago Confirmado"),
            (EstadoPedido.ENVIADO, "En Camino"),
            (EstadoPedido.ENTREGADO, "Entregado"),
        ]
    else:
        etiquetas_paso_2 = {
            TipoEntrega.PUNTO_ENCUENTRO: "Listo para coordinar",
            TipoEntrega.RECOJO: "Listo para recojo",
        }
        pasos_def = [
            (EstadoPedido.NUEVO, "Recibido"),
            (EstadoPedido.COTIZADO, etiquetas_paso_2.get(tipo, "Cotizado / Listo")),
            (EstadoPedido.PAGADO, "Pago Confirmado"),
            (EstadoPedido.ENTREGADO, "Entregado"),
        ]
        if estado == EstadoPedido.ENVIADO:
            pasos_def.insert(3, (EstadoPedido.ENVIADO, "En Camino"))

    estados_orden = [codigo for codigo, _ in pasos_def]
    indice_actual = estados_orden.index(estado) if estado in estados_orden else -1

    pasos: list[dict[str, Any]] = []
    for idx, (codigo_paso, etiqueta) in enumerate(pasos_def, start=1):
        es_actual = codigo_paso == estado
        completado = indice_actual > (idx - 1) or (
            estado == EstadoPedido.ENTREGADO and codigo_paso == EstadoPedido.ENTREGADO
        )
        pasos.append(
            {
                "numero": idx,
                "codigo": codigo_paso,
                "etiqueta": etiqueta,
                "es_actual": es_actual,
                "completado": completado,
            }
        )
    return pasos


def _construir_guia_modalidad_publica(*, tipo_entrega: str) -> dict[str, str]:
    """Construye la explicación y ejemplo paso a paso de la modalidad elegida por el cliente.

    Qué hace:      Describe qué estados recorre el pedido en la web y qué hace Richard en gestión.
    Va hacia:      Retorna diccionario con titulo, resumen_flujo y ejemplo_practico para la vista pública.
    Depende de:    TipoEntrega.
    Cuándo usarla: En obtener_pedido_publico() para la ventana/desplegable de ayuda del cliente.
    Si no opera:   Retorna la guía estándar de Punto de Encuentro.
    """
    guias = {
        TipoEntrega.PUNTO_ENCUENTRO: {
            "titulo": "📍 Punto de Encuentro en Lima (4 etapas · Envío S/ 0.00)",
            "resumen_flujo": (
                "1. Recibido → 2. Listo para coordinar (nace aquí con envío S/ 0.00) → "
                "3. Pago Confirmado (si yapeas antes para separar o al momento de vernos) → 4. Entregado."
            ),
            "ejemplo_practico": (
                "Ejemplo: Pides tu camiseta indicando 'Estación La Cultura'. Coordinas hora con Richard por WhatsApp; "
                "si deseas asegurar tu talla antes de la cita puedes yapear por adelantado (pasa a Pago Confirmado), "
                "o pagarle ahí mismo al recibir tu prenda en mano (pasa directo a Entregado)."
            ),
        },
        TipoEntrega.AGENCIA: {
            "titulo": "🚚 Envío a Provincia por Agencia Shalom / Olva (5 etapas)",
            "resumen_flujo": (
                "1. Recibido (falta cotizar flete) → 2. Cotizado / Listo (ya ves el total con QR Yape) → "
                "3. Pago Confirmado (stock separado) → 4. En Camino (N° Orden registrado) → 5. Entregado."
            ),
            "ejemplo_practico": (
                "Ejemplo (Trujillo / Arequipa / Cusco): Registras tu pedido con tu DNI de 8 dígitos. Richard cotiza el "
                "flete, tú yapeas tus camisetas y envías la captura; Richard deja el paquete en Shalom/Olva, sube la "
                "boleta y te envía por WhatsApp tu N° de Orden y tu Clave secreta de 4 dígitos para recoger."
            ),
        },
        TipoEntrega.DELIVERY_LIMA: {
            "titulo": "🛵 Delivery en Lima Metropolitana (4 etapas)",
            "resumen_flujo": (
                "1. Recibido (Richard revisa tu distrito) → 2. Cotizado / Listo (tarifa de delivery sumada al total) → "
                "3. Pago Confirmado (camisetas separadas tras tu Yape) → 4. Entregado en tu dirección."
            ),
            "ejemplo_practico": (
                "Ejemplo: Indicas tu dirección exacta en Lima. Richard cotiza el costo del delivery según tu distrito, "
                "realizas el Yape usando el QR de tu pedido y recibes el paquete en tu domicilio o centro de trabajo."
            ),
        },
        TipoEntrega.RECOJO: {
            "titulo": "🏪 Recojo Acordado con Richard (4 etapas · Envío S/ 0.00)",
            "resumen_flujo": (
                "1. Recibido → 2. Listo para recojo (nace aquí con envío S/ 0.00) → "
                "3. Pago Confirmado → 4. Entregado al recoger."
            ),
            "ejemplo_practico": (
                "Ejemplo: Tu pedido nace listo sin recargo de envío. Escribes a Richard por WhatsApp para acordar "
                "el horario de recojo y pagas con Yape o efectivo al retirar tus camisetas."
            ),
        },
    }
    return guias.get(tipo_entrega, guias[TipoEntrega.PUNTO_ENCUENTRO])


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

    envio_obj = getattr(pedido, "envio", None)
    envio_publico: dict[str, Any] | None = None
    if envio_obj and pedido.estado in (EstadoPedido.ENVIADO, EstadoPedido.ENTREGADO):
        envio_publico = {
            "agencia": envio_obj.get_agencia_display(),
            "numero_orden_agencia": envio_obj.numero_orden_agencia,
            "fecha_despacho": envio_obj.fecha_despacho,
        }

    siguiente_paso = _construir_siguiente_paso_publico(
        pedido=pedido, envio_publico=envio_publico
    )
    pasos_seguimiento = _construir_pasos_seguimiento_publico(pedido=pedido)
    guia_modalidad = _construir_guia_modalidad_publica(tipo_entrega=pedido.tipo_entrega)
    es_estado_terminal = pedido.estado in (
        EstadoPedido.ENTREGADO,
        EstadoPedido.CANCELADO,
        EstadoPedido.RECHAZADO,
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
        "envio_publico": envio_publico,
        "siguiente_paso": siguiente_paso,
        "pasos_seguimiento": pasos_seguimiento,
        "guia_modalidad": guia_modalidad,
        "es_estado_terminal": es_estado_terminal,
    }


def construir_enlace_whatsapp_pedido(*, pedido: Pedido, url_publica_pedido: str) -> str:
    """Construye el enlace wa.me hacia Richard adaptado al estado actual del pedido.

    Qué hace:      Formatea código, ítems, modalidad o consulta específica según el estado del pedido.
    Va hacia:      Retorna una URL https://api.whatsapp.com/send?... para el botón de la página pública.
    Depende de:    obtener_configuracion_tienda, Pedido, Envio y sus líneas ItemPedido.
    Cuándo usarla: En la página de seguimiento (/pedidos/<codigo>/) en cada etapa del flujo.
    Si no opera:   Usa el número por defecto de Emuná Sport si aún no hay configuración en BD.
    """
    config = obtener_configuracion_tienda()

    if pedido.estado == EstadoPedido.PAGADO:
        mensaje = (
            f"Hola Richard, tengo una consulta sobre mi pedido *{pedido.codigo}* "
            f"(Pago Confirmado por S/ {pedido.total:.2f}).\n"
            f"*Ver pedido:* {url_publica_pedido}"
        )
    elif pedido.estado == EstadoPedido.ENVIADO:
        envio = getattr(pedido, "envio", None)
        guia = f" ({envio.get_agencia_display()} – Orden {envio.numero_orden_agencia})" if envio else ""
        mensaje = (
            f"Hola Richard, mi pedido *{pedido.codigo}* ya figura En Camino{guia}. "
            f"¿Me confirmas la clave de recojo de 4 dígitos por favor?\n"
            f"*Ver pedido:* {url_publica_pedido}"
        )
    elif pedido.estado == EstadoPedido.ENTREGADO:
        mensaje = (
            f"Hola Richard, ya recibí conforme mi pedido *{pedido.codigo}* de *Emuná Sport*. "
            f"¡Muchas gracias!"
        )
    elif pedido.estado in (EstadoPedido.CANCELADO, EstadoPedido.RECHAZADO):
        mensaje = (
            f"Hola Richard, te escribo sobre mi pedido *{pedido.codigo}* "
            f"(estado: {pedido.get_estado_display()}).\n"
            f"*Ver pedido:* {url_publica_pedido}"
        )
    elif pedido.estado == EstadoPedido.COTIZADO and pedido.tipo_entrega in (
        TipoEntrega.AGENCIA,
        TipoEntrega.DELIVERY_LIMA,
    ):
        mensaje = (
            f"Hola Richard, ya recibí la cotización de mi pedido *{pedido.codigo}* "
            f"(Total: *S/ {pedido.total:.2f}*). Aquí te envío mi captura de Yape para confirmar "
            f"y separar mis camisetas:\n*Ver pedido:* {url_publica_pedido}"
        )
    else:
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
