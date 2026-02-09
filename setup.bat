@echo off
echo ========================================
echo  SMARTTASK ORGANIZER - INSTALADOR
echo ========================================
echo.

REM Verificar Python (usa py primero)
py --version >nul 2>&1
if errorlevel 1 (
    echo Python no encontrado.
    echo.
    echo Por favor, instala Python 3.8 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

echo Python encontrado.

REM Actualizar pip
echo.
echo Actualizando pip...
py -m pip install --upgrade pip

REM Instalar dependencias
echo.
echo Instalando dependencias...
py -m pip install -r requirements.txt

REM Inicializar base de datos
echo.
echo Inicializando base de datos...
py -c "from app.database import db; print('Base de datos lista')"

echo.
echo ========================================
echo  INSTALACION COMPLETADA
echo ========================================
echo.
echo Para ejecutar la aplicacion:
echo   Ejecutar: py run.py
echo.
pause

REM Ejecutar la aplicacion
py run.py
