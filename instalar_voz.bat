@echo off
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

echo.
echo 6. Instalando PyAudio (puede fallar en Windows)...
pip install pipwin
pipwin install pyaudio

echo.
echo ========================================
echo  VERIFICANDO INSTALACIONES...
echo ========================================
echo.
pip list | findstr /i "numpy scipy sounddevice speech pyttsx3 pyaudio"

echo.
echo ✅ Si ves las 6 librerías arriba, TODO ESTÁ INSTALADO
echo.
echo 🚀 Ahora ejecuta: python run.py
echo.

pause
