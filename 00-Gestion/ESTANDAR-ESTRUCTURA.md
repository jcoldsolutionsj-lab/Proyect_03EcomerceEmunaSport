# Estándar de estructura de proyecto (reutilizable)

Este estándar sirve para cualquier proyecto. Cambia el contenido, no las carpetas. Cada carpeta responde una pregunta y tiene un solo propósito, para que una persona o una IA sepa dónde mirar y dónde guardar.

## Carpetas

| Carpeta | Pregunta que responde | Qué va dentro | Quién la escribe |
|---|---|---|---|
| `.agents/rules/` | ¿Cómo debe trabajar la IA? | Reglas cortas y siempre activas. Apuntan a los documentos, no los repiten. | Humano + IA |
| `00-Gestion/` | ¿Dónde estamos y por qué? | `ESTADO-ACTUAL`, `BITACORA-sesiones`, decisiones y cambios, riesgos, índice. | IA y humano, **cada sesión** |
| `01-Relevamiento/` | ¿Qué necesita el cliente? | Visión, reglas de negocio, flujos. `diagramas/` guarda los diagramas UML (Mermaid); `fuentes/` guarda chats, capturas y archivos originales sin tocar. | Humano + IA |
| `02-Planificacion/` | ¿Qué hacemos y en qué orden? | Plan por fases, criterios de aceptación, backlog. | Humano + IA |
| `03-Diseno-Tecnico/` | ¿Cómo se construye? | Modelo de datos, arquitectura, UI, seguridad, referencias, estándar de base de datos, `base-datos/`, `estandares/` y `assets/`. | Humano + IA |
| `04-Desarrollo/` | ¿Dónde está el código? | El código de la aplicación. Va en el mismo repositorio git del proyecto. | IA + humano |
| `05-Despliegue/` | ¿Cómo se publica y se opera? | Entornos, guías de despliegue, checklist de salida a producción. | Humano + IA |
| `06-Observaciones-Piloto/` | ¿Qué dijo el cliente al probarlo? | Una nota por ronda de pruebas, con prioridad y decisión tomada. | Humano |

## LEEME.txt en cada carpeta
Toda carpeta lleva un `LEEME.txt` con el mismo formato: **nivel de información**, propósito, qué va, qué no va y quién lo actualiza. Una carpeta nueva nace con su `LEEME.txt` (además evita que git ignore carpetas vacías).

## Regla de oro: una sola fuente de verdad
- Cada dato vive en **un** documento. Los demás lo enlazan.
- Si el código y los documentos se contradicen, se avisa y se decide cuál actualizar. No se decide en silencio.
- Los datos sensibles (secretos, DNI, QR de pago, boletas) **nunca** entran al repositorio.

## Memoria de continuidad (para que la IA no se pierda)
Una IA no recuerda conversaciones anteriores. Lo que no está escrito en estas carpetas, para ella no existe.

1. **Al empezar una sesión**, la IA lee en este orden:
   1. `.agents/rules/` (automático).
   2. `00-Gestion/ESTADO-ACTUAL.md` (dónde quedamos y cuál es el siguiente paso).
   3. Los últimos registros de `00-Gestion/BITACORA-sesiones.md` y de `00-Gestion/11-decisiones-cambios.md`.
   4. Solo los documentos que necesite para la tarea (ver «Orden de lectura» en `00-LEEME-indice.md`).
2. **Al terminar una sesión**, la IA:
   1. Actualiza `ESTADO-ACTUAL.md`: hecho, en curso, siguiente paso, bloqueos.
   2. Agrega una entrada breve en `BITACORA-sesiones.md`.
   3. Si cambió una regla o una decisión, edita el documento correspondiente y agrega una línea en `11-decisiones-cambios.md`.
3. `ESTADO-ACTUAL.md` se mantiene **corto** (una pantalla). El detalle va en la bitácora.

## Cómo usar este estándar en otro proyecto
1. Copia la estructura de carpetas, los `LEEME.txt` y los archivos `ESTANDAR-ESTRUCTURA`, `ESTADO-ACTUAL`, `BITACORA-sesiones` y `00-LEEME-indice`.
2. Escribe las reglas del proyecto en `.agents/rules/` (cortas, con enlaces a los documentos).
3. Rellena `01-Relevamiento/` antes de diseñar y `02-Planificacion/` antes de programar.

## Convenciones de nombres
- Carpetas: `NN-Nombre-Sin-Tildes` (dos dígitos, sin espacios, tildes ni «ñ»).
- Documentos: `NN-tema-en-minusculas.md`.
- Fechas en formato `AAAA-MM-DD` en documentos; `ddmmaaaa` solo en nombres de scripts SQL (estándar de base de datos).
- Diagramas: un archivo `.md` por diagrama con código Mermaid, en `01-Relevamiento/diagramas/`.
