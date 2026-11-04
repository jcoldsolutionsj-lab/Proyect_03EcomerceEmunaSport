# 02 – Reglas de negocio

## Catálogo
- Un **producto** tiene nombre, descripción, categoría, precio base por unidad, fotos y estado (activo/oculto).
- Cada producto tiene **variantes**: la talla es obligatoria; color y modelo son opcionales.
- El stock se lleva **por variante** (por talla).
- Categorías organizan el catálogo por uso (fútbol, entrenamiento, casual), colección o tela. Las categorías se crean desde el admin.
- Cada producto tiene un **código interno** (SKU) tipo `EMU-001`.
- **Marca:** el campo existe pero está apagado por defecto. Richard lo activa solo si un producto tiene una marca que puede mostrar. Por defecto el catálogo no muestra marcas ni nombres de clubes.
- Un producto sin stock en una talla muestra esa talla como «agotada» y no se puede agregar.

## Precios
- Cada producto tiene un **precio por unidad** en soles.
- Reglas de **precio por mayor** configurables por producto: «desde N unidades, precio S/ X». Inicialmente se espera poco volumen (1 a 3 docenas). Se aplica sumando las unidades del mismo producto en el pedido (confirmar con Richard, ver doc 11).
- Si no hay regla de mayor, se cobra el precio por unidad.
- El precio se calcula en el servidor al crear el pedido y se guarda como copia en cada ítem.

## Stock
- El stock disponible de una variante es su cantidad actual.
- El stock **se descuenta cuando Richard confirma el pago**, no al enviar el pedido.
- Si al confirmar no hay stock suficiente, el sistema no confirma y avisa; Richard decide (ajustar el pedido o rechazarlo).
- Todo movimiento (entrada, venta, ajuste, devolución) queda en el registro de movimientos con fecha, motivo y quién lo hizo.
- Si un pedido ya pagado se cancela o rechaza, el stock se devuelve con un movimiento de devolución.
- Alerta de stock bajo con umbral configurable por producto (valor por defecto en Ajustes).

## Modalidades de entrega y venta
1. **Provincia por agencia (`AGENCIA`):** Shalom u Olva. El delivery lo paga el cliente y lo cotiza Richard según la agencia y el destino; se suma al total. El cliente paga antes de que Richard despache. Exige nombres y apellidos, **DNI (8 dígitos)**, teléfono (9 dígitos que empieza con 9) y agencia de destino (ciudad y referencia). Al despachar, Richard registra: agencia, número de orden, **clave de 4 dígitos**, foto de la boleta, costo del flete y quién lo pagó (`CLIENTE_ADELANTADO`, `CLIENTE_EN_DESTINO`, `RICHARD_ADELANTO`). Un botón arma el mensaje de WhatsApp con número de orden, clave y cómo seguir el envío.
2. **Delivery en Lima (`DELIVERY_LIMA`):** Richard cotiza el delivery dentro de Lima y lo suma al total. Pide nombre, teléfono y dirección/referencia (DNI opcional). Cuando sale el motorizado pasa a `ENVIADO`.
3. **Entrega personal en punto de encuentro en Lima (`PUNTO_ENCUENTRO`):** Es el caso más frecuente en Lima. Richard se cita con el cliente en un lugar acordado (estación, centro comercial, etc.), le entrega la mercadería en mano y **ahí mismo recibe el Yape (o efectivo)**. Nace directamente en `COTIZADO` con costo de envío `S/ 0` (salvo que acuerden un adicional). Guarda el lugar (`punto_encuentro`) y la fecha/hora acordadas (`entrega_programada`). El DNI no es obligatorio. Cuando se encuentran y el cliente paga, Richard confirma el pago y la entrega en un solo paso (`COTIZADO` → `PAGADO` → `ENTREGADO`).
4. **Recojo (`RECOJO`):** El cliente recoge sin costo de envío. Nace ya en `COTIZADO` con envío `S/ 0`.
5. **Venta presencial directa (origen `PRESENCIAL`):** Cuando la venta se cierra por WhatsApp o en persona sin que el cliente llene el carrito web, Richard registra la venta en el panel eligiendo variantes, cantidades y método de pago; el sistema crea el pedido, descuenta el stock y lo deja en `PAGADO` o `ENTREGADO` en un solo paso, para que ningún movimiento de camisetas quede fuera del control.

## Pago
- Método principal: **Yape**. Se muestra el QR, el nombre del titular y el número con botón «copiar». En entregas personales o ventas presenciales también se puede registrar **Efectivo** (y **Plin** cuando se active).
- El QR y el titular se suben y cambian desde el admin (no se guardan en el código ni en el repositorio).
- El QR de Yape no lleva el monto: la pantalla muestra el total grande y claro.
- En envíos a provincia o delivery previo pago, el cliente envía el voucher por WhatsApp a Richard. En punto de encuentro en Lima, el cliente yapea frente a Richard al recibir la mercadería.
- Richard confirma el pago manualmente y registra con qué método se pagó.

## PDF del pedido
Contiene: logo, código del pedido, fecha, lista de ítems (producto, talla, cantidad, precio, subtotal), total de camisetas, modalidad de entrega y línea de delivery («por cotizar», monto o «S/ 0.00 – Punto de encuentro / Recojo»), total final y datos de contacto de Richard. Es visible y descargable por el cliente. Debe verse profesional.

## Dashboard y notificaciones (versión 1)
Reglas simples: stock bajo, productos sin ventas en N días, más vendidos, pedidos pendientes hace más de 24 horas, ventas por período, pedidos rechazados/cancelados. Las notificaciones por correo van en una fase posterior.

## Roles
- **Richard** (grupo «Dueño»): todo lo operativo; no ve configuración técnica.
- **Jonathan** (superusuario): acceso total.
