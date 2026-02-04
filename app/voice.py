"""
Módulo de reconocimiento y síntesis de voz para SmartTask Organizer
"""
import speech_recognition as sr
import pyttsx3
import threading
import time
from datetime import datetime
from app.database import db

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        self.is_listening = False
        
        # Configurar la voz
        self._configurar_voz()
        
        # Comandos de voz reconocidos
        self.comandos = {
            "crear tarea": self._crear_tarea_por_voz,
            "listar tareas": self._listar_tareas_por_voz,
            "tareas pendientes": self._tareas_pendientes_por_voz,
            "tareas completadas": self._tareas_completadas_por_voz,
            "eliminar tarea": self._eliminar_tarea_por_voz,
            "completar tarea": self._completar_tarea_por_voz,
            "ayuda": self._mostrar_ayuda_voz,
            "salir": self._salir_voz,
        }
    
    def _configurar_voz(self):
        """Configura el motor de síntesis de voz"""
        voices = self.engine.getProperty('voices')
        
        # Buscar voces en español
        for voice in voices:
            if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        # Configurar velocidad y volumen
        self.engine.setProperty('rate', 150)  # Velocidad de habla
        self.engine.setProperty('volume', 0.9)  # Volumen (0.0 a 1.0)
    
    def hablar(self, texto):
        """Habla el texto proporcionado"""
        print(f"🤖 Asistente: {texto}")
        
        def _hablar():
            self.engine.say(texto)
            self.engine.runAndWait()
        
        # Ejecutar en un hilo separado para no bloquear la interfaz
        thread = threading.Thread(target=_hablar)
        thread.start()
    
    def escuchar(self, timeout=5):
        """Escucha comandos de voz y los convierte en texto"""
        try:
            with self.microphone as source:
                print("🎤 Escuchando... (habla ahora)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            
            print("🔍 Procesando audio...")
            texto = self.recognizer.recognize_google(audio, language="es-ES")
            texto = texto.lower()
            
            print(f"📝 Tú dijiste: {texto}")
            
            # Guardar en base de datos
            db.guardar_comando_voz(texto)
            
            return texto
        
        except sr.WaitTimeoutError:
            print("⏰ Tiempo de espera agotado")
            return None
        except sr.UnknownValueError:
            print("❌ No se pudo entender el audio")
            self.hablar("No te pude entender, ¿puedes repetirlo?")
            return None
        except sr.RequestError as e:
            print(f"❌ Error en el servicio de reconocimiento: {e}")
            self.hablar("Hay un problema con el servicio de voz")
            return None
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return None
    
    def procesar_comando(self, comando_texto):
        """Procesa un comando de voz"""
        if not comando_texto:
            return "No se detectó comando"
        
        # Buscar el comando más adecuado
        for comando_key, comando_func in self.comandos.items():
            if comando_key in comando_texto:
                return comando_func(comando_texto)
        
        # Si no encuentra comando específico, intenta crear tarea
        if "tarea" in comando_texto and ("crear" in comando_texto or "nueva" in comando_texto):
            return self._crear_tarea_por_voz(comando_texto)
        
        # Comando no reconocido
        self.hablar(f"No reconozco el comando: {comando_texto}")
        return "Comando no reconocido"
    
    def _crear_tarea_por_voz(self, comando_texto):
        """Crea una tarea a partir de un comando de voz"""
        try:
            # Extraer información del comando
            palabras = comando_texto.split()
            
            # Buscar palabras clave
            titulo = ""
            descripcion = ""
            prioridad = "media"
            categoria = None
            
            # Palabras clave para prioridad
            if "urgente" in comando_texto or "importante" in comando_texto:
                prioridad = "alta"
            elif "baja" in comando_texto:
                prioridad = "baja"
            
            # Palabras clave para categoría
            if "trabajo" in comando_texto:
                categoria = 1  # ID de Trabajo
            elif "personal" in comando_texto:
                categoria = 2  # ID de Personal
            elif "hogar" in comando_texto:
                categoria = 3  # ID de Hogar
            elif "estudio" in comando_texto:
                categoria = 4  # ID de Estudio
            
            # Extraer título (después de "crear tarea" o "nueva tarea")
            if "crear tarea" in comando_texto:
                start_idx = comando_texto.find("crear tarea") + len("crear tarea")
            elif "nueva tarea" in comando_texto:
                start_idx = comando_texto.find("nueva tarea") + len("nueva tarea")
            else:
                start_idx = 0
            
            titulo = comando_texto[start_idx:].strip()
            if not titulo:
                titulo = "Tarea creada por voz"
            
            # Crear la tarea
            tarea_id = db.crear_tarea(
                titulo=titulo,
                descripcion=descripcion,
                fecha_limite=None,
                prioridad=prioridad,
                categoria_id=categoria
            )
            
            respuesta = f"Tarea creada exitosamente: {titulo}. ID: {tarea_id}"
            self.hablar(respuesta)
            return respuesta
        
        except Exception as e:
            error_msg = f"Error al crear tarea por voz: {str(e)}"
            print(error_msg)
            self.hablar("Hubo un error al crear la tarea")
            return error_msg
    
    def _listar_tareas_por_voz(self, comando_texto):
        """Lista las tareas por voz"""
        try:
            tareas = db.obtener_todas_tareas()
            
            if not tareas:
                respuesta = "No hay tareas registradas"
                self.hablar(respuesta)
                return respuesta
            
            # Contar tareas por estado
            completadas = sum(1 for t in tareas if t['estado'] == 'completada')
            pendientes = sum(1 for t in tareas if t['estado'] == 'pendiente')
            vencidas = sum(1 for t in tareas if t['estado'] == 'vencida')
            
            respuesta = f"Tienes {len(tareas)} tareas. {completadas} completadas, {pendientes} pendientes y {vencidas} vencidas."
            
            # Leer las 3 tareas más urgentes
            tareas_pendientes = [t for t in tareas if t['estado'] == 'pendiente']
            tareas_pendientes.sort(key=lambda x: (
                0 if x['prioridad'] == 'alta' else 1 if x['prioridad'] == 'media' else 2,
                x['fecha_limite'] or '9999-12-31'
            ))
            
            if tareas_pendientes:
                respuesta += " Las tareas más urgentes son: "
                for i, tarea in enumerate(tareas_pendientes[:3], 1):
                    respuesta += f"{i}. {tarea['titulo']}. "
            
            self.hablar(respuesta)
            return respuesta
        
        except Exception as e:
            error_msg = f"Error al listar tareas: {str(e)}"
            print(error_msg)
            self.hablar("Hubo un error al listar las tareas")
            return error_msg
    
    def _tareas_pendientes_por_voz(self, comando_texto):
        """Lista las tareas pendientes por voz"""
        try:
            tareas = db.obtener_todas_tareas()
            tareas_pendientes = [t for t in tareas if t['estado'] == 'pendiente']
            
            if not tareas_pendientes:
                respuesta = "No tienes tareas pendientes"
                self.hablar(respuesta)
                return respuesta
            
            respuesta = f"Tienes {len(tareas_pendientes)} tareas pendientes: "
            for i, tarea in enumerate(tareas_pendientes[:5], 1):
                prioridad = tarea['prioridad']
                titulo = tarea['titulo']
                respuesta += f"{i}. {titulo} ({prioridad}). "
            
            self.hablar(respuesta)
            return respuesta
        
        except Exception as e:
            error_msg = f"Error al obtener tareas pendientes: {str(e)}"
            print(error_msg)
            self.hablar("Hubo un error al obtener las tareas pendientes")
            return error_msg
    
    def _tareas_completadas_por_voz(self, comando_texto):
        """Lista las tareas completadas por voz"""
        try:
            tareas = db.obtener_todas_tareas()
            tareas_completadas = [t for t in tareas if t['estado'] == 'completada']
            
            if not tareas_completadas:
                respuesta = "No tienes tareas completadas"
                self.hablar(respuesta)
                return respuesta
            
            respuesta = f"Tienes {len(tareas_completadas)} tareas completadas. "
            self.hablar(respuesta)
            return respuesta
        
        except Exception as e:
            error_msg = f"Error al obtener tareas completadas: {str(e)}"
            print(error_msg)
            self.hablar("Hubo un error al obtener las tareas completadas")
            return error_msg
    
    def _eliminar_tarea_por_voz(self, comando_texto):
        """Elimina una tarea por voz"""
        self.hablar("Para eliminar una tarea, por favor usa la interfaz gráfica para seleccionar la tarea específica.")
        return "Usa la interfaz gráfica para eliminar tareas"
    
    def _completar_tarea_por_voz(self, comando_texto):
        """Completa una tarea por voz"""
        self.hablar("Para completar una tarea, por favor usa la interfaz gráfica para seleccionar la tarea específica.")
        return "Usa la interfaz gráfica para completar tareas"
    
    def _mostrar_ayuda_voz(self, comando_texto):
        """Muestra ayuda de comandos de voz"""
        comandos_lista = "\n".join([f"• {cmd}" for cmd in self.comandos.keys()])
        respuesta = f"Comandos disponibles: {comandos_lista}"
        
        ayuda_texto = """
        Puedes decir:
        - "Crear tarea [título]" para crear una nueva tarea
        - "Listar tareas" para ver todas tus tareas
        - "Tareas pendientes" para ver las tareas pendientes
        - "Tareas completadas" para ver las tareas completadas
        - "Ayuda" para ver esta ayuda
        - "Salir" para salir del modo voz
        """
        
        print(ayuda_texto)
        self.hablar("Te he mostrado los comandos disponibles en pantalla.")
        return respuesta
    
    def _salir_voz(self, comando_texto):
        """Sale del modo voz"""
        self.hablar("Saliendo del modo de voz. Puedes usar la interfaz gráfica para continuar.")
        return "Modo voz finalizado"
    
    def iniciar_modo_voz(self):
        """Inicia el modo de escucha continua por voz"""
        self.is_listening = True
        self.hablar("Modo voz activado. Di 'ayuda' para ver comandos disponibles.")
        
        while self.is_listening:
            comando = self.escuchar()
            
            if comando:
                if "salir" in comando or "terminar" in comando:
                    self.is_listening = False
                    self.hablar("Modo voz desactivado.")
                    break
                
                self.procesar_comando(comando)
            
            time.sleep(1)
    
    def detener_modo_voz(self):
        """Detiene el modo de escucha por voz"""
        self.is_listening = False

# Instancia global del asistente de voz
voice_assistant = VoiceAssistant()