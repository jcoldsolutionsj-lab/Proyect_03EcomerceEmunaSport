# 16 – Los 10 Atributos de Calidad del Software (Emuná Sport)

Este documento establece los **10 atributos de calidad innegociables** del sistema Emuná Sport. Todo cambio futuro en base de datos, lógica de negocio, panel administrativo (`/gestion/`) o tienda pública debe evaluarse contra estos diez principios para garantizar rapidez operativa, claridad para el cliente y valor real para el negocio de Richard.

---

## 1. Alineación Operativa Real (Modalidad vs. Estados sin pasos fantasma)
- **Principio:** Lo que el cliente ve en la barra de seguimiento web (`/pedidos/<codigo>/`) debe reflejar exactamente los pasos operativos reales que Richard ejecuta en `/gestion/` según la modalidad elegida.
- **Aplicación en Emuná Sport:**
  - **`PUNTO_ENCUENTRO` y `RECOJO` (4 etapas):** `1. Recibido` → `2. Listo para coordinar / recojo` (nace aquí con envío `S/ 0.00`) → `3. Pago Confirmado` → `4. Entregado`. Se omite `En Camino` porque no interviene agencia ni courier.
  - **`DELIVERY_LIMA` (4 etapas):** `1. Recibido` → `2. Cotizado / Listo` → `3. Pago Confirmado` → `4. Entregado`.
  - **`AGENCIA` Shalom / Olva (5 etapas):** `1. Recibido` → `2. Cotizado / Listo` → `3. Pago Confirmado` → `4. En Camino` (exige orden, clave de 4 dígitos y boleta) → `5. Entregado`.

## 2. Minimalismo de Datos con Valor de Negocio (Cero campos de relleno)
- **Principio:** Solo se solicita o almacena un dato en base de datos si el negocio depende de él para operar, despachar o generar inteligencia comercial. Si un dato ya viaja en un respaldo visual o no acciona ninguna regla, no se obliga a digitarlo.
- **Aplicación en Emuná Sport:**
  - Del cliente solo se capturan sus **campos principales**: `cliente_nombre`, `cliente_telefono` (9 dígitos WhatsApp) y `cliente_dni` (8 dígitos, obligatorio en `AGENCIA` porque Shalom/Olva lo exigen en ventanilla y opcional en Lima).
  - En el despacho por agencia (`TBL_TENVIO`) solo se digitan los datos accionables (`agencia`, `numero_orden_agencia`, `clave_recojo`, `costo_flete`, `quien_paga`, `cobrado`). Datos accesorios del ticket físico (origen, fecha/hora de traslado, peso `XXS`, RUC, garantía o QR) quedan respaldados en la **foto privada de la boleta** (`imagen_boleta`).

## 3. Agilidad Móvil y Captura en 1 Toque (Operación en calle y ventanilla)
- **Principio:** Richard opera gran parte del día desde el celular (en estaciones del tren, taller o ventanilla de Shalom/Olva). Toda acción recurrente debe resolverse en 1 o 2 toques sin desbordes horizontales.
- **Aplicación en Emuná Sport:**
  - Al registrar el despacho en agencia (`change_form.html`), el campo de boleta ofrece dos botones directos: **`📷 Tomar foto`** (abre directamente la cámara trasera con `capture="environment"`) y **`📎 Adjuntar galería/PDF`**, además de desmarcar automáticamente `Flete ya cobrado` cuando se elige pago en destino (`CLIENTE_EN_DESTINO`).
  - Cabecera superior y barra de navegación rápida (`emuna-mobile-sticky-bar` + `emuna-mobile-quicknav`) fijas al hacer scroll en móvil, y tablas operativas con deslizamiento horizontal táctil (`emuna-table-scroll`).

## 4. Claridad Cognitiva y Autoexplicación (Tooltips y Ventanas de Ayuda con Ejemplos)
- **Principio:** Ningún botón crítico ni modalidad de entrega debe prestarse a ambigüedad. Tanto el administrador como el comprador deben contar con ayuda contextual inmediata antes de confirmar una acción.
- **Aplicación en Emuná Sport:**
  - **En `/gestion/` (Richard):** Los botones de estado `COTIZADO` distinguen explícitamente **`🤝 Ya entregué y cobré en persona (→ ENTREGADO)`** (verde, 1 paso en el acto) frente a **`💳 Pagó por adelantado (Separar → PAGADO)`** (azul, 2 pasos para reservar stock), acompañados de íconos `toltip.png` con aviso táctil en móvil y tooltip en escritorio.
  - **En la Web (Cliente):** El checkout (`/pedidos/checkout/`) incluye la ventana interactiva **`❓ ¿Cómo funciona cada modalidad? Ver ejemplos`** y la página de seguimiento (`/pedidos/<codigo>/`) incorpora el desplegable paso a paso con ejemplos reales para la modalidad elegida.

