"""Servicios de escritura de la app pedidos: Carrito en sesión, Creación de pedido y PDF."""
import io
import json
import secrets
import urllib.parse
import urllib.request
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.db import transaction
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from apps.catalogo.models import Variante
from apps.nucleo.excepciones import (
    DatosEnvioIncompletosError,
    EntradaInvalidaError,
    StockInsuficienteError,
)
from apps.nucleo.selectores import obtener_configuracion_tienda
from apps.nucleo.validadores import (
    limpiar_texto_seguro,
    validar_dni_peruano,
    validar_telefono_peruano,
)

from .models import (
    AgenciaEnvio,
    EstadoPedido,
    ItemPedido,
    OrigenPedido,
    Pedido,
    RegistroEstadoPedido,
    TipoEntrega,
)
from .selectores import (
    CLAVE_SESION_CARRITO,
    obtener_carrito_detallado,
    obtener_pedido_por_codigo,
)

ALFABETO_CODIGO_PEDIDO = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def agregar_al_carrito(
    *,
    sesion: SessionBase | dict[str, Any],
    variante_id: int,
    cantidad: int = 1,
    reemplazar: bool = False,
) -> dict[str, Any]:
    """Agrega o actualiza una variante de camiseta en el carrito de sesión validando el stock.

    Qué hace:      Verifica que la variante exista, esté activa y tenga stock suficiente.
    Va hacia:      Actualiza el diccionario CLAVE_SESION_CARRITO en la sesión y retorna el carrito.
    Depende de:    Variante, StockInsuficienteError y obtener_carrito_detallado.
    Cuándo usarla: Al pulsar 'Agregar al Carrito' o ajustar cantidades (+/-) en el cajón HTMX.
    Si no opera:   Lanza EntradaInvalidaError o StockInsuficienteError si no hay stock suficiente.
    """
    try:
        variante_id_int = int(variante_id)
        cantidad_int = int(cantidad)
    except (TypeError, ValueError) as exc:
        raise EntradaInvalidaError("La variante y la cantidad deben ser números enteros.") from exc

    if cantidad_int < 1:
        return eliminar_del_carrito(sesion=sesion, variante_id=variante_id_int)

    variante = (
        Variante.objects.filter(
            id=variante_id_int,
            activa=True,
            producto__activo=True,
            producto__categoria__activa=True,
        )
        .select_related("producto")
        .first()
    )
    if variante is None:
        raise EntradaInvalidaError("La talla seleccionada ya no está disponible en el catálogo.")

    mapa_actual = dict(sesion.get(CLAVE_SESION_CARRITO, {}))
    clave = str(variante.id)
    cantidad_previa = int(mapa_actual.get(clave, 0))
    nueva_cantidad = cantidad_int if reemplazar else (cantidad_previa + cantidad_int)

    if variante.cantidad_stock <= 0:
        raise StockInsuficienteError(
            f"La talla {variante.talla} de {variante.producto.nombre} está agotada."
        )
    if nueva_cantidad > variante.cantidad_stock:
        raise StockInsuficienteError(
            f"Solo quedan {variante.cantidad_stock} unidades disponibles en talla "
            f"{variante.talla} de {variante.producto.nombre}."
        )

    mapa_actual[clave] = nueva_cantidad
    sesion[CLAVE_SESION_CARRITO] = mapa_actual
    if hasattr(sesion, "modified"):
        sesion.modified = True

    return obtener_carrito_detallado(sesion)


def eliminar_del_carrito(
    *, sesion: SessionBase | dict[str, Any], variante_id: int
) -> dict[str, Any]:
    """Elimina una variante específica del carrito en sesión.

    Qué hace:      Quita la clave de la variante de CLAVE_SESION_CARRITO y marca la sesión modificada.
    Va hacia:      Sesión del usuario y retorna el estado actualizado de obtener_carrito_detallado.
    Depende de:    CLAVE_SESION_CARRITO y obtener_carrito_detallado.
    Cuándo usarla: Cuando el cliente pulsa 'Quitar' o reduce la cantidad a 0 en el carrito.
    Si no opera:   Si la variante no estaba en el carrito, retorna el carrito sin cambios.
    """
    mapa_actual = dict(sesion.get(CLAVE_SESION_CARRITO, {}))
    mapa_actual.pop(str(variante_id), None)
    sesion[CLAVE_SESION_CARRITO] = mapa_actual
    if hasattr(sesion, "modified"):
        sesion.modified = True
    return obtener_carrito_detallado(sesion)


