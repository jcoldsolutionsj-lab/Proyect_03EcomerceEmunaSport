"""Configuración de navegación, insignia en tiempo real y tablero Flat Design para django-unfold."""
from decimal import Decimal
from typing import Any

from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse_lazy


def obtener_url_logo_panel(request: HttpRequest) -> str:
    """Devuelve la URL del logo de Emuná Sport para la cabecera y barra lateral del panel.

    Qué hace:      Resuelve la ruta estática de logo_emuna_transparente.png para Unfold.
    Va hacia:      Retorna str con la ruta URL del ícono institucional.
    Depende de:    django.templatetags.static.static.
    Cuándo usarla: En UNFOLD['SITE_ICON'] y favicons al renderizar /gestion/.
    Si no opera:   Si el archivo no existe en staticfiles devuelve la ruta lógica esperada.
    """
    return static("logo_emuna_transparente.png")


def obtener_url_estilo_flat_unfold(request: HttpRequest) -> str:
    """Devuelve la URL de la hoja de estilos Flat Design personalizada para /gestion/.

    Qué hace:      Resuelve static('css/emuna_flat_unfold.css') para cargarse en Unfold.
    Va hacia:      Inyecta las reglas de cero sombras, zoom 0.85, tooltips y móvil en el panel.
    Depende de:    django.templatetags.static.static y static/css/emuna_flat_unfold.css.
    Cuándo usarla: En UNFOLD['STYLES'] para aplicar diseño Flat consistente en todo /gestion/.
    Si no opera:   Unfold sigue cargando normalmente con sus estilos base Tailwind.
    """
    return static("css/emuna_flat_unfold.css")


def contar_pedidos_por_atender(request: HttpRequest) -> str | None:
    """Calcula el total de pedidos en cola activa (NUEVO o COTIZADO) para la barra lateral.

    Qué hace:      Cuenta los pedidos en estado NUEVO o COTIZADO y formatea una etiqueta breve.
    Va hacia:      Muestra insignia numérica junto al enlace 'Pedidos' en el menú de Unfold.
    Depende de:    apps.pedidos.models.Pedido y EstadoPedido.
    Cuándo usarla: En UNFOLD['SIDEBAR']['navigation'] para alertar trabajo pendiente.
    Si no opera:   Retorna None si ocurre error de consulta (ej. antes de migrar BD).
    """
    try:
        from apps.pedidos.models import EstadoPedido, Pedido

        cantidad = Pedido.objects.filter(
            estado__in=(EstadoPedido.NUEVO, EstadoPedido.COTIZADO)
        ).count()
        return str(cantidad) if cantidad > 0 else None
    except Exception:
        return None


def contar_alertas_tablero(request: HttpRequest) -> str | None:
    """Calcula el conteo de alertas operativas críticas (stock bajo o pedidos demorados).

    Qué hace:      Suma variantes bajo umbral y pedidos con demora usando selectores de tablero.
    Va hacia:      Muestra insignia de atención en el acceso directo al Tablero dentro del sidebar.
    Depende de:    apps.tablero.selectores.listar_alertas_stock_bajo y listar_pedidos_pendientes_antiguos.
    Cuándo usarla: Al renderizar la navegación lateral de Unfold en cada vista de /gestion/.
    Si no opera:   Retorna None ante errores tempranos antes de migrar tablas.
    """
    try:
        from apps.tablero.selectores import (
            listar_alertas_stock_bajo,
            listar_pedidos_pendientes_antiguos,
        )

        total_alertas = len(listar_alertas_stock_bajo()) + len(
            listar_pedidos_pendientes_antiguos()
        )
        return str(total_alertas) if total_alertas > 0 else None
    except Exception:
        return None


