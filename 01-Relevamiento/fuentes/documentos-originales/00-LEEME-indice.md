# Emuná Sport – Índice de documentos

Estos documentos describen la tienda web de Emuná Sport. Se actualizan a medida que Richard dé observaciones. Cuando cambie algo, se edita primero el documento y se anota en el 11.

| N.º | Documento | Para qué sirve |
|---|---|---|
| 00 | Índice (este) | Orden y cómo usar los documentos |
| 01 | Visión y alcance | Qué se construye y qué no |
| 02 | Reglas de negocio | Catálogo, precios, stock, envío, pagos |
| 03 | Flujo de pedidos y estados | Paso a paso y transiciones permitidas |
| 04 | Modelo de datos | Tablas, campos y reglas de integridad |
| 05 | Arquitectura y stack | Tecnologías, apps, capas, estructura de carpetas |
| 06 | Diseño y UI | Colores, tipografía, pantallas |
| 07 | Seguridad y datos personales | Protección de DNI, accesos, límites |
| 08 | Despliegue y entornos | Local, demo en Render, producción |
| 09 | Referencias (repos y librerías) | Dónde mirar para no reinventar |
| 10 | Plan por fases | Qué se hace primero y cómo se acepta |
| 11 | Decisiones y cambios | Bitácora y pendientes |

## Orden de lectura para la IA
1. Reglas en `.agents/rules/00-emuna-proyecto.md` (siempre activas).
2. 01 → 02 → 03 → 04 antes de tocar modelos o lógica.
3. 05 y 07 antes de crear apps, endpoints o configuración.
4. 06 antes de crear plantillas.
5. 10 para saber qué fase toca. 11 para ver decisiones recientes.

## Cómo instalar en Antigravity
- Copia la carpeta `.agents/rules/` en la raíz del repositorio (Antigravity también reconoce `.agent/rules/` por compatibilidad).
- Copia la carpeta `docs/` y `assets/` en la raíz.
- Cada archivo de reglas tiene un límite de 12,000 caracteres. Por eso las reglas son cortas y apuntan a `docs/`.
- En la primera conversación pide: «Lee `.agents/rules` y `docs/`, y propón el plan de implementación de la Fase 0 y la Fase 1. No escribas código hasta que yo apruebe el plan».
