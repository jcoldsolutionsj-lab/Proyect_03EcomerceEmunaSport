"""Pruebas unitarias de la Fase 0: app núcleo, blindaje anti-hacking y permisos del grupo Dueño."""
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.nucleo.models import ConfiguracionTienda, MetodoPago, TipoMetodoPago
from apps.nucleo.selectores import listar_metodos_pago_activos, obtener_configuracion_tienda
from apps.nucleo.servicios import (
    NOMBRE_GRUPO_DUENO,
    actualizar_configuracion_tienda,
    asignar_usuario_a_grupo_dueno,
)
from apps.nucleo.validadores import (
    limpiar_texto_seguro,
    validar_dni_peruano,
    validar_telefono_peruano,
)


@pytest.mark.django_db
def test_configuracion_tienda_es_registro_unico() -> None:
    """Comprueba que ConfiguracionTienda cree un único registro y bloquee duplicados.

    Qué hace:      Obtiene la configuración por defecto e intenta crear un segundo registro.
    Va hacia:      Valida la invariante de registro único en TBL_RCONFIGURACION_TIENDA.
    Depende de:    obtener_configuracion_tienda() y ConfiguracionTienda.save().
    Cuándo usarla: En la suite de pruebas de la Fase 0.
    Si no opera:   Falla si permite más de una fila en TBL_RCONFIGURACION_TIENDA.
    """
    config = obtener_configuracion_tienda()
    assert config.pk == 1
    assert config.nombre == "Emuná Sport"
    assert config.mostrar_marcas is False

    actualizada = actualizar_configuracion_tienda(
        numero_whatsapp="987654321",
        umbral_stock_bajo=5,
    )
    assert actualizada.pk == 1
    assert actualizada.numero_whatsapp == "987654321"
    assert actualizada.umbral_stock_bajo == 5

    with pytest.raises(ValidationError):
        duplicada = ConfiguracionTienda(nombre="Otra Tienda", numero_whatsapp="912345678")
        duplicada.save()


@pytest.mark.django_db
def test_metodo_pago_yape_exige_titular_y_numero() -> None:
    """Verifica que activar Yape sin titular o sin número lance ValidationError.

    Qué hace:      Intenta guardar un MetodoPago YAPE activo incompleto y luego uno completo.
    Va hacia:      Valida las reglas de negocio de TBL_RMETODO_PAGO.
    Depende de:    MetodoPago y listar_metodos_pago_activos().
    Cuándo usarla: En las pruebas de la Fase 0.
    Si no opera:   Falla si permite activar Yape sin titular ni número copiable.
    """
    with pytest.raises(ValidationError):
        MetodoPago.objects.create(
            tipo=TipoMetodoPago.YAPE,
            titular="",
            numero_cuenta="",
            activo=True,
        )

    yape = MetodoPago.objects.create(
        tipo=TipoMetodoPago.YAPE,
        titular="Richard Emuná",
        numero_cuenta="987654321",
        activo=True,
        orden=1,
    )
    efectivo = MetodoPago.objects.create(
        tipo=TipoMetodoPago.EFECTIVO,
        activo=True,
        orden=2,
    )
    activos = list(listar_metodos_pago_activos())
    assert activos == [yape, efectivo]


def test_sanitizacion_anti_xss_y_validadores_peruanos() -> None:
    """Comprueba que limpiar_texto_seguro elimine scripts y que DNI/celular validen formato.

    Qué hace:      Pasa payloads con <script> y formatos inválidos a los validadores del núcleo.
    Va hacia:      Asegura el cumplimiento del Pilar 5 Anti-Hacking (sanitización de inputs).
    Depende de:    limpiar_texto_seguro, validar_dni_peruano y validar_telefono_peruano.
    Cuándo usarla: En cada ejecución de pytest.
    Si no opera:   Falla si una etiqueta HTML sobrevive o si acepta un DNI/celular mal formado.
    """
    texto_sucio = "  <script>alert('hack')</script>  Estación   Central   <b>Lima</b>  "
    assert limpiar_texto_seguro(texto_sucio) == "alert('hack') Estación Central Lima"

    assert validar_dni_peruano("45678912") == "45678912"
    with pytest.raises(ValidationError):
        validar_dni_peruano("1234567A")
    with pytest.raises(ValidationError):
        validar_dni_peruano("12345")

    assert validar_telefono_peruano("+51 987-654-321") == "987654321"
    with pytest.raises(ValidationError):
        validar_telefono_peruano("887654321")


@pytest.mark.django_db
def test_asignacion_grupo_dueno_para_richard(client) -> None:
    """Verifica que el grupo 'Dueño' se cree con permisos y que el endpoint de salud responda.

    Qué hace:      Crea al usuario 'richard', lo asigna al grupo 'Dueño' y consulta /salud/.
    Va hacia:      Valida la gestión de accesos (doc 07) y que el servidor levante sin errores.
    Depende de:    asignar_usuario_a_grupo_dueno() y vista_estado_salud.
    Cuándo usarla: En las pruebas de aceptación de la Fase 0.
    Si no opera:   Falla si el usuario no recibe is_staff=True o si /salud/ no devuelve 200.
    """
    User = get_user_model()
    richard = User.objects.create_user(username="richard", password="ClaveSeguraRichard2026!")
    grupo = asignar_usuario_a_grupo_dueno(usuario=richard)

    richard.refresh_from_db()
    assert richard.is_staff is True
    assert grupo.name == NOMBRE_GRUPO_DUENO
    assert richard.groups.filter(name=NOMBRE_GRUPO_DUENO).exists()

    respuesta = client.get(reverse("estado_salud"))
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"

    inicio = client.get(reverse("inicio_base"))
    assert inicio.status_code == 200
    assert "Emuná Sport" in inicio.content.decode("utf-8")


@pytest.mark.django_db
def test_comando_preparar_local_crea_usuarios_y_metodos() -> None:
    """Verifica que el comando preparar_local inicialice configuración, pagos y usuarios.

    Qué hace:      Ejecuta call_command('preparar_local') y comprueba jonathan, richard y Yape.
    Va hacia:      Asegura que Jonathan pueda levantar el entorno local con un solo comando.
    Depende de:    django.core.management.call_command y apps.nucleo.
    Cuándo usarla: En la suite de pruebas de la Fase 0.
    Si no opera:   Falla si no se crean los usuarios o los métodos de pago base.
    """
    from django.core.management import call_command

    call_command("preparar_local")
    User = get_user_model()
    assert User.objects.filter(username="jonathan", is_superuser=True).exists()
    assert User.objects.filter(username="richard", is_staff=True).exists()
    assert MetodoPago.objects.filter(tipo=TipoMetodoPago.YAPE, activo=True).exists()
