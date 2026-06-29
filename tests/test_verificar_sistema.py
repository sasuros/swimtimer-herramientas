import unittest
from unittest.mock import Mock, patch

from core.verificar_sistema import formatear_resultados, verificar_sistema
from gui.app import SwimtimerApp


class _PyodbcSinAccess:
    @staticmethod
    def drivers():
        return ["SQL Server"]


class VerificarSistemaTests(unittest.TestCase):
    def test_detecta_ausencia_del_driver_access(self):
        with patch.dict("sys.modules", {"pyodbc": _PyodbcSinAccess()}):
            resultados, _, puede_importar = verificar_sistema()

        driver = next(item for item in resultados if item[0] == "Driver Access (ODBC)")
        self.assertFalse(driver[1])
        self.assertFalse(puede_importar)

    def test_formatea_resumen_para_cli_y_gui(self):
        texto = formatear_resultados(
            [("Driver Access (ODBC)", False, "NO ENCONTRADO")], True, False
        )
        self.assertIn("Exportar evento: LISTO", texto)
        self.assertIn("Importar inscripciones: REQUIERE DRIVER ACCESS", texto)

    def test_muestra_banner_si_falta_driver(self):
        app = object.__new__(SwimtimerApp)
        app._mostrar_aviso_driver = Mock()
        with patch("gui.app.verificar_sistema", return_value=([], True, False)):
            app._verificar_al_iniciar()
        app._mostrar_aviso_driver.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
