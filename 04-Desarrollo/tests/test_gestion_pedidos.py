"""Pruebas integrales de la Fase 3: Gestión del pedido, stock atómico y panel administrativo."""
from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.catalogo.models import MovimientoStock, ReglaPrecio, TipoMovimientoStock
from apps.catalogo.selectores import obtener_producto_detalle_por_slug
from apps.nucleo.excepciones import (
    DatosEnvioIncompletosError,
    StockInsuficienteError,
    TransicionInvalidaError,
)
from apps.pedidos.models import (
    AgenciaEnvio,
    Envio,
    EstadoPedido,
    ItemPedido,
    OrigenPedido,
    Pedido,
    QuienPagaFlete,
    RegistroEstadoPedido,
    TipoEntrega,
)
from apps.pedidos.servicios import (
    agregar_al_carrito,
    cambiar_estado,
    cancelar_o_rechazar,
    confirmar_pago,
    confirmar_pago_y_entregar,
    cotizar_envio,
    crear_pedido_web,
    registrar_envio_agencia,
    registrar_venta_presencial,
)


@pytest.fixture
def datos_base(db) -> dict:
    """Carga datos de demostración y usuarios del sistema para las pruebas de pedidos.

    Qué hace:      Ejecuta preparar_local y cargar_demo obteniendo a Richard y variantes.
    Va hacia:      Entrega diccionario con usuarios, variantes de fútbol y cliente de prueba.
    Depende de:    Comandos de gestión preparar_local y cargar_demo.
    Cuándo usarla: Como fixture en cada test de test_gestion_pedidos.
    Si no opera:   Falla si las migraciones o cargas iniciales no están listas.
    """
    call_command("preparar_local")
    call_command("cargar_demo")
    user_model = get_user_model()
    richard = user_model.objects.get(username="richard")
    messi = obtener_producto_detalle_por_slug(slug="argentina-x-messi-10")
    variantes = {v.talla: v for v in messi.variantes.all()}
    return {
        "richard": richard,
        "messi": messi,
        "variantes": variantes,
        "var_s": variantes["S"],
        "var_m": variantes["M"],
    }


