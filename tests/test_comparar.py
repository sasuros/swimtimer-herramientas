import unittest

from core.comparar import comparar_por_club


def atleta(ath_no, apellido, nombre="Ana", team=6):
    return {
        "Ath_no": ath_no, "Last_name": apellido, "First_name": nombre,
        "Ath_Sex": "F", "Birth_date": "2014-01-02", "Team_no": team,
        "Ath_age": 12, "Comp_no": ath_no,
    }


class ComparacionTests(unittest.TestCase):
    def test_clasifica_cambios_por_club(self):
        datos = {
            "teams": [{"Team_no": 6, "Team_name": "Mantarrayas"}],
            "athletes": [
                atleta(6001, "Igual"),
                atleta(6002, "Corregido"),
                atleta(6004, "Nuevo"),
            ],
        }
        indices = {"athlete_records": [
            atleta(6001, "Igual"),
            atleta(6002, "Anterior"),
            atleta(6003, "Eliminado"),
        ]}

        result = comparar_por_club(datos, indices)
        club = result["clubs"][0]
        self.assertEqual([item["Ath_no"] for item in club["unchanged"]], [6001])
        self.assertEqual([item["Ath_no"] for item in club["new"]], [6004])
        self.assertEqual([item["Ath_no"] for item in club["removed"]], [6003])
        self.assertEqual([item["Ath_no"] for item in club["modified"]], [6002])
        self.assertEqual(club["modified"][0]["changed_labels"], ["apellido"])
        self.assertEqual(result["modified_ids"], {6002})
        self.assertEqual(result["removed"][0]["Team_name"], "Mantarrayas")

    def test_primera_importacion_no_genera_comparacion(self):
        result = comparar_por_club({"teams": [], "athletes": []}, {"athlete_records": []})
        self.assertFalse(result["has_previous_data"])
        self.assertEqual(result["clubs"], [])


if __name__ == "__main__":
    unittest.main()
