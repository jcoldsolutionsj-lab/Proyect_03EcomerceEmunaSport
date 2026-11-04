# Bitácora de sesiones

Una entrada breve por sesión de trabajo, la más reciente **arriba**. Cada entrada responde: qué se hizo, qué se decidió, qué queda.

## 2026-11-03 – Git, diagramas y estándar de base de datos
- **Hecho:** `git init` en la raíz (rama `main`) con `.gitignore` y `.gitattributes`. `LEEME.txt` en todas las carpetas. Diagramas UML de actividades y estados (Mermaid) en `01-Relevamiento/diagramas/`. Se leyó el PDF de estándares y se adaptó a Django/PostgreSQL.
- **Creado:** `03-Diseno-Tecnico/12-estandar-base-datos.md`, `base-datos/diccionario-datos.md`, `base-datos/modelo-er.md`, carpetas `base-datos/scripts` y `scripts-bd`, `estandares/` con el PDF (renombrado `estandares-area-desarrollo-2.pdf`).
- **Decidido:** un solo repositorio git en la raíz (reemplaza la idea de repo propio en `04-Desarrollo/`). Nombres físicos de la base en inglés con el estándar `TBL_`/prefijo de 3 letras. Sin procedimientos almacenados para la lógica.
- **Incidente:** un comando auxiliar de PowerShell usó el alias `rd` (Remove-Item) y borró 4 archivos sin commit: docs 04 y 05, `ESTANDAR-ESTRUCTURA.md` y las reglas de la IA. Se reconstruyeron los tres primeros desde el contexto de la conversación. El doc 05 se reconstruyó solo en parte y requiere revisión. Lección: hacer el primer commit apenas existan los documentos.
- **Queda:** crear el remoto privado y el primer commit; revisar el doc 05; decidir los pendientes técnicos del doc 11.

## 2026-11-03 – Orden del proyecto
- **Hecho:** se revisó la estructura inicial. Se renombraron las carpetas a `00` … `06` sin espacios ni tildes. Se repartieron los documentos 01 al 11 por propósito. Se movieron `.agents/rules/` a la raíz y el logo a `03-Diseno-Tecnico/assets/`.
- **Creado:** `ESTANDAR-ESTRUCTURA.md`, `ESTADO-ACTUAL.md`, esta bitácora y un `LEEME.md` en `04-Desarrollo/` y `06-Observaciones-Piloto/`.
- **Decidido:** el código irá en `04-Desarrollo/` como repositorio git propio. La IA lee `ESTADO-ACTUAL.md` al empezar y lo actualiza al terminar.
- **Queda:** aprobar el plan de la Fase 0 y la Fase 1.
