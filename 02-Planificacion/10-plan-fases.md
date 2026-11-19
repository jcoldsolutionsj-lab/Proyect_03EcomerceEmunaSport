# 10 – Plan por fases

Cada fase termina con algo que Richard pueda ver. La IA trabaja una fase a la vez y propone un plan antes de empezar. Definición de terminado: pruebas pasando, `ruff` sin errores, docstrings de 5 líneas en cada función, migraciones incluidas, diccionario de datos validado (`python generar_diccionario.py`), documentos actualizados y una nota en el doc 11 si cambió alguna regla.

## Fase 0 – Base del proyecto
- Estructura en `04-Desarrollo/` y apps vacías (`nucleo`, `catalogo`, `inventario`, `pedidos`, `envios`, `tablero`), settings por entorno (con HTTPS forzado `SECURE_SSL_REDIRECT` y cabeceras HSTS listas para `demo`/`production`), `.env.example`, `ruff` y `pytest`.
- Modelo de usuario y grupos (`Dueño`).
- `ConfiguracionTienda` (`TBL_RCONFIGURACION_TIENDA`) y `MetodoPago` (`TBL_RMETODO_PAGO`) en el admin.
- Test automático que verifica que todas las tablas y columnas propias cumplen el estándar `TBL_` en MAYÚSCULAS.
- **Listo cuando:** el proyecto corre en local, el admin abre y las pruebas base pasan.

## Fase 1 – Catálogo y Frontend público (UI, SEO y páginas legales)
- Categorías, productos, variantes con stock por talla, reglas de precio por mayor, fotos comprimidas automáticamente en WebP (~400 px miniatura y ~900 px detalle) y texto alternativo (`alt`) automático/editable (`IMA_CTEXTO_ALT`).
- Plantilla base, página de inicio y ficha de producto aplicando el doc 06 (**Taste Skill + Emil Kowalski/Impeccable**): contraste accesible (`#39FF14` con texto `#0A0A0A`), diseño adaptable móvil (`360 px`) y desktop (`1280 px+`), **un único botón de acción principal (CTA) por pantalla**, botón de WhatsApp visible y contextual, `loading="lazy"` y `aspect-ratio: 4/5` (velocidad optimizada sin saltos de pantalla).
- Elementos pre-lanzamiento incluidos desde la base (ver doc 15):
  - Páginas legales públicas: `/aviso-legal/`, `/privacidad/` (Ley N.º 29733 Perú) y `/cookies/` + aviso discreto de cookies.
  - SEO técnico: meta títulos y descripciones dinámicos + OpenGraph para WhatsApp, datos estructurados JSON-LD (`Organization`, `Product`, `BreadcrumbList`), `/sitemap.xml`, `/robots.txt` y `favicon` completo.
  - Páginas `404.html` y `500.html` personalizadas y gancho para analítica (`GA4_MEASUREMENT_ID` / Cloudflare).
- Comando `cargar_demo` (`seed_demo`) con 8 a 12 productos de ejemplo.
- Pruebas con `pytest` y **Playwright** (vista móvil y desktop + detector automático de enlaces rotos).
- **Listo cuando:** Richard puede cargar un producto con tallas y stock y verlo impecable en el celular y en computadora.

## Fase 2 – Carrito y pedido
- Carrito en sesión con cajón lateral fluido (HTMX + Alpine.js), checkout con modalidad de entrega (`AGENCIA`, `DELIVERY_LIMA`, `PUNTO_ENCUENTRO`, `RECOJO`), validaciones de DNI y teléfono, y casilla de aceptación de privacidad.
- Triple protección antispam en el formulario de pedido: **Cloudflare Turnstile** + `django-ratelimit` + campo trampa (*honeypot*).
- Creación del pedido con copias de precios, código no adivinable, página del pedido con **un solo CTA principal** («Enviar a Richard por WhatsApp») y descarga de PDF como acción secundaria.
- **Prueba de carga inicial con Grafana k6 (`03-Diseno-Tecnico/pruebas-carga-k6/`):** validar que el catálogo y la creación de pedidos respondan en `< 500 ms` (p95).
- **Listo cuando:** un cliente envía un pedido desde el celular, descarga su PDF y pasa la prueba E2E en Playwright y humo en k6.

## Fase 3 – Gestión del pedido (corazón del negocio)
- Estados y transiciones (`pedidos.servicios.cambiar_estado`), cotizar envío, pantalla de pago con Yape (botón «Copiar» con feedback táctil), confirmar pago con descuento de stock atómico (`select_for_update()`).
- Entrega en punto de encuentro en Lima («Confirmar pago y entregar» en un paso) y registro de venta presencial directa (`origen = PRESENCIAL`).
- Registro del envío por agencia (número de orden, clave, boleta, flete) y botones de WhatsApp para el cliente.
- Historial de cambios y registro inmutable de movimientos de stock.
- **Prueba de concurrencia con Grafana k6 (`concurrencia_stock`):** comprobar sobre PostgreSQL local que ante compras simultáneas de la última unidad nunca quede stock negativo.
- **Listo cuando:** se puede completar un pedido de agencia de `NUEVO` a `ENVIADO` y una entrega en Lima de `COTIZADO` a `ENTREGADO`, y el stock queda intacto bajo concurrencia.

## Fase 4 – Tablero y alertas
- Stock bajo, sin ventas, más vendidos, ventas por período, pedidos pendientes antiguos.
- Exportar pedidos a CSV.
- **Listo cuando:** Richard ve desde el celular qué se vendió y qué no.

## Fase 5 – Piloto en demo y observaciones
- Despliegue de demo en Render con datos de ejemplo y prueba de humo ligera (*smoke test*, sin estresar el plan gratuito de Render).
- Richard prueba y deja observaciones en `06-Observaciones-Piloto/`; se anotan en el doc 11 y se priorizan.
- Panel optimizado para celular con `django-unfold`.

## Fase 6 – Pre-lanzamiento y salida a producción (Checklist doc 15 al 100%)
- Dominio oficial en Cloudflare con HTTPS forzado, llaves reales de Cloudflare Turnstile, bucket R2 de producción, PostgreSQL persistente con respaldo y 2FA para el admin.
- Verificación de los **20 puntos del doc `05-Despliegue/15-checklist-antes-de-lanzar-web.md`**: Ficha de Google (Google Business Profile + Search Console con `sitemap.xml`), analítica activa y **prueba de carga de campaña con Grafana k6** (simulando pico de visitas desde estados de WhatsApp).
- Página de seguimiento para el cliente, segundo método de pago (Plin), notificaciones por correo, API REST con JWT y Swagger (`drf-spectacular` según `03-Diseno-Tecnico/api/openapi.yaml`) y evaluación de app móvil.

## Reglas para la IA en cada fase
1. Resume la fase y lista los archivos que vas a crear o cambiar.
2. Espera aprobación del plan.
3. Implementa con pruebas y con el docstring obligatorio en cada función.
4. Al terminar, resume lo hecho, lo pendiente y actualiza `ESTADO-ACTUAL.md` y `BITACORA-sesiones.md`.
