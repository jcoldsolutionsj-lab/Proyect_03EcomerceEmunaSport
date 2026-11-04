# Bitácora de sesiones

Una entrada breve por sesión de trabajo, la más reciente **arriba**. Cada entrada responde: qué se hizo, qué se decidió, qué queda.

## 2026-11-03 (cierre) – Restauración del doc 05, español total, Excel de BD, cita en Lima y Swagger
- **Hecho:**
  - Se restauró el doc `05-arquitectura-stack.md` desde la carpeta `docs/` que dejó Jonathan y se archivaron los originales en `01-Relevamiento/fuentes/documentos-originales/`.
  - Se pasaron el modelo lógico, el diccionario físico y los diagramas a **español** con nombres de BD en **MAYÚSCULAS**.
  - Se creó `03-Diseno-Tecnico/base-datos/generar_diccionario.py` (fuente única con validaciones) y se generaron `diccionario-datos.md`, `diccionario-datos.xlsx` (Excel con 5 hojas y filtros) y `modelo-er.md` (13 tablas, 132 columnas).
  - Se incorporó la modalidad `PUNTO_ENCUENTRO` en Lima (entrega en mano y cobro por Yape/efectivo en el momento) y la venta `PRESENCIAL` directa en los docs 02, 03, 04 y en el nuevo diagrama `08-actividad-entrega-lima-y-venta-presencial.md`.
  - Se creó la especificación de la API y Swagger: `03-Diseno-Tecnico/13-especificacion-api-swagger.md` y `03-Diseno-Tecnico/api/openapi.yaml` (19 rutas validadas con OpenAPI 3.0.3).
- **Decidido:** código y BD en español; tablas/columnas en MAYÚSCULAS; docstring obligatorio de 5 preguntas en cada función.
- **Queda:** subir al remoto privado y aprobar el plan de la Fase 0 y la Fase 1.

## 2026-11-03 – Git, diagramas y estándar de base de datos
- **Hecho:** `git init` en la raíz (rama `main`) con `.gitignore` y `.gitattributes`. `LEEME.txt` en todas las carpetas. Diagramas UML de actividades y estados (Mermaid) en `01-Relevamiento/diagramas/`. Se leyó el PDF de estándares y se adaptó a Django/PostgreSQL.
- **Creado:** `03-Diseno-Tecnico/12-estandar-base-datos.md`, `base-datos/diccionario-datos.md`, `base-datos/modelo-er.md`, carpetas `base-datos/scripts` y `scripts-bd`, `estandares/` con el PDF (renombrado `estandares-area-desarrollo-2.pdf`).
- **Decidido:** un solo repositorio git en la raíz. Sin procedimientos almacenados para la lógica.

## 2026-11-03 – Orden del proyecto
- **Hecho:** se revisó la estructura inicial. Se renombraron las carpetas a `00` … `06` sin espacios ni tildes. Se repartieron los documentos 01 al 11 por propósito. Se movieron `.agents/rules/` a la raíz y el logo a `03-Diseno-Tecnico/assets/`.
- **Creado:** `ESTANDAR-ESTRUCTURA.md`, `ESTADO-ACTUAL.md` y esta bitácora.
