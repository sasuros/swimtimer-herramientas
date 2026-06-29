"""Verificacion de requisitos locales para SWIMTIMER Herramientas."""

from __future__ import annotations

import platform
import struct
from typing import Optional


URL_DRIVER_ACCESS = "https://www.microsoft.com/en-us/download/details.aspx?id=54920"
Resultado = tuple[str, Optional[bool], str]


def verificar_sistema() -> tuple[list[Resultado], bool, bool]:
    """Detecta las capacidades disponibles sin bloquear el inicio de la app."""
    resultados: list[Resultado] = []
    resultados.append((
        "Sistema operativo", True, f"{platform.platform()} ({platform.machine()})"
    ))

    try:
        from access_parser import AccessParser  # noqa: F401
        resultados.append((
            "access-parser", True, "Disponible - Exportar funcionara sin drivers"
        ))
    except ImportError:
        resultados.append((
            "access-parser", False, "No disponible - Exportar podria fallar"
        ))

    access_drivers: list[str] = []
    try:
        import pyodbc

        access_drivers = [driver for driver in pyodbc.drivers() if "Access" in driver]
        if access_drivers:
            resultados.append(("Driver Access (ODBC)", True, access_drivers[0]))
        else:
            resultados.append((
                "Driver Access (ODBC)", False,
                f"NO ENCONTRADO - Importar no funcionara.\nDescargar de: {URL_DRIVER_ACCESS}",
            ))
    except ImportError:
        resultados.append(("Driver Access (ODBC)", False, "pyodbc no disponible"))

    inicializo_com = False
    try:
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        inicializo_com = True
        win32com.client.Dispatch("DAO.DBEngine.120")
        resultados.append(("Motor DAO (COM)", True, "DAO.DBEngine.120 disponible"))
    except Exception:
        resultados.append((
            "Motor DAO (COM)", None,
            "No disponible - se usara ODBC como alternativa",
        ))
    finally:
        if inicializo_com:
            pythoncom.CoUninitialize()

    python_bits = struct.calcsize("P") * 8
    if access_drivers:
        resultados.append((
            "Arquitectura", True, f"Python {python_bits}-bit / Driver compatible"
        ))
    else:
        resultados.append((
            "Arquitectura", None,
            f"Python {python_bits}-bit - instalar driver Access de {python_bits}-bit",
        ))

    puede_exportar = any(
        nombre == "access-parser" and ok is True for nombre, ok, _ in resultados
    )
    puede_importar = bool(access_drivers)
    return resultados, puede_exportar, puede_importar


def formatear_resultados(
    resultados: list[Resultado], puede_exportar: bool, puede_importar: bool
) -> str:
    """Construye el resumen comun para la ventana y la linea de comandos."""
    lineas = []
    for nombre, ok, detalle in resultados:
        icono = "✅" if ok else ("⚠️" if ok is None else "❌")
        lineas.append(f"{icono}  {nombre}\n    {detalle}")
    lineas.extend((
        "RESUMEN",
        f"{'✅' if puede_exportar else '❌'}  Exportar evento: "
        f"{'LISTO' if puede_exportar else 'NO DISPONIBLE'}",
        f"{'✅' if puede_importar else '❌'}  Importar inscripciones: "
        f"{'LISTO' if puede_importar else 'REQUIERE DRIVER ACCESS'}",
    ))
    return "\n\n".join(lineas)
