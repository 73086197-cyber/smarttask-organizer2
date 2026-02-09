"""
Punto de entrada para SmartTask Organizer
"""
import sys
import os

def main():
    print("🚀 Iniciando SmartTask Organizer...")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("app"):
        print("❌ Error: No se encuentra la carpeta 'app'")
        print("   Asegúrate de ejecutar desde el directorio del proyecto")
        input("Presiona Enter para salir...")
        return
    
    # Verificar que main.py existe
    if not os.path.exists("app/main.py"):
        print("❌ Error: No se encuentra app/main.py")
        input("Presiona Enter para salir...")
        return
    
    # Añadir directorio actual al path
    sys.path.insert(0, os.getcwd())
    
    try:
        from app.main import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("\nPosibles soluciones:")
        print("1. Verifica que app/__init__.py existe")
        print("2. Ejecuta en la terminal: pip install -r requirements.txt")
        print("3. Asegúrate de estar en el entorno virtual")
        input("\nPresiona Enter para salir...")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
