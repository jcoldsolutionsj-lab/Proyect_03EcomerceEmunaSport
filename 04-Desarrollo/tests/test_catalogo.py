"""Pruebas unitarias, de integración, SEO y verificador de enlaces rotos de la Fase 1 (Catálogo)."""
import re
from decimal import Decimal
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse

from apps.catalogo.models import (
    Categoria,
    Equipo,
    Producto,
    TipoEquipacion,
    TipoEquipo,
    Variante,
)
from apps.catalogo.selectores import (
    buscar_productos_para_ia,
    calcular_precio_unitario_aplicado,
    listar_productos_catalogo,
    obtener_producto_detalle_por_slug,
)
from apps.catalogo.servicios import validar_y_generar_versiones_webp


@pytest.mark.django_db
def test_cargar_demo_y_reglas_precio_por_mayor() -> None:
    """Verifica que cargar_demo cree las 4 categorías, los 8 productos y aplique precios por mayor.

    Qué hace:      Ejecuta cargar_demo, inspecciona Argentina x Messi #10 y calcula sus tramos por mayor.
    Va hacia:      Valida TBL_RCATEGORIA, TBL_RPRODUCTO, TBL_RIMAGEN_PRODUCTO, TBL_RVARIANTE y TBL_RREGLA_PRECIO.
    Depende de:    call_command('cargar_demo') y calcular_precio_unitario_aplicado().
    Cuándo usarla: En la suite de pruebas de la Fase 1.
    Si no opera:   Falla si faltan las 5 fotos WebP, las tallas S/M/L/XL o si el cálculo por mayor es erróneo.
    """
    call_command("cargar_demo")

    assert Categoria.objects.filter(activa=True).count() == 4
    assert Producto.objects.filter(activo=True).count() == 8

    messi = obtener_producto_detalle_por_slug(slug="argentina-x-messi-10")
    assert messi.precio_unidad == Decimal("55.00")
    assert messi.precio_anterior == Decimal("69.90")
    assert messi.monto_ahorro == Decimal("14.90")
    assert messi.porcentaje_descuento == 21
    assert messi.imagenes.count() == 5
    assert [v.talla for v in messi.variantes.all()] == ["S", "M", "L", "XL"]

    assert calcular_precio_unitario_aplicado(producto=messi, cantidad_total_producto=1) == Decimal("55.00")
    assert calcular_precio_unitario_aplicado(producto=messi, cantidad_total_producto=2) == Decimal("55.00")
    assert calcular_precio_unitario_aplicado(producto=messi, cantidad_total_producto=3) == Decimal("50.00")
    assert calcular_precio_unitario_aplicado(producto=messi, cantidad_total_producto=5) == Decimal("50.00")
    assert calcular_precio_unitario_aplicado(producto=messi, cantidad_total_producto=6) == Decimal("45.00")
    assert calcular_precio_unitario_aplicado(producto=messi, cantidad_total_producto=12) == Decimal("45.00")


@pytest.mark.django_db
def test_filtros_catalogo_por_talla_categoria_y_busqueda() -> None:
    """Comprueba que listar_productos_catalogo filtre por categoría, talla con stock y texto.

    Qué hace:      Ejecuta consultas con distintos filtros y verifica los productos devueltos.
    Va hacia:      Asegura que el buscador y los cuadros de talla [S][M][L][XL] operen correctamente.
    Depende de:    listar_productos_catalogo() y datos de cargar_demo.
    Cuándo usarla: En las pruebas de aceptación del catálogo.
    Si no opera:   Falla si devuelve productos agotados en esa talla o de otra categoría.
    """
    call_command("cargar_demo")

    selecciones = listar_productos_catalogo(categoria_slug="selecciones")
    assert selecciones.count() == 3

    por_messi = listar_productos_catalogo(busqueda="Messi")
    assert por_messi.count() == 1
    assert por_messi.first().sku == "EMU-ARG10"

    # En cargar_demo, EMU-PAR03 tiene talla XL en stock 0; al filtrar por XL no debe aparecer EMU-PAR03
    con_talla_xl = listar_productos_catalogo(talla="XL")
    skus_xl = {p.sku for p in con_talla_xl}
    assert "EMU-ARG10" in skus_xl
    assert "EMU-PAR03" not in skus_xl


