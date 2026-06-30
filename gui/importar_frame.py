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
        self.comparison = None
        self.changes_open = False
        self.deleted_vars = {}
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
        self.changes_button = boton_secundario(
            self.section3, "Ver cambios por club", self.toggle_changes
        )
        self.changes_panel = tk.Frame(self.section3, bg=WHITE)
        self.deleted_panel = tk.Frame(self.section3, bg=WHITE)
        self.delete_mode = tk.StringVar(value="keep")
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
        self.comparison = result.get("comparison") or {}
        self._render_comparison()
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

    def toggle_changes(self):
        self.changes_open = not self.changes_open
        self.changes_button.config(
            text="Ocultar cambios por club" if self.changes_open else "Ver cambios por club"
        )
        if self.changes_open:
            self.changes_panel.pack(fill="x", pady=(6, 8), before=self.update_existing)
        else:
            self.changes_panel.pack_forget()

    def _render_comparison(self):
        for child in self.changes_panel.winfo_children():
            child.destroy()
        for child in self.deleted_panel.winfo_children():
            child.destroy()
        self.changes_panel.pack_forget()
        self.deleted_panel.pack_forget()
        self.changes_button.pack_forget()
        self.deleted_vars = {}
        self.delete_mode.set("keep")
        self.changes_open = False
        self.changes_button.config(text="Ver cambios por club")
        if not self.comparison.get("has_previous_data"):
            return

        self.changes_button.pack(anchor="w", pady=(4, 4), before=self.update_existing)
        for club in self.comparison.get("clubs", []):
            card = tk.Frame(
                self.changes_panel, bg=CARD, highlightbackground="#D1D5DB",
                highlightthickness=1, padx=10, pady=8,
            )
            card.pack(fill="x", pady=(0, 6))
            tk.Label(
                card, text=f"{club['Team_name']} (#{club['Team_no']})",
                bg=CARD, fg=TITLE, anchor="w", font=("Segoe UI", 10, "bold"),
            ).pack(fill="x")
            diferencias = club["new"] or club["removed"] or club["modified"]
            if not diferencias:
                tk.Label(
                    card, text=f"Sin cambios ({len(club['unchanged'])} nadadores)",
                    bg=CARD, fg=MUTED, anchor="w", font=("Segoe UI", 9),
                ).pack(fill="x", pady=(4, 0))
                continue
            tk.Label(
                card, text=f"{len(club['unchanged'])} sin cambios", bg=CARD,
                fg=MUTED, anchor="w", font=("Segoe UI", 9),
            ).pack(fill="x", pady=(4, 2))
            for athlete in club["new"]:
                self._change_row(card, "✅ Nuevo", athlete, "#ECFDF5", SUCCESS)
            for athlete in club["removed"]:
                self._change_row(card, "⚠️ Eliminado", athlete, "#FEF3C7", WARNING)
            for athlete in club["modified"]:
                campos = ", ".join(athlete.get("changed_labels") or [])
                self._change_row(card, f"📝 Modificado ({campos})", athlete, "#EFF6FF", "#1D4ED8")

        removed = self.comparison.get("removed") or []
        if removed:
            self._render_deleted_selector(removed)

    def _change_row(self, parent, prefix, athlete, background, foreground):
        tk.Label(
            parent, text=f"{prefix}: {self._athlete_text(athlete)}",
            bg=background, fg=foreground, anchor="w", justify="left",
            font=("Segoe UI", 9), padx=7, pady=5,
        ).pack(fill="x", pady=1)

    @staticmethod
    def _athlete_text(athlete):
        return (
            f"{athlete.get('Last_name', '')}, {athlete.get('First_name', '')} "
            f"({athlete.get('Ath_Sex', '—')}, {athlete.get('Ath_age', '—')} años)"
        )

    def _render_deleted_selector(self, athletes):
        self.deleted_panel.configure(
            bg="#FEF3C7", highlightbackground="#F59E0B", highlightthickness=1,
            padx=12, pady=10,
        )
        tk.Label(
            self.deleted_panel, text="Nadadores que ya no están en la inscripción:",
            bg="#FEF3C7", fg=WARNING, anchor="w", font=("Segoe UI", 10, "bold"),
        ).pack(fill="x")
        for athlete in athletes:
            ath_no = int(athlete["Ath_no"])
            variable = tk.BooleanVar(value=True)
            self.deleted_vars[ath_no] = variable
            tk.Checkbutton(
                self.deleted_panel,
                text=f"{athlete.get('Last_name', '')}, {athlete.get('First_name', '')} — {athlete.get('Team_name')} (#{athlete.get('Team_no')})",
                variable=variable, bg="#FEF3C7", fg=WARNING,
                activebackground="#FEF3C7", activeforeground=WARNING,
                selectcolor=WHITE, anchor="w", font=("Segoe UI", 9),
            ).pack(fill="x")
        tk.Label(
            self.deleted_panel, text="¿Qué hacer con ellos?", bg="#FEF3C7",
            fg=TITLE, anchor="w", font=("Segoe UI", 10, "bold"),
        ).pack(fill="x", pady=(8, 2))
        for value, text in (
            ("keep", "Mantener en el .mdb (no borrar nada)"),
            ("delete", "Eliminar del .mdb (sincronizar con la inscripción)"),
        ):
            tk.Radiobutton(
                self.deleted_panel, text=text, variable=self.delete_mode, value=value,
                bg="#FEF3C7", fg=TEXT, activebackground="#FEF3C7",
                selectcolor=WHITE, anchor="w", font=("Segoe UI", 9),
            ).pack(fill="x")
        tk.Label(
            self.deleted_panel,
            text="Si eliges eliminar, se borrarán de Athlete y Entry después de crear el backup.",
            bg="#FEF3C7", fg=WARNING, anchor="w", justify="left", font=("Segoe UI", 9),
        ).pack(fill="x", pady=(4, 0))
        self.deleted_panel.pack(fill="x", pady=(6, 8), before=self.update_existing)

    def importar(self):
        eliminar = []
        if self.delete_mode.get() == "delete":
            eliminar = [ath_no for ath_no, variable in self.deleted_vars.items() if variable.get()]
            if eliminar and not messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Eliminar {len(eliminar)} nadadores del .mdb? Esta acción se incluirá en el backup.",
                parent=self,
            ):
                return
        if not messagebox.askyesno("Confirmar importación",
                                   "Se creará una copia de seguridad automática antes de escribir.\n\n¿Continuar?", parent=self):
            return
        self._busy("Creando backup e importando…")
        actualizar = self.update_existing_var.get()
        modificados = set(self.comparison.get("modified_ids") or [])
        threading.Thread(
            target=self._import_worker,
            args=(actualizar, modificados, eliminar),
            daemon=True,
        ).start()

    def _progress(self, current, total, text):
        self.after(0, self.status.config, {"text": f"{text}: {current}/{total}"})

    def _import_worker(self, actualizar_existentes, atletas_modificados, atletas_eliminar):
        try:
            result = importar_consolidado(
                self.mdb_path,
                self.datos,
                self._progress,
                actualizar_existentes=actualizar_existentes,
                atletas_modificados=atletas_modificados,
                atletas_eliminar=atletas_eliminar,
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
            f"Nadadores eliminados del .mdb: {result['athletes_deleted']}\n"
            f"Inscripciones insertadas: {result['entries']}\n"
            f"Inscripciones omitidas (ya existían): {result['entries_skipped']}\n"
            f"Inscripciones eliminadas del .mdb: {result['entries_deleted']}\n\n"
            f"Backup guardado en:\n{result['backup']}\n\nAbre Meet Manager para verificar.", parent=self)

    def _error(self, detail):
        self._free(); self.summary.config(text="No se pudo completar la operación.", fg=ERROR)
        logging.error("Operación de importación fallida: %s", detail)
        messagebox.showerror("No se pudo completar", detail, parent=self)
