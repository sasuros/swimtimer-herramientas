"""Consultas de solo lectura sobre archivos Meet Manager."""

import logging
from pathlib import Path

from core.jet4 import conectar_mdb, recuperar_clave_jet4

STROKE_MAP = {
    1: "Crawl", 2: "Espalda", 3: "Pecho", 4: "Mariposa",
    5: "Comb. Individual", 6: "Libre", 7: "Tablita",
}
SEX_MAP = {"G": "F", "F": "F", "B": "M", "M": "M", "X": "X"}


def _valor(fila, indice, nombre):
    if isinstance(fila, dict):
        if nombre in fila:
            return fila[nombre]
        nombre_normalizado = nombre.casefold()
        for clave, valor in fila.items():
            if str(clave).casefold() == nombre_normalizado:
                return valor
        return None
    try:
        return getattr(fila, nombre)
    except (AttributeError, TypeError):
        return fila[indice]


def _iso(valor):
    if valor in (None, ""):
        return ""
    if hasattr(valor, "date"):
        return valor.date().isoformat()
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return str(valor).split(" ", 1)[0]


def leer_con_access_parser(ruta_mdb: str | Path, password=None):
    """Abre un MDB directamente, sin ODBC ni DAO."""
    from access_parser import AccessParser

    if password:
        return AccessParser(str(ruta_mdb), password=password)
    return AccessParser(str(ruta_mdb))


def _filas_access_parser(database, tabla):
    """Normaliza salidas columnares o listas de diccionarios a filas."""
    datos = database.parse_table(tabla)
    if isinstance(datos, list):
        return datos
    if isinstance(datos, dict):
        columnas = list(datos)
        cantidad = max((len(datos[columna]) for columna in columnas), default=0)
        return [
            {
                columna: datos[columna][indice] if indice < len(datos[columna]) else None
                for columna in columnas
            }
            for indice in range(cantidad)
        ]
    raise TypeError(f"Formato inesperado en la tabla {tabla}: {type(datos).__name__}")


def _abrir_access_parser(ruta_mdb):
    clave = recuperar_clave_jet4(ruta_mdb)
    errores = []
    for nombre, password in (("con password", clave), ("sin password", None)):
        try:
            database = leer_con_access_parser(ruta_mdb, password=password)
            logging.info("MDB: lectura exitosa con access-parser %s", nombre)
            return database
        except Exception as exc:
            errores.append(f"{nombre}: {exc}")
            logging.warning("MDB: fallo access-parser %s: %s", nombre, exc)
    raise RuntimeError("; ".join(errores))


def _leer_evento_access_parser(ruta_mdb):
    database = _abrir_access_parser(ruta_mdb)
    meet_rows = _filas_access_parser(database, "Meet")
    if not meet_rows:
        raise RuntimeError("La tabla Meet no contiene informacion del evento.")
    return meet_rows[0], _filas_access_parser(database, "Team"), _filas_access_parser(database, "Event")


def _leer_evento_conexion(ruta_mdb):
    conexion = conectar_mdb(ruta_mdb, solo_lectura=True)
    try:
        cursor = conexion.cursor()
        meet = cursor.execute(
            "SELECT Meet_name1, Meet_start, Meet_end, Meet_location, Meet_course FROM Meet"
        ).fetchone()
        teams = cursor.execute(
            "SELECT Team_no, Team_name, Team_short, Team_abbr FROM Team WHERE Team_no > 0"
        ).fetchall()
        events = cursor.execute(
            "SELECT Event_ptr, Event_no, Event_dist, Event_stroke, Low_age, High_Age, Event_sex "
            "FROM Event WHERE Event_dist > 0"
        ).fetchall()
        return meet, teams, events
    finally:
        conexion.close()