def test_servicio_procesamiento_webp_y_bloqueo_archivos_peligrosos(tmp_path: Path) -> None:
    """Verifica que validar_y_generar_versiones_webp comprima a WebP y rechace ejecutables/SVG.

    Qué hace:      Procesa argentina_1.jpg hacia tmp_path y prueba también un archivo .svg bloqueado.
    Va hacia:      Garantiza el requisito #11 (imágenes WebP) y el Pilar 5 Anti-Hacking en subidas.
    Depende de:    validar_y_generar_versiones_webp y Pillow.
    Cuándo usarla: En la suite de pruebas de la Fase 1.
    Si no opera:   Falla si no genera los archivos .webp o si acepta una extensión prohibida.
    """
    candidatos = [
        Path(settings.REPO_DIR)
        / "03-Diseno-Tecnico/assets/productos-demo/ARGENTINA 2026 - 2027/argentina_1.jpg",
        Path(settings.REPO_DIR)
        / "03-Diseno-Tecnico/assets/productos-demo/argentina-messi/originales/argentina_1.jpg",
    ]
    origen_real = next((p for p in candidatos if p.exists()), None)
    if origen_real is None:
        from PIL import Image

        origen_real = tmp_path / "origen_valido.jpg"
        Image.new("RGB", (1000, 1200), color=(10, 10, 10)).save(origen_real, format="JPEG")
    rel_min, rel_det = validar_y_generar_versiones_webp(
        ruta_archivo_origen=origen_real,
        slug_producto="test-messi",
        orden=1,
        directorio_salida=tmp_path,
    )
    assert (tmp_path / "test-messi_1_miniatura.webp").exists()
    assert (tmp_path / "test-messi_1_detalle.webp").exists()
    assert rel_min.endswith("_miniatura.webp")
    assert rel_det.endswith("_detalle.webp")

    falso_svg = tmp_path / "malicioso.svg"
    falso_svg.write_text("<svg onload=alert(1)></svg>", encoding="utf-8")
    with pytest.raises(ValidationError):
        validar_y_generar_versiones_webp(
            ruta_archivo_origen=falso_svg,
            slug_producto="malo",
            orden=1,
            directorio_salida=tmp_path,
        )


