import tempfile
import unittest
from pathlib import Path

from core.jet4 import JET4_XOR_MASK, recuperar_clave_jet4


class Jet4Tests(unittest.TestCase):
    def test_recupera_clave_latin1(self):
        clave = "Natacion2026-n"
        clara = clave.encode("latin-1").ljust(32, b"\0")
        cabecera = bytearray(0x42) + bytearray(a ^ b for a, b in zip(clara, JET4_XOR_MASK))
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "evento.mdb"
            ruta.write_bytes(cabecera)
            self.assertEqual(recuperar_clave_jet4(ruta), clave)

    def test_rechaza_archivo_corto(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "corto.mdb"; ruta.write_bytes(b"MDB")
            with self.assertRaisesRegex(ValueError, "demasiado pequeno"):
                recuperar_clave_jet4(ruta)


if __name__ == "__main__":
    unittest.main()

