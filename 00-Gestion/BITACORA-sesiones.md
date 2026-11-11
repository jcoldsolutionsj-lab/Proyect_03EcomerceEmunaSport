# Bitácora de sesiones

Una entrada breve por sesión de trabajo, la más reciente **arriba**. Cada entrada responde: qué se hizo, qué se decidió, qué queda.

## 2026-11-10 – Mejoras de comprobante, logos oficiales de agencia y enlace dinámico de WhatsApp en Fase 2
- **Hecho:**
  - Se integró el video animado oficial `Logo_animado.mp4` en el navbar de la cabecera (`base.html`), eliminando sombras verdes externas o animaciones CSS superpuestas para que luzca limpio y fiel al video original.
  - Se incorporaron los logos oficiales de **Agencia Shalom** (`shalom_logo.png`) y **Olva Courier** (`Olva_logo.png`) dentro de la selección de agencia en `http://127.0.0.1:8000/pedidos/checkout/`, dotando de máxima seriedad y presencia de marca al formulario de envío a provincia.
  - Se actualizó el comprobante PDF (`generar_pdf_pedido`) para incrustar automáticamente el logo oficial de la agencia seleccionada (Shalom u Olva), especificar el nombre exacto de la agencia en la modalidad y plasmar la observación/comentario del cliente (`pedido.notas`) cuando exista.
  - Se integró la foto oficial del código QR de Yape de Richard (`QR_yape_richardRamos.jpeg`) en la tarjeta de seguimiento del pedido (`detalle_pedido.html`), con su titular ("Richard Ramos - Emuná Sport") y botón de copiado resiliente con fallback portapapeles.
  - Se creó el selector dinámico `carrito.url_whatsapp_consulta` (`obtener_carrito_detallado`), permitiendo que el link «Escribir por WhatsApp» en el cajón lateral HTMX, la página `/carrito/` y el checkout `/pedidos/checkout/` arme automáticamente el mensaje prellenado hacia Richard con el detalle de camisetas, tallas, cantidades y subtotales calculados.
  - Se añadieron pruebas unitarias automatizadas (`test_pdf_pedido_agencia_shalom_con_notas` y aserción de `url_whatsapp_consulta`), alcanzando 18 pruebas pasando al 100% en `pytest` y 0 errores en `ruff check`.
- **Decidido:** dar por concluida la Fase 2 y presentar a Jonathan el resumen final para su visto bueno de commit y merge a `develop`.
- **Queda:** fusionar `feature/fase-2-carrito-pedido-whatsapp` a `develop` e iniciar la **Fase 3: Panel de control de Richard, transiciones de estado de pedido y descuento atómico de stock**.

## 2026-11-10 – Implementación y pruebas de la Fase 2 (`feature/fase-2-carrito-pedido-whatsapp`)
- **Hecho:**
  - Se cerró la Fase 1 con QA UI/UX móvil y desktop aprobado, se hizo commit en `feature/fase-1-catalogo-frontend` (`296604b`), se fusionó (`--no-ff`) en `develop` (`e1492aa`), se subió a `origin` y se creó la rama `feature/fase-2-carrito-pedido-whatsapp`.
  - Se implementaron en `04-Desarrollo/apps/pedidos/models.py` (y su migración `0001_initial.py`) las 4 tablas físicas del dominio de pedidos cumpliendo el diccionario al 100%: `Pedido` (`TBL_TPEDIDO`), `ItemPedido` (`TBL_TPEDIDO_ITEM` con snapshots de nombre, SKU, talla y precio), `RegistroEstadoPedido` (`TBL_LPEDIDO_ESTADO`, inmutable) e `HistorialPedido` (`TBL_HPEDIDO` de `django-simple-history`).
  - Se crearon `selectores.py` (`obtener_carrito_detallado` sumando unidades del mismo producto entre distintas tallas `S/M/L/XL` para activar el precio por mayor, `obtener_pedido_publico` con DNI enmascarado `******15` y datos de Yape cuando está en `COTIZADO`, y `construir_enlace_whatsapp_pedido`) y `servicios.py` (`agregar_al_carrito`, `eliminar_del_carrito`, `vaciar_carrito`, `generar_codigo_pedido_unico` `EMU-XXXXXX`, `validar_turnstile_cloudflare`, `crear_pedido_web` con triple protección antispam y `generar_pdf_pedido` con ReportLab).
  - Se conectó el cajón lateral del carrito con **HTMX** (`templates/pedidos/parcial_cajon_carrito.html`, actualización OOB del contador del header y apertura automática al agregar desde `detalle_producto.html`), se construyeron `/carrito/`, `/pedidos/checkout/` (con las 4 modalidades reales de Richard: `PUNTO_ENCUENTRO`, `AGENCIA` Shalom/Olva exigiendo DNI, `DELIVERY_LIMA` y `RECOJO`), `/pedidos/<codigo>/` (con un único CTA `#39FF14` hacia WhatsApp + tarjeta Yape copiable) y `/pedidos/<codigo>/pdf/`.
  - Se ejecutó `ruff check 04-Desarrollo` (0 errores), `generar_diccionario.py` (13 tablas, 134 columnas validadas) y la suite completa de `pytest` (`17 passed`: Fase 0 + Fase 1 + Fase 2 + estándar `TBL_` en MAYÚSCULAS).
