"""Rutas públicas del catálogo y páginas legales de Emuná Sport."""
from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.vista_inicio_catalogo, name="inicio"),
    path("productos/<slug:slug>/", views.vista_detalle_producto, name="detalle_producto"),
    path("aviso-legal/", views.vista_aviso_legal, name="aviso_legal"),
    path("privacidad/", views.vista_politica_privacidad, name="privacidad"),
    path("cookies/", views.vista_aviso_cookies, name="cookies"),
]
