# 02 – Diagrama de actividades: cotizar el envío

El delivery lo paga el cliente y lo cotiza Richard según la agencia y el destino.

```mermaid
flowchart TD
  INI(("Inicio: pedido en NEW")) --> a1["Richard abre el pedido en el admin"]
  a1 --> a2{"Tipo de entrega"}
  a2 -- "AGENCY (provincia)" --> a3["Consultar tarifa a Shalom u Olva<br/>según ciudad y referencia de destino"]
  a2 -- "LIMA" --> a4["Consultar costo de delivery en Lima"]
  a2 -- "PICKUP (recojo)" --> a5["Costo de envío = S/ 0"]
  a3 --> a6["Ingresar costo de envío"]
  a4 --> a6
  a5 --> a7
  a6 --> a7["Sistema guarda el costo y recalcula<br/>total = subtotal + envío"]
  a7 --> a8["Estado QUOTED"]
  a8 --> a9["Richard avisa al cliente con el botón de WhatsApp<br/>(enlace a la página del pedido)"]
  a9 --> a10{"¿Hay que corregir la cotización?"}
  a10 -- "Sí" --> a11["Volver a NEW (obligatorio para cambiar el costo)"]
  a11 --> a1
  a10 -- "No" --> FIN(("Fin: esperando pago"))
```

## Notas
- Un pedido de recojo nace ya en `QUOTED` con envío S/ 0 y no pasa por este flujo.
- Cambiar la cotización después de `QUOTED` obliga a volver a `NEW`.
