"""Servicios de escritura del catálogo y procesamiento seguro de imágenes a WebP."""
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image

from apps.nucleo.excepciones import EntradaInvalidaError

EXTENSIONES_PROHIBIDAS = {".svg", ".html", ".htm", ".php", ".exe", ".js", ".sh", ".bat"}
PESO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5 MB


def validar_y_generar_versiones_webp(
    *,
    ruta_archivo_origen: Path,
    slug_producto: str,
    orden: int,
    directorio_salida: Path | None = None,
) -> tuple[str, str]:
    """Valida una imagen con Pillow y genera sus versiones WebP de miniatura (400px) y detalle (900px).

    Qué hace:      Verifica integridad binaria (anti-payload), redimensiona y comprime a WebP (calidad 82).
    Va hacia:      Escribe dos archivos .webp en disco/media y retorna (ruta_miniatura, ruta_detalle).
    Depende de:    PIL.Image, settings.MEDIA_ROOT y límites de seguridad del Pilar 5 Anti-Hacking.
    Cuándo usarla: Al subir imágenes en el admin o al procesar semillas del catálogo.
    Si no opera:   Lanza EntradaInvalidaError o ValidationError si el archivo está corrupto o excede 5 MB.
    """
    if not ruta_archivo_origen.exists():
        raise EntradaInvalidaError(f"No existe el archivo de imagen: {ruta_archivo_origen}")

    if ruta_archivo_origen.suffix.lower() in EXTENSIONES_PROHIBIDAS:
        raise ValidationError("Formato de archivo no permitido por seguridad.")

    if ruta_archivo_origen.stat().st_size > PESO_MAXIMO_BYTES:
        raise ValidationError("La imagen supera el tamaño máximo permitido de 5 MB.")

    try:
        with Image.open(ruta_archivo_origen) as img_verificacion:
            img_verificacion.verify()
    except Exception as exc:
        raise ValidationError("El archivo subido no es una imagen válida o está dañado.") from exc

    carpeta_destino = directorio_salida or (Path(settings.MEDIA_ROOT) / "productos" / slug_producto)
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    nombre_miniatura = f"{slug_producto}_{orden}_miniatura.webp"
    nombre_detalle = f"{slug_producto}_{orden}_detalle.webp"
    ruta_fisica_min = carpeta_destino / nombre_miniatura
    ruta_fisica_det = carpeta_destino / nombre_detalle

    with Image.open(ruta_archivo_origen) as img:
        rgb = img.convert("RGB")
        ancho, alto = rgb.size

        alto_900 = max(1, int(alto * (900 / ancho)))
        img_900 = rgb.resize((900, alto_900), Image.Resampling.LANCZOS)
        img_900.save(ruta_fisica_det, "WEBP", quality=82)

        alto_400 = max(1, int(alto * (400 / ancho)))
        img_400 = rgb.resize((400, alto_400), Image.Resampling.LANCZOS)
        img_400.save(ruta_fisica_min, "WEBP", quality=80)

    rel_min = f"productos/{slug_producto}/{nombre_miniatura}"
    rel_det = f"productos/{slug_producto}/{nombre_detalle}"
    return rel_min, rel_det
