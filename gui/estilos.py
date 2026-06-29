"""Sistema visual SWIMTIMER para tkinter."""

import sys
import tkinter as tk
from pathlib import Path

WHITE = "#FFFFFF"
CARD = "#F8F9FA"
HEADER = "#1B3A5C"
TITLE = "#2C3E50"
TEXT = "#374151"
HELP = "#059669"
PRIMARY = "#047857"
PRIMARY_HOVER = "#065F46"
SECONDARY = "#F3F4F6"
BORDER = "#D1D5DB"
SUCCESS = "#16A34A"
WARNING = "#D97706"
ERROR = "#DC2626"
MUTED = "#9CA3AF"


def ruta_recurso(nombre: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / "recursos" / nombre


def centrar(ventana, ancho=780, alto=700):
    ventana.update_idletasks()
    x = max(0, (ventana.winfo_screenwidth() - ancho) // 2)
    y = max(0, (ventana.winfo_screenheight() - alto) // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


def boton_primario(parent, texto, comando, **kwargs):
    deshabilitado = kwargs.get("state") == "disabled"
    return tk.Button(
        parent, text=texto, command=comando,
        bg=MUTED if deshabilitado else PRIMARY, fg=WHITE,
        activebackground=PRIMARY_HOVER, activeforeground=WHITE,
        disabledforeground=WHITE, relief="flat", cursor="hand2",
        font=("Segoe UI", 13, "bold"), padx=20, pady=14, **kwargs,
    )


def configurar_boton_primario(boton, habilitado):
    """Actualiza juntos el estado y color del CTA principal."""
    boton.config(
        state="normal" if habilitado else "disabled",
        bg=PRIMARY if habilitado else MUTED,
    )


def boton_secundario(parent, texto, comando, **kwargs):
    return tk.Button(
        parent, text=texto, command=comando, bg=SECONDARY, fg=TEXT,
        activebackground="#E5E7EB", activeforeground=TEXT,
        highlightbackground=BORDER, highlightthickness=1,
        relief="flat", cursor="hand2", font=("Segoe UI", 10, "bold"),
        padx=14, pady=8, **kwargs,
    )


def crear_seccion(parent, numero, titulo):
    frame = tk.LabelFrame(
        parent, text=f"  {numero}. {titulo}  ", bg=WHITE, fg=TITLE,
        font=("Segoe UI", 11, "bold"), bd=1, relief="solid",
        highlightbackground=BORDER, padx=16, pady=12,
    )
    frame.pack(fill="x", padx=28, pady=(0, 12))
    return frame


def ayuda(parent, texto):
    return tk.Label(
        parent, text=texto, bg=WHITE, fg=HELP, justify="left",
        anchor="w", font=("Segoe UI", 9), wraplength=680,
    )
