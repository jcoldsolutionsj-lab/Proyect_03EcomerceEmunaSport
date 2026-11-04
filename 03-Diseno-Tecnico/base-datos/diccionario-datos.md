# Diccionario de datos (nombres físicos)

Aplica `12-estandar-base-datos.md` al modelo lógico de `04-modelo-de-datos.md`. Cada tabla muestra el nombre físico, su sigla de 3 letras y el nombre en Python (clase y campo de Django).

**Letras de tipo:** N numérico (incluye llaves y decimales) · C carácter · D fecha o fecha-hora · B binario · O booleano.
**Columnas comunes:** todas las tablas llevan `PPP_DCREATED_AT` y `PPP_DUPDATED_AT` (campos `created_at`, `updated_at`), salvo donde se indique. Dinero: `numeric(10,2)` en PEN. Los archivos (fotos, QR, boletas) guardan la **ruta** como texto (`C`), no el binario.

## Resumen de tablas

| Tabla física | Sigla | Clase Django | App | Tipo |
|---|---|---|---|---|
| `TBL_RSTORE_SETTING` | STO | `StoreSettings` | core | Referencia |
| `TBL_RPAYMENT_METHOD` | PAY | `PaymentMethod` | core | Referencia |
| `TBL_RCATEGORY` | CAT | `Category` | catalog | Referencia |
| `TBL_RPRODUCT` | PRD | `Product` | catalog | Referencia |
| `TBL_RPRODUCT_IMAGE` | PIM | `ProductImage` | catalog | Referencia |
| `TBL_RVARIANT` | VAR | `Variant` | catalog | Referencia |
| `TBL_RPRICE_RULE` | PRU | `PriceRule` | catalog | Referencia |
| `TBL_TSTOCK_MOVEMENT` | SMO | `StockMovement` | inventory | Transacción |
| `TBL_TORDER` | ORD | `Order` | orders | Transacción |
| `TBL_TORDER_ITEM` | ORI | `OrderItem` | orders | Transacción |
| `TBL_LORDER_STATUS` | OSL | `OrderStatusLog` | orders | Log |
| `TBL_HORDER` | HOR | historial de `Order` (`simple-history`) | orders | Histórico |
| `TBL_TSHIPMENT` | SHI | `Shipment` | shipping | Transacción |

Tablas de Django que **no** se renombran: `auth_user`, `auth_group`, `auth_permission`, `django_session`, `django_migrations`, `django_admin_log`, `django_content_type` y sus tablas de unión.

---

## core

### `TBL_RSTORE_SETTING` (STO) – Ajustes de la tienda (registro único)
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `STO_NID` | `id` | PK | Identificador |
| `STO_CNAME` | `name` | C | Nombre de la tienda |
| `STO_CWHATSAPP_NUMBER` | `whatsapp_number` | C | WhatsApp de Richard |
| `STO_CFOOTER_TEXT` | `footer_text` | C | Texto de pie de página |
| `STO_NLOW_STOCK_THRESHOLD` | `low_stock_threshold` | N | Umbral de stock bajo por defecto |
| `STO_OSHOW_BRANDS` | `show_brands` | O | Mostrar marcas (apagado por defecto) |

### `TBL_RPAYMENT_METHOD` (PAY) – Métodos de pago
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `PAY_NID` | `id` | PK | Identificador |
| `PAY_CTYPE` | `type` | C | `yape`, `plin`… |
| `PAY_CHOLDER_NAME` | `holder_name` | C | Titular de la cuenta |
| `PAY_CACCOUNT_NUMBER` | `account_number` | C | Número (copiable) |
| `PAY_CQR_IMAGE` | `qr_image` | C | Ruta de la imagen del QR (no va al repositorio) |
| `PAY_OACTIVE` | `is_active` | O | Activo |
| `PAY_NSORT_ORDER` | `sort_order` | N | Orden de aparición |

## catalog

### `TBL_RCATEGORY` (CAT) – Categorías
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `CAT_NID` | `id` | PK | Identificador |
| `CAT_CNAME` | `name` | C | Nombre |
| `CAT_CSLUG` | `slug` | C | Texto para la URL |
| `CAT_NSORT_ORDER` | `sort_order` | N | Orden |
| `CAT_OACTIVE` | `is_active` | O | Activa |

### `TBL_RPRODUCT` (PRD) – Productos
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `PRD_NID` | `id` | PK | Identificador |
| `CAT_NID` | `category` | FK → `TBL_RCATEGORY` | Categoría |
| `PRD_CNAME` | `name` | C | Nombre |
| `PRD_CSLUG` | `slug` | C | Texto para la URL |
| `PRD_CSKU` | `sku` | C | Código interno único, ej. `EMU-001` |
| `PRD_CDESCRIPTION` | `description` | C | Descripción |
| `PRD_CBRAND` | `brand` | C | Marca (opcional) |
| `PRD_NUNIT_PRICE` | `unit_price` | N | Precio base por unidad (PEN) |
| `PRD_OACTIVE` | `is_active` | O | Activo |
| `PRD_OFEATURED` | `is_featured` | O | Destacado |

