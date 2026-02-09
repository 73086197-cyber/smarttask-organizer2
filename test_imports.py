print("🔍 TEST DE IMPORTACIONES DE VOZ")
print("="*50)

try:
    import numpy
    print("✅ numpy OK")
except ImportError:
    print("❌ numpy NO instalado")

try:
    import scipy
    print("✅ scipy OK") 
except ImportError:
    print("❌ scipy NO instalado")

try:
    import sounddevice
    print("✅ sounddevice OK")
except ImportError:
    print("❌ sounddevice NO instalado")

try:
    import speech_recognition
    print("✅ speech_recognition OK")
except ImportError:
    print("❌ speech_recognition NO instalado")

try:
    import pyttsx3
    print("✅ pyttsx3 OK")
except ImportError:
    print("❌ pyttsx3 NO instalado")

print("\n📦 Para instalar lo que falta:")
print("pip install numpy scipy sounddevice SpeechRecognition pyttsx3")
input("\nPresiona Enter para salir...")