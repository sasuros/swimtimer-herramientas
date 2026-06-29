"""Generacion del archivo config_evento consumido por la web."""

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


def generar_config(datos_mdb: dict, ahora: datetime | None = None) -> dict:
    ahora = ahora or datetime.now(timezone.utc)
    return {
        "source": "Meet Manager",
        "source_version": "2.0",
        "exported_at": ahora.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "meet": dict(datos_mdb["meet"]),
        "teams": list(datos_mdb.get("teams", [])),
        "events": list(datos_mdb.get("events", [])),
    }


def nombre_config_sugerido(nombre_evento: str) -> str:
    texto = unicodedata.normalize("NFKD", nombre_evento).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_") or "evento"
    return f"config_evento_{slug}.json"


def guardar_config(config: dict, ruta: str | Path) -> None:
    Path(ruta).write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