- **Decidido:** presentar la Fase 2 lista para que Jonathan la pruebe en su navegador antes de hacer commit y merge a `develop`.
- **Queda:** confirmar commit de `feature/fase-2-carrito-pedido-whatsapp`, fusionar a `develop` y pasar a la Fase 3 (Gestión del pedido y descuento atómico de stock).

## 2026-11-10 – Implementación y pruebas de la Fase 1 (`feature/fase-1-catalogo-frontend`)
- **Hecho:**
  - Se cerró la Fase 0 con commits estructurados en `feature/fase-0-base`, se fusionó (`--no-ff`) en `develop`, se subió a `origin` y se creó la rama `feature/fase-1-catalogo-frontend`.
  - Se implementó la app `catalogo` con los 5 modelos físicos (`TBL_RCATEGORIA`, `TBL_RPRODUCTO`, `TBL_RIMAGEN_PRODUCTO`, `TBL_RVARIANTE`, `TBL_RREGLA_PRECIO`), `selectores.py` (cero consultas N+1, filtros por talla `S/M/L/XL`, categoría, búsqueda y stock, y cálculo de precio por mayor), `servicios.py` (conversión automática a WebP 400 px y 900 px con bloqueo de `.svg`/`.exe`), `admin.py` con inlines y el comando `cargar_demo` (4 categorías y 8 productos encabezados por «ARGENTINA X MESSI #10» con sus 5 fotos reales).
  - Se construyó el Frontend público (`base.html`, `catalogo/inicio.html` con Hero Video Banner de `banner_1..3.mp4`, `catalogo/detalle_producto.html` con galería 5 miniaturas + selector de tallas + ahorro por mayor + CTA único `#39FF14`), páginas legales (`aviso-legal`, `privacidad` Ley N.º 29733, `cookies`), `404.html`, `500.html`, `robots.txt`, `sitemap.xml` y JSON-LD (`SportingGoodsStore` y `Product`).
  - Se ejecutó `ruff check` (0 errores) y `pytest` (`11 passed in 11.64s`, incluyendo detector automático de enlaces rotos y auditoría de las 7 tablas `TBL_` en MAYÚSCULAS).
- **Decidido:** confirmar las pruebas con Jonathan antes de realizar los commits en `feature/fase-1-catalogo-frontend` y fusionar a `develop`.
- **Queda:** hacer commit y merge de `feature/fase-1-catalogo-frontend` a `develop` y arrancar la Fase 2 (Carrito en sesión con HTMX + Pedido + PDF + WhatsApp).

## 2026-11-10 – Implementación y pruebas de la Fase 0 (`feature/fase-0-base`)
- **Hecho:**
  - Se creó el entorno virtual `.venv` con Django 5.2 LTS, DRF, `drf-spectacular`, `django-cors-headers`, `django-ratelimit`, `pytest`, `ruff` y `Pillow`.
  - Se implementó la estructura base en `04-Desarrollo/`: `manage.py`, `pyproject.toml`, `.env.example`, `requirements/` y `config/settings/` (`base`, `local`, `demo`, `production` con validación *Fail-Fast* de variables críticas).
  - Se implementó la app `nucleo` con `ConfiguracionTienda` (`TBL_RCONFIGURACION_TIENDA`), `MetodoPago` (`TBL_RMETODO_PAGO`), sanitización anti-XSS (`limpiar_texto_seguro`), validadores peruanos (DNI y celular), grupo `Dueño` y docstrings obligatorios de 5 líneas en cada función.
  - Se ejecutaron migraciones, `ruff check` (`All checks passed!`) y `pytest` (`5 passed in 2.79s`, incluyendo la auditoría automática `test_estandar_bd.py` de nombres físicos `TBL_` en MAYÚSCULAS).
- **Decidido:** realizar los commits estructurados en `feature/fase-0-base` tras confirmar las pruebas.
- **Queda:** fusionar `feature/fase-0-base` en `develop`, abrir `feature/fase-1-catalogo-frontend` y construir el Catálogo + Frontend público.

## 2026-11-10 – Pruebas de carga (Grafana k6), Skills de Diseño UI y Checklist de 20 puntos «Antes de lanzar la web»
- **Hecho:**
  - Se creó `03-Diseno-Tecnico/pruebas-carga-k6/` con `LEEME.txt`, `plan-pruebas-k6.md` y el script `escenarios-base.js` definiendo cuándo usar **Grafana k6** (Fase 2 rendimiento de pedido, Fase 3 concurrencia de stock `select_for_update()` y Fase 6 pico de campaña de WhatsApp).
  - Se evaluaron e integraron en `03-Diseno-Tecnico/06-diseno-ui.md`, `05-arquitectura-stack.md` y `09-referencias-repos-librerias.md` los estándares **Taste Skill**, **Emil Kowalski + Impeccable**, **UI UX Pro Max**, **`Feature Dev`**, **`CodeReview`** y **Playwright (+ Figma MCP opcional)**.
  - Se blindó `03-Diseno-Tecnico/07-seguridad-datos.md` con los **5 pilares anti-hacking** (`Row Level Security` con script SQL en `03-Diseno-Tecnico/base-datos/scripts-bd/01_rls_seguridad_filas.sql` + aislamiento en `selectores.py`, `CORS` estricto, `Variables de entorno` con *fail-fast*, `Rate Limiting` multicapa y `Sanitización de inputs`).
  - Se organizaron los 3 videos del Hero Banner en `03-Diseno-Tecnico/assets/banners-inicio/` (`banner_1.mp4`, `banner_2.mp4`, `banner_3.mp4`) y las 5 fotos reales de la camiseta «Argentina x Messi #10» en `03-Diseno-Tecnico/assets/productos-demo/argentina-messi/` (corrigiendo sus extensiones `.jpg` y generando miniaturas de 400 px de ~25 KB y detalles de 900 px en `.webp`).
  - Se agregó la columna `PRO_NPRECIO_ANTERIOR` (`precio_anterior`) a `TBL_RPRODUCTO` (13 tablas, 134 columnas validadas) para mostrar el precio de oferta (`S/ 55.00`) junto al precio regular tachado (`S/ 69.90`) tal como vende Richard.
  - Se creó `05-Despliegue/15-checklist-antes-de-lanzar-web.md` con los **20 requisitos pre-lanzamiento** (Aviso legal, Privacidad Ley N.º 29733, Cookies, HTTPS, SEO + OpenGraph, JSON-LD, `sitemap.xml` y `robots.txt`, Ficha de Google, Favicon, texto `alt` en imágenes `IMA_CTEXTO_ALT`, WebP comprimido, velocidad, contraste, responsive móvil/desktop, `404`/`500`, verificación de enlaces rotos, Cloudflare Turnstile antispam, botón de WhatsApp visible, analítica y **una sola llamada a la acción por pantalla**).
  - Se actualizó el diccionario de datos (`generar_diccionario.py`, `.md`, `.xlsx` y `modelo-er.md`: 13 tablas, 133 columnas) y el plan por fases (`02-Planificacion/10-plan-fases.md`).
- **Decidido:** cumplir desde la Fase 1 y Fase 2 los requisitos de SEO, páginas legales, un solo CTA principal (`#39FF14`) y protección Cloudflare Turnstile para no dejar deuda técnica al final.
- **Queda:** confirmar el arranque del Plan del Frontend (maqueta interactiva / Fase 0 y Fase 1).

## 2026-11-10 – Conexión del repositorio remoto oficial en GitHub y regla permanente de DevOps
- **Hecho:**
  - Se registró `05-Despliegue/14-flujo-git-devops-github.md` (`Guia-DevOps-GitHub-Emuna-Sport.docx`) como regla obligatoria en `.agents/rules/00-emuna-proyecto.md` para todo el proyecto.
  - Se actualizó la URL oficial del repositorio (`https://github.com/jcoldsolutionsj-lab/Proyect_03EcomerceEmunaSport.git`) en el manual Markdown y en el Word.
  - Se configuró `origin` y se subieron las ramas `main` y `develop` a GitHub.
- **Decidido:** toda fase o cambio nuevo saldrá de `develop` en una rama `feature/*` siguiendo el manual DevOps.
- **Queda:** proponer y aprobar el plan de implementación de la Fase 0 y la Fase 1.

## 2026-11-03 (cierre) – Restauración del doc 05, español total, Excel de BD, cita en Lima y Swagger
- **Hecho:**
  - Se restauró el doc `05-arquitectura-stack.md` desde la carpeta `docs/` que dejó Jonathan y se archivaron los originales en `01-Relevamiento/fuentes/documentos-originales/`.
  - Se pasaron el modelo lógico, el diccionario físico y los diagramas a **español** con nombres de BD en **MAYÚSCULAS**.
  - Se creó `03-Diseno-Tecnico/base-datos/generar_diccionario.py` (fuente única con validaciones) y se generaron `diccionario-datos.md`, `diccionario-datos.xlsx` (Excel con 5 hojas y filtros) y `modelo-er.md` (13 tablas, 132 columnas).
  - Se incorporó la modalidad `PUNTO_ENCUENTRO` en Lima (entrega en mano y cobro por Yape/efectivo en el momento) y la venta `PRESENCIAL` directa en los docs 02, 03, 04 y en el nuevo diagrama `08-actividad-entrega-lima-y-venta-presencial.md`.
  - Se creó la especificación de la API y Swagger: `03-Diseno-Tecnico/13-especificacion-api-swagger.md` y `03-Diseno-Tecnico/api/openapi.yaml` (19 rutas validadas con OpenAPI 3.0.3).
  - Se creó el manual de flujo Git, ramas y DevOps con GitHub en Markdown (`05-Despliegue/14-flujo-git-devops-github.md`) y en Word (`05-Despliegue/Guia-DevOps-GitHub-Emuna-Sport.docx`), y se dejó creada la rama `develop` sincronizada con `main`.
- **Decidido:** código y BD en español; tablas/columnas en MAYÚSCULAS; docstring obligatorio de 5 preguntas en cada función.
- **Queda:** subir al remoto privado y aprobar el plan de la Fase 0 y la Fase 1.

## 2026-11-03 – Git, diagramas y estándar de base de datos
- **Hecho:** `git init` en la raíz (rama `main`) con `.gitignore` y `.gitattributes`. `LEEME.txt` en todas las carpetas. Diagramas UML de actividades y estados (Mermaid) en `01-Relevamiento/diagramas/`. Se leyó el PDF de estándares y se adaptó a Django/PostgreSQL.
- **Creado:** `03-Diseno-Tecnico/12-estandar-base-datos.md`, `base-datos/diccionario-datos.md`, `base-datos/modelo-er.md`, carpetas `base-datos/scripts` y `scripts-bd`, `estandares/` con el PDF (renombrado `estandares-area-desarrollo-2.pdf`).
- **Decidido:** un solo repositorio git en la raíz. Sin procedimientos almacenados para la lógica.

## 2026-11-03 – Orden del proyecto
- **Hecho:** se revisó la estructura inicial. Se renombraron las carpetas a `00` … `06` sin espacios ni tildes. Se repartieron los documentos 01 al 11 por propósito. Se movieron `.agents/rules/` a la raíz y el logo a `03-Diseno-Tecnico/assets/`.
- **Creado:** `ESTANDAR-ESTRUCTURA.md`, `ESTADO-ACTUAL.md` y esta bitácora.
