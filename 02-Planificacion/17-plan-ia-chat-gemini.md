# 17 – Plan Técnico de Chat Asistente IA con Gemini (Emuná Sport)

> **Estado:** Planificado para fase posterior al piloto y migración a PostgreSQL. **No implementar código de chat** hasta aprobar la normalización previa de catálogo/índices PostgreSQL y completar el despliegue base en Render.

---

## 1. Objetivo de negocio y flujo del cliente

Integrar un asistente web rápido en la tienda pública (`/`) basado en la **API de Google Gemini** para responder consultas comerciales al instante sin saturar el WhatsApp de Richard con preguntas repetitivas de stock, tallas o modalidades.

### Flujo de ejemplo (*«¿Tienen la camiseta de Portugal?»*)
1. El cliente abre el chat web (enlazado junto o dentro de la experiencia de ayuda rápida) y pregunta: *«¿Tienen la camiseta de Portugal en talla M?»*.
2. El backend consulta la **instantánea normalizada en caché / PostgreSQL** (sin volcar toda la BD ni hacer escaneos secuenciales pesados), ubica los modelos coincidentes con stock real (`cantidad_stock > 0`), precios vigentes y tramos por mayor (`TBL_RREGLA_PRECIO`), y entrega esos resultados estructurados a Gemini.
3. Gemini responde en español peruano claro, mostrando **solo productos, tallas y precios reales existentes en base de datos**, con enlace directo a la ficha `/productos/<slug>/`.
4. **Límite estricto de 5 preguntas por sesión:**
   - Preguntas **1 a 4:** respuesta directa de catálogo/tallas/precios/modalidades + contador visible (`Consulta X de 5`).
   - Pregunta **5** (o si el cliente sigue con duda sobre pedidos a medida, envíos especiales o modelos no encontrados): respuesta final + botón destacado **`💬 Continuar con Richard por WhatsApp`**, prellenando automáticamente el resumen de lo que el cliente buscó.
   - A partir de la **6.ª tentativa**, el backend rechaza llamadas nuevas a la API de Gemini (`HTTP 429` controlado en servidor) y muestra directamente el pase a WhatsApp con Richard.

---

## 2. Reglas de negocio y seguridad del asistente

1. **Tolerancia cero a alucinaciones:** Gemini nunca responde de memoria ni inventa stock, tallas, precios ni cuentas Yape. Su prompt de sistema recibe exclusivamente el subconjunto real filtrado desde Emuná Sport y la regla de indicar exactamente cuando algo está agotado o no existe.
2. **Solo datos públicos:** el chat jamás consulta ni expone `TBL_TPEDIDO`, `TBL_TENVIO`, DNI, celulares de clientes, claves de recojo de 4 dígitos ni boletas privadas. Su dominio de lectura es únicamente catálogo público disponible (`activo=True`), reglas mayoristas y modalidades generales (`02-reglas-negocio.md`).
3. **Control del límite de 5 preguntas en el servidor (no solo en el navegador):**
   - Contador en sesión Django firmada + `django-ratelimit` por IP/sesión para evitar reinicios borrando `localStorage` o manipulando JavaScript.
   - Bloqueo de longitud máxima de mensaje (`<= 300 caracteres`) y sanitización con `limpiar_texto_seguro` antes de procesarlo.
4. **Derivación obligatoria a Richard en duda o cierre:** si hay `0` coincidencias, stock crítico en disputa, consulta de envío interprovincial personalizado o al completar las **5 preguntas**, la respuesta prioriza el enlace directo `wa.me` hacia `ConfiguracionTienda.numero_whatsapp` con contexto resumido.
5. **Protección de cuota y costos de API:** timeout estricto (`<= 6 s`) hacia Gemini, modelo ligero/rápido (ej. familia Gemini Flash), `max_output_tokens` acotado y *fallback* elegante a buscador normal + WhatsApp si la API externa falla o supera cuota.

---

## 3. Diseño orientado a velocidad y cero impacto de CPU en PostgreSQL

Para que el endpoint de chat sea rápido y **no golpee el CPU del servidor PostgreSQL** en Render:

### 3.1 Estrategia de lectura en 2 niveles
1. **Nivel 1 — Caché en memoria (`LocMemCache` / Redis) invalidada por eventos (0 queries SQL por mensaje en el 95 % de consultas):**
   - Se mantiene serializado en caché un índice compacto JSON del catálogo activo (`catalogo_ia_compacto`, pocos KB) con: `id`, `nombre`, `slug`, `sku`, `equipo`, `categoria`, `palabras_clave/etiquetas`, `precio_unidad`, `precio_anterior`, `tramos_mayor` y lista de `tallas_disponibles` (`stock > 0`).
   - Cada vez que se guarda o modifica `Producto`, `Variante`, `ReglaPrecio`, `Categoria`, `Equipo` o `MovimientoStock`, un servicio/señal invalida la clave de caché (`transaction.on_commit`).
   - Al preguntar *«¿Tienes Portugal?»*, Python filtra el resumen cacheado en memoria (`< 1 ms`, **0 conexiones a PostgreSQL**) o selecciona únicamente los Top-5 candidatos para enviarlos en el contexto de Gemini.
2. **Nivel 2 — Consultas indexadas en PostgreSQL (cuando hay miss de caché o búsqueda puntual):**
   - Uso exclusivo de columnas normalizadas e índices B-Tree/GIN parciales (`WHERE active = true` y `WHERE stock > 0`), prohibido `SELECT *` o `SUM()` repetitivo sin filtro en tiempo real durante conversaciones.
   - Uso de `select_related` y `only(...)` para traer solo campos de lectura pública.

### 3.2 Preparación estructural previa en BD (ver análisis previo a migración PostgreSQL)
Antes o durante el pase a PostgreSQL, se recomienda dejar normalizados en `catalogo` (cumpliendo `12-estandar-base-datos.md`):
- Entidad/atributos estructurados de búsqueda (`TBL_REQUIPO` o atributos normalizados de equipo/edición + `TBL_RETIQUETA` / `TBL_RPRODUCTO_ETIQUETA` para sinónimos como *Portugal / CR7 / Luso*).
- Índices parciales en `TBL_RPRODUCTO` y `TBL_RVARIANTE` + soporte trigrama (`pg_trgm` / `GinIndex`) en PostgreSQL para búsquedas con errores tipográficos sin *Sequential Scan*.
- Tablas futuras (solo cuando se apruebe implementar esta fase): `TBL_TCONVERSACION_IA` (`CON_NID`, sesión, conteo de preguntas `1..5`, derivada a WhatsApp) y `TBL_TMENSAJE_IA` (`MEN_NID`, rol, consulta normalizada, encontró resultados `O`) para que Richard sepa qué camisetas piden los clientes y no tiene en stock.

---

## 4. Fases sugeridas cuando toque implementar este módulo

1. **Subfase IA-1 — Backend de contexto y caché del catálogo:** constructor de instantánea compacta + buscador tolerante con pruebas unitarias (`pytest`, 0 queries N+1).
2. **Subfase IA-2 — Cliente Gemini + límite de 5 preguntas:** servicio aislado (`apps/asistente/servicios.py`), variable `GEMINI_API_KEY` fail-safe, control de 5 turnos en sesión/BD, `ratelimit` y pase automático a WhatsApp.
3. **Subfase IA-3 — Widget flotante móvil/web + analítica para Richard:** cajón ligero integrado en tienda pública sin afectar *CLS = 0* ni LCP, y reporte simple en Tablero sobre «Búsquedas sin stock».
