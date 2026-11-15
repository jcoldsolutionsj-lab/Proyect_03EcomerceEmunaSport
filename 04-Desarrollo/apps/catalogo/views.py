"""Vistas delgadas del catálogo público, páginas legales (Ley N.º 29733) y robots.txt."""
import json
from urllib.parse import quote

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.nucleo.selectores import obtener_configuracion_tienda
from apps.nucleo.validadores import limpiar_texto_seguro

from .selectores import (
    MAX_PRODUCTOS_DESTACADOS,
    listar_categorias_activas,
    listar_productos_catalogo,
    obtener_producto_detalle_por_slug,
)

TALLAS_FILTRO = ["S", "M", "L", "XL"]


def vista_inicio_catalogo(request: HttpRequest) -> HttpResponse:
    """Renderiza la portada con Hero Video Banner, filtros y cuadrícula de camisetas.

    Qué hace:      Lee filtros GET sanitizados, consulta selectores del catálogo y renderiza inicio.html.
    Va hacia:      Retorna un HttpResponse con la página principal de Emuná Sport.
    Depende de:    listar_categorias_activas(), listar_productos_catalogo() y obtener_configuracion_tienda().
    Cuándo usarla: Al visitar '/' o al filtrar por categoría, talla, stock o búsqueda.
    Si no opera:   Si un filtro no tiene coincidencias, muestra estado vacío con botón a WhatsApp.
    """
    categoria_slug = limpiar_texto_seguro(request.GET.get("categoria"), longitud_maxima=100)
    talla_activa = limpiar_texto_seguro(request.GET.get("talla"), longitud_maxima=10).upper()
    busqueda = limpiar_texto_seguro(request.GET.get("q"), longitud_maxima=100)
    solo_con_stock = request.GET.get("disponible") == "1"

    categorias = listar_categorias_activas()
    productos = listar_productos_catalogo(
        categoria_slug=categoria_slug or None,
        talla=talla_activa or None,
        busqueda=busqueda or None,
        solo_con_stock=solo_con_stock,
    )
    destacados = list(listar_productos_catalogo(solo_destacados=True)[:MAX_PRODUCTOS_DESTACADOS])
    config = obtener_configuracion_tienda()

    texto_wa = quote(
        f"Hola Richard, vengo de la web de {config.nombre} y quiero consultar por las camisetas deportivas."
    )
    url_whatsapp_general = f"https://wa.me/51{config.numero_whatsapp}?text={texto_wa}"

    contexto = {
        "categorias": categorias,
        "productos": productos,
        "destacados": destacados,
        "categoria_activa": categoria_slug,
        "talla_activa": talla_activa,
        "tallas_filtro": TALLAS_FILTRO,
        "busqueda": busqueda,
        "solo_con_stock": solo_con_stock,
        "total_resultados": productos.count(),
        "url_whatsapp_contextual": url_whatsapp_general,
    }
    return render(request, "catalogo/inicio.html", contexto)


