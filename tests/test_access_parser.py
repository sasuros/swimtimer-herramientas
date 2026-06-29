import unittest

from core.leer_mdb import _filas_access_parser, _valor


class _Database:
    def parse_table(self, _name):
        return {"Team_no": [1, 2], "Team_name": ["Uno", "Dos"]}


class AccessParserTests(unittest.TestCase):
    def test_normaliza_formato_columnar(self):
        rows = _filas_access_parser(_Database(), "Team")
        self.assertEqual(rows, [
            {"Team_no": 1, "Team_name": "Uno"},
            {"Team_no": 2, "Team_name": "Dos"},
        ])

    def test_valor_diccionario_no_distingue_mayusculas(self):
        self.assertEqual(_valor({"team_NO": 7}, 0, "Team_no"), 7)


if __name__ == "__main__":
    unittest.main()