@pytest.mark.django_db
def test_matriz_transiciones_permitidas_e_invalidas(datos_base: dict) -> None:
    """Verifica que la máquina de estados respete estrictamente TRANSICIONES_PERMITIDAS.

    Qué hace:      Prueba pasos válidos e intenta saltos ilegales (ej. NUEVO a ENVIADO o PAGADO).
    Va hacia:      Asegura la coherencia de estados en TBL_TPEDIDO y TBL_LPEDIDO_ESTADO.
    Depende de:    cambiar_estado y TRANSICIONES_PERMITIDAS.
    Cuándo usarla: En la validación del ciclo de vida de pedidos.
    Si no opera:   Falla si se permite un salto no contemplado en la documentación técnica.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]

    # Crear pedido en NUEVO
    pedido = Pedido.objects.create(
        codigo="EMU-TRANS01",
        estado=EstadoPedido.NUEVO,
        tipo_entrega=TipoEntrega.AGENCIA,
        agencia=AgenciaEnvio.SHALOM,
        agencia_ciudad="Trujillo",
        agencia_referencia="Sede Central",
        cliente_nombre="Cliente Prueba Transiciones",
        cliente_telefono="987654321",
        cliente_dni="12345678",
        subtotal=Decimal("55.00"),
        total=Decimal("55.00"),
    )

    # 1. Transición inválida directa: NUEVO -> PAGADO (debe pasar primero por COTIZADO)
    with pytest.raises(TransicionInvalidaError):
        cambiar_estado(pedido=pedido, nuevo_estado=EstadoPedido.PAGADO, usuario=richard)

    # 2. Transición inválida directa: NUEVO -> ENVIADO
    with pytest.raises(TransicionInvalidaError):
        cambiar_estado(pedido=pedido, nuevo_estado=EstadoPedido.ENVIADO, usuario=richard)

    # 3. Transición válida: NUEVO -> COTIZADO
    cambiar_estado(pedido=pedido, nuevo_estado=EstadoPedido.COTIZADO, usuario=richard)
    pedido.refresh_from_db()
    assert pedido.estado == EstadoPedido.COTIZADO
    assert pedido.fecha_cotizado is not None

    # 4. Transición inválida: COTIZADO -> ENTREGADO directamente
    with pytest.raises(TransicionInvalidaError):
        cambiar_estado(pedido=pedido, nuevo_estado=EstadoPedido.ENTREGADO, usuario=richard)

    # 5. Transición válida a PAGADO simulando venta
    ItemPedido.objects.create(
        pedido=pedido,
        variante=var_s,
        nombre_producto=var_s.producto.nombre,
        sku=var_s.sku,
        talla=var_s.talla,
        precio_unidad=Decimal("55.00"),
        cantidad=1,
        subtotal=Decimal("55.00"),
    )
    confirmar_pago(pedido=pedido, metodo_pago="YAPE", usuario=richard)
    pedido.refresh_from_db()
    assert pedido.estado == EstadoPedido.PAGADO
    assert pedido.fecha_pagado is not None

    # 6. Intentar regresar de PAGADO a NUEVO (ilegal)
    with pytest.raises(TransicionInvalidaError):
        cambiar_estado(pedido=pedido, nuevo_estado=EstadoPedido.NUEVO, usuario=richard)


@pytest.mark.django_db
def test_flujo_a_agencia_completo_con_envio_y_privacidad(datos_base: dict) -> None:
    """Valida el Flujo A (Provincia / Agencia): NUEVO -> COTIZADO -> PAGADO -> ENVIADO -> ENTREGADO.

    Qué hace:      Simula el pedido web por Shalom, cotización, pago Yape, despacho y privacidad de datos.
    Va hacia:      Verifica stock atómico, modelo Envio, 4 dígitos de clave y bloqueo en vista pública.
    Depende de:    crear_pedido_web, cotizar_envio, confirmar_pago, registrar_envio_agencia.
    Cuándo usarla: Como prueba end-to-end del flujo principal de provincia de Emuná Sport.
    Si no opera:   Falla si se expone la clave privada de recojo o si falla la deducción de inventario.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]
    stock_inicial = var_s.cantidad_stock

    # 1. Cliente registra pedido web a provincia por Shalom
    sesion: dict = {}
    agregar_al_carrito(sesion=sesion, variante_id=var_s.id, cantidad=2)
    datos_cliente = {
        "cliente_nombre": "Carlos Mendoza",
        "cliente_telefono": "987654321",
        "cliente_dni": "71234567",
        "tipo_entrega": TipoEntrega.AGENCIA,
        "agencia": AgenciaEnvio.SHALOM,
        "agencia_ciudad": "Arequipa",
        "agencia_referencia": "Agencia Av. Parra",
        "cf_turnstile_response": "mock-token-local",
        "acepta_privacidad": True,
    }
    pedido = crear_pedido_web(sesion=sesion, datos_cliente=datos_cliente)
    assert pedido.estado == EstadoPedido.NUEVO
    assert pedido.costo_envio is None
    assert pedido.total == Decimal("110.00")
    # Stock aún intacto
    var_s.refresh_from_db()
    assert var_s.cantidad_stock == stock_inicial

    # 2. Richard cotiza el envío a S/ 15.00
    pedido_cotizado = cotizar_envio(pedido=pedido, costo_envio=Decimal("15.00"), usuario=richard)
    assert pedido_cotizado.estado == EstadoPedido.COTIZADO
    assert pedido_cotizado.costo_envio == Decimal("15.00")
    assert pedido_cotizado.total == Decimal("125.00")

    # 3. Cliente paga con Yape y Richard confirma el pago -> Descuenta stock atómicamente
    confirmar_pago(pedido=pedido_cotizado, metodo_pago="YAPE", usuario=richard)
    pedido_cotizado.refresh_from_db()
    assert pedido_cotizado.estado == EstadoPedido.PAGADO
    var_s.refresh_from_db()
    assert var_s.cantidad_stock == stock_inicial - 2

    # Verificar movimiento de auditoría VENTA
    mov = MovimientoStock.objects.filter(pedido=pedido_cotizado).first()
    assert mov is not None
    assert mov.tipo == TipoMovimientoStock.VENTA
    assert mov.cantidad == -2
    assert mov.creado_por == richard

    # 4. Intentar registrar despacho con clave de recojo inválida (menos de 4 dígitos)
    foto_boleta = SimpleUploadedFile("boleta_shalom.jpg", b"fake-bytes", content_type="image/jpeg")
    with pytest.raises(DatosEnvioIncompletosError):
        registrar_envio_agencia(
            pedido=pedido_cotizado,
            agencia=AgenciaEnvio.SHALOM,
            numero_orden_agencia="SHA-908123",
            clave_recojo="12",  # Inválido: debe tener 4 dígitos
            imagen_boleta=foto_boleta,
            costo_flete=Decimal("15.00"),
            quien_paga=QuienPagaFlete.CLIENTE_ADELANTADO,
            usuario=richard,
        )

    # 5. Registrar despacho con datos completos y clave de 4 dígitos
    foto_valida = SimpleUploadedFile("boleta_shalom.jpg", b"fake-bytes-valido", content_type="image/jpeg")
    envio = registrar_envio_agencia(
        pedido=pedido_cotizado,
        agencia=AgenciaEnvio.SHALOM,
        numero_orden_agencia="SHA-908123",
        clave_recojo="4821",
        imagen_boleta=foto_valida,
        costo_flete=Decimal("15.00"),
        quien_paga=QuienPagaFlete.CLIENTE_ADELANTADO,
        cobrado=True,
        usuario=richard,
        notas="Despachado en sede Lince de Shalom",
    )
    pedido_cotizado.refresh_from_db()
    assert pedido_cotizado.estado == EstadoPedido.ENVIADO
    assert envio.clave_recojo == "4821"
    assert envio.numero_orden_agencia == "SHA-908123"

    # 6. Comprobar que la vista pública web JAMÁS exponga la clave de recojo ni la boleta
    cliente_http = Client()
    url_publica = reverse("pedidos:detalle_pedido", args=[pedido_cotizado.codigo])
    resp = cliente_http.get(url_publica)
    assert resp.status_code == 200
    contenido_html = resp.content.decode("utf-8")
    assert "4821" not in contenido_html, "ALERTA DE SEGURIDAD: La clave privada fue expuesta en web"
    assert "boleta_shalom.jpg" not in contenido_html

    # 7. Cliente recoge en agencia -> Richard marca como ENTREGADO
    cambiar_estado(
        pedido=pedido_cotizado,
        nuevo_estado=EstadoPedido.ENTREGADO,
        usuario=richard,
        nota="Paquete retirado por el cliente en Shalom.",
    )
    pedido_cotizado.refresh_from_db()
    assert pedido_cotizado.estado == EstadoPedido.ENTREGADO
    assert pedido_cotizado.fecha_entregado is not None