@pytest.mark.django_db
def test_vistas_publicas_seo_legales_y_enlaces_sin_roturas(client) -> None:
    """Audita las vistas públicas, JSON-LD, robots.txt, sitemap.xml y que no existan enlaces rotos.

    Qué hace:      Recorre /, /productos/argentina-x-messi-10/, páginas legales, robots.txt y sitemap.xml.
    Va hacia:      Valida los requisitos pre-lanzamiento #1, #2, #3, #5, #6, #7, #10, #16, #18 y #20.
    Depende de:    Vistas de apps.catalogo y django.test.Client.
    Cuándo usarla: En cada ejecución de pytest antes de hacer commit/merge.
    Si no opera:   Falla si alguna ruta devuelve 404/500 o si falta el JSON-LD / bloqueo en robots.txt.
    """
    call_command("cargar_demo")

    # 1. Portada y Carrusel de Bienvenida con los 3 Videos Reales (sin lupa ni textos técnicos)
    res_inicio = client.get(reverse("catalogo:inicio"))
    assert res_inicio.status_code == 200
    html_inicio = res_inicio.content.decode("utf-8")
    assert "ARGENTINA X MESSI #10" in html_inicio
    assert "banner_1.mp4" in html_inicio
    assert "banner_2.mp4" in html_inicio
    assert "banner_3.mp4" in html_inicio
    assert "playbackRate = 0.72" in html_inicio
    assert "escribirSuave" in html_inicio
    assert "whatsapp.png" in html_inicio
    assert "yape.svg" in html_inicio
    assert "carro-de-la-carretilla.png" in html_inicio
    assert "boton-whatsapp-pinpon" in html_inicio
    assert "radar-anillo-1" in html_inicio
    assert "badge-notificacion-uno" in html_inicio
    assert "Logo_animado.mp4" in html_inicio
    assert "logo_emuna_transparente.png" in html_inicio
    assert "estuve%20revisando%20tu%20p%C3%A1gina%20web" in html_inicio
    assert "EMUNÁ SPORT · RICHARD" in html_inicio
    assert "QUIERO COMPRAR POR MAYOR" in html_inicio
    assert "S/ 55.00" in html_inicio
    assert "S/ 69.90" in html_inicio
    assert "Ahorras S/ 14.90" in html_inicio
    assert "cursor-zoom-in" not in html_inicio
    assert "Ver tallas y zoom" not in html_inicio
    assert "01 · Cancha en Vivo" not in html_inicio

    # 2. Ficha de producto con 5 miniaturas, precios por mayor, ahorro exacto, lupa limpia y JSON-LD
    res_detalle = client.get(
        reverse("catalogo:detalle_producto", kwargs={"slug": "argentina-x-messi-10"})
    )
    assert res_detalle.status_code == 200
    html_detalle = res_detalle.content.decode("utf-8")
    assert '"@type": "Product"' in html_detalle
    assert '"priceCurrency": "PEN"' in html_detalle
    assert "Ahorras S/ 14.90 (-21%)" in html_detalle
    assert "actualizarLupa($event)" in html_detalle
    assert "Acerca el mouse para Lupa Zoom" not in html_detalle
    assert "whatsapp.png" in html_detalle
    assert "yape.svg" in html_detalle
    assert "carro-de-la-carretilla.png" in html_detalle
    assert "S/ 50.00" in html_detalle
    assert "S/ 45.00" in html_detalle

    # 3. Páginas legales (Aviso legal, Privacidad Ley N.º 29733 y Cookies)
    for nombre_ruta in ["catalogo:aviso_legal", "catalogo:privacidad", "catalogo:cookies"]:
        res_legal = client.get(reverse(nombre_ruta))
        assert res_legal.status_code == 200

    # 4. robots.txt y sitemap.xml
    res_robots = client.get("/robots.txt")
    assert res_robots.status_code == 200
    texto_robots = res_robots.content.decode("utf-8")
    assert "Disallow: /gestion/" in texto_robots
    assert "Disallow: /pedidos/" in texto_robots

    res_sitemap = client.get("/sitemap.xml")
    assert res_sitemap.status_code == 200
    assert "argentina-x-messi-10" in res_sitemap.content.decode("utf-8")

    # 5. Detector automático de enlaces internos rotos (Requisito #16 Antes de lanzar)
    enlaces_internos = set(re.findall(r'href="(/[^"#?]*)"', html_inicio + html_detalle))
    for ruta in enlaces_internos:
        if ruta.startswith("/static/") or ruta.startswith("/media/"):
            continue
        respuesta_enlace = client.get(ruta)
        assert respuesta_enlace.status_code in {200, 302}, (
            f"Enlace roto detectado: '{ruta}' devolvió HTTP {respuesta_enlace.status_code}"
        )


@pytest.mark.django_db
def test_stock_negativo_bloqueado_en_variante() -> None:
    """Verifica que Variante rechace cualquier intento de guardar stock menor a 0.

    Qué hace:      Intenta crear una Variante con cantidad_stock=-1 y verifica que lance ValidationError.
    Va hacia:      Garantiza la Invariante #1 del doc 04 (VAR_NCANTIDAD_STOCK >= 0).
    Depende de:    apps.catalogo.models.Variante.
    Cuándo usarla: En la suite de pruebas de la Fase 1.
    Si no opera:   Falla si el modelo permite stock negativo.
    """
    call_command("cargar_demo")
    producto = Producto.objects.first()
    assert producto is not None

    with pytest.raises(ValidationError):
        Variante.objects.create(
            producto=producto,
            talla="XXL",
            sku="EMU-NEG-XXL",
            cantidad_stock=-1,
        )


