"""Validadores y funciones de sanitización de entradas (Pilar 5 Anti-Hacking)."""
import re

from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

PATRON_DNI_PERU = re.compile(r"^\d{8}$")
PATRON_CELULAR_PERU = re.compile(r"^9\d{8}$")
PATRON_ESPACIOS_MULTIPLES = re.compile(r"\s+")


def limpiar_texto_seguro(valor: str | None, *, longitud_maxima: int = 200) -> str:
    """Limpia cadenas de texto eliminando etiquetas HTML/scripts y espacios redundantes.

    Qué hace:      Elimina etiquetas HTML (anti-XSS), normaliza espacios y recorta al largo máximo.
    Va hacia:      Devuelve un str limpio y seguro listo para guardarse en la base de datos.
    Depende de:    django.utils.html.strip_tags y expresiones regulares estándar.
    Cuándo usarla: En formularios, serializers y servicios antes de guardar cualquier texto libre.
    Si no opera:   Si recibe None devuelve cadena vacía ""; nunca permite etiquetas <script>.
    """
    if not valor:
        return ""
    sin_html = strip_tags(str(valor))
    normalizado = PATRON_ESPACIOS_MULTIPLES.sub(" ", sin_html).strip()
    return normalizado[:longitud_maxima]


def validar_dni_peruano(valor: str) -> str:
    """Verifica que el documento de identidad sea un DNI peruano válido de 8 dígitos.

    Qué hace:      Comprueba mediante expresión regular exacta que la cadena tenga 8 dígitos numéricos.
    Va hacia:      Devuelve el DNI limpio de 8 dígitos si es válido.
    Depende de:    PATRON_DNI_PERU y django.core.exceptions.ValidationError.
    Cuándo usarla: Al validar datos del cliente en envíos por agencia (Shalom / Olva).
    Si no opera:   Lanza ValidationError indicando que el DNI debe tener exactamente 8 dígitos.
    """
    limpio = (valor or "").strip()
    if not PATRON_DNI_PERU.match(limpio):
        raise ValidationError("El DNI debe contener exactamente 8 dígitos numéricos.")
    return limpio


def validar_telefono_peruano(valor: str) -> str:
    """Verifica que el teléfono sea un número celular peruano de 9 dígitos que empieza con 9.

    Qué hace:      Limpia espacios o prefijos +51 y valida el formato ^9\\d{8}$.
    Va hacia:      Devuelve el número celular normalizado de 9 dígitos.
    Depende de:    PATRON_CELULAR_PERU y django.core.exceptions.ValidationError.
    Cuándo usarla: Al validar el teléfono del cliente en pedidos web o configuración de WhatsApp.
    Si no opera:   Lanza ValidationError si el número no tiene 9 dígitos o no inicia con 9.
    """
    limpio = re.sub(r"[\s\-\(\)]", "", valor or "")
    if limpio.startswith("+51"):
        limpio = limpio[3:]
    elif limpio.startswith("51") and len(limpio) == 11:
        limpio = limpio[2:]
    if not PATRON_CELULAR_PERU.match(limpio):
        raise ValidationError(
            "El celular debe ser un número peruano válido de 9 dígitos que empiece con 9."
        )
    return limpio
