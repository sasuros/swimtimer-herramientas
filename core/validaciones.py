"""Reglas de integridad previas a escribir un archivo Meet Manager."""


def resumen_incremental(datos: dict, indices: dict) -> dict:
    """Cuenta registros nuevos y existentes usando las claves de Meet Manager."""
    atletas_existentes = indices.get("athletes", set())
    entradas_existentes = indices.get("entries", set())
    atletas = datos.get("athletes") or []
    resultados = datos.get("results") or []
    atletas_ya_existen = sum(
        1 for atleta in atletas
        if _entero(atleta.get("Ath_no")) in atletas_existentes
    )
    inscripciones_ya_existen = sum(
        1 for resultado in resultados
        if (_entero(resultado.get("Event_ptr")), _entero(resultado.get("Ath_no")))
        in entradas_existentes
    )
    return {
        "athletes_total": len(atletas),
        "athletes_new": len(atletas) - atletas_ya_existen,
        "athletes_existing": atletas_ya_existen,
        "entries_total": len(resultados),
        "entries_new": len(resultados) - inscripciones_ya_existen,
        "entries_existing": inscripciones_ya_existen,
    }


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def validar_importacion(datos: dict, indices: dict) -> dict:
    errores, avisos = [], []
    teams = datos.get("teams") or []
    athletes = datos.get("athletes") or []
    results = datos.get("results") or []
    team_json = {int(t.get("Team_no")) for t in teams if t.get("Team_no") not in (None, "")}
    atletas_json, entradas_json = set(), set()
    for pos, atleta in enumerate(athletes, 1):
        faltan = [c for c in ("Last_name", "First_name", "Ath_Sex", "Team_no") if atleta.get(c) in (None, "")]
        if faltan:
            errores.append(f"Nadador {pos}: faltan {', '.join(faltan)}.")
        try:
            ath_no = int(atleta.get("Ath_no"))
            team_no = int(atleta.get("Team_no"))
        except (TypeError, ValueError):
            errores.append(f"Nadador {pos}: Ath_no o Team_no invalido.")
            continue
        if ath_no in atletas_json:
            errores.append(f"Ath_no duplicado en JSON: {ath_no}.")
        atletas_json.add(ath_no)
        if team_no not in team_json and team_no not in indices.get("teams", set()):
            errores.append(f"El equipo {team_no} del nadador {ath_no} no esta definido.")
        if ath_no in indices.get("athletes", set()):
            avisos.append(f"El nadador {ath_no} ya existe y se omitira.")
    nuevos = team_json - indices.get("teams", set())
    if nuevos:
        avisos.append(f"Se insertaran {len(nuevos)} equipos nuevos.")
    for pos, resultado in enumerate(results, 1):
        try:
            clave = (int(resultado.get("Event_ptr")), int(resultado.get("Ath_no")))
        except (TypeError, ValueError):
            errores.append(f"Inscripcion {pos}: Event_ptr o Ath_no invalido.")
            continue
        if clave[1] not in atletas_json and clave[1] not in indices.get("athletes", set()):
            errores.append(f"La inscripcion {pos} refiere al nadador inexistente {clave[1]}.")
        if clave[0] not in indices.get("events", set()):
            errores.append(f"El Event_ptr {clave[0]} no existe en el MDB destino.")
        if clave in entradas_json:
            errores.append(f"Inscripcion duplicada en JSON: evento {clave[0]}, nadador {clave[1]}.")
        entradas_json.add(clave)
        if clave in indices.get("entries", set()):
            avisos.append(f"La inscripcion evento {clave[0]} / nadador {clave[1]} ya existe y se omitira.")
    return {
        "ok": not errores,
        "errors": errores,
        "warnings": avisos,
        "incremental": resumen_incremental(datos, indices),
    }
