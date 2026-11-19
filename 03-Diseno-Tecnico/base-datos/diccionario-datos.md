# Diccionario de datos (nombres físicos)

> Generado por `generar_diccionario.py`. **No editar a mano**: se cambia la definición en el script y se vuelve a ejecutar.
> Versión en Excel: `diccionario-datos.xlsx`.

Aplica `../12-estandar-base-datos.md` al modelo lógico de `../04-modelo-de-datos.md`. Cada tabla muestra su nombre físico, su sigla de 3 letras y el nombre en Python (clase y campo de Django).

**Letras de tipo:** N numérico (incluye llaves y decimales) · C carácter · D fecha o fecha-hora · B binario · O booleano.
**Dinero:** `numeric(10,2)` en PEN. **Archivos** (fotos, QR, boletas): se guarda la ruta como texto.
**Columnas de auditoría:** toda tabla lleva `PPP_DFECHA_CREACION` y `PPP_DFECHA_ACTUALIZACION`, salvo las inmutables (solo creación).

## Resumen de tablas

| Tabla física | Sigla | Clase Django | App | Tipo |
|---|---|---|---|---|
| `TBL_RCONFIGURACION_TIENDA` | CTI | `ConfiguracionTienda` | nucleo | Referencia |
| `TBL_RMETODO_PAGO` | MPA | `MetodoPago` | nucleo | Referencia |
| `TBL_RCATEGORIA` | CAT | `Categoria` | catalogo | Referencia |
| `TBL_REQUIPO` | EQU | `Equipo` | catalogo | Referencia |
| `TBL_RPRODUCTO` | PRO | `Producto` | catalogo | Referencia |
| `TBL_RIMAGEN_PRODUCTO` | IMA | `ImagenProducto` | catalogo | Referencia |
| `TBL_RVARIANTE` | VAR | `Variante` | catalogo | Referencia |
| `TBL_RREGLA_PRECIO` | REG | `ReglaPrecio` | catalogo | Referencia |
| `TBL_TMOVIMIENTO_STOCK` | MOV | `MovimientoStock` | inventario | Transacción |
| `TBL_TPEDIDO` | PED | `Pedido` | pedidos | Transacción |
| `TBL_TPEDIDO_ITEM` | ITE | `ItemPedido` | pedidos | Transacción |
| `TBL_LPEDIDO_ESTADO` | PES | `RegistroEstadoPedido` | pedidos | Log |
| `TBL_HPEDIDO` | HPE | `(historial de Pedido)` | pedidos | Histórico |
| `TBL_TENVIO` | ENV | `Envio` | envios | Transacción |

Tablas de Django que **no** se renombran: `auth_user`, `auth_group`, `auth_permission`, `django_session`, `django_migrations`, `django_admin_log`, `django_content_type` y sus tablas de unión.

---

## App `nucleo`

### `TBL_RCONFIGURACION_TIENDA` (CTI) – Ajustes generales de la tienda (registro único).

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `CTI_NID` | `id` | bigint | No | PK | Identificador |
| `CTI_CNOMBRE` | `nombre` | varchar(100) | No |  | Nombre de la tienda |
| `CTI_CNUMERO_WHATSAPP` | `numero_whatsapp` | varchar(15) | No |  | WhatsApp de Richard |
| `CTI_CTEXTO_PIE` | `texto_pie` | varchar(200) | Sí |  | Texto de pie de página |
| `CTI_NUMBRAL_STOCK_BAJO` | `umbral_stock_bajo` | integer | No |  | Umbral de stock bajo por defecto |
| `CTI_OMOSTRAR_MARCAS` | `mostrar_marcas` | boolean | No |  | Mostrar marcas en el catálogo (apagado por defecto) |
| `CTI_NDIAS_SIN_VENTAS` | `dias_sin_ventas` | integer | No |  | Días sin ventas para la alerta del tablero (propuesta, Fase 4) |
| `CTI_NHORAS_PEDIDO_PENDIENTE` | `horas_pedido_pendiente` | integer | No |  | Horas para avisar de un pedido pendiente (propuesta, Fase 4) |
| `CTI_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `CTI_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |


### `TBL_RMETODO_PAGO` (MPA) – Formas de pago aceptadas (Yape, Plin, efectivo).

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `MPA_NID` | `id` | bigint | No | PK | Identificador |
| `MPA_CTIPO` | `tipo` | varchar(20) | No | UK | YAPE, PLIN o EFECTIVO |
| `MPA_CTITULAR` | `titular` | varchar(100) | Sí |  | Titular de la cuenta (no aplica a EFECTIVO) |
| `MPA_CNUMERO_CUENTA` | `numero_cuenta` | varchar(20) | Sí |  | Número copiable (no aplica a EFECTIVO) |
| `MPA_CIMAGEN_QR` | `imagen_qr` | varchar(255) | Sí |  | Ruta de la imagen del QR; no va al repositorio |
| `MPA_OACTIVO` | `activo` | boolean | No |  | Método disponible |
| `MPA_NORDEN` | `orden` | integer | No |  | Orden de aparición |
| `MPA_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `MPA_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |


---

## App `catalogo`

### `TBL_RCATEGORIA` (CAT) – Categorías para organizar el catálogo (uso, colección o tela).

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `CAT_NID` | `id` | bigint | No | PK | Identificador |
| `CAT_CNOMBRE` | `nombre` | varchar(80) | No |  | Nombre |
| `CAT_CSLUG` | `slug` | varchar(100) | No | UK | Texto para la URL |
| `CAT_NORDEN` | `orden` | integer | No |  | Orden de aparición |
| `CAT_OACTIVA` | `activa` | boolean | No |  | Categoría visible |
| `CAT_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `CAT_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |


### `TBL_REQUIPO` (EQU) – Equipos, selecciones, clubes y líneas con alias para búsqueda e IA.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `EQU_NID` | `id` | bigint | No | PK | Identificador |
| `EQU_CNOMBRE` | `nombre` | varchar(80) | No | UK | Nombre del equipo o línea |
| `EQU_CSLUG` | `slug` | varchar(100) | No | UK | Texto para la URL |
| `EQU_CTIPO` | `tipo` | varchar(20) | No |  | SELECCION, CLUB o ORIGINAL |
| `EQU_CALIAS_BUSQUEDA` | `alias_busqueda` | varchar(200) | No |  | Alias / apodos separados por coma |
| `EQU_NORDEN` | `orden` | integer | No |  | Orden de aparición |
| `EQU_OACTIVO` | `activo` | boolean | No |  | Equipo activo |
| `EQU_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `EQU_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |

- **IX** `TBL_REQUIPO_ACT_ORD_NOM_IX`: (EQU_OACTIVO, EQU_NORDEN, EQU_CNOMBRE)

### `TBL_RPRODUCTO` (PRO) – Camisetas u otros productos del catálogo.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `PRO_NID` | `id` | bigint | No | PK | Identificador |
| `CAT_NID` | `categoria` | bigint | No | FK → TBL_RCATEGORIA | Categoría |
| `EQU_NID` | `equipo` | bigint | Sí | FK → TBL_REQUIPO | Equipo / Selección / Club |
| `PRO_CNOMBRE` | `nombre` | varchar(150) | No |  | Nombre |
| `PRO_CSLUG` | `slug` | varchar(170) | No | UK | Texto para la URL |
| `PRO_CSKU` | `sku` | varchar(30) | No | UK | Código interno, ej. EMU-001 |
| `PRO_CEQUIPACION` | `equipacion` | varchar(20) | No |  | Versión: LOCAL, ALTERNA, ESPECIAL, RETRO o ENTRENAMIENTO |
| `PRO_CTEMPORADA` | `temporada` | varchar(20) | No |  | Temporada, ej. 2026-2027 |
| `PRO_CPALABRAS_CLAVE` | `palabras_clave` | varchar(200) | No |  | Sinónimos de búsqueda para web y chat IA |
| `PRO_CDESCRIPCION` | `descripcion` | text | Sí |  | Descripción |
| `PRO_CMARCA` | `marca` | varchar(80) | Sí |  | Marca (opcional; solo se muestra si está activada) |
| `PRO_NPRECIO_UNIDAD` | `precio_unidad` | numeric(10,2) | No |  | Precio base o de oferta actual por unidad en PEN (ej. 55.00) |
| `PRO_NPRECIO_ANTERIOR` | `precio_anterior` | numeric(10,2) | Sí |  | Precio regular tachado en PEN (opcional, ej. 69.90) |
| `PRO_OACTIVO` | `activo` | boolean | No |  | Visible en la web |
| `PRO_ODESTACADO` | `destacado` | boolean | No |  | Destacado en el inicio |
| `PRO_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `PRO_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |

- **IX** `TBL_RPRODUCTO_ACTIVO_CAT_EQU_IX`: (CAT_NID, EQU_NID, PRO_ODESTACADO) WHERE PRO_OACTIVO = true

### `TBL_RIMAGEN_PRODUCTO` (IMA) – Fotos del producto con sus versiones generadas.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `IMA_NID` | `id` | bigint | No | PK | Identificador |
| `PRO_NID` | `producto` | bigint | No | FK → TBL_RPRODUCTO | Producto |
| `IMA_CRUTA_ORIGINAL` | `ruta_original` | varchar(255) | No |  | Ruta del original (bucket privado) |
| `IMA_CRUTA_MINIATURA` | `ruta_miniatura` | varchar(255) | Sí |  | Miniatura de unos 400 px en WebP |
| `IMA_CRUTA_DETALLE` | `ruta_detalle` | varchar(255) | Sí |  | Detalle de unos 900 px en WebP |
| `IMA_CTEXTO_ALT` | `texto_alternativo` | varchar(180) | Sí |  | Texto alternativo (alt) para SEO y accesibilidad; si es nulo usa el nombre del producto |
| `IMA_NORDEN` | `orden` | integer | No |  | Orden en la galería |
| `IMA_OPRINCIPAL` | `es_principal` | boolean | No |  | Imagen principal del producto |
| `IMA_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `IMA_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |


### `TBL_RVARIANTE` (VAR) – Variante de un producto (talla obligatoria; color y modelo opcionales) con su stock.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `VAR_NID` | `id` | bigint | No | PK | Identificador |
| `PRO_NID` | `producto` | bigint | No | FK → TBL_RPRODUCTO | Producto |
| `VAR_CTALLA` | `talla` | varchar(10) | No |  | Talla (obligatoria) |
| `VAR_CCOLOR` | `color` | varchar(40) | No |  | Color; vacío si no aplica |
| `VAR_CMODELO` | `modelo` | varchar(60) | No |  | Modelo; vacío si no aplica |
| `VAR_CSKU` | `sku` | varchar(40) | No | UK | Código único de la variante |
| `VAR_NCANTIDAD_STOCK` | `cantidad_stock` | integer | No |  | Stock actual (mayor o igual a 0). Solo cambia por un MovimientoStock |
| `VAR_NUMBRAL_STOCK_BAJO` | `umbral_stock_bajo` | integer | Sí |  | Umbral propio; si es nulo se usa el de la tienda |
| `VAR_OACTIVA` | `activa` | boolean | No |  | Variante disponible |
| `VAR_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `VAR_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |

- **IX** `TBL_RVARIANTE_PRO_NID_IX`: (PRO_NID)
- **IX** `TBL_RVARIANTE_DISP_TALLA_IX`: (VAR_CTALLA, PRO_NID) WHERE VAR_OACTIVA = true AND VAR_NCANTIDAD_STOCK > 0
- **CK** `TBL_RVARIANTE_STOCK_CK`: VAR_NCANTIDAD_STOCK >= 0
- **UK** `TBL_RVARIANTE_PRO_NID_VAR_CTALLA_VAR_CCOLOR_VAR_CMODELO_UK`: (PRO_NID, VAR_CTALLA, VAR_CCOLOR, VAR_CMODELO)
- Restricción única: (PRO_NID, VAR_CTALLA, VAR_CCOLOR, VAR_CMODELO). Color y modelo van vacíos (no nulos) para que la restricción funcione en PostgreSQL.