def vista_detalle_producto(request: HttpRequest, slug: str) -> HttpResponse:
    """Muestra la ficha de una camiseta con sus 5 miniaturas, tallas, stock y precios por mayor.

    Qué hace:      Obtiene el producto por slug, arma el JSON-LD Schema.org y renderiza detalle_producto.html.
    Va hacia:      Retorna un HttpResponse con la ficha del producto (/productos/<slug>/).
    Depende de:    obtener_producto_detalle_por_slug() y obtener_configuracion_tienda().
    Cuándo usarla: Cuando el comprador entra a ver una camiseta desde el catálogo o enlace de WhatsApp.
    Si no opera:   Si el slug no existe o está inactivo, lanza Http404 y muestra 404.html.
    """
    producto = obtener_producto_detalle_por_slug(slug=slug)
    config = obtener_configuracion_tienda()
    imagenes = list(producto.imagenes.all())
    variantes = list(producto.variantes.all())
    reglas_precio = list(producto.reglas_precio.all())

    imagen_principal = imagenes[0] if imagenes else None
    primera_variante_con_stock = next(
        (v for v in variantes if v.cantidad_stock > 0),
        variantes[0] if variantes else None,
    )

    texto_wa = quote(
        f"Hola Richard, estoy viendo en la web de {config.nombre} la camiseta "
        f"*{producto.nombre}* (SKU: {producto.sku}, S/ {producto.precio_unidad}). "
        "¿Me confirmas disponibilidad?"
    )
    url_whatsapp_producto = f"https://wa.me/51{config.numero_whatsapp}?text={texto_wa}"

    # Requisito #6 Antes de lanzar: Datos estructurados Schema.org Product en JSON-LD
    esquema_producto = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": producto.nombre,
        "sku": producto.sku,
        "description": producto.descripcion or f"{producto.nombre} – {config.nombre}",
        "brand": {
            "@type": "Brand",
            "name": producto.marca if (config.mostrar_marcas and producto.marca) else config.nombre,
        },
        "offers": {
            "@type": "Offer",
            "priceCurrency": "PEN",
            "price": str(producto.precio_unidad),
            "availability": (
                "https://schema.org/InStock"
                if getattr(producto, "stock_total", 0) > 0
                else "https://schema.org/OutOfStock"
            ),
        },
    }

    datos_variantes_js = [
        {
            "id": v.id,
            "talla": v.talla,
            "sku": v.sku,
            "stock": v.cantidad_stock,
            "umbral": v.umbral_stock_bajo or config.umbral_stock_bajo,
        }
        for v in variantes
    ]

    contexto = {
        "producto": producto,
        "imagenes": imagenes,
        "imagen_principal": imagen_principal,
        "variantes": variantes,
        "variante_inicial": primera_variante_con_stock,
        "reglas_precio": reglas_precio,
        "datos_variantes_json": json.dumps(datos_variantes_js),
        "esquema_producto_json": json.dumps(esquema_producto, ensure_ascii=False),
        "url_whatsapp_contextual": url_whatsapp_producto,
    }
    return render(request, "catalogo/detalle_producto.html", contexto)


def vista_aviso_legal(request: HttpRequest) -> HttpResponse:
    """Renderiza la página de Aviso Legal y Términos y Condiciones (Requisito #1).

    Qué hace:      Muestra las condiciones de compra, cotización de envío y cambios de Emuná Sport.
    Va hacia:      Retorna HttpResponse con la plantilla legal/aviso_legal.html.
    Depende de:    django.shortcuts.render y contexto_tienda.
    Cuándo usarla: Al visitar /aviso-legal/ desde el pie de página o el checkout.
    Si no opera:   No aplica (página informativa).
    """
    return render(request, "legal/aviso_legal.html")


def vista_politica_privacidad(request: HttpRequest) -> HttpResponse:
    """Renderiza la Política de Privacidad conforme a la Ley N.º 29733 del Perú (Requisito #2).

    Qué hace:      Explica el tratamiento del nombre, DNI y celular exclusivamente para pedidos y envíos.
    Va hacia:      Retorna HttpResponse con la plantilla legal/privacidad.html.
    Depende de:    django.shortcuts.render y contexto_tienda.
    Cuándo usarla: Al visitar /privacidad/ desde el pie de página o el formulario de pedido.
    Si no opera:   No aplica (página informativa).
    """
    return render(request, "legal/privacidad.html")


def vista_aviso_cookies(request: HttpRequest) -> HttpResponse:
    """Renderiza la página informativa sobre el uso de cookies técnicas de sesión (Requisito #3).

    Qué hace:      Detalla el uso de cookies necesarias para el carrito de compras y seguridad CSRF.
    Va hacia:      Retorna HttpResponse con la plantilla legal/cookies.html.
    Depende de:    django.shortcuts.render.
    Cuándo usarla: Al visitar /cookies/ desde el aviso inferior o el pie de página.
    Si no opera:   No aplica (página informativa).
    """
    return render(request, "legal/cookies.html")


def vista_robots_txt(request: HttpRequest) -> HttpResponse:
    """Sirve el archivo /robots.txt permitiendo el catálogo y bloqueando rutas privadas (Requisito #7).

    Qué hace:      Autoriza la indexación pública y bloquea /gestion/, /carrito/, /pedidos/ y /api/.
    Va hacia:      Retorna HttpResponse en texto plano (text/plain).
    Depende de:    request.build_absolute_uri para enlazar /sitemap.xml.
    Cuándo usarla: Cuando rastreadores de buscadores consultan /robots.txt.
    Si no opera:   No aplica.
    """
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    lineas = [
        "User-agent: *",
        "Allow: /",
        "Allow: /productos/",
        "Disallow: /gestion/",
        "Disallow: /carrito/",
        "Disallow: /pedidos/",
        "Disallow: /api/",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lineas), content_type="text/plain; charset=utf-8")
