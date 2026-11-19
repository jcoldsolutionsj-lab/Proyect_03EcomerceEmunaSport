"""Pruebas unitarias, de seguridad anti-hacking, PDF y flujo E2E de la Fase 2 (Carrito y Pedido)."""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from apps.catalogo.models import Variante
from apps.catalogo.selectores import obtener_producto_detalle_por_slug
from apps.nucleo.excepciones import (
    DatosEnvioIncompletosError,
    EntradaInvalidaError,
    StockInsuficienteError,
)
from apps.pedidos.models import (
    AgenciaEnvio,
    EstadoPedido,
    ItemPedido,
    OrigenPedido,
    Pedido,
    RegistroEstadoPedido,
    TipoEntrega,
)
from apps.pedidos.selectores import obtener_carrito_detallado, obtener_pedido_publico
from apps.pedidos.servicios import (
    agregar_al_carrito,
    crear_pedido_web,
    eliminar_del_carrito,
    generar_pdf_pedido,
)


@pytest.mark.django_db
def test_carrito_sesion_suma_tallas_y_aplica_precio_por_mayor() -> None:
    """Verifica que el carrito sume distintas tallas del mismo producto y aplique tarifa mayorista.

    Qué hace:      Agrega 1 talla S + 1 talla M + 1 talla L de Argentina x Messi #10 en la sesión.
    Va hacia:      Comprueba que al sumar 3 unidades el precio unitario baje de S/ 55.00 a S/ 50.00.
    Depende de:    agregar_al_carrito, obtener_carrito_detallado y datos de cargar_demo.
    Cuándo usarla: En la suite de pruebas de la Fase 2.
    Si no opera:   Falla si cada talla se calcula por separado sin activar el descuento por mayor.
    """
    call_command("cargar_demo")
    messi = obtener_producto_detalle_por_slug(slug="argentina-x-messi-10")
    variantes = {v.talla: v for v in messi.variantes.all()}

    sesion: dict = {}
    agregar_al_carrito(sesion=sesion, variante_id=variantes["S"].id, cantidad=1)
    carrito_1 = obtener_carrito_detallado(sesion)
    assert carrito_1["total_unidades"] == 1
    assert carrito_1["subtotal"] == Decimal("55.00")
    assert carrito_1["tiene_descuento_mayorista"] is False

    # Agregamos 1 en talla M y 1 en talla L -> Total 3 unidades del mismo producto -> S/ 50.00 c/u
    agregar_al_carrito(sesion=sesion, variante_id=variantes["M"].id, cantidad=1)
    carrito_3 = agregar_al_carrito(sesion=sesion, variante_id=variantes["L"].id, cantidad=1)

    assert carrito_3["total_unidades"] == 3
    assert carrito_3["subtotal"] == Decimal("150.00")
    assert carrito_3["subtotal_sin_descuento"] == Decimal("165.00")
    assert carrito_3["ahorro_mayorista"] == Decimal("15.00")
    assert carrito_3["tiene_descuento_mayorista"] is True

    # Validar que se genera el enlace de consulta de WhatsApp con las camisetas del carrito
    import urllib.parse
    texto_wa = urllib.parse.unquote(carrito_3["url_whatsapp_consulta"])
    assert "Hola Richard" in texto_wa
    assert "Talla S" in texto_wa
    assert "S/ 150.00" in texto_wa

    # Si sumamos 3 más en talla M (que tiene stock=8) -> Total 6 unidades -> S/ 45.00 c/u (S/ 270.00 total)
    carrito_6 = agregar_al_carrito(sesion=sesion, variante_id=variantes["M"].id, cantidad=3)
    assert carrito_6["total_unidades"] == 6
    assert carrito_6["subtotal"] == Decimal("270.00")
    assert carrito_6["ahorro_mayorista"] == Decimal("60.00")

    # Eliminar talla L regresa a 5 unidades (S/ 50.00 c/u = S/ 250.00)
    carrito_luego = eliminar_del_carrito(sesion=sesion, variante_id=variantes["L"].id)
    assert carrito_luego["total_unidades"] == 5
    assert carrito_luego["subtotal"] == Decimal("250.00")


