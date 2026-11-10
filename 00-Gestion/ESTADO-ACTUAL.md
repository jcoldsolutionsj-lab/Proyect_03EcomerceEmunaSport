# Estado actual del proyecto

> La IA lee este archivo al empezar cada sesión y lo actualiza al terminar. Mantenerlo corto.

**Última actualización:** 2026-11-10
**Fase actual:** **Fase 0 – Base del proyecto** en rama `feature/fase-0-base` (creada desde `develop`). Plan propuesto, esperando confirmación para escribir el código en `04-Desarrollo/`.

## Dónde quedamos
- Documentos **01 al 15** completos y alineados; copia intacta de los originales en `01-Relevamiento/fuentes/documentos-originales/`.
- Reglas confirmadas: **código y base de datos en español**, nombres físicos en **MAYÚSCULAS** (`TBL_`), y **docstring de 5 líneas** en cada función.
- Flujo de **cita en punto de encuentro en Lima con pago Yape al momento** y **venta presencial directa** incorporados en reglas (doc 02), estados (doc 03), modelo (doc 04), diagramas (`00` al `08`) y API.
- Diccionario de datos validado (**13 tablas, 134 columnas**, incluyendo `PRO_NPRECIO_ANTERIOR` para precio regular tachado `S/ 69.90` e `IMA_CTEXTO_ALT` para SEO `alt`) generado en Markdown y Excel (`03-Diseno-Tecnico/base-datos/diccionario-datos.xlsx`).
- Contrato OpenAPI 3.0.3 / Swagger validado (19 rutas) en `03-Diseno-Tecnico/api/openapi.yaml` y explicado en el doc 13.
- **Pruebas de carga y concurrencia con Grafana k6** definidas por fase en `03-Diseno-Tecnico/pruebas-carga-k6/` (`plan-pruebas-k6.md` y `escenarios-base.js`).
- **Estándares de Diseño Frontend (Taste Skill + Emil Kowalski/Impeccable + UI UX Pro Max + Playwright)**, **metodologías `Feature Dev` y `CodeReview`** (doc 05), **5 pilares anti-hacking (`RLS`, `CORS`, `Variables de Entorno`, `Rate Limiting`, `Sanitización de Inputs`)** (doc 07 y `01_rls_seguridad_filas.sql`) y **Checklist de 20 puntos «Antes de lanzar la web»** (doc 15) documentados y activos en las reglas.
- **Recursos visuales reales organizados en `03-Diseno-Tecnico/assets/`:**
  - `banners-inicio/`: `banner_1.mp4`, `banner_2.mp4` y `banner_3.mp4` listos para el Hero Banner del Home.
  - `productos-demo/argentina-messi/`: 5 fotos reales de «Argentina x Messi #10» (`S/ 55.00` / antes `S/ 69.90`, tallas `S, M, L, XL`) corregidas en `originales/*.jpg` y convertidas a `webp/*.webp` (400 px y 900 px).
  - `referencias-marca/plantilla-base-figma/`: 5 capturas de referencia del layout UI aprobadas con los 6 ajustes deportivos de Emuná Sport.
- Manual de flujo Git y DevOps con GitHub en Markdown (`05-Despliegue/14-flujo-git-devops-github.md`) y Word (`05-Despliegue/Guia-DevOps-GitHub-Emuna-Sport.docx`); remoto oficial configurado y ramas `main`, `develop` y `feature/fase-0-base` sincronizadas.
- Aún **no hay código de la aplicación**. `04-Desarrollo/` solo tiene su `LEEME.txt`.

## En curso
- **Fase 0 (`feature/fase-0-base`):** Plan de implementación paso a paso propuesto; esperando aprobación de Jonathan para empezar a escribir el código en `04-Desarrollo/`.

## Siguiente paso
1. Aprobar el plan de la **Fase 0** para construir la base en `feature/fase-0-base`, cerrarla hacia `develop` y abrir enseguida `feature/fase-1-catalogo-frontend`.

## Bloqueos y pendientes con Richard
Ver los 7 puntos de negocio en `00-Gestion/11-decisiones-cambios.md` (no bloquean la Fase 0 ni la Fase 1).

## Datos que aún faltan
- QR de Yape y titular de la cuenta (Richard lo entregará; se sube desde el panel, nunca al repositorio).
