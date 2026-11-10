# Guía de Ejecución Local – `04-Desarrollo/`

Aquí vive el código fuente de Django de **Emuná Sport**.

## Comandos principales (ejecutar desde la raíz `D:\JONATHAN\Proyectos\EcomerceEmunaSport`)

| Qué quieres hacer | Comando en PowerShell |
|---|---|
| **Aplicar migraciones** | `.\.venv\Scripts\python.exe 04-Desarrollo/manage.py migrate` |
| **Cargar usuarios y datos base (Fase 0)** | `.\.venv\Scripts\python.exe 04-Desarrollo/manage.py preparar_local` |
| **Iniciar el servidor web local** | `.\.venv\Scripts\python.exe 04-Desarrollo/manage.py runserver` |
| **Correr las pruebas (`pytest`)** | `.\.venv\Scripts\pytest.exe -c 04-Desarrollo/pyproject.toml 04-Desarrollo/tests` |
| **Correr el linter (`ruff`)** | `.\.venv\Scripts\ruff.exe check 04-Desarrollo` |

## Accesos locales creados por `preparar_local`
- **URL Inicio:** `http://127.0.0.1:8000/`
- **URL Panel Admin:** `http://127.0.0.1:8000/gestion/`
  - **Superusuario (Jonathan):** `jonathan` / `Emuna2026!`
  - **Dueño (Richard):** `richard` / `Emuna2026!`
