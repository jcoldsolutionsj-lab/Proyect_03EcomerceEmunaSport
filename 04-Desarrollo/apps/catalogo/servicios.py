"""Servicios de escritura del catálogo, compresión WebP y subida directa a Cloudflare R2."""
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config as BotoConfig
from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, ImageOps

from apps.nucleo.excepciones import EntradaInvalidaError

EXTENSIONES_PROHIBIDAS = {".svg", ".html", ".htm", ".php", ".exe", ".js", ".sh", ".bat"}
PESO_MAXIMO_BYTES = 10 * 1024 * 1024  # 10 MB de entrada (se comprime a ~80-150 KB WebP)


def obtener_cliente_r2() -> Any:
    """Crea y devuelve un cliente S3 (boto3) autenticado contra Cloudflare R2.

    Qué hace:      Instancia boto3.client('s3') apuntando al endpoint R2_ACCOUNT_ID con firma s3v4.
    Va hacia:      Retorna el cliente listo para put_object / head_bucket sobre R2_BUCKET_PUBLIC.
    Depende de:    boto3 y variables R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY en settings.
    Cuándo usarla: Desde subir_imagen_producto_a_r2() o utilidades de sincronización multimedia.
    Si no opera:   Lanza RuntimeError si faltan las credenciales R2 en el entorno.
    """
    account_id = getattr(settings, "R2_ACCOUNT_ID", "")
    access_key = getattr(settings, "R2_ACCESS_KEY_ID", "")
    secret_key = getattr(settings, "R2_SECRET_ACCESS_KEY", "")
    if not (account_id and access_key and secret_key):
        raise RuntimeError("Faltan credenciales R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY.")

    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=BotoConfig(signature_version="s3v4"),
    )


def validar_y_convertir_bytes_a_webp(*, contenido_bytes: bytes, nombre_archivo: str) -> bytes:
    """Valida una imagen en memoria y la convierte en 1 único WebP optimizado (máx. 800px).

    Qué hace:      Bloquea extensiones prohibidas/archivos >10 MB, verifica binario Pillow, corrige
                   orientación EXIF, redimensiona a <=800px de ancho y comprime a WebP (quality=80, method=6).
    Va hacia:      Retorna bytes listos de image/webp para subir a R2 o guardar en disco.
    Depende de:    PIL.Image, PIL.ImageOps, EXTENSIONES_PROHIBIDAS y PESO_MAXIMO_BYTES.
    Cuándo usarla: Desde admin al adjuntar fotos o desde scripts/servicios de carga multimedia.
    Si no opera:   Lanza ValidationError si el archivo está corrupto, excede 10 MB o es peligroso.
    """
    extension = Path(nombre_archivo or "").suffix.lower()
    if extension in EXTENSIONES_PROHIBIDAS:
        raise ValidationError("Formato de archivo no permitido por seguridad.")

    if not contenido_bytes or len(contenido_bytes) > PESO_MAXIMO_BYTES:
        raise ValidationError("La imagen está vacía o supera el tamaño máximo permitido de 10 MB.")

    try:
        with Image.open(BytesIO(contenido_bytes)) as img_verificacion:
            img_verificacion.verify()
    except Exception as exc:
        raise ValidationError("El archivo subido no es una imagen válida o está dañado.") from exc

    buf_webp = BytesIO()
    with Image.open(BytesIO(contenido_bytes)) as img:
        corregida = ImageOps.exif_transpose(img)
        rgb = corregida.convert("RGB")
        ancho, alto = rgb.size
        ancho_obj = min(ancho, 800)
        alto_obj = max(1, int(alto * (ancho_obj / ancho)))
        img_webp = rgb.resize((ancho_obj, alto_obj), Image.Resampling.LANCZOS)
        img_webp.save(buf_webp, "WEBP", quality=80, method=6)
    return buf_webp.getvalue()


