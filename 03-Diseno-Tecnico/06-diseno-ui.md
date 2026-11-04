# 06 – Diseño y UI

Referencia visual: el logo en `03-Diseno-Tecnico/assets/logo-emuna-sport.png` (fondo negro, letras plateadas cromadas, rayo «E» en verde neón, lema «Estilo deportivo»). La web es **blanca**, con un encabezado negro donde se ve el logo.

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
- Mobile-first: se diseña primero para 360 px de ancho; botones grandes y fáciles de tocar.
- Pocos pasos: catálogo → producto → carrito → datos → pedido enviado → pago.
- Todo en español de Perú; montos como `S/ 45.00`.
- Estados de carga y errores claros; accesibilidad básica (contraste, etiquetas en formularios, texto alternativo en fotos).

## Pantallas públicas
1. **Inicio/catálogo:** encabezado negro con logo y botón del carrito; categorías como chips; cuadrícula de 2 columnas en celular; tarjeta con foto (miniatura, carga diferida), nombre, precio desde y aviso «últimas unidades» o «agotado».
2. **Producto:** galería, nombre, precio y precios por mayor, selector de talla con stock visible, cantidad, botón «Agregar al carrito».
3. **Carrito:** lista editable, subtotal, aviso «el delivery se cotiza aparte», botón continuar.
4. **Datos y entrega:** tipo de entrega, nombres, DNI, teléfono, agencia y referencia, aviso breve de uso de datos.
5. **Pedido enviado:** código, resumen, botón «Descargar PDF», botón «Enviar a Richard por WhatsApp».
6. **Pedido (pago):** cuando está cotizado, total final, titular, número con «copiar» y QR de Yape, instrucción de enviar el voucher por WhatsApp.

## Panel para Richard
Pensado para usarse desde el celular: lista de pedidos con filtros por estado y fecha, búsqueda por código, nombre o teléfono; acciones rápidas «Cotizar», «Confirmar pago», «Registrar envío»; botones de WhatsApp; gestión de productos con carga de varias fotos; historial de stock. Dashboard con las alertas del doc 02.

## Contenido de marca
Nombre «Emuná Sport», lema «Estilo deportivo». Tono cercano y directo. No usar nombres de clubes ni marcas en textos por defecto.