def vaciar_carrito(sesion: SessionBase | dict[str, Any]) -> None:
    """Limpia por completo todas las prendas del carrito en sesión.

    Qué hace:      Elimina la clave CLAVE_SESION_CARRITO de la sesión actual.
    Va hacia:      Modifica la sesión del cliente dejándola con 0 ítems.
    Depende de:    CLAVE_SESION_CARRITO.
    Cuándo usarla: Inmediatamente después de crear un pedido web con éxito.
    Si no opera:   No realiza ninguna acción si el carrito ya estaba vacío.
    """
    sesion.pop(CLAVE_SESION_CARRITO, None)
    if hasattr(sesion, "modified"):
        sesion.modified = True


def generar_codigo_pedido_unico() -> str:
    """Genera un código público aleatorio no adivinable tipo EMU-7K3Q9X (Pilar 1 Anti-IDOR).

    Qué hace:      Construye un código de 6 caracteres alfanuméricos sin ambiguos y verifica BD.
    Va hacia:      Retorna un str único para la columna PED_CCODIGO de TBL_TPEDIDO.
    Depende de:    secrets.choice y Pedido.objects.filter(codigo=...).exists().
    Cuándo usarla: Al crear un nuevo pedido web o una venta presencial.
    Si no opera:   Reintenta hasta encontrar un código libre en TBL_TPEDIDO.
    """
    for _ in range(25):
        sufijo = "".join(secrets.choice(ALFABETO_CODIGO_PEDIDO) for _ in range(6))
        codigo = f"EMU-{sufijo}"
        if not Pedido.objects.filter(codigo=codigo).exists():
            return codigo
    sufijo_largo = "".join(secrets.choice(ALFABETO_CODIGO_PEDIDO) for _ in range(8))
    return f"EMU-{sufijo_largo}"


def validar_turnstile_cloudflare(*, token: str, ip_cliente: str | None = None) -> bool:
    """Verifica el token antispam de Cloudflare Turnstile en el checkout (Requisito #17).

    Qué hace:      Valida el token contra el endpoint siteverify de Cloudflare o llave de prueba.
    Va hacia:      Retorna True si el desafío es válido o False si es un bot/token inválido.
    Depende de:    settings.TURNSTILE_SECRET_KEY.
    Cuándo usarla: Antes de procesar crear_pedido_web en el formulario de checkout.
    Si no opera:   Si el token está vacío o Cloudflare lo rechaza, retorna False.
    """
    llave_secreta = getattr(settings, "TURNSTILE_SECRET_KEY", "")
    # Llave oficial de prueba de Cloudflare ("Always passes"): 1x0000000000000000000000000000000AA
    if llave_secreta.startswith("1x00000000000000000000"):
        return token != "BOT_TOKEN_INVALIDO"

    if not token:
        return False

    datos = urllib.parse.urlencode(
        {
            "secret": llave_secreta,
            "response": token,
            "remoteip": ip_cliente or "",
        }
    ).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=datos,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=4) as respuesta:
            cuerpo = json.loads(respuesta.read().decode("utf-8"))
            return bool(cuerpo.get("success", False))
    except Exception:
        return False


