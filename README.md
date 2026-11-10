# ⚡ Emuná Sport – E-commerce («Estilo deportivo»)

Tienda web oficial de **Emuná Sport** para venta de camisetas deportivas al por menor y por mayor en el Perú, con carrito de compras, cotización de envíos a provincia (**Shalom / Olva**), entregas en **punto de encuentro en Lima**, pago con **Yape** y panel de administración móvil para **Richard** (dueño) y **Jonathan Vera Segura** (responsable técnico).

---

## 🚀 Guía rápida para ejecutar y ver el proyecto en tu PC (Windows PowerShell)

Abre una terminal **PowerShell** en la raíz del proyecto (`D:\JONATHAN\Proyectos\EcomerceEmunaSport`) y ejecuta estos comandos:

### 1. Activar el entorno virtual (ya instalado en `.venv`)
```powershell
.\.venv\Scripts\Activate.ps1
```
*(Si prefieres no activarlo, puedes llamar directamente a `.\.venv\Scripts\python.exe` como se muestra abajo).*

### 2. Aplicar migraciones y preparar datos/usuarios locales
```powershell
.\.venv\Scripts\python.exe 04-Desarrollo/manage.py migrate
.\.venv\Scripts\python.exe 04-Desarrollo/manage.py preparar_local
```
Esto deja listos automáticamente:
- **Superusuario técnico (acceso total):** usuario `jonathan` / contraseña `Emuna2026!`
- **Usuario operativo (grupo `Dueño`):** usuario `richard` / contraseña `Emuna2026!`
- **Configuración de la tienda (`TBL_RCONFIGURACION_TIENDA`)** y **Métodos de pago (`TBL_RMETODO_PAGO`: Yape y Efectivo)**.

### 3. Levantar el servidor para verlo en tu navegador
```powershell
.\.venv\Scripts\python.exe 04-Desarrollo/manage.py runserver
```
Luego abre en tu navegador:
- **Inicio / Estado del proyecto:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Panel de Gestión (Admin de Django):** [http://127.0.0.1:8000/gestion/](http://127.0.0.1:8000/gestion/) *(ingresa con `jonathan` o `richard` y clave `Emuna2026!`)*
- **Endpoint de Salud JSON:** [http://127.0.0.1:8000/salud/](http://127.0.0.1:8000/salud/)

---

## 🧪 Cómo ejecutar las pruebas y el linter (`pytest` + `ruff`)

Antes de cada commit, puedes verificar que todo el código y el estándar de base de datos (`TBL_` en MAYÚSCULAS) pasen al 100%:

```powershell
# 1. Verificar estilo y calidad de código con Ruff
.\.venv\Scripts\ruff.exe check 04-Desarrollo

# 2. Ejecutar toda la suite de pruebas con Pytest
.\.venv\Scripts\pytest.exe -c 04-Desarrollo/pyproject.toml 04-Desarrollo/tests

# 3. Validar y regenerar el Diccionario de Datos (.md, .xlsx y ER)
.\.venv\Scripts\python.exe 03-Diseno-Tecnico/base-datos/generar_diccionario.py
```

---

## 📂 Mapa de carpetas del repositorio

| Carpeta | Contenido |
|---|---|
| [`.agents/rules/`](.agents/rules/00-emuna-proyecto.md) | Reglas permanentes de la IA (idioma español, docstrings de 5 líneas, seguridad, GitFlow) |
| [`00-Gestion/`](00-Gestion/00-LEEME-indice.md) | Índice maestro, [`ESTADO-ACTUAL.md`](00-Gestion/ESTADO-ACTUAL.md), [`BITACORA-sesiones.md`](00-Gestion/BITACORA-sesiones.md) y decisiones |
| [`01-Relevamiento/`](01-Relevamiento/01-vision-alcance.md) | Visión, reglas de negocio, estados del pedido y 9 diagramas UML en [`diagramas/`](01-Relevamiento/diagramas/) |
| [`02-Planificacion/`](02-Planificacion/10-plan-fases.md) | Plan de implementación paso a paso (Fases 0 a 6) |
| [`03-Diseno-Tecnico/`](03-Diseno-Tecnico/05-arquitectura-stack.md) | Modelo de datos, UI, blindaje anti-hacking, [`base-datos/`](03-Diseno-Tecnico/base-datos/diccionario-datos.md), [`api/openapi.yaml`](03-Diseno-Tecnico/api/openapi.yaml), [`pruebas-carga-k6/`](03-Diseno-Tecnico/pruebas-carga-k6/plan-pruebas-k6.md) y [`assets/`](03-Diseno-Tecnico/assets/LEEME.txt) |
| [`04-Desarrollo/`](04-Desarrollo/README.md) | Código fuente de la aplicación Django en español |
| [`05-Despliegue/`](05-Despliegue/14-flujo-git-devops-github.md) | Entornos, Manual GitFlow DevOps (`.md` y `.docx`) y [`15-checklist-antes-de-lanzar-web.md`](05-Despliegue/15-checklist-antes-de-lanzar-web.md) |
| [`06-Observaciones-Piloto/`](06-Observaciones-Piloto/LEEME.txt) | Observaciones de Richard durante las pruebas del piloto |
