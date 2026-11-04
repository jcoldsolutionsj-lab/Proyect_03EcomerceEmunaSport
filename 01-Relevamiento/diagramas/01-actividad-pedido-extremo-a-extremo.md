# 01 – Diagrama de actividades: pedido de punta a punta

Calles (swimlanes): Cliente, Sistema, Richard. Entre paréntesis, el estado del pedido. Fuente: `03-flujo-pedidos-estados.md`.

```mermaid
flowchart TD
  INI(("Inicio")) --> c1

  subgraph CLI["Cliente (celular)"]
    c1["Ver catálogo y elegir talla y cantidad"]
    c2["Agregar al carrito"]
    c3["Completar datos y elegir entrega"]
    c4["Enviar pedido (sin pagar)"]
    c5["Abrir página del pedido:<br/>total final, QR de Yape, titular y número"]
    c6["Pagar por Yape y enviar voucher por WhatsApp"]
    c7["Seguir el envío en la app de la agencia"]
  end

  subgraph SIS["Sistema"]
    s1["Validar datos (DNI 8 dígitos, teléfono 9 dígitos)<br/>y recalcular precios en el servidor"]
    s2["Crear pedido con código no adivinable<br/>y copias de nombre, talla y precio"]
    s3{"¿Entrega por recojo?"}
    s4["Estado NEW (falta cotizar)"]
    s5["Estado QUOTED con envío S/ 0"]
    s6["Mostrar página del pedido, PDF y botón de WhatsApp"]
    s7["Descontar stock en una transacción<br/>y estado PAID"]
    s8["Estado SHIPPED con datos de envío"]
  end

  subgraph RIC["Richard (admin)"]
    r1["Abrir pedido NEW en el admin"]
    r2["Consultar flete a la agencia<br/>e ingresar costo"]
    r3["Estado QUOTED y avisar al cliente<br/>con botón de WhatsApp"]
    r4["Revisar voucher recibido"]
    r5{"¿Pago válido?"}
    r6["Confirmar pago"]
    r7["Despachar en la agencia<br/>y registrar envío"]
    r8["Marcar Entregado (opcional)"]
    r9["Cancelar o rechazar pedido"]
  end

  c1 --> c2 --> c3 --> c4 --> s1 --> s2 --> s3
  s3 -- "Sí" --> s5
  s3 -- "No (agencia o Lima)" --> s4
  s4 --> r1 --> r2 --> r3
  s5 --> s6
  r3 --> s6
  s6 --> c5 --> c6 --> r4 --> r5
  r5 -- "Sí" --> r6 --> s7 --> r7 --> s8 --> c7 --> r8 --> FIN(("Fin"))
  r5 -- "No" --> r9 --> FIN
```

## Notas
- El stock **solo** se descuenta al confirmar el pago (ver `03-actividad-confirmar-pago.md`).
- Si el cliente desconfía de pagar así, sigue por WhatsApp con el PDF del pedido.
- La cotización, el pago y el despacho los registra siempre Richard.
