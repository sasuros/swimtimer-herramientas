"""Pantalla MDB a config_evento.json."""

import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core.generar_config import generar_config, guardar_config, nombre_config_sugerido
from core.leer_mdb import leer_evento_mdb
from gui.estilos import CARD, CREAM, GOLD, MUTED, NAVY


class ExportarFrame(tk.Frame):
    def __init__(self, master, volver):
        super().__init__(master, bg=NAVY)
        self.volver = volver
        self.datos = None
        tk.Button(self, text="< Volver", command=volver, bg=NAVY, fg=CREAM, relief="flat",
                  font=("Segoe UI", 11)).pack(anchor="w", padx=24, pady=(16, 4))
        tk.Label(self, text="Exportar evento", bg=NAVY, fg=CREAM,
                 font=("Segoe UI", 22, "bold")).pack()
        tk.Label(self, text="Selecciona el archivo .mdb de tu evento en Meet Manager",
                 bg=NAVY, fg=MUTED, font=("Segoe UI", 11)).pack(pady=(4, 16))
        tk.Button(self, text="SELECCIONAR ARCHIVO .MDB", command=self.elegir,
                  bg=GOLD, fg=NAVY, relief="flat", padx=25, pady=12,
                  font=("Segoe UI", 12, "bold")).pack()
        self.resumen = tk.Label(self, text="", bg=CARD, fg=CREAM, justify="left",
                                width=64, height=8, font=("Segoe UI", 11), padx=18)
        self.resumen.pack(padx=35, pady=18)
        self.exportar = tk.Button(self, text="EXPORTAR JSON", command=self.guardar,
                                  state="disabled", bg=GOLD, fg=NAVY, relief="flat",
                                  padx=25, pady=10, font=("Segoe UI", 11, "bold"))
        self.exportar.pack()
        self.barra = ttk.Progressbar(self, mode="indeterminate", length=400)

    def elegir(self):
        ruta = filedialog.askopenfilename(parent=self, title="Selecciona el archivo .mdb",
                                          filetypes=[("Meet Manager", "*.mdb")])
        if not ruta:
            return
        self.barra.pack(pady=12)
        self.barra.start(12)
        self.resumen.config(text="Leyendo el evento...")
        logging.info("EXPORTAR: Abriendo %s", ruta)
        threading.Thread(target=self._leer, args=(ruta,), daemon=True).start()

    def _leer(self, ruta):
        try:
            datos = leer_evento_mdb(ruta)
            self.after(0, self._mostrar, ruta, datos)
        except Exception as exc:
            self.after(0, self._error, str(exc))

    def _mostrar(self, ruta, datos):
        self.barra.stop(); self.barra.pack_forget()
        self.datos = datos
        self.ruta_mdb = Path(ruta)
        meet = datos["meet"]
        texto = (f"EVENTO ENCONTRADO\n\n{meet['name']}\n"
                 f"{meet['date_start']}  |  {meet['venue']}\n\n"
                 f"{len(datos['teams'])} clubes     {len(datos['events'])} pruebas")
        if datos["warnings"]:
            texto += f"\nAvisos: {len(datos['warnings'])} estilos no reconocidos"
        self.resumen.config(text=texto)
        self.exportar.config(state="normal")
        logging.info("EXPORTAR: %s equipos, %s eventos", len(datos["teams"]), len(datos["events"]))

    def _error(self, detalle):
        self.barra.stop(); self.barra.pack_forget()
        self.resumen.config(text="No se pudo leer el archivo seleccionado.")
        messagebox.showerror("No se pudo abrir el archivo", detalle, parent=self)

    def guardar(self):
        config = generar_config(self.datos)
        sugerido = nombre_config_sugerido(config["meet"]["name"])
        ruta = filedialog.asksaveasfilename(parent=self, title="Guardar config del evento",
                                            initialdir=self.ruta_mdb.parent, initialfile=sugerido,
                                            defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not ruta:
            return
        guardar_config(config, ruta)
        logging.info("EXPORTAR: JSON guardado en %s", ruta)
        messagebox.showinfo("Archivo guardado",
                            "Ahora subelo a la web en:\nMis eventos > Importar desde Meet Manager",
                            parent=self)

