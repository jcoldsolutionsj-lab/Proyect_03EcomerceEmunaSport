# 15 – Checklist integral «Antes de lanzar la web» (20 puntos obligatorios)

Este documento reúne los **20 puntos obligatorios de calidad, legalidad, SEO, seguridad, rendimiento y conversión** que debe cumplir la tienda de **Emuná Sport** antes de su lanzamiento oficial, indicando **en qué fase se construye cada uno** y **cómo se implementa y verifica en Django**.

---

## Mapa rápido por áreas y fases

| N.º | Requisito | Área | Fase donde se implementa | Cómo se verifica |
|---|---|---|---|---|
| **1** | Aviso legal (Términos y condiciones) | Legal (Perú) | Fase 1 (plantilla base y pie) | Ruta `/aviso-legal/` responde `200` y está enlazada en el pie y checkout |
| **2** | Política de privacidad (Ley N.º 29733) | Legal y Datos | Fase 1 y Fase 2 (checkout) | Ruta `/privacidad/` + casilla/aviso en el formulario de pedido |
| **3** | Aviso de cookies | Legal y Privacidad | Fase 1 | Ruta `/cookies/` + aviso discreto de cookies de sesión/carrito |
| **4** | Forzar HTTPS | Seguridad | Fase 0 (settings) + Fase 5/6 (Cloudflare) | `SECURE_SSL_REDIRECT=True`, HSTS y «Always Use HTTPS» en Cloudflare |
| **5** | Meta títulos y descripciones (+ OpenGraph) | SEO y WhatsApp | Fase 1 | Cada página tiene `<title>`, `<meta name="description">` y `og:image` únicos |
| **6** | Datos estructurados (Schema.org JSON-LD) | SEO | Fase 1 | Bloques JSON-LD `Organization`, `Product` (con `PEN` y stock) y `BreadcrumbList` |
| **7** | `sitemap.xml` y `robots.txt` | SEO y Privacidad | Fase 1 | `/sitemap.xml` lista productos activos; `/robots.txt` bloquea `/gestion/` y `/pedidos/` |
| **8** | Ficha de Google (Google Business + Search Console) | Presencia local | Fase 6 (con dominio oficial) | Ficha verificada en Lima y `sitemap.xml` enviado a Search Console |
| **9** | Favicon completo | Identidad de marca | Fase 1 | `favicon.ico`, `icon.svg`, `apple-touch-icon.png` y `site.webmanifest` |
| **10** | Texto alternativo (`alt`) en las imágenes | Accesibilidad y SEO | Fase 1 | Campo `IMA_CTEXTO_ALT` (`texto_alternativo`) con respaldo automático por producto |
| **11** | Imágenes comprimidas (WebP) | Rendimiento | Fase 1 | Conversión automática con Pillow a WebP (~400 px miniatura y ~900 px detalle) |
| **12** | Velocidad de carga optimizada | Rendimiento | Fase 1 y Fase 6 | `loading="lazy"`, `fetchpriority="high"` en LCP, `aspect-ratio: 4/5`, WhiteNoise + CDN |
| **13** | Contraste de colores accesible (WCAG AA) | Diseño / UI | Fase 1 | Verde neón `#39FF14` siempre con texto negro `#0A0A0A` (ratio > 12:1) |
| **14** | Que se vea bien en móvil y desktop | Diseño Responsive | Fase 1 y Fase 2 | Probado en `360×800` (celular) y `1280×800` (desktop) con Playwright |
| **15** | Página `404` (y `500`) personalizada | Experiencia (UX) | Fase 1 | `templates/404.html` y `500.html` con retorno al catálogo y botón de WhatsApp |
| **16** | Enlaces rotos arreglados | Calidad | Fase 1 a Fase 6 | Test automático con `pytest` / Playwright que recorre todos los enlaces internos |
| **17** | Formularios protegidos contra spam (Cloudflare) | Seguridad | Fase 2 y Fase 6 | Triple protección: **Cloudflare Turnstile** + `django-ratelimit` + campo trampa (*honeypot*) |
| **18** | Botón de WhatsApp visible | Conversión | Fase 1 y Fase 2 | Botón visible y contextual con mensaje prellenado hacia el número de Richard |
| **19** | Analítica instalada | Medición | Fase 1 (base) y Fase 6 (activa) | Variable `GA4_MEASUREMENT_ID` / Cloudflare Web Analytics con eventos de embudo |
| **20** | Una sola llamada a la acción (CTA) por pantalla | Conversión UI | Fase 1 y Fase 2 | Un único botón primario `#39FF14` por pantalla; acciones secundarias en borde plata |

---

## Detalle técnico de los 20 puntos

