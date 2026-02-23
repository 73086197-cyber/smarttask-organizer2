@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo  INSTALANDO SISTEMA DE VOZ COMPLETO
echo ========================================
echo.

REM Activar entorno virtual
call .venv\Scripts\activate

echo 1. Instalando numpy...
pip install numpy

echo 2. Instalando scipy...
pip install scipy

echo 3. Instalando sounddevice...
pip install sounddevice

echo 4. Instalando SpeechRecognition...
pip install SpeechRecognition

echo 5. Instalando pyttsx3...
pip install pyttsx3

echo 6. Instalando python-dateutil...
pip install python-dateutil

echo.
echo ========================================
echo  VERIFICANDO INSTALACIONES...
echo ========================================
echo.
pip list | findstr /i "numpy scipy sounddevice SpeechRecognition pyttsx3 python-dateutil"

echo.
echo [OK] Instalacion completada SIN PyAudio
echo.
echo Ahora ejecuta: python run.py
echo.

pause