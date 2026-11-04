# 03 – Flujo de pedidos y estados

## Flujo A – Envío por agencia (provincia) o delivery en Lima
1. El cliente ve el catálogo, elige talla y cantidad (ve el stock) y agrega al carrito.
2. En el checkout ingresa sus datos y elige `AGENCIA` (Shalom/Olva) o `DELIVERY_LIMA`. Envía el pedido (sin pagar todavía).
3. El sistema crea el pedido en estado `NUEVO` con un **código no adivinable** (ej. `EMU-7K3Q9X`) y muestra la página del pedido con el detalle, el PDF y el botón de WhatsApp.
4. Richard abre el pedido en el admin, consulta el costo del flete o delivery e **ingresa el costo de envío**; el pedido pasa a `COTIZADO`.
5. Richard avisa al cliente con el botón de WhatsApp que lleva el enlace a la página del pedido.
6. El cliente abre su página, ve el total final, el QR de Yape, el titular y el número. Paga y envía el voucher por WhatsApp.
7. Richard revisa el pago y pasa el pedido a `PAGADO`. **Aquí se descuenta el stock.**
8. Richard despacha en la agencia (y registra número de orden, clave, boleta y flete) o envía con motorizado. El pedido pasa a `ENVIADO` y usa el botón de WhatsApp con los datos al cliente.
9. Cuando el cliente recibe, Richard puede marcar `ENTREGADO` (opcional en agencia).

## Flujo B – Punto de encuentro en Lima o Recojo (contraentrega con Yape ahí mismo)
Es lo que más ocurre en Lima: Richard se cita con el cliente en un lugar acordado, le deja la mercadería y ahí mismo recibe el Yape.
1. El cliente arma su pedido en la web y elige `PUNTO_ENCUENTRO` (indicando lugar propuesto, ej. estación o centro comercial) o `RECOJO`. No necesita DNI.
2. El pedido nace directamente en `COTIZADO` con costo de envío `S/ 0.00`. El cliente coordina por WhatsApp con Richard el lugar y la hora exacta.
3. Richard anota en el pedido el `punto_encuentro` y la `entrega_programada`. (El stock todavía no se descuenta; si el cliente quiere asegurar la prenda antes de la cita, puede yapear por adelantado y pasa a `PAGADO`).
4. En el punto de encuentro, Richard entrega las camisetas y el cliente **yapea (o paga en efectivo) frente a él**.
5. Desde su celular, Richard pulsa **«Confirmar pago y entregar»**: en una sola transacción el sistema pasa `COTIZADO` → `PAGADO` (descuenta el stock) → `ENTREGADO` y guarda la fecha de pago y de entrega.

## Flujo C – Venta presencial directa (registrada por Richard)
Cuando un cliente compra directo en persona o por WhatsApp sin haber llenado el carrito web:
1. Richard entra al panel en su celular → «Registrar venta presencial».
2. Elige las variantes y cantidades, el método de pago (`YAPE` o `EFECTIVO`) y opcionalmente el nombre y teléfono del cliente.
3. En una sola transacción el sistema crea el pedido con `origen = PRESENCIAL`, descuenta el stock y lo deja en `PAGADO` o `ENTREGADO`. Así ninguna camiseta vendida queda fuera del control de stock ni del reporte de ventas.

## Estados (valores en código y en base de datos en español)
| Código | Etiqueta | Significado |
|---|---|---|
| `NUEVO` | Nuevo | Pedido recibido, falta cotizar el envío |
| `COTIZADO` | Cotizado | Total final definido; esperando pago o cita de entrega |
| `PAGADO` | Pago confirmado | Pago verificado por Richard; stock descontado |
| `ENVIADO` | Enviado | Entregado a la agencia o al delivery |
| `ENTREGADO` | Entregado | El cliente recibió en mano o en agencia |
| `CANCELADO` | Cancelado | El cliente desistió, no pagó o no asistió a la cita |
| `RECHAZADO` | Rechazado | Richard no acepta el pedido (sin stock, datos inválidos) |

## Transiciones permitidas
| Desde | Hacia | Quién | Efecto |
|---|---|---|---|
| `NUEVO` | `COTIZADO` | Richard | Guarda el costo de envío y recalcula el total |
| `NUEVO` | `CANCELADO` / `RECHAZADO` | Richard | Sin efecto en stock |
| `COTIZADO` | `PAGADO` | Richard | Valida stock, crea movimientos `VENTA`, descuenta stock |
| `COTIZADO` | `NUEVO` | Richard | Para corregir la cotización |
| `COTIZADO` | `CANCELADO` / `RECHAZADO` | Richard | Sin efecto en stock |
| `PAGADO` | `ENVIADO` | Richard | En `AGENCIA`, exige datos de envío completos |
| `PAGADO` | `ENTREGADO` | Richard | Entrega en mano (`PUNTO_ENCUENTRO`, `RECOJO` o venta `PRESENCIAL`), sin pasar por agencia |
| `PAGADO` | `CANCELADO` / `RECHAZADO` | Richard | Devuelve stock con movimiento `DEVOLUCION` |
| `ENVIADO` | `ENTREGADO` | Richard | — |
| `ENVIADO` | `CANCELADO` | Richard | Devuelve stock solo si se confirma la devolución física |

> **Acción rápida en el panel («Confirmar pago y entregar»):** ejecuta `COTIZADO` → `PAGADO` y enseguida `PAGADO` → `ENTREGADO` dentro de la misma transacción, dejando ambos pasos registrados en `TBL_LPEDIDO_ESTADO`.

Cualquier otra transición se rechaza con un error claro. Toda transición queda en el historial (quién, cuándo, de qué estado a cuál, nota opcional).

## Reglas
- Un pedido con ítems nunca queda sin ítems; no se editan precios de ítems ya creados.
- Cambiar la cotización después de `COTIZADO` obliga a volver a `NUEVO`.
- Confirmar el pago es atómico: o se descuenta todo el stock del pedido o nada.
- La página pública del pedido solo muestra: ítems, total, modalidad de entrega, estado, y el QR de pago cuando el estado es `COTIZADO`. Nunca muestra el DNI completo ni la clave de recojo.
