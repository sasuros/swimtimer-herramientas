import json
import tempfile
import unittest
from pathlib import Path

from core.leer_consolidado import ErrorConsolidado, calcular_sha256, leer_consolidado
from core.validaciones import validar_importacion


def ejemplo():
    datos = {
        "meta": {"version": "2.0", "type": "principal", "sha256": ""},
        "meet": {},
        "teams": [{"Team_no": 6, "Team_name": "Mantarrayas"}],
        "athletes": [{"Ath_no": 6001, "Last_name": "Perez", "First_name": "Ana",
                      "Ath_Sex": "F", "Team_no": 6}],
        "results": [{"Event_ptr": 1, "Ath_no": 6001}],
    }
    datos["meta"]["sha256"] = calcular_sha256(datos)
    return datos


class ConsolidadoTests(unittest.TestCase):
    def _archivo(self, datos, tmp):
        ruta = Path(tmp) / "consolidado.json"
        ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
        return ruta

    def test_verifica_sha_y_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            datos = leer_consolidado(self._archivo(ejemplo(), tmp))
            self.assertTrue(datos["_validation"]["sha256_verified"])

    def test_detecta_modificacion(self):
        datos = ejemplo(); datos["athletes"][0]["First_name"] = "Eva"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ErrorConsolidado, "SHA-256"):
                leer_consolidado(self._archivo(datos, tmp))

    def test_acepta_legacy_v1_sin_hash(self):
        datos = ejemplo(); datos["meta"] = {"version": "1.0"}
        with tempfile.TemporaryDirectory() as tmp:
            result = leer_consolidado(self._archivo(datos, tmp))
            self.assertFalse(result["_validation"]["sha256_verified"])

    def test_validacion_eventos_y_duplicados(self):
        datos = ejemplo(); datos["results"].append(dict(datos["results"][0]))
        indices = {"teams": {6}, "athletes": set(), "events": {2}, "entries": set()}
        result = validar_importacion(datos, indices)
        self.assertFalse(result["ok"])
        self.assertTrue(any("no existe" in e for e in result["errors"]))
        self.assertTrue(any("duplicada" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()