def preparar_contexto_dashboard(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    """Enriquece la pantalla principal /gestion/ con indicadores Flat en vivo de la jornada.

    Qué hace:      Consulta resumen de hoy y totales operativos para tarjetas KPI de /gestion/.
    Va hacia:      Agrega clave 'emuna_resumen_inicio' en el contexto de admin/index.html.
    Depende de:    apps.tablero.selectores.obtener_resumen_tablero.
    Cuándo usarla: Configurado como UNFOLD['DASHBOARD_CALLBACK'] al cargar /gestion/.
    Si no opera:   Devuelve indicadores neutros en S/ 0.00 sin bloquear la carga del panel.
    """
    try:
        from apps.tablero.selectores import obtener_resumen_tablero

        resumen = obtener_resumen_tablero(periodo="hoy")
        context["emuna_resumen_inicio"] = {
            "ventas_hoy": resumen["kpis"]["total_ventas"],
            "pedidos_hoy": resumen["kpis"]["cantidad_pedidos"],
            "unidades_hoy": resumen["kpis"]["unidades_vendidas"],
            "alertas_stock": len(resumen["alertas_stock"]),
            "pendientes_antiguos": len(resumen["pedidos_pendientes_antiguos"]),
            "cola_nuevo": resumen["cola_operativa"]["nuevo"],
            "cola_cotizado": resumen["cola_operativa"]["cotizado"],
            "cola_pagado": resumen["cola_operativa"]["pagado"],
        }
    except Exception:
        context["emuna_resumen_inicio"] = {
            "ventas_hoy": Decimal("0.00"),
            "pedidos_hoy": 0,
            "unidades_hoy": 0,
            "alertas_stock": 0,
            "pendientes_antiguos": 0,
            "cola_nuevo": 0,
            "cola_cotizado": 0,
            "cola_pagado": 0,
        }
    return context


UNFOLD_CONFIG_EMUNA: dict[str, Any] = {
    "SITE_TITLE": "Emuná Sport – Panel de Gestión",
    "SITE_HEADER": "Emuná Sport",
    "SITE_SUBHEADER": "Panel Flat · Estilo deportivo",
    "SITE_SYMBOL": "sports_soccer",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": obtener_url_logo_panel,
        "dark": obtener_url_logo_panel,
    },
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/png",
            "href": obtener_url_logo_panel,
        }
    ],
    "THEME": "light",
    "BORDER_RADIUS": "4px",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "COLORS": {
        "base": {
            "50": "#F8FAFC",
            "100": "#F1F5F9",
            "200": "#E2E8F0",
            "300": "#CBD5E1",
            "400": "#94A3B8",
            "500": "#64748B",
            "600": "#475569",
            "700": "#334155",
            "800": "#1E293B",
            "900": "#0F172A",
            "950": "#020617",
        },
        "primary": {
            "50": "#F0FDF4",
            "100": "#DCFCE7",
            "200": "#BBF7D0",
            "300": "#86EFAC",
            "400": "#4ADE80",
            "500": "#22C55E",
            "600": "#15803D",
            "700": "#166534",
            "800": "#14532D",
            "900": "#052E16",
            "950": "#022C22",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-700)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "STYLES": [obtener_url_estilo_flat_unfold],
    "DASHBOARD_CALLBACK": "apps.nucleo.unfold_config.preparar_contexto_dashboard",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Operación diaria",
                "separator": False,
                "collapsible": False,
                "items": [
                    {
                        "title": "Inicio del panel",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": "Tablero y alertas",
                        "icon": "analytics",
                        "link": reverse_lazy("tablero:resumen"),
                        "badge": contar_alertas_tablero,
                        "badge_variant": "warning",
                    },
                    {
                        "title": "Venta presencial (POS)",
                        "icon": "point_of_sale",
                        "link": reverse_lazy("admin:pedidos_pedido_venta_presencial"),
                    },
                    {
                        "title": "Pedidos web y tienda",
                        "icon": "shopping_bag",
                        "link": reverse_lazy("admin:pedidos_pedido_changelist"),
                        "badge": contar_pedidos_por_atender,
                        "badge_variant": "info",
                    },
                    {
                        "title": "Envíos por agencia",
                        "icon": "local_shipping",
                        "link": reverse_lazy("admin:pedidos_envio_changelist"),
                    },
                ],
            },
            {
                "title": "Catálogo e inventario",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Camisetas / Productos",
                        "icon": "checkroom",
                        "link": reverse_lazy("admin:catalogo_producto_changelist"),
                    },
                    {
                        "title": "Variantes de talla",
                        "icon": "straighten",
                        "link": reverse_lazy("admin:catalogo_variante_changelist"),
                    },
                    {
                        "title": "Kárdex de stock",
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:catalogo_movimientostock_changelist"),
                    },
                    {
                        "title": "Categorías",
                        "icon": "category",
                        "link": reverse_lazy("admin:catalogo_categoria_changelist"),
                    },
                ],
            },
            {
                "title": "Configuración y equipo",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Configuración tienda",
                        "icon": "tune",
                        "link": reverse_lazy("admin:nucleo_configuraciontienda_changelist"),
                        "permission": lambda r: bool(r.user.has_perm("nucleo.view_configuraciontienda")),
                    },
                    {
                        "title": "Métodos de pago",
                        "icon": "payments",
                        "link": reverse_lazy("admin:nucleo_metodopago_changelist"),
                        "permission": lambda r: bool(r.user.has_perm("nucleo.view_metodopago")),
                    },
                    {
                        "title": "Usuarios",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                        "permission": lambda r: bool(r.user.has_perm("auth.view_user")),
                    },
                    {
                        "title": "Grupos y permisos",
                        "icon": "admin_panel_settings",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda r: bool(r.user.has_perm("auth.view_group")),
                    },
                ],
            },
        ],
    },
}
