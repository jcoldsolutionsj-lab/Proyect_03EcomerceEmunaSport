# 05 – Diagrama de actividades: cancelar o rechazar un pedido

Cancelar (`CANCELADO`): el cliente desistió, no pagó o no asistió a la cita. Rechazar (`RECHAZADO`): Richard no acepta el pedido (sin stock, datos inválidos). El efecto sobre el stock depende del estado actual.

```mermaid
flowchart TD
  INI(("Inicio")) --> e1["Richard elige Cancelar o Rechazar<br/>e indica una nota opcional"]
  e1 --> e2{"Estado actual del pedido"}

  e2 -- "NUEVO o COTIZADO" --> e3["Sin efecto en el stock<br/>(aún no se descontó)"]
  e2 -- "PAGADO" --> e4["Devolver stock:<br/>crear MovimientoStock tipo DEVOLUCION por cada ítem<br/>(transacción atómica)"]
  e2 -- "ENVIADO" --> e5{"Solo se permite CANCELADO.<br/>¿Se confirmó la devolución física?"}
  e2 -- "ENTREGADO" --> e8["Transición no permitida:<br/>el sistema muestra un error claro"]

  e5 -- "Sí" --> e4
  e5 -- "No" --> e6["Cancelar sin devolver stock"]

  e3 --> e7["Cambiar estado a CANCELADO o RECHAZADO<br/>y guardar fecha_cierre"]
  e4 --> e7
  e6 --> e7
  e7 --> e9["Registrar en TBL_LPEDIDO_ESTADO: quién, cuándo, de y a qué estado"]
  e9 --> FIN(("Fin"))
  e8 --> FIN
```

## Notas
- `ENVIADO` solo puede ir a `CANCELADO`, no a `RECHAZADO`.
- Toda transición queda en el historial; cualquier otra transición se rechaza con un error claro.
