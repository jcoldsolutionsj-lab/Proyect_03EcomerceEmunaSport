"""Etiquetas y filtros de plantilla para el panel administrativo de Emuná Sport."""

from typing import Any

from django import template

register = template.Library()


@register.filter
def obtener_tooltip_inline(opts: Any, nombre_campo: str) -> str:
    """Devuelve el texto de ayuda configurado para una columna dentro de un inline."""
    # Qué hace: Busca en el diccionario tooltips_columnas del inline el texto para la columna dada.
    # Va hacia: Las plantillas tabular.html y stacked.html del panel administrativo Django.
    # Depende de: Atributo opcional tooltips_columnas definido en la clase InlineAdmin.
    # Cuándo usarla: Al renderizar cabeceras de columnas y campos en formularios inline.
    # Si no opera: Retorna cadena vacía y deja intacto el comportamiento nativo de help_text.
    tooltips = getattr(opts, "tooltips_columnas", None)
    if isinstance(tooltips, dict):
        return str(tooltips.get(nombre_campo, ""))
    return ""
