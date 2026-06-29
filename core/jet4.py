"""Acceso seguro a archivos Microsoft Jet 4 de Meet Manager."""

import struct
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
    """Abre el MDB con el primer controlador Access compatible disponible."""
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("Falta pyodbc. Ejecuta: pip install -r requirements.txt") from exc

    ruta = Path(ruta_mdb).resolve()
    clave = recuperar_clave_jet4(ruta)
    candidatos = [
        "Microsoft Access Driver (*.mdb, *.accdb)",
        "Microsoft Access Driver (*.mdb)",
    ]
    disponibles = set(pyodbc.drivers())
    instalados = [driver for driver in candidatos if driver in disponibles]
    if not instalados:
        raise RuntimeError(
            "El driver de Microsoft Access no esta instalado.\n"
            f"Descargalo de: {ACCESS_ENGINE_URL}"
        )
    errores = []
    for driver in instalados:
        partes = [f"DRIVER={{{driver}}};", f"DBQ={ruta};", f"PWD={clave};"]
        if solo_lectura:
            partes.append("READONLY=TRUE;")
        try:
            return pyodbc.connect("".join(partes), autocommit=False, timeout=10)
        except pyodbc.Error as exc:
            errores.append(str(exc))
    raise RuntimeError(
        "No se pudo abrir el archivo. Cierra Meet Manager e intenta de nuevo.\n"
        + (errores[-1] if errores else "Error desconocido de Access.")
    )
