# 06 – Diagrama de actividades: cargar un producto al catálogo

Richard (o Jonathan) carga productos desde el panel de administración. Fuente: `02-reglas-negocio.md` (Catálogo, Precios, Stock).

```mermaid
flowchart TD
  INI(("Inicio")) --> g1["Entrar al panel de administración"]
  g1 --> g2{"¿Existe la categoría?"}
  g2 -- "No" --> g3["Crear categoría"]
  g2 -- "Sí" --> g4
  g3 --> g4["Crear producto: nombre, descripción,<br/>categoría y precio por unidad (SKU tipo EMU-001)"]
  g4 --> g5{"¿El producto tiene marca visible<br/>y la opción de marcas está activa?"}
  g5 -- "Sí" --> g6["Completar el campo marca"]
  g5 -- "No (por defecto)" --> g7
  g6 --> g7["Subir fotos"]
  g7 --> g8["El sistema genera miniatura (~400 px)<br/>y detalle (~900 px) en WebP<br/>y guarda el original privado"]
  g8 --> g9["Crear variantes: talla obligatoria,<br/>color y modelo opcionales"]
  g9 --> g10["Registrar stock inicial por talla<br/>(movimiento IN)"]
  g10 --> g11{"¿Hay precio por mayor?"}
  g11 -- "Sí" --> g12["Agregar reglas: desde N unidades, precio S/ X"]
  g11 -- "No" --> g13
  g12 --> g13{"¿Activar el producto?"}
  g13 -- "Sí" --> g14["Producto activo: visible en la web<br/>(tallas sin stock se ven agotadas)"]
  g13 -- "No" --> g15["Producto oculto"]
  g14 --> FIN(("Fin"))
  g15 --> FIN
```

## Notas
- El stock inicial se registra con un `StockMovement` de tipo `IN`, no escribiendo el número a mano.
- El catálogo no muestra marcas ni nombres de clubes salvo que el producto lo tenga configurado.
- Alerta de stock bajo: umbral configurable por producto, con valor por defecto en Ajustes.
