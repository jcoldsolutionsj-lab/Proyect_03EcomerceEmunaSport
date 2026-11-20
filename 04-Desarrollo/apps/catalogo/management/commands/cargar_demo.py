"""Comando cargar_demo para poblar el catálogo con Argentina x Messi y camisetas de ejemplo."""
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogo.models import (
    Categoria,
    Equipo,
    ImagenProducto,
    Producto,
    ReglaPrecio,
    TipoEquipacion,
    TipoEquipo,
    Variante,
)


class Command(BaseCommand):
    """Carga categorías, la camiseta real Argentina x Messi (5 fotos WebP) y productos de demostración."""

    help = "Carga el catálogo inicial de demostración (8 productos con tallas S, M, L, XL y precios por mayor)."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        """Ejecuta la carga transaccional de categorías, productos, fotos WebP, tallas y reglas por mayor.

        Qué hace:      Ejecuta preparar_local y crea 4 categorías y 8 productos con sus variantes y fotos.
        Va hacia:      Tablas TBL_RCATEGORIA, TBL_RPRODUCTO, TBL_RIMAGEN_PRODUCTO, TBL_RVARIANTE y TBL_RREGLA_PRECIO.
        Depende de:    Modelos de apps.catalogo y recursos en 03-Diseno-Tecnico/assets/productos-demo/.
        Cuándo usarla: Al ejecutar python 04-Desarrollo/manage.py cargar_demo en local o demo.
        Si no opera:   Revierte toda la transacción si algún modelo incumple una validación.
        """
        call_command("preparar_local")

        datos_categorias = [
            ("Selecciones", "selecciones", 1),
            ("Edición Jugador", "edicion-jugador", 2),
            ("Clubes Internacionales", "clubes-internacionales", 3),
            ("Entrenamiento Emuná", "entrenamiento-emuna", 4),
        ]
        mapa_categorias: dict[str, Categoria] = {}
        for nombre, slug, orden in datos_categorias:
            cat, _ = Categoria.objects.update_or_create(
                slug=slug,
                defaults={"nombre": nombre, "orden": orden, "activa": True},
            )
            mapa_categorias[slug] = cat

        # Resolver carpeta demo disponible (prioriza ARGENTINA 2026 - 2027 si ya fue reorganizada)
        assets_prod = Path(settings.REPO_DIR) / "03-Diseno-Tecnico" / "assets" / "productos-demo"
        carpeta_arg = (
            "ARGENTINA 2026 - 2027"
            if (assets_prod / "ARGENTINA 2026 - 2027").exists()
            else "argentina-messi"
        )
        prefijo_orig = (
            f"productos-demo/{carpeta_arg}"
            if carpeta_arg == "ARGENTINA 2026 - 2027"
            else "productos-demo/argentina-messi/originales"
        )

        # Equipos / colecciones normalizados para filtros rápidos y futura IA
        datos_equipos = [
            ("Argentina", "argentina", TipoEquipo.SELECCION, "albiceleste, messi, escaloneta, campeon", 1),
            ("Perú", "peru", TipoEquipo.SELECCION, "blanquiroja, seleccion peruana, bicolor", 2),
            ("Brasil", "brasil", TipoEquipo.SELECCION, "verdeamarela, canarinha, pentacampeon", 3),
            ("Clubes Europeos", "clubes-europeos", TipoEquipo.CLUB, "europa, gala, nocturna, real, paris", 4),
            ("Emuná Sport", "emuna-sport", TipoEquipo.ORIGINAL, "emuna, rayo, neon, entrenamiento", 5),
        ]
        mapa_equipos: dict[str, Equipo] = {}
        for nombre_eq, slug_eq, tipo_eq, alias_eq, orden_eq in datos_equipos:
            eq, _ = Equipo.objects.update_or_create(
                slug=slug_eq,
                defaults={
                    "nombre": nombre_eq,
                    "tipo": tipo_eq,
                    "alias_busqueda": alias_eq,
                    "orden": orden_eq,
                    "activo": True,
                },
            )
            mapa_equipos[slug_eq] = eq

        # 1. Producto Estrella Real: ARGENTINA X MESSI 🇦🇷 (con las 5 fotos WebP reales)
        argentina, _ = Producto.objects.update_or_create(
            slug="argentina-x-messi-10",
            defaults={
                "categoria": mapa_categorias["selecciones"],
                "equipo": mapa_equipos["argentina"],
                "equipacion": TipoEquipacion.LOCAL,
                "temporada": "2026-2027",
                "palabras_clave": "argentina, messi, 10, tres estrellas, jugador",
                "nombre": "ARGENTINA X MESSI #10 – Edición Campeón 3 Estrellas",
                "sku": "EMU-ARG10",
                "descripcion": (
                    "Camiseta Argentina x Messi #10 versión jugador con tejido técnico "
                    "microperforado transpirable, escudo bordado de 3 estrellas, parche dorado "
                    "de Campeón del Mundo y estampado oficial MESSI 10 en pecho y espalda."
                ),
                "precio_unidad": Decimal("55.00"),
                "precio_anterior": Decimal("69.90"),
                "activo": True,
                "destacado": True,
            },
        )

        textos_alt_argentina = [
            "Camiseta Argentina x Messi #10 vista frontal completa en colgador",
            "Camiseta Argentina x Messi #10 vista lateral derecha con parche en manga",
            "Camiseta Argentina x Messi #10 vista tres cuartos mostrando escudo 3 estrellas",
            "Acercamiento de textura microperforada y escudo dorado Argentina x Messi #10",
            "Vista de espalda con dorsal oficial MESSI 10 microperforado",
        ]
        for idx in range(1, 6):
            ruta_webp_arg = (
                f"productos-demo/{carpeta_arg}/webp/argentina_{idx}.webp"
                if carpeta_arg == "ARGENTINA 2026 - 2027"
                else f"productos-demo/{carpeta_arg}/webp/argentina_{idx}_detalle.webp"
            )
            ImagenProducto.objects.update_or_create(
                producto=argentina,
                orden=idx,
                defaults={
                    "ruta_original": f"{prefijo_orig}/argentina_{idx}.jpg",
                    "ruta_miniatura": ruta_webp_arg,
                    "ruta_detalle": ruta_webp_arg,
                    "texto_alternativo": textos_alt_argentina[idx - 1],
                    "es_principal": idx == 1,
                },
            )

        tallas_argentina = [("S", 5), ("M", 8), ("L", 6), ("XL", 2)]
        for talla, stock in tallas_argentina:
            Variante.objects.update_or_create(
                producto=argentina,
                talla=talla,
                color="Albiceleste",
                modelo="Versión Jugador",
                defaults={
                    "sku": f"EMU-ARG10-{talla}",
                    "cantidad_stock": stock,
                    "umbral_stock_bajo": 3,
                    "activa": True,
                },
            )

        ReglaPrecio.objects.update_or_create(
            producto=argentina,
            cantidad_minima=3,
            defaults={"precio_unidad": Decimal("50.00")},
        )
        ReglaPrecio.objects.update_or_create(
            producto=argentina,
            cantidad_minima=6,
            defaults={"precio_unidad": Decimal("45.00")},
        )

        # 2. Productos adicionales del catálogo para completar las 8 tarjetas de demostración
        otros_productos = [
            {
                "slug": "camiseta-emuna-verde-neon-pro",
                "categoria": "entrenamiento-emuna",
                "nombre": "Camiseta Emuná Sport Verde Neón – Edición Rayo",
                "sku": "EMU-NEO01",
                "descripcion": "Diseño oficial Emuná Sport en verde neón y negro con tela dry-fit ultraligera para entrenamiento de alto rendimiento.",
                "precio_unidad": Decimal("49.00"),
                "precio_anterior": Decimal("65.00"),
                "destacado": True,
                "foto_orden": 2,
                "tallas": [("S", 6), ("M", 10), ("L", 7), ("XL", 4)],
            },
            {
                "slug": "camiseta-blanca-dorado-edicion-real",
                "categoria": "clubes-internacionales",
                "nombre": "Camiseta Blanca & Dorado – Edición Gala Europea",
                "sku": "EMU-GAL02",
                "descripcion": "Acabado blanco puro con detalles en dorado metálico en hombros y cuello. Corte atlético versión jugador.",
                "precio_unidad": Decimal("55.00"),
                "precio_anterior": Decimal("69.90"),
                "destacado": True,
                "foto_orden": 3,
                "tallas": [("S", 4), ("M", 7), ("L", 5), ("XL", 3)],
            },
            {
                "slug": "camiseta-paris-nocturna-azul",
                "categoria": "clubes-internacionales",
                "nombre": "Camiseta Azul Nocturno Franja Central – Edición Cancha",
                "sku": "EMU-PAR03",
                "descripcion": "Azul marino profundo con franja central roja y blanca. Ideal para partidos nocturnos y uso urbano.",
                "precio_unidad": Decimal("55.00"),
                "precio_anterior": Decimal("69.90"),
                "destacado": True,
                "foto_orden": 1,
                "tallas": [("S", 3), ("M", 6), ("L", 2), ("XL", 0)],
            },
            {
                "slug": "camiseta-seleccion-peruana-bicolor",
                "categoria": "selecciones",
                "nombre": "Camiseta Perú Franja Roja Clásica – Edición Hincha",
                "sku": "EMU-PER04",
                "descripcion": "Camiseta blanca con la franja roja cruzada y detalles dorados. Tela fresca y costuras reforzadas.",
                "precio_unidad": Decimal("48.00"),
                "precio_anterior": Decimal("59.90"),
                "destacado": False,
                "foto_orden": 4,
                "tallas": [("S", 8), ("M", 12), ("L", 9), ("XL", 5)],
            },
            {
                "slug": "camiseta-emuna-azul-electrico",
                "categoria": "entrenamiento-emuna",
                "nombre": "Camiseta Emuná Azul Eléctrico & Fuego – Full Print",
                "sku": "EMU-AZU05",
                "descripcion": "Sublimado digital de alta definición con líneas aerodinámicas en azul eléctrico y rojo.",
                "precio_unidad": Decimal("49.00"),
                "precio_anterior": None,
                "destacado": False,
                "foto_orden": 5,
                "tallas": [("S", 5), ("M", 5), ("L", 4), ("XL", 2)],
            },
            {
                "slug": "camiseta-brasil-verdeamarela-10",
                "categoria": "selecciones",
                "nombre": "Camiseta Brasil Verdeamarela #10 – Edición Jugador",
                "sku": "EMU-BRA06",
                "descripcion": "Textura geométrica en relieve, cuello y puños con ribete verde y ajuste ergonómico.",
                "precio_unidad": Decimal("55.00"),
                "precio_anterior": Decimal("69.90"),
                "destacado": False,
                "foto_orden": 2,
                "tallas": [("S", 4), ("M", 6), ("L", 3), ("XL", 1)],
            },
            {
                "slug": "camiseta-retro-negra-dorada-10",
                "categoria": "edicion-jugador",
                "nombre": "Camiseta Negra & Oro #10 – Colección Especial",
                "sku": "EMU-BLK07",
                "descripcion": "Edición limitada en negro intenso con números y detalles en dorado cromado.",
                "precio_unidad": Decimal("58.00"),
                "precio_anterior": Decimal("75.00"),
                "destacado": False,
                "foto_orden": 3,
                "tallas": [("S", 2), ("M", 4), ("L", 3), ("XL", 2)],
            },
        ]

        for item in otros_productos:
            prod, _ = Producto.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "categoria": mapa_categorias[item["categoria"]],
                    "nombre": item["nombre"],
                    "sku": item["sku"],
                    "descripcion": item["descripcion"],
                    "precio_unidad": item["precio_unidad"],
                    "precio_anterior": item["precio_anterior"],
                    "activo": True,
                    "destacado": item["destacado"],
                },
            )
            idx_foto = item["foto_orden"]
            ruta_webp_item = (
                f"productos-demo/{carpeta_arg}/webp/argentina_{idx_foto}.webp"
                if carpeta_arg == "ARGENTINA 2026 - 2027"
                else f"productos-demo/{carpeta_arg}/webp/argentina_{idx_foto}_detalle.webp"
            )
            ImagenProducto.objects.update_or_create(
                producto=prod,
                orden=1,
                defaults={
                    "ruta_original": f"{prefijo_orig}/argentina_{idx_foto}.jpg",
                    "ruta_miniatura": ruta_webp_item,
                    "ruta_detalle": ruta_webp_item,
                    "texto_alternativo": f"{prod.nombre} – Vista principal",
                    "es_principal": True,
                },
            )
            for talla, stock in item["tallas"]:
                Variante.objects.update_or_create(
                    producto=prod,
                    talla=talla,
                    color="",
                    modelo="Estándar",
                    defaults={
                        "sku": f"{item['sku']}-{talla}",
                        "cantidad_stock": stock,
                        "umbral_stock_bajo": 3,
                        "activa": True,
                    },
                )
            ReglaPrecio.objects.update_or_create(
                producto=prod,
                cantidad_minima=3,
                defaults={"precio_unidad": item["precio_unidad"] - Decimal("5.00")},
            )
            ReglaPrecio.objects.update_or_create(
                producto=prod,
                cantidad_minima=6,
                defaults={"precio_unidad": item["precio_unidad"] - Decimal("10.00")},
            )

        self.stdout.write(
            self.style.SUCCESS(
                "[OK] Catalogo demo cargado: 4 categorias, 8 productos (incluyendo ARGENTINA X MESSI #10 con sus 5 fotos WebP) y tallas S, M, L, XL."
            )
        )
