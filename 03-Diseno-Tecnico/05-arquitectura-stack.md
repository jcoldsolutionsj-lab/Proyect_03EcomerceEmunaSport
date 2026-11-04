# 05 – Arquitectura y stack

> [!WARNING]
> **Documento reconstruido parcialmente.** El 2026-11-03 se borró por accidente y no había copia. La sección «Stack» y la descripción de capas se rearmaron a partir de las reglas del proyecto y de los docs 07, 08 y 09. Las secciones desde «Estructura de carpetas del código» en adelante son el texto original. **Jonathan debe revisar las dos primeras secciones y corregir lo que difiera.** Cuando se confirme, borrar este aviso y anotarlo en `00-Gestion/11-decisiones-cambios.md`.

## Stack
| Pieza | Tecnología | Nota |
|---|---|---|
| Lenguaje y framework | Python + Django | Plantillas de Django, mobile-first |
| Base de datos | PostgreSQL (SQLite solo en local) | Nombres físicos según `12-estandar-base-datos.md` |
| Fotos | Bucket compatible con S3 (Cloudflare R2) con `django-storages` | Pillow para regenerar imágenes |
| PDF del pedido | ReportLab | Python puro |
| Estáticos y servidor | `whitenoise` y `gunicorn` en Render | Ver doc 08 |
| Configuración | `django-environ` | Todo por variables de entorno |
| Historial | `django-simple-history` | Pedidos y envíos |
| Antispam | `django-ratelimit` y campo trampa | Pedido público |
| Calidad | `pytest` y `ruff` | Cada service lleva pruebas |
| Fase posterior | `djangorestframework`, `simplejwt`, `drf-spectacular` | API con JWT para app móvil |
| Opcional (Fase 5) | `django-unfold` | Admin más cómodo en celular |

## Capas
Dentro de cada app, la lógica de negocio se separa de la presentación:
```
views / serializers / templates / admin   ← delgados: reciben y muestran
services.py                               ← escrituras y reglas de negocio
selectors.py                              ← lecturas y consultas
models.py                                 ← datos e invariantes simples
```
- Los services se ejecutan en `transaction.atomic()` y usan `select_for_update()` al tocar stock.
- Los errores de negocio son excepciones propias (`NotEnoughStock`, `InvalidTransition`) que las vistas traducen a mensajes claros.
- Una función por regla: no repetir cálculo de totales, precios por mayor ni generación de mensajes de WhatsApp.

## Estructura de carpetas del código
Esta es la estructura **dentro de `04-Desarrollo/`**. Los documentos, reglas de la IA y recursos de marca viven fuera del código (ver `00-Gestion/ESTANDAR-ESTRUCTURA.md`). Los nombres físicos de la base de datos (`db_table`, `db_column`) siguen `12-estandar-base-datos.md`.
```
emuna-sport/
├── config/
│   └── settings/ base.py, local.py, demo.py, production.py
├── apps/
│   ├── core/       # ajustes de tienda, métodos de pago, utilidades
│   ├── catalog/    # categorías, productos, variantes, precios
│   ├── inventory/  # movimientos de stock
│   ├── orders/     # pedidos, estados, PDF, mensajes de WhatsApp
│   ├── shipping/   # envíos y datos de agencia
│   └── dashboard/  # reportes y alertas
├── templates/  static/  tests/
└── manage.py  requirements/  .env.example  render.yaml
```

## Carrito
Carrito en **sesión del servidor**. Al enviar el pedido, el servidor recalcula precios y verifica el stock; nunca confía en los precios que llegan del navegador.

## Mensajes de WhatsApp
Se generan con enlaces `https://wa.me/<numero>?text=...` con el texto codificado. El enlace solo prellena texto; no adjunta archivos. Para el PDF se ofrece descarga y, en celulares compatibles, el botón de compartir del navegador.

## API para app futura
Endpoints públicos de lectura del catálogo y creación de pedidos; endpoints privados (JWT) para pedidos, stock y envíos. Documentación con `drf-spectacular`. Se construye cuando termine el piloto, reutilizando los services.
