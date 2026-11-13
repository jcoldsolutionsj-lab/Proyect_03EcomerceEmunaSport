"""Servicios de exportación segura de reportes del tablero operativo (CSV)."""
import csv
import io
from datetime import date
from typing import Any

from django.utils import timezone

from .selectores import listar_alertas_stock_bajo, listar_pedidos_ventas_para_csv

PREFIJOS_FORMULA_PELIGROSA = ("=", "+", "-", "@", "\t", "\r")


def _sanitizar_celda_csv(valor: Any) -> str:
    """Neutraliza inyección de fórmulas Excel/CSV en celdas generadas desde textos de usuario.

    Qué hace:      Antepone un apóstrofo si un texto arbitrario inicia con =, +, -, @, tab o CR.
    Va hacia:      Retorna cadena segura para escribir en csv.writer sin romper números positivos.
    Depende de:    PREFIJOS_FORMULA_PELIGROSA.
    Cuándo usarla: Antes de volcar nombres de clientes, productos o notas dentro de archivos CSV.
    Si no opera:   Retorna cadena vacía si valor es None.
    """
    if valor is None:
        return ""
    if isinstance(valor, (int, float)):
        return str(valor)
    texto = str(valor)
    if texto.startswith(PREFIJOS_FORMULA_PELIGROSA):
        return f"'{texto}"
    return texto


def generar_csv_ventas(
    desde: date | str | None = None,
    hasta: date | str | None = None,
    periodo: str | None = None,
) -> tuple[str, bytes]:
    """Genera un archivo CSV con BOM UTF-8 listando las ventas confirmadas del período.

    Qué hace:      Serializa pedidos confirmados (PAGADO/ENVIADO/ENTREGADO) sanitizando celdas.
    Va hacia:      Retorna (nombre_archivo, bytes_csv_utf8_sig) listo para descarga en Excel.
    Depende de:    listar_pedidos_ventas_para_csv y _sanitizar_celda_csv.
    Cuándo usarla: Cuando Richard pulsa 'Exportar Ventas (.csv)' desde /gestion/tablero/.
    Si no opera:   Genera el CSV solo con encabezados si no existen ventas en el rango dado.
    """
    pedidos, fecha_desde, fecha_hasta = listar_pedidos_ventas_para_csv(
        desde=desde, hasta=hasta, periodo=periodo
    )

    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(
        [
            "Código",
            "Fecha Venta",
            "Estado",
            "Canal / Origen",
            "Modalidad Entrega",
            "Cliente",
            "Celular",
            "Subtotal Camisetas (S/)",
            "Costo Envío (S/)",
            "Total Cobrado (S/)",
            "Prendas",
        ]
    )

    for ped in pedidos:
        fecha_ref = ped.fecha_pagado or ped.fecha_creacion
        fecha_str = timezone.localtime(fecha_ref).strftime("%Y-%m-%d %H:%M")
        prendas_str = " | ".join(
            f"{item.cantidad}x {item.nombre_producto} ({item.talla})" for item in ped.items.all()
        )
        escritor.writerow(
            [
                _sanitizar_celda_csv(ped.codigo),
                fecha_str,
                _sanitizar_celda_csv(ped.get_estado_display()),
                _sanitizar_celda_csv(ped.get_origen_display()),
                _sanitizar_celda_csv(ped.get_tipo_entrega_display()),
                _sanitizar_celda_csv(ped.cliente_nombre or "Cliente presencial"),
                _sanitizar_celda_csv(ped.cliente_telefono or ""),
                f"{ped.subtotal:.2f}",
                f"{(ped.costo_envio or 0):.2f}",
                f"{ped.total:.2f}",
                _sanitizar_celda_csv(prendas_str),
            ]
        )

    nombre_archivo = (
        f"ventas-emuna-sport-{fecha_desde.isoformat()}-a-{fecha_hasta.isoformat()}.csv"
    )
    return nombre_archivo, buffer.getvalue().encode("utf-8-sig")


def generar_csv_alertas_stock() -> tuple[str, bytes]:
    """Genera un archivo CSV con BOM UTF-8 de variantes agotadas o con stock bajo mínimo.

    Qué hace:      Lista variantes críticas con semáforo, stock actual, umbral y déficit sugerido.
    Va hacia:      Retorna (nombre_archivo, bytes_csv_utf8_sig) compatible con Microsoft Excel.
    Depende de:    listar_alertas_stock_bajo y _sanitizar_celda_csv.
    Cuándo usarla: Cuando Richard descarga la lista de reposición para taller desde el tablero.
    Si no opera:   Genera el CSV solo con encabezados si todas las tallas tienen stock óptimo.
    """
    alertas = listar_alertas_stock_bajo()
    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(
        [
            "Nivel Alerta",
            "Categoría",
            "Camiseta / Producto",
            "Talla",
            "Color",
            "SKU",
            "Stock Actual",
            "Umbral Mínimo",
            "Faltante Para Umbral",
        ]
    )

    for item in alertas:
        etiqueta_nivel = "ROJO - AGOTADO" if item["nivel"] == "ROJO" else "AMBAR - STOCK BAJO"
        escritor.writerow(
            [
                etiqueta_nivel,
                _sanitizar_celda_csv(item["categoria_nombre"]),
                _sanitizar_celda_csv(item["producto_nombre"]),
                _sanitizar_celda_csv(item["talla"]),
                _sanitizar_celda_csv(item["color"]),
                _sanitizar_celda_csv(item["sku"]),
                item["cantidad_stock"],
                item["umbral_efectivo"],
                item["deficit"],
            ]
        )

    fecha_hoy = timezone.localdate().isoformat()
    nombre_archivo = f"alertas-stock-emuna-sport-{fecha_hoy}.csv"
    return nombre_archivo, buffer.getvalue().encode("utf-8-sig")
