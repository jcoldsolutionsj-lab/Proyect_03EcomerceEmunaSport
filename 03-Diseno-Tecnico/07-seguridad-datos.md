# 07 – Seguridad, datos personales y blindaje anti-hacking

## 1. Datos sensibles (Ley N.º 29733 – Perú)
- **DNI, teléfono, nombre, dirección/punto de encuentro y agencia** del cliente: visibles solo para el personal en el panel (`/gestion/`). Nunca en URLs, logs, mensajes de error, correos ni páginas públicas.
- **Clave de 4 dígitos de recojo (`ENV_CCLAVE_RECOJO`) y foto de boleta (`ENV_CIMAGEN_BOLETA`):** solo personal; la foto vive en el bucket privado con enlaces firmados de corta duración (`<= 10 minutos`).
- **Páginas legales públicas (`/aviso-legal/`, `/privacidad/` y `/cookies/`):** explican que los datos se usan únicamente para gestionar el pedido y el despacho en Shalom/Olva. El checkout exige aceptar la política de privacidad.
- **`/robots.txt`:** bloquea explícitamente `/gestion/`, `/carrito/`, `/pedidos/` y `/api/` para que ningún buscador indexe pedidos ni rutas internas.

---

## 2. Los 5 pilares de blindaje anti-hacking en Emuná Sport

### Pilar 1 – Row Level Security (RLS) y aislamiento a nivel de fila
En Emuná Sport aplicamos aislamiento a nivel de fila en **dos capas complementarias**:
1. **En la capa de datos de Django (`selectores.py` – activa siempre):**
   - El navegador jamás se conecta directo a la base de datos.
   - Ninguna ruta pública recibe IDs numéricos secuenciales (`1, 2, 3...`), evitando ataques **IDOR (Insecure Direct Object Reference)**. Los pedidos públicos solo se consultan mediante `PED_CCODIGO` aleatorio de alta entropía (ej. `EMU-8F9K2M4P`).
   - El selector público `obtener_pedido_publico_por_codigo(codigo)` devuelve únicamente una proyección segura (estado, ítems, subtotal, envío, total y datos de pago Yape cuando está `COTIZADO`), **excluyendo por código** el DNI, el teléfono completo y la clave de recojo.
   - Los selectores administrativos exigen siempre `usuario.is_staff` y pertenencia al grupo `Dueño` o superusuario.
