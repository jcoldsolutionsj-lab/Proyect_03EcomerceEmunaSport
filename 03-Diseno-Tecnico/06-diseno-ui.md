# 06 – Diseño y UI

Referencia visual:
1. **Identidad de marca:** el logo en `03-Diseno-Tecnico/assets/logo-emuna-sport.png` (fondo negro, letras plateadas cromadas, rayo «E» en verde neón, lema «Estilo deportivo»), los videos en `assets/banners-inicio/` y las fotos reales en `assets/productos-demo/argentina-messi/`.
2. **Estructura y distribución (Layout base):** las 5 capturas de referencia guardadas en `03-Diseno-Tecnico/assets/referencias-marca/plantilla-base-figma/` (`01-home` a `05-carrito`), adaptadas a las reglas de negocio de Emuná Sport (sin login ni favoritos; con encabezado negro `#0A0A0A`, botones primarios en verde neón `#39FF14`, precios de oferta con tachado `S/ 55.00` ~~`S/ 69.90`~~, precios por mayor y checkout peruano con Shalom/Olva/Punto de encuentro en Lima).

## Colores (variables CSS)
| Variable | Valor | Uso |
|---|---|---|
| `--bg` | `#FFFFFF` | Fondo general |
| `--ink` | `#0A0A0A` | Texto principal, encabezado y pie |
| `--silver` | `#C9CED3` | Bordes, separadores, fondos suaves |
| `--silver-dark` | `#6B727A` | Texto secundario |
| `--accent` | `#39FF14` | Botones principales y detalles (el texto sobre este color es negro) |
| `--accent-dark` | `#1B8F2A` | Enlaces y textos verdes sobre blanco |
| `--danger` | `#C62828` | Errores y agotado |

Regla: el verde neón nunca se usa como color de texto sobre blanco (no se lee); sirve de fondo de botón con texto negro.

## Tipografía
Títulos deportivos en cursiva y negrita (por ejemplo `Barlow Condensed` o `Saira Condensed`); texto en `Inter`. Si se usan Google Fonts, definir fuentes de respaldo del sistema.

## Principios
- **Mobile-first y adaptable a desktop:** se diseña primero para `360 px` de ancho (2 columnas en catálogo, botones táctiles de al menos `48 px` de alto) y escala limpiamente a escritorio `1280 px+` (4 columnas y galería con panel lateral fijo).
- **Una sola llamada a la acción (CTA) principal por pantalla:** en cada vista existe **un único botón primario en verde neón (`#39FF14` con texto `#0A0A0A`)** que indica el siguiente paso del flujo. Las demás acciones secundarias usan borde plata (`#C9CED3`) o enlace de texto para no dividir la atención del comprador.
- **Pocos pasos:** catálogo → producto → carrito → datos → pedido enviado → pago.
- **Todo en español de Perú;** montos como `S/ 45.00` con números tabulares (`tabular-nums`) para que las cifras se alineen siempre.
- **Estados de carga, páginas de error (`404`/`500`) y accesibilidad:** contraste WCAG AA/AAA, etiquetas en formularios, proporción fija `aspect-ratio: 4/5` en tarjetas de camisetas para evitar saltos de pantalla (*CLS = 0*) y texto alternativo (`alt`) en todas las fotos.
- **Botón de WhatsApp visible y contextual:** siempre accesible con el mensaje prellenado según la pantalla actual (consulta de talla o seguimiento de pedido).

## Estándares de diseño y herramientas Frontend adoptadas
1. **Taste Skill (Jerarquía visual y carácter deportivo):**
   - Evitar plantillas genéricas: contraste atlético marcado entre el encabezado negro (`#0A0A0A`), el fondo blanco puro (`#FFFFFF`), los bordes metálicos (`#C9CED3`) y el acento puntual en verde neón (`#39FF14`).
   - Tipografía expresiva en títulos (`Barlow Condensed` en negrita cursiva y mayúsculas deportivas) combinada con `Inter` legible en textos y `tabular-nums` en precios y tablas por mayor.
2. **Emil Kowalski + Impeccable (Micro-interacciones rápidas y pulido táctil):**
   - Transiciones cortas y con propósito (`150 ms–220 ms cubic-bezier(0.22, 1, 0.36, 1)`) solo en `transform` y `opacity`.
   - Cajón lateral (*drawer*) del carrito fluido con Alpine.js + HTMX sin recargar la página.
   - Respuesta táctil inmediata al elegir una talla (muestra stock disponible al instante) y al tocar «Copiar número de Yape» (cambia a «¡Copiado!» con ícono de check durante 2 segundos).
   - Respeto automático a `prefers-reduced-motion: reduce`.
