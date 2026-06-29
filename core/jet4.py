"""Acceso seguro a archivos Microsoft Jet 4 de Meet Manager."""

import logging
import os
import shutil
import struct
import tempfile
from pathlib import Path

ACCESS_ENGINE_URL = "https://www.microsoft.com/en-us/download/details.aspx?id=54920"
JET4_XOR_MASK = bytes([
    0x86, 0xFB, 0xEC, 0x37, 0x5D, 0x44, 0x9C, 0xFA,
    0xC6, 0x5E, 0x28, 0xE6, 0x13, 0xB6, 0x8A, 0x60,
    0x54, 0x94, 0x7B, 0x36, 0xF5, 0x72, 0xDF, 0xB1,
    0x77, 0x68, 0xB6, 0xE3, 0x11, 0x37, 0x12, 0x09,
])
JET4_XOR_WORDS = (
    0x6ABA, 0x37EC, 0xD561, 0xFA9C, 0xCFFA, 0xE628, 0x272F, 0x608A,
    0x0568, 0x367B, 0xE3C9, 0xB1DF, 0x654B, 0x4313, 0x3EF3, 0x33B1,
    0xF008, 0x5B79, 0x24AE, 0x2A7C,
)
DAO_DB_FAIL_ON_ERROR = 128


class DAOCursor:
    """Cursor minimo sobre DAO compatible con el uso que hace la aplicacion."""

    def __init__(self, connection):
        self.connection = connection
        self._rows = []
        self._position = 0

    def execute(self, sql, *params):
        dao_sql = sql
        for index in range(len(params)):
            dao_sql = dao_sql.replace("?", f"[p{index}]", 1)
        query = self.connection._database.CreateQueryDef("", dao_sql)
        try:
            for index, value in enumerate(params):
                query.Parameters.Item(f"p{index}").Value = value
            if sql.lstrip().upper().startswith("SELECT"):
                recordset = query.OpenRecordset()
                try:
                    self._rows = self._read_rows(recordset)
                finally:
                    recordset.Close()
            else:
                query.Execute(DAO_DB_FAIL_ON_ERROR)
                self._rows = []
            self._position = 0
            return self
        finally:
            query.Close()

    @staticmethod
    def _read_rows(recordset):
        rows = []
        field_count = int(recordset.Fields.Count)
        while not recordset.EOF:
            rows.append(tuple(recordset.Fields.Item(i).Value for i in range(field_count)))
            recordset.MoveNext()
        return rows

    def fetchone(self):
        if self._position >= len(self._rows):
            return None
        row = self._rows[self._position]
        self._position += 1
        return row

    def fetchall(self):
        rows = self._rows[self._position:]
        self._position = len(self._rows)
        return rows


class DAOConnection:
    """Adapta DAO.DBEngine.120 al subconjunto de la API de pyodbc usado aqui."""

    def __init__(self, engine, database, solo_lectura=False, pythoncom_module=None):
        self._engine = engine
        self._database = database
        self._pythoncom = pythoncom_module
        self._workspace = engine.Workspaces.Item(0)
        self._transaction_active = False
        if not solo_lectura:
            self._workspace.BeginTrans()
            self._transaction_active = True

    def cursor(self):
        return DAOCursor(self)

    def commit(self):
        if self._transaction_active:
            self._workspace.CommitTrans()
            self._transaction_active = False

    def rollback(self):
        if self._transaction_active:
            self._workspace.Rollback()
            self._transaction_active = False

    def close(self):
        try:
            if self._transaction_active:
                self._workspace.Rollback()
                self._transaction_active = False
            self._database.Close()
        finally:
            if self._pythoncom is not None:
                self._pythoncom.CoUninitialize()
                self._pythoncom = None


class TemporaryDecryptedConnection:
    """Publica un MDB temporal solo despues de commit exitoso."""

    def __init__(self, connection, original_path, temporary_path, encrypted_header):
        self._connection = connection
        self._original_path = Path(original_path)
        self._temporary_path = Path(temporary_path)
        self._encrypted_header = encrypted_header
        self._finished = False
        self._connection_closed = False

    def cursor(self):
        return self._connection.cursor()

    def commit(self):
        self._connection.commit()
        self._connection.close()
        self._connection_closed = True
        with self._temporary_path.open("r+b") as archivo:
            archivo.seek(0x42)
            archivo.write(self._encrypted_header)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(self._temporary_path, self._original_path)
        self._finished = True
        logging.info("MDB: temporal confirmado y encriptacion restaurada")

    def rollback(self):
        if self._finished:
            return
        try:
            if not self._connection_closed:
                self._connection.rollback()
        finally:
            if not self._connection_closed:
                self._connection.close()
                self._connection_closed = True
            self._temporary_path.unlink(missing_ok=True)
            self._finished = True

    def close(self):
        if not self._finished:
            self.rollback()


