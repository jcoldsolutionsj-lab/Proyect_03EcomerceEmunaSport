"""Comando para preparar el entorno local con configuración, métodos de pago y usuarios de prueba."""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.nucleo.models import MetodoPago, TipoMetodoPago
from apps.nucleo.selectores import obtener_configuracion_tienda
from apps.nucleo.servicios import asignar_usuario_a_grupo_dueno


class Command(BaseCommand):
    """Inicializa datos base de la Fase 0 para que Jonathan pueda probar el panel de inmediato."""

    help = "Crea ConfiguracionTienda, métodos de pago base y usuarios locales (jonathan y richard)."

    def handle(self, *args, **options) -> None:
        """Ejecuta la carga inicial de configuración y usuarios de desarrollo local.

        Qué hace:      Crea ConfiguracionTienda, Yape/Efectivo, superusuario 'jonathan' y dueño 'richard'.
        Va hacia:      Tablas TBL_RCONFIGURACION_TIENDA, TBL_RMETODO_PAGO, auth_user y auth_group.
        Depende de:    obtener_configuracion_tienda, MetodoPago y asignar_usuario_a_grupo_dueno.
        Cuándo usarla: Al ejecutar python 04-Desarrollo/manage.py preparar_local en desarrollo.
        Si no opera:   Muestra el error en consola si las migraciones aún no han sido aplicadas.
        """
        config = obtener_configuracion_tienda()
        self.stdout.write(self.style.SUCCESS(f"[OK] Configuracion lista: {config}"))

        MetodoPago.objects.update_or_create(
            tipo=TipoMetodoPago.YAPE,
            defaults={
                "titular": "Richard Ramos - Emuna Sport",
                "numero_cuenta": "999888777",
                "imagen_qr": "QR_yape_richardRamos.jpeg",
                "activo": True,
                "orden": 1,
            },
        )
        MetodoPago.objects.update_or_create(
            tipo=TipoMetodoPago.EFECTIVO,
            defaults={
                "titular": "Pago contraentrega en punto de encuentro (Lima)",
                "numero_cuenta": "",
                "activo": True,
                "orden": 2,
            },
        )
        self.stdout.write(self.style.SUCCESS("[OK] Metodos de pago base (YAPE y EFECTIVO) listos."))

        User = get_user_model()
        clave_local = os.environ.get("LOCAL_DEV_PASSWORD", "Emuna2026!")

        jonathan, creado_j = User.objects.get_or_create(
            username="jonathan",
            defaults={
                "first_name": "Jonathan",
                "last_name": "Vera",
                "email": "jonathan@emunasport.pe",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if not jonathan.first_name:
            jonathan.first_name = "Jonathan"
            jonathan.last_name = "Vera"
            jonathan.save(update_fields=["first_name", "last_name"])
        if creado_j:
            jonathan.set_password(clave_local)
            jonathan.save()

        richard, creado_r = User.objects.get_or_create(
            username="richard",
            defaults={
                "first_name": "Richard Alexander",
                "last_name": "Ramos Hinostroza",
                "email": "richard@emunasport.pe",
                "is_staff": True,
            },
        )
        if not richard.first_name:
            richard.first_name = "Richard Alexander"
            richard.last_name = "Ramos Hinostroza"
            richard.save(update_fields=["first_name", "last_name"])
        if creado_r:
            richard.set_password(clave_local)
            richard.save()
        asignar_usuario_a_grupo_dueno(usuario=richard)

        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] Usuarios locales listos -> Superusuario: 'jonathan' | Dueno: 'richard' "
                f"(Contrasena local: {clave_local})"
            )
        )
