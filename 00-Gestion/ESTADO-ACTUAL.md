# Estado actual del proyecto

> La IA lee este archivo al empezar cada sesión y lo actualiza al terminar. Mantenerlo corto.

**Última actualización:** 2026-11-11
**Fase actual:** **Fase 3 completada y verificada al 100%** en la rama `feature/fase-3-gestion-pedidos-stock` (`29 passed` en `pytest`, 0 errores en `ruff`, diccionario de datos validado al 100% con 13 tablas y 134 columnas). Se implementaron el control atómico de stock anti-deadlock con `select_for_update()`, la bitácora inmutable de auditoría de inventario (`TBL_TMOVIMIENTO_STOCK`), la tabla de envíos por agencia con clave de 4 dígitos y boleta privada (`TBL_TENVIO`), la máquina de transiciones de estado del pedido, el panel de administración personalizado para Richard con acciones rápidas, botón WhatsApp inteligente de notificación al cliente y la interfaz POS para registrar ventas presenciales en mostrador (Flujo C). Listo para commit y merge a `develop`.

## Dónde quedamos
- Documentos **01 al 15** completos y alineados; copia intacta de los originales en `01-Relevamiento/fuentes/documentos-originales/`.
- Reglas confirmadas: **código y base de datos en español**, nombres físicos en **MAYÚSCULAS** (`TBL_`), y **docstring de 5 líneas** en cada función.
- **Fase 0 completada y fusionada en `develop` (`bae4844`):**
  - App `nucleo` (`TBL_RCONFIGURACION_TIENDA`, `TBL_RMETODO_PAGO`), `preparar_local`, grupo `Dueño`, sanitización anti-XSS y validadores de DNI/celular peruano.
- **Fase 1 completada y fusionada en `develop` (`e1492aa`):**
  - App `catalogo` (`TBL_RCATEGORIA`, `TBL_RPRODUCTO`, `TBL_RIMAGEN_PRODUCTO`, `TBL_RVARIANTE`, `TBL_RREGLA_PRECIO`), procesamiento WebP (400 px y 900 px), `cargar_demo` con «ARGENTINA X MESSI #10», carrusel de videos a `0.72x`, lupa zoom 2.2x en ficha, widget flotante de WhatsApp y SEO completo.
- **Fase 2 completada y fusionada en `develop` (`ff4f8ef`):**
  - App `pedidos`: modelos `Pedido`, `ItemPedido`, `RegistroEstadoPedido` (`TBL_LPEDIDO_ESTADO`, inmutable) e `HistorialPedido`.
  - Carrito HTMX en sesión con cálculo de precio por mayor unificado entre tallas `S/M/L/XL`, checkout con 4 modalidades, logos oficiales de Shalom y Olva Courier, comprobante PDF ReportLab con logo dinámico y QR oficial de Yape de Richard, y enlace dinámico de WhatsApp con desglose de prendas.
- **Fase 3 completada y probada al 100% (`feature/fase-3-gestion-pedidos-stock`):**
  - **Inventario inmutable:** `MovimientoStock` (`TBL_TMOVIMIENTO_STOCK`) con bloqueo en `save()` y `delete()`, constraint `MOV_NCANTIDAD <> 0` e índice por variante y fecha de creación.
  - **Despacho por agencia:** `Envio` (`TBL_TENVIO`) con relación 1 a 1 con Pedido, número de guía/orden, clave de recojo privada de 4 dígitos, foto de boleta privada con vista autenticada (`/pedidos/envio/<id>/boleta/`), flete y quién paga.
  - **Servicios del corazón del negocio:**
    - `cambiar_estado`: validación estricta según matriz oficial de transiciones, actualización de timestamps y bitácora `TBL_LPEDIDO_ESTADO`.
    - `cotizar_envio`: actualiza flete y pasa `NUEVO -> COTIZADO`.
    - `confirmar_pago`: transacción atómica con `select_for_update()` ordenado por `id` de variante (anti-deadlock), descuenta stock y genera movimientos `VENTA`.
    - `confirmar_pago_y_entregar`: Flujo B de Lima en un solo paso (`COTIZADO -> PAGADO -> ENTREGADO`) con doble registro en bitácora.
    - `registrar_envio_agencia`: valida clave de 4 dígitos, flete y foto de boleta pasando `PAGADO -> ENVIADO`.
    - `cancelar_o_rechazar`: repone automáticamente el inventario creando movimientos `DEVOLUCION` si el pedido estaba pagado.
    - `registrar_venta_presencial`: Flujo C POS en mostrador/feria con precio mayorista automático, pedido `PRESENCIAL`, descuento de stock y estado `ENTREGADO`.
    - `construir_enlace_whatsapp_notificacion_cliente`: enlaces automáticos con markdown para avisar cotización, enviar orden/clave de agencia o coordinar punto de encuentro.
  - **Panel administrativo de Richard:**
    - `PedidoAdmin`: acciones masivas para confirmar pago, entrega rápida en Lima, marcar entregado y cancelar con reposición.
    - Columna changelist `Avisar por WhatsApp` con botón dinámico según el estado del pedido.
    - `EnvioInline` y `EnvioAdmin` para gestión de despachos.
    - Interfaz POS personalizada `/admin/pedidos/pedido/venta-presencial/` con formulario táctil para mostrador.
    - `MovimientoStockAdmin` 100% solo lectura y `VarianteAdmin` con stock protegido.
  - **Pruebas integrales:** `tests/test_gestion_pedidos.py` con 9 escenarios clave (matriz de transiciones, Flujos A/B/C, rollback por stock insuficiente, restitución por cancelación, inmutabilidad de movimientos, seguridad de boletas y vista POS admin).
  - Script k6 `escenarios-base.js` actualizado con el modo `concurrencia_stock` listo para ejecutar contra PostgreSQL en Render (Fase 5).

## En curso
- Revisión de la **Fase 3** por parte de Jonathan en `feature/fase-3-gestion-pedidos-stock` antes de fusionar a `develop`.

## Siguiente paso
1. Fusionar `feature/fase-3-gestion-pedidos-stock` a `develop`.
2. Iniciar la **Fase 4: Panel visual de Richard con métricas y alertas de stock bajo**.

## Bloqueos y pendientes con Richard
Ver los 7 puntos de negocio en `00-Gestion/11-decisiones-cambios.md`.

## Datos que aún faltan
- Credenciales de PostgreSQL en Render (Jonathan las compartirá en la Fase 5).
- Credenciales y URL de Cloudflare R2 / S3 para migrar los archivos multimedia privados en Fase 6.