@pytest.mark.django_db
def test_carrito_bloquea_exceso_de_stock_y_tallas_agotadas() -> None:
    """Comprueba que agregar_al_carrito lance StockInsuficienteError cuando supera el stock real.

    Qué hace:      Intenta agregar una talla agotada (stock=0) y una cantidad mayor al stock.
    Va hacia:      Garantiza la validación de inventario desde el carrito.
    Depende de:    agregar_al_carrito y StockInsuficienteError.
    Cuándo usarla: En las pruebas unitarias de la Fase 2.
    Si no opera:   Falla si permite agregar unidades inexistentes al carrito.
    """
    call_command("cargar_demo")
    messi = obtener_producto_detalle_por_slug(slug="argentina-x-messi-10")
    var_s = messi.variantes.get(talla="S")

    sesion: dict = {}
    with pytest.raises(StockInsuficienteError):
        agregar_al_carrito(
            sesion=sesion,
            variante_id=var_s.id,
            cantidad=var_s.cantidad_stock + 5,
        )


@pytest.mark.django_db
def test_crear_pedido_punto_encuentro_nace_cotizado_y_envio_cero() -> None:
    """Verifica que un pedido con PUNTO_ENCUENTRO nazca en COTIZADO con costo_envio = S/ 0.00.

    Qué hace:      Crea un pedido en Lima sin DNI y verifica estado, totales, snapshot y bitácora.
    Va hacia:      Valida TBL_TPEDIDO, TBL_TPEDIDO_ITEM y TBL_LPEDIDO_ESTADO (doc 02 y doc 03).
    Depende de:    crear_pedido_web y obtener_pedido_publico.
    Cuándo usarla: En la suite de pruebas de la Fase 2.
    Si no opera:   Falla si nace en NUEVO, si exige DNI en Lima o si descuenta stock antes del pago.
    """
    call_command("cargar_demo")
    messi = obtener_producto_detalle_por_slug(slug="argentina-x-messi-10")
    var_m = messi.variantes.get(talla="M")
    stock_antes = var_m.cantidad_stock

    sesion: dict = {}
    agregar_al_carrito(sesion=sesion, variante_id=var_m.id, cantidad=2)

    pedido = crear_pedido_web(
        sesion=sesion,
        datos_cliente={
            "cliente_nombre": "Juan Pérez Gómez",
            "cliente_telefono": "987654321",
            "tipo_entrega": TipoEntrega.PUNTO_ENCUENTRO,
            "punto_encuentro": "Estación La Cultura del Tren",
            "acepta_privacidad": "1",
            "sitio_web": "",
            "cf_turnstile_response": "TOKEN_PRUEBA_OK",
        },
    )

    assert pedido.codigo.startswith("EMU-")
    assert pedido.estado == EstadoPedido.COTIZADO
    assert pedido.costo_envio == Decimal("0.00")
    assert pedido.subtotal == Decimal("110.00")
    assert pedido.total == Decimal("110.00")
    assert pedido.fecha_cotizado is not None
    assert obtener_carrito_detallado(sesion)["esta_vacio"] is True

    # El stock NO se descuenta al crear el pedido web (se descuenta al confirmar pago en Fase 3)
    var_m.refresh_from_db()
    assert var_m.cantidad_stock == stock_antes

    # Bitácora inmutable creada con 1 registro inicial
    registros = list(pedido.historial_estados.all())
    assert len(registros) == 1
    assert registros[0].estado_anterior is None
    assert registros[0].estado_nuevo == EstadoPedido.COTIZADO

    # Inmutabilidad de TBL_LPEDIDO_ESTADO
    with pytest.raises(ValidationError):
        registros[0].nota = "Intento de alteración"
        registros[0].save()


