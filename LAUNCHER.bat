@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title SmartTask Organizer - LAUNCHER
color 0f

echo ==================================================
echo      SMARTTASK ORGANIZER - INICIADOR UNIVERSAL
echo ==================================================
echo.

REM ---------------------------------------------------
REM 1. BUSCAR PYTHON
REM ---------------------------------------------------
echo [1/4] Buscando Python...
set PYTHON_CMD=python

python --version >nul 2>&1
if !errorlevel! neq 0 (
    set PYTHON_CMD=py
    py --version >nul 2>&1
    if !errorlevel! neq 0 (
        REM Intentar ruta comun de instalacion
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        !PYTHON_CMD! --version >nul 2>&1
        if !errorlevel! neq 0 (
            set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
            !PYTHON_CMD! --version >nul 2>&1
            if !errorlevel! neq 0 (
                set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
                !PYTHON_CMD! --version >nul 2>&1
            )
        )
    )
)

!PYTHON_CMD! --version >nul 2>&1
if !errorlevel! neq 0 (
    color 0c
    echo [ERROR CRITICO] No se encuentra Python instalado.
    echo.
    echo SOLUCION:
    echo 1. Ve a https://www.python.org/downloads/
    echo 2. Descarga la ultima version.
    echo 3. Dale click a "Add Python to PATH" al instalar.
    echo.
    pause
    exit /b
)
echo [OK] Usando: !PYTHON_CMD!

REM ---------------------------------------------------
REM 2. CONFIGURAR ENTORNO VIRTUAL
REM ---------------------------------------------------
if not exist ".venv" (
    echo [2/4] Creando entorno virtual (primera vez^)...
    !PYTHON_CMD! -m venv .venv
    if !errorlevel! neq 0 (
        color 0c
        echo [ERROR] Fallo al crear .venv
        pause
        exit /b
    )
    echo [OK] Entorno creado.
) else (
    echo [2/4] Entorno virtual detectado.
)

REM ---------------------------------------------------
REM 3. INSTALAR TODO (AUTOMATICO)
REM ---------------------------------------------------
echo [3/4] Verificando librerias...
call .venv\Scripts\activate >nul 2>&1

REM Instalar pip actualizado primero
python -m pip install --upgrade pip >nul 2>&1

REM Instalar requerimientos
pip install -r requirements.txt >nul 2>&1

if !errorlevel! neq 0 (
    color 0e
    echo [AVISO] Hubo problemas instalando librerias.
    echo Intentando instalar una por una para asegurar lo basico...
    pip install tk >nul 2>&1
    pip install plyer >nul 2>&1
    pip install matplotlib >nul 2>&1
    pip install python-dateutil >nul 2>&1
    echo [OK] Intento de recuperacion completado.
) else (
    echo [OK] Librerias listas.
)

REM ---------------------------------------------------
REM 4. EJECUTAR APP
REM ---------------------------------------------------
cls
echo ==================================================
echo               SMARTTASK ORGANIZER
echo ==================================================
echo.
echo [INFO] Iniciando aplicacion...
echo.

python run.py

if !errorlevel! neq 0 (
    color 0c
    echo.
    echo [ERROR] La aplicacion se cerro con errores.
    echo Toma una foto de esto si necesitas ayuda.
    pause
) else (
    echo.
    echo [INFO] Aplicacion cerrada. Hasta pronto.
    timeout /t 3 >nul
)

endlocal