@pytest.mark.django_db
def test_flujo_b_lima_confirmar_pago_y_entregar_en_un_paso(datos_base: dict) -> None:
    """Valida el Flujo B de Lima: COTIZADO -> PAGADO -> ENTREGADO en un solo paso atómico.

    Qué hace:      Crea un pedido con punto de encuentro y aplica confirmar_pago_y_entregar().
    Va hacia:      Comprueba que deje el pedido en ENTREGADO y genere ambos registros en bitácora.
    Depende de:    confirmar_pago_y_entregar, select_for_update y RegistroEstadoPedido.
    Cuándo usarla: Para la entrega presencial mano a mano en estaciones de Lima.
    Si no opera:   Falla si descuenta dos veces el stock o si no registra el paso intermedio PAGADO.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]
    stock_inicial = var_s.cantidad_stock

    sesion: dict = {}
    agregar_al_carrito(sesion=sesion, variante_id=var_s.id, cantidad=1)
    datos_cliente = {
        "cliente_nombre": "Jonathan Vera",
        "cliente_telefono": "987654321",
        "tipo_entrega": TipoEntrega.PUNTO_ENCUENTRO,
        "punto_encuentro": "Estación La Cultura",
        "cf_turnstile_response": "mock-token-local",
        "acepta_privacidad": True,
    }
    pedido = crear_pedido_web(sesion=sesion, datos_cliente=datos_cliente)
    assert pedido.estado == EstadoPedido.COTIZADO
    assert pedido.costo_envio == Decimal("0.00")

    # Ejecutar acción de 1 paso en Lima
    pedido_entregado = confirmar_pago_y_entregar(
        pedido=pedido,
        metodo_pago="YAPE",
        usuario=richard,
        nota="Entregado en Estación La Cultura",
    )
    assert pedido_entregado.estado == EstadoPedido.ENTREGADO
    assert pedido_entregado.fecha_pagado is not None
    assert pedido_entregado.fecha_entregado is not None

    # Stock descontado exactamente 1 vez
    var_s.refresh_from_db()
    assert var_s.cantidad_stock == stock_inicial - 1

    # Bitácora registra el salto completo con trazabilidad
    estados_historial = list(
        RegistroEstadoPedido.objects.filter(pedido=pedido_entregado)
        .order_by("fecha_creacion")
        .values_list("estado_nuevo", flat=True)
    )
    assert EstadoPedido.PAGADO in estados_historial
    assert EstadoPedido.ENTREGADO in estados_historial


@pytest.mark.django_db
def test_flujo_c_venta_presencial_pos(datos_base: dict) -> None:
    """Valida el Flujo C: Venta presencial directa en mostrador con descuento mayorista.

    Qué hace:      Ejecuta registrar_venta_presencial con 3 unidades para comprobar tarifa por mayor.
    Va hacia:      Verifica creación de Pedido PRESENCIAL, ítems, stock descontado y estado ENTREGADO.
    Depende de:    registrar_venta_presencial, Variante y MovimientoStock.
    Cuándo usarla: En ventas directas de Richard en taller o ferias.
    Si no opera:   Falla si no aplica el precio por mayor o si no genera el pedido con origen PRESENCIAL.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]
    var_m = datos_base["var_m"]
    stock_s = var_s.cantidad_stock
    stock_m = var_m.cantidad_stock

    # Comprar 2 en talla S y 1 en talla M del mismo producto (total 3 -> activa tarifa mayorista S/ 50.00)
    lineas = [
        {"variante_id": var_s.id, "cantidad": 2},
        {"variante_id": var_m.id, "cantidad": 1},
    ]

    pedido_pos = registrar_venta_presencial(
        lineas=lineas,
        metodo_pago="EFECTIVO",
        usuario=richard,
        cliente_nombre="Cliente Mostrador Taller",
        cliente_telefono="999888777",
        marcar_entregado=True,
        notas="Cobrado monto exacto en efectivo",
    )

    assert pedido_pos.origen == OrigenPedido.PRESENCIAL
    assert pedido_pos.estado == EstadoPedido.ENTREGADO
    # 3 prendas a precio mayorista S/ 50.00 = S/ 150.00
    assert pedido_pos.total == Decimal("150.00")
    assert pedido_pos.subtotal == Decimal("150.00")

    var_s.refresh_from_db()
    var_m.refresh_from_db()
    assert var_s.cantidad_stock == stock_s - 2
    assert var_m.cantidad_stock == stock_m - 1

    movimientos = MovimientoStock.objects.filter(pedido=pedido_pos)
    assert movimientos.count() == 2
    for m in movimientos:
        assert m.tipo == TipoMovimientoStock.VENTA
        assert m.cantidad < 0