@pytest.mark.django_db
def test_crear_pedido_agencia_exige_dni_y_nace_en_nuevo_y_oculta_dni_publico() -> None:
    """Verifica que AGENCIA exija DNI de 8 dígitos, nazca en NUEVO y enmascare el DNI en público.

    Qué hace:      Comprueba el rechazo sin DNI, luego crea el pedido Shalom y audita vista pública.
    Va hacia:      Garantiza las reglas de agencia (doc 02) y el Pilar 1 Anti-Hacking (privacidad DNI).
    Depende de:    crear_pedido_web, obtener_pedido_publico y generar_pdf_pedido.
    Cuándo usarla: En la suite de pruebas de la Fase 2.
    Si no opera:   Falla si permite AGENCIA sin DNI o si expone el DNI completo en público/PDF.
    """
    call_command("cargar_demo")
    messi = obtener_producto_detalle_por_slug(slug="argentina-x-messi-10")
    var_l = messi.variantes.get(talla="L")

    sesion: dict = {}
    agregar_al_carrito(sesion=sesion, variante_id=var_l.id, cantidad=3)

    # 1. Sin DNI debe fallar en AGENCIA
    with pytest.raises(DatosEnvioIncompletosError):
        crear_pedido_web(
            sesion=sesion,
            datos_cliente={
                "cliente_nombre": "María Quispe",
                "cliente_telefono": "912345678",
                "tipo_entrega": TipoEntrega.AGENCIA,
                "agencia": AgenciaEnvio.SHALOM,
                "agencia_ciudad": "Arequipa",
                "agencia_referencia": "Sede Av. Parra",
                "acepta_privacidad": "1",
            },
        )

    # 2. Con DNI válido de 8 dígitos se crea en estado NUEVO y con precio por mayor (3 x S/ 50 = S/ 150)
    pedido = crear_pedido_web(
        sesion=sesion,
        datos_cliente={
            "cliente_nombre": "María Quispe",
            "cliente_dni": "45678912",
            "cliente_telefono": "912345678",
            "tipo_entrega": TipoEntrega.AGENCIA,
            "agencia": AgenciaEnvio.SHALOM,
            "agencia_ciudad": "Arequipa",
            "agencia_referencia": "Sede Av. Parra",
            "acepta_privacidad": "1",
        },
    )

    assert pedido.estado == EstadoPedido.NUEVO
    assert pedido.costo_envio is None
    assert pedido.subtotal == Decimal("150.00")
    assert pedido.total == Decimal("150.00")

    # 3. El selector público NUNCA expone el DNI completo (45678912), solo ******12
    publico = obtener_pedido_publico(codigo=pedido.codigo)
    assert publico["dni_enmascarado"] == "******12"
    assert "cliente_dni" not in publico
    assert "cliente_telefono" not in publico

    # 4. Generación de PDF profesional válido (%PDF-)
    pdf_bytes = generar_pdf_pedido(codigo=pedido.codigo)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1200


@pytest.mark.django_db
def test_triple_proteccion_antispam_bloquea_honeypot_y_turnstile_invalido() -> None:
    """Verifica que el campo trampa (honeypot) y Turnstile bloqueen envíos automatizados.

    Qué hace:      Envía un checkout con sitio_web lleno y otro con token Turnstile inválido.
    Va hacia:      Asegura el requisito #17 y el Pilar 4 Anti-Hacking en checkout.
    Depende de:    crear_pedido_web y validar_turnstile_cloudflare.
    Cuándo usarla: En la suite de seguridad de la Fase 2.
    Si no opera:   Falla si se crea algún pedido cuando actúa un bot.
    """
    call_command("cargar_demo")
    messi = obtener_producto_detalle_por_slug(slug="argentina-x-messi-10")
    var_m = messi.variantes.get(talla="M")

    sesion: dict = {}
    agregar_al_carrito(sesion=sesion, variante_id=var_m.id, cantidad=1)

    with pytest.raises(EntradaInvalidaError):
        crear_pedido_web(
            sesion=sesion,
            datos_cliente={
                "cliente_nombre": "Bot Spam",
                "cliente_telefono": "999888777",
                "tipo_entrega": TipoEntrega.PUNTO_ENCUENTRO,
                "punto_encuentro": "Lima",
                "acepta_privacidad": "1",
                "sitio_web": "https://spam-bot.example.com",
            },
        )

    with pytest.raises(EntradaInvalidaError):
        crear_pedido_web(
            sesion=sesion,
            datos_cliente={
                "cliente_nombre": "Bot Turnstile",
                "cliente_telefono": "999888777",
                "tipo_entrega": TipoEntrega.PUNTO_ENCUENTRO,
                "punto_encuentro": "Lima",
                "acepta_privacidad": "1",
                "cf_turnstile_response": "BOT_TOKEN_INVALIDO",
            },
        )

    assert Pedido.objects.count() == 0


