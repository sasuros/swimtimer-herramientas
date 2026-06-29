#!/usr/bin/env python3
"""Punto de entrada de la aplicacion de escritorio."""

import logging
import multiprocessing
import sys
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from core.verificar_sistema import formatear_resultados, verificar_sistema
from gui.app import SwimtimerApp

try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    TkinterDnD = None


def carpeta_aplicacion():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def configurar_log():
    logging.basicConfig(
        filename=carpeta_aplicacion() / "swimtimer_herramientas.log",
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
    )


def preparar_consola_verificacion():
    """Conecta stdout al CMD padre cuando el ejecutable fue creado con --windowed."""
    try:
        if sys.platform == "win32":
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            if getattr(sys, "frozen", False):
                if not ctypes.windll.kernel32.AttachConsole(-1):
                    ctypes.windll.kernel32.AllocConsole()
                sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
                sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (OSError, AttributeError):
        pass


def ejecutar_verificacion_cli():
    preparar_consola_verificacion()
    resultados, puede_exportar, puede_importar = verificar_sistema()
    print("VERIFICACION DEL SISTEMA\n")
    print(formatear_resultados(resultados, puede_exportar, puede_importar))
    return 0


def main():
    multiprocessing.freeze_support()
    configurar_log()
    if "--verificar" in sys.argv:
        return ejecutar_verificacion_cli()
    try:
        root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()
        if TkinterDnD is None:
            logging.warning("tkinterdnd2 no está disponible; se usará selección por click")
        SwimtimerApp(root)
        root.mainloop()
        return 0
    except Exception as exc:
        logging.error("Error inesperado:\n%s", traceback.format_exc())
        try:
            ventana = tk.Tk(); ventana.withdraw()
            messagebox.showerror("Error inesperado", f"La aplicacion no pudo iniciar.\n\n{exc}")
            ventana.destroy()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
