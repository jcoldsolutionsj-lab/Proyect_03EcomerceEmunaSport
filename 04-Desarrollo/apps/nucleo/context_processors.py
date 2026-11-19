"""Procesadores de contexto para inyectar ajustes de la tienda y carrito en las plantillas."""
from typing import Any

from django.conf import settings
from django.http import HttpRequest

from apps.pedidos.selectores import obtener_carrito_detallado

from .selectores import obtener_configuracion_tienda


def contexto_tienda(request: HttpRequest) -> dict[str, Any]:
    """Expone la configuración de la tienda, el carrito en sesión y claves públicas en plantillas.

    Qué hace:      Obtiene ConfiguracionTienda, carrito detallado y variables de analítica/Turnstile.
    Va hacia:      Devuelve un diccionario disponible en base.html y demás plantillas.
    Depende de:    obtener_configuracion_tienda(), obtener_carrito_detallado() y settings.
    Cuándo usarla: En cada renderizado de plantilla mediante TEMPLATES['OPTIONS']['context_processors'].
    Si no opera:   Si la BD aún no está migrada en un test aislado, retorna valores por defecto seguros.
    """
    try:
        configuracion = obtener_configuracion_tienda()
    except Exception:
        configuracion = None

    try:
        carrito = obtener_carrito_detallado(request.session)
    except Exception:
        carrito = {
            "items": [],
            "total_unidades": 0,
            "subtotal": "0.00",
            "ahorro_mayorista": "0.00",
            "tiene_descuento_mayorista": False,
            "esta_vacio": True,
        }

    return {
        "tienda_config": configuracion,
        "carrito": carrito,
        "SITE_URL": getattr(settings, "SITE_URL", "http://127.0.0.1:8000"),
        "GA4_MEASUREMENT_ID": getattr(settings, "GA4_MEASUREMENT_ID", ""),
        "CLOUDFLARE_BEACON_TOKEN": getattr(settings, "CLOUDFLARE_BEACON_TOKEN", ""),
        "TURNSTILE_SITE_KEY": getattr(settings, "TURNSTILE_SITE_KEY", ""),
    }
