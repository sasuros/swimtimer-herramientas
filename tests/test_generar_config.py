import unittest
from datetime import datetime, timezone

from core.generar_config import generar_config, nombre_config_sugerido


class ConfigTests(unittest.TestCase):
    def test_formato_web(self):
        datos = {"meet": {"name": "Copa", "date_start": "2026-12-15"},
                 "teams": [{"code": 6}], "events": [{"event_ptr": 1}]}
        result = generar_config(datos, datetime(2026, 12, 1, 10, tzinfo=timezone.utc))
        self.assertEqual(result["source"], "Meet Manager")
        self.assertEqual(result["source_version"], "2.0")
        self.assertEqual(result["exported_at"], "2026-12-01T10:00:00Z")

    def test_nombre_sugerido_sin_acentos(self):
        self.assertEqual(nombre_config_sugerido("V Copa Navidad 2026"),
                         "config_evento_v_copa_navidad_2026.json")


if __name__ == "__main__":
    unittest.main()

