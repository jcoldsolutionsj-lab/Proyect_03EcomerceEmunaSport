"""Modelos de datos de la app pedidos: Pedido, ItemPedido y RegistroEstadoPedido."""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from simple_history.models import HistoricalRecords

from apps.nucleo.validadores import (
    limpiar_texto_seguro,
    validar_dni_peruano,
    validar_telefono_peruano,
)


class EstadoPedido(models.TextChoices):
    """Estados permitidos de un pedido en Emuná Sport (doc 03 y diccionario)."""

    NUEVO = "NUEVO", "Nuevo (falta cotizar envío)"
    COTIZADO = "COTIZADO", "Cotizado (esperando pago o entrega)"
    PAGADO = "PAGADO", "Pago confirmado (stock descontado)"
    ENVIADO = "ENVIADO", "Enviado (en agencia o delivery)"
    ENTREGADO = "ENTREGADO", "Entregado al cliente"
    CANCELADO = "CANCELADO", "Cancelado"
    RECHAZADO = "RECHAZADO", "Rechazado"


class OrigenPedido(models.TextChoices):
    """Canal donde se originó el pedido."""

    WEB = "WEB", "Tienda Web (enviado por el cliente)"
    PRESENCIAL = "PRESENCIAL", "Venta Presencial (registrada por Richard)"


class TipoEntrega(models.TextChoices):
    """Modalidades de entrega reales del negocio de Richard (doc 02)."""

    AGENCIA = "AGENCIA", "Envío a provincia por agencia (Shalom / Olva)"
    DELIVERY_LIMA = "DELIVERY_LIMA", "Delivery en Lima (cotizado por Richard)"
    PUNTO_ENCUENTRO = "PUNTO_ENCUENTRO", "Punto de encuentro en Lima (S/ 0.00 - pago al recibir)"
    RECOJO = "RECOJO", "Recojo acordado (S/ 0.00)"


class AgenciaEnvio(models.TextChoices):
    """Agencias de transporte interprovincial habilitadas."""

    SHALOM = "SHALOM", "Agencia Shalom"
    OLVA = "OLVA", "Olva Courier"
    OTRA = "OTRA", "Otra agencia"


