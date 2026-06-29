import unittest
from unittest.mock import Mock, patch

from gui.estilos import (MUTED, PRIMARY, WHITE, boton_primario,
                         configurar_boton_primario)


class EstilosTests(unittest.TestCase):
    def test_boton_primario_define_estado_habilitado_y_deshabilitado(self):
        with patch("gui.estilos.tk.Button", return_value="boton") as button:
            resultado = boton_primario("padre", "ACCION", lambda: None, state="disabled")

        self.assertEqual(resultado, "boton")
        opciones = button.call_args.kwargs
        self.assertEqual(opciones["bg"], MUTED)
        self.assertEqual(opciones["fg"], WHITE)
        self.assertEqual(opciones["pady"], 14)
        self.assertEqual(opciones["state"], "disabled")

    def test_configura_color_y_estado_al_habilitar(self):
        boton = Mock()
        configurar_boton_primario(boton, True)
        boton.config.assert_called_once_with(state="normal", bg=PRIMARY)


if __name__ == "__main__":
    unittest.main()