## 5. Inteligencia Comercial sobre Clientes VIP y Recurrentes
- **Principio:** Los campos principales del cliente (`cliente_nombre`, `cliente_telefono`, `cliente_dni`) deben transformarse en información estratégica para fidelizar a los mejores compradores y mayoristas.
- **Aplicación en Emuná Sport:**
  - El Tablero Operativo (`/gestion/tablero/`) consolida el ranking **`👑 Clientes VIP y Top Compradores`**, agrupando compras confirmadas por celular/nombre, identificando clientes recurrentes o mayoristas (`2+ pedidos` o `3+ prendas`), mostrando el total invertido en soles y ofreciendo acceso en 1 clic a su historial de pedidos y a su WhatsApp.

## 6. Atomicidad e Integridad Transaccional de Inventario
- **Principio:** El stock nunca puede quedar descuadrado, en negativo ni descontarse dos veces.
- **Aplicación en Emuná Sport:**
  - El stock se descuenta **únicamente al confirmar el pago** (`COTIZADO → PAGADO`), bloqueando las filas de `TBL_RVARIANTE` en orden determinista con `select_for_update()` dentro de `transaction.atomic()`.
  - Toda salida o reposición genera un registro inmutable en el kárdex (`TBL_TMOVIMIENTO_STOCK` con tipos `VENTA`, `ENTRADA`, `AJUSTE` o `DEVOLUCION`).

## 7. Privacidad y Seguridad por Diseño (Anti-Hacking y Ley N.º 29733)
- **Principio:** Los datos sensibles del cliente y del despacho jamás quedan expuestos al público ni a enumeración automatizada.
- **Aplicación en Emuná Sport:**
  - Códigos públicos no secuenciales (`EMU-XXXXXX`), DNI enmascarado (`******12`) en la vista pública, clave de recojo de 4 dígitos excluida de la web pública y boletas de agencia servidas desde almacenamiento privado (`private/boletas/`) solo para personal autenticado.
  - Triple protección en checkout: campo trampa (*honeypot*), aceptación expresa de la Ley N.º 29733 y validación Cloudflare Turnstile + limitación de tasa (*rate limiting*).

## 8. Trazabilidad y Auditoría Inmutable
- **Principio:** Todo cambio de estado y todo movimiento de inventario debe dejar huella auditable permanente (quién, cuándo, estado anterior, estado nuevo y motivo).
- **Aplicación en Emuná Sport:**
  - Bitácora inmutable de estados (`TBL_LPEDIDO_ESTADO`), kárdex de stock (`TBL_TMOVIMIENTO_STOCK`) que bloquea edición o borrado, e historial de auditoría (`django-simple-history` en `TBL_HPEDIDO`, `TBL_HPRODUCTO` y `TBL_HVARIANTE`).

## 9. Comunicación Contextual en Tiempo Real (Vivo + WhatsApp en 1 clic)
- **Principio:** Reducir la fricción de coordinación entre la tienda web y el WhatsApp oficial de Richard.
- **Aplicación en Emuná Sport:**
  - La página pública del pedido consulta cambios de estado cada 15 segundos (`/pedidos/<codigo>/estado-json/` y `?parcial=1`), notificando al cliente en vivo cuando Richard cotiza, confirma el pago o registra el despacho, y adaptando automáticamente el mensaje y botón de WhatsApp a la etapa actual.

## 10. Mantenibilidad y Estándar Técnico Verificable
- **Principio:** Toda regla de negocio debe estar respaldada por código limpio en español, arquitectura modular (`models`, `selectores`, `servicios`, `views`) y pruebas automatizadas reproducibles.
- **Aplicación en Emuná Sport:**
  - Cumplimiento estricto del estándar físico de base de datos (`TBL_` y prefijos de columna validados por test), cero errores de estilo en `ruff check` y suite integral `pytest` que verifica flujos extremo a extremo antes de cada entrega.