### `TBL_RREGLA_PRECIO` (REG) – Precio por mayor: desde N unidades, precio S/ X.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `REG_NID` | `id` | bigint | No | PK | Identificador |
| `PRO_NID` | `producto` | bigint | No | FK → TBL_RPRODUCTO | Producto |
| `REG_NCANTIDAD_MINIMA` | `cantidad_minima` | integer | No |  | Desde N unidades del mismo producto |
| `REG_NPRECIO_UNIDAD` | `precio_unidad` | numeric(10,2) | No |  | Precio por unidad aplicado en PEN |
| `REG_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `REG_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |

- **UK** `TBL_RREGLA_PRECIO_PRO_NID_REG_NCANTIDAD_MINIMA_UK`: (PRO_NID, REG_NCANTIDAD_MINIMA)
- Restricción única: (PRO_NID, REG_NCANTIDAD_MINIMA).

---

## App `inventario`

### `TBL_TMOVIMIENTO_STOCK` (MOV) – Cada entrada o salida de stock. Inmutable: no se edita ni se borra.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `MOV_NID` | `id` | bigint | No | PK | Identificador |
| `VAR_NID` | `variante` | bigint | No | FK → TBL_RVARIANTE | Variante afectada |
| `MOV_CTIPO` | `tipo` | varchar(15) | No |  | ENTRADA, VENTA, AJUSTE o DEVOLUCION |
| `MOV_NCANTIDAD` | `cantidad` | integer | No |  | Cantidad con signo; no puede ser 0 |
| `MOV_CMOTIVO` | `motivo` | varchar(200) | No |  | Motivo del movimiento |
| `PED_NID` | `pedido` | bigint | Sí | FK → TBL_TPEDIDO | Pedido que lo originó (si aplica) |
| `USU_NID_CREADO_POR` | `creado_por` | bigint | Sí | FK → auth_user | Quién lo registró |
| `MOV_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |

- **IX** `TBL_TMOVIMIENTO_STOCK_VAR_NID_MOV_DFECHA_CREACION_IX`: (VAR_NID, MOV_DFECHA_CREACION)
- **CK** `TBL_TMOVIMIENTO_STOCK_CANTIDAD_CK`: MOV_NCANTIDAD <> 0
- Sin fecha de actualización (inmutable). Candidatos a trigger: TRG_UPD_MOVIMIENTO_STOCK_BLOQUEO y TRG_DEL_MOVIMIENTO_STOCK_BLOQUEO.

---

## App `pedidos`

### `TBL_TPEDIDO` (PED) – Pedido de un cliente: venta web o venta presencial de Richard.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `PED_NID` | `id` | bigint | No | PK | Identificador |
| `PED_CCODIGO` | `codigo` | varchar(20) | No | UK | Código público no adivinable, ej. EMU-7K3Q9X |
| `PED_CESTADO` | `estado` | varchar(15) | No |  | NUEVO, COTIZADO, PAGADO, ENVIADO, ENTREGADO, CANCELADO o RECHAZADO |
| `PED_CORIGEN` | `origen` | varchar(15) | No |  | WEB (el cliente lo envió) o PRESENCIAL (Richard lo registró) |
| `PED_CCLIENTE_NOMBRE` | `cliente_nombre` | varchar(150) | Sí |  | Nombres y apellidos; obligatorio en pedidos WEB |
| `PED_CCLIENTE_DNI` | `cliente_dni` | varchar(8) | Sí |  | DNI de 8 dígitos; obligatorio solo en entrega por AGENCIA (privado) |
| `PED_CCLIENTE_TELEFONO` | `cliente_telefono` | varchar(9) | Sí |  | Teléfono de 9 dígitos que empieza con 9; obligatorio en pedidos WEB (privado) |
| `PED_CTIPO_ENTREGA` | `tipo_entrega` | varchar(20) | No |  | AGENCIA, DELIVERY_LIMA, PUNTO_ENCUENTRO o RECOJO |
| `PED_CAGENCIA` | `agencia` | varchar(10) | Sí |  | SHALOM, OLVA u OTRA; solo en AGENCIA |
| `PED_CAGENCIA_CIUDAD` | `agencia_ciudad` | varchar(80) | Sí |  | Ciudad de la agencia de destino |
| `PED_CAGENCIA_REFERENCIA` | `agencia_referencia` | varchar(200) | Sí |  | Referencia de la agencia |
| `PED_CPUNTO_ENCUENTRO` | `punto_encuentro` | varchar(200) | Sí |  | Lugar de entrega personal en Lima, acordado con el cliente |
| `PED_DENTREGA_PROGRAMADA` | `entrega_programada` | timestamptz | Sí |  | Fecha y hora acordadas para la entrega personal |
| `PED_NSUBTOTAL` | `subtotal` | numeric(10,2) | No |  | Suma de los subtotales de los ítems |
| `PED_NCOSTO_ENVIO` | `costo_envio` | numeric(10,2) | Sí |  | Costo de envío; nulo hasta cotizar |
| `PED_NTOTAL` | `total` | numeric(10,2) | No |  | subtotal + costo de envío (mientras no se cotiza, igual al subtotal) |
| `MPA_NID` | `metodo_pago` | bigint | Sí | FK → TBL_RMETODO_PAGO | Cómo se pagó; se llena al confirmar el pago |
| `USU_NID_CREADO_POR` | `creado_por` | bigint | Sí | FK → auth_user | Quién lo registró (solo ventas PRESENCIALES) |
| `PED_CNOTAS` | `notas` | text | Sí |  | Notas |
| `PED_DFECHA_COTIZADO` | `fecha_cotizado` | timestamptz | Sí |  | Cuándo pasó a COTIZADO |
| `PED_DFECHA_PAGADO` | `fecha_pagado` | timestamptz | Sí |  | Cuándo pasó a PAGADO |
| `PED_DFECHA_ENVIADO` | `fecha_enviado` | timestamptz | Sí |  | Cuándo pasó a ENVIADO |
| `PED_DFECHA_ENTREGADO` | `fecha_entregado` | timestamptz | Sí |  | Cuándo pasó a ENTREGADO |
| `PED_DFECHA_CIERRE` | `fecha_cierre` | timestamptz | Sí |  | Cuándo se canceló o rechazó |
| `PED_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `PED_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |

- **IX** `TBL_TPEDIDO_PED_CESTADO_PED_DFECHA_CREACION_IX`: (PED_CESTADO, PED_DFECHA_CREACION)
- **IX** `TBL_TPEDIDO_TEL_IX`: (PED_CCLIENTE_TELEFONO)
- **IX** `TBL_TPEDIDO_ORI_EST_FEC_IX`: (PED_CORIGEN, PED_CESTADO, PED_DFECHA_CREACION)
- **UK** `TBL_TPEDIDO_PED_CCODIGO_UK`: (PED_CCODIGO)
- **CK** `TBL_TPEDIDO_TOTAL_CK`: PED_NTOTAL = PED_NSUBTOTAL + coalesce(PED_NCOSTO_ENVIO, 0)

### `TBL_TPEDIDO_ITEM` (ITE) – Líneas del pedido con copia (snapshot) de nombre, talla y precio.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `ITE_NID` | `id` | bigint | No | PK | Identificador |
| `PED_NID` | `pedido` | bigint | No | FK → TBL_TPEDIDO | Pedido |
| `VAR_NID` | `variante` | bigint | No | FK → TBL_RVARIANTE | Variante comprada (relación protegida) |
| `ITE_CNOMBRE_PRODUCTO` | `nombre_producto` | varchar(150) | No |  | COPIA del nombre del producto |
| `ITE_CSKU` | `sku` | varchar(40) | No |  | COPIA del código de la variante |
| `ITE_CTALLA` | `talla` | varchar(10) | No |  | COPIA de la talla |
| `ITE_CCOLOR` | `color` | varchar(40) | No |  | COPIA del color; vacío si no aplica |
| `ITE_NPRECIO_UNIDAD` | `precio_unidad` | numeric(10,2) | No |  | COPIA del precio unitario aplicado |
| `ITE_NCANTIDAD` | `cantidad` | integer | No |  | Cantidad (mínimo 1) |
| `ITE_NSUBTOTAL` | `subtotal` | numeric(10,2) | No |  | precio_unidad por cantidad |
| `ITE_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `ITE_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |

- **CK** `TBL_TPEDIDO_ITEM_CANTIDAD_CK`: ITE_NCANTIDAD >= 1

### `TBL_LPEDIDO_ESTADO` (PES) – Bitácora de cada cambio de estado de un pedido.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `PES_NID` | `id` | bigint | No | PK | Identificador |
| `PED_NID` | `pedido` | bigint | No | FK → TBL_TPEDIDO | Pedido |
| `PES_CESTADO_ANTERIOR` | `estado_anterior` | varchar(15) | Sí |  | Estado de origen; nulo al crear el pedido |
| `PES_CESTADO_NUEVO` | `estado_nuevo` | varchar(15) | No |  | Estado de destino |
| `USU_NID_CAMBIADO_POR` | `cambiado_por` | bigint | Sí | FK → auth_user | Quién cambió; nulo si lo creó el cliente en la web |
| `PES_CNOTA` | `nota` | varchar(255) | Sí |  | Nota opcional |
| `PES_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |

- **IX** `TBL_LPEDIDO_ESTADO_PED_NID_PES_DFECHA_CREACION_IX`: (PED_NID, PES_DFECHA_CREACION)
- Sin fecha de actualización (inmutable).

### `TBL_HPEDIDO` (HPE) – Historial completo de cambios de Pedido, generado por django-simple-history.

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `HPE_NID` | `history_id` | bigint | No | PK | Identificador del historial |
| `PED_NID` | `id` | bigint | No | FK → TBL_TPEDIDO | Pedido al que pertenece la copia |

- La genera la librería con table_name='TBL_HPEDIDO'. Las columnas history_date, history_type y history_user conservan su nombre. Las columnas copiadas de TBL_TPEDIDO conservan los nombres de esa tabla.

---

## App `envios`

### `TBL_TENVIO` (ENV) – Datos del envío por agencia (solo pedidos con entrega AGENCIA).

| Columna | Campo Django | Tipo | Nulo | Clave | Descripción |
|---|---|---|---|---|---|
| `ENV_NID` | `id` | bigint | No | PK | Identificador |
| `PED_NID` | `pedido` | bigint | No | FK → TBL_TPEDIDO, UK | Pedido (uno a uno) |
| `ENV_CAGENCIA` | `agencia` | varchar(10) | No |  | SHALOM, OLVA u OTRA |
| `ENV_CNUMERO_ORDEN_AGENCIA` | `numero_orden_agencia` | varchar(30) | No |  | Número de orden de la agencia |
| `ENV_CCLAVE_RECOJO` | `clave_recojo` | varchar(4) | No |  | Clave de recojo de 4 dígitos (privado) |
| `ENV_CIMAGEN_BOLETA` | `imagen_boleta` | varchar(255) | No |  | Ruta de la foto de la boleta, en bucket privado (privado) |
| `ENV_NCOSTO_FLETE` | `costo_flete` | numeric(10,2) | No |  | Costo real del flete en PEN |
| `ENV_CQUIEN_PAGA` | `quien_paga` | varchar(20) | No |  | CLIENTE_ADELANTADO, CLIENTE_EN_DESTINO o RICHARD_ADELANTO |
| `ENV_OCOBRADO` | `cobrado` | boolean | No |  | Flete cobrado o pendiente de cobro |
| `ENV_DFECHA_DESPACHO` | `fecha_despacho` | timestamptz | No |  | Fecha de despacho en la agencia |
| `ENV_CNOTAS` | `notas` | text | Sí |  | Notas |
| `ENV_DFECHA_CREACION` | `fecha_creacion` | timestamptz | No |  | Fecha de creación |
| `ENV_DFECHA_ACTUALIZACION` | `fecha_actualizacion` | timestamptz | No |  | Fecha de última actualización |