def procesar_y_subir_archivo_imagen_producto(
    *,
    archivo_subido: Any,
    slug_producto: str,
    orden: int,
) -> str:
    """Optimiza un archivo adjuntado en el Admin a 1 WebP (~800px) y lo sube a R2 (o MEDIA_ROOT en local).

    Qué hace:      Lee bytes del archivo subido, los convierte a 1 WebP ligero y lo publica en R2 bajo webp/
                   cuando USE_S3_STORAGE está activo (o en MEDIA_ROOT/webp/ si corre en local sin R2).
    Va hacia:      Retorna la URL pública final (https://...r2.dev/webp/...webp o /media/webp/...webp).
    Depende de:    validar_y_convertir_bytes_a_webp(), obtener_cliente_r2() y settings.USE_S3_STORAGE.
    Cuándo usarla: Desde ProductoAdmin.save_formset() al adjuntar fotos desde /PanelAdministrativo/.
    Si no opera:   Propaga ValidationError si el archivo es inválido o error S3 si R2 falla.
    """
    archivo_subido.seek(0)
    bytes_origen = archivo_subido.read()
    bytes_webp = validar_y_convertir_bytes_a_webp(
        contenido_bytes=bytes_origen,
        nombre_archivo=getattr(archivo_subido, "name", "imagen.jpg"),
    )

    sufijo = uuid.uuid4().hex[:4]
    nombre_archivo = f"{slug_producto}_{orden}_{sufijo}.webp"
    clave_webp = f"webp/{nombre_archivo}"

    r2_configurado = bool(
        getattr(settings, "USE_S3_STORAGE", False)
        and getattr(settings, "R2_ACCOUNT_ID", "")
        and getattr(settings, "R2_ACCESS_KEY_ID", "")
        and getattr(settings, "R2_SECRET_ACCESS_KEY", "")
    )
    if r2_configurado:
        bucket = getattr(settings, "R2_BUCKET_PUBLIC", "emunasport-fotos")
        public_url = str(getattr(settings, "R2_PUBLIC_URL", "") or "").rstrip("/")
        s3 = obtener_cliente_r2()
        s3.put_object(
            Bucket=bucket,
            Key=clave_webp,
            Body=bytes_webp,
            ContentType="image/webp",
            CacheControl="public, max-age=31536000, immutable",
        )
        return f"{public_url}/{clave_webp}" if public_url else clave_webp

    destino_local = Path(settings.MEDIA_ROOT) / "webp"
    destino_local.mkdir(parents=True, exist_ok=True)
    (destino_local / nombre_archivo).write_bytes(bytes_webp)
    media_url = str(getattr(settings, "MEDIA_URL", "/media/") or "/media/").rstrip("/")
    return f"{media_url}/webp/{nombre_archivo}"


def subir_imagen_producto_a_r2(
    *,
    ruta_archivo_origen: Path,
    slug_producto: str,
    orden: int,
) -> tuple[str, str, str]:
    """Convierte una foto local a un único archivo WebP optimizado (800px) y lo sube a Cloudflare R2.

    Qué hace:      Valida la imagen, genera 1 archivo WebP ligero (~800px, q=80) en memoria y lo sube bajo webp/.
    Va hacia:      Retorna (url_webp_publica, url_webp_publica, url_webp_publica) evitando duplicados en R2.
    Depende de:    validar_y_convertir_bytes_a_webp(), obtener_cliente_r2() y settings.R2_BUCKET_PUBLIC / R2_PUBLIC_URL.
    Cuándo usarla: Al cargar o sincronizar fotografías reales del catálogo hacia Cloudflare R2.
    Si no opera:   Lanza ValidationError o EntradaInvalidaError si el archivo no existe o es inválido.
    """
    if not ruta_archivo_origen.exists():
        raise EntradaInvalidaError(f"No existe el archivo de imagen: {ruta_archivo_origen}")

    bytes_webp = validar_y_convertir_bytes_a_webp(
        contenido_bytes=ruta_archivo_origen.read_bytes(),
        nombre_archivo=ruta_archivo_origen.name,
    )

    bucket = getattr(settings, "R2_BUCKET_PUBLIC", "emunasport-fotos")
    public_url = str(getattr(settings, "R2_PUBLIC_URL", "") or "").rstrip("/")
    clave_webp = f"webp/{slug_producto}_{orden}.webp"

    s3 = obtener_cliente_r2()
    s3.put_object(
        Bucket=bucket,
        Key=clave_webp,
        Body=bytes_webp,
        ContentType="image/webp",
        CacheControl="public, max-age=31536000, immutable",
    )

    url_webp = f"{public_url}/{clave_webp}" if public_url else clave_webp
    return url_webp, url_webp, url_webp


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