@transaction.atomic
def crear_pedido_web(
    *,
    sesion: SessionBase | dict[str, Any],
    datos_cliente: dict[str, Any],
    ip_cliente: str | None = None,
) -> Pedido:
    """Crea un pedido web verificando antispam, stock, precios por mayor y modalidad de entrega.

    Qué hace:      Valida honeypot/Turnstile/DNI, recalcula precios en servidor y guarda el pedido.
    Va hacia:      Inserta en TBL_TPEDIDO, TBL_TPEDIDO_ITEM y TBL_LPEDIDO_ESTADO, y vacía sesión.
    Depende de:    obtener_carrito_detallado, Pedido, ItemPedido y RegistroEstadoPedido.
    Cuándo usarla: Al recibir el POST del formulario de checkout (/pedidos/checkout/).
    Si no opera:   Revierte la transacción y lanza EntradaInvalidaError o StockInsuficienteError.
    """
    # 1. Triple protección antispam: Honeypot + Privacidad Ley 29733 + Turnstile
    campo_trampa = str(datos_cliente.get("sitio_web", "")).strip()
    if campo_trampa:
        raise EntradaInvalidaError(
            "No pudimos procesar la solicitud (validación de seguridad antispam)."
        )

    acepta_privacidad = datos_cliente.get("acepta_privacidad")
    if acepta_privacidad not in (True, "true", "True", "1", "on"):
        raise EntradaInvalidaError(
            "Debes aceptar la Política de Privacidad (Ley N.º 29733) para enviar tu pedido."
        )

    token_turnstile = str(datos_cliente.get("cf_turnstile_response", "")).strip()
    if not validar_turnstile_cloudflare(token=token_turnstile, ip_cliente=ip_cliente):
        raise EntradaInvalidaError(
            "La verificación antispam de Cloudflare Turnstile expiró. Inténtalo de nuevo."
        )

    # 2. Verificar que el carrito no esté vacío y recalcular precios en el servidor
    carrito = obtener_carrito_detallado(sesion)
    if carrito["esta_vacio"]:
        raise EntradaInvalidaError(
            "Tu carrito está vacío. Agrega al menos una camiseta antes de continuar."
        )

    # 3. Validar datos personales y modalidad de entrega de Richard
    nombre = limpiar_texto_seguro(str(datos_cliente.get("cliente_nombre", "")), longitud_maxima=150)
    if not nombre or len(nombre) < 3:
        raise EntradaInvalidaError("Ingresa tus nombres y apellidos completos.")

    telefono_crudo = str(datos_cliente.get("cliente_telefono", "")).strip()
    try:
        telefono = validar_telefono_peruano(telefono_crudo)
    except Exception as exc:
        raise EntradaInvalidaError(
            "Ingresa un número de celular peruano válido de 9 dígitos que empiece con 9."
        ) from exc

    tipo_entrega = str(
        datos_cliente.get("tipo_entrega", TipoEntrega.PUNTO_ENCUENTRO)
    ).strip().upper()
    if tipo_entrega not in TipoEntrega.values:
        raise EntradaInvalidaError("Selecciona una modalidad de entrega válida.")

    dni_crudo = str(datos_cliente.get("cliente_dni", "")).strip()
    dni_limpio: str | None = None
    if dni_crudo:
        try:
            dni_limpio = validar_dni_peruano(dni_crudo)
        except Exception as exc:
            raise EntradaInvalidaError("El DNI debe tener exactamente 8 dígitos numéricos.") from exc

    agencia: str | None = None
    agencia_ciudad: str | None = None
    agencia_referencia: str | None = None
    punto_encuentro: str | None = None
    entrega_programada: datetime | None = None

    if tipo_entrega == TipoEntrega.AGENCIA:
        if not dni_limpio:
            raise DatosEnvioIncompletosError(
                "Para envíos a provincia por agencia (Shalom / Olva) el DNI de 8 dígitos es obligatorio."
            )
        agencia_cand = str(datos_cliente.get("agencia", "")).strip().upper()
        if agencia_cand not in AgenciaEnvio.values:
            raise DatosEnvioIncompletosError(
                "Selecciona la agencia de transporte (Shalom, Olva u Otra)."
            )
        agencia = agencia_cand
        agencia_ciudad = limpiar_texto_seguro(
            str(datos_cliente.get("agencia_ciudad", "")), longitud_maxima=80
        )
        if not agencia_ciudad:
            raise DatosEnvioIncompletosError(
                "Indica la ciudad o provincia de destino para el envío por agencia."
            )
        agencia_referencia = limpiar_texto_seguro(
            str(datos_cliente.get("agencia_referencia", "")), longitud_maxima=200
        )
        if not agencia_referencia:
            raise DatosEnvioIncompletosError(
                "Indica la sede o referencia de la agencia donde recogerás tu pedido."
            )

    elif tipo_entrega == TipoEntrega.PUNTO_ENCUENTRO:
        punto_encuentro = limpiar_texto_seguro(
            str(datos_cliente.get("punto_encuentro", "")), longitud_maxima=200
        )
        if not punto_encuentro:
            raise DatosEnvioIncompletosError(
                "Indica el punto de encuentro en Lima (ej. Estación La Cultura, Mall del Sur, Centro Cívico)."
            )
        fecha_prog_str = str(datos_cliente.get("entrega_programada", "")).strip()
        if fecha_prog_str:
            try:
                dt_ingresada = datetime.fromisoformat(fecha_prog_str)
                if timezone.is_naive(dt_ingresada):
                    entrega_programada = timezone.make_aware(dt_ingresada)
                else:
                    entrega_programada = dt_ingresada
            except ValueError:
                entrega_programada = None

    elif tipo_entrega == TipoEntrega.DELIVERY_LIMA:
        punto_encuentro = limpiar_texto_seguro(
            str(datos_cliente.get("punto_encuentro", "")), longitud_maxima=200
        )
        if not punto_encuentro:
            raise DatosEnvioIncompletosError(
                "Indica tu dirección y distrito en Lima para cotizar el delivery."
            )

    elif tipo_entrega == TipoEntrega.RECOJO:
        punto_encuentro = limpiar_texto_seguro(
            str(datos_cliente.get("punto_encuentro", "Recojo coordinado con Richard")),
            longitud_maxima=200,
        )

    notas = limpiar_texto_seguro(str(datos_cliente.get("notas", "")), longitud_maxima=500)

    # 4. Validar stock actual en base de datos para cada línea del carrito
    for linea in carrito["items"]:
        var_bd = Variante.objects.select_related("producto").get(id=linea["variante_id"])
        if not var_bd.activa or not var_bd.producto.activo:
            raise StockInsuficienteError(
                f"La prenda {linea['nombre_producto']} ya no se encuentra disponible."
            )
        if linea["cantidad"] > var_bd.cantidad_stock:
            raise StockInsuficienteError(
                f"Stock insuficiente para {linea['nombre_producto']} en talla {linea['talla']} "
                f"(disponible: {var_bd.cantidad_stock})."
            )

    # 5. Determinar estado inicial y costo de envío según doc 02 y doc 03
    ahora = timezone.now()
    if tipo_entrega in (TipoEntrega.PUNTO_ENCUENTRO, TipoEntrega.RECOJO):
        estado_inicial = EstadoPedido.COTIZADO
        costo_envio_inicial = Decimal("0.00")
        fecha_cotizado_inicial = ahora
        nota_bitacora = (
            "Pedido creado en web con envío S/ 0.00 (Punto de encuentro / Recojo)."
        )
    else:
        estado_inicial = EstadoPedido.NUEVO
        costo_envio_inicial = None
        fecha_cotizado_inicial = None
        nota_bitacora = "Pedido recibido desde la web; pendiente cotizar costo de envío."

    subtotal_pedido: Decimal = carrito["subtotal"]
    total_pedido = subtotal_pedido + (costo_envio_inicial or Decimal("0.00"))

    pedido = Pedido.objects.create(
        codigo=generar_codigo_pedido_unico(),
        estado=estado_inicial,
        origen=OrigenPedido.WEB,
        cliente_nombre=nombre,
        cliente_dni=dni_limpio,
        cliente_telefono=telefono,
        tipo_entrega=tipo_entrega,
        agencia=agencia,
        agencia_ciudad=agencia_ciudad,
        agencia_referencia=agencia_referencia,
        punto_encuentro=punto_encuentro,
        entrega_programada=entrega_programada,
        subtotal=subtotal_pedido,
        costo_envio=costo_envio_inicial,
        total=total_pedido,
        notas=notas or None,
        fecha_cotizado=fecha_cotizado_inicial,
    )

    # 6. Crear ítems con copia (snapshot) inmutable de nombre, SKU, talla y precio
    for linea in carrito["items"]:
        ItemPedido.objects.create(
            pedido=pedido,
            variante_id=linea["variante_id"],
            nombre_producto=linea["nombre_producto"],
            sku=linea["sku"],
            talla=linea["talla"],
            color=linea["color"] or "",
            precio_unidad=linea["precio_unidad"],
            cantidad=linea["cantidad"],
            subtotal=linea["subtotal"],
        )

    # 7. Registrar evento inicial en la bitácora inmutable TBL_LPEDIDO_ESTADO
    RegistroEstadoPedido.objects.create(
        pedido=pedido,
        estado_anterior=None,
        estado_nuevo=estado_inicial,
        cambiado_por=None,
        nota=nota_bitacora,
    )

    # 8. Vaciar el carrito de la sesión
    vaciar_carrito(sesion)
    return pedido


