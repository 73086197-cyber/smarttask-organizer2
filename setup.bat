@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo  SMARTTASK ORGANIZER - INSTALADOR
echo ========================================
echo.

REM Verificar Python (intentar python y luego py)
set PYTHON_CMD=python
%PYTHON_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    set PYTHON_CMD=py
)

call :CHECK_PYTHON
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado.
    echo    Instala Python 3.8+ desde: https://python.org
    echo    IMPORTANTE: Marca la casilla "Add Python to PATH" al instalar.
    pause
    exit /b 1
)

echo [OK] Python encontrado.

REM Crear entorno virtual si no existe
if not exist ".venv" (
    echo Creando entorno virtual...
    %PYTHON_CMD% -m venv .venv
)

REM Activar entorno
call .venv\Scripts\activate

REM Actualizar pip
echo.
echo Actualizando pip...
python -m pip install --upgrade pip

REM Instalar TODAS las dependencias
echo.
echo Instalando dependencias...
python -m pip install -r requirements.txt

REM Inicializar base de datos
echo.
echo Inicializando base de datos...
python -c "from src.database import db; print('[OK] Base de datos lista')"

echo.
echo ========================================
echo  [OK] INSTALACION COMPLETADA
echo ========================================
echo.
echo Para ejecutar la aplicacion:
echo   1. Activar entorno: .venv\Scripts\activate
echo   2. Ejecutar: python run.py
echo.
echo Presiona Enter para ejecutar la aplicacion...
pause >nul

REM Ejecutar la aplicacion
python run.py
exit /b 0

:CHECK_PYTHON
%PYTHON_CMD% --version >nul 2>&1
exit /b %errorlevel%