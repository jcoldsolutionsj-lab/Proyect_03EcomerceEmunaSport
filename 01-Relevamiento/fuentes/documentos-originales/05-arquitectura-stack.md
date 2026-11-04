# 05 – Arquitectura y stack

## Tecnologías
- Python 3.12 o superior y Django en su versión LTS vigente (verificar al iniciar).
- Base de datos: SQLite en local; **PostgreSQL** en demo persistente y producción.
- Interfaz pública: plantillas de Django + Tailwind CSS + un poco de JavaScript (Alpine.js o HTMX) para el carrito y el stock en vivo. Sin framework SPA en esta etapa.
- Admin: admin de Django con grupos y permisos. Opcional en la Fase 5: `django-unfold` para un panel más cómodo en celular.
- API: Django REST Framework en `/api/v1/` con JWT (`djangorestframework-simplejwt`) para el personal. La web pública y una futura app usan la misma lógica de services.
- PDF: **ReportLab** (Python puro) para evitar dependencias de sistema en Render. Alternativa solo si el despliegue lo permite: WeasyPrint.
- Imágenes: Pillow para generar miniatura y detalle en WebP al subir; originales en un bucket privado; archivos servidos desde Cloudflare R2 (compatible con S3) mediante `django-storages`.
- Estáticos: WhiteNoise. Servidor: gunicorn.
- Calidad: `pytest-django`, `ruff`, `django-simple-history`, `django-environ`, `django-ratelimit`.

## Capas (regla central)
```
views / serializers / admin / templates   → delgados, sin lógica de negocio
        │
        ▼
services.py   → escrituras y reglas (cotizar, confirmar pago, ajustar stock)
selectors.py  → lecturas y consultas reutilizables
        │
        ▼
models.py     → datos e invariantes simples
```
- Los services se ejecutan en `transaction.atomic()` y usan `select_for_update()` al tocar stock.
- Los errores de negocio son excepciones propias (`NotEnoughStock`, `InvalidTransition`) que las vistas traducen a mensajes claros.
- Una función por regla: no repetir cálculo de totales, precios por mayor ni generación de mensajes de WhatsApp.

## Estructura de carpetas
```
emuna-sport/
├── .agents/rules/          # reglas para Antigravity
├── docs/                   # estos documentos
├── assets/                 # logo y recursos de marca
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
├── manage.py  requirements/  .env.example  render.yaml
```

## Carrito
Carrito en **sesión del servidor**. Al enviar el pedido, el servidor recalcula precios y verifica el stock; nunca confía en los precios que llegan del navegador.

## Mensajes de WhatsApp
Se generan con enlaces `https://wa.me/<numero>?text=...` con el texto codificado. El enlace solo prellena texto; no adjunta archivos. Para el PDF se ofrece descarga y, en celulares compatibles, el botón de compartir del navegador.

## API para app futura
Endpoints públicos de lectura del catálogo y creación de pedidos; endpoints privados (JWT) para pedidos, stock y envíos. Documentación con `drf-spectacular`. Se construye cuando termine el piloto, reutilizando los services.
