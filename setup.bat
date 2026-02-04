
---

## 🏃 **7. ARCHIVO: `setup.bat`**
```batch
@echo off
echo ========================================
echo  SMARTTASK ORGANIZER - INSTALADOR
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado
    echo.
    echo Por favor, instala Python 3.8 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado

REM Actualizar pip
echo.
echo Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo.
echo Instalando dependencias...
pip install -r requirements.txt

REM Instalar pyaudio (especial para Windows)
echo.
echo Instalando pyaudio para Windows...
pip install pipwin
pipwin install pyaudio

REM Crear base de datos
echo.
echo Inicializando base de datos...
python -c "from app.database import db; print('Base de datos lista')"

echo.
echo ========================================
echo  INSTALACION COMPLETADA
echo ========================================
echo.
echo Para ejecutar la aplicacion:
echo   1. Ejecutar: python run.py
echo   2. O hacer doble click en run.py
echo.
echo Presiona una tecla para iniciar la aplicacion...
pause >nul

REM Ejecutar la aplicacion
python run.py

pause