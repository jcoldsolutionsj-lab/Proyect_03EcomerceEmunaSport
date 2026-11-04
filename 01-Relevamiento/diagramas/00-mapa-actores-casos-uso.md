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
    U3["Enviar pedido (checkout)"]
    U4["Ver página del pedido, PDF y QR de pago"]
  end

  subgraph ADM["Panel de administración"]
    A1["Gestionar catálogo<br/>(productos, variantes, precios, fotos)"]
    A2["Ajustar y consultar stock"]
    A3["Cotizar envío"]
    A4["Confirmar pago"]
    A5["Registrar envío y avisar por WhatsApp"]
    A6["Cancelar o rechazar pedido"]
    A7["Ver dashboard y alertas"]
    A8["Configurar tienda y métodos de pago"]
    A9["Administrar usuarios y configuración técnica"]
  end

  CLI --> U1 & U2 & U3 & U4
  RIC --> A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8
  JON --> A9
  JON -.->|"acceso total"| A1
  AGE -.->|"transporta el pedido; el cliente lo sigue en su app"| A5
```

## Notas
- El cliente **no se registra**: compra con nombre, DNI y teléfono.
- Richard hace todo lo operativo; Jonathan además ve la configuración técnica.
- Fuentes: `02-reglas-negocio.md` (Roles) y `03-flujo-pedidos-estados.md`.
