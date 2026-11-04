# 04 – Diagrama de actividades: despacho y registro del envío por agencia

Aplica a los pedidos con `tipo_entrega = AGENCIA`. Richard entrega el paquete en Shalom u Olva y registra los datos para el cliente.

```mermaid
flowchart TD
  INI(("Inicio: pedido en PAGADO (AGENCIA)")) --> d1["Richard prepara y lleva el paquete a la agencia (Shalom u Olva)"]
  d1 --> d2["Obtiene número de orden, clave de recojo de 4 dígitos y boleta"]
  d2 --> d3["Registra el envío en el panel (TBL_TENVIO):<br/>agencia, numero_orden_agencia, clave_recojo,<br/>imagen_boleta, costo_flete y quien_paga"]
  d3 --> d4{"¿Datos de envío completos?"}
  d4 -- "No" --> d5["El sistema rechaza el cambio e indica qué falta"]
  d5 --> d3
  d4 -- "Sí" --> d6["Estado ENVIADO y registro en TBL_LPEDIDO_ESTADO"]
  d6 --> d7["El botón arma el mensaje de WhatsApp:<br/>número de orden, clave y cómo seguir el envío"]
  d7 --> d8["Richard envía el mensaje al cliente"]
  d8 --> d9["El cliente sigue su envío en la app de la agencia y recoge"]
  d9 --> d10{"¿Richard marca Entregado?"}
  d10 -- "Sí (opcional)" --> d11["Estado ENTREGADO"]
  d10 -- "No" --> FIN(("Fin: queda ENVIADO"))
  d11 --> FIN
```

## Notas
- La **clave de recojo** y el **DNI** son datos privados: nunca en URLs, logs ni páginas públicas.
- La foto de la boleta va a un bucket privado.
- Quién pagó el flete (`quien_paga`): `CLIENTE_ADELANTADO`, `CLIENTE_EN_DESTINO` o `RICHARD_ADELANTO`.
