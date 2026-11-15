"""Selectores optimizados de lectura del catálogo (cero consultas N+1)."""
from decimal import Decimal

from django.db.models import Prefetch, Q, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

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
