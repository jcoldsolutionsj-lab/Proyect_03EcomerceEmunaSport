"""Modelos de datos del catálogo: Categoria, Producto, ImagenProducto, Variante, ReglaPrecio y MovimientoStock."""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.nucleo.validadores import limpiar_texto_seguro


class Categoria(models.Model):
    """Categorías para organizar el catálogo de camisetas (TBL_RCATEGORIA)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="CAT_NID",
        verbose_name="Identificador",
    )
    nombre = models.CharField(
        max_length=80,
        db_column="CAT_CNOMBRE",
        verbose_name="Nombre",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_column="CAT_CSLUG",
        verbose_name="Slug URL",
    )
    orden = models.IntegerField(
        default=1,
        db_column="CAT_NORDEN",
        verbose_name="Orden de aparición",
    )
    activa = models.BooleanField(
        default=True,
        db_column="CAT_OACTIVA",
        verbose_name="Categoría visible",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="CAT_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        db_column="CAT_DFECHA_ACTUALIZACION",
        verbose_name="Fecha de última actualización",
    )

    class Meta:
        db_table = "TBL_RCATEGORIA"
        ordering = ["orden", "nombre"]
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self) -> str:
        """Devuelve el nombre de la categoría como representación textual.

        Qué hace:      Retorna el campo nombre de la categoría.
        Va hacia:      Selectores del panel admin y plantillas.
        Depende de:    Atributo nombre de la instancia.
        Cuándo usarla: Automáticamente al convertir la instancia en str.
        Si no opera:   Retorna cadena vacía si aún no tiene nombre.
        """
        return self.nombre

    def clean(self) -> None:
        """Sanitiza el nombre y genera el slug automáticamente si está vacío.

        Qué hace:      Limpia etiquetas HTML del nombre y construye el slug amigable para URL.
        Va hacia:      Normaliza los atributos nombre y slug en memoria antes de persistir.
        Depende de:    limpiar_texto_seguro y django.utils.text.slugify.
        Cuándo usarla: Antes de guardar la categoría mediante full_clean().
        Si no opera:   Lanza ValidationError si el nombre queda vacío tras la limpieza.
        """
        self.nombre = limpiar_texto_seguro(self.nombre, longitud_maxima=80)
        if not self.nombre:
            raise ValidationError("El nombre de la categoría es obligatorio.")
        if not self.slug:
            self.slug = slugify(self.nombre)[:100]

    def save(self, *args, **kwargs) -> None:
        """Valida y guarda la categoría en TBL_RCATEGORIA.

        Qué hace:      Ejecuta full_clean() y persiste la fila en la base de datos.
        Va hacia:      Tabla física TBL_RCATEGORIA.
        Depende de:    clean() y models.Model.save().
        Cuándo usarla: Al crear o editar categorías desde servicios, admin o cargar_demo.
        Si no opera:   Propaga ValidationError si algún campo no es válido.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class Producto(models.Model):
    """Camisetas y prendas deportivas del catálogo de Emuná Sport (TBL_RPRODUCTO)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="PRO_NID",
        verbose_name="Identificador",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        db_column="CAT_NID",
        verbose_name="Categoría",
    )
    nombre = models.CharField(
        max_length=150,
        db_column="PRO_CNOMBRE",
        verbose_name="Nombre del producto",
    )
    slug = models.SlugField(
        max_length=170,
        unique=True,
        db_column="PRO_CSLUG",
        verbose_name="Slug URL",
    )
    sku = models.CharField(
        max_length=30,
        unique=True,
        db_column="PRO_CSKU",
        verbose_name="Código interno (SKU)",
    )
    descripcion = models.TextField(
        null=True,
        blank=True,
        db_column="PRO_CDESCRIPCION",
        verbose_name="Descripción",
    )
    marca = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        db_column="PRO_CMARCA",
        verbose_name="Marca (opcional, apagada por defecto)",
    )
    precio_unidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column="PRO_NPRECIO_UNIDAD",
        verbose_name="Precio actual por unidad (S/)",
    )
    precio_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_column="PRO_NPRECIO_ANTERIOR",
        verbose_name="Precio regular tachado (S/)",
    )
    activo = models.BooleanField(
        default=True,
        db_column="PRO_OACTIVO",
        verbose_name="Visible en la web",
    )
    destacado = models.BooleanField(
        default=False,
        db_column="PRO_ODESTACADO",
        verbose_name="Destacado en inicio",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="PRO_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        db_column="PRO_DFECHA_ACTUALIZACION",
        verbose_name="Fecha de última actualización",
    )

    class Meta:
        db_table = "TBL_RPRODUCTO"
        ordering = ["-destacado", "-id"]
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self) -> str:
        """Devuelve el nombre del producto junto a su código SKU.

        Qué hace:      Formatea '{nombre} ({sku})' para identificar la prenda.
        Va hacia:      Panel administrativo, logs y relaciones con variantes.
        Depende de:    Atributos nombre y sku.
        Cuándo usarla: Automáticamente por Django al mostrar el objeto.
        Si no opera:   Retorna el nombre disponible.
        """
        return f"{self.nombre} ({self.sku})"

    def get_absolute_url(self) -> str:
        """Devuelve la URL pública de la ficha de detalle del producto.

        Qué hace:      Resuelve la ruta 'catalogo:detalle_producto' usando el slug del producto.
        Va hacia:      Retorna un str con la ruta relativa (ej. '/productos/argentina-x-messi-10/').
        Depende de:    django.urls.reverse y el campo slug.
        Cuándo usarla: En plantillas del catálogo, sitemap.xml y datos estructurados JSON-LD.
        Si no opera:   Lanza NoReverseMatch si el slug está vacío.
        """
        return reverse("catalogo:detalle_producto", kwargs={"slug": self.slug})

    @property
    def porcentaje_descuento(self) -> int:
        """Calcula el porcentaje entero de descuento cuando existe un precio_anterior mayor.

        Qué hace:      Calcula round((1 - precio_unidad / precio_anterior) * 100).
        Va hacia:      Retorna un entero (ej. 21 para S/ 55.00 sobre S/ 69.90) o 0 si no hay oferta.
        Depende de:    Atributos precio_unidad y precio_anterior.
        Cuándo usarla: En las tarjetas del catálogo y en la ficha del producto para mostrar '-21%'.
        Si no opera:   Retorna 0 si precio_anterior es nulo o menor/igual a precio_unidad.
        """
        if self.precio_anterior and self.precio_anterior > self.precio_unidad > Decimal("0.00"):
            descuento = (Decimal("1.00") - (self.precio_unidad / self.precio_anterior)) * 100
            return int(round(descuento))
        return 0

    @property
    def monto_ahorro(self) -> Decimal:
        """Calcula cuántos Soles (PEN) ahorra el cliente restando precio_anterior menos precio_unidad.

        Qué hace:      Resta (precio_anterior - precio_unidad) redondeado a 2 decimales.
        Va hacia:      Retorna un Decimal (ej. Decimal('14.90') para 69.90 - 55.00) o Decimal('0.00').
        Depende de:    Atributos precio_anterior y precio_unidad.
        Cuándo usarla: En la ficha de producto y tarjetas para mostrar 'Ahorras S/ 14.90'.
        Si no opera:   Retorna Decimal('0.00') si precio_anterior es nulo o menor/igual a precio_unidad.
        """
        if self.precio_anterior and self.precio_anterior > self.precio_unidad > Decimal("0.00"):
            return (self.precio_anterior - self.precio_unidad).quantize(Decimal("0.01"))
        return Decimal("0.00")

    def clean(self) -> None:
        """Sanitiza textos y valida que los precios del producto sean positivos y coherentes.

        Qué hace:      Limpia nombre/descripción/SKU y verifica que precio_unidad > 0.
        Va hacia:      Normaliza los campos en memoria antes de guardar.
        Depende de:    limpiar_texto_seguro y Decimal.
        Cuándo usarla: En formularios o antes de persistir el producto.
        Si no opera:   Lanza ValidationError si el precio es <= 0 o si precio_anterior <= precio_unidad.
        """
        self.nombre = limpiar_texto_seguro(self.nombre, longitud_maxima=150)
        self.sku = limpiar_texto_seguro(self.sku, longitud_maxima=30).upper()
        if self.descripcion:
            self.descripcion = limpiar_texto_seguro(self.descripcion, longitud_maxima=2000)
        if self.marca:
            self.marca = limpiar_texto_seguro(self.marca, longitud_maxima=80)
        if not self.slug and self.nombre:
            self.slug = slugify(self.nombre)[:170]
        if self.precio_unidad is None or self.precio_unidad <= Decimal("0.00"):
            raise ValidationError("El precio por unidad debe ser mayor a S/ 0.00.")
        if self.precio_anterior is not None and self.precio_anterior <= self.precio_unidad:
            raise ValidationError(
                "El precio regular tachado debe ser mayor que el precio actual de venta."
            )

    def save(self, *args, **kwargs) -> None:
        """Ejecuta la validación de dominio y guarda el producto en TBL_RPRODUCTO.

        Qué hace:      Invoca full_clean() y persiste la instancia en la base de datos.
        Va hacia:      Tabla física TBL_RPRODUCTO.
        Depende de:    clean() y models.Model.save().
        Cuándo usarla: Al crear o actualizar productos desde servicios o el admin.
        Si no opera:   Propaga ValidationError si algún precio o texto es inválido.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class ImagenProducto(models.Model):
    """Fotos del producto con versiones optimizadas en WebP y texto alternativo SEO (TBL_RIMAGEN_PRODUCTO)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="IMA_NID",
        verbose_name="Identificador",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="imagenes",
        db_column="PRO_NID",
        verbose_name="Producto",
    )
    ruta_original = models.CharField(
        max_length=255,
        db_column="IMA_CRUTA_ORIGINAL",
        verbose_name="Ruta del original (privado)",
    )
    ruta_miniatura = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column="IMA_CRUTA_MINIATURA",
        verbose_name="Miniatura (~400 px WebP)",
    )
    ruta_detalle = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column="IMA_CRUTA_DETALLE",
        verbose_name="Detalle (~900 px WebP)",
    )
    texto_alternativo = models.CharField(
        max_length=180,
        null=True,
        blank=True,
        db_column="IMA_CTEXTO_ALT",
        verbose_name="Texto alternativo (alt SEO)",
    )
    orden = models.IntegerField(
        default=1,
        db_column="IMA_NORDEN",
        verbose_name="Orden en la galería",
    )
    es_principal = models.BooleanField(
        default=False,
        db_column="IMA_OPRINCIPAL",
        verbose_name="Imagen principal",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="IMA_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        db_column="IMA_DFECHA_ACTUALIZACION",
        verbose_name="Fecha de última actualización",
    )

    class Meta:
        db_table = "TBL_RIMAGEN_PRODUCTO"
        ordering = ["-es_principal", "orden", "id"]
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de producto"

    def __str__(self) -> str:
        """Devuelve la descripción de la imagen con el nombre de su producto y orden.

        Qué hace:      Formatea el nombre del producto y el número de orden de la foto.
        Va hacia:      Panel administrativo y logs.
        Depende de:    Relación producto y campo orden.
        Cuándo usarla: Automáticamente al representar la instancia como texto.
        Si no opera:   Retorna el ID de la imagen si el producto aún no está asignado.
        """
        return f"Foto {self.orden} de {self.producto.nombre}"

    @property
    def alt_seo(self) -> str:
        """Devuelve siempre un texto alternativo descriptivo para el atributo alt de <img>.

        Qué hace:      Retorna texto_alternativo o genera uno automático con el nombre del producto.
        Va hacia:      Atributo alt="..." en las plantillas de catálogo y detalle (Requisito #10).
        Depende de:    texto_alternativo, producto.nombre y orden.
        Cuándo usarla: En todas las etiquetas <img> del frontend público.
        Si no opera:   Nunca devuelve cadena vacía; siempre entrega un texto descriptivo válido.
        """
        if self.texto_alternativo:
            return self.texto_alternativo
        return f"{self.producto.nombre} – Estilo deportivo Emuná Sport (Vista {self.orden})"

    def clean(self) -> None:
        """Sanitiza el texto alternativo y genera el valor por defecto si se dejó en blanco.

        Qué hace:      Limpia etiquetas HTML de texto_alternativo o asigna el texto SEO automático.
        Va hacia:      Normaliza el campo IMA_CTEXTO_ALT antes de guardar.
        Depende de:    limpiar_texto_seguro y relación producto.
        Cuándo usarla: Al validar la imagen antes de guardarla en la base de datos.
        Si no opera:   Propaga ValidationError si falta la ruta original.
        """
        if self.texto_alternativo:
            self.texto_alternativo = limpiar_texto_seguro(
                self.texto_alternativo, longitud_maxima=180
            )
        elif self.producto_id:
            self.texto_alternativo = (
                f"{self.producto.nombre} – Estilo deportivo Emuná Sport (Vista {self.orden})"
            )[:180]

    def save(self, *args, **kwargs) -> None:
        """Valida y persiste el registro de imagen en TBL_RIMAGEN_PRODUCTO.

        Qué hace:      Ejecuta full_clean() y guarda la fila en la base de datos.
        Va hacia:      Tabla física TBL_RIMAGEN_PRODUCTO.
        Depende de:    clean() y models.Model.save().
        Cuándo usarla: Al registrar fotos de productos desde servicios o cargar_demo.
        Si no opera:   Lanza ValidationError si faltan campos obligatorios.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class Variante(models.Model):
    """Variante de un producto por talla (S, M, L, XL) con su stock actual (TBL_RVARIANTE)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="VAR_NID",
        verbose_name="Identificador",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="variantes",
        db_column="PRO_NID",
        verbose_name="Producto",
    )
    talla = models.CharField(
        max_length=10,
        db_column="VAR_CTALLA",
        verbose_name="Talla",
    )
    color = models.CharField(
        max_length=40,
        blank=True,
        default="",
        db_column="VAR_CCOLOR",
        verbose_name="Color (opcional)",
    )
    modelo = models.CharField(
        max_length=60,
        blank=True,
        default="",
        db_column="VAR_CMODELO",
        verbose_name="Modelo / versión (opcional)",
    )
    sku = models.CharField(
        max_length=40,
        unique=True,
        db_column="VAR_CSKU",
        verbose_name="SKU de la variante",
    )
    cantidad_stock = models.IntegerField(
        default=0,
        db_column="VAR_NCANTIDAD_STOCK",
        verbose_name="Stock actual",
    )
    umbral_stock_bajo = models.IntegerField(
        null=True,
        blank=True,
        db_column="VAR_NUMBRAL_STOCK_BAJO",
        verbose_name="Umbral propio de stock bajo",
    )
    activa = models.BooleanField(
        default=True,
        db_column="VAR_OACTIVA",
        verbose_name="Variante disponible",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="VAR_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        db_column="VAR_DFECHA_ACTUALIZACION",
        verbose_name="Fecha de última actualización",
    )

    class Meta:
        db_table = "TBL_RVARIANTE"
        ordering = ["id"]
        verbose_name = "Variante de talla"
        verbose_name_plural = "Variantes de talla"
        indexes = [
            models.Index(fields=["producto"], name="TBL_RVARIANTE_PRO_NID_IX"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad_stock__gte=0),
                name="TBL_RVARIANTE_STOCK_CK",
            ),
            models.UniqueConstraint(
                fields=["producto", "talla", "color", "modelo"],
                name="TBL_RVARIANTE_PRO_NID_VAR_CTALLA_VAR_CCOLOR_VAR_CMODELO_UK",
            ),
        ]

    def __str__(self) -> str:
        """Devuelve la descripción de la variante indicando producto, talla y stock disponible.

        Qué hace:      Formatea '{producto.nombre} - Talla {talla} (Stock: {cantidad_stock})'.
        Va hacia:      Selectores del panel administrativo y carrito de compras.
        Depende de:    Relación producto y campos talla y cantidad_stock.
        Cuándo usarla: Automáticamente al representar la variante como texto.
        Si no opera:   Retorna el SKU de la variante.
        """
        return f"{self.producto.nombre} – Talla {self.talla} (Stock: {self.cantidad_stock})"

    def clean(self) -> None:
        """Normaliza talla, color, modelo y SKU, y verifica que el stock nunca sea negativo.

        Qué hace:      Convierte talla y SKU a mayúsculas, limpia textos y valida cantidad_stock >= 0.
        Va hacia:      Prepara los campos en memoria cumpliendo las invariantes de TBL_RVARIANTE.
        Depende de:    limpiar_texto_seguro.
        Cuándo usarla: Antes de guardar la variante en la base de datos.
        Si no opera:   Lanza ValidationError si cantidad_stock < 0 o si falta la talla.
        """
        self.talla = limpiar_texto_seguro(self.talla, longitud_maxima=10).upper()
        self.color = limpiar_texto_seguro(self.color, longitud_maxima=40)
        self.modelo = limpiar_texto_seguro(self.modelo, longitud_maxima=60)
        self.sku = limpiar_texto_seguro(self.sku, longitud_maxima=40).upper()
        if not self.talla:
            raise ValidationError("La talla es obligatoria en cada variante.")
        if self.cantidad_stock < 0:
            raise ValidationError("El stock de una variante nunca puede ser negativo.")

    def save(self, *args, **kwargs) -> None:
        """Ejecuta full_clean() y guarda la variante en TBL_RVARIANTE.

        Qué hace:      Valida las invariantes del modelo y persiste los cambios en BD.
        Va hacia:      Tabla física TBL_RVARIANTE.
        Depende de:    clean() y models.Model.save().
        Cuándo usarla: Desde servicios de inventario/catálogo al crear o actualizar variantes.
        Si no opera:   Lanza ValidationError o IntegrityError si viola restricciones únicas.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class ReglaPrecio(models.Model):
    """Reglas de precio escalonado por mayor para un producto (TBL_RREGLA_PRECIO)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="REG_NID",
        verbose_name="Identificador",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="reglas_precio",
        db_column="PRO_NID",
        verbose_name="Producto",
    )
    cantidad_minima = models.IntegerField(
        db_column="REG_NCANTIDAD_MINIMA",
        verbose_name="Desde N unidades",
    )
    precio_unidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column="REG_NPRECIO_UNIDAD",
        verbose_name="Precio unitario por mayor (S/)",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="REG_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        db_column="REG_DFECHA_ACTUALIZACION",
        verbose_name="Fecha de última actualización",
    )

    class Meta:
        db_table = "TBL_RREGLA_PRECIO"
        ordering = ["cantidad_minima"]
        verbose_name = "Regla de precio por mayor"
        verbose_name_plural = "Reglas de precio por mayor"
        constraints = [
            models.UniqueConstraint(
                fields=["producto", "cantidad_minima"],
                name="TBL_RREGLA_PRECIO_PRO_NID_REG_NCANTIDAD_MINIMA_UK",
            ),
        ]

    def __str__(self) -> str:
        """Devuelve la descripción legible del tramo de precio por mayor.

        Qué hace:      Formatea 'Desde {cantidad_minima} u. -> S/ {precio_unidad}'.
        Va hacia:      Panel administrativo y tablas de ahorro en la ficha de producto.
        Depende de:    Campos cantidad_minima y precio_unidad.
        Cuándo usarla: Automáticamente al convertir la regla en cadena.
        Si no opera:   Retorna los valores numéricos disponibles.
        """
        return f"Desde {self.cantidad_minima} u. → S/ {self.precio_unidad}"

    def clean(self) -> None:
        """Verifica que la cantidad mínima sea al menos 2 y el precio sea positivo.

        Qué hace:      Comprueba que cantidad_minima >= 2 y precio_unidad > 0.
        Va hacia:      Valida la coherencia del tramo por mayor antes de guardar.
        Depende de:    Campos cantidad_minima, precio_unidad y producto.
        Cuándo usarla: En el admin o servicios antes de persistir en TBL_RREGLA_PRECIO.
        Si no opera:   Lanza ValidationError si cantidad_minima < 2 o precio_unidad <= 0.
        """
        if self.cantidad_minima < 2:
            raise ValidationError("La cantidad mínima para precio por mayor debe ser de al menos 2.")
        if self.precio_unidad is None or self.precio_unidad <= Decimal("0.00"):
            raise ValidationError("El precio por unidad en la regla debe ser mayor a S/ 0.00.")

    def save(self, *args, **kwargs) -> None:
        """Ejecuta full_clean() y persiste la regla de precio por mayor en TBL_RREGLA_PRECIO.

        Qué hace:      Valida la instancia y guarda la fila en la base de datos.
        Va hacia:      Tabla física TBL_RREGLA_PRECIO.
        Depende de:    clean() y models.Model.save().
        Cuándo usarla: Al configurar tramos de precio por mayor en un producto.
        Si no opera:   Propaga ValidationError si la regla es inválida.
        """
        self.full_clean()
        super().save(*args, **kwargs)



class TipoMovimientoStock(models.TextChoices):
    """Tipos de movimiento de inventario en TBL_TMOVIMIENTO_STOCK."""

    ENTRADA = "ENTRADA", "Entrada de mercadería"
    VENTA = "VENTA", "Salida por venta"
    AJUSTE = "AJUSTE", "Ajuste de inventario"
    DEVOLUCION = "DEVOLUCION", "Devolución por cancelación / rechazo"


class MovimientoStock(models.Model):
    """Cada entrada o salida de stock. Inmutable: no se edita ni se borra (TBL_TMOVIMIENTO_STOCK)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="MOV_NID",
        verbose_name="Identificador",
    )
    variante = models.ForeignKey(
        Variante,
        on_delete=models.PROTECT,
        related_name="movimientos",
        db_column="VAR_NID",
        verbose_name="Variante afectada",
    )
    tipo = models.CharField(
        max_length=15,
        choices=TipoMovimientoStock.choices,
        db_column="MOV_CTIPO",
        verbose_name="Tipo de movimiento",
    )
    cantidad = models.IntegerField(
        db_column="MOV_NCANTIDAD",
        verbose_name="Cantidad con signo (positiva o negativa; distinta de 0)",
    )
    motivo = models.CharField(
        max_length=200,
        db_column="MOV_CMOTIVO",
        verbose_name="Motivo del movimiento",
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_stock",
        db_column="PED_NID",
        verbose_name="Pedido asociado (si aplica)",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_stock_creados",
        db_column="USU_NID_CREADO_POR",
        verbose_name="Usuario que registró el movimiento",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="MOV_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )

    class Meta:
        db_table = "TBL_TMOVIMIENTO_STOCK"
        ordering = ["-fecha_creacion"]
        verbose_name = "Movimiento de stock"
        verbose_name_plural = "Movimientos de stock"
        indexes = [
            models.Index(
                fields=["variante", "fecha_creacion"],
                name="TBL_TMOVIMIENTO_STOCK_VAR_NID_MOV_DFECHA_CREACION_IX",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(cantidad=0),
                name="TBL_TMOVIMIENTO_STOCK_CANTIDAD_CK",
            ),
        ]

    def __str__(self) -> str:
        """Devuelve el resumen legible del movimiento con tipo, cantidad y variante.

        Qué hace:      Formatea '{tipo} {cantidad} unid. - {variante.producto.nombre} ({talla})'.
        Va hacia:      Panel administrativo de auditoría y trazabilidad de inventario.
        Depende de:    Atributos tipo, cantidad y variante.
        Cuándo usarla: Automáticamente al convertir el movimiento en cadena de texto.
        Si no opera:   Retorna 'Movimiento #{id}' si la variante no está disponible.
        """
        signo = "+" if self.cantidad > 0 else ""
        return f"{self.get_tipo_display()} ({signo}{self.cantidad} unid.) – {self.variante}"

    def clean(self) -> None:
        """Valida que la cantidad no sea cero y sanitiza el motivo del movimiento.

        Qué hace:      Comprueba cantidad != 0 y limpia texto del motivo.
        Va hacia:      Validación previa al guardado en TBL_TMOVIMIENTO_STOCK.
        Depende de:    limpiar_texto_seguro y campos cantidad y motivo.
        Cuándo usarla: Automáticamente antes de guardar el movimiento.
        Si no opera:   Lanza ValidationError si cantidad es 0 o motivo está vacío.
        """
        if self.cantidad == 0:
            raise ValidationError("La cantidad del movimiento de stock no puede ser 0.")
        self.motivo = limpiar_texto_seguro(str(self.motivo or ""), longitud_maxima=200)
        if not self.motivo:
            raise ValidationError("El motivo del movimiento de stock es obligatorio.")

    def save(self, *args, **kwargs) -> None:
        """Garantiza la inmutabilidad de los movimientos de stock impidiendo su modificación.

        Qué hace:      Lanza ValidationError si ya existe clave primaria (update bloqueado).
        Va hacia:      Tabla física inmutable TBL_TMOVIMIENTO_STOCK.
        Depende de:    self.pk y models.Model.save().
        Cuándo usarla: Al crear un nuevo registro de movimiento de stock.
        Si no opera:   Bloquea cualquier intento de actualización de un movimiento existente.
        """
        if self.pk:
            raise ValidationError(
                "Los movimientos de stock son inmutables y no se pueden modificar."
            )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:
        """Garantiza la inmutabilidad de los movimientos de stock impidiendo su eliminación.

        Qué hace:      Lanza ValidationError bloqueando el borrado de registros de auditoría.
        Va hacia:      Preserva la integridad de TBL_TMOVIMIENTO_STOCK.
        Depende de:    Regla de auditoría inmutable del estándar.
        Cuándo usarla: Bloquea cualquier invocación a delete() en instancias o QuerySets.
        Si no opera:   Impide la pérdida del rastro histórico de entradas y salidas.
        """
        raise ValidationError(
            "Los movimientos de stock son inmutables y no se pueden eliminar."
        )
