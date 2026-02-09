"""
Módulo de voz REAL - Reconocimiento de voz con micrófono
Versión FUNCIONAL con sounddevice + SpeechRecognition
"""
import threading
import tempfile
import os
import re
from datetime import datetime
import queue

class VoiceAssistant:
    def __init__(self):
        self.voice_available = True
        self.is_listening = False
        self.tts_engine = None
        self.recording = False
        self.audio_queue = queue.Queue()
        
        print("🎤 INICIANDO SISTEMA DE VOZ REAL...")
        
        # 1. Verificar e importar TODAS las librerías necesarias
        self._verificar_importaciones()
        
        # 2. Inicializar síntesis de voz
        self._inicializar_tts()
        
        # 3. Inicializar reconocimiento de voz
        self._inicializar_reconocimiento()
        
        print("✅ SISTEMA DE VOZ LISTO - MICRÓFONO ACTIVADO")
    
    def _verificar_importaciones(self):
        """Verificar que todas las librerías estén instaladas"""
        try:
            global np, sd, wavfile, sr
            import numpy as np
            import sounddevice as sd
            from scipy.io import wavfile
            import speech_recognition as sr
            import pyttsx3
            print("  ✅ Todas las librerías importadas correctamente")
            return True
        except ImportError as e:
            print(f"  ❌ FALTA LIBRERÍA: {e}")
            print("  📦 Ejecuta: pip install numpy scipy sounddevice SpeechRecognition pyttsx3")
            self.voice_available = False
            return False
    
    def _inicializar_tts(self):
        """Inicializar síntesis de voz"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Buscar voz en español
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            
            self.tts_engine.setProperty('rate', 160)
            self.tts_engine.setProperty('volume', 1.0)
            print("  ✅ Síntesis de voz: LISTA")
        except Exception as e:
            print(f"  ⚠️  Síntesis de voz: {str(e)[:50]}")
            self.tts_engine = None
    
    def _inicializar_reconocimiento(self):
        """Inicializar sistema de reconocimiento"""
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            
            # Verificar micrófonos disponibles
            print("\n  🔍 BUSCANDO MICRÓFONOS...")
            mic_list = sr.Microphone.list_microphone_names()
            
            if not mic_list:
                print("  ❌ NO SE ENCONTRARON MICRÓFONOS")
                self.voice_available = False
                return
            
            print(f"  ✅ {len(mic_list)} micrófonos encontrados:")
            for i, mic_name in enumerate(mic_list):
                print(f"     [{i}] {mic_name}")
            
            # Configurar micrófono por defecto
            self.microphone = sr.Microphone()
            
            # Ajustar para ruido ambiente
            with self.microphone as source:
                print("  🔊 Calibrando para ruido ambiente...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("  ✅ Calibración completada")
            
            self.voice_available = True
            print("  🎤 Sistema de reconocimiento: LISTO")
            
        except Exception as e:
            print(f"  ❌ Error inicializando reconocimiento: {e}")
            self.voice_available = False
    
    def hablar(self, texto):
        """Texto a voz - Habla realmente"""
        print(f"🤖 Asistente: {texto}")
        
        if self.tts_engine:
            try:
                def _hablar():
                    self.tts_engine.say(texto)
                    self.tts_engine.runAndWait()
                
                thread = threading.Thread(target=_hablar, daemon=True)
                thread.start()
                return True
            except Exception as e:
                print(f"⚠️ Error al hablar: {e}")
                return False
        return False
    
    # ============================================================
    # FUNCIÓN PRINCIPAL - RECONOCIMIENTO DE VOZ REAL
    # ============================================================
    
    def escuchar_y_parsear(self, callback=None):
        """
        ESCUCHA REALMENTE por micrófono y parsea el texto
        Esta es la función que debes llamar desde el botón 🎤
        """
        if not self.voice_available:
            self.hablar("El sistema de voz no está disponible. Instala las librerías necesarias.")
            messagebox.showerror("Error", 
                "Faltan librerías. Ejecuta:\npip install numpy scipy sounddevice SpeechRecognition pyttsx3")
            return None
        
        print("\n" + "="*70)
        print("🎤 MODO DICTADO ACTIVADO - HABLA AHORA")
        print("="*70)
        print("Instrucciones:")
        print("1. Habla claramente y de forma continua")
        print("2. Usa palabras clave: detalle, fecha, prioridad, categoría")
        print("3. Ejemplo: 'Reunión semanal detalle preparar informe fecha quince diciembre prioridad alta categoría trabajo'")
        print("4. Di 'terminar' al final para guardar automáticamente")
        print("="*70)
        
        self.hablar("Dictado activado. Por favor, habla ahora tu tarea completa.")
        
        try:
            import speech_recognition as sr
            
            # Usar el micrófono
            with self.microphone as source:
                print("⏺️  Grabando... (habla ahora)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=20)
                print("✅ Grabación completada")
            
            # Transcribir
            print("🔄 Transcribiendo...")
            texto = self.recognizer.recognize_google(audio, language='es-ES').lower()
            print(f"📝 TEXTO RECONOCIDO: {texto}")
            
            # Parsear el texto
            datos = self._parsear_texto_inteligente(texto)
            
            # Hablar confirmación
            if datos['titulo']:
                self.hablar(f"Título recibido: {datos['titulo']}")
            
            # Llamar al callback si existe
            if callback:
                callback(datos)
            
            return datos
            
        except sr.WaitTimeoutError:
            self.hablar("No escuché nada. Intenta de nuevo.")
            print("⏰ Tiempo de espera agotado")
        except sr.UnknownValueError:
            self.hablar("No pude entender lo que dijiste. Intenta de nuevo.")
            print("❌ No se pudo entender el audio")
        except sr.RequestError as e:
            self.hablar("Error en el servicio de voz. Verifica tu conexión a internet.")
            print(f"❌ Error del servicio: {e}")
        except Exception as e:
            self.hablar("Ocurrió un error al procesar tu voz.")
            print(f"❌ Error inesperado: {e}")
        
        return None
    
    def _parsear_texto_inteligente(self, texto):
        """
        Parsea el texto con la lógica que pediste
        """
        texto = texto.lower().strip()
        print(f"\n🔍 ANALIZANDO TEXTO: {texto}")
        
        # Diccionario de resultados
        resultados = {
            'titulo': '',
            'descripcion': '',
            'fecha': '',
            'prioridad': '',
            'categoria': '',
            'autoguardar': False
        }
        
        # 1. Verificar si hay "terminar" para autoguardar
        if 'terminar' in texto:
            resultados['autoguardar'] = True
            texto = texto.split('terminar')[0].strip()
        
        # 2. Lista de palabras clave
        palabras_clave = ['detalle', 'fecha', 'prioridad', 'categoría', 'categoria']
        
        # 3. Encontrar todas las posiciones de palabras clave
        posiciones = []
        for palabra in palabras_clave:
            idx = texto.find(palabra)
            if idx != -1:
                posiciones.append((idx, palabra))
        
        # Ordenar por posición
        posiciones.sort()
        
        # 4. Si no hay palabras clave, todo es título
        if not posiciones:
            resultados['titulo'] = texto
            return resultados
        
        # 5. El título es todo antes de la primera palabra clave
        primera_pos, primera_palabra = posiciones[0]
        resultados['titulo'] = texto[:primera_pos].strip()
        
        # 6. Procesar cada sección
        for i, (pos, palabra) in enumerate(posiciones):
            # Encontrar el final de esta sección (siguiente palabra clave o fin)
            if i + 1 < len(posiciones):
                siguiente_pos = posiciones[i + 1][0]
                contenido = texto[pos + len(palabra):siguiente_pos].strip()
            else:
                contenido = texto[pos + len(palabra):].strip()
            
            # Asignar según palabra clave
            if palabra == 'detalle':
                resultados['descripcion'] = contenido
            elif palabra == 'fecha':
                resultados['fecha'] = self._convertir_fecha_voz_a_texto(contenido)
            elif palabra == 'prioridad':
                resultados['prioridad'] = self._extraer_prioridad(contenido)
            elif palabra in ['categoría', 'categoria']:
                resultados['categoria'] = self._extraer_categoria(contenido)
        
        print(f"📊 RESULTADOS PARSEADOS: {resultados}")
        return resultados
    
    def _convertir_fecha_voz_a_texto(self, texto_fecha):
        """
        Convierte fecha hablada a formato DD/MM/AAAA
        Ej: "quince de diciembre de dos mil veinticuatro" -> "15/12/2024"
        """
        texto_fecha = texto_fecha.lower().strip()
        print(f"  📅 Procesando fecha: {texto_fecha}")
        
        # Diccionario completo
        numeros = {
            'cero': '0', 'un': '1', 'uno': '1', 'dos': '2', 'tres': '3', 
            'cuatro': '4', 'cinco': '5', 'seis': '6', 'siete': '7', 
            'ocho': '8', 'nueve': '9', 'diez': '10', 'once': '11', 
            'doce': '12', 'trece': '13', 'catorce': '14', 'quince': '15',
            'dieciseis': '16', 'diecisiete': '17', 'dieciocho': '18',
            'diecinueve': '19', 'veinte': '20', 'veintiuno': '21', 
            'veintidós': '22', 'veintitres': '23', 'veinticuatro': '24',
            'veinticinco': '25', 'veintiseis': '26', 'veintisiete': '27',
            'veintiocho': '28', 'veintinueve': '29', 'treinta': '30', 
            'treinta y uno': '31'
        }
        
        meses = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 
            'diciembre': '12'
        }
        
        # Intentar extraer día, mes y año
        dia = ''
        mes = ''
        año = ''
        
        # Buscar mes primero
        for mes_nombre, mes_num in meses.items():
            if mes_nombre in texto_fecha:
                mes = mes_num
                # Remover mes del texto para buscar día y año
                texto_sin_mes = texto_fecha.replace(mes_nombre, '')
                break
        
        # Si no encontramos mes, intentar con números
        if not mes:
            numeros_encontrados = re.findall(r'\d+', texto_fecha)
            if len(numeros_encontrados) >= 2:
                dia = numeros_encontrados[0].zfill(2)
                mes = numeros_encontrados[1].zfill(2)
                if len(numeros_encontrados) >= 3:
                    año = numeros_encontrados[2]
        
        else:
            # Buscar día (número antes del mes)
            partes = texto_fecha.split()
            for i, parte in enumerate(partes):
                if parte in numeros:
                    dia = numeros[parte]
                elif parte.isdigit() and len(parte) <= 2:
                    dia = parte
        
        # Buscar año
        if 'mil' in texto_fecha or 'dos mil' in texto_fecha:
            # Extraer año numérico
            numeros_año = re.findall(r'\d+', texto_fecha)
            for num in numeros_año:
                if len(num) == 4:
                    año = num
                    break
            if not año:
                # Intentar construir año desde texto
                año_texto = ''
                for palabra in texto_fecha.split():
                    if palabra in numeros and len(numeros[palabra]) == 1:
                        año_texto += numeros[palabra]
                if len(año_texto) >= 4:
                    año = año_texto
        
        # Valores por defecto
        if not año:
            año = str(datetime.now().year)
        
        if not dia:
            dia = '01'
        
        if not mes:
            mes = '01'
        
        # Formatear
        dia = dia.zfill(2) if len(dia) == 1 else dia
        if len(año) == 2:
            año = '20' + año
        
        fecha_formateada = f"{dia}/{mes}/{año}"
        print(f"  ✅ Fecha formateada: {fecha_formateada}")
        return fecha_formateada
    
    def _extraer_prioridad(self, texto):
        """Extrae prioridad: baja, media o alta"""
        texto = texto.lower()
        if 'alta' in texto:
            return 'alta'
        elif 'media' in texto:
            return 'media'
        elif 'baja' in texto:
            return 'baja'
        return ''
    
    def _extraer_categoria(self, texto):
        """Extrae categoría de las 6 opciones"""
        texto = texto.lower()
        categorias = {
            'estudio': 'Estudio',
            'finanzas': 'Finanzas', 
            'hogar': 'Hogar',
            'personal': 'Personal',
            'salud': 'Salud',
            'trabajo': 'Trabajo'
        }
        
        for clave, valor in categorias.items():
            if clave in texto:
                return valor
        
        return ''
    
    # ============================================================
    # FUNCIONES DE COMPATIBILIDAD
    # ============================================================
    
    def escuchar(self, timeout=5):
        """Función de compatibilidad - NO USAR, usar escuchar_y_parsear"""
        print("\n⚠️  Usa escuchar_y_parsear() para dictado real por voz")
        return self.escuchar_y_parsear()
    
    def iniciar_modo_voz(self):
        """Iniciar modo voz general"""
        self.is_listening = True
        self.hablar("Modo voz general activado. Usa el botón de micrófono en el formulario para dictar tareas.")
        print("\n🔊 MODO VOZ GENERAL ACTIVADO")
        return True
    
    def detener_modo_voz(self):
        """Detener modo voz"""
        self.is_listening = False
        self.hablar("Modo voz desactivado")
        print("\n🔊 Modo voz desactivado")

# Instancia global
try:
    voice_assistant = VoiceAssistant()
except Exception as e:
    print(f"❌ ERROR CRÍTICO: {e}")
    
    class VoiceAssistantDummy:
        def __init__(self):
            self.voice_available = False
            self.is_listening = False
        def hablar(self, texto): print(f"🤖: {texto}")
        def escuchar_y_parsear(self, callback=None): 
            print("❌ Voz no disponible - Instala las librerías")
            return None
        def escuchar(self, timeout=5): return None
        def iniciar_modo_voz(self): return False
        def detener_modo_voz(self): pass
    
    voice_assistant = VoiceAssistantDummy()