def recuperar_clave_jet4(ruta_mdb: str | Path) -> str:
    """Recupera la clave almacenada en los bytes 0x42-0x61 del MDB."""
    ruta = Path(ruta_mdb)
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el archivo: {ruta}")
    if ruta.stat().st_size < 0x42 + len(JET4_XOR_MASK):
        raise ValueError("El archivo es demasiado pequeno para ser un MDB Jet 4 valido.")
    with ruta.open("rb") as archivo:
        cabecera = archivo.read(4096)
    # Hy-Tek usa la codificacion Jet 4 por palabras UTF-16 en MDB reales.
    if len(cabecera) >= 4096 and cabecera[:4] == b"\x00\x01\x00\x00" and cabecera[20] == 1:
        cifrada_words = struct.unpack_from("<20H", cabecera, 0x42)
        mascara_alta = (struct.unpack_from("<H", cabecera, 0x66)[0] ^ JET4_XOR_WORDS[18]) & 0xFF00
        caracteres = []
        for indice, valor in enumerate(cifrada_words):
            claro = valor ^ JET4_XOR_WORDS[indice]
            if claro >= 256:
                claro ^= mascara_alta
            if claro == 0:
                break
            caracteres.append(chr(claro))
        return "".join(caracteres)
    cifrada = cabecera[0x42:0x42 + len(JET4_XOR_MASK)]
    if len(cifrada) != len(JET4_XOR_MASK):
        raise ValueError("No se pudo leer la cabecera de seguridad del MDB.")
    clara = bytes(valor ^ mascara for valor, mascara in zip(cifrada, JET4_XOR_MASK))
    return clara.replace(b"\x00", b"").decode("latin-1").rstrip("\x00")


def conectar_mdb(ruta_mdb: str | Path, solo_lectura: bool = False):
    """Abre el MDB probando ODBC y luego DAO, de menor a mayor compatibilidad."""
    ruta = Path(ruta_mdb).resolve()
    clave = recuperar_clave_jet4(ruta)
    errores = []

    try:
        import pyodbc
    except ImportError:
        pyodbc = None

    driver = "Microsoft Access Driver (*.mdb, *.accdb)"
    if pyodbc is not None and driver in set(pyodbc.drivers()):
        base = f"DRIVER={{{driver}}};DBQ={ruta};"
        estrategias_odbc = [
            ("pyodbc sin password", base),
            ("pyodbc con PWD", base + f"PWD={clave};"),
            ("pyodbc con Jet OLEDB Password", base + f"Jet OLEDB:Database Password={clave};"),
        ]
        for nombre, connection_string in estrategias_odbc:
            if solo_lectura:
                connection_string += "READONLY=TRUE;"
            try:
                conexion = pyodbc.connect(
                    connection_string, autocommit=False, timeout=10
                )
                logging.info("MDB: conexion exitosa con %s", nombre)
                return conexion
            except pyodbc.Error as exc:
                errores.append(f"{nombre}: {exc}")
                logging.warning("MDB: fallo %s: %s", nombre, exc)
    else:
        errores.append("pyodbc: driver Microsoft Access no disponible")

    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        errores.append(f"DAO: pywin32 no esta instalado ({exc})")
    else:
        pythoncom.CoInitialize()
        com_inicializado = True
        for nombre, connect in (
            ("DAO con password", ";PWD=" + clave),
            ("DAO sin password", ""),
        ):
            database = None
            try:
                engine = win32com.client.Dispatch("DAO.DBEngine.120")
                database = engine.OpenDatabase(str(ruta), False, solo_lectura, connect)
                conexion = DAOConnection(
                    engine, database, solo_lectura, pythoncom_module=pythoncom
                )
                com_inicializado = False
                logging.info("MDB: conexion exitosa con %s", nombre)
                return conexion
            except Exception as exc:
                if database is not None:
                    try:
                        database.Close()
                    except Exception:
                        pass
                errores.append(f"{nombre}: {exc}")
                logging.warning("MDB: fallo %s: %s", nombre, exc)
        if com_inicializado:
            pythoncom.CoUninitialize()

    raise RuntimeError(
        "No se pudo abrir el archivo con ODBC ni DAO. Cierra Meet Manager e intenta de nuevo.\n"
        "Verifica que Microsoft Access Database Engine y pywin32 esten instalados.\n"
        f"Access Engine: {ACCESS_ENGINE_URL}\n\n" + "\n".join(errores)
    )


def conectar_mdb_temporal_sin_clave(ruta_mdb: str | Path):
    """Ultimo recurso de escritura: trabaja en una copia con clave de cabecera vacia."""
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("La estrategia temporal requiere pyodbc.") from exc

    original = Path(ruta_mdb).resolve()
    with original.open("rb") as archivo:
        archivo.seek(0x42)
        encrypted_header = archivo.read(len(JET4_XOR_MASK))
    if len(encrypted_header) != len(JET4_XOR_MASK):
        raise RuntimeError("No se pudo leer la cabecera de seguridad del MDB.")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{original.stem}_swimtimer_", suffix=original.suffix, dir=original.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    connection = None
    try:
        shutil.copy2(original, temporary)
        with temporary.open("r+b") as archivo:
            archivo.seek(0x42)
            archivo.write(JET4_XOR_MASK)
            archivo.flush()
            os.fsync(archivo.fileno())

        driver = "Microsoft Access Driver (*.mdb, *.accdb)"
        if driver not in set(pyodbc.drivers()):
            raise RuntimeError("No esta instalado el driver Microsoft Access.")
        connection = pyodbc.connect(
            f"DRIVER={{{driver}}};DBQ={temporary};",
            autocommit=False,
            timeout=10,
        )
        logging.info("MDB: conexion de escritura con temporal sin clave")
        return TemporaryDecryptedConnection(
            connection, original, temporary, encrypted_header
        )
    except Exception:
        if connection is not None:
            connection.close()
        temporary.unlink(missing_ok=True)
        raise
