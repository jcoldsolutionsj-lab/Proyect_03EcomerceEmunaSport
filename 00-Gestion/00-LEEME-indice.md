# Emuná Sport – Índice de documentos

Estos documentos describen la tienda web de Emuná Sport. Se actualizan a medida que Richard dé observaciones. Cuando cambie algo, se edita primero el documento y se anota en el 11. La estructura de carpetas sigue `ESTANDAR-ESTRUCTURA.md`. Cada carpeta tiene un `LEEME.txt` que explica qué nivel de información guarda.

## Mapa del proyecto
| Carpeta | Contenido |
|---|---|
| `.agents/rules/` | Reglas de la IA (siempre activas) |
| `00-Gestion/` | Estado actual, bitácora de sesiones, decisiones, estándar, este índice |
| `01-Relevamiento/` | Visión, reglas de negocio, flujo de pedidos y `fuentes/` (chat y archivos originales) |
| `02-Planificacion/` | Plan por fases |
| `03-Diseno-Tecnico/` | Datos, arquitectura, UI, seguridad, referencias y `assets/` (logo) |
| `04-Desarrollo/` | Código de la aplicación |
| `05-Despliegue/` | Entornos y despliegue |
| `06-Observaciones-Piloto/` | Observaciones de Richard por ronda de pruebas |

## Documentos
| N.º | Documento | Ubicación | Para qué sirve |
|---|---|---|---|
| 00 | Índice (este) | `00-Gestion/` | Orden y cómo usar los documentos |
| – | Estándar de estructura | `00-Gestion/ESTANDAR-ESTRUCTURA.md` | Qué va en cada carpeta y cómo mantener la continuidad |
| – | Estado actual | `00-Gestion/ESTADO-ACTUAL.md` | Dónde quedamos y siguiente paso |
| – | Bitácora de sesiones | `00-Gestion/BITACORA-sesiones.md` | Qué se hizo en cada sesión |
| 01 | Visión y alcance | `01-Relevamiento/` | Qué se construye y qué no |
| 02 | Reglas de negocio | `01-Relevamiento/` | Catálogo, precios, stock, envío, pagos |
| 03 | Flujo de pedidos y estados | `01-Relevamiento/` | Paso a paso y transiciones permitidas |
| 04 | Modelo de datos | `03-Diseno-Tecnico/` | Tablas, campos y reglas de integridad |
| 05 | Arquitectura y stack | `03-Diseno-Tecnico/` | Tecnologías, apps, capas, estructura de carpetas del código |
| 06 | Diseño y UI | `03-Diseno-Tecnico/` | Colores, tipografía, pantallas |
| 07 | Seguridad y datos personales | `03-Diseno-Tecnico/` | Protección de DNI, accesos, límites |
| 08 | Despliegue y entornos | `05-Despliegue/` | Local, demo en Render, producción |
| 09 | Referencias (repos y librerías) | `03-Diseno-Tecnico/` | Dónde mirar para no reinventar |
| 10 | Plan por fases | `02-Planificacion/` | Qué se hace primero y cómo se acepta |
| 11 | Decisiones y cambios | `00-Gestion/` | Bitácora de decisiones y pendientes |
| 12 | Estándar de base de datos | `03-Diseno-Tecnico/` | Nombres de tablas, columnas y scripts (adaptado del manual en PDF) |
| – | Diccionario de datos | `03-Diseno-Tecnico/base-datos/diccionario-datos.md` | Nombre físico de cada tabla y columna |
| – | Modelo Entidad-Relación | `03-Diseno-Tecnico/base-datos/modelo-er.md` | Diagrama de la base (Mermaid) |
| – | Diagramas UML del negocio | `01-Relevamiento/diagramas/` | Actividades, estados y actores (Mermaid) |

## Orden de lectura para la IA
1. Reglas en `.agents/rules/00-emuna-proyecto.md` (siempre activas).
2. `00-Gestion/ESTADO-ACTUAL.md` y las últimas entradas de `BITACORA-sesiones.md` y del doc 11.
3. 01 → 02 → 03 → 04 antes de tocar modelos o lógica. Los diagramas de `01-Relevamiento/diagramas/` resumen el negocio.
   Antes de crear modelos: 12 y `base-datos/diccionario-datos.md` (nombres físicos).
4. 05 y 07 antes de crear apps, endpoints o configuración.
5. 06 antes de crear plantillas.
6. 10 para saber qué fase toca.

## Cómo usar en Antigravity
- `.agents/rules/` debe estar en la raíz del proyecto abierto (Antigravity también reconoce `.agent/rules/` por compatibilidad).
- Cada archivo de reglas tiene un límite de 12,000 caracteres. Por eso las reglas son cortas y apuntan a los documentos.
- En la primera conversación pide: «Lee `.agents/rules`, `00-Gestion/ESTADO-ACTUAL.md` y los documentos, y propón el plan de implementación de la Fase 0 y la Fase 1. No escribas código hasta que yo apruebe el plan».
