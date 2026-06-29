#!/usr/bin/env python3
"""Punto de entrada de la aplicacion de escritorio."""

import logging
import multiprocessing
import sys
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

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


def main():
    multiprocessing.freeze_support()
    configurar_log()
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
