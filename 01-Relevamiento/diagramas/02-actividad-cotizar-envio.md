# 02 – Diagrama de actividades: cotizar el envío

El delivery lo paga el cliente y lo cotiza Richard según la agencia o el distrito. Los pedidos de `PUNTO_ENCUENTRO` y `RECOJO` nacen ya en `COTIZADO` con envío `S/ 0.00`.

```mermaid
flowchart TD
  INI(("Inicio: pedido recibido")) --> a0{"¿Tipo de entrega?"}
  a0 -- "PUNTO_ENCUENTRO o RECOJO" --> a5["Nace directamente en COTIZADO<br/>con costo_envio = S/ 0.00"]
  a0 -- "AGENCIA o DELIVERY_LIMA" --> a1["Pedido en NUEVO:<br/>Richard lo abre en el panel"]
  a1 --> a2{"Modalidad"}
  a2 -- "AGENCIA (provincia)" --> a3["Consultar tarifa a Shalom u Olva<br/>según ciudad y referencia"]
  a2 -- "DELIVERY_LIMA" --> a4["Consultar costo de delivery en Lima"]
  a3 --> a6["Ingresar costo_envio"]
  a4 --> a6
  a6 --> a7["Sistema guarda costo_envio y recalcula<br/>total = subtotal + costo_envio"]
  a7 --> a8["Estado COTIZADO"]
  a5 --> a9["Avisar o coordinar con el cliente por WhatsApp"]
  a8 --> a9
  a9 --> a10{"¿Hay que corregir la cotización?"}
  a10 -- "Sí" --> a11["Volver a NUEVO (obligatorio para cambiar el costo)"]
  a11 --> a1
  a10 -- "No" --> FIN(("Fin: esperando pago o cita de entrega"))
```

## Notas
- Cambiar la cotización después de `COTIZADO` obliga a volver a `NUEVO`.
