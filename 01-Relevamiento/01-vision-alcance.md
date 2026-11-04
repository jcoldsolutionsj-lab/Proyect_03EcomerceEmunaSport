# 01 – Visión y alcance

## Contexto
Richard es dueño de Emuná Sport («Estilo deportivo») y vende camisetas por WhatsApp. Hoy comparte los precios en PDFs pesados que obligan al cliente a deslizar mucho. Richard ya tiene clientes y vende también a provincias, enviando por las agencias Shalom y Olva.

## Objetivo
Reemplazar el PDF por una web donde el cliente vea el catálogo, revise el stock por talla, arme su pedido, vea el total y pague por Yape, y donde Richard gestione productos, stock, pedidos y envíos desde un panel.

## Usuarios
- **Cliente:** entra desde el celular, compra sin registrarse.
- **Richard (dueño):** administra catálogo, stock, pedidos y envíos. Debe ver rápido qué se vendió y qué no.
- **Jonathan Vera (responsable del sistema):** desarrollo, mantenimiento y acceso técnico completo.

## Alcance del primer alcance (piloto funcional)
Dentro:
- Catálogo de camisetas con variantes por talla y stock por talla.
- Precio por unidad y precio por mayor (configurable).
- Carrito y pedido sin cuenta (invitado) con los datos de envío de Shalom.
- Página del pedido con código, detalle y PDF descargable.
- Botón de WhatsApp a Richard con el detalle.
- Pago por Yape: QR, titular visible y número copiable.
- Panel (admin de Django) para productos, stock, pedidos, envíos y ajustes.
- Historial de stock y de cambios de cada pedido.
- Dashboard simple para decidir.

Fuera por ahora (no construir todavía):
- Pago en línea con pasarela o verificación automática del pago.
- Cuentas de cliente, login de clientes.
- Facturación electrónica.
- App móvil (pero la API debe quedar lista).
- Mensajes automáticos por WhatsApp.
- Subida de voucher en la web (en la versión 1 el cliente lo manda por WhatsApp).

## Criterio de éxito del piloto
Richard puede, sin ayuda: cargar un producto con tallas y stock, recibir un pedido, cotizar el envío, confirmar el pago, despachar y ver el historial. Un cliente puede comprar desde su celular en menos de 3 minutos.
