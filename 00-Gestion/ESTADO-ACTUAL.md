# Estado actual del proyecto

> La IA lee este archivo al empezar cada sesión y lo actualiza al terminar. Mantenerlo corto.

**Última actualización:** 2026-11-10
**Fase actual:** **Fase 1 completada y probada** en `feature/fase-1-catalogo-frontend` (`11 passed` en `pytest`, 0 errores en `ruff`). `feature/fase-0-base` ya fusionada en `develop`. Listo para hacer commit de Fase 1, fusionar en `develop` y pasar a la **Fase 2 (Carrito en sesión con HTMX + Pedido + PDF + WhatsApp)**.

## Dónde quedamos
- Documentos **01 al 15** completos y alineados; copia intacta de los originales en `01-Relevamiento/fuentes/documentos-originales/`.
- Reglas confirmadas: **código y base de datos en español**, nombres físicos en **MAYÚSCULAS** (`TBL_`), y **docstring de 5 líneas** en cada función.
- Flujo de **cita en punto de encuentro en Lima con pago Yape al momento** y **venta presencial directa** incorporados en reglas (doc 02), estados (doc 03), modelo (doc 04), diagramas (`00` al `08`) y API.
- Diccionario de datos validado (**13 tablas, 134 columnas**, incluyendo `PRO_NPRECIO_ANTERIOR` para precio regular tachado `S/ 69.90` e `IMA_CTEXTO_ALT` para SEO `alt`) generado en Markdown y Excel (`03-Diseno-Tecnico/base-datos/diccionario-datos.xlsx`).
- Contrato OpenAPI 3.0.3 / Swagger validado (19 rutas) en `03-Diseno-Tecnico/api/openapi.yaml` y explicado en el doc 13.
- **Pruebas de carga y concurrencia con Grafana k6** definidas por fase en `03-Diseno-Tecnico/pruebas-carga-k6/` (`plan-pruebas-k6.md` y `escenarios-base.js`).
- **Estándares de Diseño Frontend (Taste Skill + Emil Kowalski/Impeccable + UI UX Pro Max + Playwright)**, **metodologías `Feature Dev` y `CodeReview`** (doc 05), **5 pilares anti-hacking (`RLS`, `CORS`, `Variables de Entorno`, `Rate Limiting`, `Sanitización de Inputs`)** (doc 07 y `01_rls_seguridad_filas.sql`) y **Checklist de 20 puntos «Antes de lanzar la web»** (doc 15) documentados y activos en las reglas.
- **Fase 0 completada y fusionada en `develop` (`origin/develop`):**
  - App `nucleo` (`TBL_RCONFIGURACION_TIENDA`, `TBL_RMETODO_PAGO`), `preparar_local`, grupo `Dueño`, sanitización anti-XSS y validadores de DNI/celular peruano.
- **Fase 1 implementada y verificada en `04-Desarrollo/` (`feature/fase-1-catalogo-frontend`):**
  - App `catalogo`: modelos `Categoria` (`TBL_RCATEGORIA`), `Producto` (`TBL_RPRODUCTO`), `ImagenProducto` (`TBL_RIMAGEN_PRODUCTO`), `Variante` (`TBL_RVARIANTE`) y `ReglaPrecio` (`TBL_RREGLA_PRECIO`).
  - `selectores.py` (cero consultas N+1, filtros por talla `S/M/L/XL`, categoría, búsqueda y stock, y cálculo de precio por mayor), `servicios.py` (conversión automática a WebP 400 px y 900 px con bloqueo de archivos peligrosos), `admin.py` con inlines y `cargar_demo.py` (4 categorías y 8 camisetas encabezadas por «ARGENTINA X MESSI #10» con sus 5 fotos reales).
  - Frontend público: `base.html`, `catalogo/inicio.html` (Hero Video Banner con `banner_1..3.mp4`, sección destacada, filtros de talla y grilla 4:5), `catalogo/detalle_producto.html` (layout 2 columnas con 5 miniaturas verticales, selector de tallas con stock en vivo, tabla de ahorro por mayor y un único CTA `#39FF14`), páginas legales (`aviso-legal`, `privacidad` Ley N.º 29733, `cookies`), `404.html`, `500.html`, `robots.txt`, `sitemap.xml` y datos estructurados JSON-LD (`SportingGoodsStore` y `Product`).
  - Suite de pruebas de Fase 0 + Fase 1 pasando al 100% (`11 passed in 11.64s`, `ruff` sin errores, detector automático de enlaces rotos y auditoría de las 7 tablas `TBL_` creadas hasta ahora).

## En curso
- Confirmación de commit de **`feature/fase-1-catalogo-frontend`**, merge a `develop` y arranque de la **Fase 2 (`feature/fase-2-carrito-pedido-whatsapp`)**.

## Siguiente paso
1. Confirmar el commit y merge de `feature/fase-1-catalogo-frontend` a `develop` y presentar/ejecutar la **Fase 2 (Carrito en sesión con HTMX + Checkout con las 4 modalidades de Richard + PDF + WhatsApp)**.

## Bloqueos y pendientes con Richard
Ver los 7 puntos de negocio en `00-Gestion/11-decisiones-cambios.md` (no bloquean la Fase 0 ni la Fase 1).

## Datos que aún faltan
- QR de Yape y titular de la cuenta (Richard lo entregará; se sube desde el panel, nunca al repositorio).
