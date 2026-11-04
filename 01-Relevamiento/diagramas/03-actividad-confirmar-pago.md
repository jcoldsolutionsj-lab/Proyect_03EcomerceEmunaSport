# 03 – Diagrama de actividades: confirmar pago y descontar stock

Es el corazón del negocio. La operación es **atómica**: o se descuenta todo el stock del pedido o nada. La ejecuta `pedidos.servicios.cambiar_estado()`.

```mermaid
flowchart TD
  INI(("Inicio: pedido en COTIZADO")) --> b1["Richard verifica el pago:<br/>voucher por WhatsApp o Yape/efectivo en persona"]
  b1 --> b2{"¿Pago válido y por el total correcto?"}
  b2 -- "No" --> b3["Pedir corrección al cliente<br/>o cancelar / rechazar"]
  b3 --> FIN1(("Fin sin cambios de stock"))
  b2 -- "Sí" --> b4["Richard elige el método de pago (YAPE / EFECTIVO)<br/>y pulsa Confirmar pago"]

  subgraph TX["Sistema: una sola transacción (transaction.atomic)"]
    t1["Iniciar transacción"]
    t2["Bloquear las variantes del pedido<br/>(select_for_update)"]
    t3{"¿cantidad_stock suficiente<br/>para cada ítem?"}
    t4["Crear un MovimientoStock tipo VENTA negativo por ítem<br/>y actualizar cantidad_stock de la variante"]
    t5["Cambiar estado a PAGADO, guardar metodo_pago y fecha_pagado,<br/>y registrar en TBL_LPEDIDO_ESTADO"]
    t6["Confirmar transacción (commit)"]
    t7["Deshacer todo (rollback)"]
  end

  b4 --> t1 --> t2 --> t3
  t3 -- "Sí" --> t4 --> t5 --> t6 --> FIN2(("Fin: pedido PAGADO, stock descontado"))
  t3 -- "No" --> t7 --> b5["Avisar a Richard qué ítem no tiene stock"]
  b5 --> b6{"Decisión de Richard"}
  b6 -- "Ajustar el pedido" --> b7["Volver a NUEVO, corregir y cotizar de nuevo"]
  b6 -- "Rechazar" --> b8["Estado RECHAZADO (sin efecto en stock)"]
  b7 --> FIN3(("Fin"))
  b8 --> FIN3
```

## Notas
- El stock nunca se edita a mano: solo cambia por un `MovimientoStock` creado desde un servicio.
- Invariante: `Variante.cantidad_stock` es siempre la suma de sus movimientos y nunca baja de 0.
- En entregas en punto de encuentro en Lima, la acción «Confirmar pago y entregar» ejecuta este bloque y enseguida pasa a `ENTREGADO` en la misma transacción.
