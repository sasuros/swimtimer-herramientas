import unittest

from gui.drop_zone import extraer_ruta_drop


class _Tk:
    @staticmethod
    def splitlist(value):
        if value.startswith("{"):
            return (value.strip("{}"),)
        return tuple(value.split())


class _Widget:
    tk = _Tk()


class DropZoneTests(unittest.TestCase):
    def test_extrae_ruta_con_espacios(self):
        path = extraer_ruta_drop(_Widget(), r"{C:\Mis eventos\copa 68.mdb}")
        self.assertEqual(str(path), r"C:\Mis eventos\copa 68.mdb")


if __name__ == "__main__":
    unittest.main()
