# 09 – Referencias: repositorios y librerías

Usar como **referencia** para no reinventar y para decidir con criterio. No copiar proyectos enteros. Las estrellas son aproximadas: verificar estrellas, última actividad y licencia antes de adoptar algo.

## 1. Para mirar cómo se modela una tienda (solo lectura de arquitectura)
| Repositorio | Estrellas aprox. | Qué mirar |
|---|---|---|
| `saleor/saleor` | ~23 mil | Cómo modelan productos, variantes, stock y pedidos. Es demasiado grande para este proyecto; solo referencia conceptual. |
| `django-oscar/django-oscar` | ~6.6 mil | Estructura de catálogo, stock y reglas de precios. Sirve para contrastar el modelo de datos. |

## 2. Para el Frontend, UI e interactividad mobile-first (Catálogo, Carrito y Panel)
| Repositorio | Estrellas aprox. | Para qué sirve en Emuná Sport |
|---|---|---|
| `alpinejs/alpine` | ~29 mil | Micro-interactividad en el navegador sin SPA: abrir/cerrar el cajón del carrito, cambiar de talla viendo el stock al instante, cambiar foto en la galería y botón «Copiar número de Yape». |
| `bigskysoftware/htmx` + `adamchainz/django-htmx` | ~40 mil / ~2.3 mil | Actualizar el carrito, el contador del encabezado y los precios por mayor directo desde Django con fragmentos HTML, sin recargar toda la página ni duplicar lógica en JavaScript. |
| `timonweb/django-tailwind` (o Tailwind Standalone CLI) | ~1.9 mil | Integración limpia de Tailwind CSS con las plantillas de Django usando la paleta de Emuná Sport (`#FFFFFF`, `#0A0A0A`, `#C9CED3`, `#39FF14`). |
| `themesberg/flowbite` | ~8 mil | Componentes Tailwind listos y accesibles para móvil: chips de categorías, modales, cajón lateral (drawer) del carrito, alertas y tablas. |
| `nolimits4web/swiper` | ~40 mil | Carrusel táctil (deslizar con el dedo en el celular) para ver las fotos de cada camiseta en la pantalla de producto. |
| `lucide-icons/lucide` | ~14 mil | Íconos SVG ligeros (carrito, WhatsApp, copiar, alerta de últimas unidades, camión de envío, punto de encuentro). |
| `unfoldadmin/django-unfold` | ~2.6 mil | Transforma el admin de Django en un panel moderno con Tailwind CSS y diseño mobile-first para que Richard gestione pedidos, stock y ventas presenciales cómodamente desde su celular. |

## 3. Para el Backend, Seguridad, PDF y API (base del proyecto)
| Repositorio | Estrellas aprox. | Para qué sirve en Emuná Sport |
|---|---|---|
| `cookiecutter/cookiecutter-django` | ~13.5 mil | Estructura de `settings` por entorno (`base`, `local`, `demo`, `production`) y cabeceras de seguridad. Usar solo como guía sin Celery ni Docker en el piloto. |
| `encode/django-rest-framework` | ~29 mil | Endpoints de `/api/v1/` reutilizando `servicios.py` y `selectores.py`. |
| `jazzband/djangorestframework-simplejwt` | ~4 mil | Tokens JWT para Richard, Jonathan y futura app móvil. |
| `tfranzel/drf-spectacular` | ~3.6 mil | Generación de esquema OpenAPI 3.0.3 y visor Swagger UI (`/api/docs/`) según `03-Diseno-Tecnico/api/openapi.yaml`. |
| `jazzband/django-simple-history` | ~2.3 mil | Historial automático de cambios en pedidos (`TBL_HPEDIDO`). |
| `jschneier/django-storages` | ~2.7 mil | Conexión con el bucket S3 de Cloudflare R2 (público para miniaturas/detalle WebP y privado para originales y boletas). |
| `evansd/whitenoise` | ~3.3 mil | Servir archivos estáticos en Render sin servidor adicional. |
| `joke2k/django-environ` | ~3.1 mil | Lectura tipada de variables de entorno (`.env`). |
| `jsocol/django-ratelimit` | ~1.7 mil | Límite de intentos en el formulario público de pedidos para evitar spam (combinado con **Cloudflare Turnstile** y campo trampa *honeypot*). |
| ReportLab + Pillow (PyPI) | — | Generación del PDF del pedido en Python puro y conversión automática de fotos a WebP (~400 px y ~900 px). |

## 4. Para Pruebas de Carga, Automatización Visual (E2E) y Calidad UI
| Repositorio / Herramienta | Estrellas aprox. | Para qué sirve en Emuná Sport |
|---|---|---|
| `grafana/k6` | ~26 mil | Pruebas de carga, picos de tráfico desde estados de WhatsApp y verificación de concurrencia en descuento atómico de stock (`select_for_update()`). Scripts en `03-Diseno-Tecnico/pruebas-carga-k6/`. |
| `microsoft/playwright` (`playwright-python`) | ~68 mil | Pruebas E2E en navegador real con resolución celular (`360×800`) y desktop (`1280×800`), detector automático de enlaces rotos y verificación de contraste/accesibilidad. |
| Principios **Taste Skill** + **Emil Kowalski / Impeccable** | — | Reglas de diseño adoptadas en `06-diseno-ui.md`: jerarquía deportiva con carácter (`Barlow Condensed` + `Inter` + `tabular-nums`), un solo CTA principal (`#39FF14`) por pantalla y micro-interacciones rápidas (`150 ms–220 ms`) sin saltos de diseño (*CLS = 0*). |

## Cómo usar esta lista
- Antes de agregar una librería nueva, revisa si ya hay una en esta lista o en el proyecto.
- Si necesitas algo que no está aquí, propón la librería con su razón, licencia y mantenimiento, y espera aprobación.
- No instales plantillas completas de tienda: se adapta la lógica de este proyecto con sus propias reglas (docs 02 y 03) y su identidad visual (doc 06).
