"""Rutas principales de Emuná Sport (Admin en ruta no obvia y endpoints base)."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import path

from apps.nucleo.selectores import listar_metodos_pago_activos, obtener_configuracion_tienda

admin.site.site_header = "Emuná Sport – Panel de Gestión"
admin.site.site_title = "Emuná Sport Admin"
admin.site.index_title = "Administración de Tienda, Pedidos y Stock"


def vista_inicio_base(request: HttpRequest) -> HttpResponse:
    """Muestra el panel de verificación de la Fase 0 con enlaces rápidos al Admin y Salud.

    Qué hace:      Renderiza una página de estado deportiva con los datos de ConfiguracionTienda.
    Va hacia:      Retorna un HttpResponse HTML en la ruta raíz '/' (se reemplaza en Fase 1 por el catálogo).
    Depende de:    obtener_configuracion_tienda() y listar_metodos_pago_activos().
    Cuándo usarla: Cuando Jonathan levanta runserver en la Fase 0 para verificar el avance.
    Si no opera:   Si aún no se corrió migrate, muestra valores por defecto sin caer en error 500.
    """
    config = obtener_configuracion_tienda()
    metodos = list(listar_metodos_pago_activos())
    items_metodos = "".join(
        f"<li style='margin-bottom:6px;'><strong>{m.get_tipo_display()}</strong> "
        f"{'– ' + m.titular if m.titular else ''} "
        f"{'(' + m.numero_cuenta + ')' if m.numero_cuenta else ''}</li>"
        for m in metodos
    ) or "<li>Ejecuta <code>python 04-Desarrollo/manage.py preparar_local</code> para cargar Yape y Efectivo.</li>"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{config.nombre} – Fase 0 Activa</title>
  <style>
    body {{ margin:0; font-family: system-ui, -apple-system, sans-serif; background:#FFFFFF; color:#0A0A0A; }}
    header {{ background:#0A0A0A; color:#FFFFFF; padding:20px 24px; display:flex; align-items:center; justify-content:space-between; border-bottom:3px solid #39FF14; }}
    .marca {{ font-size:22px; font-weight:900; font-style:italic; letter-spacing:1px; }}
    .marca span {{ color:#39FF14; }}
    main {{ max-width:760px; margin:36px auto; padding:0 20px; }}
    .caja {{ border:1px solid #C9CED3; padding:24px; margin-bottom:20px; }}
    .badge {{ display:inline-block; background:#39FF14; color:#0A0A0A; font-weight:800; font-size:12px; padding:4px 10px; text-transform:uppercase; margin-bottom:12px; }}
    .cta {{ display:inline-block; background:#39FF14; color:#0A0A0A; font-weight:800; text-decoration:none; padding:14px 24px; margin-right:12px; margin-top:10px; border:2px solid #0A0A0A; }}
    .sec {{ display:inline-block; background:#FFFFFF; color:#0A0A0A; font-weight:700; text-decoration:none; padding:14px 20px; margin-top:10px; border:1px solid #C9CED3; }}
    code {{ background:#F4F5F7; padding:2px 6px; font-size:13px; }}
  </style>
</head>
<body>
  <header>
    <div class="marca"><span>⚡ E</span>MUNÁ SPORT</div>
    <div style="font-size:13px; color:#C9CED3;">Estilo deportivo · Fase 0</div>
  </header>
  <main>
    <div class="caja">
      <div class="badge">Fase 0 – Base del Proyecto Operativa</div>
      <h1 style="margin:0 0 8px 0; font-size:26px;">{config.nombre}</h1>
      <p style="color:#6B727A; margin-top:0;">{config.texto_pie or ''}</p>
      <p><strong>WhatsApp configurado:</strong> +51 {config.numero_whatsapp} &nbsp;|&nbsp;
         <strong>Umbral stock bajo:</strong> {config.umbral_stock_bajo} u. &nbsp;|&nbsp;
         <strong>Mostrar marcas:</strong> {'Sí' if config.mostrar_marcas else 'No (apagado por defecto)'}</p>
      <h3 style="margin-bottom:8px;">Métodos de pago activos (<code>TBL_RMETODO_PAGO</code>):</h3>
      <ul>{items_metodos}</ul>
      <a class="cta" href="/{settings.ADMIN_URL}">ABRIR PANEL DE GESTIÓN (/gestion/) →</a>
      <a class="sec" href="/salud/">Ver JSON de Salud (/salud/)</a>
    </div>
  </main>
</body>
</html>"""
    return HttpResponse(html)


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
    path("", vista_inicio_base, name="inicio_base"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("salud/", vista_estado_salud, name="estado_salud"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
