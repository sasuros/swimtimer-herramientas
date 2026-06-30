"""Comparacion de una inscripcion JSON contra los datos actuales del MDB."""

from datetime import date, datetime


COMPARISON_FIELDS = [
    "Last_name", "First_name", "Initial", "Ath_Sex", "Birth_date", "Team_no",
    "Schl_yr", "Ath_age", "Reg_no", "Ath_stat", "Div_no", "Comp_no",
    "Pref_name", "Home_addr1", "Home_addr2", "Home_city", "Home_prov",
    "Home_statenew", "Home_zip", "Home_cntry", "Home_daytele", "Home_evetele",
    "Home_email", "Citizen_of", "second_club", "Home_celltele", "bcssa_type",
]

FIELD_LABELS = {
    "Last_name": "apellido", "First_name": "nombre", "Initial": "inicial",
    "Ath_Sex": "sexo", "Birth_date": "fecha de nacimiento", "Team_no": "club",
    "Schl_yr": "año escolar", "Ath_age": "edad", "Reg_no": "registro",
    "Ath_stat": "estado", "Div_no": "división", "Comp_no": "competidor",
    "Pref_name": "nombre preferido", "Home_addr1": "dirección",
    "Home_addr2": "dirección", "Home_city": "ciudad", "Home_prov": "estado",
    "Home_statenew": "estado", "Home_zip": "código postal",
    "Home_cntry": "país", "Home_daytele": "teléfono", "Home_evetele": "teléfono",
    "Home_email": "correo", "Citizen_of": "nacionalidad",
    "second_club": "segundo club", "Home_celltele": "celular", "bcssa_type": "tipo",
}


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _normalizar(valor):
    if valor in (None, ""):
        return ""
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()[:10]
    if isinstance(valor, str):
        texto = valor.strip()
        if len(texto) >= 10 and texto[4:5] == "-" and texto[7:8] == "-":
            return texto[:10]
        return texto.casefold()
    return valor


def _cambios(actual, nuevo):
    return [
        campo for campo in COMPARISON_FIELDS
        if _normalizar(actual.get(campo)) != _normalizar(nuevo.get(campo))
    ]


def comparar_por_club(datos: dict, indices: dict) -> dict:
    """Clasifica nadadores sin cambios, nuevos, eliminados y modificados."""
    existentes = indices.get("athlete_records") or []
    if not existentes:
        return {"has_previous_data": False, "clubs": [], "removed": [], "modified_ids": set()}

    equipos = {
        _entero(team.get("Team_no")): team.get("Team_name") or f"Club #{team.get('Team_no')}"
        for team in datos.get("teams") or []
    }
    json_por_club = {}
    for atleta in datos.get("athletes") or []:
        json_por_club.setdefault(_entero(atleta.get("Team_no")), []).append(atleta)
    mdb_por_club = {}
    for atleta in existentes:
        mdb_por_club.setdefault(_entero(atleta.get("Team_no")), []).append(atleta)

    clubes = []
    eliminados = []
    modificados_ids = set()
    for team_no in sorted(set(equipos) & set(mdb_por_club)):
        json_map = {_entero(item.get("Ath_no")): item for item in json_por_club.get(team_no, [])}
        mdb_map = {_entero(item.get("Ath_no")): item for item in mdb_por_club.get(team_no, [])}
        comunes = set(json_map) & set(mdb_map)
        modificados = []
        sin_cambios = []
        for ath_no in sorted(comunes):
            campos = _cambios(mdb_map[ath_no], json_map[ath_no])
            if campos:
                item = {**json_map[ath_no], "changed_fields": campos,
                        "changed_labels": [FIELD_LABELS.get(campo, campo) for campo in campos]}
                modificados.append(item)
                modificados_ids.add(ath_no)
            else:
                sin_cambios.append(json_map[ath_no])
        nuevos = [json_map[key] for key in sorted(set(json_map) - set(mdb_map))]
        removidos = [mdb_map[key] for key in sorted(set(mdb_map) - set(json_map))]
        eliminados.extend({**item, "Team_name": equipos[team_no]} for item in removidos)
        clubes.append({
            "Team_no": team_no,
            "Team_name": equipos[team_no],
            "unchanged": sin_cambios,
            "new": nuevos,
            "removed": removidos,
            "modified": modificados,
        })
    return {
        "has_previous_data": True,
        "clubs": clubes,
        "removed": eliminados,
        "modified_ids": modificados_ids,
    }
