import unittest
from unittest.mock import Mock

from core.escribir_mdb import ATHLETE_FIELDS, _actualizar_atleta


class EscrituraIncrementalTests(unittest.TestCase):
    def test_actualiza_datos_sin_modificar_clave_del_nadador(self):
        cursor = Mock()
        atleta = {field: f"valor-{field}" for field in ATHLETE_FIELDS}
        atleta["Ath_no"] = 6001

        _actualizar_atleta(cursor, atleta)

        sql, *valores = cursor.execute.call_args.args
        self.assertTrue(sql.startswith("UPDATE [Athlete] SET"))
        self.assertNotIn("[Ath_no] = ?", sql.split("WHERE", 1)[0])
        self.assertEqual(sql.rsplit("WHERE", 1)[1].strip(), "[Ath_no] = ?")
        self.assertEqual(valores[-1], 6001)
        self.assertEqual(len(valores), len(ATHLETE_FIELDS))


if __name__ == "__main__":
    unittest.main()
