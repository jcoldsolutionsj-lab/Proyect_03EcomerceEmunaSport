# 03 – Flujo de pedidos y estados

## Flujo completo
1. El cliente ve el catálogo, elige talla y cantidad (ve el stock) y agrega al carrito.
2. En el checkout ingresa sus datos y elige la entrega. Envía el pedido (sin pagar todavía).
3. El sistema crea el pedido con un **código no adivinable** (ej. `EMU-7K3Q9X`) y muestra la página del pedido con el detalle, el PDF y el botón de WhatsApp.
4. Richard abre el pedido en el admin. Si hay envío, consulta a la agencia y **ingresa el costo del flete**; el pedido pasa a «Cotizado». Si es recojo, el pedido nace ya cotizado con envío S/ 0.
5. Richard avisa al cliente con un botón de WhatsApp que lleva el enlace a la página del pedido.
6. El cliente abre su página, ve el total final, el QR de Yape, el titular y el número. Paga y envía el voucher por WhatsApp.
7. Richard revisa el pago y pasa el pedido a «Pago confirmado». **Aquí se descuenta el stock.**
8. Richard despacha en la agencia y registra el envío (número de orden, clave, boleta, flete). El pedido pasa a «Enviado» y usa el botón de WhatsApp con los datos al cliente.
9. El cliente sigue su envío en la app de la agencia. Cuando recoge, Richard puede marcar «Entregado» (opcional).

## Estados (valores en código en inglés)
| Código | Etiqueta | Significado |
|---|---|---|
| `NEW` | Nuevo | Pedido recibido, falta cotizar el envío |
| `QUOTED` | Cotizado | Total final definido, esperando pago |
| `PAID` | Pago confirmado | Pago verificado por Richard; stock descontado |
| `SHIPPED` | Enviado | Entregado a la agencia, con datos de envío |
| `DELIVERED` | Entregado | El cliente recibió (marcado a mano) |
| `CANCELLED` | Cancelado | El cliente desistió o no pagó |
| `REJECTED` | Rechazado | Richard no acepta el pedido (sin stock, datos inválidos) |

## Transiciones permitidas
| Desde | Hacia | Quién | Efecto |
|---|---|---|---|
| `NEW` | `QUOTED` | Richard | Guarda el costo de envío y recalcula el total |
| `NEW` | `CANCELLED` / `REJECTED` | Richard | Sin efecto en stock |
| `QUOTED` | `PAID` | Richard | Valida stock, crea movimientos de venta, descuenta |
| `QUOTED` | `NEW` | Richard | Para corregir la cotización |
| `QUOTED` | `CANCELLED` / `REJECTED` | Richard | Sin efecto en stock |
| `PAID` | `SHIPPED` | Richard | Exige datos de envío completos |
| `PAID` | `CANCELLED` / `REJECTED` | Richard | Devuelve stock con movimiento de devolución |
| `SHIPPED` | `DELIVERED` | Richard | — |
| `SHIPPED` | `CANCELLED` | Richard | Devuelve stock solo si se confirma la devolución física |

Cualquier otra transición se rechaza con un error claro. Toda transición queda en el historial (quién, cuándo, de qué estado a cuál, nota opcional).

## Reglas
- Un pedido con ítems nunca queda sin ítems; no se editan precios de ítems ya creados.
- Cambiar la cotización después de `QUOTED` obliga a volver a `NEW`.
- Confirmar el pago es atómico: o se descuenta todo el stock del pedido o nada.
- La página pública del pedido solo muestra: ítems, total, estado, y el QR de pago cuando el estado es `QUOTED`. Nunca muestra el DNI completo ni la clave de recojo salvo que se decida en una fase posterior.
