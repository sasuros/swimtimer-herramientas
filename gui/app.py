"""Ventana principal de SWIMTIMER Herramientas."""

import tkinter as tk
import webbrowser

from core.verificar_sistema import URL_DRIVER_ACCESS, formatear_resultados, verificar_sistema
from gui.estilos import (BORDER, CARD, HEADER, MUTED, PRIMARY, TEXT, TITLE,
                         WARNING, WHITE, boton_secundario, centrar, ruta_recurso)
from gui.exportar_frame import ExportarFrame
from gui.importar_frame import ImportarFrame


class SwimtimerApp:
    def __init__(self, root):
        self.root = root
        root.title("SWIMTIMER · Herramientas")
        root.configure(bg=WHITE)
        root.minsize(780, 650)
        root.resizable(True, True)
        alto = min(820, max(650, root.winfo_screenheight() - 100))
        centrar(root, 820, alto)
        self._header()
        self.contenedor = tk.Frame(root, bg=WHITE)
        self.contenedor.pack(fill="both", expand=True)
        self.mostrar_menu()
        root.after(100, self._verificar_al_iniciar)

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
        boton_secundario(
            body, "🔍  Verificar sistema", self.mostrar_verificacion
        ).pack(pady=(22, 0))
        self.aviso_driver = tk.Frame(
            body, bg="#FFFBEB", highlightbackground="#FCD34D",
            highlightthickness=1, padx=12, pady=8,
        )
        tk.Label(self.contenedor, text="SWIMTIMER · Herramientas by Scanleads · v1.0",
                 bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(side="bottom", pady=16)

    def _verificar_al_iniciar(self):
        _, _, puede_importar = verificar_sistema()
        if not puede_importar:
            self._mostrar_aviso_driver()

    def _mostrar_aviso_driver(self):
        if not self.aviso_driver.winfo_exists():
            return
        tk.Label(
            self.aviso_driver,
            text="⚠️  Driver de Access no encontrado. Exportar funciona, pero Importar requiere el driver.",
            bg="#FFFBEB", fg=WARNING, font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 10))
        tk.Button(
            self.aviso_driver, text="Instalar driver", command=self.abrir_descarga_driver,
            bg="#FFFBEB", fg=TITLE, relief="flat", cursor="hand2",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right")
        self.aviso_driver.pack(pady=(14, 0))

    @staticmethod
    def abrir_descarga_driver():
        webbrowser.open(URL_DRIVER_ACCESS)

    def mostrar_verificacion(self):
        resultados, puede_exportar, puede_importar = verificar_sistema()
        ventana = tk.Toplevel(self.root)
        ventana.title("Verificacion del sistema")
        ventana.configure(bg=WHITE)
        ventana.resizable(False, False)
        ventana.transient(self.root)
        ventana.grab_set()

        tk.Label(
            ventana, text="VERIFICACION DEL SISTEMA", bg=HEADER, fg=WHITE,
            font=("Segoe UI", 16, "bold"), padx=24, pady=16,
        ).pack(fill="x")
        seccion = tk.Frame(
            ventana, bg=WHITE, highlightbackground=BORDER, highlightthickness=1,
            padx=20, pady=16,
        )
        seccion.pack(fill="both", padx=20, pady=20)
        tk.Label(
            seccion,
            text=formatear_resultados(resultados, puede_exportar, puede_importar),
            bg=WHITE, fg=TEXT, justify="left", anchor="w",
            font=("Segoe UI", 10), wraplength=620,
        ).pack(fill="x")

        acciones = tk.Frame(ventana, bg=WHITE)
        acciones.pack(fill="x", padx=20, pady=(0, 20))
        boton_secundario(acciones, "Cerrar", ventana.destroy).pack(side="right")
        if not puede_importar:
            boton_secundario(
                acciones, "Abrir enlace de descarga del driver", self.abrir_descarga_driver
            ).pack(side="right", padx=(0, 10))
        centrar(ventana, 700, 610)

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
        viewport = tk.Frame(self.contenedor, bg=WHITE)
        viewport.pack(fill="both", expand=True)
        canvas = tk.Canvas(viewport, bg=WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(viewport, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        pagina = clase(canvas, self.mostrar_menu)
        self.pagina_activa = pagina
        window_id = canvas.create_window((0, 0), window=pagina, anchor="nw")

        def ajustar_contenido(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def ajustar_ancho(event):
            canvas.itemconfigure(window_id, width=event.width)

        pagina.bind("<Configure>", ajustar_contenido)
        canvas.bind("<Configure>", ajustar_ancho)
        canvas.bind(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(-1 if event.delta > 0 else 1, "units"),
        )
