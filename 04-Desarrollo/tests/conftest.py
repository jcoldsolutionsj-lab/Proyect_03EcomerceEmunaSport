"""Fixtures globales de pytest para aislar archivos multimedia y caché por prueba."""
import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def aislar_media_y_cache_en_tests(settings, tmp_path) -> None:
    """Redirige MEDIA_ROOT a tmp_path y limpia la caché en cada prueba automatizada.

    Qué hace:      Asigna una carpeta temporal en tmp_path a settings.MEDIA_ROOT y limpia cache.
    Va hacia:      Evita acumular boletas o fotos de prueba dentro de 04-Desarrollo/media/.
    Depende de:    pytest fixture settings, tmp_path y django.core.cache.
    Cuándo usarla: Automáticamente (autouse=True) antes de cada test en la suite pytest.
    Si no opera:   Las pruebas de subida de boletas escribirían archivos reales en el disco del repo.
    """
    media_tmp = tmp_path / "media_test"
    media_tmp.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(media_tmp)
    cache.clear()
