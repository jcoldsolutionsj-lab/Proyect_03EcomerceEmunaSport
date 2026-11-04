# 04 – Diagrama de actividades: despacho y registro del envío

Richard entrega los paquetes a la agencia y registra el envío. El cliente luego lo sigue en la app de la agencia.

```mermaid
flowchart TD
  INI(("Inicio: pedido en PAID")) --> d1["Richard prepara y lleva el paquete a la agencia (Shalom u Olva)"]
  d1 --> d2["Obtiene número de orden, clave de 4 dígitos y boleta"]
  d2 --> d3["Registra el envío en el admin:<br/>agencia, número de orden, clave, foto de boleta,<br/>costo del flete y quién pagó el flete"]
  d3 --> d4{"¿Datos de envío completos?"}
  d4 -- "No" --> d5["El sistema rechaza el cambio y indica qué falta"]
  d5 --> d3
  d4 -- "Sí" --> d6["Estado SHIPPED y registro en el historial"]
  d6 --> d7["El botón arma el mensaje de WhatsApp:<br/>número de orden, clave y cómo seguir el envío"]
  d7 --> d8["Richard envía el mensaje al cliente"]
  d8 --> d9["El cliente sigue su envío en la app de la agencia"]
  d9 --> d10["El cliente recoge el paquete en la agencia"]
  d10 --> d11{"¿Richard marca Entregado?"}
  d11 -- "Sí (opcional)" --> d12["Estado DELIVERED"]
  d11 -- "No" --> FIN(("Fin: queda SHIPPED"))
  d12 --> FIN
```

## Notas
- La **clave de recojo** y el **DNI** son datos privados: nunca en URLs, logs ni páginas públicas.
- La foto de la boleta va a un bucket privado.
- Quién pagó el flete es un campo (`CUSTOMER_PREPAID`, `CUSTOMER_AT_DEST`, `RICHARD_ADVANCED`). Si no lo pagó Richard, se marca como informativo.
