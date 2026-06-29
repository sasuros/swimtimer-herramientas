import tempfile
import unittest
from pathlib import Path

from core.jet4 import (
    JET4_XOR_MASK,
    TemporaryDecryptedConnection,
    recuperar_clave_jet4,
)


class _FakeConnection:
    def __init__(self):
        self.committed = self.rolled_back = self.closed = False

    def commit(self): self.committed = True
    def rollback(self): self.rolled_back = True
    def close(self): self.closed = True


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

    def test_temporal_restaura_cabecera_y_reemplaza_original(self):
        header = bytes(range(32))
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "evento.mdb"
            temporary = Path(tmp) / "temporal.mdb"
            original.write_bytes(b"original")
            temporary.write_bytes(bytearray(0x42) + bytearray(32) + b"datos")
            inner = _FakeConnection()
            connection = TemporaryDecryptedConnection(inner, original, temporary, header)
            connection.commit()
            contenido = original.read_bytes()
            self.assertEqual(contenido[0x42:0x62], header)
            self.assertTrue(inner.committed)
            self.assertTrue(inner.closed)
            self.assertFalse(temporary.exists())


if __name__ == "__main__":
    unittest.main()
