# 05 – Arquitectura y stack

## Tecnologías
- Python 3.12 o superior y Django en su versión LTS vigente (verificar al iniciar).
- Base de datos: SQLite en local; **PostgreSQL** en demo persistente y producción. Nombres físicos en MAYÚSCULAS y en español según `12-estandar-base-datos.md`.
- Interfaz pública: plantillas de Django + Tailwind CSS + un poco de JavaScript (Alpine.js o HTMX) para el carrito y el stock en vivo. Sin framework SPA en esta etapa.
- Admin: admin de Django con grupos y permisos. Opcional en la Fase 5: `django-unfold` para un panel más cómodo en celular.
- API: Django REST Framework en `/api/v1/` con JWT (`djangorestframework-simplejwt`) para el personal y documentación OpenAPI/Swagger con `drf-spectacular` (contrato en `03-Diseno-Tecnico/api/openapi.yaml`). La web pública y una futura app usan la misma lógica de servicios.
- PDF: **ReportLab** (Python puro) para evitar dependencias de sistema en Render. Alternativa solo si el despliegue lo permite: WeasyPrint.
- Imágenes: Pillow para generar miniatura y detalle en WebP al subir; originales en un bucket privado; archivos servidos desde Cloudflare R2 (compatible con S3) mediante `django-storages`.
- Estáticos: WhiteNoise. Servidor: gunicorn.
- Calidad y seguridad: `pytest-django`, `ruff`, `django-simple-history`, `django-environ`, `django-ratelimit`, `django-cors-headers`, `playwright`.

## Capas (regla central)
```
vistas / serializadores / admin / templates   → delgados, sin lógica de negocio
         │
         ▼
servicios.py    → escrituras y reglas (cotizar, confirmar pago, ajustar stock)
selectores.py   → lecturas y consultas reutilizables
         │
         ▼
modelos.py      → datos e invariantes simples
```
- Los servicios se ejecutan en `transaction.atomic()` y usan `select_for_update()` al tocar stock.
- Los errores de negocio son excepciones propias (`StockInsuficienteError`, `TransicionInvalidaError`, `DatosEnvioIncompletosError`) que las vistas y la API traducen a mensajes claros.
- Una función por regla: no repetir cálculo de totales, precios por mayor ni generación de mensajes de WhatsApp.

## Estándar de código y comentarios
Todo el código propio va en **español**. Cada función y método propio lleva un docstring breve con estas 5 líneas obligatorias:
```python
def confirmar_pago(*, pedido_id: int, metodo_pago_id: int, usuario) -> Pedido:
    """Confirma el pago de un pedido y descuenta el stock de forma atómica.

    Qué hace:      Pasa el pedido de COTIZADO a PAGADO y crea un MovimientoStock VENTA por ítem.
    Va hacia:      Modifica TBL_TPEDIDO, TBL_RVARIANTE y agrega filas en TBL_TMOVIMIENTO_STOCK y TBL_LPEDIDO_ESTADO.
    Depende de:    cambiar_estado(), inventario.servicios.registrar_movimiento() y select_for_update().
    Cuándo usarla: Cuando Richard verifica el Yape/efectivo en el panel o mediante POST /api/v1/admin/pedidos/{codigo}/confirmar-pago/.
    Si no opera:   Lanza TransicionInvalidaError si no está en COTIZADO o StockInsuficienteError (hace rollback completo).
    """
```

## Estructura de carpetas del código
Esta es la estructura **dentro de `04-Desarrollo/`**. Los documentos, reglas de la IA y recursos de marca viven fuera del código (ver `00-Gestion/ESTANDAR-ESTRUCTURA.md`).
```
04-Desarrollo/
├── config/
│   └── settings/ base.py, local.py, demo.py, production.py
├── apps/
│   ├── nucleo/      # ajustes de tienda, métodos de pago, utilidades y excepciones base
│   ├── catalogo/    # categorías, productos, variantes, precios por mayor
│   ├── inventario/  # movimientos de stock y alertas de stock bajo
│   ├── pedidos/     # carrito, pedidos, estados, PDF, mensajes de WhatsApp
│   ├── envios/      # envíos por agencia y datos de despacho
│   └── tablero/     # reportes, métricas y alertas para Richard
├── templates/  static/  tests/
└── manage.py  requirements/  .env.example  render.yaml
```

## Carrito
Carrito en **sesión del servidor**. Al enviar el pedido, el servidor recalcula precios y verifica el stock; nunca confía en los precios que llegan del navegador.

## Mensajes de WhatsApp
Se generan con enlaces `https://wa.me/<numero>?text=...` con el texto codificado. El enlace solo prellena texto; no adjunta archivos. Para el PDF se ofrece descarga y, en celulares compatibles, el botón de compartir del navegador.

## API y documentación Swagger
Endpoints públicos de lectura del catálogo, carrito y creación/consulta de pedidos; endpoints privados (JWT) para gestión de pedidos, ventas presenciales, stock, envíos y tablero. El contrato completo está en `03-Diseno-Tecnico/api/openapi.yaml` y la guía en `03-Diseno-Tecnico/13-especificacion-api-swagger.md`. En el servidor se publica con `drf-spectacular` en `/api/schema/`, `/api/docs/` (Swagger UI) y `/api/redoc/`.

## Metodología de desarrollo (`Feature Dev`) y auditoría (`CodeReview`)

### 1. Flujo `Feature Dev` (6 pasos por cada funcionalidad en rama `feature/*`)
1. **Contrato documental:** verificar reglas en docs `02` y `03`, modelo en `04`/`12` y ruta en `13` (`openapi.yaml`).
2. **Datos y diccionario:** definir modelo en español con `db_table` y `db_column` en MAYÚSCULAS (`TBL_`), crear migración y ejecutar `generar_diccionario.py`.
3. **Dominio (`servicios.py` y `selectores.py`):** programar la lógica con sanitización de entradas, transacciones atómicas y el **docstring obligatorio de 5 líneas** en cada función.
4. **Interfaz / API delgada:** conectar vista, template mobile-first (un solo CTA `#39FF14`) o serializer sin lógica de negocio duplicada.
5. **Pruebas:** escribir tests unitarios (`pytest`), test de permisos/aislamiento de filas y prueba visual/E2E (`Playwright`).
6. **Cierre:** ejecutar el checklist de `CodeReview` antes de hacer commit y merge a `develop`.

### 2. Checklist obligatorio de `CodeReview` (antes de cada commit / Pull Request)
- [ ] **Idioma y docstrings:** ¿Todo el código propio está en español y cada función/método tiene su docstring de 5 líneas (*Qué hace*, *Va hacia*, *Depende de*, *Cuándo usarla*, *Si no opera*)?
- [ ] **Capas limpias:** ¿Las vistas, templates y serializers están libres de reglas de negocio? ¿Las lecturas usan `select_related`/`prefetch_related` (cero consultas N+1)?
- [ ] **Integridad de stock y precios:** ¿El stock solo cambia por `MovimientoStock` con `select_for_update()`? ¿Los precios se calculan en el servidor ignorando cualquier monto enviado desde el navegador?
- [ ] **Blindaje anti-hacking (doc 07):** ¿Entradas sanitizadas (`strip_tags`, regex de DNI/teléfono)? ¿Rate limiting activo? ¿Aislamiento de filas (sin exponer DNI, teléfono ni `clave_recojo` en rutas públicas)? ¿Cero secretos en el código?
- [ ] **Calidad y base de datos:** ¿Pasan `ruff`, `pytest` y el test de nombres físicos `TBL_` en MAYÚSCULAS?
