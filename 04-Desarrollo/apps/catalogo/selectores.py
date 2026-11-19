"""Selectores optimizados de lectura del catálogo (cero consultas N+1 y caché para futura IA)."""
import unicodedata
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any

from django.core.cache import cache
from django.db.models import DecimalField, Prefetch, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.nucleo.validadores import limpiar_texto_seguro

from .models import Categoria, Equipo, ImagenProducto, Producto, ReglaPrecio, Variante
from .signals import CLAVE_CACHE_CATALOGO_IA

MAX_PRODUCTOS_DESTACADOS = 8
TTL_CACHE_CATALOGO_IA_SEGUNDOS = 300


def listar_equipos_activos() -> QuerySet[Equipo]:
    """Devuelve todos los equipos/selecciones activos ordenados para filtros y catálogo.

    Qué hace:      Filtra TBL_REQUIPO con activo=True y ordena por EQU_NORDEN y nombre.
    Va hacia:      Retorna un QuerySet de Equipo para filtros web y herramientas IA.
    Depende de:    apps.catalogo.models.Equipo.
    Cuándo usarla: En filtros de selección/club o vistas del catálogo.
    Si no opera:   Retorna un QuerySet vacío si aún no se registran equipos.
    """
    return Equipo.objects.filter(activo=True).order_by("orden", "nombre")


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
    equipo_slug: str | None = None,
    talla: str | None = None,
    busqueda: str | None = None,
    solo_con_stock: bool = False,
    solo_destacados: bool = False,
) -> QuerySet[Producto]:
    """Consulta productos activos con sus fotos, tallas, equipo y stock total en una sola carga.

    Qué hace:      Aplica filtros de categoría, equipo, talla, texto y stock con select/prefetch.
    Va hacia:      Retorna un QuerySet de Producto anotado con stock_total sin consultas N+1.
    Depende de:    Producto, Equipo, ImagenProducto, Variante, ReglaPrecio y limpiar_texto_seguro.
    Cuándo usarla: En la vista principal del catálogo, buscador y endpoints públicos de lectura.
    Si no opera:   Retorna un QuerySet vacío si ningún producto coincide con los filtros.
    """
    qs = (
        Producto.objects.filter(activo=True, categoria__activa=True)
        .select_related("categoria", "equipo")
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

    if equipo_slug:
        eq_slug_limpio = limpiar_texto_seguro(equipo_slug, longitud_maxima=100)
        qs = qs.filter(equipo__slug=eq_slug_limpio, equipo__activo=True)

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
                | Q(equipo__nombre__icontains=termino)
                | Q(equipo__alias_busqueda__icontains=termino)
                | Q(palabras_clave__icontains=termino)
                | Q(temporada__icontains=termino)
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


def _normalizar_texto_busqueda(texto: str) -> str:
    """Convierte a minúsculas y remueve tildes para comparar términos sin sensibilidad ortográfica.

    Qué hace:      Descompone caracteres Unicode (NFKD), elimina marcas diacríticas y limpia espacios.
    Va hacia:      Retorna un str normalizado listo para tokenización y comparación rápida.
    Depende de:    unicodedata.
    Cuándo usarla: En búsquedas en memoria sobre la instantánea cacheada del catálogo.
    Si no opera:   Retorna cadena vacía si el texto de entrada está vacío.
    """
    descompuesto = unicodedata.normalize("NFKD", str(texto or ""))
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().strip().split())


