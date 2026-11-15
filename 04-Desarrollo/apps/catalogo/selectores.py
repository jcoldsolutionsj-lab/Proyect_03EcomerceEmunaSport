"""Selectores optimizados de lectura del catálogo (cero consultas N+1)."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import DecimalField, Prefetch, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.nucleo.validadores import limpiar_texto_seguro

from .models import Categoria, ImagenProducto, Producto, ReglaPrecio, Variante

MAX_PRODUCTOS_DESTACADOS = 8


def listar_categorias_activas() -> QuerySet[Categoria]:
    """Devuelve todas las categorías activas ordenadas por su posición en el catálogo.

    Qué hace:      Filtra TBL_RCATEGORIA con activa=True y ordena por CAT_NORDEN y nombre.
    Va hacia:      Retorna un QuerySet de Categoria para los chips del inicio y el menú.
    Depende de:    apps.catalogo.models.Categoria.
    Cuándo usarla: En la portada, listado de productos y sitemap.
    Si no opera:   Retorna un QuerySet vacío si no hay categorías activas.
    """
    return Categoria.objects.filter(activa=True).order_by("orden", "nombre")


def listar_productos_catalogo(
    *,
    categoria_slug: str | None = None,
    talla: str | None = None,
    busqueda: str | None = None,
    solo_con_stock: bool = False,
    solo_destacados: bool = False,
) -> QuerySet[Producto]:
    """Consulta productos activos con sus fotos, tallas y stock total en una sola carga.

    Qué hace:      Aplica filtros de categoría, talla, texto y stock usando select_related y prefetch_related.
    Va hacia:      Retorna un QuerySet de Producto anotado con stock_total sin consultas N+1.
    Depende de:    Producto, ImagenProducto, Variante, ReglaPrecio y limpiar_texto_seguro.
    Cuándo usarla: En la vista principal del catálogo, buscador y endpoints públicos de lectura.
    Si no opera:   Retorna un QuerySet vacío si ningún producto coincide con los filtros.
    """
    qs = (
        Producto.objects.filter(activo=True, categoria__activa=True)
        .select_related("categoria")
        .prefetch_related(
            Prefetch(
                "imagenes",
                queryset=ImagenProducto.objects.order_by("-es_principal", "orden", "id"),
            ),
            Prefetch(
                "variantes",
                queryset=Variante.objects.filter(activa=True).order_by("id"),
            ),
            Prefetch(
                "reglas_precio",
                queryset=ReglaPrecio.objects.order_by("cantidad_minima"),
            ),
        )
        .annotate(
            stock_total=Coalesce(
                Sum("variantes__cantidad_stock", filter=Q(variantes__activa=True)),
                0,
            )
        )
    )

    if categoria_slug:
        slug_limpio = limpiar_texto_seguro(categoria_slug, longitud_maxima=100)
        qs = qs.filter(categoria__slug=slug_limpio)

    if talla:
        talla_limpia = limpiar_texto_seguro(talla, longitud_maxima=10).upper()
        qs = qs.filter(
            variantes__activa=True,
            variantes__talla=talla_limpia,
            variantes__cantidad_stock__gt=0,
        ).distinct()

    if busqueda:
        termino = limpiar_texto_seguro(busqueda, longitud_maxima=100)
        if termino:
            qs = qs.filter(
                Q(nombre__icontains=termino)
                | Q(descripcion__icontains=termino)
                | Q(sku__icontains=termino)
                | Q(categoria__nombre__icontains=termino)
            )

    if solo_con_stock:
        qs = qs.filter(stock_total__gt=0)

    if solo_destacados:
        qs = qs.filter(destacado=True)

    return qs.order_by("-destacado", "-id")


def obtener_producto_detalle_por_slug(*, slug: str) -> Producto:
    """Obtiene un producto activo por su slug con fotos, tallas y precios por mayor precargados.

    Qué hace:      Busca en TBL_RPRODUCTO por slug y precarga imágenes, variantes y reglas de precio.
    Va hacia:      Retorna la instancia de Producto anotada con stock_total.
    Depende de:    listar_productos_catalogo() y django.shortcuts.get_object_or_404.
    Cuándo usarla: En la vista pública de ficha de producto (/productos/<slug>/).
    Si no opera:   Lanza Http404 (renderizando nuestra plantilla personalizada 404.html) si no existe.
    """
    qs = listar_productos_catalogo()
    return get_object_or_404(qs, slug=slug)


def calcular_precio_unitario_aplicado(
    *, producto: Producto, cantidad_total_producto: int
) -> Decimal:
    """Calcula el precio unitario que corresponde según las reglas de precio por mayor del producto.

    Qué hace:      Busca el tramo de ReglaPrecio con mayor cantidad_minima <= cantidad_total_producto.
    Va hacia:      Retorna un Decimal en PEN con el precio por unidad (por mayor o base).
    Depende de:    Producto.precio_unidad y sus filas en TBL_RREGLA_PRECIO.
    Cuándo usarla: Al mostrar el ahorro en la ficha, calcular el carrito o crear un ItemPedido.
    Si no opera:   Si cantidad_total_producto < 1 o no alcanza ningún tramo, devuelve precio_unidad.
    """
    if cantidad_total_producto <= 1:
        return producto.precio_unidad

    reglas = list(producto.reglas_precio.all())
    reglas_aplicables = [
        r for r in reglas if r.cantidad_minima <= cantidad_total_producto
    ]
    if not reglas_aplicables:
        return producto.precio_unidad

    mejor_regla = max(reglas_aplicables, key=lambda r: r.cantidad_minima)
    return mejor_regla.precio_unidad


_MAPA_ETIQUETAS_VITRINA: dict[tuple[str, ...], tuple[str, str]] = {
    ("Hoy",): ("Hoy", "🔥 Más vendida de hoy"),
    ("Semana",): ("Semana", "🔥 Más vendida de la semana"),
    ("Mes",): ("Mes", "🔥 Más vendida del mes"),
    ("Hoy", "Semana"): ("Hoy · Semana", "🔥 Más vendida · Hoy y semana"),
    ("Hoy", "Mes"): ("Hoy · Mes", "🔥 Más vendida · Hoy y mes"),
    ("Semana", "Mes"): ("Semana · Mes", "🔥 Más vendida · Semana y mes"),
    ("Hoy", "Semana", "Mes"): ("Top ventas", "🔥 Más vendida · Hoy, semana y mes"),
}


def _construir_tarjeta_vitrina_portada(
    *,
    producto: Producto,
    periodos: list[str],
    unidades: int,
    es_respaldo: bool,
) -> dict[str, Any]:
    """Arma el diccionario serializable para un slide de la vitrina editorial de portada.

    Qué hace:      Extrae fotos reales (1 o 2), tallas con stock, tramo mayorista y textos limpios.
    Va hacia:      Retorna un dict listo para renderizar en templates/catalogo/inicio.html.
    Depende de:    Producto con relaciones imagenes, variantes y reglas_precio prefetched.
    Cuándo usarla: Desde obtener_vitrina_mas_vendidas_portada() para cada ganador único o respaldo.
    Si no opera:   Si el producto no tiene fotos o tallas con stock, devuelve imagen None y 'Sin stock'.
    """
    imagenes = list(producto.imagenes.all())
    tallas_disp = list(dict.fromkeys(v.talla for v in producto.variantes.all() if v.cantidad_stock > 0))
    tallas_texto = " · ".join(tallas_disp) if tallas_disp else "Consultar stock"
    regla_mayor = next(iter(producto.reglas_precio.all()), None)

    if es_respaldo:
        etiqueta_pill = "Destacada"
        etiqueta_badge = "⭐ Destacada Emuná Sport"
        etiqueta_volumen = ""
    else:
        etiqueta_pill, etiqueta_badge = _MAPA_ETIQUETAS_VITRINA.get(
            tuple(periodos), ("Top ventas", "🔥 Más vendida")
        )
        unidad_lbl = "ud. vendida" if unidades == 1 else "uds. vendidas"
        etiqueta_volumen = f"{unidades} {unidad_lbl}"

    return {
        "producto": producto,
        "etiqueta_pill": etiqueta_pill,
        "etiqueta_badge": etiqueta_badge,
        "etiqueta_volumen": etiqueta_volumen,
        "unidades": unidades,
        "es_respaldo": es_respaldo,
        "imagen_1": imagenes[0] if len(imagenes) >= 1 else None,
        "imagen_2": imagenes[1] if len(imagenes) >= 2 else None,
        "total_fotos": len(imagenes),
        "tallas_texto": tallas_texto,
        "regla_mayor": regla_mayor,
    }


def obtener_vitrina_mas_vendidas_portada(
    *, destacados: list[Producto] | None = None
) -> list[dict[str, Any]]:
    """Obtiene los productos reales más vendidos de hoy, la semana y el mes para la vitrina de portada.

    Qué hace:      Consulta ventas confirmadas (PAGADO/ENVIADO/ENTREGADO) por período y deduplica modelos.
    Va hacia:      Retorna hasta 3 slides reales (Hoy/Semana/Mes) o 1 respaldo destacado si aún no hay ventas.
    Depende de:    apps.pedidos.models.ItemPedido, ESTADOS_VENTA_CONFIRMADA y resolver_rango_fechas().
    Cuándo usarla: En vista_inicio_catalogo() al construir la Sección 1 de portada.
    Si no opera:   Si no existen ventas confirmadas en ningún período, usa el primer destacado sin errores.
    """
    from apps.pedidos.models import ItemPedido
    from apps.tablero.selectores import ESTADOS_VENTA_CONFIRMADA, resolver_rango_fechas

    zona_actual = timezone.get_current_timezone()
    slots: list[dict[str, Any]] = []
    slots_por_pid: dict[int, dict[str, Any]] = {}

    for clave_periodo, corto in (("hoy", "Hoy"), ("7dias", "Semana"), ("mes", "Mes")):
        fecha_desde, fecha_hasta, _ = resolver_rango_fechas(periodo=clave_periodo)
        inicio_dt = timezone.make_aware(datetime.combine(fecha_desde, time.min), zona_actual)
        fin_dt = timezone.make_aware(
            datetime.combine(fecha_hasta + timedelta(days=1), time.min),
            zona_actual,
        )

        top_fila = (
            ItemPedido.objects.filter(
                pedido__estado__in=ESTADOS_VENTA_CONFIRMADA,
                variante__producto__activo=True,
                variante__producto__categoria__activa=True,
            )
            .annotate(fecha_efectiva=Coalesce("pedido__fecha_pagado", "pedido__fecha_creacion"))
            .filter(fecha_efectiva__gte=inicio_dt, fecha_efectiva__lt=fin_dt)
            .values("variante__producto_id")
            .annotate(
                unidades=Coalesce(Sum("cantidad"), Value(0)),
                ingresos=Coalesce(
                    Sum("subtotal"),
                    Value(Decimal("0.00")),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
            .order_by("-unidades", "-ingresos", "-variante__producto_id")
            .first()
        )
        if not top_fila:
            continue

        pid = int(top_fila["variante__producto_id"])
        unidades_periodo = int(top_fila["unidades"])
        if pid in slots_por_pid:
            slots_por_pid[pid]["periodos"].append(corto)
            slots_por_pid[pid]["unidades"] = max(slots_por_pid[pid]["unidades"], unidades_periodo)
        else:
            nuevo = {
                "producto_id": pid,
                "periodos": [corto],
                "unidades": unidades_periodo,
            }
            slots_por_pid[pid] = nuevo
            slots.append(nuevo)

    if slots:
        productos_map = {
            p.id: p
            for p in listar_productos_catalogo().filter(
                id__in=[s["producto_id"] for s in slots]
            )
        }
        tarjetas = [
            _construir_tarjeta_vitrina_portada(
                producto=productos_map[s["producto_id"]],
                periodos=s["periodos"],
                unidades=s["unidades"],
                es_respaldo=False,
            )
            for s in slots
            if s["producto_id"] in productos_map
        ]
        if tarjetas:
            return tarjetas

    respaldo = destacados[0] if destacados else listar_productos_catalogo().first()
    if not respaldo:
        return []
    return [
        _construir_tarjeta_vitrina_portada(
            producto=respaldo,
            periodos=[],
            unidades=0,
            es_respaldo=True,
        )
    ]
