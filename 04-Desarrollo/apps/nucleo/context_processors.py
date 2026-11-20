"""Procesadores de contexto para inyectar ajustes de la tienda y carrito en las plantillas."""
from typing import Any

from django.conf import settings
from django.http import HttpRequest

from apps.pedidos.selectores import obtener_carrito_detallado

from .selectores import obtener_configuracion_tienda


def _url_recurso_r2_o_static(clave_r2: str, ruta_static: str) -> str:
    """Devuelve la URL en Cloudflare R2 cuando está configurado o un fallback estático seguro."""
    r2_pub = str(getattr(settings, "R2_PUBLIC_URL", "") or "").strip().rstrip("/")
    if r2_pub:
        return f"{r2_pub}/{clave_r2.lstrip('/')}"
    static_url = str(getattr(settings, "STATIC_URL", "/static/") or "/static/")
    if not static_url.endswith("/"):
        static_url += "/"
    return f"{static_url}{ruta_static.lstrip('/')}"


def contexto_tienda(request: HttpRequest) -> dict[str, Any]:
    """Expone la configuración de la tienda, el carrito en sesión y claves públicas en plantillas.

    Qué hace:      Obtiene ConfiguracionTienda, carrito detallado y variables de analítica/Turnstile/R2.
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
        "URL_LOGO_ANIMADO": _url_recurso_r2_o_static(
            "banners/Logo_animado.mp4", "banners-inicio/Logo_animado.mp4"
        ),
        "URL_BANNER_1": _url_recurso_r2_o_static(
            "banners/banner_1.mp4", "banners-inicio/banner_1.mp4"
        ),
        "URL_BANNER_2": _url_recurso_r2_o_static(
            "banners/banner_2.mp4", "banners-inicio/banner_2.mp4"
        ),
        "URL_BANNER_3": _url_recurso_r2_o_static(
            "banners/banner_3.mp4", "banners-inicio/banner_3.mp4"
        ),
        "URL_CALIDAD_1": _url_recurso_r2_o_static(
            "webp/argentina_1.webp",
            "productos-demo/ARGENTINA 2026 - 2027/webp/argentina_1.webp",
        ),
        "URL_CALIDAD_2": _url_recurso_r2_o_static(
            "webp/argentina_2.webp",
            "productos-demo/ARGENTINA 2026 - 2027/webp/argentina_2.webp",
        ),
        "URL_CALIDAD_3": _url_recurso_r2_o_static(
            "webp/argentina_3.webp",
            "productos-demo/ARGENTINA 2026 - 2027/webp/argentina_3.webp",
        ),
        "URL_CALIDAD_4": _url_recurso_r2_o_static(
            "webp/argentina_4.webp",
            "productos-demo/ARGENTINA 2026 - 2027/webp/argentina_4.webp",
        ),
        "URL_CALIDAD_5": _url_recurso_r2_o_static(
            "webp/argentina_5.webp",
            "productos-demo/ARGENTINA 2026 - 2027/webp/argentina_5.webp",
        ),
    }
