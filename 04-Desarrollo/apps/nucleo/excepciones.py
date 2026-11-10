"""Excepciones de dominio de Emuná Sport compartidas entre servicios, vistas y API."""


class ErrorDominioEmuna(Exception):
    """Excepción base para todas las reglas de negocio de Emuná Sport."""


class StockInsuficienteError(ErrorDominioEmuna):
    """Se lanza cuando se intenta vender o reservar más unidades que el stock disponible."""


class TransicionInvalidaError(ErrorDominioEmuna):
    """Se lanza cuando se intenta cambiar un pedido a un estado no permitido por el flujo."""


class DatosEnvioIncompletosError(ErrorDominioEmuna):
    """Se lanza cuando faltan datos obligatorios para una modalidad de entrega o despacho."""


class EntradaInvalidaError(ErrorDominioEmuna):
    """Se lanza cuando un dato ingresado no supera la sanitización o el formato permitido."""
