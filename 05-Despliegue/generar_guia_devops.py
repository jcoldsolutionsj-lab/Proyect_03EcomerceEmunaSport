# -*- coding: utf-8 -*-
"""Generador del documento Word de DevOps y flujo de ramas GitHub para Emuná Sport.

Qué hace:      Crea el manual en formato Word (Guia-DevOps-GitHub-Emuna-Sport.docx)
               con el modelo de ramas, versionado, comandos Git y pipeline CI/CD.
Va hacia:      05-Despliegue/Guia-DevOps-GitHub-Emuna-Sport.docx.
Depende de:    python-docx y del contenido definido en 14-flujo-git-devops-github.md.
Cuándo usarla: Cuando se actualice el proceso de ramas o despliegue: python generar_guia_devops.py
Si no opera:   Muestra un error claro si falta python-docx o si el archivo Word está abierto en pantalla.
"""
from pathlib import Path
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

CARPETA = Path(__file__).resolve().parent
RUTA_SALIDA = CARPETA / "Guia-DevOps-GitHub-Emuna-Sport.docx"


def sombrear_celda(celda, color_hex: str) -> None:
    """Pinta el fondo de una celda de tabla en Word con un color hexadecimal.

    Qué hace:      Inserta el elemento XML w:shd con el color indicado en la celda.
    Va hacia:      Modifica el objeto celda del documento Word en memoria.
    Depende de:    docx.oxml (OxmlElement y qn).
    Cuándo usarla: Al construir encabezados de tablas o bloques de código/consola.
    Si no opera:   La celda quedaría con fondo blanco sin formato.
    """
    tc_pr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def agregar_tabla(doc, encabezados, filas, anchos_cm=None) -> None:
    """Agrega una tabla con encabezado negro y texto blanco al documento Word.

    Qué hace:      Crea la tabla, aplica estilo a la primera fila y rellena todas las celdas.
    Va hacia:      Agrega una tabla al objeto Document de python-docx.
    Depende de:    sombrear_celda() y las utilidades de formato de python-docx.
    Cuándo usarla: Para mostrar el mapa de ramas, prefijos de commit y entornos de despliegue.
    Si no opera:   El documento perdería las tablas comparativas de ramas y entornos.
    """
    tabla = doc.add_table(rows=1, cols=len(encabezados))
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.style = "Table Grid"

    celdas_cab = tabla.rows[0].cells
    for i, texto in enumerate(encabezados):
        celdas_cab[i].text = ""
        p = celdas_cab[i].paragraphs[0]
        r = p.add_run(texto)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        sombrear_celda(celdas_cab[i], "0A0A0A")

    for indice_fila, fila in enumerate(filas):
        celdas = tabla.add_row().cells
        color_fondo = "F5F7F9" if indice_fila % 2 == 1 else "FFFFFF"
        for i, valor in enumerate(fila):
            celdas[i].text = ""
            p = celdas[i].paragraphs[0]
            r = p.add_run(str(valor))
            r.font.size = Pt(9)
            if i == 0:
                r.bold = True
            sombrear_celda(celdas[i], color_fondo)

    if anchos_cm:
        for fila in tabla.rows:
            for i, ancho in enumerate(anchos_cm):
                fila.cells[i].width = Cm(ancho)

    doc.add_paragraph()


def agregar_bloque_codigo(doc, lineas) -> None:
    """Inserta un bloque de comandos de consola con fuente monoespaciada y fondo gris.

    Qué hace:      Crea una tabla de 1x1 con fondo oscuro suave y fuente Consolas.
    Va hacia:      Agrega el bloque formateado al documento Word.
    Depende de:    sombrear_celda().
    Cuándo usarla: Para mostrar comandos de git y esquemas de flujo en el Word.
    Si no opera:   Los comandos se verían como texto normal y serían difíciles de copiar.
    """
    tabla = doc.add_table(rows=1, cols=1)
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.style = "Table Grid"
    celda = tabla.rows[0].cells[0]
    sombrear_celda(celda, "1E1E1E")
    p = celda.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    texto = "\n".join(lineas) if isinstance(lineas, list) else lineas
    r = p.add_run(texto)
    r.font.name = "Consolas"
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0xE8, 0xF5, 0xE9)
    doc.add_paragraph()


