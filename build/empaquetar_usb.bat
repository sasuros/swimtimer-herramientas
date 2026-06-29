@echo off
setlocal
cd /d "%~dp0.."

echo ==========================================
echo  SWIMTIMER Herramientas - Empaquetar USB
echo ==========================================
echo.

echo [1/4] Generando ejecutable...
call build\build_exe.bat
if errorlevel 1 (
  echo ERROR: No se pudo generar el ejecutable.
  exit /b 1
)
echo.

echo [2/4] Creando carpeta USB...
if exist "USB_SWIMTIMER_HERRAMIENTAS" rmdir /s /q "USB_SWIMTIMER_HERRAMIENTAS"
mkdir "USB_SWIMTIMER_HERRAMIENTAS"

echo [3/4] Copiando archivos...
copy /y "dist\SWIMTIMER Herramientas.exe" "USB_SWIMTIMER_HERRAMIENTAS\" >nul
if errorlevel 1 (
  echo ERROR: No se pudo copiar el ejecutable.
  exit /b 1
)

echo [4/4] Generando documentacion...
> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo SWIMTIMER - Herramientas de Inscripciones
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo ==========================================
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo Este programa conecta Meet Manager con la web de inscripciones SWIMTIMER.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo INSTRUCCIONES:
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo 1. Haz doble clic en "SWIMTIMER Herramientas.exe".
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo 2. La primera vez, el programa avisara si necesitas instalar el driver
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    de Microsoft Access. Solo se necesita para IMPORTAR inscripciones.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    EXPORTAR un evento funciona sin el driver.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo 3. Para EXPORTAR un evento:
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    - Pulsa "EXPORTAR EVENTO".
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    - Selecciona o arrastra el archivo .mdb de Meet Manager.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    - Pulsa "EXPORTAR JSON".
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    - Sube el JSON desde Mis eventos - Importar desde Meet Manager.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo 4. Para IMPORTAR inscripciones:
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    - Descarga el consolidado desde la web.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    - Pulsa "IMPORTAR INSCRIPCIONES".
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    - Selecciona el archivo .json y el archivo .mdb.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    - Pulsa "IMPORTAR AL MEET MANAGER".
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    - El programa crea un respaldo automatico del .mdb.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo 5. Driver de Access:
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    https://www.microsoft.com/en-us/download/details.aspx?id=54920
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo    Instala la version de 64 bits.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo.
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo Soporte: Samuel Suros - sasuros@gmail.com
>> "USB_SWIMTIMER_HERRAMIENTAS\LEEME.txt" echo SWIMTIMER by Scanleads

> "USB_SWIMTIMER_HERRAMIENTAS\VERIFICAR.bat" echo @echo off
>> "USB_SWIMTIMER_HERRAMIENTAS\VERIFICAR.bat" echo echo Verificando requisitos de SWIMTIMER Herramientas...
>> "USB_SWIMTIMER_HERRAMIENTAS\VERIFICAR.bat" echo echo.
>> "USB_SWIMTIMER_HERRAMIENTAS\VERIFICAR.bat" echo "SWIMTIMER Herramientas.exe" --verificar
>> "USB_SWIMTIMER_HERRAMIENTAS\VERIFICAR.bat" echo pause

echo.
echo ==========================================
echo  USB listo en: USB_SWIMTIMER_HERRAMIENTAS
echo ==========================================
echo.
echo Contenido:
dir "USB_SWIMTIMER_HERRAMIENTAS" /b
echo.
echo Copia esta carpeta a tu USB.
echo.
if not defined CI pause
endlocal