### `TBL_RPRODUCT_IMAGE` (PIM) – Fotos del producto
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `PIM_NID` | `id` | PK | Identificador |
| `PRD_NID` | `product` | FK → `TBL_RPRODUCT` | Producto |
| `PIM_CORIGINAL_PATH` | `original` | C | Ruta del original (privado) |
| `PIM_CTHUMB_PATH` | `thumbnail` | C | Miniatura ~400 px WebP |
| `PIM_CDETAIL_PATH` | `detail` | C | Detalle ~900 px WebP |
| `PIM_NSORT_ORDER` | `sort_order` | N | Orden |
| `PIM_OPRIMARY` | `is_primary` | O | Imagen principal |

### `TBL_RVARIANT` (VAR) – Variantes (talla, color, modelo)
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `VAR_NID` | `id` | PK | Identificador |
| `PRD_NID` | `product` | FK → `TBL_RPRODUCT` | Producto |
| `VAR_CSIZE` | `size` | C | Talla (obligatoria) |
| `VAR_CCOLOR` | `color` | C | Color (opcional) |
| `VAR_CMODEL` | `model` | C | Modelo (opcional) |
| `VAR_CSKU` | `sku` | C | Código único de la variante |
| `VAR_NSTOCK_QUANTITY` | `stock_quantity` | N | Stock actual (≥ 0). Solo cambia por `StockMovement` |
| `VAR_NLOW_STOCK_THRESHOLD` | `low_stock_threshold` | N | Umbral propio (opcional) |
| `VAR_OACTIVE` | `is_active` | O | Activa |

Restricción única: (`PRD_NID`, `VAR_CSIZE`, `VAR_CCOLOR`, `VAR_CMODEL`).

### `TBL_RPRICE_RULE` (PRU) – Precio por mayor
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `PRU_NID` | `id` | PK | Identificador |
| `PRD_NID` | `product` | FK → `TBL_RPRODUCT` | Producto |
| `PRU_NMIN_QUANTITY` | `min_quantity` | N | Desde N unidades |
| `PRU_NUNIT_PRICE` | `unit_price` | N | Precio unitario aplicado (PEN) |

## inventory

### `TBL_TSTOCK_MOVEMENT` (SMO) – Movimientos de stock (inmutable)
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `SMO_NID` | `id` | PK | Identificador |
| `VAR_NID` | `variant` | FK → `TBL_RVARIANT` | Variante |
| `SMO_CTYPE` | `type` | C | `IN`, `SALE`, `ADJUSTMENT`, `RETURN` |
| `SMO_NQUANTITY` | `quantity` | N | Cantidad (positiva o negativa) |
| `SMO_CREASON` | `reason` | C | Motivo |
| `ORD_NID` | `order` | FK → `TBL_TORDER` (opcional) | Pedido relacionado |
| `USR_NID_CREATED_BY` | `created_by` | FK → `auth_user` | Quién lo hizo |

No se edita ni se borra. Candidato a `TRG_UPD_STOCK_MOVEMENT_BLOCK` y `TRG_DEL_STOCK_MOVEMENT_BLOCK`.

## orders

### `TBL_TORDER` (ORD) – Pedidos
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `ORD_NID` | `id` | PK | Identificador |
| `ORD_CCODE` | `code` | C | Código público no adivinable, único (ej. `EMU-7K3Q9X`) |
| `ORD_CSTATUS` | `status` | C | `NEW`, `QUOTED`, `PAID`, `SHIPPED`, `DELIVERED`, `CANCELLED`, `REJECTED` |
| `ORD_CCUSTOMER_NAME` | `customer_name` | C | Nombres y apellidos |
| `ORD_CCUSTOMER_DNI` | `customer_dni` | C | DNI de 8 dígitos (**privado**) |
| `ORD_CCUSTOMER_PHONE` | `customer_phone` | C | Teléfono de 9 dígitos que empieza con 9 |
| `ORD_CDELIVERY_TYPE` | `delivery_type` | C | `AGENCY`, `LIMA`, `PICKUP` |
| `ORD_CAGENCY` | `agency` | C | `SHALOM`, `OLVA`, otra |
| `ORD_CAGENCY_CITY` | `agency_city` | C | Ciudad de la agencia de destino |
| `ORD_CAGENCY_REFERENCE` | `agency_reference` | C | Referencia de la agencia |
| `ORD_NSUBTOTAL` | `subtotal` | N | Suma de los subtotales de los ítems |
| `ORD_NSHIPPING_COST` | `shipping_cost` | N | Costo de envío (nulo hasta cotizar) |
| `ORD_NTOTAL` | `total` | N | `subtotal + shipping_cost` |
| `ORD_CNOTES` | `notes` | C | Notas |
| `ORD_DQUOTED_AT` | `quoted_at` | D | Fecha en que pasó a `QUOTED` |
| `ORD_DPAID_AT` | `paid_at` | D | Fecha en que pasó a `PAID` |
| `ORD_DSHIPPED_AT` | `shipped_at` | D | Fecha en que pasó a `SHIPPED` |
| `ORD_DDELIVERED_AT` | `delivered_at` | D | Fecha en que pasó a `DELIVERED` |
| `ORD_DCLOSED_AT` | `closed_at` | D | Fecha de cancelación o rechazo |

