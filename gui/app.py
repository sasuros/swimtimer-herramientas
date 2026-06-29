"""Ventana principal de SWIMTIMER Herramientas."""

import tkinter as tk

from gui.estilos import CARD, CREAM, GOLD, MUTED, NAVY, TEAL, centrar, ruta_recurso
from gui.exportar_frame import ExportarFrame
from gui.importar_frame import ImportarFrame


class SwimtimerApp:
    def __init__(self, root):
        self.root = root
        root.title("SWIMTIMER - Herramientas")
        root.configure(bg=NAVY)
        root.minsize(700, 500)
        root.resizable(False, False)
        centrar(root)
        self.contenedor = tk.Frame(root, bg=NAVY)
        self.contenedor.pack(fill="both", expand=True)
        self.mostrar_menu()

    def limpiar(self):
        for hijo in self.contenedor.winfo_children():
            hijo.destroy()

    def mostrar_menu(self):
        self.limpiar()
        logo_path = ruta_recurso("logo_swimtimer.png")
        if logo_path.is_file():
            try:
                self.logo = tk.PhotoImage(file=str(logo_path)).subsample(4, 4)
                tk.Label(self.contenedor, image=self.logo, bg=NAVY).pack(pady=(24, 2))
            except tk.TclError:
                pass
        tk.Label(self.contenedor, text="SWIMTIMER - Herramientas", bg=NAVY, fg=CREAM,
                 font=("Segoe UI", 22, "bold")).pack(pady=(2, 0))
        tk.Label(self.contenedor, text="by Scanleads", bg=NAVY, fg=MUTED,
                 font=("Segoe UI", 10)).pack(pady=(0, 20))
        tarjetas = tk.Frame(self.contenedor, bg=NAVY); tarjetas.pack()
        self._tarjeta(tarjetas, "EXPORTAR\nEVENTO", "Leer tu .mdb y generar\nel JSON para la web",
                      GOLD, NAVY, lambda: self.mostrar(ExportarFrame)).pack(side="left", padx=12)
        self._tarjeta(tarjetas, "IMPORTAR\nINSCRIPCIONES", "Leer el JSON de la web\ny escribir en tu .mdb",
                      TEAL, "white", lambda: self.mostrar(ImportarFrame)).pack(side="left", padx=12)
        tk.Label(self.contenedor, text="Version 1.0 - SWIMTIMER Inscripciones by Scanleads",
                 bg=NAVY, fg=MUTED, font=("Segoe UI", 9)).pack(side="bottom", pady=18)

    def _tarjeta(self, padre, titulo, descripcion, fondo, texto, comando):
        frame = tk.Frame(padre, bg=fondo, width=270, height=185)
        frame.pack_propagate(False)
        boton = tk.Button(frame, text=titulo, command=comando, bg=fondo, fg=texto,
                          activebackground=fondo, activeforeground=texto, relief="flat",
                          font=("Segoe UI", 17, "bold"), cursor="hand2")
        boton.pack(fill="both", expand=True, pady=(15, 0))
        tk.Label(frame, text=descripcion, bg=fondo, fg=texto, justify="center",
                 font=("Segoe UI", 10)).pack(pady=(0, 22))
        for widget in (frame,):
            widget.bind("<Button-1>", lambda _e: comando())
        return frame

    def mostrar(self, clase):
        self.limpiar()
        clase(self.contenedor, self.mostrar_menu).pack(fill="both", expand=True)