def generar_pdf_pedido(*, codigo: str) -> bytes:
    """Genera el comprobante profesional en PDF de un pedido usando ReportLab (doc 02).

    Qué hace:      Dibuja cabecera deportiva Emuná Sport, datos de entrega, tabla de ítems y totales.
    Va hacia:      Retorna los bytes del documento PDF listo para descargar o enviar por WhatsApp.
    Depende de:    obtener_pedido_por_codigo, obtener_configuracion_tienda y reportlab.
    Cuándo usarla: En la vista GET /pedidos/<codigo>/pdf/ y en el endpoint API de PDF.
    Si no opera:   Lanza Http404 si el código del pedido no existe.
    """
    pedido = obtener_pedido_por_codigo(codigo=codigo)
    config = obtener_configuracion_tienda()
    items = list(pedido.items.all())
    total_prendas = sum(i.cantidad for i in items)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4

    color_ink = colors.HexColor("#0A0A0A")
    color_neon = colors.HexColor("#39FF14")
    color_neon_oscuro = colors.HexColor("#1B8F2A")
    color_plata = colors.HexColor("#C9CED3")
    color_gris_texto = colors.HexColor("#4B5563")

    # 1. Franja superior negra deportiva (#0A0A0A) con línea inferior verde neón (#39FF14)
    c.setFillColor(color_ink)
    c.rect(0, alto - 38 * mm, ancho, 38 * mm, stroke=0, fill=1)
    c.setFillColor(color_neon)
    c.rect(0, alto - 39.5 * mm, ancho, 1.5 * mm, stroke=0, fill=1)

    # Inclusión del logo oficial transparente de Emuná Sport
    ruta_logo = Path(settings.BASE_DIR) / "static" / "logo_emuna_transparente.png"
    if not ruta_logo.exists():
        ruta_logo = (
            Path(settings.REPO_DIR) / "03-Diseno-Tecnico" / "assets" / "logo_emuna_transparente.png"
        )

    if ruta_logo.exists():
        try:
            c.drawImage(
                str(ruta_logo),
                18 * mm,
                alto - 35 * mm,
                width=24 * mm,
                height=24 * mm,
                mask="auto",
                preserveAspectRatio=True,
            )
            x_texto_header = 46 * mm
        except Exception:
            x_texto_header = 18 * mm
    else:
        x_texto_header = 18 * mm

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(x_texto_header, alto - 17 * mm, (config.nombre or "EMUNÁ SPORT").upper())

    c.setFillColor(color_neon)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x_texto_header, alto - 23 * mm, "ESTILO DEPORTIVO · COMPROBANTE DE PEDIDO")

    c.setFillColor(colors.white)
    c.setFont("Helvetica", 8.5)
    c.drawString(
        x_texto_header,
        alto - 29 * mm,
        f"Atención WhatsApp: +51 {config.numero_whatsapp}",
    )

    # Caja derecha en cabecera con el código del pedido
    c.setFillColor(color_neon)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(ancho - 18 * mm, alto - 17 * mm, f"PEDIDO: {pedido.codigo}")

    fecha_local = timezone.localtime(pedido.fecha_creacion).strftime("%d/%m/%Y %H:%M")
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 8.5)
    c.drawRightString(ancho - 18 * mm, alto - 23 * mm, f"Fecha: {fecha_local} (Hora Perú)")
    c.drawRightString(
        ancho - 18 * mm,
        alto - 29 * mm,
        f"Estado: {pedido.get_estado_display().upper()}",
    )

    # 2. Bloque de datos del cliente y modalidad de entrega (sin DNI completo por privacidad)
    y = alto - 52 * mm
    tiene_notas = bool(pedido.notas and pedido.notas.strip())
    altura_caja = 36 * mm if tiene_notas else 30 * mm

    c.setStrokeColor(color_plata)
    c.setFillColor(colors.HexColor("#F9FAFB"))
    c.rect(18 * mm, y - altura_caja, ancho - 36 * mm, altura_caja, stroke=1, fill=1)

    c.setFillColor(color_ink)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(23 * mm, y - 7 * mm, "DATOS DEL CLIENTE Y MODALIDAD DE ENTREGA")

    if pedido.dni_enmascarado:
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(color_ink)
        c.drawRightString(ancho - 23 * mm, y - 7 * mm, f"DNI: {pedido.dni_enmascarado}")

    # Modalidad y agencia específica
    logo_agencia_nombre = None
    if pedido.tipo_entrega == TipoEntrega.AGENCIA:
        if pedido.agencia == AgenciaEnvio.SHALOM:
            modalidad_texto = "Envío a provincia por Agencia Shalom"
            logo_agencia_nombre = "shalom_logo.png"
        elif pedido.agencia == AgenciaEnvio.OLVA:
            modalidad_texto = "Envío a provincia por Olva Courier"
            logo_agencia_nombre = "Olva_logo.png"
        else:
            modalidad_texto = (
                f"Envío a provincia por {pedido.get_agencia_display() if pedido.agencia else 'Agencia'}"
            )
        detalle_lugar = (
            f"Destino ({pedido.get_agencia_display() if pedido.agencia else 'Agencia'}): "
            f"{pedido.agencia_ciudad or ''} – {pedido.agencia_referencia or ''}"
        )
    else:
        modalidad_texto = pedido.get_tipo_entrega_display()
        detalle_lugar = f"Lugar / Dirección: {pedido.punto_encuentro or 'Coordinado por WhatsApp'}"

    # Logo oficial de la agencia si corresponde
    if logo_agencia_nombre:
        ruta_logo_agencia = Path(settings.STATICFILES_DIRS[0]) / logo_agencia_nombre
        if not ruta_logo_agencia.exists():
            ruta_logo_agencia = (
                Path(settings.REPO_DIR) / "03-Diseno-Tecnico" / "assets" / logo_agencia_nombre
            )
        if ruta_logo_agencia.exists():
            try:
                c.drawImage(
                    str(ruta_logo_agencia),
                    ancho - 55 * mm,
                    y - (altura_caja - 4 * mm),
                    width=32 * mm,
                    height=14 * mm,
                    mask="auto",
                    preserveAspectRatio=True,
                )
            except Exception:
                pass

    limite_chars = 72 if logo_agencia_nombre else 95

    c.setFont("Helvetica", 9)
    c.setFillColor(color_gris_texto)
    c.drawString(23 * mm, y - 13.5 * mm, f"Cliente: {pedido.cliente_nombre or 'Venta presencial'}")
    c.drawString(23 * mm, y - 19.5 * mm, f"Modalidad: {modalidad_texto}")
    c.drawString(23 * mm, y - 25.5 * mm, detalle_lugar[:limite_chars])

    if tiene_notas:
        c.drawString(
            23 * mm,
            y - 31.5 * mm,
            f"Nota / Observación: {pedido.notas.strip()[:limite_chars]}",
        )

    # 3. Tabla de camisetas solicitadas
    y = y - altura_caja - 8 * mm
    c.setFillColor(color_ink)
    c.rect(18 * mm, y - 8 * mm, ancho - 36 * mm, 8 * mm, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(21 * mm, y - 5.5 * mm, "CAMISETA / PRODUCTO")
    c.drawString(108 * mm, y - 5.5 * mm, "TALLA")
    c.drawRightString(138 * mm, y - 5.5 * mm, "CANT.")
    c.drawRightString(163 * mm, y - 5.5 * mm, "P. UNIT.")
    c.drawRightString(ancho - 21 * mm, y - 5.5 * mm, "SUBTOTAL")

    y = y - 8 * mm

    for idx, item in enumerate(items):
        if y < 75 * mm:
            c.showPage()
            y = alto - 25 * mm

        altura_fila = 11 * mm
        if idx % 2 == 1:
            c.setFillColor(colors.HexColor("#F9FAFB"))
            c.rect(18 * mm, y - altura_fila, ancho - 36 * mm, altura_fila, stroke=0, fill=1)

        c.setStrokeColor(color_plata)
        c.line(18 * mm, y - altura_fila, ancho - 18 * mm, y - altura_fila)

        c.setFillColor(color_ink)
        c.setFont("Helvetica-Bold", 9)
        nombre_corto = item.nombre_producto[:38]
        c.drawString(21 * mm, y - 4.5 * mm, nombre_corto)

        c.setFont("Helvetica", 7.5)
        c.setFillColor(color_gris_texto)
        c.drawString(21 * mm, y - 8.5 * mm, f"SKU: {item.sku}")

        c.setFillColor(color_ink)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(108 * mm, y - 6 * mm, item.talla)
        c.drawRightString(136 * mm, y - 6 * mm, str(item.cantidad))
        c.drawRightString(163 * mm, y - 6 * mm, f"S/ {item.precio_unidad:.2f}")
        c.drawRightString(ancho - 21 * mm, y - 6 * mm, f"S/ {item.subtotal:.2f}")
        y -= altura_fila

    # 4. Resumen de totales y línea de envío sin colisiones
    y -= 6 * mm
    c.setFillColor(color_ink)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(21 * mm, y - 4 * mm, f"Total de prendas en el pedido: {total_prendas} unid.")

    x_etiqueta_total = 108 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(color_gris_texto)
    c.drawString(x_etiqueta_total, y - 4 * mm, "Subtotal camisetas:")
    c.setFillColor(color_ink)
    c.drawRightString(ancho - 21 * mm, y - 4 * mm, f"S/ {pedido.subtotal:.2f}")

    y -= 6.5 * mm
    c.setFillColor(color_gris_texto)
    c.drawString(x_etiqueta_total, y - 4 * mm, "Envío / Entrega:")
    c.setFillColor(color_ink)
    if pedido.costo_envio is None:
        texto_envio = "Por cotizar por Richard"
    elif pedido.costo_envio == Decimal("0.00"):
        texto_envio = "S/ 0.00 (Gratis)"
    else:
        texto_envio = f"S/ {pedido.costo_envio:.2f}"
    c.drawRightString(ancho - 21 * mm, y - 4 * mm, texto_envio)

    y -= 9 * mm
    c.setFillColor(color_ink)
    c.rect(106 * mm, y - 6 * mm, ancho - 124 * mm, 9.5 * mm, stroke=0, fill=1)
    c.setFillColor(color_neon)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(110 * mm, y - 3 * mm, "TOTAL FINAL:")
    c.drawRightString(ancho - 21 * mm, y - 3 * mm, f"S/ {pedido.total:.2f}")

    # 5. Pie de página profesional con instrucciones claras
    c.setStrokeColor(color_plata)
    c.line(18 * mm, 28 * mm, ancho - 18 * mm, 28 * mm)
    c.setFillColor(color_neon_oscuro)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(
        18 * mm,
        22 * mm,
        "¿Cómo continuar? Envía este código o comprobante al WhatsApp de Richard para coordinar tu entrega o pago con Yape.",
    )
    c.setFillColor(color_gris_texto)
    c.setFont("Helvetica", 8)
    c.drawString(
        18 * mm,
        16 * mm,
        f"{config.nombre} – Estilo deportivo | WhatsApp oficial: +51 {config.numero_whatsapp} | Código de seguimiento: {pedido.codigo}",
    )

    c.showPage()
    c.save()
    return buffer.getvalue()
