# 11 – Decisiones y cambios

Bitácora viva. Cuando una regla cambie, se edita el documento correspondiente (02, 03, 04…) y se agrega una línea aquí con la fecha.

## Decisiones tomadas (2026-11-03)
- Tienda tipo e-commerce con web pública para clientes y panel para Richard (admin de Django).
- Cliente compra sin registrarse.
- Variantes por talla con stock por talla; modelo y marca opcionales y apagados por defecto.
- Precio por unidad y por mayor, configurable por producto.
- Stock se descuenta cuando Richard confirma el pago.
- Delivery cotizado por Richard (Shalom/Olva) y sumado al total; el cliente paga antes de que Richard despache.
- Pago inicial por Yape, con titular visible, número copiable y voucher por WhatsApp.
- Si el cliente desconfía, sigue por WhatsApp con el PDF.
- Cuenta de Cloudflare a nombre de Richard; fotos en bucket compatible con S3 (calidad de detalle ~900 px en WebP, miniatura ~400 px, original privado).
- Piloto en Render; producción con PostgreSQL persistente.
- Convención: código en inglés, textos visibles y comentarios en español (modificable).

## Pendientes por confirmar con Richard
1. Cómo se aplica el precio por mayor: por producto sumando tallas (propuesto) o por pedido completo.
2. Quién paga el flete en la agencia: si siempre el cliente por adelantado a Richard o a veces en destino (el sistema ya lo permite con un campo).
3. Si las camisetas son diseños propios o genéricos, para definir cómo se nombran las categorías y evitar mostrar marcas o clubes sin autorización.
4. Confirmar que el titular que muestra el QR de Yape coincide con el nombre del dueño del negocio, para que el cliente confíe.
5. Cuánto tiempo conservar datos de pedidos antiguos (DNI y teléfono).
6. Si Richard emite comprobantes electrónicos (queda fuera del piloto).
7. Número de fotos por producto y orden de carga inicial.

## Registro de cambios
| Fecha | Cambio | Documentos afectados |
|---|---|---|
| 2026-11-03 | Versión inicial de los documentos | Todos |
