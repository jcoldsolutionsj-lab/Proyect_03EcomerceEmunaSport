"""Vistas protegidas del Tablero Operativo y exportación CSV para Richard y Jonathan."""
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .selectores import obtener_resumen_tablero
from .servicios import generar_csv_alertas_stock, generar_csv_ventas


def _usuario_es_personal_emuna(usuario: Any) -> bool:
    """Verifica si el usuario autenticado pertenece al equipo autorizado del panel.

    Qué hace:      Comprueba que el usuario esté activo y sea staff, superusuario o Dueño.
    Va hacia:      Retorna True si puede ver métricas y reportes internos, False en caso contrario.
    Depende de:    django.contrib.auth.models.AbstractUser y grupo 'Dueño'.
    Cuándo usarla: En el decorador _solo_personal_autorizado de las vistas del tablero.
    Si no opera:   Retorna False ante usuarios anónimos, inactivos o clientes sin permisos.
    """
    return bool(
        usuario
        and usuario.is_authenticated
        and usuario.is_active
        and (
            usuario.is_staff
            or usuario.is_superuser
            or usuario.groups.filter(name="Dueño").exists()
        )
    )


def _solo_personal_autorizado(
    vista_fn: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """Restringe las vistas del tablero exclusivamente al personal autorizado de la tienda.

    Qué hace:      Redirige a /gestion/login/ si es anónimo o devuelve 403 si no tiene permisos.
    Va hacia:      Envuelve vista_resumen_tablero y descargas CSV administrativas.
    Depende de:    _usuario_es_personal_emuna y reverse('admin:login').
    Cuándo usarla: Como decorador en todas las vistas definidas dentro de apps/tablero/views.py.
    Si no opera:   Bloquea el acceso no autorizado sin filtrar datos comerciales ni de clientes.
    """

    @wraps(vista_fn)
    def _envoltura(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            login_url = reverse("admin:login")
            return redirect(f"{login_url}?next={request.get_full_path()}")
        if not _usuario_es_personal_emuna(request.user):
            return HttpResponseForbidden(
                "Acceso denegado: el tablero operativo es exclusivo para el personal autorizado de Emuná Sport."
            )
        return vista_fn(request, *args, **kwargs)

    return _envoltura


@require_GET
@_solo_personal_autorizado
def vista_resumen_tablero(request: HttpRequest) -> HttpResponse:
    """Renderiza el tablero operativo con métricas de ventas por período y alertas de gestión.

    Qué hace:      Lee periodo/desde/hasta de GET, consulta obtener_resumen_tablero() y renderiza.
    Va hacia:      Renderiza templates/tablero/resumen_tablero.html integrado con base_site Admin.
    Depende de:    obtener_resumen_tablero y admin.site.each_context.
    Cuándo usarla: Cuando Richard accede a /gestion/tablero/ desde celular o computadora.
    Si no opera:   Si el rango es vacío retorna métricas en cero manteniendo la pantalla operativa.
    """
    periodo = request.GET.get("periodo")
    desde = request.GET.get("desde")
    hasta = request.GET.get("hasta")

    resumen = obtener_resumen_tablero(desde=desde, hasta=hasta, periodo=periodo)

    contexto = {
        **admin.site.each_context(request),
        "has_permission": _usuario_es_personal_emuna(request.user),
        "is_popup": False,
        "title": "Tablero Operativo y Alertas",
        "resumen": resumen,
        "desde_iso": resumen["fecha_desde"].isoformat(),
        "hasta_iso": resumen["fecha_hasta"].isoformat(),
    }
    return render(request, "tablero/resumen_tablero.html", contexto)


@require_GET
@_solo_personal_autorizado
def vista_exportar_ventas_csv(request: HttpRequest) -> HttpResponse:
    """Descarga en formato CSV (UTF-8 con BOM) las ventas confirmadas del rango seleccionado.

    Qué hace:      Invoca generar_csv_ventas() respetando periodo/desde/hasta y fuerza descarga.
    Va hacia:      Retorna HttpResponse text/csv con encabezados Content-Disposition y Cache-Control.
    Depende de:    generar_csv_ventas y _solo_personal_autorizado.
    Cuándo usarla: Al pulsar 'Exportar Ventas (.csv)' en la cabecera del tablero.
    Si no opera:   Si el rango no tiene ventas, entrega el archivo CSV válido solo con cabeceras.
    """
    nombre_archivo, contenido = generar_csv_ventas(
        desde=request.GET.get("desde"),
        hasta=request.GET.get("hasta"),
        periodo=request.GET.get("periodo"),
    )
    respuesta = HttpResponse(contenido, content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    respuesta["Cache-Control"] = "no-store"
    return respuesta


@require_GET
@_solo_personal_autorizado
def vista_exportar_alertas_stock_csv(request: HttpRequest) -> HttpResponse:
    """Descarga en formato CSV (UTF-8 con BOM) las variantes agotadas o con stock bajo mínimo.

    Qué hace:      Invoca generar_csv_alertas_stock() para entregar la lista de reposición de taller.
    Va hacia:      Retorna HttpResponse text/csv descargable sin caché.
    Depende de:    generar_csv_alertas_stock y _solo_personal_autorizado.
    Cuándo usarla: Al pulsar 'Exportar Alertas de Stock (.csv)' en el tablero operativo.
    Si no opera:   Entrega CSV solo con cabeceras cuando no hay tallas críticas.
    """
    nombre_archivo, contenido = generar_csv_alertas_stock()
    respuesta = HttpResponse(contenido, content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    respuesta["Cache-Control"] = "no-store"
    return respuesta