2. **En PostgreSQL de producción (`ENABLE ROW LEVEL SECURITY`):**
   - El script [`03-Diseno-Tecnico/base-datos/scripts-bd/01_rls_seguridad_filas.sql`](file:///d:/JONATHAN/Proyectos/EcomerceEmunaSport/03-Diseno-Tecnico/base-datos/scripts-bd/01_rls_seguridad_filas.sql) activa `ROW LEVEL SECURITY` sobre las tablas críticas (`TBL_TPEDIDO`, `TBL_TPEDIDO_ITEM`, `TBL_LPEDIDO_ESTADO`, `TBL_TENVIO`, `TBL_TMOVIMIENTO_STOCK`).
   - Así, si en el futuro se conecta un usuario de base de datos de solo lectura, auditoría o herramienta externa, PostgreSQL bloquea a nivel de motor cualquier fila que no cumpla la política de sesión (`app.rol_actual` / `app.codigo_pedido_actual`).

### Pilar 2 – CORS estricto (`django-cors-headers`)
- **`CORS_ALLOW_ALL_ORIGINS = False` siempre** (está terminantemente prohibido usar `*` en producción o demo).
- Las vistas HTML + HTMX corren bajo el mismo dominio (*Same-Origin Policy*) con protección `CSRF` activa (`CsrfViewMiddleware`).
- Para `/api/v1/`, solo se aceptan orígenes declarados explícitamente en las variables de entorno `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS` (únicamente el dominio oficial de Emuná Sport), permitiendo solo los métodos HTTP necesarios (`GET`, `POST`, `PATCH`, `OPTIONS`).

### Pilar 3 – Variables de entorno blindadas (`django-environ`)
- **Cero secretos en el código fuente:** `SECRET_KEY`, `DATABASE_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `TURNSTILE_SECRET_KEY` y credenciales se leen exclusivamente desde variables de entorno.
- **Fallo seguro al arrancar (*Fail-Fast*):** en `demo.py` y `production.py`, si falta una variable obligatoria o si `DEBUG` intenta quedar en `True` en producción, Django detiene el arranque inmediatamente con un error explícito.
- `.env` está bloqueado en `.gitignore` y el repositorio solo incluye `.env.example` con nombres de variables vacíos.

### Pilar 4 – Rate Limiting multicapa (anti-fuerza bruta, anti-spam y anti-scraping)
Se combina **`django-ratelimit`** en vistas web, **Throttling de DRF** en la API y **Cloudflare Turnstile + WAF** en el borde:

| Ruta / Acción | Límite máximo | Qué ataque evita |
|---|---|---|
| `POST /pedidos/crear/` (Checkout) | `5/min` y `20/hora` por IP + **Cloudflare Turnstile** + *honeypot* | Bots llenando pedidos falsos o agotando la base de datos |
| `GET /pedidos/<codigo>/` (Ver pedido) | `15/min` por IP | Fuerza bruta intentando adivinar códigos `PED_CCODIGO` |
| `POST /gestion/login/` y `/api/v1/auth/token/` | `5/min` por IP y usuario | Ataques de diccionario contra las claves de Richard o Jonathan |
| `GET /api/v1/catalogo/*` | `60/min` por IP anónima (`AnonRateThrottle`) | Scraping masivo del catálogo y precios |
| `POST` en acciones del panel | `30/min` por usuario autenticado (`UserRateThrottle`) | Clics duplicados o scripts automatizados |

### Pilar 5 – Sanitización y validación estricta de Inputs (Cero confianza en el cliente)
Todo dato que entra desde el navegador o la API se considera no confiable y pasa por **3 filtros** (Formulario/Serializer → Validador de dominio → Servicio):
1. **Limpieza contra XSS (Cross-Site Scripting):**
   - En todos los campos de texto libre (`cliente_nombre`, `agencia_ciudad`, `agencia_referencia`, `punto_encuentro`, `notas`), se recortan espacios (`strip`), se eliminan etiquetas HTML o scripts (`django.utils.html.strip_tags`) antes de guardar y las plantillas de Django mantienen el auto-escape activo (prohibido usar `|safe` con datos de usuarios).
2. **Validación por formato exacto (Allowlist):**
   - `cliente_dni`: solo 8 dígitos numéricos exactos (`^\d{8}$`).
   - `cliente_telefono`: solo celular peruano de 9 dígitos que inicia en `9` (`^9\d{8}$`).
   - `cantidad`: entero positivo (`1 <= cantidad <= stock_actual`).
3. **Integridad de precios (anti-manipulación de carrito):**
   - El backend **jamás lee precios, descuentos ni totales desde el request del navegador**. El navegador solo envía `(variante_id, cantidad)` y `pedidos/servicios.py` calcula el precio real consultando `TBL_RPRODUCTO` y `TBL_RREGLA_PRECIO` en el servidor.
4. **Protección contra Inyección SQL (SQLi):**
   - Todas las consultas usan el ORM de Django con parámetros ligados. Está prohibido concatenar variables en SQL crudo.
5. **Sanitización de archivos subidos (fotos de productos y boletas):**
   - Se valida el tipo real del archivo abriéndolo con `Pillow` (`Image.verify()`), no solo por su extensión.
   - Se bloquean formatos ejecutables o vectoriales con scripts (`.svg`, `.html`, `.php`, `.exe`), se limita el peso a `5 MB` y la imagen se recodifica íntegramente a **WebP**, destruyendo cualquier código malicioso oculto en metadatos EXIF.

---

## 3. Accesos, respaldos y evidencia
- Admin en ruta no obvia (`/gestion/`), contraseñas fuertes y segundo factor (`django-otp`) en producción.
- El stock solo se modifica dentro de `transaction.atomic()` con bloqueo de fila `select_for_update()`.
- Respaldo automático de PostgreSQL en producción, historial de cambios en pedidos (`TBL_HPEDIDO`) y bitácora inmutable de stock (`TBL_TMOVIMIENTO_STOCK`) y de estados (`TBL_LPEDIDO_ESTADO`).