@pytest.mark.django_db
def test_atomicidad_stock_insuficiente_revierte_todo(datos_base: dict) -> None:
    """Verifica que si una línea no tiene stock, ninguna se descuente (rollback total).

    Qué hace:      Configura una variante con stock 1 e intenta confirmar el pago de un pedido de 2 unidades.
    Va hacia:      Comprueba que lance StockInsuficienteError y preserve el inventario intacto.
    Depende de:    confirmar_pago, transaction.atomic y select_for_update.
    Cuándo usarla: Para validar la atomicidad transaccional del corazón del negocio.
    Si no opera:   Falla si deja stock en negativo o descuenta unas prendas y otras no.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]
    # Dejamos la variante con solo 1 unidad
    var_s.cantidad_stock = 1
    var_s.save(update_fields=["cantidad_stock"])

    pedido = Pedido.objects.create(
        codigo="EMU-STOCKFAIL",
        estado=EstadoPedido.COTIZADO,
        tipo_entrega=TipoEntrega.PUNTO_ENCUENTRO,
        cliente_nombre="Prueba Falla Stock",
        cliente_telefono="987654321",
        punto_encuentro="Estación Gamarra",
        subtotal=Decimal("110.00"),
        costo_envio=Decimal("0.00"),
        total=Decimal("110.00"),
    )
    ItemPedido.objects.create(
        pedido=pedido,
        variante=var_s,
        nombre_producto=var_s.producto.nombre,
        sku=var_s.sku,
        talla=var_s.talla,
        precio_unidad=Decimal("55.00"),
        cantidad=2,  # Pide 2 pero solo hay 1
        subtotal=Decimal("110.00"),
    )

    with pytest.raises(StockInsuficienteError):
        confirmar_pago(pedido=pedido, metodo_pago="YAPE", usuario=richard)

    # El pedido sigue en COTIZADO y el stock se mantiene en 1 intacto
    pedido.refresh_from_db()
    assert pedido.estado == EstadoPedido.COTIZADO
    var_s.refresh_from_db()
    assert var_s.cantidad_stock == 1
    assert MovimientoStock.objects.filter(pedido=pedido).count() == 0


@pytest.mark.django_db
def test_cancelacion_pedido_pagado_repone_stock_con_devolucion(datos_base: dict) -> None:
    """Verifica que cancelar un pedido PAGADO reponga el inventario con movimientos DEVOLUCION.

    Qué hace:      Pasa pedido a PAGADO descontando stock y luego llama a cancelar_o_rechazar().
    Va hacia:      Comprueba que el stock vuelva a su nivel inicial y se registre DEVOLUCION en TBL_TMOVIMIENTO_STOCK.
    Depende de:    cancelar_o_rechazar, reponer_stock_pedido y MovimientoStock.
    Cuándo usarla: Al anular pedidos por arrepentimiento o cancelación formal del cliente.
    Si no opera:   Falla si se pierde el stock descontado tras cancelar.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]
    stock_inicial = var_s.cantidad_stock

    pedido = Pedido.objects.create(
        codigo="EMU-CANCEL01",
        estado=EstadoPedido.COTIZADO,
        tipo_entrega=TipoEntrega.PUNTO_ENCUENTRO,
        cliente_nombre="Cliente Desiste",
        cliente_telefono="987654321",
        punto_encuentro="Estación Central",
        subtotal=Decimal("110.00"),
        costo_envio=Decimal("0.00"),
        total=Decimal("110.00"),
    )
    ItemPedido.objects.create(
        pedido=pedido,
        variante=var_s,
        nombre_producto=var_s.producto.nombre,
        sku=var_s.sku,
        talla=var_s.talla,
        precio_unidad=Decimal("55.00"),
        cantidad=2,
        subtotal=Decimal("110.00"),
    )

    confirmar_pago(pedido=pedido, metodo_pago="YAPE", usuario=richard)
    var_s.refresh_from_db()
    assert var_s.cantidad_stock == stock_inicial - 2

    # Richard cancela el pedido
    cancelar_o_rechazar(
        pedido=pedido,
        nuevo_estado=EstadoPedido.CANCELADO,
        usuario=richard,
        nota="Cliente solicita cancelación antes de la entrega",
        devolucion_fisica=True,
    )
    pedido.refresh_from_db()
    assert pedido.estado == EstadoPedido.CANCELADO

    # Stock repuesto
    var_s.refresh_from_db()
    assert var_s.cantidad_stock == stock_inicial

    # Movimiento de DEVOLUCION registrado
    mov_dev = MovimientoStock.objects.filter(
        pedido=pedido, tipo=TipoMovimientoStock.DEVOLUCION
    ).first()
    assert mov_dev is not None
    assert mov_dev.cantidad == 2