class Pedido(models.Model):
    """Pedido de un cliente: venta web o venta presencial de Richard (TBL_TPEDIDO)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="PED_NID",
        verbose_name="Identificador",
    )
    codigo = models.CharField(
        max_length=20,
        unique=True,
        db_column="PED_CCODIGO",
        verbose_name="Código público del pedido",
    )
    estado = models.CharField(
        max_length=15,
        choices=EstadoPedido.choices,
        default=EstadoPedido.NUEVO,
        db_column="PED_CESTADO",
        verbose_name="Estado",
    )
    origen = models.CharField(
        max_length=15,
        choices=OrigenPedido.choices,
        default=OrigenPedido.WEB,
        db_column="PED_CORIGEN",
        verbose_name="Origen del pedido",
    )
    cliente_nombre = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        db_column="PED_CCLIENTE_NOMBRE",
        verbose_name="Nombres y apellidos del cliente",
    )
    cliente_dni = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        db_column="PED_CCLIENTE_DNI",
        verbose_name="DNI del cliente (8 dígitos - privado)",
    )
    cliente_telefono = models.CharField(
        max_length=9,
        null=True,
        blank=True,
        db_column="PED_CCLIENTE_TELEFONO",
        verbose_name="Celular del cliente (9 dígitos - privado)",
    )
    tipo_entrega = models.CharField(
        max_length=20,
        choices=TipoEntrega.choices,
        default=TipoEntrega.PUNTO_ENCUENTRO,
        db_column="PED_CTIPO_ENTREGA",
        verbose_name="Modalidad de entrega",
    )
    agencia = models.CharField(
        max_length=10,
        choices=AgenciaEnvio.choices,
        null=True,
        blank=True,
        db_column="PED_CAGENCIA",
        verbose_name="Agencia de envío",
    )
    agencia_ciudad = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        db_column="PED_CAGENCIA_CIUDAD",
        verbose_name="Ciudad de destino",
    )
    agencia_referencia = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        db_column="PED_CAGENCIA_REFERENCIA",
        verbose_name="Sede o referencia de agencia",
    )
    punto_encuentro = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        db_column="PED_CPUNTO_ENCUENTRO",
        verbose_name="Punto de encuentro o dirección en Lima",
    )
    entrega_programada = models.DateTimeField(
        null=True,
        blank=True,
        db_column="PED_DENTREGA_PROGRAMADA",
        verbose_name="Fecha y hora acordadas de entrega",
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        db_column="PED_NSUBTOTAL",
        verbose_name="Subtotal de camisetas (PEN)",
    )
    costo_envio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_column="PED_NCOSTO_ENVIO",
        verbose_name="Costo de envío (PEN)",
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        db_column="PED_NTOTAL",
        verbose_name="Total final (PEN)",
    )
    metodo_pago = models.ForeignKey(
        "nucleo.MetodoPago",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",
        db_column="MPA_NID",
        verbose_name="Método de pago confirmado",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos_registrados",
        db_column="USU_NID_CREADO_POR",
        verbose_name="Registrado por",
    )
    notas = models.TextField(
        null=True,
        blank=True,
        db_column="PED_CNOTAS",
        verbose_name="Notas adicionales",
    )
    fecha_cotizado = models.DateTimeField(
        null=True,
        blank=True,
        db_column="PED_DFECHA_COTIZADO",
        verbose_name="Fecha de cotización",
    )
    fecha_pagado = models.DateTimeField(
        null=True,
        blank=True,
        db_column="PED_DFECHA_PAGADO",
        verbose_name="Fecha de confirmación de pago",
    )
    fecha_enviado = models.DateTimeField(
        null=True,
        blank=True,
        db_column="PED_DFECHA_ENVIADO",
        verbose_name="Fecha de despacho / envío",
    )
    fecha_entregado = models.DateTimeField(
        null=True,
        blank=True,
        db_column="PED_DFECHA_ENTREGADO",
        verbose_name="Fecha de entrega al cliente",
    )
    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        db_column="PED_DFECHA_CIERRE",
        verbose_name="Fecha de cancelación o rechazo",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="PED_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        db_column="PED_DFECHA_ACTUALIZACION",
        verbose_name="Fecha de última actualización",
    )

    history = HistoricalRecords(
        table_name="TBL_HPEDIDO",
        custom_model_name="HistorialPedido",
        history_id_field=models.BigAutoField(
            primary_key=True,
            db_column="HPE_NID",
            verbose_name="Identificador del historial",
        ),
    )

    class Meta:
        db_table = "TBL_TPEDIDO"
        ordering = ["-fecha_creacion"]
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        indexes = [
            models.Index(
                fields=["estado", "fecha_creacion"],
                name="TBL_TPEDIDO_PED_CESTADO_PED_DFECHA_CREACION_IX",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    total=F("subtotal")
                    + Coalesce(
                        F("costo_envio"),
                        models.Value(
                            Decimal("0.00"),
                            output_field=models.DecimalField(max_digits=10, decimal_places=2),
                        ),
                    )
                ),
                name="TBL_TPEDIDO_TOTAL_CK",
            ),
        ]

    def __str__(self) -> str:
        """Devuelve el código del pedido, el cliente y su estado actual.

        Qué hace:      Formatea una representación legible del pedido.
        Va hacia:      Panel de administración, bitácoras y selectores.
        Depende de:    Atributos codigo, cliente_nombre y estado.
        Cuándo usarla: Automáticamente al convertir la instancia Pedido en cadena.
        Si no opera:   Muestra 'Cliente presencial' si cliente_nombre está vacío.
        """
        cliente = self.cliente_nombre or "Cliente presencial"
        return f"{self.codigo} – {cliente} ({self.estado})"

    @property
    def dni_enmascarado(self) -> str:
        """Devuelve el DNI ocultando los primeros 6 dígitos para vistas públicas seguras.

        Qué hace:      Enmascara el DNI mostrando solo los últimos 2 dígitos (ej. ******45).
        Va hacia:      Plantillas públicas y respuestas de seguimiento sin exponer datos privados.
        Depende de:    Atributo cliente_dni de la instancia.
        Cuándo usarla: En la página pública /pedidos/<codigo>/ o resúmenes al cliente.
        Si no opera:   Retorna cadena vacía si el pedido no registró DNI.
        """
        if not self.cliente_dni or len(self.cliente_dni) < 2:
            return ""
        return f"******{self.cliente_dni[-2:]}"

    def clean(self) -> None:
        """Sanitiza textos y valida las reglas de negocio según el origen y modalidad de entrega.

        Qué hace:      Limpia HTML, valida DNI/teléfono y recalcula total = subtotal + costo_envio.
        Va hacia:      Normaliza los atributos del modelo en memoria antes de persistir.
        Depende de:    limpiar_texto_seguro, validar_dni_peruano y validar_telefono_peruano.
        Cuándo usarla: Antes de guardar mediante full_clean().
        Si no opera:   Lanza ValidationError con mensajes en español claros para cada campo.
        """
        self.codigo = limpiar_texto_seguro(self.codigo, longitud_maxima=20).upper()
        if self.cliente_nombre:
            self.cliente_nombre = limpiar_texto_seguro(self.cliente_nombre, longitud_maxima=150)
        if self.agencia_ciudad:
            self.agencia_ciudad = limpiar_texto_seguro(self.agencia_ciudad, longitud_maxima=80)
        if self.agencia_referencia:
            self.agencia_referencia = limpiar_texto_seguro(
                self.agencia_referencia, longitud_maxima=200
            )
        if self.punto_encuentro:
            self.punto_encuentro = limpiar_texto_seguro(self.punto_encuentro, longitud_maxima=200)
        if self.notas:
            self.notas = limpiar_texto_seguro(self.notas, longitud_maxima=1000)

        if self.origen == OrigenPedido.WEB:
            if not self.cliente_nombre:
                raise ValidationError(
                    {"cliente_nombre": "El nombre y apellido son obligatorios en pedidos web."}
                )
            if not self.cliente_telefono:
                raise ValidationError(
                    {
                        "cliente_telefono": (
                            "El celular de contacto es obligatorio en pedidos web."
                        )
                    }
                )

        if self.cliente_telefono:
            self.cliente_telefono = validar_telefono_peruano(self.cliente_telefono)

        if self.tipo_entrega == TipoEntrega.AGENCIA:
            if not self.cliente_dni:
                raise ValidationError(
                    {
                        "cliente_dni": (
                            "El DNI de 8 dígitos es obligatorio para envíos por agencia "
                            "(Shalom / Olva)."
                        )
                    }
                )
            if not self.agencia:
                raise ValidationError(
                    {"agencia": "Debes seleccionar la agencia de envío (Shalom, Olva u Otra)."}
                )
            if not self.agencia_ciudad:
                raise ValidationError(
                    {"agencia_ciudad": "Indica la ciudad de destino para el envío por agencia."}
                )

        if self.cliente_dni:
            self.cliente_dni = validar_dni_peruano(self.cliente_dni)

        envio_sumar = self.costo_envio if self.costo_envio is not None else Decimal("0.00")
        self.total = (self.subtotal or Decimal("0.00")) + envio_sumar

    def save(self, *args, **kwargs) -> None:
        """Valida las invariantes del pedido y lo guarda en TBL_TPEDIDO.

        Qué hace:      Ejecuta full_clean() y persiste la instancia en la base de datos.
        Va hacia:      Tabla física TBL_TPEDIDO (y copia en TBL_HPEDIDO).
        Depende de:    clean() y models.Model.save().
        Cuándo usarla: Desde los servicios de creación o actualización de pedidos.
        Si no opera:   Propaga ValidationError o IntegrityError si no cumple las reglas.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class ItemPedido(models.Model):
    """Líneas del pedido con copia (snapshot) de nombre, talla y precio (TBL_TPEDIDO_ITEM)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="ITE_NID",
        verbose_name="Identificador",
    )
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="items",
        db_column="PED_NID",
        verbose_name="Pedido",
    )
    variante = models.ForeignKey(
        "catalogo.Variante",
        on_delete=models.PROTECT,
        related_name="items_pedido",
        db_column="VAR_NID",
        verbose_name="Variante comprada",
    )
    nombre_producto = models.CharField(
        max_length=150,
        db_column="ITE_CNOMBRE_PRODUCTO",
        verbose_name="Nombre del producto (copia)",
    )
    sku = models.CharField(
        max_length=40,
        db_column="ITE_CSKU",
        verbose_name="SKU de variante (copia)",
    )
    talla = models.CharField(
        max_length=10,
        db_column="ITE_CTALLA",
        verbose_name="Talla (copia)",
    )
    color = models.CharField(
        max_length=40,
        blank=True,
        default="",
        db_column="ITE_CCOLOR",
        verbose_name="Color (copia)",
    )
    precio_unidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column="ITE_NPRECIO_UNIDAD",
        verbose_name="Precio unitario aplicado (PEN)",
    )
    cantidad = models.IntegerField(
        db_column="ITE_NCANTIDAD",
        verbose_name="Cantidad",
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column="ITE_NSUBTOTAL",
        verbose_name="Subtotal de la línea (PEN)",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="ITE_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        db_column="ITE_DFECHA_ACTUALIZACION",
        verbose_name="Fecha de última actualización",
    )

    class Meta:
        db_table = "TBL_TPEDIDO_ITEM"
        ordering = ["id"]
        verbose_name = "Ítem del pedido"
        verbose_name_plural = "Ítems del pedido"
        constraints = [
            models.CheckConstraint(
                condition=Q(cantidad__gte=1),
                name="TBL_TPEDIDO_ITEM_CANTIDAD_CK",
            ),
        ]

    def __str__(self) -> str:
        """Devuelve el resumen del ítem con cantidad, producto y talla.

        Qué hace:      Formatea una cadena con cantidad, nombre_producto, talla y subtotal.
        Va hacia:      Panel de administración, PDF y mensajes de WhatsApp.
        Depende de:    Atributos cantidad, nombre_producto, talla y subtotal.
        Cuándo usarla: Al representar textualmente una línea del pedido.
        Si no opera:   Retorna representación básica con los valores disponibles.
        """
        return f"{self.cantidad}x {self.nombre_producto} (Talla {self.talla}) – S/ {self.subtotal}"

    def clean(self) -> None:
        """Valida que la cantidad sea al menos 1 y calcula el subtotal exacto de la línea.

        Qué hace:      Verifica cantidad >= 1 y calcula subtotal = precio_unidad * cantidad.
        Va hacia:      Actualiza el atributo subtotal en memoria antes de guardar.
        Depende de:    Atributos cantidad y precio_unidad.
        Cuándo usarla: Antes de guardar mediante full_clean().
        Si no opera:   Lanza ValidationError si la cantidad es menor a 1.
        """
        if not self.cantidad or self.cantidad < 1:
            raise ValidationError({"cantidad": "La cantidad mínima por ítem es 1 unidad."})
        if self.precio_unidad is None or self.precio_unidad <= Decimal("0.00"):
            raise ValidationError({"precio_unidad": "El precio unitario debe ser mayor a S/ 0.00."})
        self.subtotal = (self.precio_unidad * Decimal(self.cantidad)).quantize(Decimal("0.01"))

    def save(self, *args, **kwargs) -> None:
        """Valida y guarda la línea del pedido en TBL_TPEDIDO_ITEM.

        Qué hace:      Ejecuta full_clean() y persiste la fila con los datos snapshot.
        Va hacia:      Tabla física TBL_TPEDIDO_ITEM.
        Depende de:    clean() y models.Model.save().
        Cuándo usarla: Al registrar las líneas de un pedido en servicios.py.
        Si no opera:   Propaga ValidationError si la cantidad o precio son inválidos.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class RegistroEstadoPedido(models.Model):
    """Bitácora inmutable de cada cambio de estado de un pedido (TBL_LPEDIDO_ESTADO)."""

    id = models.BigAutoField(
        primary_key=True,
        db_column="PES_NID",
        verbose_name="Identificador",
    )
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="historial_estados",
        db_column="PED_NID",
        verbose_name="Pedido",
    )
    estado_anterior = models.CharField(
        max_length=15,
        choices=EstadoPedido.choices,
        null=True,
        blank=True,
        db_column="PES_CESTADO_ANTERIOR",
        verbose_name="Estado anterior",
    )
    estado_nuevo = models.CharField(
        max_length=15,
        choices=EstadoPedido.choices,
        db_column="PES_CESTADO_NUEVO",
        verbose_name="Estado nuevo",
    )
    cambiado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cambios_estado_pedido",
        db_column="USU_NID_CAMBIADO_POR",
        verbose_name="Cambiado por",
    )
    nota = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column="PES_CNOTA",
        verbose_name="Nota del cambio",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="PES_DFECHA_CREACION",
        verbose_name="Fecha de creación",
    )

    class Meta:
        db_table = "TBL_LPEDIDO_ESTADO"
        ordering = ["fecha_creacion", "id"]
        verbose_name = "Registro de estado del pedido"
        verbose_name_plural = "Registros de estado de pedidos"
        indexes = [
            models.Index(
                fields=["pedido", "fecha_creacion"],
                name="TBL_LPEDIDO_ESTADO_PED_NID_PES_DFECHA_CREACION_IX",
            ),
        ]

    def __str__(self) -> str:
        """Devuelve la transición de estado registrada en la bitácora.

        Qué hace:      Formatea el cambio desde estado_anterior hacia estado_nuevo.
        Va hacia:      Panel de administración y auditoría del pedido.
        Depende de:    Atributos pedido_id, estado_anterior y estado_nuevo.
        Cuándo usarla: Automáticamente al mostrar la instancia en texto.
        Si no opera:   Muestra 'INICIO' cuando estado_anterior es nulo.
        """
        origen = self.estado_anterior or "INICIO"
        return f"{self.pedido.codigo}: {origen} → {self.estado_nuevo}"

    def save(self, *args, **kwargs) -> None:
        """Garantiza que el registro de bitácora sea inmutable una vez creado.

        Qué hace:      Impide actualizar un registro existente y sanitiza la nota opcional.
        Va hacia:      Tabla física inmutable TBL_LPEDIDO_ESTADO.
        Depende de:    limpiar_texto_seguro y models.Model.save().
        Cuándo usarla: Al insertar un nuevo evento de estado de un pedido.
        Si no opera:   Lanza ValidationError si se intenta modificar un registro ya creado.
        """
        if self.pk:
            raise ValidationError(
                "Los registros de estado del pedido (TBL_LPEDIDO_ESTADO) son inmutables."
            )
        if self.nota:
            self.nota = limpiar_texto_seguro(self.nota, longitud_maxima=255)
        super().save(*args, **kwargs)
