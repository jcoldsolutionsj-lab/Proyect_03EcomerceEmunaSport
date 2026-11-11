"""Pruebas unitarias, de integración, SEO y verificador de enlaces rotos de la Fase 1 (Catálogo)."""
import re
from decimal import Decimal
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse

from apps.catalogo.models import Categoria, Producto, Variante
from apps.catalogo.selectores import (
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
    origen_real = (
        Path(settings.REPO_DIR)
        / "03-Diseno-Tecnico/assets/productos-demo/argentina-messi/originales/argentina_1.jpg"
    )
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
    assert "logo-emuna-animado" in html_inicio
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
