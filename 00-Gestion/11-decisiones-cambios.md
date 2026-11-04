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

## Decisiones técnicas (2026-11-03)
- Un solo repositorio git en la raíz del proyecto (documentos y código); el remoto será privado.
- Estándar de base de datos adaptado del manual «Estándares Área de Desarrollo» (doc 12): tablas `TBL_`, columnas con sigla de 3 letras y letra de tipo, sin cursores, scripts con cabecera y versionado `X.Y.Z` (primera versión en producción: 1.1.0).
- La lógica de negocio no va en procedimientos almacenados; triggers solo para proteger invariantes.
- Diagramas del negocio en Mermaid dentro de `01-Relevamiento/diagramas/`.

## Pendientes técnicos (Jonathan)
1. Nombres de la base en MAYÚSCULAS obligan a usar comillas en PostgreSQL. Confirmar si se mantiene el estándar tal cual o se usan minúsculas.
2. Nombres físicos en inglés (propuesto) o en español.
3. Renombrar las llaves PK y FK según el estándar mediante migración, o aceptar los nombres automáticos de Django.
4. Nombre de la base local: `TIENDA_WEB_EMUNA_SPORT` (propuesto).
5. Revisar `03-Diseno-Tecnico/05-arquitectura-stack.md`: se reconstruyó parcialmente tras un borrado accidental.
6. Crear el remoto privado y hacer el primer commit.

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
| 2026-11-03 | Reorganización de carpetas (00 a 06) y memoria de continuidad (ESTADO-ACTUAL y BITACORA-sesiones) | Índice 00, reglas de la IA, doc 05, doc 06 |
| 2026-11-03 | Git iniciado en la raíz; LEEME.txt en cada carpeta; diagramas UML en 01-Relevamiento/diagramas | Estándar de estructura, índice 00, reglas de la IA |
| 2026-11-03 | Estándar de base de datos (doc 12), diccionario de datos y modelo ER; se agrega unit_price a Product | Doc 04, doc 05, doc 12, base-datos/ |
| 2026-11-03 | Reconstrucción de los docs 04 y 05, estándar de estructura y reglas de la IA tras borrado accidental (doc 05 parcial) | Doc 04, doc 05, ESTANDAR-ESTRUCTURA, reglas |
