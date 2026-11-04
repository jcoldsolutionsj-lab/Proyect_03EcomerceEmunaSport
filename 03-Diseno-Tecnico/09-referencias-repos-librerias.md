# 09 – Referencias: repositorios y librerías

Usar como **referencia** para no reinventar y para decidir con criterio. No copiar proyectos enteros. Las estrellas son aproximadas: verificar estrellas, última actividad y licencia antes de adoptar algo.

## Para mirar cómo se modela una tienda (solo lectura)
| Repositorio | Aprox. | Qué mirar |
|---|---|---|
| `saleor/saleor` | ~23 mil estrellas | Cómo modelan productos, variantes, stock y pedidos. Es demasiado grande para este proyecto |
| `django-oscar/django-oscar` | ~6.6 mil estrellas | Estructura de catálogo, partners, stock y ofertas. También pesado; sirve para contrastar el modelo de datos |

## Para la base del proyecto
| Repositorio | Aprox. | Para qué |
|---|---|---|
| `cookiecutter/cookiecutter-django` | ~13.5 mil estrellas | Estructura de settings, seguridad y despliegue. Se puede usar con opciones mínimas o solo como guía; evitar Celery y Docker en el piloto si no se necesitan |
| `encode/django-rest-framework` | ~29 mil estrellas | API de la fase posterior |
| `jazzband/djangorestframework-simplejwt` | ~4 mil estrellas | Tokens JWT para personal y app futura |
| `jazzband/django-simple-history` | — | Historial de cambios de pedidos y envíos |
| `jschneier/django-storages` | — | Conectar el bucket de Cloudflare R2 (API S3) |
| `evansd/whitenoise` | — | Servir estáticos en Render |
| `joke2k/django-environ` | — | Variables de entorno |
| `jsocol/django-ratelimit` | — | Límite de intentos en el pedido público |
| `tfranzel/drf-spectacular` | — | Documentación de la API |
| `unfoldadmin/django-unfold` | — | Admin más cómodo en celular (opcional, Fase 5) |
| ReportLab (paquete PyPI) | — | Generar el PDF del pedido en Python puro |

## Cómo usar esta lista
- Antes de agregar una librería nueva, revisa si ya hay una en esta lista o en el proyecto.
- Si necesitas algo que no está aquí, propón la librería con su razón, licencia y mantenimiento, y espera aprobación.
- No instales plantillas completas de tienda: se adapta la lógica de este proyecto con sus propias reglas (docs 02 y 03).