@pytest.mark.django_db
def test_limite_ocho_destacados_admin_y_rotacion_portada(client, admin_user) -> None:
    """Verifica que la vitrina muestre hasta 8 destacados (rotando en bloques de 4) y el admin bloquee el 9.º.

    Qué hace:      Marca los 8 productos demo como destacados, valida la portada con rotación 3s y prueba crear el 9.º.
    Va hacia:      Garantiza el tope de MAX_PRODUCTOS_DESTACADOS=8 y el mensaje claro en /gestion/ sin desmarcar otros.
    Depende de:    ProductoAdminForm, ProductoAdmin.get_form, vista_inicio_catalogo e inicio.html.
    Cuándo usarla: En la suite de pruebas de catálogo y usabilidad admin.
    Si no opera:   Falla si la portada corta en 4, falta el temporizador de 3000ms o deja guardar un 9.º destacado.
    """
    from django.contrib.admin.sites import AdminSite

    from apps.catalogo.admin import ProductoAdmin, ProductoAdminForm

    call_command("cargar_demo")
    Producto.objects.update(destacado=True)
    assert Producto.objects.filter(destacado=True).count() == 8

    # 1. En portada aparecen los 8 destacados con rotación cada 3000ms
    resp_web = client.get(reverse("catalogo:inicio"))
    assert resp_web.status_code == 200
    html_web = resp_web.content.decode("utf-8")
    assert "(8)" in html_web
    assert "3000" in html_web
    assert "Controles de destacados" in html_web

    # 2. En /gestion/ un 9.º producto sin destacar muestra aviso de límite alcanzado y bloquea guardarlo como destacado
    cat = Categoria.objects.first()
    noveno = Producto.objects.create(
        categoria=cat,
        nombre="Camiseta Novena Prueba",
        slug="camiseta-novena-prueba",
        sku="EMU-NOV09",
        precio_unidad=Decimal("55.00"),
        activo=True,
        destacado=False,
    )
    client.force_login(admin_user)
    resp_change = client.get(reverse("admin:catalogo_producto_change", args=[noveno.pk]))
    assert resp_change.status_code == 200
    assert "Límite alcanzado (8/8)" in resp_change.content.decode("utf-8")

    form_noveno = ProductoAdminForm(
        data={
            "categoria": cat.pk,
            "nombre": noveno.nombre,
            "slug": noveno.slug,
            "sku": noveno.sku,
            "descripcion": "",
            "marca": "",
            "precio_unidad": "55.00",
            "precio_anterior": "",
            "activo": True,
            "destacado": True,
        },
        instance=noveno,
    )
    assert not form_noveno.is_valid()
    assert "destacado" in form_noveno.errors
    assert "límite de 8" in form_noveno.errors["destacado"][0]

    # El 8.º ya existente sí puede editarse normalmente manteniendo destacado=True
    primero = Producto.objects.filter(destacado=True).first()
    admin_inst = ProductoAdmin(Producto, AdminSite())
    req = client.get(reverse("admin:catalogo_producto_change", args=[primero.pk])).wsgi_request
    form_octavo_cls = admin_inst.get_form(req, obj=primero, change=True)
    assert "8 de 8" in str(form_octavo_cls.base_fields["destacado"].help_text)


