# 08 – Diagrama de actividades: entrega en punto de encuentro en Lima y venta presencial

En Lima lo más habitual es que Richard se cite con el cliente en un lugar acordado, le deje la mercadería y ahí mismo reciba el Yape (o efectivo). Este diagrama cubre los dos caminos posibles.

```mermaid
flowchart TD
  INI(("Inicio")) --> M{"¿Cómo se originó el pedido?"}

  subgraph C1["Camino 1: el cliente armó el pedido en la web (origen = WEB)"]
    w1["Cliente elige PUNTO_ENCUENTRO en el checkout<br/>e indica lugar sugerido, nombre y teléfono"]
    w2["El pedido nace en COTIZADO con costo_envio = S/ 0.00"]
    w3["Cliente y Richard coordinan por WhatsApp<br/>el lugar y la hora exacta"]
    w4["Richard anota en el pedido:<br/>punto_encuentro y entrega_programada"]
  end

  subgraph C2["Camino 2: venta cerrada directo por WhatsApp o en persona (origen = PRESENCIAL)"]
    p1["Richard abre en su celular:<br/>Registrar venta presencial"]
    p2["Selecciona variantes, cantidades,<br/>punto_encuentro y datos opcionales del cliente"]
  end

  M -- "Desde la web" --> w1 --> w2 --> w3 --> w4 --> E1
  M -- "Directo con Richard" --> p1 --> p2 --> E1

  subgraph ENC["En el punto de encuentro en Lima"]
    E1["Richard se encuentra con el cliente<br/>y le entrega las camisetas"]
    E2{"¿El cliente paga en el acto?"}
    E3["Cliente yapea (o paga en efectivo) frente a Richard"]
    E4["Richard verifica el Yape en su celular y pulsa:<br/>Confirmar pago y entregar (método YAPE o EFECTIVO)"]
    E5["El cliente no asiste o desiste:<br/>Richard marca CANCELADO (sin efecto en stock)"]
  end

  subgraph TX["Sistema: transacción atómica"]
    t1["Bloquear variantes con select_for_update<br/>y verificar stock disponible"]
    t2["Crear MovimientoStock VENTA por cada ítem<br/>y descontar cantidad_stock"]
    t3["Registrar COTIZADO → PAGADO → ENTREGADO<br/>con fecha_pagado y fecha_entregado"]
  end

  E1 --> E2
  E2 -- "Sí" --> E3 --> E4 --> t1 --> t2 --> t3 --> FIN1(("Fin: pedido ENTREGADO y stock al día"))
  E2 -- "No" --> E5 --> FIN2(("Fin: pedido CANCELADO"))
```

## Notas
- Si el cliente quiere **asegurar la prenda antes de la cita**, puede yapear por adelantado: Richard confirma el pago (`COTIZADO` → `PAGADO`, ya se descuenta el stock) y cuando se ven en el punto de encuentro solo pulsa «Marcar entregado» (`PAGADO` → `ENTREGADO`).
- Si el cliente cancela después de haber pagado por adelantado, pasar de `PAGADO` a `CANCELADO` devuelve el stock automáticamente con un movimiento `DEVOLUCION`.
