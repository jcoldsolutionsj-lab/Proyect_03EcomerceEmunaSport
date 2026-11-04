# 04 – Modelo de datos

Convenciones: claves primarias `id`; `created_at` y `updated_at` en todos; dinero `DecimalField(max_digits=10, decimal_places=2)` en PEN; zona `America/Lima`; textos de interfaz en español.

## Apps y modelos
### core
- **StoreSettings** (único): nombre de la tienda, número de WhatsApp de Richard, texto de pie, umbral de stock bajo por defecto, mostrar marcas (bool, apagado). Se edita en el admin.
- **PaymentMethod**: tipo (`yape`, `plin`, …), titular, número (copiable), imagen del QR, activo, orden.

### catalog
- **Category**: nombre, slug, orden, activa.
- **Product**: nombre, slug, sku único, descripción, categoría, marca (texto, opcional), activo, destacado.
- **ProductImage**: producto, imagen (original), versiones generadas (miniatura ~400 px y detalle ~900 px en WebP), orden, imagen principal.
- **Variant**: producto, talla (obligatoria), color (opcional), modelo (opcional), sku único, `stock_quantity` (entero ≥ 0), umbral de stock bajo (opcional), activa. Única por (producto, talla, color, modelo).
- **PriceRule**: producto, `min_quantity`, `unit_price`. El precio base está en `Product.unit_price`.

### inventory
- **StockMovement**: variante, tipo (`IN`, `SALE`, `ADJUSTMENT`, `RETURN`), cantidad (positiva o negativa), motivo, pedido (opcional), creado por. Inmutable: no se edita ni se borra. `Variant.stock_quantity` siempre es la suma de sus movimientos.

### orders
- **Order**: código público único no adivinable, estado, cliente (nombres, DNI, teléfono), tipo de entrega (`AGENCY`, `LIMA`, `PICKUP`), agencia destino (`SHALOM`, `OLVA`, otra), ciudad y referencia de la agencia, subtotal, costo de envío (nulo hasta cotizar), total, notas, fechas de cambio de estado. Historial con `django-simple-history`.
- **OrderItem**: pedido, variante (FK protegida), **copias**: nombre del producto, sku, talla, color, precio unitario aplicado, cantidad, subtotal.
- **OrderStatusLog**: pedido, de, a, usuario, nota, fecha.

### shipping
- **Shipment**: pedido (uno a uno), agencia, número de orden de la agencia, **clave de recojo (4 dígitos, privada)**, foto de boleta (bucket privado), costo del flete, quién paga (`CUSTOMER_AT_DEST`, `CUSTOMER_PREPAID`, `RICHARD_ADVANCED`), cobrado/pendiente de cobro, fecha de despacho, notas.

## Invariantes (deben cumplirse siempre)
1. `Variant.stock_quantity >= 0` y es igual a la suma de sus `StockMovement`.
2. `Order.total = subtotal + shipping_cost` y `subtotal = suma de OrderItem.subtotal`.
3. Un pedido en `PAID` o posterior tiene movimientos `SALE` por cada ítem.
4. Un pedido en `SHIPPED` tiene un `Shipment` completo.
5. Los códigos de pedido y SKU son únicos.
6. Validaciones: DNI = 8 dígitos; teléfono peruano = 9 dígitos que empieza con 9; cantidad ≥ 1.

## Índices sugeridos
`Order(status, created_at)`, `Order(code)`, `Variant(product)`, `StockMovement(variant, created_at)`.
