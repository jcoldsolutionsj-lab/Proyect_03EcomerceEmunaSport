#!/usr/bin/env python
"""Utilidad de línea de comandos de Django para tareas administrativas de Emuná Sport."""
import os
import sys


def ejecutar_cli() -> None:
    """Ejecuta los comandos administrativos de Django configurando el entorno por defecto.

    Qué hace:      Inicializa DJANGO_SETTINGS_MODULE y delega la ejecución a Django.
    Va hacia:      Comandos del framework (runserver, migrate, test, cargar_demo).
    Depende de:    config.settings.local y django.core.management.
    Cuándo usarla: Al ejecutar python manage.py <comando> desde la terminal.
    Si no opera:   Lanza ImportError si Django no está instalado en el entorno activo.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Verifica que esté instalado en el entorno Python activo."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    ejecutar_cli()
