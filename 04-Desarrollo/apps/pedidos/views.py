"""Vistas delgadas de la app pedidos: Carrito HTMX, Checkout, Detalle del Pedido y PDF."""
import mimetypes

from django.http import (
    FileResponse,
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django_ratelimit.decorators import ratelimit

from apps.nucleo.excepciones import ErrorDominioEmuna

from .models import AgenciaEnvio, Envio, TipoEntrega
from .selectores import (
    construir_enlace_whatsapp_pedido,
    obtener_carrito_detallado,
    obtener_pedido_publico,
)
from .servicios import (
    agregar_al_carrito,
    crear_pedido_web,
    eliminar_del_carrito,
    generar_pdf_pedido,
)


def _es_peticion_htmx(request: HttpRequest) -> bool:
    """Detecta si la solicitud proviene de un componente HTMX.

    Qué hace:      Verifica el atributo request.htmx o la cabecera HTTP HX-Request.
    Va hacia:      Retorna True si es HTMX para devolver el fragmento parcial del cajón.
    Depende de:    django-htmx y HttpRequest.headers.
    Cuándo usarla: En las vistas de carrito para decidir entre fragmento HTML o redirección.
    Si no opera:   Retorna False.
    """
    return bool(getattr(request, "htmx", False) or request.headers.get("HX-Request") == "true")


@require_GET
def vista_carrito(request: HttpRequest) -> HttpResponse:
    """Muestra la página completa del carrito de compras (/carrito/).

    Qué hace:      Consulta el carrito en sesión con precios por mayor recalculados.
    Va hacia:      Renderiza templates/pedidos/carrito.html (o parcial si se pide por HTMX).
    Depende de:    obtener_carrito_detallado.
    Cuándo usarla: Cuando el cliente visita /carrito/ para revisar sus tallas y ahorro.
    Si no opera:   Muestra el estado vacío con enlace directo al catálogo.
    """
    carrito = obtener_carrito_detallado(request.session)
    if _es_peticion_htmx(request) and request.GET.get("parcial") == "1":
        return render(
            request,
            "pedidos/parcial_cajon_carrito.html",
            {"carrito": carrito, "incluir_oob_contador": True},
        )
    return render(request, "pedidos/carrito.html", {"carrito": carrito})


@require_POST
def vista_agregar_item_carrito(request: HttpRequest) -> HttpResponse:
    """Agrega o actualiza una talla en el carrito y devuelve el cajón lateral actualizado.

    Qué hace:      Invoca agregar_al_carrito() y prepara el fragmento HTMX con contador OOB.
    Va hacia:      Renderiza pedidos/parcial_cajon_carrito.html o redirige a /carrito/.
    Depende de:    agregar_al_carrito y obtener_carrito_detallado.
    Cuándo usarla: Desde el botón 'Agregar al Carrito' de la ficha o los botones +/- del cajón.
    Si no opera:   Si falta stock, muestra el mensaje de aviso dentro del mismo cajón sin error 500.
    """
    variante_id = request.POST.get("variante_id", 0)
    cantidad = request.POST.get("cantidad", 1)
    reemplazar = request.POST.get("reemplazar", "0") == "1"
    origen_pagina = request.POST.get("origen", "cajon")
    mensaje_error = ""
    mensaje_exito = ""

    try:
        carrito = agregar_al_carrito(
            sesion=request.session,
            variante_id=int(variante_id),
            cantidad=int(cantidad),
            reemplazar=reemplazar,
        )
        mensaje_exito = "Prenda actualizada en tu carrito."
    except (ErrorDominioEmuna, ValueError, TypeError) as exc:
        mensaje_error = str(exc)
        carrito = obtener_carrito_detallado(request.session)

    if _es_peticion_htmx(request) and origen_pagina != "pagina_carrito":
        respuesta = render(
            request,
            "pedidos/parcial_cajon_carrito.html",
            {
                "carrito": carrito,
                "mensaje_error_carrito": mensaje_error,
                "mensaje_exito_carrito": mensaje_exito,
                "incluir_oob_contador": True,
            },
        )
        respuesta["HX-Trigger"] = "carritoActualizado"
        return respuesta

    return redirect("pedidos:ver_carrito")


@require_POST
def vista_eliminar_item_carrito(request: HttpRequest, variante_id: int) -> HttpResponse:
    """Elimina una variante del carrito en sesión y actualiza la vista o el cajón HTMX.

    Qué hace:      Llama a eliminar_del_carrito() para quitar la talla seleccionada.
    Va hacia:      Retorna el fragmento HTMX actualizado o redirige a /carrito/.
    Depende de:    eliminar_del_carrito.
    Cuándo usarla: Cuando el cliente pulsa 'Quitar' en el cajón lateral o en /carrito/.
    Si no opera:   Retorna el estado actual del carrito sin fallar.
    """
    carrito = eliminar_del_carrito(sesion=request.session, variante_id=variante_id)
    origen_pagina = request.POST.get("origen", "cajon")

    if _es_peticion_htmx(request) and origen_pagina != "pagina_carrito":
        respuesta = render(
            request,
            "pedidos/parcial_cajon_carrito.html",
            {
                "carrito": carrito,
                "incluir_oob_contador": True,
            },
        )
        respuesta["HX-Trigger"] = "carritoActualizado"
        return respuesta

    return redirect("pedidos:ver_carrito")


@ratelimit(key="ip", rate="12/m", method="POST", block=False)
@require_http_methods(["GET", "POST"])
def vista_checkout(request: HttpRequest) -> HttpResponse:
    """Muestra y procesa el formulario de checkout con las 4 modalidades de Richard.

    Qué hace:      En GET muestra el resumen y formulario; en POST valida y ejecuta crear_pedido_web.
    Va hacia:      Redirige a /pedidos/<codigo>/ al crear el pedido o muestra errores en el formulario.
    Depende de:    obtener_carrito_detallado, crear_pedido_web y django-ratelimit.
    Cuándo usarla: En la ruta /pedidos/checkout/.
    Si no opera:   Si supera el límite de intentos devuelve 429; si hay error de datos lo muestra en pantalla.
    """
    carrito = obtener_carrito_detallado(request.session)
    if carrito["esta_vacio"] and request.method == "GET":
        return redirect("pedidos:ver_carrito")

    valores_previos = {
        "cliente_nombre": "",
        "cliente_telefono": "",
        "cliente_dni": "",
        "tipo_entrega": TipoEntrega.PUNTO_ENCUENTRO,
        "agencia": AgenciaEnvio.SHALOM,
        "agencia_ciudad": "",
        "agencia_referencia": "",
        "punto_encuentro": "",
        "entrega_programada": "",
        "notas": "",
    }
    mensaje_error = ""

    if request.method == "POST":
        if getattr(request, "limited", False):
            return HttpResponse(
                "Has realizado demasiados intentos seguidos. Por favor espera un minuto.",
                status=429,
            )

        valores_previos = {
            "cliente_nombre": request.POST.get("cliente_nombre", "").strip(),
            "cliente_telefono": request.POST.get("cliente_telefono", "").strip(),
            "cliente_dni": request.POST.get("cliente_dni", "").strip(),
            "tipo_entrega": request.POST.get("tipo_entrega", TipoEntrega.PUNTO_ENCUENTRO).strip(),
            "agencia": request.POST.get("agencia", AgenciaEnvio.SHALOM).strip(),
            "agencia_ciudad": request.POST.get("agencia_ciudad", "").strip(),
            "agencia_referencia": request.POST.get("agencia_referencia", "").strip(),
            "punto_encuentro": request.POST.get("punto_encuentro", "").strip(),
            "entrega_programada": request.POST.get("entrega_programada", "").strip(),
            "notas": request.POST.get("notas", "").strip(),
        }

        datos_entrada = {
            **valores_previos,
            "sitio_web": request.POST.get("sitio_web", ""),
            "acepta_privacidad": request.POST.get("acepta_privacidad", ""),
            "cf_turnstile_response": (
                request.POST.get("cf-turnstile-response")
                or request.POST.get("cf_turnstile_response")
                or ""
            ),
        }

        try:
            pedido = crear_pedido_web(
                sesion=request.session,
                datos_cliente=datos_entrada,
                ip_cliente=request.META.get("REMOTE_ADDR"),
            )
            return redirect("pedidos:detalle_pedido", codigo=pedido.codigo)
        except ErrorDominioEmuna as exc:
            mensaje_error = str(exc)

    contexto = {
        "carrito": carrito,
        "valores": valores_previos,
        "mensaje_error": mensaje_error,
        "modalidades": TipoEntrega.choices,
        "agencias": AgenciaEnvio.choices,
    }
    return render(request, "pedidos/checkout.html", contexto)


@ratelimit(key="ip", rate="30/m", method="GET", block=True)
@require_GET
def vista_detalle_pedido_publico(request: HttpRequest, codigo: str) -> HttpResponse:
    """Muestra la página pública del pedido con un único CTA hacia WhatsApp y descarga de PDF.

    Qué hace:      Obtiene el resumen público seguro (sin DNI completo) y construye el link a WhatsApp.
    Va hacia:      Renderiza templates/pedidos/detalle_pedido.html.
    Depende de:    obtener_pedido_publico y construir_enlace_whatsapp_pedido.
    Cuándo usarla: En la ruta /pedidos/<codigo>/ tras completar el checkout o desde el link de WhatsApp.
    Si no opera:   Devuelve 404 si el código no existe.
    """
    datos_publicos = obtener_pedido_publico(codigo=codigo)
    pedido = datos_publicos["pedido"]
    url_absoluta = request.build_absolute_uri(
        reverse("pedidos:detalle_pedido", kwargs={"codigo": pedido.codigo})
    )
    url_whatsapp_pedido = construir_enlace_whatsapp_pedido(
        pedido=pedido,
        url_publica_pedido=url_absoluta,
    )

    contexto = {
        **datos_publicos,
        "url_publica_pedido": url_absoluta,
        "url_whatsapp_pedido": url_whatsapp_pedido,
    }
    return render(request, "pedidos/detalle_pedido.html", contexto)


@ratelimit(key="ip", rate="20/m", method="GET", block=True)
@require_GET
def vista_descargar_pdf_pedido(request: HttpRequest, codigo: str) -> HttpResponse:
    """Genera y entrega el archivo PDF descargable del pedido (/pedidos/<codigo>/pdf/).

    Qué hace:      Invoca generar_pdf_pedido(codigo) y configura Content-Disposition attachment.
    Va hacia:      Retorna un HttpResponse con content_type='application/pdf'.
    Depende de:    generar_pdf_pedido.
    Cuándo usarla: Cuando el cliente o Richard pulsa 'Descargar Comprobante en PDF'.
    Si no opera:   Devuelve 404 si el código no existe.
    """
    pdf_bytes = generar_pdf_pedido(codigo=codigo)
    codigo_seguro = codigo.upper()
    respuesta = HttpResponse(pdf_bytes, content_type="application/pdf")
    respuesta["Content-Disposition"] = f'inline; filename="Pedido-{codigo_seguro}-EmunaSport.pdf"'
    return respuesta


@require_GET
def vista_api_carrito_resumen(request: HttpRequest) -> JsonResponse:
    """Devuelve el estado del carrito en formato JSON para clientes ligeros o pruebas de carga k6.

    Qué hace:      Serializa el resumen de obtener_carrito_detallado en JSON.
    Va hacia:      Retorna JsonResponse con total_unidades, subtotal y ahorro_mayorista.
    Depende de:    obtener_carrito_detallado.
    Cuándo usarla: En llamadas de verificación rápida y pruebas de humo en Grafana k6.
    Si no opera:   Retorna carrito vacío con código 200.
    """
    carrito = obtener_carrito_detallado(request.session)
    return JsonResponse(
        {
            "total_unidades": carrito["total_unidades"],
            "subtotal": str(carrito["subtotal"]),
            "ahorro_mayorista": str(carrito["ahorro_mayorista"]),
            "tiene_descuento_mayorista": carrito["tiene_descuento_mayorista"],
            "esta_vacio": carrito["esta_vacio"],
            "items": [
                {
                    "variante_id": item["variante_id"],
                    "nombre_producto": item["nombre_producto"],
                    "sku": item["sku"],
                    "talla": item["talla"],
                    "cantidad": item["cantidad"],
                    "precio_unidad": str(item["precio_unidad"]),
                    "subtotal": str(item["subtotal"]),
                }
                for item in carrito["items"]
            ],
        }
    )


@require_GET
def vista_ver_boleta_privada(request: HttpRequest, envio_id: int) -> HttpResponse:
    """Sirve de forma privada y autenticada la foto de la boleta de agencia.

    Qué hace:      Verifica permisos de staff o grupo Dueño y transmite el archivo binario.
    Va hacia:      FileResponse con MIME type seguro para visualización en navegador.
    Depende de:    Envio y permisos de sesión del usuario autenticado.
    Cuándo usarla: Al pulsar 'Ver boleta privada' desde el panel de administración de Richard.
    Si no opera:   Retorna HTTP 403 Forbidden para usuarios anónimos o clientes sin privilegios.
    """
    if not request.user.is_authenticated or not (
        request.user.is_staff or request.user.groups.filter(name="Dueño").exists()
    ):
        return HttpResponseForbidden("Acceso denegado a comprobantes privados de despacho.")

    envio = get_object_or_404(Envio.objects.select_related("pedido"), id=envio_id)
    if not envio.imagen_boleta:
        raise Http404("El envío no cuenta con imagen de boleta registrada.")

    try:
        archivo = envio.imagen_boleta.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("El archivo de la boleta no se encuentra en el almacenamiento.") from None

    nombre_archivo = envio.imagen_boleta.name.lower()
    tipo_mime, _ = mimetypes.guess_type(nombre_archivo)
    if not tipo_mime:
        tipo_mime = "application/octet-stream"

    return FileResponse(archivo, content_type=tipo_mime)
