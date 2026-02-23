@echo off
echo ========================================
echo  SMARTTASK ORGANIZER - PRUEBAS UNITARIAS
echo ========================================
echo.

REM Activar entorno virtual
call .venv\Scripts\activate

REM Instalar pytest si no está
pip install pytest pytest-cov >nul 2>&1

echo Ejecutando pruebas unitarias...
echo.

pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

echo.
echo ========================================
echo  PRUEBAS COMPLETADAS
echo ========================================
pause