def agregar_subtitulo(doc, texto: str) -> None:
    """Agrega un encabezado de sección principal numerado al documento Word.

    Qué hace:      Inserta un Heading 1 con el color principal de Emuná Sport.
    Va hacia:      Agrega un párrafo de título al objeto Document.
    Depende de:    python-docx.
    Cuándo usarla: Al iniciar cada capítulo de la guía DevOps.
    Si no opera:   El documento no tendría jerarquía visual de capítulos.
    """
    h = doc.add_heading(level=1)
    r = h.add_run(texto)
    r.font.color.rgb = RGBColor(0x0A, 0x0A, 0x0A)
    r.font.size = Pt(14)


def agregar_apartado(doc, texto: str) -> None:
    """Agrega un subtítulo de segundo nivel (Heading 2) en color verde deportivo.

    Qué hace:      Inserta un Heading 2 con color #1B8F2A.
    Va hacia:      Agrega un subtítulo al objeto Document.
    Depende de:    python-docx.
    Cuándo usarla: Para cada caso práctico de comandos Git o subsección.
    Si no opera:   Los casos prácticos quedarían mezclados sin separación clara.
    """
    h = doc.add_heading(level=2)
    r = h.add_run(texto)
    r.font.color.rgb = RGBColor(0x1B, 0x8F, 0x2A)
    r.font.size = Pt(11.5)


