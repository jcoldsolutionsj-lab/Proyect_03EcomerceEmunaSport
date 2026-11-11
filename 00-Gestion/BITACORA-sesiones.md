# Bitácora de sesiones

Una entrada breve por sesión de trabajo, la más reciente **arriba**. Cada entrada responde: qué se hizo, qué se decidió, qué queda.

## 2026-11-11 – Implementación integral y pruebas de la Fase 3 (`feature/fase-3-gestion-pedidos-stock`)
- **Hecho:**
  - Se completó al 100% el esquema relacional con las 2 tablas finales del diccionario de datos: `TBL_TMOVIMIENTO_STOCK` (auditoría inmutable de entradas, ventas, ajustes y devoluciones de stock con bloqueos en `save()` y `delete()`) y `TBL_TENVIO` (seguimiento de despachos por Shalom/Olva con orden, flete, quién paga, clave de 4 dígitos y boleta privada).
  - Se ejecutaron las migraciones correspondientes (`catalogo/0002_movimientostock.py` y `pedidos/0002_envio.py`). El script `generar_diccionario.py` validó las 13 tablas y 134 columnas del proyecto (100% de coincidencia) y `test_estandar_bd.py` aprobó todas las tablas en mayúsculas `TBL_`.
  - Se implementaron en `apps/pedidos/servicios.py` los servicios del corazón del negocio:
    - Transición atómica de estados con matriz estricta `TRANSICIONES_PERMITIDAS` y bitácora `TBL_LPEDIDO_ESTADO`.
    - Descuento atómico de inventario con `select_for_update()` ordenado por `id` de variante para prevenir deadlocks en bases de datos relacionales concurrentes.
    - Flujo A (Provincia / Agencia): `NUEVO -> COTIZADO -> PAGADO -> ENVIADO -> ENTREGADO`.
    - Flujo B (Punto de Encuentro Lima): `confirmar_pago_y_entregar()` en un solo paso (`COTIZADO -> PAGADO -> ENTREGADO`) con doble registro en bitácora.
    - Flujo C (Venta Presencial POS): `registrar_venta_presencial()` para mostrador y ferias con descuento automático de stock y tarifa mayorista unificada.
    - Reposición automática de stock con movimientos `DEVOLUCION` al cancelar pedidos pagados.
    - `construir_enlace_whatsapp_notificacion_cliente` con mensajes enriquecidos para notificar cotización, número de orden y clave de recojo.
  - Se blindó la privacidad de las boletas de agencia mediante la vista autenticada `vista_ver_boleta_privada` (`/pedidos/envio/<id>/boleta/`), restringida exclusivamente a staff y miembros del grupo `Dueño`. La clave de recojo y la foto de la boleta jamás se exponen en la vista pública web.
  - Se adaptó el Django Admin para Richard:
    - Acciones masivas de confirmación de pago, entrega rápida en Lima, entrega final y cancelación con devolución de stock.
    - Columna con botón directo de notificación al cliente por WhatsApp según el estado del pedido.
    - Inlines de `Envio` (con enlace al comprobante privado) y `RegistroEstadoPedido` (inmutable).
    - Módulo POS táctil de Venta Presencial en `/admin/pedidos/pedido/venta-presencial/` (`templates/admin/pedidos/venta_presencial.html`).
    - `MovimientoStockAdmin` estrictamente en solo lectura.
  - Se preparó el script k6 `03-Diseno-Tecnico/pruebas-carga-k6/escenarios-base.js` con el escenario `concurrencia_stock` listo para su ejecución contra PostgreSQL en Render (Fase 5).
  - Se creó la suite de pruebas `04-Desarrollo/tests/test_gestion_pedidos.py` con 9 escenarios automatizados.
  - Se ejecutó `pytest` completo con **27 pruebas pasando al 100%** (`27 passed in 54.95s`) y `ruff check 04-Desarrollo` con **0 errores**.
- **Decidido:**
  - Diferir la ejecución de la prueba de concurrencia k6 con PostgreSQL a la Fase 5 (entorno Render con PostgreSQL en producción).
  - Mantener las fotos de boletas de despacho en almacenamiento privado local (`media/private/boletas/`) con acceso exclusivo por vista autenticada hasta la Fase 6, donde se conectará Cloudflare R2 / S3.
- **Queda:**
  - Realizar commit estructurado de la Fase 3 en `feature/fase-3-gestion-pedidos-stock`.
  - Fusionar (`--no-ff`) a `develop` y subir a `origin`.
  - Iniciar la **Fase 4: Panel visual de Richard con métricas y alertas de stock bajo**.

## 2026-11-10 – Mejoras de comprobante, logos oficiales de agencia y enlace dinámico de WhatsApp en Fase 2
- **Hecho:**
  - Se integró el video animado oficial `Logo_animado.mp4` en el navbar de la cabecera (`base.html`), eliminando sombras verdes externas o animaciones CSS superpuestas para que luzca limpio y fiel al video original.
  - Se incorporaron los logos oficiales de **Agencia Shalom** (`shalom_logo.png`) y **Olva Courier** (`Olva_logo.png`) dentro de la selección de agencia en `http://127.0.0.1:8000/pedidos/checkout/`, dotando de máxima seriedad y presencia de marca al formulario de envío a provincia.
  - Se actualizó el comprobante PDF (`generar_pdf_pedido`) para incrustar automáticamente el logo oficial de la agencia seleccionada (Shalom u Olva), especificar el nombre exacto de la agencia en la modalidad y plasmar la observación/comentario del cliente (`pedido.notas`) cuando exista.
  - Se integró la foto oficial del código QR de Yape de Richard (`QR_yape_richardRamos.jpeg`) en la tarjeta de seguimiento del pedido (`detalle_pedido.html`), con su titular ("Richard Ramos - Emuná Sport") y botón de copiado resiliente con fallback portapapeles.
  - Se creó el selector dinámico `carrito.url_whatsapp_consulta` (`obtener_carrito_detallado`), permitiendo que el link «Escribir por WhatsApp» en el cajón lateral HTMX, la página `/carrito/` y el checkout `/pedidos/checkout/` arme automáticamente el mensaje prellenado hacia Richard con el detalle de camisetas, tallas, cantidades y subtotales calculados.
  - Se añadieron pruebas unitarias automatizadas (`test_pdf_pedido_agencia_shalom_con_notas` y aserción de `url_whatsapp_consulta`), alcanzando 18 pruebas pasando al 100% en `pytest` y 0 errores en `ruff check`.
- **Decidido:** dar por concluida la Fase 2 y presentar a Jonathan el resumen final para su visto bueno de commit y merge a `develop`.
- **Queda:** fusionar `feature/fase-2-carrito-pedido-whatsapp` a `develop` e iniciar la **Fase 3: Panel de control de Richard, transiciones de estado de pedido y descuento atómico de stock**.
