"""Selectores de lectura y cálculo de métricas/alertas del Tablero de Richard."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db.models import Count, DecimalField, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.urls import reverse
from django.utils import timezone

from apps.catalogo.models import Producto, Variante
from apps.nucleo.selectores import obtener_configuracion_tienda
from apps.pedidos.models import EstadoPedido, ItemPedido, OrigenPedido, Pedido
from apps.pedidos.servicios import construir_enlace_whatsapp_notificacion_cliente

ESTADOS_VENTA_CONFIRMADA = (
    EstadoPedido.PAGADO,
    EstadoPedido.ENVIADO,
    EstadoPedido.ENTREGADO,
)

ETIQUETAS_PERIODO = {
    "hoy": "Hoy",
    "7dias": "Últimos 7 días",
    "mes": "Este mes",
    "todo": "Todo el historial",
    "personalizado": "Rango personalizado",
}


def _parsear_fecha(valor: date | str | None) -> date | None:
    """Convierte una fecha en texto ISO (YYYY-MM-DD) o date a objeto date válido.

    Qué hace:      Normaliza entradas de query params o llamadas directas de Python.
    Va hacia:      Retorna un objeto date o None si la entrada es vacía o inválida.
    Depende de:    datetime.date.fromisoformat.
    Cuándo usarla: En resolver_rango_fechas() antes de construir límites de consulta.
    Si no opera:   Retorna None de forma segura sin lanzar excepciones por formatos rotos.
    """
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str) and valor.strip():
        try:
            return date.fromisoformat(valor.strip())
        except ValueError:
            return None
    return None


def resolver_rango_fechas(
    periodo: str | None = None,
    desde: date | str | None = None,
    hasta: date | str | None = None,
) -> tuple[date, date, str]:
    """Determina el rango inclusivo de fechas (desde, hasta) y la clave de período activa.

    Qué hace:      Interpreta presets ('hoy', '7dias', 'mes', 'todo') o fechas personalizadas.
    Va hacia:      Retorna una tupla (fecha_desde, fecha_hasta, codigo_periodo).
    Depende de:    django.utils.timezone.localdate y _parsear_fecha.
    Cuándo usarla: Al iniciar obtener_resumen_tablero() y al exportar ventas en CSV.
    Si no opera:   Si las fechas llegan invertidas, las ordena automáticamente (desde <= hasta).
    """
    hoy = timezone.localdate()
    fecha_desde_param = _parsear_fecha(desde)
    fecha_hasta_param = _parsear_fecha(hasta)

    if fecha_desde_param or fecha_hasta_param:
        fecha_inicio = fecha_desde_param or hoy.replace(day=1)
        fecha_fin = fecha_hasta_param or hoy
        if fecha_inicio > fecha_fin:
            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
        codigo = periodo if periodo in ETIQUETAS_PERIODO else "personalizado"
        return fecha_inicio, fecha_fin, codigo

    clave = (periodo or "mes").strip().lower()
    if clave == "hoy":
        return hoy, hoy, "hoy"
    if clave == "7dias":
        return hoy - timedelta(days=6), hoy, "7dias"
    if clave == "todo":
        primer_pedido = Pedido.objects.order_by("fecha_creacion").values_list(
            "fecha_creacion", flat=True
        ).first()
        fecha_inicio = (
            timezone.localtime(primer_pedido).date() if primer_pedido else hoy.replace(day=1)
        )
        if fecha_inicio > hoy:
            fecha_inicio = hoy
        return fecha_inicio, hoy, "todo"

    return hoy.replace(day=1), hoy, "mes"


def listar_alertas_stock_bajo() -> list[dict[str, Any]]:
    """Lista las variantes activas con stock agotado o menor/igual a su umbral mínimo.

    Qué hace:      Consulta TBL_RVARIANTE y compara cantidad_stock contra umbral propio o global.
    Va hacia:      Retorna una lista de diccionarios ordenada por criticidad (stock ascendente).
    Depende de:    Variante, ConfiguracionTienda y reverse('admin:catalogo_variante_change').
    Cuándo usarla: En el tablero operativo, endpoint de alertas y exportación CSV de stock.
    Si no opera:   Retorna lista vacía si todas las variantes activas tienen stock saludable.
    """
    config = obtener_configuracion_tienda()
    variantes = (
        Variante.objects.select_related("producto", "producto__categoria")
        .filter(activa=True, producto__activo=True)
        .annotate(
            umbral_efectivo=Coalesce(
                "umbral_stock_bajo",
                Value(config.umbral_stock_bajo),
                output_field=IntegerField(),
            )
        )
        .filter(cantidad_stock__lte=F("umbral_efectivo"))
        .order_by("cantidad_stock", "producto__nombre", "talla")
    )

    alertas: list[dict[str, Any]] = []
    for var in variantes:
        umbral = int(var.umbral_efectivo)
        nivel = "ROJO" if var.cantidad_stock <= 0 else "AMBAR"
        deficit = max(0, umbral - var.cantidad_stock)
        alertas.append(
            {
                "variante_id": var.id,
                "producto_id": var.producto_id,
                "producto_nombre": var.producto.nombre,
                "categoria_nombre": var.producto.categoria.nombre,
                "talla": var.talla,
                "color": var.color or "",
                "sku": var.sku,
                "cantidad_stock": var.cantidad_stock,
                "umbral_efectivo": umbral,
                "deficit": deficit,
                "nivel": nivel,
                "url_admin": reverse("admin:catalogo_variante_change", args=[var.id]),
            }
        )
    return alertas


def listar_pedidos_pendientes_antiguos(
    horas_limite: int | None = None,
) -> list[dict[str, Any]]:
    """Obtiene pedidos NUEVO o COTIZADO que superan el límite de horas sin ser pagados.

    Qué hace:      Filtra TBL_TPEDIDO por estados iniciales con fecha_creacion anterior al corte.
    Va hacia:      Retorna lista ordenada del más antiguo al más reciente con enlace WhatsApp.
    Depende de:    Pedido, obtener_configuracion_tienda y construir_enlace_whatsapp_notificacion_cliente.
    Cuándo usarla: En el bloque de alertas urgentes de pedidos pendientes en el tablero de Richard.
    Si no opera:   Retorna lista vacía si todos los pedidos recientes están dentro del plazo.
    """
    config = obtener_configuracion_tienda()
    horas = horas_limite if horas_limite is not None else config.horas_pedido_pendiente
    ahora = timezone.now()
    corte = ahora - timedelta(hours=horas)

    pedidos = (
        Pedido.objects.filter(
            estado__in=(EstadoPedido.NUEVO, EstadoPedido.COTIZADO),
            fecha_creacion__lte=corte,
        )
        .order_by("fecha_creacion")
    )

    base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    resultado: list[dict[str, Any]] = []
    for ped in pedidos:
        horas_espera = max(1, int((ahora - ped.fecha_creacion).total_seconds() // 3600))
        tipo_notif = "COTIZADO" if ped.estado == EstadoPedido.COTIZADO else "GENERAL"
        url_publica = f"{base_url}{reverse('pedidos:detalle_pedido', args=[ped.codigo])}"
        resultado.append(
            {
                "id": ped.id,
                "codigo": ped.codigo,
                "estado": ped.estado,
                "estado_label": ped.get_estado_display(),
                "tipo_entrega_label": ped.get_tipo_entrega_display(),
                "cliente_nombre": ped.cliente_nombre or "Cliente presencial",
                "cliente_telefono": ped.cliente_telefono or "—",
                "total": ped.total,
                "fecha_creacion": ped.fecha_creacion,
                "horas_espera": horas_espera,
                "url_admin": reverse("admin:pedidos_pedido_change", args=[ped.id]),
                "url_whatsapp": construir_enlace_whatsapp_notificacion_cliente(
                    pedido=ped,
                    tipo_notificacion=tipo_notif,
                    url_publica_pedido=url_publica,
                ),
            }
        )
    return resultado


def obtener_resumen_tablero(
    desde: date | str | None = None,
    hasta: date | str | None = None,
    periodo: str | None = None,
) -> dict[str, Any]:
    """Calcula todas las métricas de ventas y alertas operativas para el tablero de Richard.

    Qué hace:      Consolida ingresos Web/POS, ticket promedio, evolución diaria y 4 grupos de alertas.
    Va hacia:      Retorna un diccionario estructurado consumible por vistas HTML, CSV y API REST.
    Depende de:    Pedido, ItemPedido, Producto, Variante y ConfiguracionTienda.
    Cuándo usarla: Al renderizar /gestion/tablero/ o responder GET /api/v1/admin/tablero/resumen/.
    Si no opera:   Retorna métricas en Decimal('0.00') y listas vacías sin fallar si no hay datos.
    """
    config = obtener_configuracion_tienda()
    fecha_desde, fecha_hasta, periodo_activo = resolver_rango_fechas(
        periodo=periodo, desde=desde, hasta=hasta
    )

    zona_actual = timezone.get_current_timezone()
    inicio_dt = timezone.make_aware(datetime.combine(fecha_desde, time.min), zona_actual)
    fin_dt = timezone.make_aware(
        datetime.combine(fecha_hasta + timedelta(days=1), time.min),
        zona_actual,
    )

    pedidos_periodo_qs = (
        Pedido.objects.filter(estado__in=ESTADOS_VENTA_CONFIRMADA)
        .annotate(fecha_efectiva=Coalesce("fecha_pagado", "fecha_creacion"))
        .filter(fecha_efectiva__gte=inicio_dt, fecha_efectiva__lt=fin_dt)
    )

    agregado_ventas = pedidos_periodo_qs.aggregate(
        total_ventas=Coalesce(
            Sum("total"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        cantidad_pedidos=Count("id"),
        ventas_web=Coalesce(
            Sum("total", filter=Q(origen=OrigenPedido.WEB)),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        pedidos_web=Count("id", filter=Q(origen=OrigenPedido.WEB)),
        ventas_presencial=Coalesce(
            Sum("total", filter=Q(origen=OrigenPedido.PRESENCIAL)),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        pedidos_presencial=Count("id", filter=Q(origen=OrigenPedido.PRESENCIAL)),
    )

    items_periodo_qs = ItemPedido.objects.filter(pedido__in=pedidos_periodo_qs)
    unidades_vendidas = int(
        items_periodo_qs.aggregate(total_unid=Coalesce(Sum("cantidad"), Value(0)))["total_unid"]
    )

    cantidad_pedidos = int(agregado_ventas["cantidad_pedidos"])
    total_ventas = Decimal(agregado_ventas["total_ventas"]).quantize(Decimal("0.01"))
    ticket_promedio = (
        (total_ventas / Decimal(cantidad_pedidos)).quantize(Decimal("0.01"))
        if cantidad_pedidos > 0
        else Decimal("0.00")
    )

    # Ranking de productos más vendidos en el período
    mas_vendidos_raw = (
        items_periodo_qs.values(
            "variante__producto_id",
            "variante__producto__nombre",
            "variante__producto__sku",
        )
        .annotate(
            unidades=Coalesce(Sum("cantidad"), Value(0)),
            ingresos=Coalesce(
                Sum("subtotal"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        .order_by("-unidades", "-ingresos", "variante__producto__nombre")[:10]
    )
    mas_vendidos: list[dict[str, Any]] = []
    for idx, fila in enumerate(mas_vendidos_raw, start=1):
        pid = fila["variante__producto_id"]
        mas_vendidos.append(
            {
                "posicion": idx,
                "producto_id": pid,
                "nombre": fila["variante__producto__nombre"],
                "sku": fila["variante__producto__sku"],
                "unidades": int(fila["unidades"]),
                "ingresos": Decimal(fila["ingresos"]).quantize(Decimal("0.01")),
                "url_admin": reverse("admin:catalogo_producto_change", args=[pid]),
            }
        )

    # Productos activos sin ninguna venta confirmada en los últimos N días configurados
    corte_sin_ventas = timezone.now() - timedelta(days=config.dias_sin_ventas)
    productos_con_venta_ids = (
        ItemPedido.objects.filter(
            pedido__estado__in=ESTADOS_VENTA_CONFIRMADA,
        )
        .annotate(fecha_efectiva=Coalesce("pedido__fecha_pagado", "pedido__fecha_creacion"))
        .filter(fecha_efectiva__gte=corte_sin_ventas)
        .values_list("variante__producto_id", flat=True)
        .distinct()
    )
    sin_ventas_qs = (
        Producto.objects.select_related("categoria")
        .filter(activo=True, categoria__activa=True)
        .exclude(id__in=productos_con_venta_ids)
        .annotate(stock_total=Coalesce(Sum("variantes__cantidad_stock"), Value(0)))
        .order_by("-stock_total", "nombre")
    )
    productos_sin_ventas = [
        {
            "producto_id": prod.id,
            "nombre": prod.nombre,
            "sku": prod.sku,
            "categoria_nombre": prod.categoria.nombre,
            "precio_unidad": prod.precio_unidad,
            "stock_total": int(prod.stock_total),
            "url_admin": reverse("admin:catalogo_producto_change", args=[prod.id]),
        }
        for prod in sin_ventas_qs
    ]

    # Evolución diaria del período
    ventas_diarias_raw = (
        pedidos_periodo_qs.annotate(dia=TruncDate("fecha_efectiva", tzinfo=zona_actual))
        .values("dia")
        .annotate(
            pedidos=Count("id"),
            monto_total=Coalesce(
                Sum("total"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            monto_web=Coalesce(
                Sum("total", filter=Q(origen=OrigenPedido.WEB)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            monto_presencial=Coalesce(
                Sum("total", filter=Q(origen=OrigenPedido.PRESENCIAL)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        .order_by("-dia")
    )
    max_dia = max((Decimal(d["monto_total"]) for d in ventas_diarias_raw), default=Decimal("0.00"))
    ventas_por_dia = []
    for fila in ventas_diarias_raw:
        total_dia = Decimal(fila["monto_total"]).quantize(Decimal("0.01"))
        porcentaje_barra = int((total_dia / max_dia) * 100) if max_dia > 0 else 0
        ventas_por_dia.append(
            {
                "fecha": fila["dia"],
                "pedidos": int(fila["pedidos"]),
                "web": Decimal(fila["monto_web"]).quantize(Decimal("0.01")),
                "presencial": Decimal(fila["monto_presencial"]).quantize(Decimal("0.01")),
                "total": total_dia,
                "porcentaje_barra": porcentaje_barra,
            }
        )

    # Cola operativa en tiempo real (todos los pedidos activos por estado)
    conteo_estados = {
        fila["estado"]: int(fila["cantidad"])
        for fila in Pedido.objects.values("estado").annotate(cantidad=Count("id"))
    }
    cola_operativa = {
        "nuevo": conteo_estados.get(EstadoPedido.NUEVO, 0),
        "cotizado": conteo_estados.get(EstadoPedido.COTIZADO, 0),
        "pagado": conteo_estados.get(EstadoPedido.PAGADO, 0),
        "enviado": conteo_estados.get(EstadoPedido.ENVIADO, 0),
        "entregado": conteo_estados.get(EstadoPedido.ENTREGADO, 0),
    }

    alertas_stock = listar_alertas_stock_bajo()
    pendientes_antiguos = listar_pedidos_pendientes_antiguos(
        horas_limite=config.horas_pedido_pendiente
    )

    # Ranking de Clientes VIP y Recurrentes a partir de los campos principales (Nombre, Teléfono, DNI)
    mapa_clientes: dict[str, dict[str, Any]] = {}
    pedidos_clientes_raw = (
        pedidos_periodo_qs.annotate(
            unidades_pedido=Coalesce(Sum("items__cantidad"), Value(0))
        )
        .values("cliente_nombre", "cliente_telefono", "cliente_dni", "total", "unidades_pedido")
        .order_by("fecha_creacion")
    )
    url_changelist_pedidos = reverse("admin:pedidos_pedido_changelist")
    for ped_c in pedidos_clientes_raw:
        tel = (ped_c["cliente_telefono"] or "").strip()
        nom = (ped_c["cliente_nombre"] or "").strip()
        dni = (ped_c["cliente_dni"] or "").strip()
        if not tel and (not nom or nom.lower() == "venta presencial"):
            continue
        clave_cliente = tel if tel else f"NOM:{nom.upper()}"
        if clave_cliente not in mapa_clientes:
            busqueda_q = tel or nom
            mapa_clientes[clave_cliente] = {
                "nombre": nom or "Cliente Registrado",
                "telefono": tel,
                "dni": dni,
                "pedidos": 0,
                "unidades": 0,
                "total_gastado": Decimal("0.00"),
                "url_historial": f"{url_changelist_pedidos}?q={busqueda_q}",
                "url_whatsapp": f"https://api.whatsapp.com/send?phone=51{tel}" if tel else "",
            }
        registro_cli = mapa_clientes[clave_cliente]
        if nom and nom.lower() != "venta presencial":
            registro_cli["nombre"] = nom
        if dni and not registro_cli["dni"]:
            registro_cli["dni"] = dni
        registro_cli["pedidos"] += 1
        registro_cli["unidades"] += int(ped_c["unidades_pedido"] or 0)
        registro_cli["total_gastado"] = (
            registro_cli["total_gastado"] + Decimal(ped_c["total"] or Decimal("0.00"))
        ).quantize(Decimal("0.01"))

    clientes_vip = sorted(
        mapa_clientes.values(),
        key=lambda c: (c["total_gastado"], c["pedidos"], c["unidades"]),
        reverse=True,
    )[:10]
    for idx_cli, cli in enumerate(clientes_vip, start=1):
        cli["posicion"] = idx_cli
        cli["es_vip_recurrente"] = cli["pedidos"] >= 2 or cli["unidades"] >= 3

    return {
        "configuracion": config,
        "periodo_activo": periodo_activo,
        "etiqueta_periodo": ETIQUETAS_PERIODO.get(periodo_activo, "Este mes"),
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "kpis": {
            "total_ventas": total_ventas,
            "cantidad_pedidos": cantidad_pedidos,
            "unidades_vendidas": unidades_vendidas,
            "ticket_promedio": ticket_promedio,
            "ventas_web": Decimal(agregado_ventas["ventas_web"]).quantize(Decimal("0.01")),
            "pedidos_web": int(agregado_ventas["pedidos_web"]),
            "ventas_presencial": Decimal(agregado_ventas["ventas_presencial"]).quantize(
                Decimal("0.01")
            ),
            "pedidos_presencial": int(agregado_ventas["pedidos_presencial"]),
        },
        "cola_operativa": cola_operativa,
        "alertas_stock": alertas_stock,
        "total_variantes_agotadas": sum(1 for a in alertas_stock if a["nivel"] == "ROJO"),
        "total_variantes_bajo_umbral": sum(1 for a in alertas_stock if a["nivel"] == "AMBAR"),
        "pedidos_pendientes_antiguos": pendientes_antiguos,
        "mas_vendidos": mas_vendidos,
        "clientes_vip": clientes_vip,
        "productos_sin_ventas": productos_sin_ventas,
        "ventas_por_dia": ventas_por_dia,
        "dias_sin_ventas_limite": config.dias_sin_ventas,
        "horas_pendiente_limite": config.horas_pedido_pendiente,
    }


def listar_pedidos_ventas_para_csv(
    desde: date | str | None = None,
    hasta: date | str | None = None,
    periodo: str | None = None,
) -> tuple[list[Pedido], date, date]:
    """Obtiene los pedidos con venta confirmada dentro del período para exportación CSV.

    Qué hace:      Consulta TBL_TPEDIDO con prefetch de items dentro del rango de fechas efectivo.
    Va hacia:      Retorna (lista de Pedido, fecha_desde, fecha_hasta) para servicios CSV.
    Depende de:    Pedido, resolver_rango_fechas y ESTADOS_VENTA_CONFIRMADA.
    Cuándo usarla: Desde apps.tablero.servicios.generar_csv_ventas().
    Si no opera:   Retorna lista vacía conservando las fechas resueltas del filtro.
    """
    fecha_desde, fecha_hasta, _ = resolver_rango_fechas(
        periodo=periodo, desde=desde, hasta=hasta
    )
    zona_actual = timezone.get_current_timezone()
    inicio_dt = timezone.make_aware(datetime.combine(fecha_desde, time.min), zona_actual)
    fin_dt = timezone.make_aware(
        datetime.combine(fecha_hasta + timedelta(days=1), time.min),
        zona_actual,
    )
    pedidos = list(
        Pedido.objects.prefetch_related("items")
        .filter(estado__in=ESTADOS_VENTA_CONFIRMADA)
        .annotate(fecha_efectiva=Coalesce("fecha_pagado", "fecha_creacion"))
        .filter(fecha_efectiva__gte=inicio_dt, fecha_efectiva__lt=fin_dt)
        .order_by("-fecha_efectiva", "-id")
    )
    return pedidos, fecha_desde, fecha_hasta
