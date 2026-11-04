# 07 – Diagrama de estados del pedido

Transiciones permitidas. Cualquier otra se rechaza. Todas las ejecuta `pedidos.servicios.cambiar_estado()` y quedan en `TBL_LPEDIDO_ESTADO`. Fuente: `03-flujo-pedidos-estados.md`.

```mermaid
stateDiagram-v2
  [*] --> NUEVO : cliente envía pedido (AGENCIA o DELIVERY_LIMA)
  [*] --> COTIZADO : cliente envía pedido (PUNTO_ENCUENTRO o RECOJO, envío S/ 0)

  NUEVO : NUEVO - Falta cotizar envío
  COTIZADO : COTIZADO - Total definido
  PAGADO : PAGADO - Pago confirmado y stock descontado
  ENVIADO : ENVIADO - En agencia o delivery
  ENTREGADO : ENTREGADO - Recibido por el cliente
  CANCELADO : CANCELADO - Desistió o no pagó
  RECHAZADO : RECHAZADO - No aceptado por Richard

  NUEVO --> COTIZADO : Richard cotiza el envío
  NUEVO --> CANCELADO : sin efecto en stock
  NUEVO --> RECHAZADO : sin efecto en stock

  COTIZADO --> NUEVO : corregir cotización
  COTIZADO --> PAGADO : confirma pago y descuenta stock (VENTA)
  COTIZADO --> CANCELADO : sin efecto en stock
  COTIZADO --> RECHAZADO : sin efecto en stock

  PAGADO --> ENVIADO : despacho por agencia o delivery
  PAGADO --> ENTREGADO : entrega en mano (punto de encuentro, recojo o presencial)
  PAGADO --> CANCELADO : devuelve stock (DEVOLUCION)
  PAGADO --> RECHAZADO : devuelve stock (DEVOLUCION)

  ENVIADO --> ENTREGADO : recepción confirmada
  ENVIADO --> CANCELADO : devuelve stock si hay devolución física

  ENTREGADO --> [*]
  CANCELADO --> [*]
  RECHAZADO --> [*]
```

## Notas
- La acción rápida **«Confirmar pago y entregar»** (para entregas personales en Lima) ejecuta `COTIZADO` → `PAGADO` → `ENTREGADO` dentro de una sola transacción.
- Una venta presencial directa (`origen = PRESENCIAL`) nace y pasa en el mismo acto a `PAGADO` o `ENTREGADO`.
