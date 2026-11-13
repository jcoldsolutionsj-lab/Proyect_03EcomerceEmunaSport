# Estado actual del proyecto

> La IA lee este archivo al empezar cada sesión y lo actualiza al terminar. Mantenerlo corto.

**Última actualización:** 2026-11-13
**Fase actual:** **Fase 4 fusionada en `develop` (`48ce0b9`) + Rediseño Flat Design exclusivo para `/gestion/` completado en `feature/panel-flat-design-unfold`** (`32 passed` en `pytest`, **0 errores** en `ruff`, verificación visual Playwright móvil `360x740` y escritorio `1280x800` aprobada en las 17 vistas del panel). La tienda web pública quedó intacta. Lista para revisar y fusionar `feature/panel-flat-design-unfold` en `develop` antes de iniciar la **Fase 5: Piloto en demo y observaciones**.

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
- **Fase 3 completada, probada al 100% y fusionada en `develop` (`feature/fase-3-gestion-pedidos-stock`):**
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

- **Fase 4 completada y fusionada en `develop` (`48ce0b9`):**
  - **Métricas y selectores (`apps/tablero/selectores.py`):** cálculo de ingresos confirmados (`PAGADO`/`ENVIADO`/`ENTREGADO`), desglose Web vs. POS presencial, unidades vendidas, ticket promedio, filtros rápidos (`hoy`, `7dias`, `mes`, `todo`, rango personalizado `desde`/`hasta`), evolución diaria con barra proporcional, cola operativa en vivo, ranking Top 10 más vendidos y productos activos sin rotación en los últimos `dias_sin_ventas` días.
  - **Alertas críticas y semáforos:** detección de tallas agotadas (`[ROJO]`) y stock bajo (`[ÁMBAR]`) respetando `Variante.umbral_stock_bajo` individual o el umbral global de `ConfiguracionTienda` mediante `Coalesce`, además de pedidos pendientes (`NUEVO`/`COTIZADO`) con más de `horas_pedido_pendiente` horas y enlace directo por WhatsApp. Resguardo adicional en `VarianteAdmin.stock_semaforo` y `umbral_col` ante umbrales `None`.
  - **Exportación CSV segura (`apps/tablero/servicios.py`):** descarga con BOM UTF-8 (`utf-8-sig` compatible con Excel) para ventas del período y alertas de stock, neutralizando inyección de fórmulas (`=`, `+`, `-`, `@`, tab, CR) mediante `_sanitizar_celda_csv` y encabezados `Cache-Control: no-store`.
  - **UI Enterprise Java/JSP y móvil (`templates/tablero/resumen_tablero.html`, `templates/admin/base_site.html`):** ruta privada `/gestion/tablero/` protegida exclusivamente para usuarios activos `staff`/`superuser`/`Dueño` (`302`/`403`), accesos directos en `/gestion/` y barra rápida móvil, diseño verificado en `360x740` (sin desborde horizontal, tablas con scroll interno) y `1280x800`.
  - **Pruebas:** `tests/test_tablero.py` (3 escenarios completos alcanzando **32 pruebas pasando al 100%**).

- **Rediseño Flat Design del Panel `/gestion/` con `django-unfold==0.110.1` (`feature/panel-flat-design-unfold`):**
  - Migración estética e interfaz responsiva exclusiva dentro de `/gestion/` (sin modificar la tienda pública web `/`): `config/settings/base.py`, `apps/nucleo/unfold_config.py`, `requirements/base.txt` y hoja plana compartida `static/css/emuna_flat_unfold.css` (cero sombras, bordes definidos `1px`, radio `4px`, modo claro forzado, `zoom: 0.85` en escritorio y `zoom: 1` en móvil `<= 1024px`).
  - Navegación lateral operativa con insignias en tiempo real para alertas del tablero y cola de pedidos pendientes, portada `/gestion/` con 4 tarjetas KPI ejecutivas en vivo (`DASHBOARD_CALLBACK`) y acceso rápido a Tablero y POS.
  - Consistencia total de tooltips `toltip.png` en listados e inlines (`templates/unfold/helpers/inline_heading.html`, `templates/unfold/edit_inline/*`), botones táctiles en móvil (`.emuna-mobile-quicknav` + `#emuna-touch-tooltip` en cabecera) y traducciones al español para login y buscadores de Unfold.
  - Pruebas integrales aprobadas (`ruff check 04-Desarrollo` sin errores, `32/32` en `pytest` y 17 capturas Edge headless móvil/escritorio sin desborde horizontal).

## En curso
- Revisión final por Jonathan del nuevo panel Flat Design en `feature/panel-flat-design-unfold` para autorizar su merge a `develop`.

## Siguiente paso
1. Con el visto bueno de Jonathan, fusionar (`--no-ff`) `feature/panel-flat-design-unfold` en `develop` y subir a `origin`.
2. Recordar instalar/actualizar dependencias (`pip install -r 04-Desarrollo/requirements/base.txt`) o usar la `.venv` actualizada con `django-unfold==0.110.1`.
3. Iniciar la **Fase 5: Piloto en demo y observaciones** (configuración PostgreSQL/Render, endpoints REST/Swagger, CORS/whitenoise y pruebas k6).

## Bloqueos y pendientes con Richard
Ver los 7 puntos de negocio en `00-Gestion/11-decisiones-cambios.md`.

## Datos que aún faltan
- Credenciales de PostgreSQL en Render (Jonathan las compartirá en la Fase 5).
- Credenciales y URL de Cloudflare R2 / S3 para migrar los archivos multimedia privados en Fase 6.
