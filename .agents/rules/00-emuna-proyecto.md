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
- **Idioma:** Todo el código propio (apps, clases, funciones, variables, campos, URLs y constantes de estado) va en **español** (`catalogo`, `pedidos`, `Producto`, `cambiar_estado`). Solo conservan su nombre en inglés los métodos propios de Django (`save`, `clean`, `get_queryset`, `Meta`).
- **Docstring obligatorio en cada función y método propio** (breve, respondiendo estas 5 líneas):
  ```python
  """Resumen de una línea.

  Qué hace:      Qué realiza la función.
  Va hacia:      Qué devuelve o qué tabla/estado modifica.
  Depende de:    De qué modelos, servicios o datos depende.
  Cuándo usarla: Quién la llama y en qué caso.
  Si no opera:   Qué excepción lanza o qué ocurre si falla.
  """
  ```
- Lógica de negocio solo en `servicios.py` (escrituras) y `selectores.py` (lecturas). Las vistas, serializers, templates y el admin son delgados y llaman a servicios.
- No dupliques lógica: si dos lugares necesitan lo mismo, crea una función compartida.
- El stock solo cambia mediante `MovimientoStock` creado por un servicio, dentro de una transacción. Nunca edites `cantidad_stock` a mano en el código.
- El estado de un pedido solo cambia mediante `pedidos.servicios.cambiar_estado()`, que valida la transición (ver `01-Relevamiento/03-flujo-pedidos-estados.md`).
- `ItemPedido` guarda una copia (snapshot) del nombre, la talla y el precio en el momento de la compra. Nunca recalcules pedidos viejos con precios nuevos.
- Dinero: `Decimal`, soles peruanos (PEN), 2 decimales. Zona horaria `America/Lima`.
- Nada de secretos en el repositorio: todo por variables de entorno. No hagas commit del QR de Yape, boletas, DNI ni datos reales de clientes.
- El DNI del cliente y la clave de recojo del envío son datos privados: nunca en URLs, logs, páginas públicas ni mensajes de error.
- Cada cambio de modelo lleva su migración. Cada servicio lleva pruebas (`pytest`). Formato y lint con `ruff`.
- **Blindaje Anti-Hacking (5 pilares obligatorios en doc 07):**
  1. **Row Level Security / Aislamiento de filas:** ninguna ruta pública usa IDs numéricos secuenciales (`1, 2, 3`); solo `PED_CCODIGO` aleatorio mediante un selector público que excluye DNI, teléfono y `clave_recojo`, más políticas RLS en PostgreSQL (`01_rls_seguridad_filas.sql`).
  2. **CORS estricto:** `CORS_ALLOW_ALL_ORIGINS = False` siempre; solo orígenes en lista blanca por entorno.
  3. **Variables de entorno blindadas:** cero claves en código; fallo inmediato al arrancar (*fail-fast*) si falta una variable crítica en `demo`/`production`.
  4. **Rate Limiting multicapa:** `django-ratelimit` + Throttling DRF + Cloudflare Turnstile en checkout, consulta de pedidos y login.
  5. **Sanitización de Inputs:** limpiar HTML (`strip_tags`), validar DNI (`^\d{8}$`) y celular (`^9\d{8}$`), **recalcular precios siempre en el servidor**, ORM parametrizado (anti-SQLi) y recodificación de imágenes con Pillow a WebP.
- **Metodología `Feature Dev` y auditoría `CodeReview` (doc 05):** cada funcionalidad sigue los 6 pasos de `Feature Dev` y antes de hacer commit/merge pasa por el checklist `CodeReview` del doc 05.
- Base de datos: nombres físicos en **MAYÚSCULAS y en español** según `03-Diseno-Tecnico/12-estandar-base-datos.md` y `03-Diseno-Tecnico/base-datos/diccionario-datos.md` (`db_table` y `db_column` en cada modelo). Si cambia un modelo, actualiza `generar_diccionario.py` y ejecútalo. Sin cursores; la lógica no va en procedimientos almacenados.

## Convenciones
- Interfaz en español de Perú. Mobile-first (`360 px` y adaptable a desktop `1280 px+`): la mayoría de clientes entra desde WhatsApp en el celular.
- **Estándar Frontend, Conversión y Pre-lanzamiento (docs 06 y 15):**
  - Aplicar jerarquía deportiva (**Taste Skill**: `Barlow Condensed` + `Inter` + `tabular-nums`), micro-interacciones rápidas (`150 ms–220 ms`, **Emil Kowalski / Impeccable**) y heurísticas de conversión e-commerce móvil (**UI UX Pro Max**: barra inferior fija en producto, tabla de ahorro por mayor e indicadores reales de stock) sin saltos de pantalla (*CLS = 0*, `aspect-ratio: 4/5`).
  - **Una sola llamada a la acción (CTA) principal en verde neón (`#39FF14` con texto `#0A0A0A`) por pantalla.**
  - Cumplir desde las fases 1 y 2 los 20 requisitos de `05-Despliegue/15-checklist-antes-de-lanzar-web.md` (páginas `/aviso-legal/`, `/privacidad/` Ley N.º 29733 y `/cookies/`, SEO + JSON-LD + OpenGraph, `sitemap.xml`, `robots.txt`, favicon, `alt` en imágenes WebP, `404.html`/`500.html`, botón de WhatsApp visible, Cloudflare Turnstile antispam, pruebas E2E con Playwright y pruebas de carga/concurrencia con Grafana k6 en `03-Diseno-Tecnico/pruebas-carga-k6/`).
- La marca (`marca`) del producto está apagada por defecto. No muestres marcas ni nombres de clubes en el catálogo salvo que el producto lo tenga configurado.
- Cambios de reglas de negocio: actualiza primero el documento correspondiente y agrega una línea en `00-Gestion/11-decisiones-cambios.md`.
- Cada carpeta nueva lleva un `LEEME.txt`. Los diagramas del negocio están en `01-Relevamiento/diagramas/` y el contrato de la API en `03-Diseno-Tecnico/api/`: si cambia un flujo o un endpoint, actualízalos.
- **Flujo Git y DevOps (obligatorio en todo el proyecto):** sigue siempre `05-Despliegue/14-flujo-git-devops-github.md` (`Guia-DevOps-GitHub-Emuna-Sport.docx`). `main` es Producción, `develop` es Integración/Demo, y cada fase o cambio se trabaja en su rama `feature/*`, `bugfix/*`, `release/*` o `hotfix/*` con mensajes de commit en español (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Remoto oficial: `https://github.com/jcoldsolutionsj-lab/Proyect_03EcomerceEmunaSport.git`.
