import unittest
from unittest.mock import Mock, call

from core.escribir_mdb import ATHLETE_FIELDS, _actualizar_atleta, _eliminar_atleta


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

    def test_elimina_entries_antes_del_nadador(self):
        cursor = Mock()
        count_result = Mock(); count_result.fetchone.return_value = (5,)
        athlete_result = Mock(); athlete_result.fetchone.return_value = (6001,)
        cursor.execute.side_effect = [count_result, athlete_result, cursor, cursor]

        self.assertEqual(_eliminar_atleta(cursor, 6001), (1, 5))
        self.assertEqual(cursor.execute.call_args_list, [
            call("SELECT COUNT(*) FROM Entry WHERE Ath_no = ?", 6001),
            call("SELECT Ath_no FROM Athlete WHERE Ath_no = ?", 6001),
            call("DELETE FROM Entry WHERE Ath_no = ?", 6001),
            call("DELETE FROM Athlete WHERE Ath_no = ?", 6001),
        ])


if __name__ == "__main__":
    unittest.main()
