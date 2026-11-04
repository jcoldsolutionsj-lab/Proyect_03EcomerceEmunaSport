# 03 – Diagrama de actividades: confirmar pago y descontar stock

Es el corazón del negocio. La operación es **atómica**: o se descuenta todo el stock del pedido o nada. La ejecuta `orders.services.change_status()`.

```mermaid
flowchart TD
  INI(("Inicio: pedido en QUOTED")) --> b1["Richard revisa el voucher que envió el cliente por WhatsApp"]
  b1 --> b2{"¿Pago válido y por el total correcto?"}
  b2 -- "No" --> b3["Pedir corrección al cliente<br/>o cancelar / rechazar"]
  b3 --> FIN1(("Fin sin cambios de stock"))
  b2 -- "Sí" --> b4["Richard pulsa Confirmar pago"]

  subgraph TX["Sistema: una sola transacción"]
    t1["Iniciar transacción"]
    t2["Bloquear las variantes del pedido<br/>(select_for_update)"]
    t3{"¿Stock suficiente<br/>para cada ítem?"}
    t4["Crear un StockMovement SALE negativo por ítem<br/>y actualizar el stock de la variante"]
    t5["Cambiar estado a PAID y registrar en el historial<br/>(quién, cuándo, de y a qué estado)"]
    t6["Confirmar transacción (commit)"]
    t7["Deshacer todo (rollback)"]
  end

  b4 --> t1 --> t2 --> t3
  t3 -- "Sí" --> t4 --> t5 --> t6 --> FIN2(("Fin: pedido PAID, stock descontado"))
  t3 -- "No" --> t7 --> b5["Avisar a Richard qué ítem no tiene stock"]
  b5 --> b6{"Decisión de Richard"}
  b6 -- "Ajustar el pedido" --> b7["Volver a NEW, corregir y cotizar de nuevo"]
  b6 -- "Rechazar" --> b8["Estado REJECTED (sin efecto en stock)"]
  b7 --> FIN3(("Fin"))
  b8 --> FIN3
```

## Notas
- El stock nunca se edita a mano: solo cambia por un `StockMovement` creado desde un service.
- Invariante: `Variant.stock_quantity` es siempre la suma de sus movimientos y nunca baja de 0.
- Si el pago se confirmó, el pedido tiene un movimiento `SALE` por cada ítem.
