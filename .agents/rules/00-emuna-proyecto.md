# Emuná Sport – Reglas del proyecto (siempre activas)

Proyecto: tienda web (catálogo + carrito + pedido) para Emuná Sport, con panel de administración para Richard (dueño) y Jonathan Vera (responsable técnico). Stack: Django + PostgreSQL (SQLite solo en local).

## Continuidad entre sesiones (siempre)
- Al empezar: lee `00-Gestion/ESTADO-ACTUAL.md` y las últimas entradas de `00-Gestion/BITACORA-sesiones.md` y del doc 11. Resume en 3 líneas dónde quedamos antes de actuar.
- Al terminar: actualiza `ESTADO-ACTUAL.md` (hecho, en curso, siguiente paso, bloqueos) y agrega una entrada en `BITACORA-sesiones.md`.
- Estructura y propósito de cada carpeta: `00-Gestion/ESTANDAR-ESTRUCTURA.md`. El código va solo en `04-Desarrollo/`.

## Antes de escribir código
1. Lee los documentos del proyecto (carpetas `01` a `05`; índice en `00-Gestion/00-LEEME-indice.md`). Son la fuente de verdad. Si el código y los documentos se contradicen, avisa y propón cuál actualizar; no decidas en silencio.
2. Propón un plan de implementación y espera aprobación antes de crear o modificar muchos archivos.
3. Trabaja solo la fase actual de `02-Planificacion/10-plan-fases.md`. No agregues funciones de fases futuras.

## Reglas obligatorias de código
- Lógica de negocio solo en `services.py` (escrituras) y `selectors.py` (lecturas). Las vistas, serializers, templates y el admin son delgados y llaman a services.
- No dupliques lógica: si dos lugares necesitan lo mismo, crea una función compartida.
- El stock solo cambia mediante `StockMovement` creado por un service, dentro de una transacción. Nunca edites `stock_quantity` a mano en el código.
- El estado de un pedido solo cambia mediante `orders.services.change_status()`, que valida la transición (ver `01-Relevamiento/03-flujo-pedidos-estados.md`).
- `OrderItem` guarda una copia (snapshot) del nombre, la talla y el precio en el momento de la compra. Nunca recalcules pedidos viejos con precios nuevos.
- Dinero: `Decimal`, soles peruanos (PEN), 2 decimales. Zona horaria `America/Lima`.
- Nada de secretos en el repositorio: todo por variables de entorno. No hagas commit del QR de Yape, boletas, DNI ni datos reales de clientes.
- El DNI del cliente y la clave de recojo del envío son datos privados: nunca en URLs, logs, páginas públicas ni mensajes de error.
- Cada cambio de modelo lleva su migración. Cada service lleva pruebas (`pytest`). Formato y lint con `ruff`.
- Base de datos: nombres físicos de tablas y columnas según `03-Diseno-Tecnico/12-estandar-base-datos.md` y `03-Diseno-Tecnico/base-datos/diccionario-datos.md` (`db_table` y `db_column` en cada modelo). Sin cursores; la lógica no va en procedimientos almacenados.

## Convenciones
- Código (clases, variables, apps) en inglés. Textos visibles al usuario, comentarios y mensajes de commit en español.
- Interfaz en español de Perú. Mobile-first: la mayoría de clientes entra desde WhatsApp en el celular.
- La marca (brand) del producto está apagada por defecto. No muestres marcas ni nombres de clubes en el catálogo salvo que el producto lo tenga configurado.
- Cambios de reglas de negocio: actualiza primero el documento correspondiente y agrega una línea en `00-Gestion/11-decisiones-cambios.md`.
- Cada carpeta nueva lleva un `LEEME.txt`. Los diagramas del negocio están en `01-Relevamiento/diagramas/`: si cambia un flujo, actualiza su diagrama.
