import unittest

from core.leer_mdb import (
    _normalizar_course,
    _normalizar_sex,
    _normalizar_stroke,
)


class MapeosMDBTests(unittest.TestCase):
    def test_strokes_numericos_y_letras(self):
        self.assertEqual(_normalizar_stroke(1)[0], "Crawl")
        self.assertEqual(_normalizar_stroke(6)[0], "Crawl")
        self.assertEqual(_normalizar_stroke("A")[0], "Crawl")
        self.assertEqual(_normalizar_stroke("e")[0], "Comb. Individual")

    def test_strokes_texto_sin_distinguir_mayusculas(self):
        self.assertEqual(_normalizar_stroke("Breaststroke")[0], "Pecho")
        self.assertEqual(_normalizar_stroke("individual medley")[0], "Comb. Individual")
        self.assertEqual(_normalizar_stroke("Freestyle Relay")[0], "Relevo Crawl")

    def test_stroke_desconocido_conserva_original(self):
        estilo, original = _normalizar_stroke("Especial Local")
        self.assertIsNone(estilo)
        self.assertEqual(original, "Especial Local")

    def test_sex_mm2_y_compatibilidad_mm3(self):
        self.assertEqual(_normalizar_sex("X"), "F")
        self.assertEqual(_normalizar_sex("B"), "X")
        self.assertEqual(_normalizar_sex("S"), "F")
        self.assertEqual(_normalizar_sex("H"), "M")
        self.assertEqual(_normalizar_sex("G"), "F")

    def test_course_numerico_y_letra(self):
        self.assertEqual(_normalizar_course(1), "Y")
        self.assertEqual(_normalizar_course("2"), "S")
        self.assertEqual(_normalizar_course("3"), "L")
        self.assertEqual(_normalizar_course("s"), "S")


if __name__ == "__main__":
    unittest.main()