Índices: `TBL_TORDER_ORD_CSTATUS_ORD_DCREATED_AT_IX`, `TBL_TORDER_ORD_CCODE_IX`. Restricción única: `ORD_CCODE`.

### `TBL_TORDER_ITEM` (ORI) – Ítems del pedido (con copias)
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `ORI_NID` | `id` | PK | Identificador |
| `ORD_NID` | `order` | FK → `TBL_TORDER` | Pedido |
| `VAR_NID` | `variant` | FK → `TBL_RVARIANT` (protegida) | Variante comprada |
| `ORI_CPRODUCT_NAME` | `product_name` | C | **Copia** del nombre |
| `ORI_CSKU` | `sku` | C | **Copia** del código |
| `ORI_CSIZE` | `size` | C | **Copia** de la talla |
| `ORI_CCOLOR` | `color` | C | **Copia** del color |
| `ORI_NUNIT_PRICE` | `unit_price` | N | **Copia** del precio unitario aplicado |
| `ORI_NQUANTITY` | `quantity` | N | Cantidad (≥ 1) |
| `ORI_NSUBTOTAL` | `subtotal` | N | `unit_price × quantity` |

### `TBL_LORDER_STATUS` (OSL) – Bitácora de estados
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `OSL_NID` | `id` | PK | Identificador |
| `ORD_NID` | `order` | FK → `TBL_TORDER` | Pedido |
| `OSL_CFROM_STATUS` | `from_status` | C | Estado anterior |
| `OSL_CTO_STATUS` | `to_status` | C | Estado nuevo |
| `USR_NID_CHANGED_BY` | `changed_by` | FK → `auth_user` | Quién cambió |
| `OSL_CNOTE` | `note` | C | Nota opcional |

### `TBL_HORDER` (HOR) – Historial de `Order`
Generada por `django-simple-history` con `table_name='TBL_HORDER'`. Las columnas propias de la librería (`history_id`, `history_date`, `history_type`, `history_user`) se **dejan con su nombre**; las columnas copiadas de `TBL_TORDER` conservan los nombres de esa tabla.

## shipping

### `TBL_TSHIPMENT` (SHI) – Envíos
| Columna | Campo Django | Tipo | Descripción |
|---|---|---|---|
| `SHI_NID` | `id` | PK | Identificador |
| `ORD_NID` | `order` | FK única → `TBL_TORDER` | Pedido (uno a uno) |
| `SHI_CAGENCY` | `agency` | C | Agencia |
| `SHI_CAGENCY_ORDER_NUMBER` | `agency_order_number` | C | Número de orden de la agencia |
| `SHI_CPICKUP_KEY` | `pickup_key` | C | Clave de recojo de 4 dígitos (**privada**) |
| `SHI_CRECEIPT_IMAGE` | `receipt_image` | C | Ruta de la boleta (bucket privado) |
| `SHI_NFREIGHT_COST` | `freight_cost` | N | Costo del flete (PEN) |
| `SHI_CPAYER` | `payer` | C | `CUSTOMER_AT_DEST`, `CUSTOMER_PREPAID`, `RICHARD_ADVANCED` |
| `SHI_OCOLLECTED` | `is_collected` | O | Cobrado / pendiente de cobro |
| `SHI_DSHIPPED_AT` | `shipped_at` | D | Fecha de despacho |
| `SHI_CNOTES` | `notes` | C | Notas |

---

## Datos privados
`ORD_CCUSTOMER_DNI`, `ORD_CCUSTOMER_PHONE`, `SHI_CPICKUP_KEY`, `SHI_CRECEIPT_IMAGE` y `PAY_CQR_IMAGE`: nunca en URLs, logs, páginas públicas ni mensajes de error (ver `07-seguridad-datos.md`).

## Cambios al modelo lógico detectados
- `04-modelo-de-datos.md` no listaba el precio base en `Product`, aunque `PriceRule` dice que está en `Product.unit_price`. Se agrega `PRD_NUNIT_PRICE` y se corrige el doc 04.
- Las fechas de cambio de estado de `Order` se detallan como `ORD_DQUOTED_AT`, `ORD_DPAID_AT`, `ORD_DSHIPPED_AT`, `ORD_DDELIVERED_AT` y `ORD_DCLOSED_AT` (propuesta; confirmar en la Fase 3).
