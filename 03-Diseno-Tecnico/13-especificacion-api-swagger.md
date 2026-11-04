# 13 – Especificación de la API y Swagger

Este documento explica **cómo opera cada endpoint** de la API de Emuná Sport, a qué función de `servicios.py` o `selectores.py` llama, quién puede invocarlo y qué ocurre si falla. El contrato formal en formato OpenAPI 3.0.3 está en [`api/openapi.yaml`](file:///d:/JONATHAN/Proyectos/EcomerceEmunaSport/03-Diseno-Tecnico/api/openapi.yaml).

## 1. Cómo se publica y se consulta Swagger
- En Django se usa `drf-spectacular`.
- Rutas en el servidor:
  - `/api/schema/` → descarga el archivo OpenAPI (`openapi.yaml`).
  - `/api/docs/` → **Swagger UI** interactivo (permite probar cada endpoint con el botón *Try it out* y autorizar con JWT).
  - `/api/redoc/` → **ReDoc** para lectura rápida.
- Mientras aún no exista el servidor, cualquier persona puede abrir `03-Diseno-Tecnico/api/openapi.yaml` en [editor.swagger.io](https://editor.swagger.io) o con la extensión *OpenAPI (Swagger) Editor* de VS Code / Antigravity.

## 2. Reglas generales de la API
- **Prefijo:** `/api/v1/`.
- **Una sola lógica:** las vistas de la API son delgadas; **no** contienen consultas ni reglas de negocio. Llaman a los mismos `servicios.py` y `selectores.py` que usan las plantillas web y el panel de administración.
- **Seguridad:**
  - Endpoints públicos (`/catalogo/…`, `/carrito/…`, `/pedidos/…`): sin login. El `POST /pedidos/` tiene límite de intentos (`django-ratelimit`) y campo trampa (`sitio_web`).
  - Endpoints de administración (`/admin/…`): exigen token **JWT Bearer** de un usuario activo del grupo `Dueño` (Richard) o superusuario (Jonathan).
- **Privacidad:** `GET /pedidos/{codigo}/` nunca devuelve `cliente_dni` completo ni `clave_recojo`.
- **Formato de error unificado:**
  ```json
  {
    "codigo_error": "stock_insuficiente",
    "mensaje": "No hay stock suficiente para la talla M (disponible: 2).",
    "detalles": { "variante_id": 12, "disponible": 2, "solicitado": 4 }
  }
  ```

## 3. Mapa de endpoints

### 3.1 Públicos (cliente desde el celular)

| Método y ruta | Servicio / Selector que ejecuta | Qué hace y hacia dónde va | Si no opera (errores) |
|---|---|---|---|
| `GET /api/v1/catalogo/categorias/` | `catalogo.selectores.listar_categorias_activas()` | Lee `TBL_RCATEGORIA` activas en orden. | `200` lista vacía si no hay categorías. |
| `GET /api/v1/catalogo/productos/` | `catalogo.selectores.listar_productos_catalogo()` | Lista `TBL_RPRODUCTO` activos con miniatura, precio base y precio mínimo por mayor. Oculta `marca` si `mostrar_marcas` está apagado. | `200` lista vacía si no hay coincidencias. |
| `GET /api/v1/catalogo/productos/{slug}/` | `catalogo.selectores.obtener_producto_detalle(slug)` | Devuelve fotos (`TBL_RIMAGEN_PRODUCTO`), variantes con `cantidad_stock` (`TBL_RVARIANTE`) y escalas (`TBL_RREGLA_PRECIO`). | `404` si el producto no existe o está oculto. |
| `GET /api/v1/carrito/` | `pedidos.selectores.obtener_carrito_detallado(sesion)` | Lee el carrito en sesión y recalcula los precios por mayor vigentes. | `200` carrito vacío. |
| `POST /api/v1/carrito/items/` | `pedidos.servicios.agregar_al_carrito()` | Verifica stock actual en `TBL_RVARIANTE` y guarda la cantidad en la sesión. | `400 stock_insuficiente` o `variante_inactiva`. |
| `POST /api/v1/pedidos/` | `pedidos.servicios.crear_pedido_web()` | Valida datos (DNI 8 dígitos en `AGENCIA`, teléfono `9XXXXXXXX`), recalcula precios, crea `TBL_TPEDIDO`, `TBL_TPEDIDO_ITEM` (con copias) y `TBL_LPEDIDO_ESTADO`. Nace en `NUEVO` (`AGENCIA`/`DELIVERY_LIMA`) o en `COTIZADO` con envío `S/ 0` (`PUNTO_ENCUENTRO`/`RECOJO`). | `400 datos_invalidos`, `carrito_vacio`, `stock_insuficiente`; `429` por exceso de intentos. |
| `GET /api/v1/pedidos/{codigo}/` | `pedidos.selectores.obtener_pedido_publico(codigo)` | Devuelve ítems, totales, estado y, solo si está en `COTIZADO`, los datos de Yape. Sin DNI ni clave de recojo. | `404` si el código no existe. |
| `GET /api/v1/pedidos/{codigo}/pdf/` | `pedidos.servicios.generar_pdf_pedido(codigo)` | Genera y entrega el PDF del pedido con ReportLab. | `404` si el código no existe. |

### 3.2 Autenticación y administración (Richard y Jonathan, con JWT)

| Método y ruta | Servicio / Selector que ejecuta | Qué hace y hacia dónde va | Si no opera (errores) |
|---|---|---|---|
| `POST /api/v1/auth/token/` | `TokenObtainPairView` (SimpleJWT) | Valida usuario y contraseña y entrega tokens `access` y `refresh`. | `401` credenciales inválidas. |
| `POST /api/v1/auth/token/refrescar/` | `TokenRefreshView` (SimpleJWT) | Entrega un nuevo `access` token. | `401` token vencido o inválido. |
| `GET /api/v1/admin/pedidos/` | `pedidos.selectores.listar_pedidos_admin(filtros)` | Lista pedidos con DNI, teléfono, agencia/punto de encuentro y enlaces de WhatsApp. | `401/403` sin permiso. |
| `POST /api/v1/admin/pedidos/venta-presencial/` | `pedidos.servicios.registrar_venta_presencial()` | Registra una venta cerrada en persona por Richard (`origen = PRESENCIAL`), descuenta stock con `MovimientoStock` `VENTA` y deja el pedido en `PAGADO` o `ENTREGADO`. | `400 stock_insuficiente`. |
| `POST /api/v1/admin/pedidos/{codigo}/cotizar/` | `pedidos.servicios.cotizar_envio()` | Guarda `PED_NCOSTO_ENVIO`, recalcula `PED_NTOTAL` y pasa de `NUEVO` a `COTIZADO`. | `400 transicion_invalida` si no está en `NUEVO`. |
| `POST /api/v1/admin/pedidos/{codigo}/confirmar-pago/` | `pedidos.servicios.confirmar_pago()` | En `transaction.atomic()` bloquea variantes (`select_for_update`), crea `MovimientoStock` `VENTA`, descuenta `VAR_NCANTIDAD_STOCK` y pasa a `PAGADO`. Con `entregar_en_acto = true` (cita en punto de encuentro en Lima), pasa en el mismo acto a `ENTREGADO`. | `400 transicion_invalida` o `stock_insuficiente` (rollback total). |
| `POST /api/v1/admin/pedidos/{codigo}/despachar/` | `envios.servicios.registrar_despacho()` | Crea `TBL_TENVIO` (orden, clave de 4 dígitos, foto de boleta en bucket privado, flete y quién paga) y pasa de `PAGADO` a `ENVIADO`. | `400 datos_envio_incompletos` o `transicion_invalida`. |
| `POST /api/v1/admin/pedidos/{codigo}/entregar/` | `pedidos.servicios.cambiar_estado(..., 'ENTREGADO')` | Pasa de `PAGADO` (entrega en mano) o `ENVIADO` (agencia) a `ENTREGADO`. | `400 transicion_invalida`. |
| `POST /api/v1/admin/pedidos/{codigo}/cerrar/` | `pedidos.servicios.cerrar_pedido()` | Pasa a `CANCELADO` o `RECHAZADO`. Si estaba en `PAGADO` (o `ENVIADO` con devolución física confirmada), devuelve el stock con movimientos `DEVOLUCION`. | `400 transicion_invalida` (ej. si ya estaba `ENTREGADO`). |
| `POST /api/v1/admin/inventario/movimientos/` | `inventario.servicios.registrar_movimiento()` | Registra una `ENTRADA` o `AJUSTE` en `TBL_TMOVIMIENTO_STOCK` y actualiza `VAR_NCANTIDAD_STOCK`. | `400 stock_negativo` si el ajuste dejaría el stock menor a 0. |
| `GET /api/v1/admin/tablero/resumen/` | `tablero.selectores.obtener_resumen_tablero()` | Devuelve alertas (stock bajo, sin ventas, pendientes > 24 h) y ventas del período. | `401/403` sin permiso. |
