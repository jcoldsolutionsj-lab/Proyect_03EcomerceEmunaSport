# 02 – Reglas de negocio

## Catálogo
- Un **producto** tiene nombre, descripción, categoría, fotos y estado (activo/oculto).
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

## Envío
- El delivery **lo paga el cliente** y lo cotiza Richard según la agencia (Shalom u Olva) y el destino. El envío se suma al total del pedido.
- Opciones de entrega: provincia con agencia (Shalom/Olva), Lima, recojo (sin costo de envío).
- Datos del cliente para envío por agencia: nombres y apellidos, DNI (8 dígitos), teléfono (9 dígitos, empieza con 9), agencia de destino (ciudad y referencia).
- Al despachar, Richard registra: agencia, número de orden, **clave de 4 dígitos**, foto de la boleta y costo del flete. Quién pagó el flete es un campo (cliente / Richard lo adelantó / pago en destino); si no es de Richard, se marca informativo.
- Un botón arma el mensaje de WhatsApp para el cliente con número de orden, clave y cómo seguir el envío en la app de la agencia.

## Pago
- Método inicial: **Yape**. Se muestra el QR, el nombre del titular y el número con botón «copiar».
- El QR y el titular se suben y cambian desde el admin (no se guardan en el código ni en el repositorio). Plin u otro método se agrega después como otro método de pago.
- El QR de Yape no lleva el monto: la pantalla muestra el total grande y claro.
- El cliente envía el voucher por WhatsApp a Richard. Si desconfía de pagar así, sigue el pedido por WhatsApp con el PDF.
- Richard confirma el pago manualmente.

## PDF del pedido
Contiene: logo, código del pedido, fecha, lista de ítems (producto, talla, cantidad, precio, subtotal), total de camisetas, línea de delivery («por cotizar» o monto), total final y datos de contacto de Richard. Es visible y descargable por el cliente. Debe verse profesional.

## Dashboard y notificaciones (versión 1)
Reglas simples: stock bajo, productos sin ventas en N días, más vendidos, pedidos pendientes hace más de 24 horas, ventas por período, pedidos rechazados/cancelados. Las notificaciones por correo van en una fase posterior.

## Roles
- **Richard** (grupo «Dueño»): todo lo operativo; no ve configuración técnica.
- **Jonathan** (superusuario): acceso total.