def obtener_catalogo_compacto_para_ia() -> list[dict[str, Any]]:
    """Obtiene desde caché (o construye una sola vez) el catálogo resumido para consultas rápidas.

    Qué hace:      Lee CLAVE_CACHE_CATALOGO_IA o consulta productos activos con tallas disponibles.
    Va hacia:      Retorna lista de dicts livianos evitando SUM/GROUP BY por cada turno de chat.
    Depende de:    django.core.cache, Producto, Variante, ReglaPrecio y Equipo.
    Cuándo usarla: Desde buscar_productos_para_ia() o futuros endpoints de asistente Gemini.
    Si no opera:   Retorna lista vacía si no existen productos activos.
    """
    cacheado = cache.get(CLAVE_CACHE_CATALOGO_IA)
    if cacheado is not None:
        return cacheado

    qs = (
        Producto.objects.filter(activo=True, categoria__activa=True)
        .select_related("categoria", "equipo")
        .prefetch_related(
            Prefetch(
                "variantes",
                queryset=Variante.objects.filter(activa=True, cantidad_stock__gt=0).order_by(
                    "id"
                ),
            ),
            Prefetch(
                "reglas_precio",
                queryset=ReglaPrecio.objects.order_by("cantidad_minima"),
            ),
        )
        .only(
            "id",
            "nombre",
            "slug",
            "sku",
            "equipacion",
            "temporada",
            "palabras_clave",
            "precio_unidad",
            "precio_anterior",
            "destacado",
            "categoria__nombre",
            "categoria__slug",
            "equipo__nombre",
            "equipo__slug",
            "equipo__alias_busqueda",
            "equipo__activo",
        )
        .order_by("-destacado", "-id")
    )

    resumen: list[dict[str, Any]] = []
    for prod in qs:
        variantes_disp = list(prod.variantes.all())
        tallas = list(dict.fromkeys(v.talla for v in variantes_disp))
        stock_total = sum(v.cantidad_stock for v in variantes_disp)
        equipo_obj = prod.equipo if prod.equipo and prod.equipo.activo else None
        equipo_nombre = equipo_obj.nombre if equipo_obj else ""
        alias_equipo = equipo_obj.alias_busqueda if equipo_obj else ""

        reglas = [
            {"desde": r.cantidad_minima, "precio": str(r.precio_unidad)}
            for r in prod.reglas_precio.all()
        ]
        texto_indice = _normalizar_texto_busqueda(
            " ".join(
                filter(
                    None,
                    [
                        prod.nombre,
                        prod.sku,
                        prod.get_equipacion_display() if prod.equipacion else "",
                        prod.temporada,
                        prod.palabras_clave,
                        prod.categoria.nombre,
                        equipo_nombre,
                        alias_equipo,
                    ],
                )
            )
        )
        resumen.append(
            {
                "id": prod.id,
                "sku": prod.sku,
                "nombre": prod.nombre,
                "slug": prod.slug,
                "url": prod.get_absolute_url(),
                "categoria": prod.categoria.nombre,
                "equipo": equipo_nombre,
                "equipacion": prod.get_equipacion_display() if prod.equipacion else "",
                "temporada": prod.temporada,
                "precio_unidad": str(prod.precio_unidad),
                "precio_anterior": str(prod.precio_anterior) if prod.precio_anterior else None,
                "reglas_mayor": reglas,
                "tallas_disponibles": tallas,
                "stock_total": stock_total,
                "_indice_equipo": _normalizar_texto_busqueda(
                    f"{equipo_nombre} {alias_equipo}"
                ),
                "_indice_palabras": _normalizar_texto_busqueda(prod.palabras_clave),
                "_indice_texto": texto_indice,
            }
        )

    cache.set(CLAVE_CACHE_CATALOGO_IA, resumen, TTL_CACHE_CATALOGO_IA_SEGUNDOS)
    return resumen


def buscar_productos_para_ia(consulta: str, *, limite: int = 5) -> list[dict[str, Any]]:
    """Filtra en memoria sobre la instantánea cacheada los productos más relevantes sin cargar la BD.

    Qué hace:      Normaliza la pregunta, puntúa coincidencias por equipo/alias/nombre/talla y ordena.
    Va hacia:      Retorna hasta `limite` fichas compactas listas para contextualizar a Gemini.
    Depende de:    obtener_catalogo_compacto_para_ia(), _normalizar_texto_busqueda() y limpiar_texto_seguro().
    Cuándo usarla: Antes de invocar la API externa de Gemini en el asistente web.
    Si no opera:   Retorna lista vacía si ningún término coincide con productos con stock.
    """
    limpio = limpiar_texto_seguro(consulta or "", longitud_maxima=200)
    normalizado = _normalizar_texto_busqueda(limpio)
    if not normalizado:
        return []

    palabras_vacias = {
        "hola",
        "tienen",
        "tienes",
        "hay",
        "camiseta",
        "camisetas",
        "polo",
        "polos",
        "de",
        "la",
        "el",
        "en",
        "talla",
        "para",
        "por",
        "mayor",
        "cuanto",
        "cuesta",
        "precio",
        "una",
        "un",
        "quiero",
        "busco",
    }
    tokens = [t for t in normalizado.replace(",", " ").split() if len(t) >= 2 and t not in palabras_vacias]
    if not tokens:
        tokens = [t for t in normalizado.split() if len(t) >= 2]
    if not tokens:
        return []

    catalogo = obtener_catalogo_compacto_para_ia()
    puntuados: list[tuple[int, dict[str, Any]]] = []
    for item in catalogo:
        if item["stock_total"] <= 0:
            continue
        puntaje = 0
        for tok in tokens:
            if tok in item["_indice_equipo"].split():
                puntaje += 12
            elif tok in item["_indice_equipo"]:
                puntaje += 8
            if tok in item["_indice_palabras"]:
                puntaje += 7
            if tok in item["_indice_texto"]:
                puntaje += 4
            if tok.upper() in item["tallas_disponibles"]:
                puntaje += 2
        if puntaje > 0:
            ficha_limpia = {k: v for k, v in item.items() if not k.startswith("_")}
            puntuados.append((puntaje, ficha_limpia))

    puntuados.sort(key=lambda par: (-par[0], -par[1]["stock_total"]))
    return [ficha for _, ficha in puntuados[: max(1, limite)]]
