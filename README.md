# SWIMTIMER Herramientas

Aplicacion de escritorio para conectar Hy-Tek Meet Manager con SWIMTIMER Inscripciones:

- Exporta un evento de `.mdb` a `config_evento.json`.
- Importa el consolidado de la web a las tablas `Team`, `Athlete` y `Entry`.
- Crea siempre un backup del `.mdb` antes de escribir.
- Valida version, SHA-256, referencias y duplicados.

## Requisitos

- Windows 10 u 11 y Python 3.8 o posterior.
- Microsoft Access Database Engine, con la misma arquitectura (32/64 bits) que Python.
  Descarga oficial: https://www.microsoft.com/en-us/download/details.aspx?id=54920
- `pywin32`, que habilita la conexion DAO compatible con archivos Jet 4 protegidos.
- `access-parser`, usado para leer directamente archivos Jet 3/Access 97 sin ODBC.
- `tkinterdnd2`, usado para arrastrar archivos desde el Explorador de Windows.

Instalacion individual, si fuera necesaria:

```powershell
pip install pywin32
pip install access-parser
pip install tkinterdnd2
```

## Desarrollo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python swimtimer_herramientas.py
```

Pruebas:

```powershell
python -m unittest discover -s tests -v
```

## Generar el ejecutable

Desde el explorador, haz doble click en `build\build_exe.bat`, o ejecuta:

```powershell
.\build\build_exe.bat
```

El resultado queda en `dist\SWIMTIMER Herramientas.exe`. El ejecutable es portable,
pero el equipo destino necesita el controlador de Access para abrir archivos `.mdb`.

Para exportar, la aplicacion intenta primero `access-parser` y cae a ODBC/DAO si una
tabla no puede analizarse. Para importar prueba ODBC y DAO directos; como ultimo
recurso trabaja en una copia temporal sin clave, restaura la cabecera cifrada y solo
entonces reemplaza el MDB original. El log indica la estrategia utilizada.

## Seguridad

La herramienta solo ejecuta `SELECT` e `INSERT`. Antes del primer `INSERT` crea
`{archivo}_BACKUP_YYYYMMDD_HHMMSS.mdb`. Si el backup falla, la importacion se cancela.
Todas las inserciones se confirman juntas; ante un error se revierte la transaccion.
El log `swimtimer_herramientas.log` queda junto al ejecutable.
