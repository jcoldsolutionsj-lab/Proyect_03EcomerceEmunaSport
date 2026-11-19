"""Configuración de navegación, insignia en tiempo real y tablero Flat Design para django-unfold."""
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
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

    Qué hace:      Resuelve static('css/emuna_flat_unfold.css') con control de caché en desarrollo.
    Va hacia:      Inyecta los colores de Emuná Sport (#0A0A0A / #39FF14), zoom 0.85 y reglas móvil.
    Depende de:    django.templatetags.static.static y static/css/emuna_flat_unfold.css.
    Cuándo usarla: En UNFOLD['STYLES'] para aplicar diseño Flat consistente en todo el panel.
    Si no opera:   Unfold sigue cargando normalmente con sus estilos base Tailwind.
    """
    url_base = static("css/emuna_flat_unfold.css")
    if getattr(settings, "DEBUG", False):
        ruta_css = Path(settings.BASE_DIR) / "static" / "css" / "emuna_flat_unfold.css"
        if ruta_css.exists():
            return f"{url_base}?v={int(ruta_css.stat().st_mtime)}"
    return url_base


def es_menu_pos_activo(request: HttpRequest) -> bool:
    """Marca activo el ítem 'Venta presencial (POS)' solo dentro de la vista POS.

    Qué hace:      Evalúa si 'venta-presencial' forma parte de request.path.
    Va hacia:      Controla el resaltado del ítem POS en UNFOLD['SIDEBAR']['navigation'].
    Depende de:    request.path normalizado por Django o por vista_alias_panel_perfil.
    Cuándo usarla: Como callback 'active' del ítem POS en el menú lateral.
    Si no opera:   Retorna False evitando resaltados duplicados.
    """
    return "venta-presencial" in getattr(request, "path", "")


def es_menu_pedidos_activo(request: HttpRequest) -> bool:
    """Marca activo 'Pedidos web y tienda' únicamente en listado/ficha de pedidos (excluye POS).

    Qué hace:      Evita que /pedidos/pedido/venta-presencial/ encienda también 'Pedidos web y tienda'.
    Va hacia:      Controla el resaltado exclusivo del ítem de pedidos en el menú lateral.
    Depende de:    request.path.
    Cuándo usarla: Como callback 'active' del ítem 'Pedidos web y tienda' en UNFOLD['SIDEBAR'].
    Si no opera:   Retorna False cuando la ruta activa corresponde al POS presencial.
    """
    ruta = getattr(request, "path", "")
    return "/pedidos/pedido/" in ruta and "venta-presencial" not in ruta


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


def preparar_contexto_global_panel(request: HttpRequest) -> dict[str, Any]:
    """Construye los datos detallados del perfil del usuario autenticado y su ruta dinámica.

    Qué hace:      Extrae nombre, rol (Dueño vs Superadministrador), DNI, teléfono, registro y ruta.
    Va hacia:      Inyecta 'emuna_perfil_usuario' en todas las pantallas del panel vía GLOBAL_CALLBACK.
    Depende de:    request.user, auth.Group y obtener_configuracion_tienda.
    Cuándo usarla: En cada petición de Unfold para el modal de perfil y la URL dinámica por rol.
    Si no opera:   Si el usuario es anónimo (pantalla login), retorna diccionario vacío seguro.
    """
    usuario = getattr(request, "user", None)
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return {}

    try:
        from apps.nucleo.selectores import obtener_configuracion_tienda

        config = obtener_configuracion_tienda()
        whatsapp_tienda = config.numero_whatsapp if config else "932859746"
    except Exception:
        whatsapp_tienda = "932859746"

    try:
        grupos = list(usuario.groups.values_list("name", flat=True))
    except Exception:
        grupos = []

    es_super = bool(getattr(usuario, "is_superuser", False))
    username = usuario.get_username()
    nombre_completo = usuario.get_full_name().strip()
    if not nombre_completo:
        if username.lower() == "richard":
            nombre_completo = "Richard Alexander Ramos Hinostroza"
        elif username.lower() == "jonathan" or es_super:
            nombre_completo = "Jonathan Vera"
        else:
            nombre_completo = username

    if es_super:
        rol_titulo = "Superadministrador Técnico y Operativo"
        nombre_panel = "PanelAdministrativo"
        prefijo_url_panel = "/PanelAdministrativo/"
        dni_perfil = "Administrador Principal (Acceso Total)"
        alcance = "Acceso total a configuración técnica, usuarios, base de datos, catálogo, POS y pedidos."
    else:
        rol_titulo = "Dueño Operativo – Emuná Sport"
        nombre_panel = "PanelDueño"
        prefijo_url_panel = "/PanelDueño/"
        dni_perfil = "48348911" if username.lower() == "richard" else "Registrado en tienda"
        alcance = "Gestión integral de tienda: Tablero VIP, Pedidos, POS Presencial, Productos, Tallas y Kárdex."

    inicial = (nombre_completo or username)[:1].upper()
    grupos_texto = ", ".join(grupos) if grupos else ("Superusuario" if es_super else "Staff Operativo")

    return {
        "emuna_perfil_usuario": {
            "username": username,
            "inicial": inicial,
            "nombre_completo": nombre_completo,
            "email": usuario.email or "Sin correo registrado",
            "es_superusuario": es_super,
            "rol_titulo": rol_titulo,
            "nombre_panel": nombre_panel,
            "prefijo_url_panel": prefijo_url_panel,
            "grupos": grupos_texto,
            "dni": dni_perfil,
            "telefono": f"+51 {whatsapp_tienda}",
            "fecha_registro": getattr(usuario, "date_joined", None),
            "ultimo_acceso": getattr(usuario, "last_login", None),
            "alcance": alcance,
        }
    }


def obtener_subtitulo_panel(request: HttpRequest) -> str:
    """Devuelve el subtítulo dinámico del panel según el perfil del usuario conectado.

    Qué hace:      Muestra 'PanelAdministrativo' para superusuario o 'PanelDueño' para el grupo Dueño.
    Va hacia:      Cabecera lateral de Unfold (SITE_SUBHEADER).
    Depende de:    preparar_contexto_global_panel.
    Cuándo usarla: Al renderizar la marca superior izquierda del panel administrativo.
    Si no opera:   Retorna 'Panel Flat · Estilo deportivo' en la pantalla de login.
    """
    datos = preparar_contexto_global_panel(request).get("emuna_perfil_usuario")
    if not datos:
        return "Panel Flat · Estilo deportivo"
    return f"{datos['nombre_panel']} · {datos['rol_titulo']}"


def obtener_etiqueta_entorno_perfil(request: HttpRequest) -> list[str]:
    """Devuelve la insignia superior derecha con el nombre del panel según el rol activo.

    Qué hace:      Construye la tupla [texto, variante] para UNFOLD['ENVIRONMENT'].
    Va hacia:      Barra superior derecha junto al avatar del usuario.
    Depende de:    preparar_contexto_global_panel.
    Cuándo usarla: En cada vista del panel para identificar si opera en PanelDueño o PanelAdministrativo.
    Si no opera:   Retorna etiqueta general de Emuná Sport.
    """
    datos = preparar_contexto_global_panel(request).get("emuna_perfil_usuario")
    if not datos:
        return ["Emuná Sport · Gestión", "success"]
    if datos["es_superusuario"]:
        return [f"⚡ {datos['nombre_panel']} · Superusuario", "info"]
    return [f"👑 {datos['nombre_panel']} · Dueño", "success"]


UNFOLD_CONFIG_EMUNA: dict[str, Any] = {
    "SITE_TITLE": "Emuná Sport – Panel de Gestión",
    "SITE_HEADER": "Emuná Sport",
    "SITE_SUBHEADER": obtener_subtitulo_panel,
    "ENVIRONMENT": "apps.nucleo.unfold_config.obtener_etiqueta_entorno_perfil",
    "GLOBAL_CALLBACK": "apps.nucleo.unfold_config.preparar_contexto_global_panel",
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
                        "active": "apps.nucleo.unfold_config.es_menu_pos_activo",
                    },
                    {
                        "title": "Pedidos web y tienda",
                        "icon": "shopping_bag",
                        "link": reverse_lazy("admin:pedidos_pedido_changelist"),
                        "badge": contar_pedidos_por_atender,
                        "badge_variant": "info",
                        "active": "apps.nucleo.unfold_config.es_menu_pedidos_activo",
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
                    {
                        "title": "Equipos / Selecciones",
                        "icon": "shield",
                        "link": reverse_lazy("admin:catalogo_equipo_changelist"),
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