### Bloque A – Legalidad y confianza del comprador en Perú (Puntos 1, 2 y 3)
1. **Aviso legal (`/aviso-legal/`):**
   - Explica de forma clara y cercana quién opera Emuná Sport, cómo funciona el pedido web, que el costo de envío a provincia (Shalom/Olva) o delivery en Lima se confirma antes del pago, y las condiciones de cambios por talla.
2. **Política de privacidad (`/privacidad/` – Ley N.º 29733 de Protección de Datos Personales):**
   - Detalla que el **nombre, DNI (8 dígitos) y teléfono celular** se solicitan única y exclusivamente para coordinar el pedido y registrar el envío en la agencia de transporte (Shalom u Olva exigen DNI para entregar la encomienda).
   - Incluye en el formulario de pedido (Fase 2) una casilla de aceptación explícita y un enlace directo a `/privacidad/`.
3. **Aviso de cookies (`/cookies/`):**
   - Explica que la tienda utiliza cookies técnicas de sesión necesarias para guardar el carrito de compras sin obligar al cliente a registrarse y para proteger los formularios (`csrftoken`), más analítica anónima si está activa.
   - Se muestra una barra discreta en la parte inferior en la primera visita con el botón «Entendido», que no tapa el catálogo ni molesta la compra.

### Bloque B – Seguridad y protección contra bots/spam (Puntos 4 y 17)
4. **Forzar HTTPS:**
   - En `config/settings/production.py` y `demo.py`: `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_HSTS_SECONDS = 31536000`, `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`.
   - En Cloudflare: regla **Always Use HTTPS** activa.
17. **Formularios protegidos contra spam (Cloudflare Turnstile + Ratelimit + Honeypot):**
   - **Capa 1 – Cloudflare Turnstile:** widget gratuito e invisible/sin acertijos molestos en el formulario de creación de pedido, validado en el servidor (`pedidos/servicios.py`) contra la API de Cloudflare usando `TURNSTILE_SECRET_KEY` (en local o tests usa las llaves de prueba oficiales de Cloudflare).
   - **Capa 2 – `django-ratelimit`:** máximo de envíos de pedido por IP por minuto para frenar ataques automatizados.
   - **Capa 3 – Campo trampa (*honeypot*):** campo oculto `sitio_web` en el formulario; si un bot lo llena, el pedido se descarta silenciosamente sin tocar la base de datos.