@pytest.mark.django_db
def test_movimiento_stock_es_estrictamente_inmutable(datos_base: dict) -> None:
    """Garantiza que TBL_TMOVIMIENTO_STOCK sea una bitácora inmutable (bloquea update y delete).

    Qué hace:      Crea un movimiento de inventario e intenta modificarlo y eliminarlo.
    Va hacia:      Comprueba que save() y delete() lancen excepción preservando la pista de auditoría.
    Depende de:    MovimientoStock.save y MovimientoStock.delete.
    Cuándo usarla: Como salvaguarda de auditoría forense de stock.
    Si no opera:   Falla si se permite borrar o alterar registros históricos de stock.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]

    mov = MovimientoStock.objects.create(
        variante=var_s,
        tipo=TipoMovimientoStock.ENTRADA,
        cantidad=10,
        motivo="Ingreso de lote inicial de fábrica",
        creado_por=richard,
    )
    assert mov.pk is not None

    # Intentar modificar el movimiento
    mov.cantidad = 20
    with pytest.raises((ValidationError, RuntimeError)):
        mov.save()

    # Intentar eliminar el movimiento
    with pytest.raises((ValidationError, RuntimeError)):
        mov.delete()


@pytest.mark.django_db
def test_seguridad_vista_boleta_privada(datos_base: dict) -> None:
    """Verifica que la descarga de boletas privadas esté blindada contra accesos no autorizados.

    Qué hace:      Intenta acceder anónimamente, luego con cliente normal y finalmente como Richard.
    Va hacia:      Comprueba que anónimo y cliente reciban 403 Forbidden y Richard reciba 200 OK.
    Depende de:    vista_ver_boleta_privada, Envio y permisos del grupo Dueño.
    Cuándo usarla: Para proteger datos personales de envíos (DNI, celular, dirección en guía).
    Si no opera:   Falla si un usuario anónimo puede descargar fotos de boletas de despacho.
    """
    richard = datos_base["richard"]
    user_model = get_user_model()
    cliente_normal = user_model.objects.create_user(username="cliente_comun", password="password123")

    pedido = Pedido.objects.create(
        codigo="EMU-BOLETA01",
        estado=EstadoPedido.PAGADO,
        tipo_entrega=TipoEntrega.AGENCIA,
        agencia=AgenciaEnvio.SHALOM,
        agencia_ciudad="Chiclayo",
        agencia_referencia="Sede Balta",
        cliente_nombre="Cliente Privacidad",
        cliente_telefono="987654321",
        cliente_dni="71234567",
        subtotal=Decimal("55.00"),
        costo_envio=Decimal("15.00"),
        total=Decimal("70.00"),
    )
    archivo_boleta = SimpleUploadedFile(
        "boleta_privada.jpg", b"contenido_privado_de_boleta", content_type="image/jpeg"
    )
    envio = Envio.objects.create(
        pedido=pedido,
        agencia=AgenciaEnvio.SHALOM,
        numero_orden_agencia="ORD-777",
        clave_recojo="9988",
        imagen_boleta=archivo_boleta,
        costo_flete=Decimal("15.00"),
        quien_paga=QuienPagaFlete.CLIENTE_ADELANTADO,
        cobrado=True,
        fecha_despacho=timezone.now(),
    )

    url_boleta = reverse("pedidos:ver_boleta_privada", args=[envio.pk])
    http_client = Client()

    # 1. Anónimo -> 403 Forbidden
    resp_anonimo = http_client.get(url_boleta)
    assert resp_anonimo.status_code == 403

    # 2. Cliente normal sin rol de staff/Dueño -> 403 Forbidden
    http_client.force_login(cliente_normal)
    resp_cliente = http_client.get(url_boleta)
    assert resp_cliente.status_code == 403

    # 3. Richard (miembro del grupo Dueño / staff) -> 200 OK
    http_client.force_login(richard)
    resp_richard = http_client.get(url_boleta)
    assert resp_richard.status_code == 200
    assert resp_richard["Content-Type"] == "image/jpeg"


@pytest.mark.django_db
def test_vista_admin_venta_presencial_pos(datos_base: dict) -> None:
    """Verifica que Richard pueda operar la vista POS de venta presencial desde el panel de control.

    Qué hace:      Simula GET y POST en /admin/pedidos/pedido/venta-presencial/ con sesión de Richard.
    Va hacia:      Comprueba que cree el pedido PRESENCIAL, descuente stock y redirija con mensaje de éxito.
    Depende de:    PedidoAdmin.vista_venta_presencial y permisos administrativos.
    Cuándo usarla: Al validar la interfaz de usuario de Richard para Flujo C.
    Si no opera:   Falla si el formulario no valida cantidades o si no descuenta el inventario.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]
    stock_inicial = var_s.cantidad_stock

    http_client = Client()
    http_client.force_login(richard)
    url_pos = reverse("admin:pedidos_pedido_venta_presencial")

    # 1. GET renderiza formulario con variantes disponibles, paginación y búsqueda
    resp_get = http_client.get(url_pos)
    assert resp_get.status_code == 200
    assert "Registrar Venta Presencial" in resp_get.content.decode("utf-8")
    assert resp_get.context["pagina_obj"] is not None
    assert "modulo-totalizador-venta" in resp_get.content.decode("utf-8")

    # 1.1 GET con búsqueda indexada por palabras
    resp_busq = http_client.get(url_pos + "?q=Argentina+Messi")
    assert resp_busq.status_code == 200
    assert "ARGENTINA X MESSI" in resp_busq.content.decode("utf-8")

    # 2. POST sin cantidades seleccionadas -> Muestra error sin guardar
    resp_post_vacio = http_client.post(
        url_pos,
        {
            "cliente_nombre": "Carlos Venta Directa",
            "metodo_pago": "EFECTIVO",
            "marcar_entregado": "1",
        },
    )
    assert resp_post_vacio.status_code == 200
    assert "Debes ingresar al menos una camiseta" in resp_post_vacio.content.decode("utf-8")

    # 3. POST con 1 unidad de talla S -> Crea pedido y descuenta stock
    resp_post_valido = http_client.post(
        url_pos,
        {
            "cliente_nombre": "Carlos Venta Directa",
            "cliente_telefono": "987654321",
            "metodo_pago": "EFECTIVO",
            "marcar_entregado": "1",
            "notas": "Vendido en mostrador",
            f"cant_{var_s.id}": "1",
        },
    )
    assert resp_post_valido.status_code == 302
    var_s.refresh_from_db()
    assert var_s.cantidad_stock == stock_inicial - 1

    pedido_creado = Pedido.objects.filter(cliente_nombre="Carlos Venta Directa").first()
    assert pedido_creado is not None
    assert pedido_creado.origen == OrigenPedido.PRESENCIAL
    assert pedido_creado.estado == EstadoPedido.ENTREGADO
