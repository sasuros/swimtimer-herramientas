"""Paleta visual y utilidades compartidas de tkinter."""

import sys
from pathlib import Path

NAVY = "#0a1628"
CARD = "#0f1f3a"
CREAM = "#E8E6DF"
MUTED = "#9f9e99"
GOLD = "#c9a84c"
TEAL = "#0F6E56"
RED = "#ef4444"
GREEN = "#22c55e"


def ruta_recurso(nombre: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / "recursos" / nombre


def centrar(ventana, ancho=700, alto=500):
    ventana.update_idletasks()
    x = max(0, (ventana.winfo_screenwidth() - ancho) // 2)
    y = max(0, (ventana.winfo_screenheight() - alto) // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

