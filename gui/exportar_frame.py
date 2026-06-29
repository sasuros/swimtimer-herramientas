"""Pantalla MDB a config_evento.json."""

import logging
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from core.generar_config import generar_config, guardar_config, nombre_config_sugerido
from core.leer_mdb import leer_evento_mdb
from gui.drop_zone import DropZone
from gui.estilos import (
    BORDER, CARD, ERROR, HELP, MUTED, SUCCESS, TEXT, TITLE, WHITE,
    ayuda, boton_primario, boton_secundario, crear_seccion,
)

COURSE_LABELS = {"S": "Piscina corta (25m)", "L": "Piscina larga (50m)", "Y": "Piscina en yardas"}


class ExportarFrame(tk.Frame):
    def __init__(self, master, volver):
        super().__init__(master, bg=WHITE)
        self.datos = None
        self.ruta_mdb = self.output_path = None
        top = tk.Frame(self, bg=WHITE); top.pack(fill="x", padx=28, pady=(14, 6))
        boton_secundario(top, "← Volver", volver).pack(side="left")
        tk.Label(self, text="EXPORTAR EVENTO", bg=WHITE, fg=TITLE,
                 font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=28, pady=(4, 12))

        section1 = crear_seccion(self, 1, "Archivo de Meet Manager")
        self.drop = DropZone(
            section1, [("Archivos MDB", "*.mdb"), ("Todos", "*.*")], {".mdb"},
            self.seleccionar, "Selecciona el archivo .mdb del evento configurado en Meet Manager",
        )
        self.drop.pack(fill="x")

        self.section2 = crear_seccion(self, 2, "Evento encontrado")
        self.event_title = tk.Label(self.section2, text="Selecciona un archivo para ver el resumen.",
                                    bg=WHITE, fg=MUTED, font=("Segoe UI", 11))
        self.event_title.pack(anchor="w")
        self.event_meta = tk.Label(self.section2, text="", bg=WHITE, fg=TEXT,
                                   font=("Segoe UI", 10))
        self.event_meta.pack(anchor="w", pady=(3, 8))
        self.stats = tk.Frame(self.section2, bg=WHITE); self.stats.pack(fill="x")
        self.club_stat = self._stat(self.stats, "Clubes")
        self.event_stat = self._stat(self.stats, "Pruebas")

        section3 = crear_seccion(self, 3, "Exportar")
        row = tk.Frame(section3, bg=WHITE); row.pack(fill="x")
        self.output_var = tk.StringVar(value="El nombre aparecerá al leer el evento")
        tk.Entry(row, textvariable=self.output_var, state="readonly", readonlybackground=CARD,
                 fg=TEXT, relief="solid", bd=1, font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True, ipady=8)
        boton_secundario(row, "Abrir carpeta", self.abrir_carpeta).pack(side="left", padx=(8, 0))
        ayuda(section3, "Se guardará en la misma carpeta del archivo .mdb").pack(fill="x", pady=(6, 9))
        self.exportar = boton_primario(section3, "►  EXPORTAR JSON", self.guardar, state="disabled")
        self.exportar.pack(fill="x")
        self.barra = ttk.Progressbar(self, mode="indeterminate", length=500)

    def _stat(self, parent, label):
        card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1,
                        padx=16, pady=8)
        card.pack(side="left", padx=(0, 10))
        value = tk.Label(card, text="—", bg=CARD, fg=SUCCESS, font=("Segoe UI", 15, "bold"))
        value.pack()
        tk.Label(card, text=label, bg=CARD, fg=TEXT, font=("Segoe UI", 9)).pack()
        return value

    def seleccionar(self, path):
        self.ruta_mdb = Path(path)
        self.exportar.config(state="disabled")
        self.event_title.config(text="Leyendo el evento…", fg=MUTED)
        self.barra.pack(pady=5); self.barra.start(12)
        logging.info("EXPORTAR: Abriendo %s", path)
        threading.Thread(target=self._leer, args=(path,), daemon=True).start()

    def _leer(self, path):
        try:
            self.after(0, self._mostrar, leer_evento_mdb(path))
        except Exception as exc:
            self.after(0, self._error, str(exc))

    def _mostrar(self, datos):
        self.barra.stop(); self.barra.pack_forget(); self.datos = datos
        meet = datos["meet"]
        self.event_title.config(text=meet["name"], fg=TITLE, font=("Segoe UI", 13, "bold"))
        self.event_meta.config(text=f"{meet['date_start']} · {COURSE_LABELS.get(meet['course'], meet['course'])}")
        self.club_stat.config(text=f"✓  {len(datos['teams'])}")
        self.event_stat.config(text=f"✓  {len(datos['events'])}")
        filename = nombre_config_sugerido(meet["name"])
        self.output_path = self.ruta_mdb.with_name(filename)
        self.output_var.set(str(self.output_path))
        self.exportar.config(state="normal")
        logging.info("EXPORTAR: %s equipos, %s pruebas", len(datos["teams"]), len(datos["events"]))

    def _error(self, detail):
        self.barra.stop(); self.barra.pack_forget()
        self.event_title.config(text="No se pudo leer el archivo.", fg=ERROR)
        messagebox.showerror("No se pudo abrir el archivo", detail, parent=self)

    def abrir_carpeta(self):
        folder = self.output_path.parent if self.output_path else self.ruta_mdb.parent if self.ruta_mdb else None
        if folder:
            os.startfile(folder)

    def guardar(self):
        guardar_config(generar_config(self.datos), self.output_path)
        logging.info("EXPORTAR: JSON guardado en %s", self.output_path)
        messagebox.showinfo("Archivo guardado",
                            f"JSON guardado en:\n{self.output_path}\n\nAhora súbelo en Mis eventos → Importar desde Meet Manager.",
                            parent=self)
