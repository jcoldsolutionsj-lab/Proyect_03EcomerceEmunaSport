"""Rutas públicas de la aplicación pedidos (Carrito HTMX, Checkout, Detalle por código y PDF)."""
from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("carrito/", views.vista_carrito, name="ver_carrito"),
    path("carrito/resumen-json/", views.vista_api_carrito_resumen, name="api_carrito_resumen"),
    path("carrito/agregar/", views.vista_agregar_item_carrito, name="agregar_al_carrito"),
    path(
        "carrito/eliminar/<int:variante_id>/",
        views.vista_eliminar_item_carrito,
        name="eliminar_del_carrito",
    ),
    path("pedidos/checkout/", views.vista_checkout, name="checkout"),
    path("pedidos/<str:codigo>/", views.vista_detalle_pedido_publico, name="detalle_pedido"),
    path("pedidos/<str:codigo>/estado-json/", views.vista_estado_pedido_json, name="estado_pedido_json"),
    path("pedidos/<str:codigo>/pdf/", views.vista_descargar_pdf_pedido, name="descargar_pdf_pedido"),
    path(
        "pedidos/envio/<int:envio_id>/boleta/",
        views.vista_ver_boleta_privada,
        name="ver_boleta_privada",
    ),
]