---

## Valores permitidos

### PED_CESTADO / PES_CESTADO_*

| Valor | Significado |
|---|---|
| `NUEVO` | Pedido recibido; falta cotizar el envío |
| `COTIZADO` | Total final definido; esperando el pago |
| `PAGADO` | Pago verificado por Richard; stock descontado |
| `ENVIADO` | Entregado a la agencia o al delivery |
| `ENTREGADO` | El cliente ya tiene su pedido |
| `CANCELADO` | El cliente desistió o no pagó |
| `RECHAZADO` | Richard no acepta el pedido |

### PED_CORIGEN

| Valor | Significado |
|---|---|
| `WEB` | El cliente envió el pedido desde la tienda |
| `PRESENCIAL` | Richard registró la venta en persona |

### PED_CTIPO_ENTREGA

| Valor | Significado |
|---|---|
| `AGENCIA` | Envío a provincia por Shalom u Olva; exige DNI y datos de agencia |
| `DELIVERY_LIMA` | Delivery dentro de Lima cotizado por Richard |
| `PUNTO_ENCUENTRO` | Richard se encuentra con el cliente en Lima, entrega y cobra ahí; nace con envío S/ 0 |
| `RECOJO` | El cliente recoge; nace con envío S/ 0 |

### PED_CAGENCIA / ENV_CAGENCIA

