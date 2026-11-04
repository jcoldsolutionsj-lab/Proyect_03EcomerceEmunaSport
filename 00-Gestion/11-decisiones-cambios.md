# 11 – Decisiones y cambios

Bitácora viva. Cuando una regla cambie, se edita el documento correspondiente (02, 03, 04…) y se agrega una línea aquí con la fecha.

## Decisiones de negocio tomadas (2026-11-03)
- Tienda tipo e-commerce con web pública para clientes y panel para Richard (admin de Django).
- Cliente compra sin registrarse.
- Variantes por talla con stock por talla; modelo y marca opcionales y apagados por defecto.
- Precio por unidad y por mayor, configurable por producto.
- Stock se descuenta cuando Richard confirma el pago.
- **Modalidades de entrega y venta:**
  1. `AGENCIA` (provincia con Shalom u Olva): delivery cotizado por Richard y pagado por el cliente antes del despacho; exige DNI de 8 dígitos.
  2. `DELIVERY_LIMA`: delivery en Lima cotizado por Richard.
  3. `PUNTO_ENCUENTRO` (la modalidad más frecuente en Lima): Richard se cita con el cliente en un lugar acordado, le entrega la mercadería en mano y ahí mismo recibe el Yape (o efectivo). Nace en `COTIZADO` con envío `S/ 0.00` y se cierra con la acción rápida «Confirmar pago y entregar» (`COTIZADO` → `PAGADO` → `ENTREGADO`).
  4. `RECOJO`: recojo sin costo de envío (`S/ 0.00`).
  5. Venta directa `PRESENCIAL`: Richard registra en el panel ventas cerradas en persona o por WhatsApp para que ningún movimiento de stock quede fuera del sistema.
- Métodos de pago: `YAPE` (con titular visible, número copiable y QR), `EFECTIVO` (para entregas personales) y `PLIN` en fase posterior.
- Si el cliente desconfía, sigue por WhatsApp con el PDF.
- Cuenta de Cloudflare a nombre de Richard; fotos en bucket compatible con S3 (calidad de detalle ~900 px en WebP, miniatura ~400 px, original privado).
- Piloto en Render; producción con PostgreSQL persistente.

## Decisiones técnicas confirmadas por Jonathan (2026-11-03)
- **Todo el código propio va en español** (apps, clases, funciones, variables, campos, URLs y constantes de estado).
- **Docstring obligatorio de 5 líneas en cada función/método propio:** *Qué hace*, *Va hacia*, *Depende de*, *Cuándo usarla* y *Si no opera*.
- **Base de datos en MAYÚSCULAS y en español** siguiendo el estándar `TBL_` del manual (doc 12). Fuente única: `03-Diseno-Tecnico/base-datos/generar_diccionario.py`, que valida y genera `diccionario-datos.md`, `diccionario-datos.xlsx` y `modelo-er.md`.
- **API documentada con OpenAPI 3.0.3 / Swagger:** contrato en `03-Diseno-Tecnico/api/openapi.yaml` y guía operativa en `03-Diseno-Tecnico/13-especificacion-api-swagger.md` (servida en Django con `drf-spectacular`).
- Un solo repositorio git en la raíz del proyecto; el remoto será privado.
- La lógica de negocio vive solo en `servicios.py` y `selectores.py` (no en procedimientos almacenados).

## Pendientes por confirmar con Richard
1. Cómo se aplica el precio por mayor: por producto sumando tallas (propuesto) o por pedido completo.
2. Quién paga el flete en la agencia: si siempre el cliente por adelantado a Richard o a veces en destino (el sistema ya lo permite con `ENV_CQUIEN_PAGA`).
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
| 2026-11-03 | Estándar de base de datos (doc 12), diccionario de datos y modelo ER; se agrega precio base a Producto | Doc 04, doc 05, doc 12, base-datos/ |
| 2026-11-03 | Restauración íntegra del doc 05 desde `docs/`; código y BD en español; docstring obligatorio de 5 líneas; diccionario en Excel (`diccionario-datos.xlsx`); flujo de cita en punto de encuentro en Lima y venta presencial (diagrama 08); especificación OpenAPI/Swagger (doc 13 y `api/openapi.yaml`) | Reglas IA, docs 02, 03, 04, 05, 10, 11, 12, 13, diagramas 00-08, base-datos/, api/ |
