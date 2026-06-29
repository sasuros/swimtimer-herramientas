"""Ventana principal de SWIMTIMER Herramientas."""

import tkinter as tk

from gui.estilos import BORDER, CARD, HEADER, MUTED, PRIMARY, TEXT, TITLE, WHITE, centrar, ruta_recurso
from gui.exportar_frame import ExportarFrame
from gui.importar_frame import ImportarFrame


class SwimtimerApp:
    def __init__(self, root):
        self.root = root
        root.title("SWIMTIMER · Herramientas")
        root.configure(bg=WHITE)
        root.minsize(780, 700)
        root.resizable(False, False)
        centrar(root)
        self._header()
        self.contenedor = tk.Frame(root, bg=WHITE)
        self.contenedor.pack(fill="both", expand=True)
        self.mostrar_menu()

    def _header(self):
        header = tk.Frame(self.root, bg=HEADER, height=88, padx=22, pady=12)
        header.pack(fill="x"); header.pack_propagate(False)
        logo_path = ruta_recurso("logo_swimtimer.png")
        if logo_path.is_file():
            try:
                self.logo = tk.PhotoImage(file=str(logo_path)).subsample(7, 7)
                tk.Label(header, image=self.logo, bg=HEADER).pack(side="left", padx=(0, 14))
            except tk.TclError:
                pass
        title = tk.Frame(header, bg=HEADER); title.pack(side="left", fill="y")
        tk.Label(title, text="SWIMTIMER · HERRAMIENTAS", bg=HEADER, fg=WHITE,
                 font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(title, text="by Scanleads", bg=HEADER, fg="#D1D5DB",
                 font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(header, text="v1.0", bg=HEADER, fg=WHITE,
                 font=("Segoe UI", 10, "bold")).pack(side="right")

    def limpiar(self):
        for hijo in self.contenedor.winfo_children():
            hijo.destroy()

    def mostrar_menu(self):
        self.limpiar()
        body = tk.Frame(self.contenedor, bg=WHITE); body.pack(expand=True)
        tk.Label(body, text="¿Qué necesitas hacer?", bg=WHITE, fg=TITLE,
                 font=("Segoe UI", 24, "bold")).pack(pady=(30, 24))
        cards = tk.Frame(body, bg=WHITE); cards.pack()
        self._card(cards, "↑  EXPORTAR\nEVENTO", "Lee tu .mdb y genera el JSON\npara crear el evento en la web",
                   lambda: self.mostrar(ExportarFrame)).pack(side="left", padx=12)
        self._card(cards, "↓  IMPORTAR\nINSCRIPCIONES", "Lee el JSON de la web y escribe\nlos nadadores en tu .mdb",
                   lambda: self.mostrar(ImportarFrame)).pack(side="left", padx=12)
        tk.Label(self.contenedor, text="SWIMTIMER · Herramientas by Scanleads · v1.0",
                 bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(side="bottom", pady=16)

    def _card(self, parent, title, description, command):
        frame = tk.Frame(parent, bg=CARD, width=315, height=225,
                         highlightbackground=BORDER, highlightthickness=1)
        frame.pack_propagate(False)
        tk.Label(frame, text=title, bg=CARD, fg=TITLE, justify="center",
                 font=("Segoe UI", 17, "bold")).pack(pady=(28, 12))
        tk.Label(frame, text=description, bg=CARD, fg=TEXT, justify="center",
                 font=("Segoe UI", 10)).pack()
        tk.Button(frame, text="ELEGIR", command=command, bg=PRIMARY, fg=WHITE,
                  activebackground="#065F46", activeforeground=WHITE, relief="flat",
                  font=("Segoe UI", 12, "bold"), cursor="hand2", padx=32, pady=10).pack(pady=22)
        return frame

    def mostrar(self, clase):
        self.limpiar()
        clase(self.contenedor, self.mostrar_menu).pack(fill="both", expand=True)