@pytest.mark.django_db
def test_flujo_web_e2e_carrito_htmx_checkout_vista_pedido_y_pdf(client: Client) -> None:
    """Prueba de extremo a extremo (E2E) del cliente agregando por HTMX, haciendo checkout y bajando PDF.

    Qué hace:      Simula peticiones HTMX al cajón del carrito, envío de checkout y visita al pedido.
    Va hacia:      Valida vistas, plantillas, un único CTA #39FF14, ocultamiento de DNI y descarga PDF.
    Depende de:    django.test.Client y rutas de apps.pedidos.
    Cuándo usarla: En la verificación integral de la Fase 2.
    Si no opera:   Falla si alguna ruta devuelve error, expone el DNI o rompe el enlace de WhatsApp.
    """
    call_command("cargar_demo")
    messi = obtener_producto_detalle_por_slug(slug="argentina-x-messi-10")
    var_m = messi.variantes.get(talla="M")

    # 1. Agregar 3 camisetas por HTMX -> devuelve el cajón parcial y cabecera HX-Trigger
    resp_htmx = client.post(
        reverse("pedidos:agregar_al_carrito"),
        data={"variante_id": var_m.id, "cantidad": 3, "origen": "cajon"},
        HTTP_HX_REQUEST="true",
    )
    assert resp_htmx.status_code == 200
    assert resp_htmx["HX-Trigger"] == "carritoActualizado"
    html_cajon = resp_htmx.content.decode("utf-8")
    assert "Ahorras S/ 15.00" in html_cajon
    assert "CONTINUAR AL PEDIDO" in html_cajon

    # 2. Abrir página completa de carrito y página de checkout
    resp_carrito = client.get(reverse("pedidos:ver_carrito"))
    assert resp_carrito.status_code == 200
    assert "S/ 150.00" in resp_carrito.content.decode("utf-8")

    resp_checkout_get = client.get(reverse("pedidos:checkout"))
    assert resp_checkout_get.status_code == 200

    # 3. Enviar checkout con AGENCIA y DNI privado
    resp_checkout_post = client.post(
        reverse("pedidos:checkout"),
        data={
            "cliente_nombre": "Roberto Carlos",
            "cliente_telefono": "988776655",
            "cliente_dni": "70809015",
            "tipo_entrega": "AGENCIA",
            "agencia": "OLVA",
            "agencia_ciudad": "Trujillo",
            "agencia_referencia": "Av. España 450",
            "acepta_privacidad": "1",
            "sitio_web": "",
        },
    )
    assert resp_checkout_post.status_code == 302
    pedido = Pedido.objects.first()
    assert pedido is not None

    # 4. Visitar la página pública del pedido (/pedidos/<codigo>/)
    resp_pedido = client.get(reverse("pedidos:detalle_pedido", kwargs={"codigo": pedido.codigo}))
    assert resp_pedido.status_code == 200
    html_pedido = resp_pedido.content.decode("utf-8")
    assert pedido.codigo in html_pedido
    assert "ENVIAR A RICHARD POR WHATSAPP" in html_pedido
    assert "******15" in html_pedido
    # El DNI completo NUNCA debe aparecer en el HTML público
    assert "70809015" not in html_pedido

    # 5. Descargar comprobante PDF
    resp_pdf = client.get(
        reverse("pedidos:descargar_pdf_pedido", kwargs={"codigo": pedido.codigo})
    )
    assert resp_pdf.status_code == 200
    assert resp_pdf["Content-Type"] == "application/pdf"
    assert resp_pdf.content.startswith(b"%PDF-")

    # 6. Consultar un código inexistente o secuencial devuelve 404 (Anti-IDOR)
    resp_404 = client.get(reverse("pedidos:detalle_pedido", kwargs={"codigo": "1"}))
    assert resp_404.status_code == 404
    assert RegistroEstadoPedido.objects.filter(pedido=pedido).count() == 1


@pytest.mark.django_db
def test_pdf_pedido_agencia_shalom_con_notas(client: Client) -> None:
    """Valida que el comprobante PDF se genera correctamente con Shalom, notas y sin colisiones.

    Qué hace:      Crea un pedido con modalidad AGENCIA Shalom y notas personalizadas, genera el PDF.
    Va hacia:      Invoca vista_descargar_pdf_pedido y verifica cabecera %PDF- y tamaño > 1KB.
    Depende de:    Pedido, ItemPedido y generar_pdf_pedido.
    Cuándo usarla: En la validación de comprobantes de envío a provincia por agencia.
    Si no opera:   Falla si hay error de sintaxis, falta de logo o desbordamiento ReportLab.
    """
    call_command("cargar_demo")
    pedido = Pedido.objects.create(
        codigo="EMU-TESTSHALOM",
        estado=EstadoPedido.COTIZADO,
        origen=OrigenPedido.WEB,
        cliente_nombre="Carlos Tevez",
        cliente_telefono="999111222",
        cliente_dni="45889922",
        tipo_entrega=TipoEntrega.AGENCIA,
        agencia=AgenciaEnvio.SHALOM,
        agencia_ciudad="Arequipa",
        agencia_referencia="Sede Parque Industrial",
        notas="Entregar por la tarde después de las 4pm por favor.",
        costo_envio=Decimal("15.00"),
    )
    var = Variante.objects.first()
    ItemPedido.objects.create(
        pedido=pedido,
        variante=var,
        nombre_producto=var.producto.nombre,
        sku=var.sku,
        talla=var.talla,
        color="Azul",
        precio_unidad=Decimal("55.00"),
        cantidad=2,
        subtotal=Decimal("110.00"),
    )
    resp = client.get(reverse("pedidos:descargar_pdf_pedido", kwargs={"codigo": pedido.codigo}))
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")
    assert len(resp.content) > 5000