@pytest.mark.django_db
def test_vitrina_mas_vendidas_portada_periodos_y_fotos(client, monkeypatch) -> None:
    """Verifica el ranking real Hoy/Semana/Mes, deduplicación, respaldo y fotos reales en portada.

    Qué hace:      Prueba ventas nulas (respaldo), pedidos cancelados ignorados, ganadores distintos y duplicados.
    Va hacia:      Valida obtener_vitrina_mas_vendidas_portada() y la transición suave de 4000ms en inicio.html.
    Depende de:    Pedido, ItemPedido, cargar_demo y obtener_vitrina_mas_vendidas_portada().
    Cuándo usarla: En cada ejecución de pytest para validar la vitrina superior de portada.
    Si no opera:   Falla si repite camisetas, cuenta pedidos cancelados o muestra textos/fotos fijos ajenos.
    """
    from datetime import date, datetime

    from django.utils import timezone

    from apps.catalogo.selectores import obtener_vitrina_mas_vendidas_portada
    from apps.pedidos.models import EstadoPedido, ItemPedido, OrigenPedido, Pedido, TipoEntrega

    call_command("cargar_demo")

    fecha_fija = date(2026, 11, 20)
    monkeypatch.setattr(timezone, "localdate", lambda: fecha_fija)
    tz = timezone.get_current_timezone()

    def _crear_venta(
        *, codigo: str, prod_slug: str, estado: str, fecha_local: datetime, cantidad: int
    ) -> None:
        prod = Producto.objects.get(slug=prod_slug)
        var = prod.variantes.first()
        assert var is not None
        ped = Pedido.objects.create(
            codigo=codigo,
            origen=OrigenPedido.PRESENCIAL,
            tipo_entrega=TipoEntrega.RECOJO,
            estado=estado,
            subtotal=prod.precio_unidad * cantidad,
            costo_envio=Decimal("0.00"),
            total=prod.precio_unidad * cantidad,
        )
        aware_dt = timezone.make_aware(fecha_local, tz)
        Pedido.objects.filter(pk=ped.pk).update(fecha_creacion=aware_dt, fecha_pagado=aware_dt)
        ItemPedido.objects.create(
            pedido=ped,
            variante=var,
            nombre_producto=prod.nombre,
            sku=var.sku,
            talla=var.talla,
            color=var.color,
            precio_unidad=prod.precio_unidad,
            cantidad=cantidad,
            subtotal=prod.precio_unidad * cantidad,
        )

    # 1. Sin ventas confirmadas: solo pedidos NUEVO/CANCELADO -> usa 1 respaldo destacado honesto
    _crear_venta(
        codigo="EMU-CANCEL",
        prod_slug="camiseta-retro-negra-dorada-10",
        estado=EstadoPedido.CANCELADO,
        fecha_local=datetime(2026, 11, 20, 10, 0),
        cantidad=20,
    )
    _crear_venta(
        codigo="EMU-NUEVO",
        prod_slug="camiseta-retro-negra-dorada-10",
        estado=EstadoPedido.NUEVO,
        fecha_local=datetime(2026, 11, 20, 11, 0),
        cantidad=15,
    )
    respaldo = obtener_vitrina_mas_vendidas_portada(
        destacados=list(listar_productos_catalogo(solo_destacados=True)[:1])
    )
    assert len(respaldo) == 1
    assert respaldo[0]["es_respaldo"] is True
    assert respaldo[0]["etiqueta_badge"] == "⭐ Destacada Emuná Sport"
    assert "ESPALDA MESSI #10" not in client.get(reverse("catalogo:inicio")).content.decode("utf-8")

    # 2. Tres ganadores reales distintos: Hoy=Argentina (5 fotos), Semana=Brasil (1 foto), Mes=Negra&Oro (1 foto)
    _crear_venta(
        codigo="EMU-HOY-ARG",
        prod_slug="argentina-x-messi-10",
        estado=EstadoPedido.ENTREGADO,
        fecha_local=datetime(2026, 11, 20, 12, 0),
        cantidad=2,
    )
    _crear_venta(
        codigo="EMU-SEM-BRA",
        prod_slug="camiseta-brasil-verdeamarela-10",
        estado=EstadoPedido.PAGADO,
        fecha_local=datetime(2026, 11, 17, 15, 0),
        cantidad=5,
    )
    _crear_venta(
        codigo="EMU-MES-BLK",
        prod_slug="camiseta-retro-negra-dorada-10",
        estado=EstadoPedido.PAGADO,
        fecha_local=datetime(2026, 11, 5, 16, 0),
        cantidad=9,
    )

    vitrina = obtener_vitrina_mas_vendidas_portada()
    assert [v["etiqueta_pill"] for v in vitrina] == ["Hoy", "Semana", "Mes"]
    assert [v["producto"].slug for v in vitrina] == [
        "argentina-x-messi-10",
        "camiseta-brasil-verdeamarela-10",
        "camiseta-retro-negra-dorada-10",
    ]
    assert vitrina[0]["imagen_2"] is not None
    assert vitrina[1]["imagen_2"] is None

    html = client.get(reverse("catalogo:inicio")).content.decode("utf-8")
    assert "4000" in html
    assert "duration-500 ease-in-out" in html
    assert "🔥 Más vendida de hoy" in html
    assert "🔥 Más vendida de la semana" in html
    assert "🔥 Más vendida del mes" in html
    assert "argentina_2_detalle.webp" in html
    assert "max-w-[360px]" in html

    # 3. Sin duplicar camiseta: si Argentina también supera en Semana (6 uds hoy), fusiona Hoy y Semana
    _crear_venta(
        codigo="EMU-HOY-ARG2",
        prod_slug="argentina-x-messi-10",
        estado=EstadoPedido.PAGADO,
        fecha_local=datetime(2026, 11, 20, 14, 0),
        cantidad=4,
    )
    vitrina_fusionada = obtener_vitrina_mas_vendidas_portada()
    slugs_fusionados = [v["producto"].slug for v in vitrina_fusionada]
    assert len(slugs_fusionados) == len(set(slugs_fusionados)) == 2
    assert vitrina_fusionada[0]["etiqueta_pill"] == "Hoy · Semana"
    assert vitrina_fusionada[1]["etiqueta_pill"] == "Mes"


