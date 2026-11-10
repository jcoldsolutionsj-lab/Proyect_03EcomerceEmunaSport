"""Servicios de escritura y administración de roles de la aplicación núcleo."""
from django.contrib.auth.models import AbstractBaseUser, Group, Permission
from django.db import transaction

from .models import ConfiguracionTienda
from .selectores import obtener_configuracion_tienda

NOMBRE_GRUPO_DUENO = "Dueño"


@transaction.atomic
def actualizar_configuracion_tienda(
    *,
    nombre: str | None = None,
    numero_whatsapp: str | None = None,
    texto_pie: str | None = None,
    umbral_stock_bajo: int | None = None,
    mostrar_marcas: bool | None = None,
    dias_sin_ventas: int | None = None,
    horas_pedido_pendiente: int | None = None,
) -> ConfiguracionTienda:
    """Actualiza de forma atómica los ajustes generales de la tienda Emuná Sport.

    Qué hace:      Modifica los campos provistos del registro único y ejecuta save() con validación.
    Va hacia:      Actualiza la fila única en TBL_RCONFIGURACION_TIENDA y la retorna.
    Depende de:    obtener_configuracion_tienda() y validadores de ConfiguracionTienda.
    Cuándo usarla: Desde el panel administrativo, comandos de carga inicial o endpoint PATCH de API.
    Si no opera:   Lanza ValidationError y revierte la transacción si algún dato es inválido.
    """
    configuracion = obtener_configuracion_tienda()
    if nombre is not None:
        configuracion.nombre = nombre
    if numero_whatsapp is not None:
        configuracion.numero_whatsapp = numero_whatsapp
    if texto_pie is not None:
        configuracion.texto_pie = texto_pie
    if umbral_stock_bajo is not None:
        configuracion.umbral_stock_bajo = umbral_stock_bajo
    if mostrar_marcas is not None:
        configuracion.mostrar_marcas = mostrar_marcas
    if dias_sin_ventas is not None:
        configuracion.dias_sin_ventas = dias_sin_ventas
    if horas_pedido_pendiente is not None:
        configuracion.horas_pedido_pendiente = horas_pedido_pendiente
    configuracion.save()
    return configuracion


@transaction.atomic
def asegurar_grupo_dueno() -> Group:
    """Crea o actualiza el grupo operativo 'Dueño' (para Richard) con sus permisos de negocio.

    Qué hace:      Obtiene o crea el grupo 'Dueño' y le asigna permisos sobre las apps del negocio.
    Va hacia:      Tabla auth_group y auth_group_permissions de Django.
    Depende de:    django.contrib.auth.models.Group y Permission.
    Cuándo usarla: En migraciones de arranque, comando cargar_demo o pruebas de permisos.
    Si no opera:   Propaga DatabaseError si la base de datos no está migrada.
    """
    grupo, _ = Group.objects.get_or_create(name=NOMBRE_GRUPO_DUENO)
    apps_operativas = ["nucleo", "catalogo", "inventario", "pedidos", "envios", "tablero"]
    permisos = Permission.objects.filter(content_type__app_label__in=apps_operativas)
    grupo.permissions.set(permisos)
    return grupo


@transaction.atomic
def asignar_usuario_a_grupo_dueno(*, usuario: AbstractBaseUser) -> Group:
    """Habilita a un usuario como personal operativo y lo incorpora al grupo 'Dueño'.

    Qué hace:      Marca is_staff=True en el usuario y lo agrega al grupo 'Dueño'.
    Va hacia:      Modifica auth_user y la relación auth_user_groups.
    Depende de:    asegurar_grupo_dueno() y el modelo User de Django.
    Cuándo usarla: Al dar de alta la cuenta operativa de Richard.
    Si no opera:   Lanza ValueError si el usuario no está guardado previamente en la base de datos.
    """
    if not usuario.pk:
        raise ValueError("El usuario debe estar guardado antes de asignarle el grupo Dueño.")
    grupo = asegurar_grupo_dueno()
    if not getattr(usuario, "is_staff", False):
        usuario.is_staff = True  # type: ignore[attr-defined]
        usuario.save(update_fields=["is_staff"])
    usuario.groups.add(grupo)  # type: ignore[attr-defined]
    return grupo
