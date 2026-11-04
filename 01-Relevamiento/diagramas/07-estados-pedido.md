# 07 – Diagrama de estados del pedido

Transiciones permitidas. Cualquier otra se rechaza. Todas las ejecuta `orders.services.change_status()` y quedan en el historial. Fuente: `03-flujo-pedidos-estados.md`.

```mermaid
stateDiagram-v2
  [*] --> NEW : cliente envía el pedido

  NEW : NEW - Nuevo
  QUOTED : QUOTED - Cotizado
  PAID : PAID - Pago confirmado
  SHIPPED : SHIPPED - Enviado
  DELIVERED : DELIVERED - Entregado
  CANCELLED : CANCELLED - Cancelado
  REJECTED : REJECTED - Rechazado

  NEW --> QUOTED : Richard cotiza el envío
  NEW --> CANCELLED : sin efecto en stock
  NEW --> REJECTED : sin efecto en stock

  QUOTED --> NEW : corregir cotización
  QUOTED --> PAID : confirma pago y descuenta stock
  QUOTED --> CANCELLED : sin efecto en stock
  QUOTED --> REJECTED : sin efecto en stock

  PAID --> SHIPPED : exige datos de envío completos
  PAID --> CANCELLED : devuelve stock
  PAID --> REJECTED : devuelve stock

  SHIPPED --> DELIVERED : marcado a mano (opcional)
  SHIPPED --> CANCELLED : devuelve stock si hay devolución física

  DELIVERED --> [*]
  CANCELLED --> [*]
  REJECTED --> [*]
```

## Notas
- Un pedido de recojo nace directamente en `QUOTED` con envío S/ 0.
- Un pedido en `PAID` o posterior tiene movimientos `SALE`; en `SHIPPED` tiene un `Shipment` completo.
