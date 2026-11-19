"""Pruebas automatizadas de la Fase 4: Tablero operativo, alertas de negocio y exportación CSV."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.catalogo.admin import VarianteAdmin
from apps.catalogo.models import Categoria, Producto, Variante
from apps.nucleo.selectores import obtener_configuracion_tienda
from apps.pedidos.models import EstadoPedido, Pedido, TipoEntrega
from apps.pedidos.servicios import (
    agregar_al_carrito,
    cancelar_o_rechazar,
    confirmar_pago_y_entregar,
    crear_pedido_web,
    registrar_venta_presencial,
)
from apps.tablero.selectores import obtener_resumen_tablero, resolver_rango_fechas
from apps.tablero.servicios import generar_csv_alertas_stock, generar_csv_ventas


@pytest.fixture
def escenario_tablero(db) -> dict:
    """Prepara usuarios, productos de prueba, stock variado y pedidos para probar el tablero.

    Qué hace:      Ejecuta preparar_local/cargar_demo e incorpora variantes críticas de prueba.
    Va hacia:      Retorna diccionario con usuario Richard, cliente estándar y objetos base.
    Depende de:    Comandos preparar_local, cargar_demo y modelos de catalogo/nucleo.
    Cuándo usarla: Como fixture en todas las pruebas unitarias e integración de test_tablero.
    Si no opera:   Falla si las migraciones o tablas maestras no están inicializadas.
    """
    call_command("preparar_local")
    call_command("cargar_demo")
    user_model = get_user_model()
    richard = user_model.objects.get(username="richard")
    cliente_normal = user_model.objects.create_user(
        username="cliente_sin_permiso",
        password="ClaveSeguraCliente123!",
        is_staff=False,
    )
    categoria = Categoria.objects.first()

    # Producto con una talla agotada, una bajo umbral heredado global (None) y una normal
    prod_critico = Producto.objects.create(
        categoria=categoria,
        nombre="Camiseta Control Crítico",
        slug="camiseta-control-critico",
        sku="EMU-CRIT01",
        precio_unidad=Decimal("60.00"),
        activo=True,
    )
    var_agotada = Variante.objects.create(
        producto=prod_critico,
        talla="S",
        sku="EMU-CRIT01-S",
        cantidad_stock=0,
        umbral_stock_bajo=3,
        activa=True,
    )
    var_baja_global = Variante.objects.create(
        producto=prod_critico,
        talla="M",
        sku="EMU-CRIT01-M",
        cantidad_stock=2,
        umbral_stock_bajo=None,
        activa=True,
    )
    var_normal = Variante.objects.create(
        producto=prod_critico,
        talla="L",
        sku="EMU-CRIT01-L",
        cantidad_stock=12,
        umbral_stock_bajo=3,
        activa=True,
    )
    var_inactiva = Variante.objects.create(
        producto=prod_critico,
        talla="XL",
        sku="EMU-CRIT01-XL",
        cantidad_stock=0,
        umbral_stock_bajo=3,
        activa=False,
    )

    return {
        "richard": richard,
        "cliente_normal": cliente_normal,
        "prod_critico": prod_critico,
        "var_agotada": var_agotada,
        "var_baja_global": var_baja_global,
        "var_normal": var_normal,
        "var_inactiva": var_inactiva,
    }


@pytest.mark.django_db
def test_metricas_ventas_canales_mas_vendidos_y_sin_ventas(escenario_tablero: dict) -> None:
    """Verifica totales de venta Web/POS, exclusión de no pagados, más vendidos y sin ventas.

    Qué hace:      Registra venta Web confirmada, venta POS, pedido pendiente y pedido cancelado.
    Va hacia:      Comprueba KPIs exactos en obtener_resumen_tablero() y detección sin rotación.
    Depende de:    crear_pedido_web, confirmar_pago_y_entregar, registrar_venta_presencial.
    Cuándo usarla: En la verificación financiera y comercial del Tablero de Fase 4.
    Si no opera:   Falla si cuenta pedidos NUEVO/CANCELADO como ingresos o falla el ranking.
    """
    richard = escenario_tablero["richard"]
    var_normal = escenario_tablero["var_normal"]
    prod_critico = escenario_tablero["prod_critico"]

    # 1. Venta Web confirmada: 2 unidades de var_normal (S/ 60.00 x 2 = S/ 120.00)
    sesion_web: dict = {}
    agregar_al_carrito(sesion=sesion_web, variante_id=var_normal.id, cantidad=2)
    ped_web = crear_pedido_web(
        sesion=sesion_web,
        datos_cliente={
            "cliente_nombre": "Carlos Cliente Web",
            "cliente_telefono": "987654321",
            "tipo_entrega": TipoEntrega.PUNTO_ENCUENTRO,
            "punto_encuentro": "Real Plaza Centro Cívico",
            "acepta_privacidad": True,
        },
        ip_cliente="127.0.0.1",
    )
    confirmar_pago_y_entregar(pedido=ped_web, metodo_pago="YAPE", usuario=richard)

    # 2. Venta POS presencial: 1 unidad del catálogo demo (Argentina Messi M = S/ 55.00)
    var_messi_m = Variante.objects.get(sku="EMU-ARG10-M")
    registrar_venta_presencial(
        lineas=[{"variante_id": var_messi_m.id, "cantidad": 1}],
        metodo_pago="EFECTIVO",
        usuario=richard,
        cliente_nombre="Cliente Feria",
        marcar_entregado=True,
    )

    # 3. Pedido pendiente NUEVO (agencia) que NO debe sumarse como ingreso
    sesion_nuevo: dict = {}
    agregar_al_carrito(sesion=sesion_nuevo, variante_id=var_normal.id, cantidad=1)
    crear_pedido_web(
        sesion=sesion_nuevo,
        datos_cliente={
            "cliente_nombre": "=FORMULA_MALICIOSA",
            "cliente_telefono": "912345678",
            "cliente_dni": "45678912",
            "tipo_entrega": TipoEntrega.AGENCIA,
            "agencia": "SHALOM",
            "agencia_ciudad": "Cusco",
            "agencia_referencia": "Wanchaq",
            "acepta_privacidad": True,
        },
    )

    # 4. Pedido pagado y luego cancelado que NO debe figurar en ventas ni más vendidos
    ped_cancelado = registrar_venta_presencial(
        lineas=[{"variante_id": var_normal.id, "cantidad": 1}],
        metodo_pago="YAPE",
        usuario=richard,
        cliente_nombre="Anulado",
        marcar_entregado=False,
    )
    cancelar_o_rechazar(
        pedido=ped_cancelado,
        nuevo_estado=EstadoPedido.CANCELADO,
        usuario=richard,
        nota="Cliente desistió",
    )

    resumen = obtener_resumen_tablero(periodo="hoy")
    kpis = resumen["kpis"]

    assert kpis["cantidad_pedidos"] == 2
    assert kpis["unidades_vendidas"] == 3
    assert kpis["ventas_web"] == Decimal("120.00")
    assert kpis["pedidos_web"] == 1
    assert kpis["ventas_presencial"] == Decimal("55.00")
    assert kpis["pedidos_presencial"] == 1
    assert kpis["total_ventas"] == Decimal("175.00")
    assert kpis["ticket_promedio"] == Decimal("87.50")

    # Más vendidos debe ordenar primero a prod_critico (2 und.) y luego Argentina Messi (1 und.)
    assert len(resumen["mas_vendidos"]) >= 2
    assert resumen["mas_vendidos"][0]["producto_id"] == prod_critico.id
    assert resumen["mas_vendidos"][0]["unidades"] == 2
    assert resumen["mas_vendidos"][1]["unidades"] == 1

    # Productos activos sin ventas no debe incluir los 2 productos vendidos
    ids_sin_ventas = {p["producto_id"] for p in resumen["productos_sin_ventas"]}
    assert prod_critico.id not in ids_sin_ventas
    assert var_messi_m.producto_id not in ids_sin_ventas
    assert len(ids_sin_ventas) >= 1

    # Rango invertido se normaliza automáticamente
    hoy = timezone.localdate()
    ayer = hoy - timedelta(days=1)
    desde_ok, hasta_ok, codigo_ok = resolver_rango_fechas(
        desde=hoy.isoformat(), hasta=ayer.isoformat()
    )
    assert desde_ok == ayer
    assert hasta_ok == hoy
    assert codigo_ok == "personalizado"


@pytest.mark.django_db
def test_alertas_stock_bajo_umbral_global_y_pendientes_antiguos(
    escenario_tablero: dict,
) -> None:
    """Valida detección de variantes agotadas/bajas (incluyendo umbral NULL) y pedidos > 24 h.

    Qué hace:      Simula pedidos envejecidos (> 24h) vs recientes e inspecciona alertas de stock.
    Va hacia:      Confirma niveles ROJO/AMBAR, omisión de variantes inactivas y cálculo de espera.
    Depende de:    obtener_resumen_tablero, Pedido y VarianteAdmin.stock_semaforo.
    Cuándo usarla: En la validación de alertas críticas para reposición y seguimiento.
    Si no opera:   Falla si una variante con umbral NULL rompe o si un pedido reciente dispara alerta.
    """
    config = obtener_configuracion_tienda()
    var_agotada = escenario_tablero["var_agotada"]
    var_baja_global = escenario_tablero["var_baja_global"]
    var_normal = escenario_tablero["var_normal"]
    var_inactiva = escenario_tablero["var_inactiva"]

    ahora = timezone.now()
    ped_viejo_nuevo = Pedido.objects.create(
        codigo="EMU-VIEJO01",
        estado=EstadoPedido.NUEVO,
        tipo_entrega=TipoEntrega.AGENCIA,
        agencia="SHALOM",
        agencia_ciudad="Arequipa",
        agencia_referencia="Cerro Colorado",
        cliente_nombre="Cliente Demorado",
        cliente_dni="41234567",
        cliente_telefono="987001122",
        subtotal=Decimal("55.00"),
        total=Decimal("55.00"),
    )
    Pedido.objects.filter(pk=ped_viejo_nuevo.pk).update(
        fecha_creacion=ahora - timedelta(hours=config.horas_pedido_pendiente + 6)
    )

    ped_viejo_entregado = Pedido.objects.create(
        codigo="EMU-CER01",
        estado=EstadoPedido.ENTREGADO,
        tipo_entrega=TipoEntrega.RECOJO,
        cliente_nombre="Ya Cerrado",
        cliente_telefono="987001133",
        subtotal=Decimal("55.00"),
        total=Decimal("55.00"),
    )
    Pedido.objects.filter(pk=ped_viejo_entregado.pk).update(
        fecha_creacion=ahora - timedelta(hours=48)
    )

    Pedido.objects.create(
        codigo="EMU-REC01",
        estado=EstadoPedido.COTIZADO,
        tipo_entrega=TipoEntrega.PUNTO_ENCUENTRO,
        cliente_nombre="Cliente Reciente",
        cliente_telefono="987001144",
        subtotal=Decimal("55.00"),
        total=Decimal("55.00"),
    )

    resumen = obtener_resumen_tablero(periodo="mes")
    mapa_stock = {a["variante_id"]: a for a in resumen["alertas_stock"]}

    assert var_agotada.id in mapa_stock
    assert mapa_stock[var_agotada.id]["nivel"] == "ROJO"
    assert var_baja_global.id in mapa_stock
    assert mapa_stock[var_baja_global.id]["nivel"] == "AMBAR"
    assert mapa_stock[var_baja_global.id]["umbral_efectivo"] == config.umbral_stock_bajo
    assert var_normal.id not in mapa_stock
    assert var_inactiva.id not in mapa_stock

    # Pedidos pendientes antiguos solo debe contener a EMU-VIEJO01
    codigos_pend = [p["codigo"] for p in resumen["pedidos_pendientes_antiguos"]]
    assert codigos_pend == ["EMU-VIEJO01"]
    assert resumen["pedidos_pendientes_antiguos"][0]["horas_espera"] >= config.horas_pedido_pendiente
    assert "api.whatsapp.com/send" in resumen["pedidos_pendientes_antiguos"][0]["url_whatsapp"]

    # VarianteAdmin.stock_semaforo también debe soportar umbral_stock_bajo = None sin lanzar TypeError
    from django.contrib.admin.sites import AdminSite

    admin_var = VarianteAdmin(Variante, AdminSite())
    html_bajo = admin_var.stock_semaforo(var_baja_global)
    assert "🟡 Bajo (2)" in html_bajo
    assert "[ÁMBAR]" not in html_bajo
    assert admin_var.umbral_col(var_baja_global) == "Global"


@pytest.mark.django_db
def test_vistas_tablero_permisos_ui_movil_y_csv_seguro(escenario_tablero: dict) -> None:
    """Valida control de acceso al tablero, diseño responsivo y exportación CSV anti-inyección.

    Qué hace:      Prueba respuestas HTTP para anónimo/cliente/Richard, render HTML y CSV con fórmulas.
    Va hacia:      Asegura protección de rutas privadas y neutralización de =, +, -, @ en CSV.
    Depende de:    Client de Django, vistas tablero y generar_csv_ventas/generar_csv_alertas_stock.
    Cuándo usarla: Al validar seguridad y descargables de la Fase 4.
    Si no opera:   Falla si expone métricas a clientes o permite fórmulas sin comilla simple en CSV.
    """
    richard = escenario_tablero["richard"]
    cliente_normal = escenario_tablero["cliente_normal"]
    var_normal = escenario_tablero["var_normal"]

    url_tablero = reverse("tablero:resumen")
    url_csv_ventas = reverse("tablero:exportar_ventas_csv")
    url_csv_stock = reverse("tablero:exportar_stock_csv")

    # 1. Anónimo -> 302 a /gestion/login/
    c_anon = Client()
    for ruta in (url_tablero, url_csv_ventas, url_csv_stock):
        resp = c_anon.get(ruta)
        assert resp.status_code == 302
        assert reverse("admin:login") in resp.url

    # 2. Usuario autenticado sin permiso -> 403 Forbidden
    c_cliente = Client()
    c_cliente.force_login(cliente_normal)
    for ruta in (url_tablero, url_csv_ventas, url_csv_stock):
        resp = c_cliente.get(ruta)
        assert resp.status_code == 403

    # 3. Venta POS con nombre potencialmente malicioso para probar sanitización CSV
    registrar_venta_presencial(
        lineas=[{"variante_id": var_normal.id, "cantidad": 1}],
        metodo_pago="YAPE",
        usuario=richard,
        cliente_nombre="=HYPERLINK(\"http://evil.example\",\"clic\")",
        marcar_entregado=True,
    )

    c_richard = Client()
    c_richard.force_login(richard)

    # /gestion/ inicio muestra acceso rápido al Tablero y POS
    resp_admin = c_richard.get(reverse("admin:index"))
    assert resp_admin.status_code == 200
    assert url_tablero in resp_admin.content.decode("utf-8")

    # Tablero HTML renderiza tarjetas, tooltips formal y diseño móvil
    resp_tab = c_richard.get(f"{url_tablero}?periodo=hoy")
    assert resp_tab.status_code == 200
    html_tab = resp_tab.content.decode("utf-8")
    assert "Tablero Operativo y Alertas" in html_tab
    assert "toltip.png" in html_tab
    assert '<nav class="emuna-mobile-quicknav"' in html_tab
    assert "@media (max-width: 767px)" in html_tab
    assert "grid-template-columns: minmax(0, 1fr);" in html_tab
    assert "emuna-table-scroll" in html_tab
    assert "emuna-swipe-hint" in html_tab
    assert "EMU-CRIT01-S" in html_tab
    assert "Clientes VIP y Top Compradores" in html_tab
    assert 'data-emuna-mob-modal="Alertas de Stock"' in html_tab
    assert 'data-emuna-mob-modal="Cliente VIP"' in html_tab

    # CSV de ventas: BOM UTF-8, sin caché, descarga y sanitización de fórmula '=HYPERLINK...'
    resp_csv_v = c_richard.get(f"{url_csv_ventas}?periodo=hoy")
    assert resp_csv_v.status_code == 200
    assert resp_csv_v["Cache-Control"] == "no-store"
    assert "attachment;" in resp_csv_v["Content-Disposition"]
    texto_v = resp_csv_v.content.decode("utf-8")
    assert texto_v.startswith("\ufeff")
    assert "'=HYPERLINK" in texto_v

    # CSV de alertas de stock: incluye BOM UTF-8 y SKU agotado/bajo
    resp_csv_s = c_richard.get(url_csv_stock)
    assert resp_csv_s.status_code == 200
    assert resp_csv_s["Cache-Control"] == "no-store"
    texto_s = resp_csv_s.content.decode("utf-8")
    assert texto_s.startswith("\ufeff")
    assert "ROJO - AGOTADO" in texto_s
    assert "AMBAR - STOCK BAJO" in texto_s

    # Verificación directa de helpers CSV
    nombre_v, bytes_v = generar_csv_ventas(periodo="hoy")
    nombre_s, bytes_s = generar_csv_alertas_stock()
    assert nombre_v.endswith(".csv")
    assert nombre_s.endswith(".csv")
    assert bytes_v.startswith(b"\xef\xbb\xbf")
    assert bytes_s.startswith(b"\xef\xbb\xbf")
    assert b"Total Cobrado (S/)" in bytes_v
    assert b"'=HYPERLINK" in bytes_v
    assert b"EMU-CRIT01-S" in bytes_s
