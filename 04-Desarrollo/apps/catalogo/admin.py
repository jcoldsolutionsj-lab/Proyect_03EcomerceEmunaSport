"""Configuración del panel administrativo para el catálogo de camisetas."""
from django.contrib import admin

from .models import Categoria, ImagenProducto, Producto, ReglaPrecio, Variante


class ImagenProductoInline(admin.TabularInline):
    """Permite gestionar las fotos del producto en la misma pantalla del producto."""

    model = ImagenProducto
    extra = 1
    fields = (
        "orden",
        "es_principal",
        "ruta_original",
        "ruta_miniatura",
        "ruta_detalle",
        "texto_alternativo",
    )


class VarianteInline(admin.TabularInline):
    """Permite gestionar las tallas (S, M, L, XL) y ver su stock dentro del producto."""

    model = Variante
    extra = 1
    fields = ("talla", "sku", "cantidad_stock", "umbral_stock_bajo", "activa", "color", "modelo")


class ReglaPrecioInline(admin.TabularInline):
    """Permite configurar los tramos de precio por mayor dentro de cada producto."""

    model = ReglaPrecio
    extra = 1
    fields = ("cantidad_minima", "precio_unidad")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Administración de categorías del catálogo."""

    list_display = ("nombre", "slug", "orden", "activa", "fecha_actualizacion")
    list_filter = ("activa",)
    search_fields = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}
    ordering = ("orden", "nombre")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Administración integral de productos con tallas, fotos y precios por mayor."""

    list_display = (
        "nombre",
        "sku",
        "categoria",
        "precio_unidad",
        "precio_anterior",
        "activo",
        "destacado",
    )
    list_filter = ("activo", "destacado", "categoria")
    search_fields = ("nombre", "sku", "descripcion")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [VarianteInline, ReglaPrecioInline, ImagenProductoInline]


@admin.register(Variante)
class VarianteAdmin(admin.ModelAdmin):
    """Vista directa de variantes por talla y su stock actual."""

    list_display = ("producto", "talla", "sku", "cantidad_stock", "activa")
    list_filter = ("talla", "activa", "producto__categoria")
    search_fields = ("sku", "producto__nombre", "talla")