| Valor | Significado |
|---|---|
| `SHALOM` | Agencia Shalom |
| `OLVA` | Agencia Olva |
| `OTRA` | Otra agencia |

### ENV_CQUIEN_PAGA

| Valor | Significado |
|---|---|
| `CLIENTE_ADELANTADO` | El cliente pagó el flete antes del despacho |
| `CLIENTE_EN_DESTINO` | El cliente paga el flete al recoger |
| `RICHARD_ADELANTO` | Richard lo adelantó; queda como pendiente de cobro |

### MPA_CTIPO

| Valor | Significado |
|---|---|
| `YAPE` | Yape con QR, titular y número copiable |
| `PLIN` | Plin (fase posterior) |
| `EFECTIVO` | Dinero en efectivo, típico en entregas personales |

### MOV_CTIPO

| Valor | Significado |
|---|---|
| `ENTRADA` | Ingreso de mercadería (cantidad positiva) |
| `VENTA` | Salida por venta al confirmar el pago (cantidad negativa) |
| `AJUSTE` | Corrección de inventario (positiva o negativa) |
| `DEVOLUCION` | Regreso de stock por cancelación o rechazo (cantidad positiva) |

### EQU_CTIPO

| Valor | Significado |
|---|---|
| `SELECCION` | Selección nacional |
| `CLUB` | Club internacional |
| `ORIGINAL` | Diseño propio Emuná Sport |

### PRO_CEQUIPACION

| Valor | Significado |
|---|---|
| `LOCAL` | Local / Titular |
| `ALTERNA` | Alterna / Visitante |
| `ESPECIAL` | Edición especial |
| `RETRO` | Retro / Histórica |
| `ENTRENAMIENTO` | Entrenamiento / Línea propia |

## Datos privados

Columnas marcadas «(privado)»: nunca en URLs, logs, páginas públicas ni mensajes de error (ver `../07-seguridad-datos.md`).
