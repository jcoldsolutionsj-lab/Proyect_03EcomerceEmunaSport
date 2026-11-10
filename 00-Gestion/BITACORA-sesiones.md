# Bitácora de sesiones

Una entrada breve por sesión de trabajo, la más reciente **arriba**. Cada entrada responde: qué se hizo, qué se decidió, qué queda.

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
