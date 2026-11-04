# 05 – Diagrama de actividades: cancelar o rechazar un pedido

Cancelar: el cliente desistió o no pagó. Rechazar: Richard no acepta el pedido (sin stock, datos inválidos). El efecto sobre el stock depende del estado en que está el pedido.

```mermaid
flowchart TD
  INI(("Inicio")) --> e1["Richard elige Cancelar o Rechazar<br/>e indica una nota opcional"]
  e1 --> e2{"Estado actual del pedido"}

  e2 -- "NEW o QUOTED" --> e3["Sin efecto en el stock<br/>(aún no se descontó)"]
  e2 -- "PAID" --> e4["Devolver stock:<br/>crear StockMovement RETURN por cada ítem<br/>(transacción atómica)"]
  e2 -- "SHIPPED" --> e5{"Solo se permite CANCELLED.<br/>¿Se confirmó la devolución física?"}
  e2 -- "DELIVERED" --> e8["Transición no permitida:<br/>el sistema muestra un error claro"]

  e5 -- "Sí" --> e4
  e5 -- "No" --> e6["Cancelar sin devolver stock"]

  e3 --> e7["Cambiar estado a CANCELLED o REJECTED"]
  e4 --> e7
  e6 --> e7
  e7 --> e9["Registrar en el historial: quién, cuándo, de y a qué estado"]
  e9 --> FIN(("Fin"))
  e8 --> FIN
```

## Notas
- `SHIPPED` solo puede ir a `CANCELLED`, no a `REJECTED`.
- Toda transición queda en el historial; cualquier otra transición se rechaza con un error claro.
