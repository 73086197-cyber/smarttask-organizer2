"""
Script de ejecución para SmartTask Organizer
"""
import sys
import os
import subprocess

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    dependencias = [
        ("pyttsx3", "pyttsx3"),
        ("SpeechRecognition", "speech_recognition"),
        ("pyaudio", "pyaudio"),
    ]
    
    faltantes = []
    
    for nombre, import_name in dependencias:
        try:
            __import__(import_name)
            print(f"✅ {nombre} instalado")
        except ImportError:
            faltantes.append(nombre)
            print(f"❌ {nombre} NO instalado")
    
    return faltantes

def instalar_dependencias(faltantes):
    """Instala las dependencias faltantes"""
    if not faltantes:
        return True
    
    print(f"\nInstalando {len(faltantes)} dependencias faltantes...")
    
    try:
        for dep in faltantes:
            print(f"Instalando {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        
        print("✅ Todas las dependencias instaladas correctamente")
        return True
    
    except Exception as e:
        print(f"❌ Error al instalar dependencias: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 50)
    print("SMARTTASK ORGANIZER - Configuración Inicial")
    print("=" * 50)
    
    # Verificar Python
    print(f"Python: {sys.version}")
    
    # Verificar directorio
    if not os.path.exists("app"):
        print("❌ Error: No se encuentra el directorio 'app'")
        print("   Ejecuta desde el directorio raíz del proyecto")
        input("Presiona Enter para salir...")
        return
    
    # Verificar dependencias
    print("\nVerificando dependencias...")
    faltantes = verificar_dependencias()
    
    if faltantes:
        respuesta = input(f"\n¿Instalar las {len(faltantes)} dependencias faltantes? (s/n): ")
        if respuesta.lower() == 's':
            if not instalar_dependencias(faltantes):
                input("Presiona Enter para salir...")
                return
        else:
            print("⚠️  Algunas funcionalidades pueden no estar disponibles")
    
    # Verificar micrófono (opcional)
    try:
        import speech_recognition as sr
        mic_list = sr.Microphone.list_microphone_names()
        if mic_list:
            print(f"✅ Micrófono detectado: {mic_list[0]}")
        else:
            print("⚠️  No se detectó micrófono. La funcionalidad de voz puede no funcionar.")
    except:
        print("⚠️  No se pudo verificar el micrófono")
    
    # Iniciar aplicación
    print("\n" + "=" * 50)
    print("Iniciando SmartTask Organizer...")
    print("=" * 50)
    
    try:
        from app.main import main as app_main
        app_main()
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()