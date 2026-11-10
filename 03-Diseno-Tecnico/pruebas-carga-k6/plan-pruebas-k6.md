# Plan de pruebas de carga y concurrencia con Grafana k6

## 1. Propósito en Emuná Sport
Usamos **Grafana k6** para medir cuánto tráfico soporta la tienda y garantizar dos cosas críticas del negocio de Richard:
1. **Que la web no se caiga ni se vuelva lenta** cuando Richard comparta un enlace de campaña o nueva colección en estados de WhatsApp y entren decenas de clientes al mismo tiempo desde el celular.
2. **Que jamás se sobrevenda una talla (stock negativo):** verificar bajo concurrencia real que el bloqueo de fila `select_for_update()` en `pedidos.servicios` e `inventario.servicios` funciona cuando varios compradores intentan llevarse la última camiseta talla `M` al mismo segundo.

---

## 2. ¿En qué momento del proyecto usamos k6?

| Fase | Momento de uso | Qué escenario se ejecuta | Dónde se corre |
|---|---|---|---|
| **Fase 2** (Carrito y pedido) | Al terminar el flujo de creación de pedidos | **Escenario 1 y 2 (`smoke` + `carga_catalogo_y_pedido`):** validar que el catálogo, el carrito en sesión y la creación de pedidos respondan en `< 400 ms` (p95) sin fugas de memoria. | Entorno `local` con **PostgreSQL local** (no usar SQLite para pruebas de concurrencia, porque SQLite bloquea todo el archivo). |
| **Fase 3** (Gestión del pedido y stock) | Al terminar la confirmación de pago y descuento de stock | **Escenario 3 (`concurrencia_stock`):** 20 solicitudes simultáneas intentando descontar una variante con `cantidad_stock = 5`. Deben aprobarse exactamente 5 y rechazarse 15, quedando `VAR_NCANTIDAD_STOCK = 0` (nunca negativo). | Entorno `local` con PostgreSQL local. |
| **Fase 5** (Piloto en Render Free) | Solo prueba de humo ligera (*smoke test* de 1 a 3 usuarios) | **Advertencia importante:** **NO correr pruebas de estrés pesadas contra el plan gratuito de Render**, ya que tiene CPU compartida limitada y políticas contra picos artificiales. | Demo o local. |
| **Fase 6** (Pre-producción antes de lanzar) | Antes del lanzamiento oficial con dominio y PostgreSQL persistente | **Prueba completa de carga y pico (*spike test*):** simular un pico de 50 a 100 usuarios concurrentes entrando desde un estado de WhatsApp de Richard. | Entorno `staging` / pre-producción con PostgreSQL persistente y caché CDN de Cloudflare activo. |

---

## 3. Umbrales de aprobación (SLAs del proyecto)

Para dar por aprobada una prueba antes de salir a producción, k6 verifica automáticamente estos umbrales (`thresholds`):
- **Tasa de errores HTTP (`http_req_failed`):** `< 1%` (ningún error `500` permitido).
- **Catálogo y detalle de producto (`p95`):** `< 300 ms`.
- **Agregar al carrito y creación de pedido (`p95`):** `< 500 ms`.
- **Integridad de stock:** `VAR_NCANTIDAD_STOCK >= 0` siempre e igual a la suma de `TBL_TMOVIMIENTO_STOCK`.

---

## 4. Cómo instalar y ejecutar k6

### Instalación en Windows (máquina de Jonathan)
```powershell
winget install k6 --source winget
```

### Ejecución rápida (prueba de humo en local)
```powershell
k6 run -e BASE_URL=http://127.0.0.1:8000 -e MODO=humo 03-Diseno-Tecnico/pruebas-carga-k6/escenarios-base.js
```

### Ejecución de carga de campaña de WhatsApp
```powershell
k6 run -e BASE_URL=http://127.0.0.1:8000 -e MODO=campana 03-Diseno-Tecnico/pruebas-carga-k6/escenarios-base.js
```
