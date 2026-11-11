"""Rutas principales de Emuná Sport (Catálogo público, Carrito, Pedidos, SEO, Admin y Salud)."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpRequest, JsonResponse
from django.urls import include, path

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


urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
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
