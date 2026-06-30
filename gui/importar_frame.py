"""Pantalla consolidado.json a MDB."""

import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from core.escribir_mdb import importar_consolidado
from core.leer_consolidado import leer_consolidado
from core.leer_mdb import leer_indices_mdb
from core.validaciones import validar_importacion
from gui.drop_zone import DropZone
from gui.estilos import (CARD, ERROR, HELP, MUTED, SUCCESS, TEXT, TITLE,
                         WARNING, WHITE, ayuda, boton_primario,
                         boton_secundario, configurar_boton_primario,
                         crear_seccion)


class ImportarFrame(tk.Frame):
    def __init__(self, master, volver):
        super().__init__(master, bg=WHITE)
        self.json_path = self.mdb_path = self.datos = self.indices = None
        top = tk.Frame(self, bg=WHITE); top.pack(fill="x", padx=28, pady=(12, 4))
        boton_secundario(top, "← Volver", volver).pack(side="left")
        tk.Label(self, text="IMPORTAR INSCRIPCIONES", bg=WHITE, fg=TITLE,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=28, pady=(2, 8))

        section1 = crear_seccion(self, 1, "Archivo de inscripciones")
        self.json_drop = DropZone(section1, [("Archivos JSON", "*.json")], {".json"},
                                  self.seleccionar_json, "El consolidado descargado desde la web")
        self.json_drop.pack(fill="x")

        section2 = crear_seccion(self, 2, "Base de datos de Meet Manager")
        self.mdb_drop = DropZone(section2, [("Archivos MDB", "*.mdb")], {".mdb"},
                                 self.seleccionar_mdb, "El archivo .mdb donde se importarán los nadadores")
        self.mdb_drop.pack(fill="x")

        self.section3 = crear_seccion(self, 3, "Resumen")
        self.summary = tk.Label(self.section3, text="Selecciona los dos archivos para validar la importación.",
                                bg=WHITE, fg=MUTED, justify="left", anchor="w", font=("Segoe UI", 10))
        self.summary.pack(fill="x")
        self.detail_button = boton_secundario(self.section3, "Ver detalle", self.detalle, state="disabled")
        self.detail_button.pack(anchor="w", pady=(8, 4))
        self.update_existing_var = tk.BooleanVar(value=False)
        self.update_existing = tk.Checkbutton(
            self.section3,
            text="Actualizar nadadores existentes (sobrescribir datos corregidos)",
            variable=self.update_existing_var,
            bg=WHITE,
            fg=TEXT,
            activebackground=WHITE,
            activeforeground=TEXT,
            selectcolor=WHITE,
            anchor="w",
            font=("Segoe UI", 10),
        )
        self.update_existing.pack(fill="x", pady=(4, 2))
        ayuda(
            self.section3,
            "Desmarcado: los nadadores que ya existen se omiten. Marcado: se actualizan sus datos.",
        ).pack(fill="x", pady=(0, 4))
        ayuda(self.section3, "Antes de escribir se creará automáticamente una copia de seguridad del archivo .mdb").pack(fill="x", pady=(4, 8))
        self.import_button = boton_primario(self.section3, "►  IMPORTAR AL MEET MANAGER", self.importar, state="disabled")
        self.import_button.pack(fill="x")
        self.progress = ttk.Progressbar(self, mode="indeterminate", length=500)
        self.status = tk.Label(self, text="", bg=WHITE, fg=HELP, font=("Segoe UI", 9))

    def seleccionar_json(self, path):
        self.json_path = Path(path); self._ready()

    def seleccionar_mdb(self, path):
        self.mdb_path = Path(path); self._ready()

    def _ready(self):
        if self.json_path and self.mdb_path:
            self._busy("Validando archivos…")
            threading.Thread(target=self._validate, daemon=True).start()

    def _busy(self, text):
        configurar_boton_primario(self.import_button, False)
        self.detail_button.config(state="disabled")
        self.status.config(text=text); self.status.pack(pady=(2, 0))
        self.progress.pack(pady=(4, 0)); self.progress.start(12)

    def _free(self):
        self.progress.stop(); self.progress.pack_forget(); self.status.pack_forget()

    def _validate(self):
        try:
            data = leer_consolidado(self.json_path)
            indices = leer_indices_mdb(self.mdb_path)
            result = validar_importacion(data, indices)
            self.after(0, self._show, data, indices, result)
        except Exception as exc:
            self.after(0, self._error, str(exc))

    def _show(self, data, indices, result):
        self._free(); self.datos, self.indices, self.validacion = data, indices, result
        late = sum(1 for athlete in data["athletes"] if athlete.get("late"))
        sha = "✓ SHA-256 verificado" if data["_validation"]["sha256_verified"] else "SHA-256 no requerido (v1)"
        incremental = result["incremental"]
        text = (
            "Resumen de importación:\n"
            f"{incremental['athletes_total']} nadadores en el JSON\n"
            f"{incremental['athletes_new']} son NUEVOS (se insertarán)\n"
            f"{incremental['athletes_existing']} ya existen en el .mdb (se omitirán)\n"
            f"{incremental['entries_total']} inscripciones en el JSON\n"
            f"{incremental['entries_new']} son NUEVAS (se insertarán)\n"
            f"{incremental['entries_existing']} ya existen (se omitirán)\n\n"
            f"{sha}"
        )
        if late:
            text += f"\n⚠  {late} nadadores marcados como tardíos"
        if result["warnings"]:
            text += f"\n{len(result['warnings'])} avisos para revisar"
        self.summary.config(text=text, fg=SUCCESS if result["ok"] else ERROR,
                            font=("Segoe UI", 10, "bold"))
        self.detail_button.config(state="normal")
        if result["ok"]:
            configurar_boton_primario(self.import_button, True)
        else:
            messagebox.showerror("No se puede importar", "\n".join(result["errors"][:12]), parent=self)

    def detalle(self):
        window = tk.Toplevel(self); window.title("Detalle de inscripciones"); window.geometry("650x430")
        text = tk.Text(window, wrap="word", font=("Segoe UI", 10), bg=WHITE, fg=TEXT)
        text.pack(fill="both", expand=True)
        teams = {int(t["Team_no"]): t.get("Team_name", str(t["Team_no"])) for t in self.datos.get("teams", [])}
        groups = {}
        for athlete in self.datos["athletes"]:
            groups.setdefault(int(athlete["Team_no"]), []).append(athlete)
        for team_no, athletes in groups.items():
            text.insert("end", f"\n{teams.get(team_no, 'Equipo ' + str(team_no))} ({len(athletes)})\n")
            for athlete in athletes:
                mark = " [TARDÍO]" if athlete.get("late") else ""
                text.insert("end", f"  {athlete.get('Last_name','')}, {athlete.get('First_name','')}{mark}\n")
        if self.validacion["warnings"]:
            text.insert("end", "\nAVISOS\n" + "\n".join(self.validacion["warnings"]))
        text.config(state="disabled")

    def importar(self):
        if not messagebox.askyesno("Confirmar importación",
                                   "Se creará una copia de seguridad automática antes de escribir.\n\n¿Continuar?", parent=self):
            return
        self._busy("Creando backup e importando…")
        actualizar = self.update_existing_var.get()
        threading.Thread(target=self._import_worker, args=(actualizar,), daemon=True).start()

    def _progress(self, current, total, text):
        self.after(0, self.status.config, {"text": f"{text}: {current}/{total}"})

    def _import_worker(self, actualizar_existentes):
        try:
            result = importar_consolidado(
                self.mdb_path,
                self.datos,
                self._progress,
                actualizar_existentes=actualizar_existentes,
            )
            self.after(0, self._done, result)
        except Exception as exc:
            self.after(0, self._error, str(exc))

    def _done(self, result):
        self._free()
        messagebox.showinfo("Importación completada",
            f"Nadadores insertados: {result['athletes']}\n"
            f"Nadadores actualizados: {result['athletes_updated']}\n"
            f"Nadadores omitidos (ya existían): {result['athletes_skipped']}\n"
            f"Inscripciones insertadas: {result['entries']}\n"
            f"Inscripciones omitidas (ya existían): {result['entries_skipped']}\n\n"
            f"Backup guardado en:\n{result['backup']}\n\nAbre Meet Manager para verificar.", parent=self)

    def _error(self, detail):
        self._free(); self.summary.config(text="No se pudo completar la operación.", fg=ERROR)
        logging.error("Operación de importación fallida: %s", detail)
        messagebox.showerror("No se pudo completar", detail, parent=self)
