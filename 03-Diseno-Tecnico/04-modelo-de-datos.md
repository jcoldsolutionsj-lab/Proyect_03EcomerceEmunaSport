# 04 – Modelo de datos

Convenciones: claves primarias `id` (en base `PPP_NID`); `fecha_creacion` y `fecha_actualizacion` en todos (salvo tablas inmutables); dinero `DecimalField(max_digits=10, decimal_places=2)` en PEN; zona `America/Lima`; código, modelos, campos y textos de interfaz en **español**. Los nombres **físicos** de tablas y columnas en la base van en MAYÚSCULAS según `12-estandar-base-datos.md` (diccionario completo en `base-datos/diccionario-datos.md` y `base-datos/diccionario-datos.xlsx`).

## Apps y modelos
### `nucleo` (`TBL_RCONFIGURACION_TIENDA`, `TBL_RMETODO_PAGO`)
- **ConfiguracionTienda** (único): `nombre`, `numero_whatsapp`, `texto_pie`, `umbral_stock_bajo`, `mostrar_marcas` (bool, apagado), `dias_sin_ventas`, `horas_pedido_pendiente`. Se edita en el admin.
- **MetodoPago**: `tipo` (`YAPE`, `PLIN`, `EFECTIVO`), `titular`, `numero_cuenta` (copiable), `imagen_qr`, `activo`, `orden`.

### `catalogo` (`TBL_RCATEGORIA`, `TBL_REQUIPO`, `TBL_RPRODUCTO`, `TBL_RIMAGEN_PRODUCTO`, `TBL_RVARIANTE`, `TBL_RREGLA_PRECIO`)
- **Categoria**: `nombre`, `slug`, `orden`, `activa`.
- **Equipo**: `nombre`, `slug`, `tipo` (`SELECCION`, `CLUB`, `ORIGINAL`), `alias_busqueda` (apodos/sinónimos separados por coma para buscador e IA), `orden`, `activo`.
- **Producto**: `nombre`, `slug`, `sku` único, `descripcion`, `categoria`, `equipo` (FK opcional a `Equipo`), `equipacion` (`LOCAL`, `ALTERNA`, `ESPECIAL`, `RETRO`, `ENTRENAMIENTO`), `temporada` (ej. `2026-2027`), `palabras_clave` (sinónimos), `marca` (texto, opcional), `precio_unidad` (precio actual de venta, ej. `S/ 55.00`), `precio_anterior` (opcional, precio regular tachado antes de oferta, ej. `S/ 69.90`), `activo`, `destacado`.
- **ImagenProducto**: `producto`, `ruta_original` (privado), versiones generadas (`ruta_miniatura` ~400 px y `ruta_detalle` ~900 px en WebP), `texto_alternativo` (opcional; si es vacío se genera automáticamente con el nombre del producto para SEO y accesibilidad), `orden`, `es_principal`.
- **Variante**: `producto`, `talla` (obligatoria), `color` (opcional), `modelo` (opcional), `sku` único, `cantidad_stock` (entero ≥ 0), `umbral_stock_bajo` (opcional), `activa`. Única por (`producto`, `talla`, `color`, `modelo`).
- **ReglaPrecio**: `producto`, `cantidad_minima`, `precio_unidad`. El precio base está en `Producto.precio_unidad`.

### `inventario` (`TBL_TMOVIMIENTO_STOCK`)
- **MovimientoStock**: `variante`, `tipo` (`ENTRADA`, `VENTA`, `AJUSTE`, `DEVOLUCION`), `cantidad` (positiva o negativa, distinta de 0), `motivo`, `pedido` (opcional), `creado_por`. Inmutable: no se edita ni se borra. `Variante.cantidad_stock` siempre es la suma de sus movimientos.

