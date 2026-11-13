"""Configuración del panel administrativo para el catálogo de camisetas y auditoría de stock."""
from typing import Any

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.views.decorators.http import require_POST

from apps.nucleo.admin_helpers import encabezado_con_tooltip
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
    list_display = (
        "producto_col",
        "talla_col",
        "sku_col",
        "stock_semaforo",
        "umbral_col",
        "activa_col",
    )
    list_filter = ("talla", "activa", "producto__categoria")
    search_fields = ("sku", "producto__nombre", "talla")

    @admin.display(
        description=encabezado_con_tooltip("Producto", "Camiseta a la que pertenece esta talla."),
        ordering="producto__nombre",
    )
    def producto_col(self, obj: Variante) -> str:
        """Muestra el nombre del producto de la variante con tooltip explicativo.

        Qué hace:      Retorna el nombre del producto padre.
        Va hacia:      Columna Producto de VarianteAdmin.
        Depende de:    obj.producto.nombre.
        Cuándo usarla: En el listado de variantes del panel administrativo.
        Si no opera:   Retorna cadena vacía si no hay producto asociado.
        """
        return obj.producto.nombre

    @admin.display(
        description=encabezado_con_tooltip("Talla", "Talla física disponible (S, M, L, XL)."),
        ordering="talla",
    )
    def talla_col(self, obj: Variante) -> str:
        """Muestra la talla en badge compacto.

        Qué hace:      Formatea la talla en negrita.
        Va hacia:      Columna Talla de VarianteAdmin.
        Depende de:    obj.talla.
        Cuándo usarla: En el listado de variantes.
        Si no opera:   Retorna el texto plano de talla.
        """
        return format_html("<strong>{}</strong>", obj.talla)

    @admin.display(
        description=encabezado_con_tooltip("SKU", "Código único interno por modelo y talla."),
        ordering="sku",
    )
    def sku_col(self, obj: Variante) -> str:
        """Muestra el SKU en fuente monoespaciada.

        Qué hace:      Renderiza obj.sku como código legible.
        Va hacia:      Columna SKU de VarianteAdmin.
        Depende de:    obj.sku.
        Cuándo usarla: En el listado de variantes.
        Si no opera:   Retorna cadena vacía.
        """
        return format_html("<code>{}</code>", obj.sku)

    @admin.display(
        description=encabezado_con_tooltip(
            "Stock Actual",
            "Unidades disponibles. Solo cambia por ventas confirmadas, cancelaciones o entrada auditada; no se edita a mano.",
        ),
        ordering="cantidad_stock",
    )
    def stock_semaforo(self, obj: Variante) -> str:
        """Muestra el stock actual con semáforo de color según umbral mínimo.

        Qué hace:      Pinta rojo si está agotado (0), amarillo si es bajo y verde si está normal.
        Va hacia:      Columna Stock Actual en VarianteAdmin.
        Depende de:    obj.cantidad_stock y obj.umbral_stock_bajo.
        Cuándo usarla: Para detectar rápido tallas críticas o agotadas desde el panel.
        Si no opera:   Muestra el número entero como respaldo.
        """
        if obj.cantidad_stock <= 0:
            return format_html(
                '<span style="color:#DC2626;background:#FEE2E2;padding:2px 8px;border-radius:999px;font-weight:800;font-size:12px;">{}</span>',
                "🔴 Agotado (0)",
            )
        if obj.cantidad_stock <= obj.umbral_stock_bajo:
            return format_html(
                '<span style="color:#B45309;background:#FEF3C7;padding:2px 8px;border-radius:999px;font-weight:800;font-size:12px;">🟡 Bajo ({})</span>',
                obj.cantidad_stock,
            )
        return format_html(
            '<span style="color:#059669;background:#D1FAE5;padding:2px 8px;border-radius:999px;font-weight:800;font-size:12px;">🟢 {} und.</span>',
            obj.cantidad_stock,
        )

    @admin.display(
        description=encabezado_con_tooltip(
            "Alerta mín.",
            "Cuando el stock baja a este límite, se muestra alerta amarilla de reposición.",
        ),
        ordering="umbral_stock_bajo",
    )
    def umbral_col(self, obj: Variante) -> int:
        """Muestra el umbral mínimo configurado para alertas de stock bajo.

        Qué hace:      Retorna obj.umbral_stock_bajo.
        Va hacia:      Columna Alerta mín. en VarianteAdmin.
        Depende de:    obj.umbral_stock_bajo.
        Cuándo usarla: En el listado de variantes.
        Si no opera:   Retorna 0.
        """
        return obj.umbral_stock_bajo

    @admin.display(
        description=encabezado_con_tooltip(
            "Activa",
            "Si está desmarcada, esta talla no se muestra disponible en la tienda web.",
        ),
        ordering="activa",
        boolean=True,
    )
    def activa_col(self, obj: Variante) -> bool:
        """Muestra si la variante está activa para venta pública.

        Qué hace:      Retorna booleano obj.activa para renderizado con ícono nativo.
        Va hacia:      Columna Activa en VarianteAdmin.
        Depende de:    obj.activa.
        Cuándo usarla: En el listado de variantes.
        Si no opera:   Retorna False.
        """
        return obj.activa

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
        "fecha_col",
        "tipo_col",
        "cantidad_col",
        "variante_col",
        "motivo_col",
        "pedido_col",
        "creado_por_col",
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
    fieldsets = (
        (
            "Auditoría de Inventario (Kárdex Inmutable)",
            {
                "fields": (
                    "fecha_creacion",
                    "tipo",
                    "cantidad",
                    "variante",
                    "motivo",
                    "pedido",
                    "creado_por",
                ),
                "description": (
                    "Registro inalterable de auditoría para trazabilidad del stock de Emuná Sport. "
                    "Las cantidades negativas (-) representan salidas de almacén por venta o arqueo; "
                    "las cantidades positivas (+) representan ingresos de mercadería o devoluciones por pedido cancelado."
                ),
            },
        ),
    )
    ordering = ("-fecha_creacion",)

    @admin.display(
        description=encabezado_con_tooltip(
            "Fecha", "Fecha y hora exacta en que se registró este movimiento (inmutable)."
        ),
        ordering="fecha_creacion",
    )
    def fecha_col(self, obj: MovimientoStock) -> Any:
        """Muestra la fecha de creación del movimiento con tooltip de ayuda.

        Qué hace:      Retorna obj.fecha_creacion formateado por Django Admin.
        Va hacia:      Columna Fecha en MovimientoStockAdmin.
        Depende de:    obj.fecha_creacion.
        Cuándo usarla: En la vista de auditoría de inventario.
        Si no opera:   Retorna None.
        """
        return obj.fecha_creacion

    @admin.display(
        description=encabezado_con_tooltip(
            "Tipo",
            "VENTA: salida por pedido pagado; ENTRADA: ingreso de lote; DEVOLUCION: reposición por cancelación; AJUSTE: corrección manual.",
        ),
        ordering="tipo",
    )
    def tipo_col(self, obj: MovimientoStock) -> str:
        """Muestra el tipo de movimiento con insignia legible.

        Qué hace:      Renderiza etiqueta de tipo con color contextual.
        Va hacia:      Columna Tipo en MovimientoStockAdmin.
        Depende de:    obj.tipo y get_tipo_display().
        Cuándo usarla: En la tabla de auditoría de inventario.
        Si no opera:   Retorna el texto plano del tipo.
        """
        colores = {
            "VENTA": ("#7C3AED", "#EDE9FE"),
            "ENTRADA": ("#059669", "#D1FAE5"),
            "DEVOLUCION": ("#0284C7", "#E0F2FE"),
            "AJUSTE": ("#B45309", "#FEF3C7"),
        }
        fg, bg = colores.get(obj.tipo, ("#334155", "#F1F5F9"))
        return format_html(
            '<span style="color:{};background:{};padding:2px 8px;border-radius:4px;font-weight:700;font-size:11px;">{}</span>',
            fg,
            bg,
            obj.get_tipo_display(),
        )

    @admin.display(
        description=encabezado_con_tooltip(
            "Cantidad",
            "Negativo (-): salida de almacén por venta o ajuste. Positivo (+): ingreso de lote o devolución. Nunca puede ser 0.",
        ),
        ordering="cantidad",
    )
    def cantidad_col(self, obj: MovimientoStock) -> str:
        """Muestra la cantidad con signo e indicador visual Entrada (+) / Salida (-).

        Qué hace:      Distingue en verde las entradas positivas y en rojo las salidas negativas.
        Va hacia:      Columna Cantidad en MovimientoStockAdmin.
        Depende de:    obj.cantidad.
        Cuándo usarla: Para leer al instante si el movimiento sumó o restó camisetas del almacén.
        Si no opera:   Muestra el número entero.
        """
        if obj.cantidad > 0:
            return format_html(
                '<span style="color:#059669;background:#D1FAE5;padding:2px 8px;border-radius:999px;font-weight:800;font-size:12px;">🟢 Entrada +{}</span>',
                obj.cantidad,
            )
        return format_html(
            '<span style="color:#DC2626;background:#FEE2E2;padding:2px 8px;border-radius:999px;font-weight:800;font-size:12px;">🔴 Salida {}</span>',
            obj.cantidad,
        )

    @admin.display(
        description=encabezado_con_tooltip(
            "Camiseta / Talla", "Prenda y talla específica cuyo stock cambió."
        ),
        ordering="variante__producto__nombre",
    )
    def variante_col(self, obj: MovimientoStock) -> Variante:
        """Muestra la variante afectada por el movimiento.

        Qué hace:      Retorna obj.variante para su renderizado estándar.
        Va hacia:      Columna Camiseta / Talla en MovimientoStockAdmin.
        Depende de:    obj.variante.
        Cuándo usarla: En el listado de movimientos de inventario.
        Si no opera:   No aplica.
        """
        return obj.variante

    @admin.display(
        description=encabezado_con_tooltip(
            "Motivo", "Explicación del movimiento registrada para trazabilidad y arqueo."
        ),
        ordering="motivo",
    )
    def motivo_col(self, obj: MovimientoStock) -> str:
        """Muestra el motivo del movimiento de inventario.

        Qué hace:      Retorna obj.motivo.
        Va hacia:      Columna Motivo en MovimientoStockAdmin.
        Depende de:    obj.motivo.
        Cuándo usarla: En el listado de movimientos.
        Si no opera:   Retorna cadena vacía.
        """
        return obj.motivo

    @admin.display(
        description=encabezado_con_tooltip(
            "Pedido", "Pedido asociado cuando el movimiento proviene de una venta o cancelación."
        ),
        ordering="pedido__codigo",
    )
    def pedido_col(self, obj: MovimientoStock) -> str:
        """Muestra el código del pedido vinculado o guion si fue ajuste manual.

        Qué hace:      Retorna obj.pedido.codigo si existe pedido, o '—'.
        Va hacia:      Columna Pedido en MovimientoStockAdmin.
        Depende de:    obj.pedido.
        Cuándo usarla: En el listado de auditoría de stock.
        Si no opera:   Retorna '—'.
        """
        return obj.pedido.codigo if obj.pedido else "—"

    @admin.display(
        description=encabezado_con_tooltip(
            "Responsable", "Usuario del sistema que confirmó el pago, canceló o ingresó el lote."
        ),
        ordering="creado_por__username",
    )
    def creado_por_col(self, obj: MovimientoStock) -> str:
        """Muestra el nombre de usuario responsable del movimiento.

        Qué hace:      Retorna username de creado_por o 'Sistema'.
        Va hacia:      Columna Responsable en MovimientoStockAdmin.
        Depende de:    obj.creado_por.
        Cuándo usarla: En la tabla de auditoría de inventario.
        Si no opera:   Retorna 'Sistema'.
        """
        return obj.creado_por.username if obj.creado_por else "Sistema"

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
