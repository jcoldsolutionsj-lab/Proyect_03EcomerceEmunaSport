"""Modelos de datos de la app núcleo: ConfiguracionTienda y MetodoPago."""
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from django.db import models
from django.templatetags.static import static

from .validadores import limpiar_texto_seguro, validar_telefono_peruano


class TipoMetodoPago(models.TextChoices):
    """Tipos de método de pago soportados por Emuná Sport."""

    YAPE = "YAPE", "Yape"
    PLIN = "PLIN", "Plin"
    EFECTIVO = "EFECTIVO", "Efectivo (entrega presencial)"


class ConfiguracionTienda(models.Model):
    """Ajustes generales de la tienda Emuná Sport (registro único en TBL_RCONFIGURACION_TIENDA)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="CTI_NID",
        verbose_name="Identificador",
    )
    nombre = models.CharField(
        max_length=100,
        default="Emuná Sport",
        db_column="CTI_CNOMBRE",
        verbose_name="Nombre de la tienda",
    )
    numero_whatsapp = models.CharField(
        max_length=15,
        default="999888777",
        db_column="CTI_CNUMERO_WHATSAPP",
        verbose_name="WhatsApp de Richard",
    )
    texto_pie = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        default="Emuná Sport – Estilo deportivo. Envíos a todo el Perú por Shalom y Olva.",
        db_column="CTI_CTEXTO_PIE",
        verbose_name="Texto de pie de página",
    )
    umbral_stock_bajo = models.IntegerField(
        default=3,
        db_column="CTI_NUMBRAL_STOCK_BAJO",
        verbose_name="Umbral de stock bajo por defecto",
    )
    mostrar_marcas = models.BooleanField(
        default=False,
        db_column="CTI_OMOSTRAR_MARCAS",
        verbose_name="Mostrar marcas en el catálogo",
    )
    dias_sin_ventas = models.IntegerField(
        default=30,
        db_column="CTI_NDIAS_SIN_VENTAS",
        verbose_name="Días sin ventas para alerta",
    )
    horas_pedido_pendiente = models.IntegerField(
        default=24,
        db_column="CTI_NHORAS_PEDIDO_PENDIENTE",
        verbose_name="Horas para alerta de pedido pendiente",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="CTI_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        db_column="CTI_DFECHA_ACTUALIZACION",
        verbose_name="Fecha de última actualización",
    )

    class Meta:
        db_table = "TBL_RCONFIGURACION_TIENDA"
        verbose_name = "Configuración de la tienda"
        verbose_name_plural = "Configuración de la tienda"

    def __str__(self) -> str:
        """Devuelve la representación legible de la configuración de la tienda.

        Qué hace:      Formatea el nombre de la tienda y su número de WhatsApp.
        Va hacia:      Retorna un str descriptivo para el admin y los logs.
        Depende de:    Campos nombre y numero_whatsapp del modelo.
        Cuándo usarla: Automáticamente por Django al mostrar la instancia.
        Si no opera:   Retorna el nombre por defecto si algún campo está vacío.
        """
        return f"{self.nombre} (WhatsApp: {self.numero_whatsapp})"

    def clean(self) -> None:
        """Valida que exista un único registro de configuración y que los datos sean válidos.

        Qué hace:      Garantiza el patrón Singleton (id=1), sanitiza textos y valida el celular.
        Va hacia:      Modifica los campos en memoria con valores limpios antes de guardar.
        Depende de:    limpiar_texto_seguro, validar_telefono_peruano y TBL_RCONFIGURACION_TIENDA.
        Cuándo usarla: En formularios del admin o antes de guardar mediante full_clean().
        Si no opera:   Lanza ValidationError si ya existe otro registro o si un umbral es menor a 1.
        """
        if not self.pk and ConfiguracionTienda.objects.exists():
            raise ValidationError("Solo puede existir un registro de Configuración de la Tienda.")
        self.nombre = limpiar_texto_seguro(self.nombre, longitud_maxima=100)
        if self.texto_pie:
            self.texto_pie = limpiar_texto_seguro(self.texto_pie, longitud_maxima=200)
        self.numero_whatsapp = validar_telefono_peruano(self.numero_whatsapp)
        if self.umbral_stock_bajo < 0:
            raise ValidationError("El umbral de stock bajo no puede ser negativo.")
        if self.dias_sin_ventas < 1 or self.horas_pedido_pendiente < 1:
            raise ValidationError("Los días sin ventas y horas de alerta deben ser mayores a 0.")

    def save(self, *args, **kwargs) -> None:
        """Guarda la configuración forzando su validación completa e identificador único.

        Qué hace:      Fija pk=1 si es el primer registro, ejecuta full_clean() y persiste en BD.
        Va hacia:      Tabla física TBL_RCONFIGURACION_TIENDA.
        Depende de:    clean() y models.Model.save().
        Cuándo usarla: Al crear o actualizar la configuración desde servicios o el panel admin.
        Si no opera:   Propaga ValidationError si algún dato no cumple las reglas.
        """
        if not self.pk and not ConfiguracionTienda.objects.exists():
            self.pk = 1
        self.full_clean()
        super().save(*args, **kwargs)


class MetodoPago(models.Model):
    """Formas de pago aceptadas por Emuná Sport (Yape, Plin, Efectivo en TBL_RMETODO_PAGO)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="MPA_NID",
        verbose_name="Identificador",
    )
    tipo = models.CharField(
        max_length=20,
        unique=True,
        choices=TipoMetodoPago.choices,
        db_column="MPA_CTIPO",
        verbose_name="Tipo de método de pago",
    )
    titular = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_column="MPA_CTITULAR",
        verbose_name="Titular de la cuenta",
    )
    numero_cuenta = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_column="MPA_CNUMERO_CUENTA",
        verbose_name="Número copiable (celular Yape/Plin)",
    )
    imagen_qr = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column="MPA_CIMAGEN_QR",
        verbose_name="Ruta de la imagen del QR",
    )
    activo = models.BooleanField(
        default=True,
        db_column="MPA_OACTIVO",
        verbose_name="Método disponible",
    )
    orden = models.IntegerField(
        default=1,
        db_column="MPA_NORDEN",
        verbose_name="Orden de aparición",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="MPA_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        db_column="MPA_DFECHA_ACTUALIZACION",
        verbose_name="Fecha de última actualización",
    )

    class Meta:
        db_table = "TBL_RMETODO_PAGO"
        ordering = ["orden", "id"]
        verbose_name = "Método de pago"
        verbose_name_plural = "Métodos de pago"

    def __str__(self) -> str:
        """Devuelve la representación en texto del método de pago.

        Qué hace:      Muestra el tipo de pago y el titular si está configurado.
        Va hacia:      Retorna un str legible para selectores y panel administrativo.
        Depende de:    Campos tipo y titular del modelo.
        Cuándo usarla: Automáticamente al representar la instancia como cadena.
        Si no opera:   Retorna únicamente el código del tipo si no hay titular.
        """
        if self.titular:
            return f"{self.get_tipo_display()} – {self.titular}"
        return self.get_tipo_display()

    def clean(self) -> None:
        """Sanitiza y valida la coherencia de los datos del método de pago.

        Qué hace:      Limpia textos y exige titular y número cuando Yape o Plin están activos.
        Va hacia:      Normaliza los atributos de la instancia antes de guardar en BD.
        Depende de:    limpiar_texto_seguro y TipoMetodoPago.
        Cuándo usarla: Al validar desde el admin o servicios antes de persistir.
        Si no opera:   Lanza ValidationError si se activa Yape/Plin sin titular o sin número.
        """
        if self.titular:
            self.titular = limpiar_texto_seguro(self.titular, longitud_maxima=100)
        if self.numero_cuenta:
            self.numero_cuenta = limpiar_texto_seguro(self.numero_cuenta, longitud_maxima=20)
        if self.activo and self.tipo in {TipoMetodoPago.YAPE, TipoMetodoPago.PLIN}:
            if not self.titular or not self.numero_cuenta:
                raise ValidationError(
                    "Para activar Yape o Plin es obligatorio indicar el titular y el número."
                )

    def save(self, *args, **kwargs) -> None:
        """Persiste el método de pago ejecutando las validaciones de dominio.

        Qué hace:      Invoca full_clean() y guarda la fila en TBL_RMETODO_PAGO.
        Va hacia:      Tabla física TBL_RMETODO_PAGO.
        Depende de:    clean() y models.Model.save().
        Cuándo usarla: Al crear o editar métodos de pago desde servicios o el admin.
        Si no opera:   Lanza ValidationError si los datos están incompletos.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def url_qr(self) -> str:
        """Resuelve de forma segura la URL del QR (URL externa/R2 o estático disponible).

        Qué hace:      Devuelve URL directa si es http(s)/R2, o verifica si el estático existe sin fallar en producción.
        Va hacia:      Atributo src del QR en parcial_seguimiento_pedido.html.
        Depende de:    settings.R2_PUBLIC_URL, staticfiles_storage y finders.
        Cuándo usarla: Al mostrar la tarjeta de pago con Yape/Plin al cliente.
        Si no opera:   Retorna '' si el archivo estático no está publicado en Render para evitar HTTP 500.
        """
        ruta = str(self.imagen_qr or "QR_yape_richardRamos.jpeg").strip()
        if not ruta:
            return ""
        if ruta.startswith(("http://", "https://", "/")):
            return ruta
        r2_pub = str(getattr(settings, "R2_PUBLIC_URL", "") or "").strip().rstrip("/")
        if r2_pub and ruta.startswith(("webp/", "productos/", "pagos/", "qr/")):
            return f"{r2_pub}/{ruta.lstrip('/')}"
        try:
            if staticfiles_storage.exists(ruta):
                return staticfiles_storage.url(ruta)
        except Exception:
            pass
        if finders.find(ruta) or (Path(settings.STATIC_ROOT) / ruta).exists():
            return static(ruta)
        return ""