### `pedidos` (`TBL_TPEDIDO`, `TBL_TPEDIDO_ITEM`, `TBL_LPEDIDO_ESTADO`, `TBL_HPEDIDO`)
- **Pedido**: `codigo` público único no adivinable, `estado` (`NUEVO`, `COTIZADO`, `PAGADO`, `ENVIADO`, `ENTREGADO`, `CANCELADO`, `RECHAZADO`), `origen` (`WEB`, `PRESENCIAL`), cliente (`cliente_nombre`, `cliente_dni`, `cliente_telefono`), `tipo_entrega` (`AGENCIA`, `DELIVERY_LIMA`, `PUNTO_ENCUENTRO`, `RECOJO`), agencia destino (`agencia`: `SHALOM`, `OLVA`, `OTRA`; `agencia_ciudad`, `agencia_reference`), entrega personal en Lima (`punto_encuentro`, `entrega_programada`), `subtotal`, `costo_envio` (nulo hasta cotizar), `total`, `metodo_pago`, `creado_por` (en ventas presenciales), `notas`, fechas de cambio de estado (`fecha_cotizado`, `fecha_pagado`, `fecha_enviado`, `fecha_entregado`, `fecha_cierre`). Historial con `django-simple-history` (`TBL_HPEDIDO`).
- **ItemPedido**: `pedido`, `variante` (FK protegida), **copias**: `nombre_producto`, `sku`, `talla`, `color`, `precio_unidad`, `cantidad`, `subtotal`.
- **RegistroEstadoPedido**: `pedido`, `estado_anterior`, `estado_nuevo`, `cambiado_por`, `nota`, `fecha_creacion`. Inmutable.

### `envios` (`TBL_TENVIO`)
- **Envio**: `pedido` (uno a uno, solo cuando `tipo_entrega = AGENCIA`), `agencia`, `numero_orden_agencia`, **`clave_recojo` (4 dígitos, privada)**, `imagen_boleta` (bucket privado), `costo_flete`, `quien_paga` (`CLIENTE_ADELANTADO`, `CLIENTE_EN_DESTINO`, `RICHARD_ADELANTO`), `cobrado`, `fecha_despacho`, `notas`.

## Invariantes (deben cumplirse siempre)
1. `Variante.cantidad_stock >= 0` y es igual a la suma de sus `MovimientoStock`.
2. `Pedido.total = subtotal + coalesce(costo_envio, 0)` y `subtotal = suma de ItemPedido.subtotal`.
3. Un pedido en `PAGADO`, `ENVIADO` o `ENTREGADO` tiene movimientos `VENTA` por cada ítem.
4. Un pedido en `ENVIADO` con `tipo_entrega = AGENCIA` tiene un `Envio` completo.
5. Los códigos de pedido y SKU son únicos.
6. Validaciones: DNI = 8 dígitos (obligatorio en `AGENCIA`); teléfono peruano = 9 dígitos que empieza con 9 (obligatorio en pedidos `WEB`); cantidad ≥ 1.

## Índices sugeridos
`TBL_REQUIPO(EQU_OACTIVO, EQU_NORDEN, EQU_CNOMBRE)`, `TBL_RPRODUCTO(CAT_NID, EQU_NID, PRO_ODESTACADO) WHERE PRO_OACTIVO = true`, `TBL_RVARIANTE(PRO_NID)`, `TBL_RVARIANTE(VAR_CTALLA, PRO_NID) WHERE VAR_OACTIVA = true AND VAR_NCANTIDAD_STOCK > 0`, `TBL_TPEDIDO(PED_CESTADO, PED_DFECHA_CREACION)`, `TBL_TPEDIDO(PED_CCLIENTE_TELEFONO)`, `TBL_TPEDIDO(PED_CORIGEN, PED_CESTADO, PED_DFECHA_CREACION)`, `TBL_TPEDIDO(PED_CCODIGO)`, `TBL_TMOVIMIENTO_STOCK(VAR_NID, MOV_DFECHA_CREACION)` y en PostgreSQL índices `GIN` (`pg_trgm`) sobre `PRO_CNOMBRE`, `PRO_CPALABRAS_CLAVE`, `EQU_CNOMBRE` y `EQU_CALIAS_BUSQUEDA`.
