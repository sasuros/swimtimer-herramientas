"""Importacion transaccional y con backup a Meet Manager."""

import logging
import shutil
from datetime import date, datetime
from pathlib import Path

from core.jet4 import conectar_mdb

ATHLETE_FIELDS = [
    "Ath_no", "Last_name", "First_name", "Initial", "Ath_Sex", "Birth_date",
    "Team_no", "Schl_yr", "Ath_age", "Reg_no", "Ath_stat", "Div_no", "Comp_no",
    "Pref_name", "Home_addr1", "Home_addr2", "Home_city", "Home_prov",
    "Home_statenew", "Home_zip", "Home_cntry", "Home_daytele", "Home_evetele",
    "Home_faxtele", "Home_email", "Citizen_of", "Picture_bmp", "second_club",
    "Home_celltele", "bcssa_type",
]
RESULT_FIELDS = [
    "Event_ptr", "Ath_no", "ActSeed_course", "ActualSeed_time", "ConvSeed_course",
    "ConvSeed_time", "Scr_stat", "Spec_stat", "Dec_stat", "Alt_stat", "Bonus_event",
    "Div_no", "Ev_score", "JDEv_score", "Seed_place", "event_age", "Pre_heat",
    "Pre_lane", "Pre_stat", "Pre_Time", "Pre_course", "Pre_heatplace", "Pre_place",
    "Pre_jdplace", "Pre_exh", "Pre_points", "Pre_back1", "Pre_back2", "Pre_back3",
    "Pre_watch1", "Pre_pad", "Pre_reactiontime1", "Pre_dqcode", "Pre_dqcodeSecond",
    "Pre_TimeType", "Fin_heat", "Fin_lane", "Fin_stat", "Fin_Time", "Fin_course",
    "Fin_heatplace", "Fin_jdheatplace", "Fin_place", "Fin_jdplace", "Fin_exh",
    "Fin_points", "Fin_back1", "Fin_back2", "Fin_back3", "Fin_watch1", "Fin_pad",
    "Fin_reactiontime1", "Fin_dqcode", "Fin_dqcodeSecond", "Fin_ptsplace",
    "fin_heatltr", "fin_TimeType", "Sem_heat", "Sem_lane", "Sem_stat", "Sem_Time",
    "Sem_course", "Sem_heatplace", "Sem_place", "Sem_jdplace", "Sem_exh", "Sem_points",
    "Sem_back1", "Sem_back2", "Sem_back3", "Sem_watch1", "Sem_pad",
    "Sem_reactiontime1", "Sem_dqcode", "Sem_dqcodeSecond", "Sem_TimeType", "dq_type",
    "Fin_group", "Fin_dolphin1", "Fin_dolphin2", "Fin_dolphin3", "Pre_dolphin1",
    "Pre_dolphin2", "Pre_dolphin3", "Sem_dolphin1", "Sem_dolphin2", "Sem_dolphin3",
]


def crear_backup(ruta_mdb: str | Path) -> Path:
    origen = Path(ruta_mdb)
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = origen.with_name(f"{origen.stem}_BACKUP_{sello}{origen.suffix}")
    try:
        shutil.copy2(origen, destino)
    except OSError as exc:
        raise RuntimeError(f"No se pudo crear el backup. No se modifico el MDB: {exc}") from exc
    if destino.stat().st_size != origen.stat().st_size:
        destino.unlink(missing_ok=True)
        raise RuntimeError("El backup no paso la verificacion de tamano. No se modifico el MDB.")
    logging.info("IMPORTAR: Backup creado: %s", destino)
    return destino


def _normalizar_valor(campo, valor):
    if campo == "Birth_date" and isinstance(valor, str) and valor:
        try:
            return date.fromisoformat(valor[:10])
        except ValueError:
            return valor
    return None if valor == "" else valor


def _insertar_si_no_existe(cursor, tabla, campos, registro, consulta, clave):
    if cursor.execute(consulta, *clave).fetchone() is not None:
        return False
    columnas = ", ".join(f"[{campo}]" for campo in campos)
    marcas = ", ".join("?" for _ in campos)
    valores = [_normalizar_valor(campo, registro.get(campo)) for campo in campos]
    cursor.execute(f"INSERT INTO [{tabla}] ({columnas}) VALUES ({marcas})", *valores)
    return True


def importar_consolidado(ruta_mdb: str | Path, datos: dict, progreso=None) -> dict:
    """Crea backup y agrega equipos, atletas e inscripciones en una transaccion."""
    backup = crear_backup(ruta_mdb)
    conexion = None
    conteos = {"teams": 0, "athletes": 0, "entries": 0, "skipped": 0}
    try:
        conexion = conectar_mdb(ruta_mdb)
        cursor = conexion.cursor()
        iniciales = {
            tabla: int(cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]").fetchone()[0])
            for tabla in ("Team", "Athlete", "Entry")
        }
        teams = datos.get("teams") or []
        total = len(teams) + len(datos["athletes"]) + len(datos["results"])
        actual = 0
        for team in teams:
            campos = ["Team_no", "Team_name", "Team_short", "Team_abbr"]
            inserted = _insertar_si_no_existe(
                cursor, "Team", campos, team,
                "SELECT Team_no FROM Team WHERE Team_no = ?", (team.get("Team_no"),),
            )
            conteos["teams" if inserted else "skipped"] += 1
            actual += 1
            if progreso:
                progreso(actual, total, "Insertando equipos")
        for athlete in datos["athletes"]:
            inserted = _insertar_si_no_existe(
                cursor, "Athlete", ATHLETE_FIELDS, athlete,
                "SELECT Ath_no FROM Athlete WHERE Ath_no = ?", (athlete.get("Ath_no"),),
            )
            conteos["athletes" if inserted else "skipped"] += 1
            actual += 1
            if progreso:
                progreso(actual, total, "Insertando nadadores")
        for entry in datos["results"]:
            inserted = _insertar_si_no_existe(
                cursor, "Entry", RESULT_FIELDS, entry,
                "SELECT Event_ptr FROM Entry WHERE Event_ptr = ? AND Ath_no = ?",
                (entry.get("Event_ptr"), entry.get("Ath_no")),
            )
            conteos["entries" if inserted else "skipped"] += 1
            actual += 1
            if progreso:
                progreso(actual, total, "Insertando inscripciones")
        finales = {
            tabla: int(cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]").fetchone()[0])
            for tabla in ("Team", "Athlete", "Entry")
        }
        esperados = {
            "Team": iniciales["Team"] + conteos["teams"],
            "Athlete": iniciales["Athlete"] + conteos["athletes"],
            "Entry": iniciales["Entry"] + conteos["entries"],
        }
        discrepancias = [
            f"{tabla}: esperado {esperados[tabla]}, obtenido {finales[tabla]}"
            for tabla in esperados if finales[tabla] != esperados[tabla]
        ]
        if discrepancias:
            raise RuntimeError("La verificacion posterior fallo: " + "; ".join(discrepancias))
        conexion.commit()
        conteos["table_counts"] = finales
        conteos["backup"] = str(backup)
        logging.info("IMPORTAR: Completado. Resultado=%s", conteos)
        return conteos
    except Exception:
        if conexion is not None:
            conexion.rollback()
        logging.exception("IMPORTAR: Error; transaccion revertida")
        raise
    finally:
        if conexion is not None:
            conexion.close()