def construir_documento() -> None:
    """Construye y guarda el archivo Guia-DevOps-GitHub-Emuna-Sport.docx completo.

    Qué hace:      Ensambla portada, tablas de ramas, flujo visual, reglas de versionado,
                   los 6 casos de comandos Git y el pipeline CI/CD.
    Va hacia:      Escribe el archivo físico Guia-DevOps-GitHub-Emuna-Sport.docx.
    Depende de:    agregar_tabla(), agregar_bloque_codigo(), agregar_subtitulo() y agregar_apartado().
    Cuándo usarla: Desde el bloque principal al ejecutar este script.
    Si no opera:   Lanza PermissionError si el archivo Word está abierto en Word al momento de guardar.
    """
    doc = Document()

    for seccion in doc.sections:
        seccion.top_margin = Cm(2.0)
        seccion.bottom_margin = Cm(2.0)
        seccion.left_margin = Cm(2.2)
        seccion.right_margin = Cm(2.2)

    estilo_normal = doc.styles["Normal"]
    estilo_normal.font.name = "Calibri"
    estilo_normal.font.size = Pt(10.5)

    # Encabezado / Portada compacta
    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r_marca = titulo.add_run("EMUNÁ SPORT – ESTILO DEPORTIVO\n")
    r_marca.bold = True
    r_marca.font.size = Pt(11)
    r_marca.font.color.rgb = RGBColor(0x1B, 0x8F, 0x2A)

    r_tit = titulo.add_run("Manual de Flujo Git, Ramas y Despliegue DevOps con GitHub")
    r_tit.bold = True
    r_tit.font.size = Pt(18)
    r_tit.font.color.rgb = RGBColor(0x0A, 0x0A, 0x0A)

    meta = doc.add_paragraph()
    r_meta = meta.add_run(
        "Desarrollador: Jonathan Vera Segura (GitHub: jhon2018)  |  "
        "Repositorio Central: jcoldsolutionsj-lab  |  Dueño del Negocio: Richard"
    )
    r_meta.italic = True
    r_meta.font.size = Pt(9.5)
    r_meta.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    intro = doc.add_paragraph(
        "Este documento define el comportamiento de las ramas en GitHub, el versionado X.Y.Z, "
        "los comandos paso a paso para cada escenario (nuevas fases, correcciones, versiones y "
        "arreglos urgentes) y cómo se conectan automáticamente con el entorno de prueba (Demo) y con Producción."
    )
    intro.paragraph_format.space_after = Pt(10)

    # 1. Mapa de ramas
    agregar_subtitulo(doc, "1. Mapa de Ramas y Entornos (GitFlow adaptado)")
    doc.add_paragraph(
        "El repositorio utiliza 2 ramas permanentes (main y develop) y 4 tipos de ramas temporales "
        "que se crean según la tarea y se eliminan tras fusionarse:"
    )

    agregar_tabla(
        doc,
        ["Rama", "Tipo", "Nace de", "Se une a", "Entorno", "Propósito y comportamiento"],
        [
            ["main", "Permanente", "—", "—", "Producción (Render + Cloudflare)",
             "Código 100% estable que usan los clientes reales. Nunca se programa directo aquí. Cada fusión lleva una etiqueta de versión (ej. v1.1.0)."],
            ["develop", "Permanente", "main", "main (vía release/*)", "Demo / Piloto (Render Demo)",
             "Rama de integración donde se unen las fases terminadas para que Richard pruebe desde su celular y dé observaciones."],
            ["feature/<nombre>", "Temporal", "develop", "develop", "Local (PC de Jonathan)",
             "Desarrollar una fase o funcionalidad nueva (ej. feature/fase-0-base, feature/fase-1-catalogo, feature/cita-lima)."],
            ["bugfix/<nombre>", "Temporal", "develop", "develop", "Local",
             "Corregir un error detectado en desarrollo o durante las pruebas del piloto de Richard en develop."],
            ["release/<X.Y.Z>", "Temporal", "develop", "main y develop", "Pre-producción",
             "Congelar una versión lista para salir a producción, generar el script sbd_ddmmaaaa.sql y publicar la versión."],
            ["hotfix/<nombre>", "Temporal", "main", "main y develop", "Urgencia en Producción",
             "Corregir un fallo urgente en producción sin arrastrar cambios de develop que aún no estén listos. Sube el número Z (ej. v1.1.1)."],
        ],
        anchos_cm=[3.2, 2.1, 2.0, 2.3, 2.8, 4.2],
    )

    # 2. Esquema visual
    agregar_subtitulo(doc, "2. Esquema Visual del Flujo de Ramas")
    agregar_bloque_codigo(
        doc,
        [
            "main (Producción)    o------------------------o (v1.1.0) -----------o (v1.1.1)",
            "                      \\                      /                     /",
            "hotfix/*               \\                    /       o-------------o (hotfix/error-pdf)",
            "                        \\                  /       /               \\",
            "release/*                \\                o-------o (release/1.1.0) \\",
            "                          \\              /         \\                 ▼",
            "develop (Piloto Demo)      o----o-------o-----------o----------------o----►",
            "                               /       / ▲         ▲",
            "feature/* y bugfix/*          o-------o  o---------o",
            "                         (feature/fase-0) (bugfix/ajuste)",
        ],
    )

    # 3. Versionado
    agregar_subtitulo(doc, "3. Estándar de Versionado X.Y.Z y Etapas")
    doc.add_paragraph(
        "Cumpliendo el Manual de Estándares del Área de Desarrollo (sección 4), toda versión se "
        "identifica con tres números v[X].[Y].[Z]:"
    )
    for item in [
        "X (Versión mayor): sube cuando hay una nueva evolución grande o cambio de interfaz general. Al subir X, Y y Z vuelven a 0.",
        "Y (Incremento funcional): sube al completar una nueva fase o módulo funcional sin romper lo anterior. Al subir Y, Z vuelve a 0.",
        "Z (Modificación / Parche / Hotfix): sube con cada corrección de errores o parche de mantenimiento.",
        "Etapa Alfa (v0.1.0 a v0.4.0 en develop): construcción de las Fases 0 a 4.",
        "Etapa Beta / Piloto (v0.5.0-beta en develop): desplegada en Render Demo para las pruebas de Richard.",
        "Etapa Estable / Producción (v1.1.0 en main): primera versión oficial en producción.",
    ]:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(item)

    # 4. Convención de commits
    agregar_subtitulo(doc, "4. Convención de Nombres de Ramas y Mensajes de Commit")
    doc.add_paragraph(
        "Los mensajes de commit se escriben siempre en español con el formato: <tipo>(<alcance>): <descripción>"
    )
    agregar_tabla(
        doc,
        ["Prefijo", "Cuándo se usa", "Ejemplo real en Emuná Sport"],
        [
            ["feat", "Nueva funcionalidad o pantalla", "feat(pedidos): agregar confirmacion de pago y entrega en cita Lima"],
            ["fix", "Corrección de un error (bugfix o hotfix)", "fix(inventario): bloquear variante con select_for_update al descontar"],
            ["docs", "Cambios en documentos, diagramas, Excel o Swagger", "docs(api): actualizar esquema de venta presencial en openapi.yaml"],
            ["refactor", "Mejora interna de código sin cambiar qué hace", "refactor(catalogo): mover calculo de precio mayorista a servicios.py"],
            ["test", "Agregar o ajustar pruebas en pytest", "test(pedidos): probar rollback cuando falta stock en una talla"],
            ["chore", "Configuración, librerías, scripts o despliegue", "chore(despliegue): configurar render.yaml y whitenoise"],
        ],
        anchos_cm=[2.2, 5.5, 8.9],
    )

    # 5. Casos prácticos paso a paso
    agregar_subtitulo(doc, "5. Guía Paso a Paso de Comandos Git por Escenario")

    agregar_apartado(doc, "Caso 1: Subir el proyecto por primera vez al repositorio remoto en GitHub")
    doc.add_paragraph(
        "Repositorio central (propietario): jcoldsolutionsj-lab  |  Desarrollador (colaborador): Jonathan Vera Segura (jhon2018)"
    )
    agregar_bloque_codigo(
        doc,
        [
            'git config user.name "jhon2018"',
            "git remote add origin https://jhon2018@github.com/jcoldsolutionsj-lab/Proyect_03EcomerceEmunaSport.git",
            "git push -u origin main",
            "git push -u origin develop",
        ],
    )

    agregar_apartado(doc, "Caso 2: Empezar una fase o funcionalidad nueva (rama feature/*)")
    doc.add_paragraph("Siempre se crea desde la rama develop actualizada:")
    agregar_bloque_codigo(
        doc,
        [
            "git checkout develop",
            "git pull origin develop",
            "git checkout -b feature/fase-0-base",
            "",
            "# Guardar cambios durante el trabajo:",
            "git add -A",
            'git commit -m "feat(nucleo): crear modelos ConfiguracionTienda y MetodoPago"',
            "git push -u origin feature/fase-0-base",
        ],
    )

    agregar_apartado(doc, "Caso 3: Terminar una funcionalidad y pasarla a develop (Render Demo)")
    doc.add_paragraph(
        "Primero se ejecutan las validaciones locales (ruff, pytest y generador del diccionario) y luego se une a develop:"
    )
    agregar_bloque_codigo(
        doc,
        [
            "ruff check .",
            "pytest",
            "python 03-Diseno-Tecnico/base-datos/generar_diccionario.py",
            "",
            "git checkout develop",
            "git pull origin develop",
            'git merge --no-ff feature/fase-0-base -m "Merge feature/fase-0-base hacia develop"',
            "git push origin develop",
            "git branch -d feature/fase-0-base",
        ],
    )

    agregar_apartado(doc, "Caso 4: Corregir una observación de Richard en el piloto (rama bugfix/*)")
    agregar_bloque_codigo(
        doc,
        [
            "git checkout develop",
            "git pull origin develop",
            "git checkout -b bugfix/ajuste-mensaje-whatsapp",
            "",
            "# ... realizar la corrección y probar ...",
            "git add -A",
            'git commit -m "fix(pedidos): incluir punto de encuentro en mensaje de WhatsApp"',
            "git checkout develop",
            'git merge --no-ff bugfix/ajuste-mensaje-whatsapp -m "Merge bugfix/ajuste-mensaje-whatsapp hacia develop"',
            "git push origin develop",
            "git branch -d bugfix/ajuste-mensaje-whatsapp",
        ],
    )

    agregar_apartado(doc, "Caso 5: Preparar y publicar una versión en Producción (release/* -> main)")
    doc.add_paragraph(
        "Cuando develop está probado y aprobado, se genera el script completo de base de datos (sbd_ddmmaaaa.sql) y se pasa a main:"
    )
    agregar_bloque_codigo(
        doc,
        [
            "git checkout develop",
            "git pull origin develop",
            "git checkout -b release/1.1.0",
            "",
            "# 1. Guardar script completo en 03-Diseno-Tecnico/base-datos/scripts-bd/sbd_ddmmaaaa.sql",
            "# 2. Actualizar 00-Gestion/11-decisiones-cambios.md y ESTADO-ACTUAL.md",
            "git add -A",
            'git commit -m "chore(release): preparar version 1.1.0 para produccion"',
            "",
            "# 3. Pasar a main y etiquetar versión:",
            "git checkout main",
            "git pull origin main",
            'git merge --no-ff release/1.1.0 -m "Release v1.1.0 a produccion"',
            'git tag -a v1.1.0 -m "Version 1.1.0 - Salida a produccion"',
            "git push origin main --tags",
            "",
            "# 4. Sincronizar en develop y borrar la rama temporal:",
            "git checkout develop",
            'git merge --no-ff release/1.1.0 -m "Sincronizar release/1.1.0 en develop"',
            "git push origin develop",
            "git branch -d release/1.1.0",
        ],
    )

    agregar_apartado(doc, "Caso 6: Corregir un fallo urgente en Producción (hotfix/* -> main y develop)")
    doc.add_paragraph(
        "Nace directamente de main para arreglar el problema rápido sin mezclar lo que esté a mitad de camino en develop:"
    )
    agregar_bloque_codigo(
        doc,
        [
            "git checkout main",
            "git pull origin main",
            "git checkout -b hotfix/error-descarga-pdf",
            "",
            "# ... corregir el error y correr pytest ...",
            "git add -A",
            'git commit -m "fix(pedidos): corregir tildes al generar PDF"',
            "",
            "# 1. Fusionar en main y subir Z (v1.1.1):",
            "git checkout main",
            'git merge --no-ff hotfix/error-descarga-pdf -m "Hotfix v1.1.1: corregir PDF"',
            'git tag -a v1.1.1 -m "Version 1.1.1 - Correccion urgente de PDF"',
            "git push origin main --tags",
            "",
            "# 2. Fusionar también en develop para no perder el arreglo:",
            "git checkout develop",
            'git merge --no-ff hotfix/error-descarga-pdf -m "Sincronizar hotfix v1.1.1 en develop"',
            "git push origin develop",
            "git branch -d hotfix/error-descarga-pdf",
        ],
    )

    # 6. Pipeline CI/CD y entornos
    agregar_subtitulo(doc, "6. Automatización CI/CD (GitHub Actions + Render)")
    doc.add_paragraph(
        "Cada vez que se sube código a GitHub, el flujo automático verifica la calidad y despliega según la rama:"
    )
    agregar_tabla(
        doc,
        ["Entorno", "Rama conectada", "Base de datos", "Qué ejecuta automáticamente"],
        [
            ["Local (Desarrollo)", "feature/* o bugfix/*", "SQLite",
             "Validación con ruff, pytest, generar_diccionario.py y openapi-spec-validator."],
            ["Demo / Piloto (Render)", "develop", "PostgreSQL Demo / SQLite con semilla",
             "Instala dependencias -> collectstatic -> migrate -> cargar_demo -> levanta gunicorn para que Richard pruebe."],
            ["Producción (Render + Cloudflare)", "main", "PostgreSQL persistente con respaldo",
             "Instala dependencias -> collectstatic -> migrate -> levanta gunicorn (nunca ejecuta cargar_demo)."],
        ],
        anchos_cm=[3.5, 3.2, 3.8, 6.1],
    )

    # 7. Reglas de oro
    agregar_subtitulo(doc, "7. Reglas de Seguridad y Control del Repositorio")
    for regla in [
        "El repositorio en GitHub debe ser PRIVADO.",
        "Proteger las ramas main y develop en GitHub (bloquear force push y exigir que las pruebas pasen antes de unir).",
        "Nunca subir archivos .env, el QR real de Yape, boletas de agencia ni DNI reales de clientes (están bloqueados en .gitignore).",
        "Antes de cerrar cualquier rama, actualizar 00-Gestion/ESTADO-ACTUAL.md y BITACORA-sesiones.md para que la IA mantenga la continuidad.",
    ]:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(regla)

    doc.save(RUTA_SALIDA)
    print(f"Documento Word generado correctamente en: {RUTA_SALIDA}")


if __name__ == "__main__":
    construir_documento()
