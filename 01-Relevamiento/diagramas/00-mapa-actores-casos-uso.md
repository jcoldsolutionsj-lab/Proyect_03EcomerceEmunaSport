# 00 – Mapa de actores y casos de uso

Quién hace qué en el sistema. Es la vista más general; los demás diagramas bajan al detalle.

```mermaid
flowchart LR
  CLI(["Cliente<br/>(compra desde el celular)"])
  RIC(["Richard<br/>(dueño, grupo Dueño)"])
  JON(["Jonathan<br/>(superusuario)"])
  AGE(["Agencia<br/>(Shalom / Olva)"])

  subgraph WEB["Web pública"]
    U1["Ver catálogo y detalle de producto"]
    U2["Armar carrito"]
    U3["Enviar pedido (Agencia, Delivery Lima,<br/>Punto de encuentro o Recojo)"]
    U4["Ver página del pedido, PDF y QR de Yape"]
  end

  subgraph ADM["Panel de administración"]
    A1["Gestionar catálogo<br/>(productos, variantes, precios, fotos)"]
    A2["Ajustar y consultar stock"]
    A3["Cotizar envío (Agencia / Delivery Lima)"]
    A4["Confirmar pago (previo o en punto de encuentro)"]
    A5["Entregar en punto de encuentro en Lima<br/>y cobrar Yape/efectivo ahí mismo"]
    A6["Registrar venta presencial directa"]
    A7["Registrar envío por agencia y avisar por WhatsApp"]
    A8["Cancelar o rechazar pedido"]
    A9["Ver tablero y alertas"]
    A10["Configurar tienda y métodos de pago"]
    A11["Administrar usuarios y configuración técnica"]
  end

  CLI --> U1 & U2 & U3 & U4
  RIC --> A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10
  JON --> A11
  JON -.->|"acceso total"| A1
  AGE -.->|"transporta el pedido; el cliente lo sigue en su app"| A7
```

## Notas
- El cliente **no se registra**: compra con nombre, teléfono y (si es envío por agencia) DNI.
- En Lima lo más frecuente es que Richard se cite con el cliente en un punto de encuentro, entregue la mercadería y reciba el Yape en ese momento (`A5`).
- Fuentes: `02-reglas-negocio.md` y `03-flujo-pedidos-estados.md`.
