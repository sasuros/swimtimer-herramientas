"""Pantalla consolidado.json a MDB."""

import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core.escribir_mdb import importar_consolidado
from core.leer_consolidado import leer_consolidado
from core.leer_mdb import leer_indices_mdb
from core.validaciones import validar_importacion
from gui.estilos import CARD, CREAM, MUTED, NAVY, TEAL


class ImportarFrame(tk.Frame):
    def __init__(self, master, volver):
        super().__init__(master, bg=NAVY)
        self.datos = self.indices = None
        tk.Button(self, text="< Volver", command=volver, bg=NAVY, fg=CREAM, relief="flat",
                  font=("Segoe UI", 11)).pack(anchor="w", padx=24, pady=(16, 4))
        tk.Label(self, text="Importar inscripciones", bg=NAVY, fg=CREAM,
                 font=("Segoe UI", 22, "bold")).pack()
        tk.Label(self, text="Primero el JSON de la web; despues el .mdb de Meet Manager",
                 bg=NAVY, fg=MUTED, font=("Segoe UI", 11)).pack(pady=(4, 16))
        tk.Button(self, text="SELECCIONAR JSON Y MDB", command=self.elegir,
                  bg=TEAL, fg="white", relief="flat", padx=25, pady=12,
                  font=("Segoe UI", 12, "bold")).pack()
        self.resumen = tk.Label(self, text="", bg=CARD, fg=CREAM, justify="left",
                                width=67, height=10, font=("Segoe UI", 10), padx=16)
        self.resumen.pack(padx=30, pady=16)
        acciones = tk.Frame(self, bg=NAVY); acciones.pack()
        self.detalle_btn = tk.Button(acciones, text="Ver detalle", command=self.detalle,
                                     state="disabled", bg=CARD, fg=CREAM, relief="flat", padx=18, pady=9)
        self.detalle_btn.pack(side="left", padx=5)
        self.importar_btn = tk.Button(acciones, text="IMPORTAR", command=self.importar,
                                      state="disabled", bg=TEAL, fg="white", relief="flat",
                                      padx=25, pady=9, font=("Segoe UI", 11, "bold"))
        self.importar_btn.pack(side="left", padx=5)
        self.barra = ttk.Progressbar(self, mode="indeterminate", length=430)
        self.estado = tk.Label(self, text="", bg=NAVY, fg=MUTED)

    def elegir(self):
        json_path = filedialog.askopenfilename(parent=self, title="Selecciona las inscripciones JSON",
                                               filetypes=[("JSON", "*.json")])
        if not json_path: return
        mdb_path = filedialog.askopenfilename(parent=self, title="Selecciona el MDB donde importar",
                                              filetypes=[("Meet Manager", "*.mdb")])
        if not mdb_path: return
        self.json_path, self.mdb_path = Path(json_path), Path(mdb_path)
        self._ocupado("Validando archivos...")
        threading.Thread(target=self._validar, daemon=True).start()

    def _ocupado(self, texto):
        self.importar_btn.config(state="disabled"); self.detalle_btn.config(state="disabled")
        self.estado.config(text=texto); self.estado.pack(pady=(8, 0))
        self.barra.pack(pady=(8, 0)); self.barra.start(12)

    def _libre(self):
        self.barra.stop(); self.barra.pack_forget(); self.estado.pack_forget()

    def _validar(self):
        try:
            datos = leer_consolidado(self.json_path)
            indices = leer_indices_mdb(self.mdb_path)
            resultado = validar_importacion(datos, indices)
            self.after(0, self._mostrar, datos, indices, resultado)
        except Exception as exc:
            self.after(0, self._error, str(exc))

    def _mostrar(self, datos, indices, resultado):
        self._libre(); self.datos, self.indices, self.validacion = datos, indices, resultado
        meta = datos.get("meta", {})
        tardios = sum(1 for atleta in datos["athletes"] if atleta.get("late"))
        tipo = "SUPLEMENTO DE TARDIAS" if meta.get("type") == "supplement" else "Consolidado completo"
        sha = "verificado" if datos["_validation"]["sha256_verified"] else "no requerido (v1)"
        texto = (f"RESUMEN DE IMPORTACION\n{self.json_path.name}\nMDB: {self.mdb_path.name}\n\n"
                 f"Tipo: {tipo}\n{len(datos.get('teams', []))} clubes | "
                 f"{len(datos['athletes'])} nadadores | {len(datos['results'])} inscripciones\n"
                 f"SHA-256: {sha} | Tardios: {tardios}\n"
                 f"Errores: {len(resultado['errors'])} | Avisos: {len(resultado['warnings'])}")
        self.resumen.config(text=texto)
        self.detalle_btn.config(state="normal")
        if resultado["ok"]:
            self.importar_btn.config(state="normal")
        else:
            messagebox.showerror("No se puede importar", "\n".join(resultado["errors"][:12]), parent=self)

    def detalle(self):
        ventana = tk.Toplevel(self); ventana.title("Detalle de inscripciones"); ventana.geometry("650x430")
        texto = tk.Text(ventana, wrap="word", font=("Segoe UI", 10)); texto.pack(fill="both", expand=True)
        equipos = {int(t["Team_no"]): t.get("Team_name", str(t["Team_no"])) for t in self.datos.get("teams", [])}
        grupos = {}
        for atleta in self.datos["athletes"]:
            grupos.setdefault(int(atleta["Team_no"]), []).append(atleta)
        for team_no, atletas in grupos.items():
            texto.insert("end", f"\n{equipos.get(team_no, 'Equipo ' + str(team_no))} ({len(atletas)})\n")
            for a in atletas:
                marca = " [TARDIO]" if a.get("late") else ""
                texto.insert("end", f"  {a.get('Last_name','')}, {a.get('First_name','')}{marca}\n")
        if self.validacion["warnings"]:
            texto.insert("end", "\nAVISOS\n" + "\n".join(self.validacion["warnings"]))
        texto.config(state="disabled")

    def importar(self):
        if not messagebox.askyesno("Confirmar importacion",
                                   "Se creara un backup automatico antes de escribir.\n\nContinuar?", parent=self):
            return
        self._ocupado("Creando backup e importando...")
        threading.Thread(target=self._importar_worker, daemon=True).start()

    def _progreso(self, actual, total, texto):
        self.after(0, self.estado.config, {"text": f"{texto}: {actual}/{total}"})

    def _importar_worker(self):
        try:
            resultado = importar_consolidado(self.mdb_path, self.datos, self._progreso)
            self.after(0, self._terminado, resultado)
        except Exception as exc:
            self.after(0, self._error, str(exc))

    def _terminado(self, r):
        self._libre()
        messagebox.showinfo("Importacion completada",
            f"Equipos insertados: {r['teams']}\nNadadores: {r['athletes']}\n"
            f"Inscripciones: {r['entries']}\nOmitidos: {r['skipped']}\n\nBackup:\n{r['backup']}\n\n"
            "Abre Meet Manager para verificar.", parent=self)

    def _error(self, detalle):
        self._libre(); logging.exception("Operacion de importacion fallida")
        messagebox.showerror("No se pudo completar", detalle, parent=self)