### Bloque C – SEO, WhatsApp Preview y presencia en Google (Puntos 5, 6, 7, 8 y 9)
5. **Meta títulos y descripciones (+ OpenGraph para WhatsApp):**
   - `base.html` define bloques `meta_titulo`, `meta_descripcion` y etiquetas OpenGraph (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`).
   - Cuando Richard o un cliente pega el enlace de una camiseta en WhatsApp, aparece automáticamente la tarjeta con la **foto en WebP, el nombre de la camiseta y su precio en soles (`S/ 45.00`)**.
6. **Datos estructurados (Schema.org en JSON-LD):**
   - En la portada: `Organization` / `SportingGoodsStore` con el nombre «Emuná Sport», logo y contacto de WhatsApp.
   - En cada ficha de producto: `Product` con `sku`, imágenes, `offers` (`priceCurrency: "PEN"`, `price`, `availability` automática en `https://schema.org/InStock` o `OutOfStock` según la suma de stock de sus tallas) y `BreadcrumbList`.
7. **`sitemap.xml` y `robots.txt`:**
   - `/sitemap.xml` generado dinámicamente con `django.contrib.sitemaps` incluyendo inicio, categorías activas, productos activos y páginas legales.
   - `/robots.txt` servido por Django:
     - **Permite (`Allow`):** `/`, `/categorias/`, `/productos/`.
     - **Bloquea (`Disallow`):** `/gestion/`, `/carrito/`, `/pedidos/`, `/api/` (así ningún buscador indexa jamás los enlaces de pedidos con código ni el panel de Richard).
8. **Ficha de Google (Google Business Profile + Google Search Console):**
   - Al activar el dominio en la Fase 6, se verifica el dominio en **Google Search Console** por registro DNS en Cloudflare, se envía `/sitemap.xml` y se enlaza la ficha de **Google Perfil de Negocio** de Emuná Sport (con botón a la web y al WhatsApp de Richard).
9. **Favicon e íconos de dispositivo:**
   - Generados a partir de `03-Diseno-Tecnico/assets/logo-emuna-sport.png` (el rayo «E» en verde neón `#39FF14` sobre fondo negro `#0A0A0A`): `favicon.ico` (32×32), `icon.svg`, `apple-touch-icon.png` (180×180 para iPhone) y `site.webmanifest` (con `theme_color: "#0A0A0A"` para que la barra del navegador móvil se vea negra deportiva).

### Bloque D – Imágenes, velocidad, diseño y calidad técnica (Puntos 10, 11, 12, 13, 14, 15 y 16)
10. **Texto alternativo (`alt`) en todas las imágenes:**
    - `TBL_RIMAGEN_PRODUCTO` incluye la columna `IMA_CTEXTO_ALT` (`texto_alternativo`, opcional). Si Richard no escribe uno al subir la foto, el modelo devuelve automáticamente `"{producto.nombre} – Estilo deportivo Emuná Sport (Foto {orden})"`. Ninguna etiqueta `<img>` sale con `alt=""` vacío en productos.
11. **Imágenes comprimidas en WebP:**
    - Al guardar una `ImagenProducto`, un servicio con Pillow valida el archivo, guarda el original en el bucket privado y genera automáticamente dos versiones comprimidas en **WebP** (`quality=82`): miniatura de ~400 px (`< 40 KB`) para las tarjetas del catálogo y detalle de ~900 px (`< 110 KB`) para la ficha del producto.
12. **Velocidad de carga optimizada:**
    - Imágenes del catálogo con `loading="lazy"` y `decoding="async"`; primera imagen del producto con `fetchpriority="high"`.
    - Contenedores de fotos con proporción fija `aspect-ratio: 4/5` para evitar saltos de diseño (*CLS = 0*).
    - Consultas optimizadas en `selectores.py` con `select_related` y `prefetch_related` (cero problema N+1).
    - Pruebas de rendimiento y concurrencia con **Grafana k6** (`03-Diseno-Tecnico/pruebas-carga-k6/`).
13. **Contraste de colores accesible:**
    - Cumplimiento estricto de `03-Diseno-Tecnico/06-diseno-ui.md`: el verde neón `#39FF14` solo se usa como fondo de botón con texto negro `#0A0A0A` (contraste `13.4:1`, nivel AAA). Sobre fondo blanco `#FFFFFF`, los textos de acento usan verde oscuro `#1B8F2A`.
14. **Diseño adaptable (móvil y desktop):**
    - *Mobile-first* desde `360 px` de ancho (botones táctiles de mínimo `48 px` de alto, cuadrícula de 2 columnas en celular y 4 en escritorio, barra fija inferior de compra en celular).
15. **Página `404` (y `500`) personalizada:**
    - Plantillas `404.html` y `500.html` con la estética de Emuná Sport («Esta jugada salió fuera de la cancha»), botón principal «Ver catálogo de camisetas» y enlace directo al WhatsApp de Richard.
16. **Enlaces rotos arreglados / verificados:**
    - Suite de pruebas automáticas (`pytest` + Playwright) que recorre todas las vistas públicas, menú, pie de página y tarjetas del catálogo comprobando que ningún enlace interno devuelva `404` o `500`.

### Bloque E – Conversión y analítica (Puntos 18, 19 y 20)
18. **Botón de WhatsApp visible y contextual:**
    - Visible en toda la tienda pública con un mensaje adaptado a lo que el cliente está viendo:
      - En catálogo/inicio: *«Hola Richard, vengo de la web de Emuná Sport y quiero consultar por las camisetas»*.
      - En ficha de producto: *«Hola Richard, me interesa la camiseta [Nombre] ([SKU]), ¿tienes disponible en talla [Talla]?»*.
      - En pedido creado / cotizado: *«Hola Richard, acabo de registrar mi pedido #[CODIGO] en la web de Emuná Sport»*.
19. **Analítica instalada:**
    - Integración ligera configurable por variable de entorno (`GA4_MEASUREMENT_ID` o `CLOUDFLARE_BEACON_TOKEN`) que no bloquea la carga de la página y registra los eventos clave del embudo: visita al catálogo, vista de camiseta, clic en agregar al carrito, pedido generado y clic en WhatsApp.
20. **Una sola llamada a la acción (CTA) principal por pantalla:**
    - Regla de oro en `06-diseno-ui.md`: cada pantalla tiene **un único botón primario en verde neón `#39FF14`** que guía al usuario al siguiente paso del flujo sin distracciones:
      - En **Producto**: `Agregar al carrito` (`#39FF14`).
      - En **Carrito**: `Continuar con mis datos` (`#39FF14`).
      - En **Checkout**: `Confirmar y generar pedido` (`#39FF14`).
      - En **Pedido enviado**: `Enviar pedido a Richard por WhatsApp` (`#39FF14`), mientras que `Descargar PDF` va como botón secundario con borde plata (`#C9CED3`).
      - En **Pedido cotizado (pago)**: `Ya yapeé – Enviar comprobante por WhatsApp` (`#39FF14`).
