# Estado actual del proyecto

> La IA lee este archivo al empezar cada sesión y lo actualiza al terminar. Mantenerlo corto.

**Última actualización:** 2026-11-10
**Fase actual:** **Fase 2 completada y verificada al 100%** en `feature/fase-2-carrito-pedido-whatsapp` (`18 passed` en `pytest`, 0 errores en `ruff`, diccionario de datos validado con 13 tablas y 134 columnas). Se incorporaron los logos oficiales de Shalom y Olva Courier en la selección de agencia en checkout, enlace inteligente de WhatsApp con desglose de camisetas y tallas en carrito/checkout, incrustación de logos en el comprobante PDF, QR de Yape oficial y notas de entrega. Listo para commit/merge a `develop` e iniciar la **Fase 3 (Panel de Richard, transiciones de estado y descuento atómico de stock)**.

## Dónde quedamos
- Documentos **01 al 15** completos y alineados; copia intacta de los originales en `01-Relevamiento/fuentes/documentos-originales/`.
- Reglas confirmadas: **código y base de datos en español**, nombres físicos en **MAYÚSCULAS** (`TBL_`), y **docstring de 5 líneas** en cada función.
- **Fase 0 completada y fusionada en `develop` (`bae4844`):**
  - App `nucleo` (`TBL_RCONFIGURACION_TIENDA`, `TBL_RMETODO_PAGO`), `preparar_local`, grupo `Dueño`, sanitización anti-XSS y validadores de DNI/celular peruano.
- **Fase 1 completada y fusionada en `develop` (`e1492aa`):**
  - App `catalogo` (`TBL_RCATEGORIA`, `TBL_RPRODUCTO`, `TBL_RIMAGEN_PRODUCTO`, `TBL_RVARIANTE`, `TBL_RREGLA_PRECIO`), procesamiento WebP (400 px y 900 px), `cargar_demo` con «ARGENTINA X MESSI #10», carrusel de 3 videos 16:9 a `0.72x` con efecto máquina de escribir, lupa zoom 2.2x en ficha, widget flotante de WhatsApp con 2 saltos pin-pon + radar verde + badge `(1)`, QA móvil/desktop y SEO completo.
- **Fase 2 implementada y probada en `04-Desarrollo/` (`feature/fase-2-carrito-pedido-whatsapp`):**
  - App `pedidos`: modelos `Pedido` (`TBL_TPEDIDO`), `ItemPedido` (`TBL_TPEDIDO_ITEM`), `RegistroEstadoPedido` (`TBL_LPEDIDO_ESTADO`, inmutable) e `HistorialPedido` (`TBL_HPEDIDO` con `django-simple-history`).
  - `selectores.py`: `obtener_carrito_detallado` (suma unidades del mismo producto combinando tallas `S + M + L + XL` y aplica tarifa mayorista en el servidor), `obtener_pedido_publico` (oculta DNI completo como `******15` y muestra datos de Yape cuando está en `COTIZADO`) y `construir_enlace_whatsapp_pedido`.
  - `servicios.py`: `agregar_al_carrito`, `eliminar_del_carrito`, `vaciar_carrito`, `generar_codigo_pedido_unico` (`EMU-XXXXXX` no adivinable), `validar_turnstile_cloudflare`, `crear_pedido_web` (`@transaction.atomic`, triple protección antispam Turnstile + `django-ratelimit` + *honeypot*, nace en `COTIZADO` con envío `S/ 0.00` para `PUNTO_ENCUENTRO`/`RECOJO` y en `NUEVO` para `AGENCIA`/`DELIVERY_LIMA`) y `generar_pdf_pedido` con **ReportLab**.
  - Plantillas y vistas HTMX: cajón lateral reactivo (`templates/pedidos/parcial_cajon_carrito.html`), página completa `/carrito/`, checkout `/pedidos/checkout/` con las 4 modalidades de Richard, y página de seguimiento `/pedidos/<codigo>/` con un único CTA `#39FF14` hacia WhatsApp + descarga de PDF (`/pedidos/<codigo>/pdf/`).
  - Suite completa de Fase 0 + Fase 1 + Fase 2 pasando al 100% (`17 passed`, `0` errores en `ruff`, 11 tablas auditadas con `test_estandar_bd.py`).

## En curso
- Revisión en vivo de la **Fase 2** por parte de Jonathan en `feature/fase-2-carrito-pedido-whatsapp` antes de hacer commit, fusionar a `develop` y pasar a la **Fase 3**.

## Siguiente paso
1. Confirmar commit de `feature/fase-2-carrito-pedido-whatsapp`, merge a `develop` y abrir `feature/fase-3-gestion-pedidos-stock` (Fase 3: transiciones de estado, cotizar envío, confirmar pago con descuento atómico de stock `select_for_update()`, entrega en punto de encuentro en un paso, venta presencial directa y registro de despacho por agencia).

## Bloqueos y pendientes con Richard
Ver los 7 puntos de negocio en `00-Gestion/11-decisiones-cambios.md`.

## Datos que aún faltan
- QR de Yape y titular de la cuenta (Richard lo entregará; se sube desde el panel, nunca al repositorio).
