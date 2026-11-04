# 01 – Diagrama de actividades: pedido de punta a punta

Calles (swimlanes): Cliente, Sistema, Richard. Contempla tanto el envío a provincia/delivery como la cita en punto de encuentro en Lima (donde el cliente yapea al recibir). Fuente: `03-flujo-pedidos-estados.md`.

```mermaid
flowchart TD
  INI(("Inicio")) --> c1

  subgraph CLI["Cliente (celular)"]
    c1["Ver catálogo y elegir talla y cantidad"]
    c2["Agregar al carrito"]
    c3["Completar datos y elegir modalidad:<br/>AGENCIA, DELIVERY_LIMA, PUNTO_ENCUENTRO o RECOJO"]
    c4["Enviar pedido (sin pagar aún)"]
    c5["Abrir página del pedido:<br/>total final, QR de Yape, titular y número"]
    c6["Pagar por Yape y enviar voucher por WhatsApp"]
    c7["Acudir al punto de encuentro en Lima,<br/>recibir prendas y yapear ahí mismo"]
    c8["Seguir el envío en la app de la agencia"]
  end

  subgraph SIS["Sistema"]
    s1["Validar datos y recalcular precios en el servidor"]
    s2["Crear pedido con código no adivinable<br/>y copias de nombre, talla y precio"]
    s3{"¿Modalidad de entrega?"}
    s4["Estado NUEVO (falta cotizar envío)"]
    s5["Estado COTIZADO con envío S/ 0.00"]
    s6["Mostrar página del pedido, PDF y botón de WhatsApp"]
    s7["Descontar stock en transacción<br/>y estado PAGADO"]
    s8["Estado ENVIADO con datos de agencia"]
    s9["Descontar stock y pasar<br/>COTIZADO → PAGADO → ENTREGADO"]
  end

  subgraph RIC["Richard (panel)"]
    r1["Abrir pedido NUEVO en el panel"]
    r2["Consultar tarifa e ingresar costo de envío"]
    r3["Estado COTIZADO y avisar al cliente por WhatsApp"]
    r4["Coordinar lugar y hora del punto de encuentro"]
    r5["Revisar voucher recibido"]
    r6{"¿Pago válido?"}
    r7["Confirmar pago"]
    r8["Despachar y registrar envío"]
    r9["Entregar en mano en el punto de encuentro,<br/>verificar Yape y pulsar Confirmar pago y entregar"]
    r10["Cancelar o rechazar pedido"]
  end

  c1 --> c2 --> c3 --> c4 --> s1 --> s2 --> s3
  s3 -- "AGENCIA o DELIVERY_LIMA" --> s4 --> r1 --> r2 --> r3 --> s6
  s3 -- "PUNTO_ENCUENTRO o RECOJO" --> s5 --> r4 --> c7 --> r9 --> s9 --> FIN(("Fin"))
  s6 --> c5 --> c6 --> r5 --> r6
  r6 -- "Sí" --> r7 --> s7 --> r8 --> s8 --> c8 --> FIN
  r6 -- "No" --> r10 --> FIN
```

## Notas
- El stock **solo** se descuenta cuando Richard confirma el pago (`s7` o `s9`).
- El detalle de la cita en Lima y la venta presencial directa está en `08-actividad-entrega-lima-y-venta-presencial.md`.