@pytest.mark.django_db(transaction=True)
def test_normalizacion_equipo_y_busqueda_ia_en_cache(django_assert_num_queries) -> None:
    """Verifica Equipo normalizado, filtro por alias/sinónimos e invalidación automática de caché IA.

    Qué hace:      Crea Equipo Portugal con alias 'cr7', consulta caché IA con 0 SQL tras calentar y
                   verifica invalidación automática al agotarse la variante vía transaction.on_commit.
    Va hacia:      Garantiza velocidad constante sin golpear CPU en PostgreSQL para futura IA Gemini.
    Depende de:    Equipo, Producto, Variante, signals.py y selectores.buscar_productos_para_ia().
    Cuándo usarla: En la suite de pruebas tras normalización e índices de catálogo.
    Si no opera:   Falla si requiere queries repetidas al consultar IA o no refresca stock agotado.
    """
    cat = Categoria.objects.create(nombre="Selecciones Mundial", slug="selecciones-mundial")
    eq_portugal = Equipo.objects.create(
        nombre="Portugal",
        slug="portugal",
        tipo=TipoEquipo.SELECCION,
        alias_busqueda="cr7, cristiano, lusa",
    )
    prod = Producto.objects.create(
        categoria=cat,
        equipo=eq_portugal,
        equipacion=TipoEquipacion.LOCAL,
        temporada="2026-2027",
        palabras_clave="euro, seleccion europea, granate",
        nombre="Portugal Local – Edición Jugador",
        slug="portugal-local-2026",
        sku="EMU-POR26",
        precio_unidad=Decimal("59.00"),
        activo=True,
    )
    var_m = Variante.objects.create(
        producto=prod,
        talla="M",
        sku="EMU-POR26-M",
        cantidad_stock=4,
        activa=True,
    )

    # Filtro ORM normalizado por equipo_slug y alias
    assert listar_productos_catalogo(equipo_slug="portugal").count() == 1
    assert listar_productos_catalogo(busqueda="cr7").count() == 1

    # Primera consulta IA calienta caché; segunda consulta debe ejecutar exactamente 0 queries SQL
    res_1 = buscar_productos_para_ia("Hola, ¿tienen camiseta de CR7 en talla M?")
    assert len(res_1) == 1
    assert res_1[0]["equipo"] == "Portugal"
    assert res_1[0]["tallas_disponibles"] == ["M"]

    with django_assert_num_queries(0):
        res_2 = buscar_productos_para_ia("tienen portugal talla m?")
    assert len(res_2) == 1
    assert res_2[0]["sku"] == "EMU-POR26"

    # Al agotarse el stock, signals.py (on_commit) invalida la caché y deja de ofrecerlo
    var_m.cantidad_stock = 0
    var_m.save()
    res_agotado = buscar_productos_para_ia("tienen portugal?")
    assert res_agotado == []
