"""Selectores de lectura de la aplicación núcleo (ConfiguracionTienda y MetodoPago)."""
from django.db.models import QuerySet

from .models import ConfiguracionTienda, MetodoPago


def obtener_configuracion_tienda() -> ConfiguracionTienda:
    """Obtiene el registro único de configuración de la tienda o lo crea con valores base.

    Qué hace:      Consulta la primera fila de TBL_RCONFIGURACION_TIENDA o crea la fila inicial.
    Va hacia:      Retorna una instancia válida de ConfiguracionTienda.
    Depende de:    apps.nucleo.models.ConfiguracionTienda.
    Cuándo usarla: En context processors, vistas públicas, servicios de alertas y API.
    Si no opera:   Si la tabla aún no tiene registros, crea y devuelve la configuración por defecto.
    """
    configuracion = ConfiguracionTienda.objects.first()
    if configuracion is None:
        configuracion = ConfiguracionTienda.objects.create(
            id=1,
            nombre="Emuná Sport",
            numero_whatsapp="999888777",
            texto_pie="Emuná Sport – Estilo deportivo. Envíos a todo el Perú por Shalom y Olva.",
            umbral_stock_bajo=3,
            mostrar_marcas=False,
            dias_sin_ventas=30,
            horas_pedido_pendiente=24,
        )
    return configuracion


def listar_metodos_pago_activos() -> QuerySet[MetodoPago]:
    """Devuelve los métodos de pago activos ordenados por su prioridad de aparición.

    Qué hace:      Filtra TBL_RMETODO_PAGO con activo=True ordenando por MPA_NORDEN.
    Va hacia:      Retorna un QuerySet de instancias MetodoPago.
    Depende de:    apps.nucleo.models.MetodoPago.
    Cuándo usarla: En la pantalla de pedido cotizado (pago con Yape) y en el panel de Richard.
    Si no opera:   Retorna un QuerySet vacío si ningún método está activo.
    """
    return MetodoPago.objects.filter(activo=True).order_by("orden", "id")
