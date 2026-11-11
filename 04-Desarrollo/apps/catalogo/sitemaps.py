"""Configuración de Sitemaps XML dinámicos para SEO (Requisito #7 Antes de lanzar)."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Producto


class ProductoSitemap(Sitemap):
    """Genera las entradas en /sitemap.xml para todos los productos activos del catálogo."""

    changefreq = "daily"
    priority = 0.9

    def items(self):
        """Obtiene el listado de productos activos que deben indexarse en buscadores.

        Qué hace:      Filtra TBL_RPRODUCTO con activo=True y categoría activa.
        Va hacia:      Retorna un QuerySet de Producto para el generador de sitemap.xml.
        Depende de:    apps.catalogo.models.Producto.
        Cuándo usarla: Cuando Google Search Console u otro buscador solicita /sitemap.xml.
        Si no opera:   Retorna un QuerySet vacío si no hay productos publicados.
        """
        return Producto.objects.filter(activo=True, categoria__activa=True).order_by("-id")

    def lastmod(self, obj: Producto):
        """Devuelve la fecha de última modificación del producto para el sitemap.

        Qué hace:      Lee el campo PRO_DFECHA_ACTUALIZACION del producto.
        Va hacia:      Etiqueta <lastmod> dentro de /sitemap.xml.
        Depende de:    Atributo fecha_actualizacion de Producto.
        Cuándo usarla: Automáticamente por django.contrib.sitemaps.
        Si no opera:   Retorna None si no hubiera fecha disponible.
        """
        return obj.fecha_actualizacion


class PaginasEstaticasSitemap(Sitemap):
    """Genera las entradas en /sitemap.xml para el inicio y las páginas legales públicas."""

    changefreq = "weekly"
    priority = 0.7

    def items(self) -> list[str]:
        """Devuelve los nombres de las rutas públicas estáticas indexables.

        Qué hace:      Lista las rutas de inicio, aviso legal, privacidad y cookies.
        Va hacia:      Generador de URLs de django.contrib.sitemaps.
        Depende de:    Nombres de rutas definidos en apps.catalogo.urls.
        Cuándo usarla: Al construir /sitemap.xml.
        Si no opera:   No aplica (lista constante).
        """
        return [
            "catalogo:inicio",
            "catalogo:aviso_legal",
            "catalogo:privacidad",
            "catalogo:cookies",
        ]

    def location(self, item: str) -> str:
        """Resuelve la URL relativa de cada página pública estática.

        Qué hace:      Invoca reverse(item) para obtener su ruta real.
        Va hacia:      Etiqueta <loc> de /sitemap.xml.
        Depende de:    django.urls.reverse.
        Cuándo usarla: Automáticamente al renderizar /sitemap.xml.
        Si no opera:   Lanza NoReverseMatch si cambia el nombre de una ruta sin actualizarse aquí.
        """
        return reverse(item)