3. **UI UX Pro Max (Heurísticas de conversión e-commerce móvil):**
   - **Barra fija inferior (*sticky bottom bar*) en celular** dentro de la ficha de producto con la talla elegida, el precio actualizado y el CTA único «Agregar al carrito» siempre al alcance del pulgar.
   - **Tabla de ahorro por mayor visible de un vistazo:** resalta cuánto ahorra el cliente por unidad al llevar 3, 6 o 12 prendas.
   - **Indicadores de stock honestos:** insignia «Últimas N unidades» cuando el stock está bajo el umbral y bloqueo visual claro de tallas agotadas.
   - **Estados vacíos con salida clara:** si el carrito o una búsqueda están vacíos, mostrar un botón directo para ver las camisetas destacadas o consultar a Richard por WhatsApp.
4. **Playwright + Figma MCP (Verificación visual y E2E):**
   - **Playwright (obligatorio desde Fase 1):** valida automáticamente las pantallas en resolución celular (`360×800`) y desktop (`1280×800`), comprueba que no existan enlaces rotos y ejecuta el flujo completo de compra sin errores.
   - **Figma MCP (opcional):** si existe una maqueta en Figma se conecta por MCP; si no, el diseño se construye directamente como prototipo interactivo en HTML + Tailwind CSS siguiendo este documento y se valida en el navegador.

## Pantallas públicas
1. **Inicio/catálogo:**
   - **Encabezado negro (`#0A0A0A`)** con logo de Emuná Sport y botón del carrito con contador en vivo.
   - **Hero Video Banner deportivo al inicio:** reproduce en bucle silencioso (`autoplay muted loop playsinline`) los videos de marca de `03-Diseno-Tecnico/assets/banners-inicio/` (`banner_1.mp4`, `banner_3.mp4` y `banner_2.mp4`) con capa oscura de contraste, titular en `Barlow Condensed` cursiva y **CTA principal `#39FF14` («Ver catálogo disponible»)**.
   - **Categorías como chips** desplazables con el dedo y cuadrícula de **2 columnas en celular** (4 en desktop).
   - **Tarjeta de camiseta profesional (evolución del formato de WhatsApp de Richard):** foto en WebP (miniatura ~400 px, `loading="lazy"`, `aspect-ratio: 4/5`, `alt` descriptivo), insignia de descuento automática (ej. `-21%`) si tiene `precio_anterior`, nombre (ej. «Argentina x Messi #10»), **precio actual grande (`S/ 55.00`) junto al precio regular tachado (`S/ 69.90`)**, tallas disponibles visibles (`S · M · L · XL`) y aviso «últimas unidades» o «agotado».
   - Pie de página con enlaces a `/aviso-legal/`, `/privacidad/` y `/cookies/` más aviso discreto de cookies en la primera visita.
2. **Producto:** galería deslizable (`Swiper`), nombre, precio unitario y tabla de precios por mayor, selector de talla con stock visible, cantidad, **CTA único «Agregar al carrito» (`#39FF14`)** y botón secundario de consulta por WhatsApp. Incluye metadatos OpenGraph y datos estructurados JSON-LD (`Product`).
3. **Carrito:** cajón/lista editable con HTMX, ahorro por mayor visible, subtotal, aviso «el delivery se cotiza aparte», **CTA único «Continuar con mis datos» (`#39FF14`)**.
4. **Datos y entrega (Checkout):** selector visual de modalidad (`AGENCIA`, `DELIVERY_LIMA`, `PUNTO_ENCUENTRO`, `RECOJO`), campos dinámicos según la modalidad elegida, protección antispam invisible (**Cloudflare Turnstile** + honeypot), casilla de aceptación de política de privacidad y **CTA único «Confirmar y generar pedido» (`#39FF14`)**.
5. **Pedido enviado:** código único, resumen, **CTA principal «Enviar a Richard por WhatsApp» (`#39FF14`)** y botón secundario «Descargar PDF».
6. **Pedido cotizado (pago):** total final con envío incluido, titular verificado, número de Yape con botón «Copiar» y QR, **CTA principal «Ya yapeé – Enviar comprobante por WhatsApp» (`#39FF14`)**.
7. **Páginas `404.html` y `500.html` personalizadas:** diseño de Emuná Sport con botón para volver al catálogo o escribir a Richard por WhatsApp.

## Panel para Richard
Pensado para usarse desde el celular: lista de pedidos con filtros por estado y fecha, búsqueda por código, nombre o teléfono; acciones rápidas «Cotizar», «Confirmar pago», «Registrar envío»; botones de WhatsApp; gestión de productos con carga de varias fotos; historial de stock. Dashboard con las alertas del doc 02.

## Contenido de marca
Nombre «Emuná Sport», lema «Estilo deportivo». Tono cercano y directo. No usar nombres de clubes ni marcas en textos por defecto.