def leer_evento_mdb(ruta_mdb: str | Path) -> dict:
    """Lee Meet, Team y Event sin modificar el archivo."""
    avisos = []
    try:
        try:
            meet, equipo_rows, evento_rows = _leer_evento_access_parser(ruta_mdb)
            equipo_rows = [row for row in equipo_rows if int(_valor(row, 0, "Team_no") or 0) > 0]
            evento_rows = [row for row in evento_rows if float(_valor(row, 2, "Event_dist") or 0) > 0]
        except Exception as raw_exc:
            logging.warning("MDB: access-parser no pudo leer las tablas requeridas: %s", raw_exc)
            try:
                meet, equipo_rows, evento_rows = _leer_evento_conexion(ruta_mdb)
            except Exception as exc:
                raise RuntimeError("El archivo no parece ser un MDB de Meet Manager.") from exc
        if meet is None:
            raise RuntimeError("La tabla Meet no contiene informacion del evento.")

        teams = []
        for row in equipo_rows:
            nombre = str(_valor(row, 1, "Team_name") or "Equipo sin nombre").strip()
            corto = str(_valor(row, 2, "Team_short") or "").strip()
            abbr = str(_valor(row, 3, "Team_abbr") or "").strip()
            teams.append({
                "code": int(_valor(row, 0, "Team_no")),
                "name": nombre,
                "short_name": corto or nombre.split()[0].upper()[:16],
                "abbreviation": abbr or _abreviar(nombre),
            })
        events = []
        for row in evento_rows:
            codigo_bruto = _valor(row, 3, "Event_stroke")
            try:
                codigo = int(codigo_bruto or 0)
            except (TypeError, ValueError):
                codigo = str(codigo_bruto or "?").strip().upper()
            estilo = STROKE_MAP.get(codigo)
            if estilo is None:
                estilo = f"Estilo {codigo}"
                avisos.append(f"El evento {_valor(row, 1, 'Event_no')} usa estilo desconocido {codigo}.")
            events.append({
                "event_ptr": int(_valor(row, 0, "Event_ptr")),
                "distance": int(_valor(row, 2, "Event_dist")),
                "style": estilo,
                "age_lo": int(_valor(row, 4, "Low_age") or 0),
                "age_hi": int(_valor(row, 5, "High_Age") or 0),
                "sex": SEX_MAP.get(str(_valor(row, 6, "Event_sex") or "X").strip().upper(), "X"),
            })
        inicio = _iso(_valor(meet, 1, "Meet_start"))
        return {
            "meet": {
                "name": str(_valor(meet, 0, "Meet_name1") or "Evento sin nombre").strip(),
                "date_start": inicio,
                "date_end": _iso(_valor(meet, 2, "Meet_end")) or inicio,
                "venue": str(_valor(meet, 3, "Meet_location") or "").strip(),
                "course": str(_valor(meet, 4, "Meet_course") or "S").strip().upper(),
                "reference_date": inicio,
            },
            "teams": teams,
            "events": events,
            "warnings": avisos,
        }
    except KeyError as exc:
        raise RuntimeError(f"Falta una columna requerida de Meet Manager: {exc}") from exc


def leer_indices_mdb(ruta_mdb: str | Path) -> dict:
    """Obtiene IDs existentes para validar una importacion."""
    try:
        database = _abrir_access_parser(ruta_mdb)
        teams = _filas_access_parser(database, "Team")
        athletes = _filas_access_parser(database, "Athlete")
        events = _filas_access_parser(database, "Event")
        entries = _filas_access_parser(database, "Entry")
        return {
            "teams": {int(_valor(row, 0, "Team_no")) for row in teams},
            "athletes": {int(_valor(row, 0, "Ath_no")) for row in athletes},
            "events": {int(_valor(row, 0, "Event_ptr")) for row in events},
            "entries": {
                (int(_valor(row, 0, "Event_ptr")), int(_valor(row, 1, "Ath_no")))
                for row in entries
            },
        }
    except Exception as exc:
        logging.warning("MDB: access-parser no pudo leer indices: %s", exc)
    conexion = conectar_mdb(ruta_mdb, solo_lectura=True)
    try:
        cursor = conexion.cursor()
        return {
            "teams": {int(row[0]) for row in cursor.execute("SELECT Team_no FROM Team").fetchall()},
            "athletes": {int(row[0]) for row in cursor.execute("SELECT Ath_no FROM Athlete").fetchall()},
            "events": {int(row[0]) for row in cursor.execute("SELECT Event_ptr FROM Event").fetchall()},
            "entries": {
                (int(row[0]), int(row[1]))
                for row in cursor.execute("SELECT Event_ptr, Ath_no FROM Entry").fetchall()
            },
        }
    finally:
        conexion.close()


def _abreviar(nombre: str) -> str:
    consonantes = "".join(c for c in nombre.upper() if c.isalpha() and c not in "AEIOUAEIOU")
    letras = consonantes or "".join(c for c in nombre.upper() if c.isalpha())
    return (letras[:3] or "EQP").ljust(3, "X")
