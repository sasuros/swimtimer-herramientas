"""Lectura y verificacion del consolidado exportado por la web."""

import copy
import hashlib
import json
from pathlib import Path


class ErrorConsolidado(ValueError):
    pass


def calcular_sha256(datos: dict) -> str:
    copia = copy.deepcopy(datos)
    copia.setdefault("meta", {})["sha256"] = ""
    compacto = json.dumps(copia, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(compacto.encode("utf-8")).hexdigest()


def leer_consolidado(ruta: str | Path) -> dict:
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ErrorConsolidado(f"No se pudo leer el JSON: {exc}") from exc
    if not isinstance(datos, dict):
        raise ErrorConsolidado("El JSON debe contener un objeto principal.")
    meta = datos.get("meta") or {}
    version = str(meta.get("version") or "1.0")
    if version.split(".", 1)[0] not in {"1", "2"}:
        raise ErrorConsolidado(f"Version no compatible: {version}")
    for clave in ("athletes", "results"):
        if not isinstance(datos.get(clave), list):
            raise ErrorConsolidado(f"Falta la lista obligatoria '{clave}'.")
    esperado = str(meta.get("sha256") or "")
    verificado = False
    if version.startswith("2"):
        if not esperado:
            raise ErrorConsolidado("El consolidado 2.x no contiene SHA-256.")
        obtenido = calcular_sha256(datos)
        if obtenido.lower() != esperado.lower():
            raise ErrorConsolidado("El SHA-256 no coincide. El archivo pudo ser modificado.")
        verificado = True
    datos["_validation"] = {"version": version, "sha256_verified": verificado}
    return datos

