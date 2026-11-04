# 10 – Plan por fases

Cada fase termina con algo que Richard pueda ver. La IA trabaja una fase a la vez y propone un plan antes de empezar. Definición de terminado: pruebas pasando, `ruff` sin errores, docstrings de 5 líneas en cada función, migraciones incluidas, diccionario de datos validado (`python generar_diccionario.py`), documentos actualizados y una nota en el doc 11 si cambió alguna regla.

## Fase 0 – Base del proyecto
- Estructura en `04-Desarrollo/` y apps vacías (`nucleo`, `catalogo`, `inventario`, `pedidos`, `envios`, `tablero`), settings por entorno, `.env.example`, `ruff` y `pytest`.
- Modelo de usuario y grupos (`Dueño`).
- `ConfiguracionTienda` (`TBL_RCONFIGURACION_TIENDA`) y `MetodoPago` (`TBL_RMETODO_PAGO`) en el admin.
- Test automático que verifica que todas las tablas y columnas propias cumplen el estándar `TBL_` en MAYÚSCULAS.
- **Listo cuando:** el proyecto corre en local, el admin abre y las pruebas base pasan.

## Fase 1 – Catálogo
- Categorías, productos, variantes con stock por talla, reglas de precio por mayor, fotos con miniatura y detalle.
- Página de inicio y de producto (diseño del doc 06).
- Comando `cargar_demo` (`seed_demo`) con 8 a 12 productos de ejemplo.
- **Listo cuando:** Richard puede cargar un producto con tallas y stock y verlo en la web en el celular.

## Fase 2 – Carrito y pedido
- Carrito en sesión, checkout con modalidad de entrega (`AGENCIA`, `DELIVERY_LIMA`, `PUNTO_ENCUENTRO`, `RECOJO`), validaciones de DNI y teléfono.
- Creación del pedido con copias de precios, código no adivinable y página del pedido.
- PDF del pedido y botón de WhatsApp.
- **Listo cuando:** un cliente envía un pedido desde el celular y descarga su PDF.

## Fase 3 – Gestión del pedido (corazón del negocio)
- Estados y transiciones (`pedidos.servicios.cambiar_estado`), cotizar envío, pantalla de pago con Yape, confirmar pago con descuento de stock atómico.
- Entrega en punto de encuentro en Lima («Confirmar pago y entregar» en un paso) y registro de venta presencial directa (`origen = PRESENCIAL`).
- Registro del envío por agencia (número de orden, clave, boleta, flete) y botones de WhatsApp para el cliente.
- Historial de cambios y registro inmutable de movimientos de stock.
- **Listo cuando:** se puede completar un pedido de agencia de `NUEVO` a `ENVIADO` y una entrega en Lima de `COTIZADO` a `ENTREGADO`, y el stock queda correcto.

## Fase 4 – Tablero y alertas
- Stock bajo, sin ventas, más vendidos, ventas por período, pedidos pendientes antiguos.
- Exportar pedidos a CSV.
- **Listo cuando:** Richard ve desde el celular qué se vendió y qué no.

## Fase 5 – Piloto en demo y observaciones
- Despliegue de demo en Render con datos de ejemplo.
- Richard prueba y deja observaciones en `06-Observaciones-Piloto/`; se anotan en el doc 11 y se priorizan.
- Opcional: `django-unfold`.

## Fase 6 – Después del piloto
Dominio oficial en Cloudflare, bucket R2 de producción, PostgreSQL persistente con respaldo, 2FA para el admin, página de seguimiento para el cliente, segundo método de pago (Plin), notificaciones por correo, API REST con JWT y Swagger (`drf-spectacular` según `03-Diseno-Tecnico/api/openapi.yaml`) y evaluación de app móvil.

## Reglas para la IA en cada fase
1. Resume la fase y lista los archivos que vas a crear o cambiar.
2. Espera aprobación del plan.
3. Implementa con pruebas y con el docstring obligatorio en cada función.
4. Al terminar, resume lo hecho, lo pendiente y actualiza `ESTADO-ACTUAL.md` y `BITACORA-sesiones.md`.