@pytest.mark.django_db
def test_flujo_ui_admin_contextual_y_entrada_stock_como_richard(datos_base: dict) -> None:
    """Verifica el flujo visual en /gestion/ usando exclusivamente la cuenta 'richard' (Dueño).

    Qué hace:      Simula a Richard abriendo un pedido NUEVO de agencia, cotizándolo, confirmando pago,
                   registrando despacho con boleta y reponiendo stock desde VarianteAdmin.
    Va hacia:      Comprueba permisos del grupo Dueño, panel contextual y vistas POST en el admin.
    Depende de:    PedidoAdmin, VarianteAdmin, change_form.html y permisos de preparar_local.
    Cuándo usarla: Antes de validar manualmente en el navegador los escenarios de Richard.
    Si no opera:   Falla si falta algún permiso en Dueño o si alguna ruta del panel da error HTTP.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]
    stock_inicial = var_s.cantidad_stock

    sesion: dict = {}
    agregar_al_carrito(sesion=sesion, variante_id=var_s.id, cantidad=2)
    pedido = crear_pedido_web(
        sesion=sesion,
        datos_cliente={
            "cliente_nombre": "Luis Prueba UI",
            "cliente_telefono": "987654321",
            "cliente_dni": "71234567",
            "tipo_entrega": TipoEntrega.AGENCIA,
            "agencia": AgenciaEnvio.SHALOM,
            "agencia_ciudad": "Piura",
            "agencia_referencia": "Sede Principal",
            "cf_turnstile_response": "mock-token-local",
            "acepta_privacidad": True,
        },
    )

    http_client = Client()
    http_client.force_login(richard)

    # 1. Richard abre la ficha del pedido y ve el Paso 1 (Cotizar envío)
    url_ficha = reverse("admin:pedidos_pedido_change", args=[pedido.pk])
    resp_ficha = http_client.get(url_ficha)
    assert resp_ficha.status_code == 200
    assert "Cotizar envío (pasar a COTIZADO)" in resp_ficha.content.decode("utf-8")

    # 2. Richard cotiza S/ 18.00 -> COTIZADO
    resp_cot = http_client.post(
        reverse("admin:pedidos_pedido_cotizar", args=[pedido.pk]),
        {"costo_envio": "18.00", "nota": "Tarifa Shalom Piura"},
        follow=True,
    )
    assert resp_cot.status_code == 200
    pedido.refresh_from_db()
    assert pedido.estado == EstadoPedido.COTIZADO
    assert pedido.total == Decimal("128.00")

    # 3. Richard confirma pago Yape -> PAGADO y stock -2
    resp_pago = http_client.post(
        reverse("admin:pedidos_pedido_confirmar_pago", args=[pedido.pk]),
        {"metodo_pago": "YAPE", "nota": "Yape confirmado en móvil"},
        follow=True,
    )
    assert resp_pago.status_code == 200
    pedido.refresh_from_db()
    assert pedido.estado == EstadoPedido.PAGADO
    var_s.refresh_from_db()
    assert var_s.cantidad_stock == stock_inicial - 2

    # 4. Richard registra despacho Shalom con boleta -> ENVIADO
    foto = SimpleUploadedFile("guia_piura.jpg", b"imagen-guia", content_type="image/jpeg")
    resp_env = http_client.post(
        reverse("admin:pedidos_pedido_registrar_envio", args=[pedido.pk]),
        {
            "agencia": AgenciaEnvio.SHALOM,
            "numero_orden_agencia": "SHA-PIU-1001",
            "clave_recojo": "5678",
            "costo_flete": "18.00",
            "quien_paga": QuienPagaFlete.CLIENTE_ADELANTADO,
            "cobrado": "1",
            "imagen_boleta": foto,
        },
        follow=True,
    )
    assert resp_env.status_code == 200
    pedido.refresh_from_db()
    assert pedido.estado == EstadoPedido.ENVIADO
    assert "Enviar Guía y Clave por WhatsApp" in resp_env.content.decode("utf-8")

    # 5. Richard repone +5 unidades en VarianteAdmin con auditoría
    url_var = reverse("admin:catalogo_variante_change", args=[var_s.pk])
    resp_var = http_client.get(url_var)
    assert resp_var.status_code == 200
    assert "Registrar Movimiento de Stock" in resp_var.content.decode("utf-8")

    resp_entrada = http_client.post(
        reverse("admin:catalogo_variante_entrada_stock", args=[var_s.pk]),
        {"cantidad": "5", "motivo": "Reposición desde taller"},
        follow=True,
    )
    assert resp_entrada.status_code == 200
    var_s.refresh_from_db()
    assert var_s.cantidad_stock == stock_inicial - 2 + 5
@pytest.mark.django_db
def test_seguimiento_en_vivo_contextual_y_tooltips_admin(datos_base: dict) -> None:
    """Verifica el seguimiento en vivo (JSON + parcial), mensajes por estado y tooltips admin.

    Qué hace:      Prueba /pedidos/<codigo>/estado-json/, /?parcial=1, cambios de bloque Siguiente Paso
                   según estado y verifica que las 4 tablas del admin carguen tooltips y colores para richard.
    Va hacia:      Garantiza privacidad en JSON, actualización dinámica y UX sin errores 500 en admin.
    Depende de:    vista_estado_pedido_json, obtener_pedido_publico y encabezado_con_tooltip.
    Cuándo usarla: En la verificación integral de mejoras UX de la Fase 3.
    Si no opera:   Falla si el JSON expone claves privadas o si alguna vista admin da error.
    """
    richard = datos_base["richard"]
    var_s = datos_base["var_s"]

    sesion: dict = {}
    agregar_al_carrito(sesion=sesion, variante_id=var_s.id, cantidad=1)
    pedido = crear_pedido_web(
        sesion=sesion,
        datos_cliente={
            "cliente_nombre": "Ana Seguimiento Vivo",
            "cliente_telefono": "987654321",
            "cliente_dni": "74561239",
            "tipo_entrega": TipoEntrega.AGENCIA,
            "agencia": AgenciaEnvio.OLVA,
            "agencia_ciudad": "Cusco",
            "agencia_referencia": "Av. El Sol",
            "cf_turnstile_response": "mock-token-local",
            "acepta_privacidad": True,
        },
    )

    http_client = Client()
    url_json = reverse("pedidos:estado_pedido_json", kwargs={"codigo": pedido.codigo})
    url_pub = reverse("pedidos:detalle_pedido", kwargs={"codigo": pedido.codigo})

    # 1. Estado NUEVO -> JSON y mensaje inicial
    resp_json_1 = http_client.get(url_json)
    assert resp_json_1.status_code == 200
    data_1 = resp_json_1.json()
    assert data_1["estado"] == EstadoPedido.NUEVO
    assert data_1["es_estado_terminal"] is False

    # 2. Cotizar + Confirmar pago -> Estado PAGADO cambia tarjeta y WhatsApp
    cotizar_envio(pedido=pedido, costo_envio=Decimal("20.00"), usuario=richard)
    confirmar_pago(pedido=pedido, metodo_pago="YAPE", usuario=richard)

    resp_parcial = http_client.get(f"{url_pub}?parcial=1")
    assert resp_parcial.status_code == 200
    html_pagado = resp_parcial.content.decode("utf-8")
    assert "Richard está preparando tu paquete" in html_pagado
    assert "ENVÍA TU PEDIDO A RICHARD" not in html_pagado.upper()

    # 3. Registrar envío -> JSON actualiza, muestra orden en público pero jamás clave secreta
    foto = SimpleUploadedFile("olva_cusco.jpg", b"boleta-olva", content_type="image/jpeg")
    registrar_envio_agencia(
        pedido=pedido,
        agencia=AgenciaEnvio.OLVA,
        numero_orden_agencia="OLV-998811",
        clave_recojo="7391",
        imagen_boleta=foto,
        costo_flete=Decimal("20.00"),
        quien_paga=QuienPagaFlete.CLIENTE_ADELANTADO,
        cobrado=True,
        usuario=richard,
    )
    resp_env_html = http_client.get(url_pub).content.decode("utf-8")
    assert "OLV-998811" in resp_env_html
    assert "7391" not in resp_env_html

    # 4. Todos los módulos admin tienen paginación, buscador, zoom 0.85 e íconos toltip.png
    from django.contrib import admin as django_admin

    for modelo, model_admin in django_admin.site._registry.items():
        if modelo._meta.app_label in ("nucleo", "catalogo", "pedidos"):
            assert model_admin.list_per_page <= 20, f"{modelo} sin paginación compacta"
            assert len(model_admin.search_fields) >= 1, f"{modelo} sin buscador configurado"

    http_client.force_login(richard)
    for ruta_admin in (
        "admin:catalogo_categoria_changelist",
        "admin:catalogo_producto_changelist",
        "admin:catalogo_movimientostock_changelist",
        "admin:catalogo_variante_changelist",
        "admin:pedidos_pedido_changelist",
        "admin:pedidos_envio_changelist",
    ):
        resp_adm = http_client.get(reverse(ruta_admin))
        assert resp_adm.status_code == 200
        cuerpo = resp_adm.content.decode("utf-8")
        assert "/static/toltip.png" in cuerpo
        assert "emuna_flat_unfold.css" in cuerpo
        assert "unfold/css/styles.css" in cuerpo
        if "movimientostock" in ruta_admin:
            assert "Salida -1" in cuerpo

    # 5. Ficha de Producto renderiza toltip.png en títulos inline y columnas
    resp_prod = http_client.get(
        reverse("admin:catalogo_producto_change", args=[var_s.producto_id])
    )
    assert resp_prod.status_code == 200
    cuerpo_prod = resp_prod.content.decode("utf-8")
    assert "Imágenes de producto" in cuerpo_prod
    assert "Variantes de talla" in cuerpo_prod
    assert "Reglas de precio por mayor" in cuerpo_prod
    assert "/static/toltip.png" in cuerpo_prod
    assert "Escalas de descuento por volumen" in cuerpo_prod

    # 6. POS de venta presencial tiene 1 solo buscador, tooltips, reglas JSON por mayor y aplica 3+ en POST
    ReglaPrecio.objects.get_or_create(
        producto=var_s.producto,
        cantidad_minima=3,
        defaults={"precio_unidad": Decimal("50.00")},
    )
    var_s.refresh_from_db()
    if var_s.cantidad_stock < 3:
        var_s.cantidad_stock = 5
        var_s.save(update_fields=["cantidad_stock"])

    resp_pos = http_client.get(reverse("admin:pedidos_pedido_venta_presencial"))
    assert resp_pos.status_code == 200
    cuerpo_pos = resp_pos.content.decode("utf-8")
    assert "input-busqueda-servidor" in cuerpo_pos
    assert "filtro-rapido-local" not in cuerpo_pos
    assert "/static/toltip.png" in cuerpo_pos
    assert "pos-reglas-precio-data" in cuerpo_pos
    assert "3+ u: S/ 50.00" in cuerpo_pos

    resp_pos_post = http_client.post(
        reverse("admin:pedidos_pedido_venta_presencial"),
        {
            "cliente_nombre": "Cliente Mayorista POS",
            "metodo_pago": "YAPE",
            "marcar_entregado": "1",
            f"cant_{var_s.id}": "3",
        },
        follow=True,
    )
    assert resp_pos_post.status_code == 200
    pedido_mayor = Pedido.objects.filter(cliente_nombre="Cliente Mayorista POS").latest("id")
    assert pedido_mayor.total == Decimal("150.00")

    # 7. Todas las vistas dentro de /gestion/ incluyen reglas responsive, navegación móvil y scroll inline
    assert "emuna-mobile-quicknav" in cuerpo_prod
    assert "emuna-inline-scroll" in cuerpo_prod
    assert "pos-desglose-wrap" in cuerpo_pos
    assert "emuna_flat_unfold.css" in cuerpo_pos
    assert "@media (max-width: 767px)" in cuerpo_pos

    # Hoja Flat Design compartida de /gestion/ existe y declara zoom 0.85 + breakpoints móviles
    from django.contrib.staticfiles import finders

    ruta_css_flat = finders.find("css/emuna_flat_unfold.css")
    assert ruta_css_flat is not None
    contenido_css_flat = Path(ruta_css_flat).read_text(encoding="utf-8")
    assert "zoom: 0.85;" in contenido_css_flat
    assert "box-shadow: none !important;" in contenido_css_flat
    assert "@media (max-width: 1024px)" in contenido_css_flat
    assert "position: sticky;" in contenido_css_flat
    assert ".emuna-mobile-sticky-bar" in contenido_css_flat
    assert ".emuna-table-scroll," in contenido_css_flat
    assert "#header-inner span.cursor-pointer > span.material-symbols-outlined" in contenido_css_flat
    assert "touch-action: pan-x pan-y;" in contenido_css_flat
    assert "min-width: 680px;" in contenido_css_flat
    assert "@media (max-width: 767px)" in contenido_css_flat

    for ruta_gestion in (
        reverse("admin:index"),
        reverse("tablero:resumen"),
        reverse("admin:app_list", kwargs={"app_label": "catalogo"}),
        reverse("admin:app_list", kwargs={"app_label": "pedidos"}),
        reverse("admin:catalogo_categoria_changelist"),
        reverse("admin:catalogo_variante_changelist"),
        reverse("admin:pedidos_pedido_changelist"),
        reverse("admin:pedidos_pedido_change", args=[pedido.pk]),
        reverse("admin:catalogo_variante_change", args=[var_s.pk]),
    ):
        resp_g = http_client.get(ruta_gestion)
        assert resp_g.status_code == 200
        html_g = resp_g.content.decode("utf-8")
        assert '<div class="emuna-mobile-sticky-bar">' in html_g
        assert "__emunaThemePatched" in html_g
        assert "window.innerWidth < 1280" in html_g
        assert '<nav class="emuna-mobile-quicknav"' in html_g
        assert "emuna-touch-tooltip" in html_g
        assert "emuna_flat_unfold.css" in html_g
        assert "unfold/css/styles.css" in html_g
        assert "&lt;img src=" not in html_g
        if ruta_gestion == reverse("admin:index"):
            assert "Accesos rápidos de venta diaria" in html_g
            assert "Ventas confirmadas hoy" in html_g

    # Login de /gestion/ sin usuario autenticado omite quicknav y carga Unfold Flat Design en español
    cliente_anon = Client()
    resp_login = cliente_anon.get(reverse("admin:login"))
    assert resp_login.status_code == 200
    html_login = resp_login.content.decode("utf-8")
    assert '<nav class="emuna-mobile-quicknav"' not in html_login
    assert "emuna_flat_unfold.css" in html_login
    assert "login-form" in html_login
    assert "Bienvenido a" in html_login

    # 8. Cabecera semáforo real en variante agotada, limpiar búsqueda (?q=) y filas por página visibles
    resp_q = http_client.get(reverse("admin:catalogo_variante_changelist") + "?q=EMU")
    assert resp_q.status_code == 200
    html_q = resp_q.content.decode("utf-8")
    assert "✕ Ver todos" in html_q
    assert "Limpiar búsqueda y ver todos" in html_q
    assert "filas/pág." in html_q
    assert "filas por página" in html_q

    var_s.cantidad_stock = 0
    var_s.save(update_fields=["cantidad_stock"])
    resp_var_cero = http_client.get(reverse("admin:catalogo_variante_change", args=[var_s.pk]))
    assert resp_var_cero.status_code == 200
    html_var_cero = resp_var_cero.content.decode("utf-8")
    assert "🔴 [ROJO] Agotado: 0 und." in html_var_cero
    assert "🟢 [VERDE] Stock actual: 0 und." not in html_var_cero
