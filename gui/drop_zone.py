"""Zona visual de seleccion por drag and drop o dialogo clasico."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from gui.estilos import BORDER, CARD, HELP, PRIMARY, SUCCESS, TEXT

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None


def extraer_ruta_drop(widget, data):
    """Extrae la primera ruta que tkinterdnd2 entrega, incluso con espacios."""
    try:
        valores = widget.tk.splitlist(data)
    except (tk.TclError, AttributeError):
        valores = [str(data).strip("{}")]
    return Path(valores[0]) if valores else None


class DropZone(tk.Frame):
    def __init__(self, parent, file_types, extensions, on_file_selected, help_text):
        super().__init__(parent, bg="white")
        self.file_types = file_types
        self.extensions = {item.lower() for item in extensions}
        self.on_file_selected = on_file_selected
        self.help_text = help_text
        self.path = None
        self.hover = False
        self.canvas = tk.Canvas(self, height=92, bg=CARD, highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill="x")
        self.help_label = tk.Label(self, text=help_text, bg="white", fg=HELP,
                                   anchor="w", justify="left", font=("Segoe UI", 9))
        self.help_label.pack(fill="x", pady=(7, 0))
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Button-1>", self._on_click)
        if DND_FILES and hasattr(self.canvas, "drop_target_register"):
            self.canvas.drop_target_register(DND_FILES)
            self.canvas.dnd_bind("<<Drop>>", self._on_drop)
            self.canvas.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.canvas.dnd_bind("<<DragLeave>>", self._on_drag_leave)

    def _draw(self, _event=None):
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 100)
        color = SUCCESS if self.path else PRIMARY if self.hover else BORDER
        fill = "#ECFDF5" if self.hover or self.path else CARD
        self.canvas.configure(bg=fill)
        self.canvas.create_rectangle(4, 4, width - 4, 88, outline=color, width=2,
                                     dash=() if self.path else (7, 5))
        if self.path:
            self.canvas.create_text(width / 2, 34, text="✓  Archivo seleccionado",
                                    fill=SUCCESS, font=("Segoe UI", 11, "bold"))
            self.canvas.create_text(width / 2, 60, text=self.path.name, fill=TEXT,
                                    font=("Segoe UI", 10), width=width - 40)
        else:
            self.canvas.create_text(width / 2, 32, text="▣  Arrastra tu archivo aquí",
                                    fill=TEXT, font=("Segoe UI", 11, "bold"))
            self.canvas.create_text(width / 2, 59, text="o haz clic para seleccionar",
                                    fill=HELP, font=("Segoe UI", 10))

    def _on_click(self, _event=None):
        selected = filedialog.askopenfilename(parent=self, title="Elegir archivo",
                                              filetypes=self.file_types)
        if selected:
            self.select(selected)

    def _on_drop(self, event):
        self.hover = False
        path = extraer_ruta_drop(self, event.data)
        if path:
            self.select(path)

    def _on_drag_enter(self, _event):
        self.hover = True; self._draw()

    def _on_drag_leave(self, _event):
        self.hover = False; self._draw()

    def select(self, path):
        path = Path(path)
        if not path.is_file() or path.suffix.lower() not in self.extensions:
            messagebox.showerror("Archivo no válido",
                                 f"Elige un archivo {', '.join(sorted(self.extensions))} válido.",
                                 parent=self)
            return
        self.path = path
        self._draw()
        self.on_file_selected(path)
