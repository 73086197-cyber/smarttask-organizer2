"""
TEST DE RECONOCIMIENTO DE VOZ REAL
Ejecuta esto para verificar que tu micrófono funciona
"""
import sys
import os

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("🔊 TEST DE RECONOCIMIENTO DE VOZ REAL")
print("="*70)
print("\nEste test verificará:")
print("1. Si las librerías están instaladas")
print("2. Si el micrófono funciona")
print("3. Si puede transcribir tu voz\n")

# ====================================================
# PRUEBA 1: Verificar instalaciones
# ====================================================
print("\n✅ PRUEBA 1: Verificando librerías...")
librerias_necesarias = [
    'numpy',
    'scipy',
    'sounddevice', 
    'speech_recognition',
    'pyttsx3'
]

for lib in librerias_necesarias:
    try:
        __import__(lib)
        print(f"  ✅ {lib} está instalado")
    except ImportError:
        print(f"  ❌ {lib} NO está instalado")
        print(f"     Ejecuta: pip install {lib}")

# ====================================================
# PRUEBA 2: Crear una versión simple de reconocimiento
# ====================================================
print("\n\n✅ PRUEBA 2: Creando sistema de voz simple...")

try:
    import numpy as np
    import sounddevice as sd
    from scipy.io import wavfile
    import speech_recognition as sr
    import pyttsx3
    import tempfile
    
    print("  ✅ Todas las librerías importadas correctamente")
    
    # Inicializar reconocimiento
    print("\n🎤 Buscando micrófonos...")
    recognizer = sr.Recognizer()
    
    # Listar micrófonos
    mic_list = sr.Microphone.list_microphone_names()
    if mic_list:
        print(f"  ✅ Encontrados {len(mic_list)} micrófonos:")
        for i, mic in enumerate(mic_list):
            print(f"     [{i}] {mic}")
        
        # Probar con el micrófono por defecto
        print("\n🔊 Probando con el micrófono por defecto...")
        with sr.Microphone() as source:
            print("  🔊 Calibrando para ruido ambiente...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("  ✅ Calibración completada")
            
            print("\n🎤 HABLA AHORA (di algo como 'Hola, esto es una prueba')...")
            print("   (Grabando por 5 segundos...)\n")
            
            try:
                # Escuchar
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                print("✅ Grabación completada")
                print("🔄 Transcribiendo...")
                
                # Transcribir
                texto = recognizer.recognize_google(audio, language='es-ES')
                
                print(f"\n🎉 ¡ÉXITO! Texto reconocido: '{texto}'")
                
                # Probar síntesis de voz
                print("\n🔊 Probando síntesis de voz...")
                engine = pyttsx3.init()
                engine.say(f"Reconocí: {texto}")
                print("  🔊 Reproduciendo audio...")
                engine.runAndWait()
                print("  ✅ Síntesis de voz funcionando")
                
            except sr.WaitTimeoutError:
                print("❌ No se detectó voz. Habla más fuerte o acerca el micrófono.")
            except sr.UnknownValueError:
                print("❌ No se pudo entender el audio. Intenta hablar más claro.")
            except sr.RequestError as e:
                print(f"❌ Error del servicio: {e}")
                print("   Verifica tu conexión a internet.")
                
    else:
        print("❌ No se encontraron micrófonos.")
        print("   Conecta un micrófono y reinicia la aplicación.")
        
except Exception as e:
    print(f"\n❌ ERROR DURANTE LA PRUEBA: {e}")
    import traceback
    traceback.print_exc()

# ====================================================
# PRUEBA 3: Probar grabación directa con sounddevice
# ====================================================
print("\n\n✅ PRUEBA 3: Probar grabación con sounddevice...")

try:
    print("🎤 Dispositivos de audio disponibles:")
    
    # Listar dispositivos
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  [{i}] {device['name']} (Entradas: {device['max_input_channels']})")
    
    # Probar grabación
    print("\n⏺️  Probando grabación de 3 segundos...")
    print("   Habla ahora...")
    
    # Configuración
    samplerate = 16000
    duration = 3  # segundos
    
    # Grabar
    recording = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype='float32'
    )
    
    print("   Grabando...", end='', flush=True)
    sd.wait()
    print(" ✅ Grabación completada")
    
    # Verificar que se grabó algo
    if np.max(np.abs(recording)) > 0.01:
        print("✅ Se detectó audio (nivel suficiente)")
    else:
        print("⚠️  Audio muy bajo o silencio")
    
    print("\n🎉 ¡PRUEBA COMPLETADA!")
    
except Exception as e:
    print(f"❌ Error en prueba 3: {e}")

# ====================================================
# INSTRUCCIONES FINALES
# ====================================================
print("\n" + "="*70)
print("📋 RESUMEN Y SOLUCIONES:")
print("="*70)

print("\nSi alguna prueba falló:")
print("1. INSTALA LAS LIBRERÍAS:")
print("   pip install numpy scipy sounddevice SpeechRecognition pyttsx3")
print("")
print("2. VERIFICA TU MICRÓFONO:")
print("   - Asegúrate de que el micrófono esté conectado")
print("   - Verifica en Windows: Configuración > Sistema > Sonido")
print("   - Prueba con la 'Grabadora de voz' de Windows")
print("")
print("3. PERMISOS:")
print("   - Da permisos a VS Code para usar el micrófono")
print("   - Windows: Configuración > Privacidad > Micrófono")
print("")
print("4. EJECUTA EL PROYECTO COMPLETO:")
print("   - Ve a la carpeta principal del proyecto")
print("   - Ejecuta: python run.py")
print("   - Usa Ctrl+V en el formulario para dictar")

input("\nPresiona Enter para salir...")