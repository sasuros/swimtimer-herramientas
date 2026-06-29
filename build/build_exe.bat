@echo off
setlocal
cd /d "%~dp0.."
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "SWIMTIMER Herramientas" ^
  --icon="recursos\swimtimer_icon.ico" ^
  --add-data="recursos\logo_swimtimer.png;recursos" ^
  swimtimer_herramientas.py
if errorlevel 1 (
  echo ERROR: No se pudo generar el ejecutable.
  exit /b 1
)
echo Ejecutable generado en dist\SWIMTIMER Herramientas.exe
endlocal
