"""Rutas URL internas de la aplicación tablero (/gestion/tablero/)."""
from django.urls import path

from .views import (
    vista_exportar_alertas_stock_csv,
    vista_exportar_ventas_csv,
    vista_resumen_tablero,
)

app_name = "tablero"

urlpatterns = [
    path("", vista_resumen_tablero, name="resumen"),
    path("exportar-ventas.csv", vista_exportar_ventas_csv, name="exportar_ventas_csv"),
    path("exportar-stock.csv", vista_exportar_alertas_stock_csv, name="exportar_stock_csv"),
]
