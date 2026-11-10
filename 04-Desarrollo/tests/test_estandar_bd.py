"""Pruebas automáticas del estándar de base de datos (12-estandar-base-datos.md)."""
import re

from django.apps import apps

PATRON_TABLA = re.compile(r"^TBL_[RTLH][A-Z0-9_]+$")
PATRON_COLUMNA = re.compile(r"^[A-Z]{3}_[NCDBO][A-Z0-9_]+$")
APPS_PROPIAS = {"nucleo", "catalogo", "inventario", "pedidos", "envios", "tablero"}


def test_todas_las_tablas_y_columnas_propias_cumplen_estandar_tbl_mayusculas() -> None:
    """Verifica que todos los modelos de las apps propias cumplan el estándar físico TBL_.

    Qué hace:      Recorre los modelos registrados en APPS_PROPIAS y audita db_table y db_column.
    Va hacia:      Asegura el cumplimiento del doc 12 (nombres físicos en MAYÚSCULAS y español).
    Depende de:    django.apps.apps y expresiones regulares PATRON_TABLA / PATRON_COLUMNA.
    Cuándo usarla: En cada ejecución de pytest dentro del flujo de integración continua.
    Si no opera:   Falla el test indicando exactamente qué modelo o campo viola el estándar.
    """
    modelos_propios = [
        modelo
        for modelo in apps.get_models()
        if modelo._meta.app_label in APPS_PROPIAS
    ]
    assert len(modelos_propios) >= 2, "Deben existir al menos los modelos de la Fase 0."

    for modelo in modelos_propios:
        nombre_tabla = modelo._meta.db_table
        assert PATRON_TABLA.match(nombre_tabla), (
            f"El modelo {modelo.__name__} tiene db_table='{nombre_tabla}', "
            "que no cumple el formato TBL_[R|T|L|H]NOMBRE en MAYÚSCULAS."
        )
        for campo in modelo._meta.concrete_fields:
            nombre_columna = campo.column
            assert PATRON_COLUMNA.match(nombre_columna), (
                f"El campo {modelo.__name__}.{campo.name} tiene columna '{nombre_columna}', "
                "que no cumple el formato PPP_[N|C|D|B|O]CUERPO en MAYÚSCULAS."
            )
