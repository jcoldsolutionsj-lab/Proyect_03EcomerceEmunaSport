"""Configuración del panel administrativo para el catálogo de camisetas."""
from typing import Any

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.views.decorators.http import require_POST

from apps.nucleo.excepciones import ErrorDominioEmuna

from .models import Categoria, ImagenProducto, MovimientoStock, Producto, ReglaPrecio, Variante


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
    """Vista directa de variantes por talla y control auditado de stock."""

    change_form_template = "admin/catalogo/variante/change_form.html"
    list_display = ("producto", "talla", "sku", "cantidad_stock", "umbral_stock_bajo", "activa")
    list_filter = ("talla", "activa", "producto__categoria")
    search_fields = ("sku", "producto__nombre", "talla")

    def get_readonly_fields(
        self, request: HttpRequest, obj: Variante | None = None
    ) -> tuple[str, ...]:
        """Bloquea la edición manual de cantidad_stock una vez creada la variante.

        Qué hace:      Retorna ('cantidad_stock',) cuando obj existe para forzar movimientos.
        Va hacia:      Evita alteraciones de stock sin registro en TBL_TMOVIMIENTO_STOCK.
        Depende de:    django.contrib.admin.ModelAdmin.get_readonly_fields.
        Cuándo usarla: Al abrir el formulario de edición de una talla existente en el admin.
        Si no opera:   Si obj es None (alta nueva), permite establecer stock inicial.
        """
        if obj is not None:
            return ("cantidad_stock",)
        return ()

    def get_urls(self) -> list[Any]:
        """Registra la ruta de entrada o ajuste auditado de stock para la variante.

        Qué hace:      Agrega <int:variante_id>/entrada-stock/ vinculada a vista_entrada_stock.
        Va hacia:      Resuelve el formulario superior en templates/admin/catalogo/variante/change_form.html.
        Depende de:    self.admin_site.admin_view y vista_entrada_stock.
        Cuándo usarla: Al inicializar rutas de VarianteAdmin.
        Si no opera:   Retorna las rutas estándar de ModelAdmin.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:variante_id>/entrada-stock/",
                self.admin_site.admin_view(require_POST(self.vista_entrada_stock)),
                name="catalogo_variante_entrada_stock",
            ),
        ]
        return custom_urls + urls

    def vista_entrada_stock(
        self, request: HttpRequest, variante_id: int
    ) -> HttpResponseRedirect:
        """Procesa una entrada o ajuste de inventario llamando a registrar_entrada_stock().

        Qué hace:      Lee cantidad y motivo del POST, valida enteros y crea TBL_TMOVIMIENTO_STOCK.
        Va hacia:      Actualiza stock atómicamente y redirige a la ficha de la variante.
        Depende de:    apps.pedidos.servicios.registrar_entrada_stock.
        Cuándo usarla: Cuando Richard repone lote del taller o ajusta inventario desde el panel.
        Si no opera:   Muestra mensaje de error si la cantidad es 0 o dejaría stock negativo.
        """
        from apps.pedidos.servicios import registrar_entrada_stock

        variante = get_object_or_404(Variante, pk=variante_id)
        try:
            cantidad = int(request.POST.get("cantidad", "0").strip())
            motivo = request.POST.get("motivo", "").strip()
            registrar_entrada_stock(
                variante_id=variante.pk,
                cantidad=cantidad,
                motivo=motivo,
                usuario=request.user,
            )
            self.message_user(
                request,
                f"Movimiento de stock registrado ({cantidad:+d} und.) para {variante}.",
                level=messages.SUCCESS,
            )
        except ValueError:
            self.message_user(
                request,
                "Ingresa una cantidad entera válida distinta de 0 (ej. 10 o -2).",
                level=messages.ERROR,
            )
        except (ErrorDominioEmuna, ValidationError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)

        return HttpResponseRedirect(
            reverse("admin:catalogo_variante_change", args=[variante_id])
        )


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    """Auditoría inmutable de todas las entradas y salidas de stock (TBL_TMOVIMIENTO_STOCK)."""

    list_display = (
        "fecha_creacion",
        "tipo",
        "cantidad",
        "variante",
        "motivo",
        "pedido",
        "creado_por",
    )
    list_filter = ("tipo", "fecha_creacion", "variante__producto__categoria")
    search_fields = (
        "variante__sku",
        "variante__producto__nombre",
        "motivo",
        "pedido__codigo",
    )
    readonly_fields = (
        "variante",
        "tipo",
        "cantidad",
        "motivo",
        "pedido",
        "creado_por",
        "fecha_creacion",
    )
    ordering = ("-fecha_creacion",)

    def has_add_permission(self, request, obj=None) -> bool:
        """Impide crear movimientos directamente desde el formulario para forzar servicios.

        Qué hace:      Retorna False para garantizar que el stock se altere solo por servicios.
        Va hacia:      Panel de administración de auditoría.
        Depende de:    django.contrib.admin.ModelAdmin.
        Cuándo usarla: Al verificar permisos de adición en MovimientoStockAdmin.
        Si no opera:   No aplica.
        """
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Impide editar movimientos de stock existentes para cumplir inmutabilidad.

        Qué hace:      Retorna False deshabilitando el guardado en MovimientoStockAdmin.
        Va hacia:      Conserva la inmutabilidad de TBL_TMOVIMIENTO_STOCK.
        Depende de:    django.contrib.admin.ModelAdmin.
        Cuándo usarla: Al verificar permisos de modificación en el admin.
        Si no opera:   No aplica.
        """
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Impide eliminar registros de trazabilidad de inventario.

        Qué hace:      Retorna False deshabilitando el borrado de filas en el admin.
        Va hacia:      Conserva la inmutabilidad de TBL_TMOVIMIENTO_STOCK.
        Depende de:    django.contrib.admin.ModelAdmin.
        Cuándo usarla: Al verificar permisos de borrado en el admin.
        Si no opera:   No aplica.
        """
        return False
