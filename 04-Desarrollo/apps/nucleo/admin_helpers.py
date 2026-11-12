"""Helpers reutilizables de presentación y tooltips para el panel administrativo."""
from django.utils.html import format_html
from django.utils.safestring import SafeString


def encabezado_con_tooltip(titulo: str, explicacion: str) -> SafeString:
    """Genera un encabezado de columna para Django Admin con ícono de ayuda flotante (ⓘ).

    Qué hace:      Combina el título visible y un span con atributo title explicativo.
    Va hacia:      Retorna SafeString compatible con @admin.display(description=...).
    Depende de:    django.utils.html.format_html.
    Cuándo usarla: En las tablas del admin de Pedidos, Envíos, Variantes y Movimientos.
    Si no opera:   Si el texto contiene comillas, format_html las escapa automáticamente.
    """
    return format_html(
        '{} <span title="{}" style="cursor:help;display:inline-flex;align-items:center;'
        'justify-content:center;width:15px;height:15px;border-radius:999px;'
        'background:#1E293B;color:#34D399;font-size:10px;font-weight:800;'
        'vertical-align:middle;margin-left:3px;">ⓘ</span>',
        titulo,
        explicacion,
    )
