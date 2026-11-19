"""Rutas principales de Emuná Sport (Catálogo público, Carrito, Pedidos, SEO, Admin y Salud)."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import include, path, resolve

from apps.catalogo.sitemaps import PaginasEstaticasSitemap, ProductoSitemap
from apps.catalogo.views import vista_robots_txt

admin.site.site_header = "Emuná Sport – Panel de Gestión"
admin.site.site_title = "Emuná Sport Admin"
admin.site.index_title = "Administración de Tienda, Pedidos y Stock"

sitemaps_emuna = {
    "productos": ProductoSitemap,
    "paginas": PaginasEstaticasSitemap,
}


def vista_estado_salud(request: HttpRequest) -> JsonResponse:
    """Devuelve el estado de salud del servidor para verificaciones de despliegue.

    Qué hace:      Responde con un JSON {'estado': 'ok', 'tienda': 'Emuná Sport'}.
    Va hacia:      Retorna un JsonResponse con código HTTP 200.
    Depende de:    django.http.JsonResponse.
    Cuándo usarla: En sondas de salud (healthcheck) de Render, Cloudflare o pruebas k6.
    Si no opera:   No aplica (no requiere base de datos para responder).
    """
    return JsonResponse({"estado": "ok", "tienda": "Emuná Sport"})


def vista_alias_panel_perfil(request: HttpRequest, subruta: str = "") -> HttpResponse:
    """Resuelve dinámicamente las rutas amigables /PanelDueño/ y /PanelAdministrativo/ hacia el panel.

    Qué hace:      Mapea cualquier acceso bajo /PanelDueño/, /PanelDueno/ o /PanelAdministrativo/ a la vista real.
    Va hacia:      Ejecuta la vista correspondiente del panel sin perder parámetros GET ni formularios POST.
    Depende de:    django.urls.resolve y settings.ADMIN_URL.
    Cuándo usarla: Cuando el dueño o el superadministrador navegan con su URL personalizada por perfil.
    Si no opera:   Propaga Resolver404 si la subruta interna no existe en el panel.
    """
    prefijo_admin = settings.ADMIN_URL.strip("/")
    ruta_limpia = subruta.lstrip("/")
    ruta_destino = f"/{prefijo_admin}/{ruta_limpia}" if ruta_limpia else f"/{prefijo_admin}/"
    coincidencia = resolve(ruta_destino)
    request.resolver_match = coincidencia
    request.path = ruta_destino
    request.path_info = ruta_destino
    return coincidencia.func(request, *coincidencia.args, **coincidencia.kwargs)


urlpatterns = [
    path(f"{settings.ADMIN_URL}tablero/", include("apps.tablero.urls", namespace="tablero")),
    path(settings.ADMIN_URL, admin.site.urls),
    path("PanelAdministrativo/", vista_alias_panel_perfil, name="panel_administrativo_raiz"),
    path("PanelAdministrativo/<path:subruta>", vista_alias_panel_perfil, name="panel_administrativo_ruta"),
    path("PanelDueño/", vista_alias_panel_perfil, name="panel_dueno_tilde_raiz"),
    path("PanelDueño/<path:subruta>", vista_alias_panel_perfil, name="panel_dueno_tilde_ruta"),
    path("PanelDueno/", vista_alias_panel_perfil, name="panel_dueno_raiz"),
    path("PanelDueno/<path:subruta>", vista_alias_panel_perfil, name="panel_dueno_ruta"),
    path("salud/", vista_estado_salud, name="estado_salud"),
    path("robots.txt", vista_robots_txt, name="robots_txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps_emuna},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", include("apps.pedidos.urls", namespace="pedidos")),
    path("", include("apps.catalogo.urls", namespace="catalogo")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
