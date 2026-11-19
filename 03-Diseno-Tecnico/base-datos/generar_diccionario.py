# -*- coding: utf-8 -*-
"""Generador del diccionario de datos de Emuná Sport.

Qué hace:      Lee la definición de tablas de este archivo y genera el diccionario
               en Markdown, en Excel y el modelo Entidad-Relación en Mermaid.
Va hacia:      diccionario-datos.md, diccionario-datos.xlsx y modelo-er.md
               (en esta misma carpeta).
Depende de:    openpyxl (solo para el Excel) y de 12-estandar-base-datos.md.
La llama:      Jonathan, a mano:  python generar_diccionario.py
Cuándo usarla: Cada vez que cambie un modelo. Se edita SOLO este archivo.
Si no opera:   Los tres archivos quedan desactualizados. Si una tabla o columna
               no cumple el estándar, el script se detiene y dice cuál.
"""
import re
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent

# --------------------------------------------------------------------------
# Definición de tablas.  Columna: (nombre, campo_django, tipo_sql, nulo, clave, descripcion)
#   nulo  : "N" no admite nulo, "S" admite nulo
#   clave : "PK", "UK", "FK:TBL_xxx", "FK:TBL_xxx|UK", "" (ninguna)
#   Una descripción que termina en "(privado)" marca un dato sensible.
# --------------------------------------------------------------------------
TABLAS = [
    dict(nombre="TBL_RCONFIGURACION_TIENDA", sigla="CTI", clase="ConfiguracionTienda", app="nucleo",
         tipo="Referencia", descripcion="Ajustes generales de la tienda (registro único).",
         columnas=[
             ("CTI_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("CTI_CNOMBRE", "nombre", "varchar(100)", "N", "", "Nombre de la tienda"),
             ("CTI_CNUMERO_WHATSAPP", "numero_whatsapp", "varchar(15)", "N", "", "WhatsApp de Richard"),
             ("CTI_CTEXTO_PIE", "texto_pie", "varchar(200)", "S", "", "Texto de pie de página"),
             ("CTI_NUMBRAL_STOCK_BAJO", "umbral_stock_bajo", "integer", "N", "", "Umbral de stock bajo por defecto"),
             ("CTI_OMOSTRAR_MARCAS", "mostrar_marcas", "boolean", "N", "", "Mostrar marcas en el catálogo (apagado por defecto)"),
             ("CTI_NDIAS_SIN_VENTAS", "dias_sin_ventas", "integer", "N", "", "Días sin ventas para la alerta del tablero (propuesta, Fase 4)"),
             ("CTI_NHORAS_PEDIDO_PENDIENTE", "horas_pedido_pendiente", "integer", "N", "", "Horas para avisar de un pedido pendiente (propuesta, Fase 4)"),
         ]),
    dict(nombre="TBL_RMETODO_PAGO", sigla="MPA", clase="MetodoPago", app="nucleo",
         tipo="Referencia", descripcion="Formas de pago aceptadas (Yape, Plin, efectivo).",
         columnas=[
             ("MPA_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("MPA_CTIPO", "tipo", "varchar(20)", "N", "UK", "YAPE, PLIN o EFECTIVO"),
             ("MPA_CTITULAR", "titular", "varchar(100)", "S", "", "Titular de la cuenta (no aplica a EFECTIVO)"),
             ("MPA_CNUMERO_CUENTA", "numero_cuenta", "varchar(20)", "S", "", "Número copiable (no aplica a EFECTIVO)"),
             ("MPA_CIMAGEN_QR", "imagen_qr", "varchar(255)", "S", "", "Ruta de la imagen del QR; no va al repositorio"),
             ("MPA_OACTIVO", "activo", "boolean", "N", "", "Método disponible"),
             ("MPA_NORDEN", "orden", "integer", "N", "", "Orden de aparición"),
         ]),
    dict(nombre="TBL_RCATEGORIA", sigla="CAT", clase="Categoria", app="catalogo",
         tipo="Referencia", descripcion="Categorías para organizar el catálogo (uso, colección o tela).",
         columnas=[
             ("CAT_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("CAT_CNOMBRE", "nombre", "varchar(80)", "N", "", "Nombre"),
             ("CAT_CSLUG", "slug", "varchar(100)", "N", "UK", "Texto para la URL"),
             ("CAT_NORDEN", "orden", "integer", "N", "", "Orden de aparición"),
             ("CAT_OACTIVA", "activa", "boolean", "N", "", "Categoría visible"),
         ]),
    dict(nombre="TBL_REQUIPO", sigla="EQU", clase="Equipo", app="catalogo",
         tipo="Referencia", descripcion="Equipos, selecciones, clubes y líneas con alias para búsqueda e IA.",
         columnas=[
             ("EQU_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("EQU_CNOMBRE", "nombre", "varchar(80)", "N", "UK", "Nombre del equipo o línea"),
             ("EQU_CSLUG", "slug", "varchar(100)", "N", "UK", "Texto para la URL"),
             ("EQU_CTIPO", "tipo", "varchar(20)", "N", "", "SELECCION, CLUB o ORIGINAL"),
             ("EQU_CALIAS_BUSQUEDA", "alias_busqueda", "varchar(200)", "N", "", "Alias / apodos separados por coma"),
             ("EQU_NORDEN", "orden", "integer", "N", "", "Orden de aparición"),
             ("EQU_OACTIVO", "activo", "boolean", "N", "", "Equipo activo"),
         ]),
    dict(nombre="TBL_RPRODUCTO", sigla="PRO", clase="Producto", app="catalogo",
         tipo="Referencia", descripcion="Camisetas u otros productos del catálogo.",
         columnas=[
             ("PRO_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("CAT_NID", "categoria", "bigint", "N", "FK:TBL_RCATEGORIA", "Categoría"),
             ("EQU_NID", "equipo", "bigint", "S", "FK:TBL_REQUIPO", "Equipo / Selección / Club"),
             ("PRO_CNOMBRE", "nombre", "varchar(150)", "N", "", "Nombre"),
             ("PRO_CSLUG", "slug", "varchar(170)", "N", "UK", "Texto para la URL"),
             ("PRO_CSKU", "sku", "varchar(30)", "N", "UK", "Código interno, ej. EMU-001"),
             ("PRO_CEQUIPACION", "equipacion", "varchar(20)", "N", "", "Versión: LOCAL, ALTERNA, ESPECIAL, RETRO o ENTRENAMIENTO"),
             ("PRO_CTEMPORADA", "temporada", "varchar(20)", "N", "", "Temporada, ej. 2026-2027"),
             ("PRO_CPALABRAS_CLAVE", "palabras_clave", "varchar(200)", "N", "", "Sinónimos de búsqueda para web y chat IA"),
             ("PRO_CDESCRIPCION", "descripcion", "text", "S", "", "Descripción"),
             ("PRO_CMARCA", "marca", "varchar(80)", "S", "", "Marca (opcional; solo se muestra si está activada)"),
             ("PRO_NPRECIO_UNIDAD", "precio_unidad", "numeric(10,2)", "N", "", "Precio base o de oferta actual por unidad en PEN (ej. 55.00)"),
             ("PRO_NPRECIO_ANTERIOR", "precio_anterior", "numeric(10,2)", "S", "", "Precio regular tachado en PEN (opcional, ej. 69.90)"),
             ("PRO_OACTIVO", "activo", "boolean", "N", "", "Visible en la web"),
             ("PRO_ODESTACADO", "destacado", "boolean", "N", "", "Destacado en el inicio"),
         ]),
    dict(nombre="TBL_RIMAGEN_PRODUCTO", sigla="IMA", clase="ImagenProducto", app="catalogo",
         tipo="Referencia", descripcion="Fotos del producto con sus versiones generadas.",
         columnas=[
             ("IMA_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("PRO_NID", "producto", "bigint", "N", "FK:TBL_RPRODUCTO", "Producto"),
             ("IMA_CRUTA_ORIGINAL", "ruta_original", "varchar(255)", "N", "", "Ruta del original (bucket privado)"),
             ("IMA_CRUTA_MINIATURA", "ruta_miniatura", "varchar(255)", "S", "", "Miniatura de unos 400 px en WebP"),
             ("IMA_CRUTA_DETALLE", "ruta_detalle", "varchar(255)", "S", "", "Detalle de unos 900 px en WebP"),
             ("IMA_CTEXTO_ALT", "texto_alternativo", "varchar(180)", "S", "", "Texto alternativo (alt) para SEO y accesibilidad; si es nulo usa el nombre del producto"),
             ("IMA_NORDEN", "orden", "integer", "N", "", "Orden en la galería"),
             ("IMA_OPRINCIPAL", "es_principal", "boolean", "N", "", "Imagen principal del producto"),
         ]),
    dict(nombre="TBL_RVARIANTE", sigla="VAR", clase="Variante", app="catalogo",
         tipo="Referencia", descripcion="Variante de un producto (talla obligatoria; color y modelo opcionales) con su stock.",
         columnas=[
             ("VAR_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("PRO_NID", "producto", "bigint", "N", "FK:TBL_RPRODUCTO", "Producto"),
             ("VAR_CTALLA", "talla", "varchar(10)", "N", "", "Talla (obligatoria)"),
             ("VAR_CCOLOR", "color", "varchar(40)", "N", "", "Color; vacío si no aplica"),
             ("VAR_CMODELO", "modelo", "varchar(60)", "N", "", "Modelo; vacío si no aplica"),
             ("VAR_CSKU", "sku", "varchar(40)", "N", "UK", "Código único de la variante"),
             ("VAR_NCANTIDAD_STOCK", "cantidad_stock", "integer", "N", "", "Stock actual (mayor o igual a 0). Solo cambia por un MovimientoStock"),
             ("VAR_NUMBRAL_STOCK_BAJO", "umbral_stock_bajo", "integer", "S", "", "Umbral propio; si es nulo se usa el de la tienda"),
             ("VAR_OACTIVA", "activa", "boolean", "N", "", "Variante disponible"),
         ],
         notas=["Restricción única: (PRO_NID, VAR_CTALLA, VAR_CCOLOR, VAR_CMODELO). Color y modelo van vacíos (no nulos) para que la restricción funcione en PostgreSQL."]),
    dict(nombre="TBL_RREGLA_PRECIO", sigla="REG", clase="ReglaPrecio", app="catalogo",
         tipo="Referencia", descripcion="Precio por mayor: desde N unidades, precio S/ X.",
         columnas=[
             ("REG_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("PRO_NID", "producto", "bigint", "N", "FK:TBL_RPRODUCTO", "Producto"),
             ("REG_NCANTIDAD_MINIMA", "cantidad_minima", "integer", "N", "", "Desde N unidades del mismo producto"),
             ("REG_NPRECIO_UNIDAD", "precio_unidad", "numeric(10,2)", "N", "", "Precio por unidad aplicado en PEN"),
         ],
         notas=["Restricción única: (PRO_NID, REG_NCANTIDAD_MINIMA)."]),
    dict(nombre="TBL_TMOVIMIENTO_STOCK", sigla="MOV", clase="MovimientoStock", app="inventario",
         tipo="Transacción", inmutable=True, descripcion="Cada entrada o salida de stock. Inmutable: no se edita ni se borra.",
         columnas=[
             ("MOV_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("VAR_NID", "variante", "bigint", "N", "FK:TBL_RVARIANTE", "Variante afectada"),
             ("MOV_CTIPO", "tipo", "varchar(15)", "N", "", "ENTRADA, VENTA, AJUSTE o DEVOLUCION"),
             ("MOV_NCANTIDAD", "cantidad", "integer", "N", "", "Cantidad con signo; no puede ser 0"),
             ("MOV_CMOTIVO", "motivo", "varchar(200)", "N", "", "Motivo del movimiento"),
             ("PED_NID", "pedido", "bigint", "S", "FK:TBL_TPEDIDO", "Pedido que lo originó (si aplica)"),
             ("USU_NID_CREADO_POR", "creado_por", "bigint", "S", "FK:auth_user", "Quién lo registró"),
         ],
         notas=["Sin fecha de actualización (inmutable). Candidatos a trigger: TRG_UPD_MOVIMIENTO_STOCK_BLOQUEO y TRG_DEL_MOVIMIENTO_STOCK_BLOQUEO."]),
    dict(nombre="TBL_TPEDIDO", sigla="PED", clase="Pedido", app="pedidos",
         tipo="Transacción", descripcion="Pedido de un cliente: venta web o venta presencial de Richard.",
         columnas=[
             ("PED_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("PED_CCODIGO", "codigo", "varchar(20)", "N", "UK", "Código público no adivinable, ej. EMU-7K3Q9X"),
             ("PED_CESTADO", "estado", "varchar(15)", "N", "", "NUEVO, COTIZADO, PAGADO, ENVIADO, ENTREGADO, CANCELADO o RECHAZADO"),
             ("PED_CORIGEN", "origen", "varchar(15)", "N", "", "WEB (el cliente lo envió) o PRESENCIAL (Richard lo registró)"),
             ("PED_CCLIENTE_NOMBRE", "cliente_nombre", "varchar(150)", "S", "", "Nombres y apellidos; obligatorio en pedidos WEB"),
             ("PED_CCLIENTE_DNI", "cliente_dni", "varchar(8)", "S", "", "DNI de 8 dígitos; obligatorio solo en entrega por AGENCIA (privado)"),
             ("PED_CCLIENTE_TELEFONO", "cliente_telefono", "varchar(9)", "S", "", "Teléfono de 9 dígitos que empieza con 9; obligatorio en pedidos WEB (privado)"),
             ("PED_CTIPO_ENTREGA", "tipo_entrega", "varchar(20)", "N", "", "AGENCIA, DELIVERY_LIMA, PUNTO_ENCUENTRO o RECOJO"),
             ("PED_CAGENCIA", "agencia", "varchar(10)", "S", "", "SHALOM, OLVA u OTRA; solo en AGENCIA"),
             ("PED_CAGENCIA_CIUDAD", "agencia_ciudad", "varchar(80)", "S", "", "Ciudad de la agencia de destino"),
             ("PED_CAGENCIA_REFERENCIA", "agencia_referencia", "varchar(200)", "S", "", "Referencia de la agencia"),
             ("PED_CPUNTO_ENCUENTRO", "punto_encuentro", "varchar(200)", "S", "", "Lugar de entrega personal en Lima, acordado con el cliente"),
             ("PED_DENTREGA_PROGRAMADA", "entrega_programada", "timestamptz", "S", "", "Fecha y hora acordadas para la entrega personal"),
             ("PED_NSUBTOTAL", "subtotal", "numeric(10,2)", "N", "", "Suma de los subtotales de los ítems"),
             ("PED_NCOSTO_ENVIO", "costo_envio", "numeric(10,2)", "S", "", "Costo de envío; nulo hasta cotizar"),
             ("PED_NTOTAL", "total", "numeric(10,2)", "N", "", "subtotal + costo de envío (mientras no se cotiza, igual al subtotal)"),
             ("MPA_NID", "metodo_pago", "bigint", "S", "FK:TBL_RMETODO_PAGO", "Cómo se pagó; se llena al confirmar el pago"),
             ("USU_NID_CREADO_POR", "creado_por", "bigint", "S", "FK:auth_user", "Quién lo registró (solo ventas PRESENCIALES)"),
             ("PED_CNOTAS", "notas", "text", "S", "", "Notas"),
             ("PED_DFECHA_COTIZADO", "fecha_cotizado", "timestamptz", "S", "", "Cuándo pasó a COTIZADO"),
             ("PED_DFECHA_PAGADO", "fecha_pagado", "timestamptz", "S", "", "Cuándo pasó a PAGADO"),
             ("PED_DFECHA_ENVIADO", "fecha_enviado", "timestamptz", "S", "", "Cuándo pasó a ENVIADO"),
             ("PED_DFECHA_ENTREGADO", "fecha_entregado", "timestamptz", "S", "", "Cuándo pasó a ENTREGADO"),
             ("PED_DFECHA_CIERRE", "fecha_cierre", "timestamptz", "S", "", "Cuándo se canceló o rechazó"),
         ]),
    dict(nombre="TBL_TPEDIDO_ITEM", sigla="ITE", clase="ItemPedido", app="pedidos",
         tipo="Transacción", descripcion="Líneas del pedido con copia (snapshot) de nombre, talla y precio.",
         columnas=[
             ("ITE_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("PED_NID", "pedido", "bigint", "N", "FK:TBL_TPEDIDO", "Pedido"),
             ("VAR_NID", "variante", "bigint", "N", "FK:TBL_RVARIANTE", "Variante comprada (relación protegida)"),
             ("ITE_CNOMBRE_PRODUCTO", "nombre_producto", "varchar(150)", "N", "", "COPIA del nombre del producto"),
             ("ITE_CSKU", "sku", "varchar(40)", "N", "", "COPIA del código de la variante"),
             ("ITE_CTALLA", "talla", "varchar(10)", "N", "", "COPIA de la talla"),
             ("ITE_CCOLOR", "color", "varchar(40)", "N", "", "COPIA del color; vacío si no aplica"),
             ("ITE_NPRECIO_UNIDAD", "precio_unidad", "numeric(10,2)", "N", "", "COPIA del precio unitario aplicado"),
             ("ITE_NCANTIDAD", "cantidad", "integer", "N", "", "Cantidad (mínimo 1)"),
             ("ITE_NSUBTOTAL", "subtotal", "numeric(10,2)", "N", "", "precio_unidad por cantidad"),
         ]),
    dict(nombre="TBL_LPEDIDO_ESTADO", sigla="PES", clase="RegistroEstadoPedido", app="pedidos",
         tipo="Log", inmutable=True, descripcion="Bitácora de cada cambio de estado de un pedido.",
         columnas=[
             ("PES_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("PED_NID", "pedido", "bigint", "N", "FK:TBL_TPEDIDO", "Pedido"),
             ("PES_CESTADO_ANTERIOR", "estado_anterior", "varchar(15)", "S", "", "Estado de origen; nulo al crear el pedido"),
             ("PES_CESTADO_NUEVO", "estado_nuevo", "varchar(15)", "N", "", "Estado de destino"),
             ("USU_NID_CAMBIADO_POR", "cambiado_por", "bigint", "S", "FK:auth_user", "Quién cambió; nulo si lo creó el cliente en la web"),
             ("PES_CNOTA", "nota", "varchar(255)", "S", "", "Nota opcional"),
         ],
         notas=["Sin fecha de actualización (inmutable)."]),
    dict(nombre="TBL_HPEDIDO", sigla="HPE", clase="(historial de Pedido)", app="pedidos",
         tipo="Histórico", generada=True, descripcion="Historial completo de cambios de Pedido, generado por django-simple-history.",
         columnas=[
             ("HPE_NID", "history_id", "bigint", "N", "PK", "Identificador del historial"),
             ("PED_NID", "id", "bigint", "N", "FK:TBL_TPEDIDO", "Pedido al que pertenece la copia"),
         ],
         notas=["La genera la librería con table_name='TBL_HPEDIDO'. Las columnas history_date, history_type y history_user conservan su nombre. Las columnas copiadas de TBL_TPEDIDO conservan los nombres de esa tabla."]),
    dict(nombre="TBL_TENVIO", sigla="ENV", clase="Envio", app="envios",
         tipo="Transacción", descripcion="Datos del envío por agencia (solo pedidos con entrega AGENCIA).",
         columnas=[
             ("ENV_NID", "id", "bigint", "N", "PK", "Identificador"),
             ("PED_NID", "pedido", "bigint", "N", "FK:TBL_TPEDIDO|UK", "Pedido (uno a uno)"),
             ("ENV_CAGENCIA", "agencia", "varchar(10)", "N", "", "SHALOM, OLVA u OTRA"),
             ("ENV_CNUMERO_ORDEN_AGENCIA", "numero_orden_agencia", "varchar(30)", "N", "", "Número de orden de la agencia"),
             ("ENV_CCLAVE_RECOJO", "clave_recojo", "varchar(4)", "N", "", "Clave de recojo de 4 dígitos (privado)"),
             ("ENV_CIMAGEN_BOLETA", "imagen_boleta", "varchar(255)", "N", "", "Ruta de la foto de la boleta, en bucket privado (privado)"),
             ("ENV_NCOSTO_FLETE", "costo_flete", "numeric(10,2)", "N", "", "Costo real del flete en PEN"),
             ("ENV_CQUIEN_PAGA", "quien_paga", "varchar(20)", "N", "", "CLIENTE_ADELANTADO, CLIENTE_EN_DESTINO o RICHARD_ADELANTO"),
             ("ENV_OCOBRADO", "cobrado", "boolean", "N", "", "Flete cobrado o pendiente de cobro"),
             ("ENV_DFECHA_DESPACHO", "fecha_despacho", "timestamptz", "N", "", "Fecha de despacho en la agencia"),
             ("ENV_CNOTAS", "notas", "text", "S", "", "Notas"),
         ]),
]

# Índices y restricciones propias: (tabla, nombre, tipo, definición)
INDICES = [
    ("TBL_REQUIPO", "TBL_REQUIPO_ACT_ORD_NOM_IX", "IX", "(EQU_OACTIVO, EQU_NORDEN, EQU_CNOMBRE)"),
    ("TBL_RPRODUCTO", "TBL_RPRODUCTO_ACTIVO_CAT_EQU_IX", "IX", "(CAT_NID, EQU_NID, PRO_ODESTACADO) WHERE PRO_OACTIVO = true"),
    ("TBL_TPEDIDO", "TBL_TPEDIDO_PED_CESTADO_PED_DFECHA_CREACION_IX", "IX", "(PED_CESTADO, PED_DFECHA_CREACION)"),
    ("TBL_TPEDIDO", "TBL_TPEDIDO_TEL_IX", "IX", "(PED_CCLIENTE_TELEFONO)"),
    ("TBL_TPEDIDO", "TBL_TPEDIDO_ORI_EST_FEC_IX", "IX", "(PED_CORIGEN, PED_CESTADO, PED_DFECHA_CREACION)"),
    ("TBL_TPEDIDO", "TBL_TPEDIDO_PED_CCODIGO_UK", "UK", "(PED_CCODIGO)"),
    ("TBL_TPEDIDO", "TBL_TPEDIDO_TOTAL_CK", "CK", "PED_NTOTAL = PED_NSUBTOTAL + coalesce(PED_NCOSTO_ENVIO, 0)"),
    ("TBL_RVARIANTE", "TBL_RVARIANTE_PRO_NID_IX", "IX", "(PRO_NID)"),
    ("TBL_RVARIANTE", "TBL_RVARIANTE_DISP_TALLA_IX", "IX", "(VAR_CTALLA, PRO_NID) WHERE VAR_OACTIVA = true AND VAR_NCANTIDAD_STOCK > 0"),
    ("TBL_RVARIANTE", "TBL_RVARIANTE_STOCK_CK", "CK", "VAR_NCANTIDAD_STOCK >= 0"),
    ("TBL_RVARIANTE", "TBL_RVARIANTE_PRO_NID_VAR_CTALLA_VAR_CCOLOR_VAR_CMODELO_UK", "UK", "(PRO_NID, VAR_CTALLA, VAR_CCOLOR, VAR_CMODELO)"),
    ("TBL_RREGLA_PRECIO", "TBL_RREGLA_PRECIO_PRO_NID_REG_NCANTIDAD_MINIMA_UK", "UK", "(PRO_NID, REG_NCANTIDAD_MINIMA)"),
    ("TBL_TMOVIMIENTO_STOCK", "TBL_TMOVIMIENTO_STOCK_VAR_NID_MOV_DFECHA_CREACION_IX", "IX", "(VAR_NID, MOV_DFECHA_CREACION)"),
    ("TBL_TMOVIMIENTO_STOCK", "TBL_TMOVIMIENTO_STOCK_CANTIDAD_CK", "CK", "MOV_NCANTIDAD <> 0"),
    ("TBL_TPEDIDO_ITEM", "TBL_TPEDIDO_ITEM_CANTIDAD_CK", "CK", "ITE_NCANTIDAD >= 1"),
    ("TBL_LPEDIDO_ESTADO", "TBL_LPEDIDO_ESTADO_PED_NID_PES_DFECHA_CREACION_IX", "IX", "(PED_NID, PES_DFECHA_CREACION)"),
]

# Valores permitidos (columna de texto -> lista de (valor, significado))
VALORES = [
    ("PED_CESTADO / PES_CESTADO_*", [
        ("NUEVO", "Pedido recibido; falta cotizar el envío"),
        ("COTIZADO", "Total final definido; esperando el pago"),
        ("PAGADO", "Pago verificado por Richard; stock descontado"),
        ("ENVIADO", "Entregado a la agencia o al delivery"),
        ("ENTREGADO", "El cliente ya tiene su pedido"),
        ("CANCELADO", "El cliente desistió o no pagó"),
        ("RECHAZADO", "Richard no acepta el pedido"),
    ]),
    ("PED_CORIGEN", [
        ("WEB", "El cliente envió el pedido desde la tienda"),
        ("PRESENCIAL", "Richard registró la venta en persona"),
    ]),
    ("PED_CTIPO_ENTREGA", [
        ("AGENCIA", "Envío a provincia por Shalom u Olva; exige DNI y datos de agencia"),
        ("DELIVERY_LIMA", "Delivery dentro de Lima cotizado por Richard"),
        ("PUNTO_ENCUENTRO", "Richard se encuentra con el cliente en Lima, entrega y cobra ahí; nace con envío S/ 0"),
        ("RECOJO", "El cliente recoge; nace con envío S/ 0"),
    ]),
    ("PED_CAGENCIA / ENV_CAGENCIA", [
        ("SHALOM", "Agencia Shalom"), ("OLVA", "Agencia Olva"), ("OTRA", "Otra agencia"),
    ]),
    ("ENV_CQUIEN_PAGA", [
        ("CLIENTE_ADELANTADO", "El cliente pagó el flete antes del despacho"),
        ("CLIENTE_EN_DESTINO", "El cliente paga el flete al recoger"),
        ("RICHARD_ADELANTO", "Richard lo adelantó; queda como pendiente de cobro"),
    ]),
    ("MPA_CTIPO", [
        ("YAPE", "Yape con QR, titular y número copiable"),
        ("PLIN", "Plin (fase posterior)"),
        ("EFECTIVO", "Dinero en efectivo, típico en entregas personales"),
    ]),
    ("MOV_CTIPO", [
        ("ENTRADA", "Ingreso de mercadería (cantidad positiva)"),
        ("VENTA", "Salida por venta al confirmar el pago (cantidad negativa)"),
        ("AJUSTE", "Corrección de inventario (positiva o negativa)"),
        ("DEVOLUCION", "Regreso de stock por cancelación o rechazo (cantidad positiva)"),
    ]),
    ("EQU_CTIPO", [
        ("SELECCION", "Selección nacional"),
        ("CLUB", "Club internacional"),
        ("ORIGINAL", "Diseño propio Emuná Sport"),
    ]),
    ("PRO_CEQUIPACION", [
        ("LOCAL", "Local / Titular"),
        ("ALTERNA", "Alterna / Visitante"),
        ("ESPECIAL", "Edición especial"),
        ("RETRO", "Retro / Histórica"),
        ("ENTRENAMIENTO", "Entrenamiento / Línea propia"),
    ]),
]

# Relaciones para el modelo ER: (padre, hijo, cardinalidad Mermaid, etiqueta)
RELACIONES = [
    ("TBL_RCATEGORIA", "TBL_RPRODUCTO", "||--o{", "clasifica"),
    ("TBL_REQUIPO", "TBL_RPRODUCTO", "|o--o{", "agrupa equipo"),
    ("TBL_RPRODUCTO", "TBL_RIMAGEN_PRODUCTO", "||--o{", "tiene fotos"),
    ("TBL_RPRODUCTO", "TBL_RVARIANTE", "||--o{", "tiene variantes"),
    ("TBL_RPRODUCTO", "TBL_RREGLA_PRECIO", "||--o{", "tiene precios por mayor"),
    ("TBL_RVARIANTE", "TBL_TMOVIMIENTO_STOCK", "||--o{", "mueve stock"),
    ("TBL_RVARIANTE", "TBL_TPEDIDO_ITEM", "||--o{", "se vende en"),
    ("TBL_TPEDIDO", "TBL_TPEDIDO_ITEM", "||--|{", "contiene"),
    ("TBL_TPEDIDO", "TBL_TMOVIMIENTO_STOCK", "||--o{", "origina"),
    ("TBL_TPEDIDO", "TBL_LPEDIDO_ESTADO", "||--o{", "registra estados"),
    ("TBL_TPEDIDO", "TBL_TENVIO", "||--o|", "se envía con"),
    ("TBL_TPEDIDO", "TBL_HPEDIDO", "||--o{", "historial"),
    ("TBL_RMETODO_PAGO", "TBL_TPEDIDO", "|o--o{", "se paga con"),
    ("AUTH_USER", "TBL_TMOVIMIENTO_STOCK", "||--o{", "registra"),
    ("AUTH_USER", "TBL_LPEDIDO_ESTADO", "||--o{", "cambia"),
    ("AUTH_USER", "TBL_TPEDIDO", "|o--o{", "registra ventas presenciales"),
]

TIPOS_LETRA = {"N": ("bigint", "integer", "numeric"), "C": ("varchar", "text"),
               "D": ("date", "timestamptz"), "B": ("bytea",), "O": ("boolean",)}
MAX_IDENTIFICADOR = 63


def comunes(tabla):
    """Agrega las columnas de auditoría a una tabla (fechas de creación y actualización).

    Qué hace:      Devuelve las columnas de la tabla más PPP_DFECHA_CREACION y,
                   si la tabla no es inmutable, PPP_DFECHA_ACTUALIZACION.
    Va hacia:      La lista que usan el Markdown, el Excel y las validaciones.
    Depende de:    La sigla de la tabla y su bandera 'inmutable' o 'generada'.
    La llama:      completar_tablas().
    Cuándo usarla: Una vez por tabla, antes de validar o generar archivos.
    Si no opera:   Las tablas saldrían sin sus fechas de auditoría.
    """
    columnas = list(tabla["columnas"])
    if tabla.get("generada"):
        return columnas
    s = tabla["sigla"]
    columnas.append((f"{s}_DFECHA_CREACION", "fecha_creacion", "timestamptz", "N", "", "Fecha de creación"))
    if not tabla.get("inmutable"):
        columnas.append((f"{s}_DFECHA_ACTUALIZACION", "fecha_actualizacion", "timestamptz", "N", "", "Fecha de última actualización"))
    return columnas


def completar_tablas():
    """Deja cada tabla con todas sus columnas, incluidas las de auditoría.

    Qué hace:      Recorre TABLAS y reemplaza 'columnas' por la lista completa.
    Va hacia:      La variable global TABLAS.
    Depende de:    comunes().
    La llama:      main().
    Cuándo usarla: Al inicio de cada ejecución.
    Si no opera:   Se generan documentos sin columnas de auditoría.
    """
    for t in TABLAS:
        t["columnas"] = comunes(t)


def validar():
    """Comprueba que todas las tablas y columnas cumplan el estándar (doc 12).

    Qué hace:      Revisa prefijos, siglas únicas, letra de tipo, longitud y llaves foráneas.
    Va hacia:      Devuelve la lista de errores (vacía si todo está bien).
    Depende de:    TABLAS, INDICES y TIPOS_LETRA.
    La llama:      main(), antes de escribir cualquier archivo.
    Cuándo usarla: Siempre antes de generar los documentos.
    Si no opera:   Podrían publicarse nombres que no cumplen el estándar.
    """
    errores = []
    siglas = {}
    pk = {t["nombre"]: f'{t["sigla"]}_NID' for t in TABLAS}
    for t in TABLAS:
        n, s = t["nombre"], t["sigla"]
        if not re.fullmatch(r"TBL_[TRHLUACD]?[A-Z]+(_[A-Z]+)*", n) or len(n) > MAX_IDENTIFICADOR:
            errores.append(f"Tabla mal nombrada: {n}")
        if not re.fullmatch(r"[A-Z]{3}", s):
            errores.append(f"{n}: la sigla debe tener 3 letras ({s})")
        if s in siglas:
            errores.append(f"Sigla repetida {s}: {n} y {siglas[s]}")
        siglas[s] = n
        for col, campo, sql, nulo, clave, desc in t["columnas"]:
            if len(col) > MAX_IDENTIFICADOR:
                errores.append(f"{n}.{col}: más de {MAX_IDENTIFICADOR} caracteres")
            es_fk = clave.startswith("FK:")
            if es_fk:
                destino = clave[3:].split("|")[0]
                if destino != "auth_user" and pk.get(destino) != col:
                    errores.append(f"{n}.{col}: una FK debe llamarse como la PK de {destino} ({pk.get(destino)})")
                if destino == "auth_user" and not col.startswith("USU_NID_"):
                    errores.append(f"{n}.{col}: la FK a usuario debe empezar con USU_NID_")
                continue
            m = re.fullmatch(rf"{s}_([NCDBO])[A-Z0-9_]+", col)
            if not m:
                errores.append(f"{n}.{col}: debe seguir {s}_<tipo><cuerpo>")
                continue
            base = sql.split("(")[0]
            if base not in TIPOS_LETRA[m.group(1)]:
                errores.append(f"{n}.{col}: la letra {m.group(1)} no corresponde al tipo {sql}")
    for tabla, nombre, tipo, _ in INDICES:
        if len(nombre) > MAX_IDENTIFICADOR:
            errores.append(f"Índice demasiado largo ({len(nombre)}): {nombre}")
        if not nombre.endswith(f"_{tipo}"):
            errores.append(f"El índice {nombre} debe terminar en _{tipo}")
    return errores


def texto_clave(clave):
    """Convierte el código de clave en texto legible para las tablas.

    Qué hace:      'FK:TBL_X|UK' pasa a 'FK → TBL_X, UK'.
    Va hacia:      La columna «Clave» del Markdown y del Excel.
    Depende de:    Nada.
    La llama:      generar_markdown() y generar_excel().
    Cuándo usarla: Al escribir cada columna.
    Si no opera:   La clave se vería con la sintaxis interna.
    """
    partes = []
    for p in clave.split("|"):
        partes.append(f"FK → {p[3:]}" if p.startswith("FK:") else p)
    return ", ".join(x for x in partes if x)


def generar_markdown():
    """Escribe diccionario-datos.md con todas las tablas, valores e índices.

    Qué hace:      Arma el documento Markdown del diccionario.
    Va hacia:      diccionario-datos.md en esta carpeta.
    Depende de:    TABLAS, VALORES, INDICES, texto_clave().
    La llama:      main().
    Cuándo usarla: Después de validar().
    Si no opera:   El diccionario en Markdown queda desactualizado.
    """
    L = ["# Diccionario de datos (nombres físicos)", "",
         "> Generado por `generar_diccionario.py`. **No editar a mano**: se cambia la definición en el script y se vuelve a ejecutar.",
         "> Versión en Excel: `diccionario-datos.xlsx`.", "",
         "Aplica `../12-estandar-base-datos.md` al modelo lógico de `../04-modelo-de-datos.md`. Cada tabla muestra su nombre físico, su sigla de 3 letras y el nombre en Python (clase y campo de Django).", "",
         "**Letras de tipo:** N numérico (incluye llaves y decimales) · C carácter · D fecha o fecha-hora · B binario · O booleano.",
         "**Dinero:** `numeric(10,2)` en PEN. **Archivos** (fotos, QR, boletas): se guarda la ruta como texto.",
         "**Columnas de auditoría:** toda tabla lleva `PPP_DFECHA_CREACION` y `PPP_DFECHA_ACTUALIZACION`, salvo las inmutables (solo creación).", "",
         "## Resumen de tablas", "",
         "| Tabla física | Sigla | Clase Django | App | Tipo |", "|---|---|---|---|---|"]
    for t in TABLAS:
        L.append(f'| `{t["nombre"]}` | {t["sigla"]} | `{t["clase"]}` | {t["app"]} | {t["tipo"]} |')
    L += ["", "Tablas de Django que **no** se renombran: `auth_user`, `auth_group`, `auth_permission`, `django_session`, `django_migrations`, `django_admin_log`, `django_content_type` y sus tablas de unión.", ""]
    app_actual = None
    for t in TABLAS:
        if t["app"] != app_actual:
            app_actual = t["app"]
            L += ["---", "", f"## App `{app_actual}`", ""]
        L += [f'### `{t["nombre"]}` ({t["sigla"]}) – {t["descripcion"]}', "",
              "| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |", "|---|---|---|---|---|---|"]
        for col, campo, sql, nulo, clave, desc in t["columnas"]:
            L.append(f"| `{col}` | `{campo}` | {sql} | {'Sí' if nulo == 'S' else 'No'} | {texto_clave(clave)} | {desc} |")
        L.append("")
        for ix in [i for i in INDICES if i[0] == t["nombre"]]:
            L.append(f"- **{ix[2]}** `{ix[1]}`: {ix[3]}")
        for nota in t.get("notas", []):
            L.append(f"- {nota}")
        L.append("")
    L += ["---", "", "## Valores permitidos", ""]
    for col, vals in VALORES:
        L += [f"### {col}", "", "| Valor | Significado |", "|---|---|"]
        L += [f"| `{v}` | {d} |" for v, d in vals]
        L.append("")
    L += ["## Datos privados", "",
          "Columnas marcadas «(privado)»: nunca en URLs, logs, páginas públicas ni mensajes de error (ver `../07-seguridad-datos.md`).", ""]
    (CARPETA / "diccionario-datos.md").write_text("\n".join(L), encoding="utf-8")


def generar_er():
    """Escribe modelo-er.md con el diagrama Entidad-Relación en Mermaid.

    Qué hace:      Dibuja todas las tablas con sus columnas y sus relaciones.
    Va hacia:      modelo-er.md en esta carpeta.
    Depende de:    TABLAS y RELACIONES.
    La llama:      main().
    Cuándo usarla: Después de validar().
    Si no opera:   El diagrama queda desactualizado respecto al diccionario.
    """
    def tipo_mermaid(sql):
        base = sql.split("(")[0]
        return {"timestamptz": "timestamptz", "numeric": "numeric", "varchar": "varchar"}.get(base, base)

    L = ["# Modelo Entidad-Relación", "",
         "> Generado por `generar_diccionario.py`. **No editar a mano.**", "",
         "Con los nombres físicos del estándar (`../12-estandar-base-datos.md`). Detalle de columnas en `diccionario-datos.md`. `AUTH_USER` es la tabla `auth_user` de Django.", "",
         "```mermaid", "erDiagram"]
    for padre, hijo, card, etiqueta in RELACIONES:
        L.append(f'  {padre} {card} {hijo} : "{etiqueta}"')
    L.append("")
    for t in TABLAS:
        L.append(f'  {t["nombre"]} {{')
        for col, campo, sql, nulo, clave, desc in t["columnas"]:
            if col.endswith(("_DFECHA_CREACION", "_DFECHA_ACTUALIZACION")):
                continue
            claves = []
            for p in clave.split("|"):
                if p == "PK" or p == "UK":
                    claves.append(p)
                elif p.startswith("FK:"):
                    claves.append("FK")
            L.append(f'    {tipo_mermaid(sql)} {col} {",".join(claves)}'.rstrip())
        L.append("  }")
    L += ["  AUTH_USER {", "    bigint id PK", "    varchar username", "  }", "```", "",
          "## Notas",
          "- `TBL_HPEDIDO` es una simplificación: `django-simple-history` la genera con sus propias columnas.",
          "- `TBL_TPEDIDO_ITEM` guarda **copias** del nombre, talla y precio; su relación con `TBL_RVARIANTE` es protegida.",
          "- `TBL_TENVIO` existe solo para pedidos con entrega `AGENCIA`.",
          "- `TBL_RCONFIGURACION_TIENDA` no se relaciona con otras tablas.", ""]
    (CARPETA / "modelo-er.md").write_text("\n".join(L), encoding="utf-8")


def generar_excel():
    """Escribe diccionario-datos.xlsx con hojas Leeme, Tablas, Columnas, Valores e Indices.

    Qué hace:      Crea un Excel con filtros, filas fijas y anchos ajustados.
    Va hacia:      diccionario-datos.xlsx en esta carpeta.
    Depende de:    openpyxl, TABLAS, VALORES, INDICES, texto_clave().
    La llama:      main().
    Cuándo usarla: Después de validar(), para compartir el diccionario con quien no usa Markdown.
    Si no opera:   Se avisa que falta openpyxl; el resto de archivos se generan igual.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        print("AVISO: falta openpyxl (pip install openpyxl); no se generó el Excel.")
        return
    cabecera = PatternFill("solid", fgColor="0A0A0A")
    letra_cab = Font(bold=True, color="FFFFFF")
    wb = Workbook()

    def hoja(titulo, encabezados, filas, anchos):
        ws = wb.create_sheet(titulo)
        ws.append(encabezados)
        for c in ws[1]:
            c.fill, c.font = cabecera, letra_cab
            c.alignment = Alignment(vertical="center", wrap_text=True)
        for f in filas:
            ws.append(f)
        for i, a in enumerate(anchos, start=1):
            ws.column_dimensions[get_column_letter(i)].width = a
        for fila in ws.iter_rows(min_row=2):
            for c in fila:
                c.alignment = Alignment(vertical="top", wrap_text=True)
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        return ws

    ws0 = wb.active
    ws0.title = "Leeme"
    for linea in ["Diccionario de datos – Emuná Sport", "",
                  "Generado desde 03-Diseno-Tecnico/base-datos/generar_diccionario.py. No editar a mano.",
                  "Estándar de nombres: 03-Diseno-Tecnico/12-estandar-base-datos.md", "",
                  "Hojas:", "  Tablas   – una fila por tabla", "  Columnas – una fila por columna (con filtros)",
                  "  Valores  – valores permitidos de las columnas de texto", "  Indices  – índices, únicos y restricciones propias", "",
                  "Letras de tipo: N numérico · C carácter · D fecha · B binario · O booleano",
                  "Columnas marcadas «(privado)» son datos sensibles."]:
        ws0.append([linea])
    ws0["A1"].font = Font(bold=True, size=14)
    ws0.column_dimensions["A"].width = 95

    hoja("Tablas", ["Tabla física", "Sigla", "Clase Django", "App", "Tipo", "Descripción", "N.º columnas"],
         [[t["nombre"], t["sigla"], t["clase"], t["app"], t["tipo"], t["descripcion"], len(t["columnas"])] for t in TABLAS],
         [30, 8, 24, 12, 14, 70, 12])
    filas = []
    for t in TABLAS:
        for col, campo, sql, nulo, clave, desc in t["columnas"]:
            filas.append([t["nombre"], t["sigla"], col, campo, sql, "Sí" if nulo == "S" else "No", texto_clave(clave), desc,
                          "Sí" if "(privado)" in desc else ""])
    hoja("Columnas", ["Tabla", "Sigla", "Columna", "Campo Django", "Tipo", "Admite nulo", "Clave", "Descripción", "Privado"],
         filas, [28, 8, 32, 26, 16, 12, 28, 70, 9])
    filas = [[col, v, d] for col, vals in VALORES for v, d in vals]
    hoja("Valores", ["Columna", "Valor", "Significado"], filas, [32, 22, 80])
    hoja("Indices", ["Tabla", "Nombre", "Tipo", "Definición"], [list(i) for i in INDICES], [28, 70, 8, 70])
    wb.save(CARPETA / "diccionario-datos.xlsx")


def main():
    """Valida el estándar y genera los tres archivos.

    Qué hace:      Ejecuta completar_tablas(), validar() y los tres generadores.
    Va hacia:      Los archivos de salida; termina con código 1 si hay errores.
    Depende de:    Todas las funciones de este archivo.
    La llama:      La línea final (python generar_diccionario.py).
    Cuándo usarla: Siempre que cambie la definición de tablas.
    Si no opera:   No se actualiza ninguna documentación de la base de datos.
    """
    completar_tablas()
    errores = validar()
    if errores:
        print("El diccionario NO cumple el estándar:")
        for e in errores:
            print("  -", e)
        sys.exit(1)
    generar_markdown()
    generar_er()
    generar_excel()
    columnas = sum(len(t["columnas"]) for t in TABLAS)
    print(f"Listo: {len(TABLAS)} tablas, {columnas} columnas validadas.")


if __name__ == "__main__":
    main()
