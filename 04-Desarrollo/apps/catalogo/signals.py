"""Señales de invalidación de caché del catálogo para mantener consistencia en lectura y chat IA."""
from typing import Any

from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Categoria, Equipo, MovimientoStock, Producto, ReglaPrecio, Variante

CLAVE_CACHE_CATALOGO_IA = "emuna_catalogo_ia_compacto_v1"


def invalidar_cache_catalogo_ia() -> None:
    """Invalida la instantánea compacta del catálogo tras confirmarse la transacción en BD.

    Qué hace:      Programa la limpieza de CLAVE_CACHE_CATALOGO_IA en transaction.on_commit().
    Va hacia:      Evita lecturas obsoletas sin golpear el CPU de PostgreSQL entre cambios.
    Depende de:    django.core.cache y django.db.transaction.on_commit.
    Cuándo usarla: Desde señales post_save/post_delete o servicios de catálogo e inventario.
    Si no opera:   Si el caché aún no existía, cache.delete() finaliza de forma segura sin error.
    """
    transaction.on_commit(lambda: cache.delete(CLAVE_CACHE_CATALOGO_IA))


@receiver(post_save, sender=Categoria)
@receiver(post_delete, sender=Categoria)
@receiver(post_save, sender=Equipo)
@receiver(post_delete, sender=Equipo)
@receiver(post_save, sender=Producto)
@receiver(post_delete, sender=Producto)
@receiver(post_save, sender=Variante)
@receiver(post_delete, sender=Variante)
@receiver(post_save, sender=ReglaPrecio)
@receiver(post_delete, sender=ReglaPrecio)
@receiver(post_save, sender=MovimientoStock)
def _al_cambiar_catalogo_o_stock(sender: Any, **kwargs: Any) -> None:
    """Escucha cambios en catálogo o movimientos de stock para refrescar la caché IA.

    Qué hace:      Dispara invalidar_cache_catalogo_ia() cuando cambia un modelo del catálogo.
    Va hacia:      Mantiene sincronizados los precios, equipos y tallas con stock real.
    Depende de:    invalidar_cache_catalogo_ia() y señales Django.
    Cuándo usarla: Conectada automáticamente en CatalogoConfig.ready().
    Si no opera:   No afecta la escritura en base de datos ni lanza excepciones.
    """
    invalidar_cache_catalogo_ia()
