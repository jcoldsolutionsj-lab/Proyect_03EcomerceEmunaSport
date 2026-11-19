"""Helpers reutilizables de presentación y tooltips para el panel administrativo."""
from django.utils.html import format_html
from django.utils.safestring import SafeString


def encabezado_con_tooltip(titulo: str, explicacion: str) -> SafeString:
    """Genera un encabezado de columna para Django Admin con ícono formal PNG de ayuda.

    Qué hace:      Combina el título visible y un ícono PNG formal con tooltip nativo.
    Va hacia:      Retorna SafeString compatible con @admin.display(description=...).
    Depende de:    django.utils.html.format_html y archivo /static/toltip.png.
    Cuándo usarla: En las tablas del admin de Pedidos, Envíos, Variantes y Movimientos.
    Si no opera:   Si el texto contiene comillas, format_html las escapa automáticamente.
    """
    return format_html(
        '{} <img src="/static/toltip.png" alt="Ayuda" title="{}" '
        'style="width:14px;height:14px;object-fit:contain;vertical-align:middle;'
        'margin-left:4px;cursor:help;display:inline-block;" />',
        titulo,
        explicacion,
    )
