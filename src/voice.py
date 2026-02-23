"""
Módulo de reconocimiento y síntesis de voz para SmartTask Organizer.

Implementa la clase VoiceAssistant que permite crear tareas mediante
dictado por voz (HU11). Utiliza sounddevice para grabar audio del
micrófono, SpeechRecognition para convertir audio a texto (vía Google
Speech API), y pyttsx3 para síntesis de voz offline (texto a voz).

Dependencias:
    - numpy: Procesamiento de arrays de audio.
    - sounddevice: Grabación de audio del micrófono (reemplaza PyAudio).
    - scipy: Escritura de archivos WAV temporales.
    - SpeechRecognition: Reconocimiento de voz con Google Speech API.
    - pyttsx3: Motor de texto a voz offline.

Nota:
    Si alguna dependencia no está instalada, se crea automáticamente
    una instancia de VoiceAssistantDummy que desactiva la funcionalidad
    de voz sin afectar el resto de la aplicación.
"""
import threading
import tempfile
import os
import re
import queue
import time
from datetime import datetime

class VoiceAssistant:
    """Asistente de voz con reconocimiento y síntesis para SmartTask Organizer (HU11).

    Proporciona funcionalidades de:
        - Reconocimiento de voz: Graba audio con sounddevice, lo convierte
          a texto con Google Speech Recognition.
        - Síntesis de voz: Convierte texto a voz usando pyttsx3 (offline).
        - Parseo inteligente: Extrae título, descripción, fecha, prioridad
          y categoría del texto dictado.

    Attributes:
        voice_available (bool): Indica si el sistema de voz está operativo.
        is_listening (bool): Indica si está en modo escucha activa.
        tts_engine (pyttsx3.Engine): Motor de texto a voz. None si falló.
        recording (bool): Indica si hay una grabación en curso.
        audio_queue (queue.Queue): Cola para datos de audio entre hilos.
        recognizer (speech_recognition.Recognizer): Instancia del reconocedor.
    """

    def __init__(self):
        """Inicializa el asistente de voz importando las dependencias necesarias.

        Ejecuta tres pasos de inicialización:
            1. Verifica e importa las librerías (numpy, sounddevice, scipy,
               SpeechRecognition, pyttsx3).
            2. Inicializa el motor de texto a voz (TTS) con voz en español.
            3. Inicializa el sistema de reconocimiento con sounddevice.

        Si alguna librería falta, voice_available se establece en False.
        """
        self.voice_available = True
        self.is_listening = False
        self.tts_engine = None
        self.recording = False
        self.audio_queue = queue.Queue()
        
        print("🎤 INICIANDO SISTEMA DE VOZ (SoundDevice)...")
        
        # 1. Verificar e importar TODAS las librerías necesarias
        self._verificar_importaciones()
        
        # 2. Inicializar síntesis de voz
        self._inicializar_tts()
        
        # 3. Inicializar reconocimiento de voz
        self._inicializar_reconocimiento()
        
        print("✅ SISTEMA DE VOZ LISTO - MICRÓFONO ACTIVADO")
    
    def _verificar_importaciones(self):
        """Verifica que todas las librerías de voz estén instaladas.

        Importa numpy, sounddevice, scipy.io.wavfile, speech_recognition
        y pyttsx3 como variables globales.

        Returns:
            bool: True si todas las importaciones fueron exitosas,
                False si falta alguna librería.
        """
        try:
            global np, sd, wavfile, sr, pyttsx3
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
        """Inicializa el motor de texto a voz (Text-To-Speech) con pyttsx3.

        Configura velocidad a 150 palabras/min y volumen al máximo.
        Intenta seleccionar una voz en español si está disponible.
        """
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  # Velocidad
            self.tts_engine.setProperty('volume', 1.0) # Volumen
            
            # Intentar poner voz en español
            voces = self.tts_engine.getProperty('voices')
            for voz in voces:
                if 'spanish' in voz.name.lower() or 'es' in voz.languages:
                    self.tts_engine.setProperty('voice', voz.id)
                    break
        except Exception as e:
            print(f"  ⚠️ Error inicializando TTS: {e}")
    
    def _inicializar_reconocimiento(self):
        """Inicializa el sistema de reconocimiento de voz sin PyAudio.

        Crea una instancia de speech_recognition.Recognizer y verifica
        que sounddevice pueda detectar dispositivos de entrada (micrófonos).
        """
        try:
            print("\n  🔍 INICIALIZANDO RECONOCIMIENTO (SoundDevice)...")
            self.recognizer = sr.Recognizer()
            self.voice_available = True
            
            # Listar dispositivos para confirmar que sounddevice funciona
            try:
                devices = sd.query_devices()
                input_devices = [d for d in devices if d['max_input_channels'] > 0]
                print(f"  🎤 {len(input_devices)} dispositivos de entrada encontrados con SoundDevice")
            except Exception as e:
                print(f"  ⚠️ Error consultando dispositivos: {e}")
                
            print("  🎤 Sistema de reconocimiento: LISTO (Custom SoundDevice Recorder)")
            
        except Exception as e:
            print(f"  ❌ Error inicializando reconocimiento: {e}")
            self.voice_available = False
    
    def hablar(self, texto):
        """Convierte texto a voz y lo reproduce por los altavoces.

        Ejecuta la síntesis en un hilo separado para no bloquear la GUI.

        Args:
            texto (str): Texto a convertir en voz y reproducir.

        Returns:
            bool: True si el motor TTS está disponible, False si no.
        """
        print(f"🤖 Asistente: {texto}")
        
        if self.tts_engine:
            def _hablar():
                try:
                    self.tts_engine.say(texto)
                    self.tts_engine.runAndWait()
                except RuntimeError:
                    # Si el loop ya está corriendo, ignorar o solo hacer say
                    try:
                         self.tts_engine.say(texto)
                    except RuntimeError:
                        pass
                except Exception as e:
                    print(f"⚠️ Error al hablar: {e}")

            thread = threading.Thread(target=_hablar, daemon=True)
            thread.start()
            return True
        return False
    
    # ============================================================
    # FUNCIÓN PRINCIPAL - RECONOCIMIENTO DE VOZ REAL
    # ============================================================
    
    def _grabar_audio_sounddevice(self, duracion_max=30, umbral_silencio=0.01):
        """Graba audio del micrófono usando sounddevice hasta detectar silencio.

        Graba en bloques de 0.5s, calculando el volumen RMS de cada bloque.
        La grabación termina al detectar 2.5s de silencio o al alcanzar
        duracion_max. El audio se convierte de float32 a int16 y se
        guarda como archivo WAV temporal.

        Args:
            duracion_max (int): Duración máxima de grabación en segundos.
            umbral_silencio (float): Umbral RMS para considerar silencio.

        Returns:
            str: Ruta absoluta al archivo temporal WAV con la grabación.
            None: Si la grabación falló o el sistema no está disponible.
        """
        if not self.voice_available:
            return None
            
        fs = 44100  # Frecuencia de muestreo
        canales = 1 # Mono
        
        print(f"  🎙️ Iniciando grabación (máx {duracion_max}s)...")
        
        grabacion = []
        silencio_contador = 0
        silencio_max = 2.5 # Segundos de silencio para parar
        bloque_duracion = 0.5 # Segundos por bloque de análisis
        bloques_max = int(duracion_max / bloque_duracion)
        
        muestras_por_bloque = int(fs * bloque_duracion)
        
        try:
            with sd.InputStream(samplerate=fs, channels=canales) as stream:
                for _ in range(bloques_max):
                    # Leer bloque
                    audio_chunk, overflowed = stream.read(muestras_por_bloque)
                    if overflowed:
                        print("    ⚠️ Overflow de audio (ignorable)")
                        
                    grabacion.append(audio_chunk)
                    
                    # Calcular volumen (RMS)
                    rms = np.sqrt(np.mean(audio_chunk**2))
                    
                    # Detectar silencio
                    if rms < umbral_silencio:
                        silencio_contador += bloque_duracion
                    else:
                        silencio_contador = 0 # Resetear si hay ruido
                        
                    # Si hay mucho silencio, parar (pero asegurar que grabamos al menos algo)
                    if silencio_contador >= silencio_max and len(grabacion) > (2/bloque_duracion):
                        print("  🛑 Silencio detectado, terminando grabación.")
                        break
                        
            # Concatenar
            if not grabacion:
                return None
                
            audio_completo = np.concatenate(grabacion, axis=0)
            
            # CONVERTIR A INT16 (CRÍTICO PARA SpeechRecognition)
            # sounddevice graba en float32 (-1.0 a 1.0), pero wavfile/sr prefiere int16
            audio_int16 = (audio_completo * 32767).astype(np.int16)
            
            # Guardar a archivo temporal
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wavfile.write(temp_file.name, fs, audio_int16)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            print(f"  ❌ Error grabando audio: {e}")
            return None

    def escuchar_y_parsear(self, callback=None):
        """Escucha audio del micrófono, lo convierte a texto y lo parsea (HU11).

        Flujo: graba audio → guarda WAV → envía a Google Speech → parsea.

        Args:
            callback (callable): Función a llamar con los datos parseados.

        Returns:
            dict: Datos extraídos: 'titulo', 'descripcion', 'fecha',
                'prioridad', 'categoria', 'autoguardar'.
            None: Si no se pudo reconocer el audio.
        """
        if not self.voice_available:
            self.hablar("El sistema de voz no está disponible.")
            return None
    
        print("\n" + "="*70)
        print("🎤 MODO DICTADO ACTIVADO (SoundDevice)")
        print("="*70)
    
        self.hablar("Te escucho. Tienes 30 segundos.")
    
        try:
            # 1. Grabar audio a archivo temporal
            wav_path = self._grabar_audio_sounddevice(duracion_max=30)
            
            if not wav_path:
                self.hablar("No se pudo grabar el audio.")
                return None
                
            print(f"  💾 Audio guardado temporalmente en: {wav_path}")
            
            # 2. Usar SpeechRecognition con el archivo de audio
            with sr.AudioFile(wav_path) as source:
                print("  🔄 Procesando archivo de audio...")
                audio_data = self.recognizer.record(source)
                
                print("  ☁️ Enviando a Google Speech Recognition...")
                texto = self.recognizer.recognize_google(audio_data, language='es-ES').lower()
                print(f"  📝 TEXTO RECONOCIDO: {texto}")
            
            # Limpiar archivo temporal
            try:
                os.remove(wav_path)
            except OSError:
                pass
        
            # Parsear el texto
            datos = self._parsear_texto_inteligente(texto)
        
            # Hablar confirmación
            if datos['titulo']:
                self.hablar(f"Entendido: {datos['titulo']}")
                print(f"🎯 Título extraído: {datos['titulo']}")
        
            # Llamar al callback si existe
            if callback:
                callback(datos)
        
            return datos
        
        except sr.UnknownValueError:
            self.hablar("No pude entender lo que dijiste.")
            print("❌ No se pudo entender el audio")
        except sr.RequestError as e:
            self.hablar("Error de conexión con el servicio de voz.")
            print(f"❌ Error del servicio: {e}")
        except Exception as e:
            self.hablar("Ocurrió un error al procesar tu voz.")
            print(f"❌ Error inesperado: {e}")
            
            # Intentar limpiar archivo en caso de error
            if 'wav_path' in locals():
                try: os.remove(wav_path)
                except OSError: pass
    
        return None
    
    def _parsear_texto_inteligente(self, texto):
        """Analiza el texto reconocido y extrae datos estructurados de la tarea.

        Busca palabras clave (detalle, fecha, prioridad, categoría, terminar)
        para separar el texto en secciones y asignar cada parte al campo
        correspondiente de la tarea.

        Args:
            texto (str): Texto reconocido del dictado, en minúsculas.

        Returns:
            dict: Diccionario con claves: 'titulo', 'descripcion', 'fecha',
                'prioridad', 'categoria', 'autoguardar'.
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
        """Convierte una fecha hablada en español a formato DD/MM/AAAA (HU06).

        Soporta formatos: texto natural ('quince de diciembre'),
        numérico ('15 12 2025') y mixto ('15 diciembre 2025').

        Args:
            texto_fecha (str): Texto con la fecha hablada en español.

        Returns:
            str: Fecha formateada como 'DD/MM/AAAA'.
        """
        texto_fecha = texto_fecha.lower().strip()
        
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
        return fecha_formateada
    
    def _extraer_prioridad(self, texto):
        """Extrae el nivel de prioridad del texto hablado.

        Args:
            texto (str): Texto donde buscar la prioridad.

        Returns:
            str: 'alta', 'media' o 'baja'. Vacío si no se detectó.
        """
        texto = texto.lower()
        if 'alta' in texto:
            return 'alta'
        elif 'media' in texto:
            return 'media'
        elif 'baja' in texto:
            return 'baja'
        return ''
    
    def _extraer_categoria(self, texto):
        """Extrae la categoría del texto hablado (HU09).

        Busca una de las 6 categorías predefinidas en el texto.

        Args:
            texto (str): Texto donde buscar la categoría.

        Returns:
            str: Nombre de la categoría capitalizado. Vacío si no se detectó.
        """
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
        """Escucha audio y retorna datos parseados (compatibilidad).

        Args:
            timeout (int): Tiempo de espera (no utilizado, por compatibilidad).

        Returns:
            dict: Datos parseados del dictado, o None si falló.
        """
        return self.escuchar_y_parsear()
    
    def iniciar_modo_voz(self):
        """Activa el modo de escucha continua del asistente.

        Returns:
            bool: Siempre True indicando que el modo se activó.
        """
        self.is_listening = True
        return True
    
    def detener_modo_voz(self):
        """Desactiva el modo de escucha continua del asistente."""
        self.is_listening = False

# Instancia global
try:
    voice_assistant = VoiceAssistant()
except Exception as e:
    print(f"❌ ERROR CRÍTICO: {e}")
    
    class VoiceAssistantDummy:
        """Clase sustituta cuando VoiceAssistant no puede inicializarse.

        Proporciona la misma interfaz sin funcionalidad real.
        """

        def __init__(self):
            """Inicializa el dummy con voz desactivada."""
            self.voice_available = False
            self.is_listening = False
        def hablar(self, texto): 
            """Imprime texto en consola (sin voz real)."""
            print(f"🤖: {texto}")
        def escuchar_y_parsear(self, callback=None): 
            """Simula escuchar. Siempre retorna None."""
            print("❌ Voz no disponible")
            return None
        def escuchar(self, timeout=5): 
            """Simula escuchar. Siempre retorna None."""
            return None
        def iniciar_modo_voz(self): 
            """Simula iniciar modo voz. Retorna False."""
            return False
        def detener_modo_voz(self): 
            """No realiza ninguna acción."""
            pass
    
    voice_assistant = VoiceAssistantDummy()