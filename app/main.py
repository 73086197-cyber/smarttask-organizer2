"""
SmartTask Organizer - Aplicación principal
Versión CORREGIDA para Visual Studio Code
"""
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import threading
import sys
import os

# Asegurar que Python encuentra los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar base de datos
try:
    from app.database import db
    print("✅ Base de datos importada")
except ImportError as e:
    print(f"❌ Error importando base de datos: {e}")
    print("Intentando importar directamente...")
    # Intentar importación relativa
    from database import db

# Importar módulo de voz con manejo de errores
try:
    from app.voice import voice_assistant
    print("✅ Módulo de voz importado")
except ImportError as e:
    print(f"⚠️  Error importando voz: {e}")
    print("Usando voz simulada...")
    
    # Dummy para desarrollo
    class DummyVoice:
        def __init__(self): 
            self.voice_available = True
            self.is_listening = False
        def hablar(self, texto): 
            print(f"🤖 [Simulado]: {texto}")
        def escuchar(self, timeout=5): 
            return None
        def iniciar_modo_voz(self): 
            print("🎤 Modo voz simulado activado")
            return True
        def detener_modo_voz(self): 
            print("🎤 Modo voz desactivado")
    
    voice_assistant = DummyVoice()

# ============================================================================
# DIÁLOGOS (las mismas clases de antes, pero adaptadas)
# ============================================================================

class CrearTareaDialog:
    """HU01 - Crear nueva tarea CON VOZ"""
    def __init__(self, parent, callback=None, voice_assistant=None):
        self.top = tk.Toplevel(parent)
        self.top.title("NUEVA TAREA - CON RECONOCIMIENTO DE VOZ")
        self.top.geometry("1000x800")  # Más grande para incluir sección de voz
        self.top.resizable(False, False)
        
        self.callback = callback
        self.resultado = False
        self.voice_assistant = voice_assistant
        
        # Variables para almacenar datos de voz
        self.datos_voz = {}
        
        self._crear_widgets()
        self._centrar_ventana(parent)
        
        # Si hay asistente de voz, configurar tecla rápida (V)
        if self.voice_assistant and self.voice_assistant.voice_available:
            self.top.bind('<Control-v>', lambda e: self._activar_dictado_voz())
            self.top.bind('<Command-v>', lambda e: self._activar_dictado_voz())
    
    def _centrar_ventana(self, parent):
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _crear_widgets(self):
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título principal con botón de voz
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        
        ttk.Label(header_frame, text="NUEVA TAREA", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Botón grande de voz si está disponible
        if self.voice_assistant and self.voice_assistant.voice_available:
            self.btn_voz = ttk.Button(
                header_frame, 
                text="🎤 DICTAR TAREA COMPLETA",
                command=self._activar_dictado_voz,
                style="Accent.TButton",
                width=25
            )
            self.btn_voz.pack(side=tk.RIGHT, padx=10)
            
            ttk.Label(header_frame, text="(Ctrl+V)", 
                     font=("Arial", 9)).pack(side=tk.RIGHT)
        
        # Sección de instrucciones de voz
        if self.voice_assistant and self.voice_assistant.voice_available:
            inst_frame = ttk.LabelFrame(main_frame, text="📢 INSTRUCCIONES DE VOZ", padding="10")
            inst_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 15))
            
            instrucciones = """
            Ejemplo de dictado: "Reunión equipo detalle preparar presentación 
            fecha quince diciembre prioridad alta categoría trabajo terminar"
            
            Palabras clave:
            • detalle: para descripción
            • fecha: para fecha límite
            • prioridad: baja/media/alta  
            • categoría: Estudio/Finanzas/Hogar/Personal/Salud/Trabajo
            • terminar: guarda automáticamente
            """
            
            ttk.Label(inst_frame, text=instrucciones, 
                     font=("Arial", 9), justify=tk.LEFT).pack(anchor="w")
        
        # Campos del formulario
        campos = [
            ("Título *", "entry", ""),
            ("Descripción", "text", ""),
            ("Fecha Límite (DD/MM/AAAA)", "entry", ""),
            ("Prioridad", "combo_pri", "media"),
            ("Categoría", "combo_cat", "")
        ]
        
        self.widgets = {}
        row_start = 3 if self.voice_assistant and self.voice_assistant.voice_available else 1
        
        for i, (label_text, tipo, valor_default) in enumerate(campos):
            row = row_start + i
            
            ttk.Label(main_frame, text=label_text).grid(
                row=row, column=0, padx=(0, 10), pady=8, sticky="w"
            )
            
            if tipo == "entry":
                widget = ttk.Entry(main_frame, width=45)
                widget.grid(row=row, column=1, columnspan=2, pady=8, sticky="ew")
                
            elif tipo == "text":
                widget = tk.Text(main_frame, width=45, height=5)
                widget.grid(row=row, column=1, columnspan=2, pady=8, sticky="ew")
                
            elif tipo == "combo_pri":
                widget = ttk.Combobox(main_frame, values=["baja", "media", "alta"], 
                                     state="readonly", width=42)
                widget.set(valor_default)
                widget.grid(row=row, column=1, columnspan=2, pady=8, sticky="ew")
                
            elif tipo == "combo_cat":
                categorias = db.obtener_categorias()
                valores = ["Seleccionar..."] + [cat['nombre'] for cat in categorias]
                widget = ttk.Combobox(main_frame, values=valores, 
                                     state="readonly", width=42)
                widget.set("Seleccionar...")
                widget.grid(row=row, column=1, columnspan=2, pady=8, sticky="ew")
            
            self.widgets[label_text.split()[0].lower()] = widget
        
        # Configurar expansión
        main_frame.columnconfigure(1, weight=1)
        
        # Separador
        sep_row = row_start + len(campos) + 1
        ttk.Separator(main_frame, orient="horizontal").grid(
            row=sep_row, column=0, columnspan=3, pady=20, sticky="ew"
        )
        
        # Botones
        btn_row = sep_row + 1
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=btn_row, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="💾 GUARDAR", width=15,
                  command=self._guardar, style="Success.TButton").pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="🗑️ LIMPIAR", width=15,
                  command=self._limpiar_campos).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="❌ CANCELAR", width=15,
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _activar_dictado_voz(self):
        """Activa el reconocimiento de voz REAL"""
        if not self.voice_assistant or not self.voice_assistant.voice_available:
            messagebox.showerror("Error", 
                "El sistema de voz no está disponible.\n\n"
                "Instala las librerías:\n"
                "pip install numpy scipy sounddevice SpeechRecognition pyttsx3")
            return
        
        # Deshabilitar botón temporalmente
        if hasattr(self, 'btn_voz'):
            self.btn_voz.config(state='disabled')
        
        # Mostrar ventana de espera
        wait_window = tk.Toplevel(self.top)
        wait_window.title("Escuchando...")
        wait_window.geometry("400x250")
        wait_window.resizable(False, False)
        wait_window.transient(self.top)
        wait_window.grab_set()
        
        ttk.Label(wait_window, text="🎤 ESCUCHANDO...", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        ttk.Label(wait_window, text="Habla claramente tu tarea completa").pack()
        ttk.Label(wait_window, text="Estoy procesando...", font=("Arial", 9)).pack(pady=10)
        
        # Centrar ventana de espera
        wait_window.update_idletasks()
        x = self.top.winfo_x() + (self.top.winfo_width() // 2) - (150)
        y = self.top.winfo_y() + (self.top.winfo_height() // 2) - (75)
        wait_window.geometry(f"+{x}+{y}")
        
        def procesar_voz():
            """Proceso en segundo plano"""
            try:
                # LLAMADA PRINCIPAL A LA FUNCIÓN DE VOZ
                datos = self.voice_assistant.escuchar_y_parsear(self._procesar_datos_voz)
                
                # Cerrar ventana de espera
                self.top.after(0, wait_window.destroy)
                
                if datos:
                    # Actualizar interfaz en el hilo principal
                    self.top.after(0, lambda: self._rellenar_campos_desde_voz(datos))
                
            except Exception as e:
                print(f"Error en hilo de voz: {e}")
                self.top.after(0, wait_window.destroy)
            
            # Rehabilitar botón
            if hasattr(self, 'btn_voz'):
                self.top.after(0, lambda: self.btn_voz.config(state='normal'))
        
        # Ejecutar en hilo separado
        voz_thread = threading.Thread(target=procesar_voz, daemon=True)
        voz_thread.start()
    
    def _procesar_datos_voz(self, datos):
        """Callback para procesar datos de voz (se ejecuta desde hilo de voz)"""
        self.datos_voz = datos
        print(f"Datos de voz recibidos en callback: {datos}")
    
    def _rellenar_campos_desde_voz(self, datos):
        """Rellena los campos del formulario con los datos de voz"""
        if not datos:
            return
        
        # Título
        if datos.get('titulo'):
            self.widgets['título'].delete(0, tk.END)
            self.widgets['título'].insert(0, datos['titulo'])
        
        # Descripción
        if datos.get('descripcion'):
            self.widgets['descripción'].delete("1.0", tk.END)
            self.widgets['descripción'].insert("1.0", datos['descripcion'])
        
        # Fecha
        if datos.get('fecha'):
            self.widgets['fecha'].delete(0, tk.END)
            self.widgets['fecha'].insert(0, datos['fecha'])
        
        # Prioridad
        if datos.get('prioridad'):
            self.widgets['prioridad'].set(datos['prioridad'])
        
        # Categoría
        if datos.get('categoria'):
            self.widgets['categoría'].set(datos['categoria'])
        
        # Mostrar mensaje de confirmación
        if datos.get('autoguardar'):
            respuesta = messagebox.askyesno(
                "Autoguardado detectado",
                f"Se detectó la palabra 'terminar'.\n\n"
                f"¿Deseas guardar la tarea automáticamente?\n\n"
                f"Título: {datos.get('titulo', '')}"
            )
            if respuesta:
                self._guardar()
        else:
            messagebox.showinfo(
                "Dictado completado",
                f"Tarea dictada correctamente.\n\n"
                f"Revisa los campos y haz clic en GUARDAR."
            )
    
    def _limpiar_campos(self):
        """Limpia todos los campos del formulario"""
        for key, widget in self.widgets.items():
            if isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
            elif isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
            elif isinstance(widget, ttk.Combobox):
                if key == 'prioridad':
                    widget.set('media')
                else:
                    widget.set('Seleccionar...')
    
    def _guardar(self):
        """GUARDA la tarea (igual que antes pero mejorado)"""
        titulo = self.widgets['título'].get().strip()
        if not titulo:
            messagebox.showerror("Error", "El título es obligatorio")
            return
        
        descripcion = ""
        if 'descripción' in self.widgets:
            descripcion = self.widgets['descripción'].get("1.0", tk.END).strip()
        
        fecha_text = self.widgets['fecha'].get().strip()
        fecha_sql = None
        if fecha_text:
            try:
                fecha_obj = datetime.strptime(fecha_text, "%d/%m/%Y")
                fecha_sql = fecha_obj.strftime("%Y-%m-%d")
                
                from datetime import date
                if fecha_obj.date() < date.today():
                    messagebox.showerror("Error", "La fecha límite no puede ser en el pasado")
                    return
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use DD/MM/AAAA")
                return
        
        prioridad = self.widgets['prioridad'].get()
        categoria_nombre = self.widgets['categoría'].get()
        
        categoria_id = None
        if categoria_nombre and categoria_nombre != "Seleccionar...":
            categorias = db.obtener_categorias()
            for cat in categorias:
                if cat['nombre'] == categoria_nombre:
                    categoria_id = cat['id']
                    break
        
        try:
            tarea_id = db.crear_tarea(
                titulo=titulo,
                descripcion=descripcion,
                fecha_limite=fecha_sql,
                prioridad=prioridad,
                categoria_id=categoria_id
            )
            
            self.resultado = True
            if self.callback:
                self.callback()
            
            self.top.destroy()
            messagebox.showinfo("Éxito", "✅ Tarea guardada correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la tarea:\n{str(e)}")
# (Las clases EditarTareaDialog y EliminarTareaDialog se mantienen igual que antes,
class EditarTareaDialog:
    """HU03 - Editar tarea existente"""
    def __init__(self, parent, tarea_id, callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("EDITAR TAREA")
        self.top.geometry("500x500")
        self.top.resizable(False, False)
        
        self.callback = callback
        self.tarea_id = tarea_id
        self.resultado = False
        
        self._cargar_tarea()
        self._crear_widgets()
        self._centrar_ventana(parent)
    
    def _centrar_ventana(self, parent):
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _cargar_tarea(self):
        """Cargar datos de la tarea desde la base de datos"""
        try:
            self.tarea = db.obtener_tarea(self.tarea_id)
            if not self.tarea:
                raise ValueError("Tarea no encontrada")
        except Exception as e:
            print(f"Error cargando tarea: {e}")
            self.tarea = None
    
    def _crear_widgets(self):
        if not self.tarea:
            ttk.Label(self.top, text="Error: Tarea no encontrada", 
                     font=("Arial", 12), foreground="red").pack(pady=50)
            ttk.Button(self.top, text="Cerrar", 
                      command=self.top.destroy).pack(pady=10)
            return
        
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"EDITAR TAREA ID: {self.tarea_id}", 
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, 
                                                 pady=(0, 20), sticky="w")
        
        # Campos del formulario
        campos = [
            ("Título *", "entry", self.tarea['titulo']),
            ("Descripción", "text", self.tarea['descripcion'] or ""),
            ("Fecha Límite", "entry", self._formatear_fecha(self.tarea['fecha_limite'])),
            ("Prioridad", "combo_pri", self.tarea['prioridad']),
            ("Categoría", "combo_cat", self.tarea['categoria_nombre'] or "Seleccionar..."),
            ("Estado", "combo_estado", self.tarea['estado'])
        ]
        
        self.widgets = {}
        row = 1
        
        for label_text, tipo, valor in campos:
            ttk.Label(main_frame, text=label_text).grid(row=row, column=0, 
                                                       padx=(0, 10), pady=5, 
                                                       sticky="w")
            
            if tipo == "entry":
                widget = ttk.Entry(main_frame, width=40)
                widget.insert(0, valor)
                widget.grid(row=row, column=1, pady=5, sticky="ew")
                
            elif tipo == "text":
                widget = tk.Text(main_frame, width=40, height=4)
                widget.insert("1.0", valor)
                widget.grid(row=row, column=1, pady=5, sticky="ew")
                
            elif tipo == "combo_pri":
                widget = ttk.Combobox(main_frame, values=["baja", "media", "alta"], 
                                     state="readonly", width=38)
                widget.set(valor)
                widget.grid(row=row, column=1, pady=5, sticky="ew")
                
            elif tipo == "combo_cat":
                categorias = db.obtener_categorias()
                valores = ["Seleccionar..."] + [cat['nombre'] for cat in categorias]
                widget = ttk.Combobox(main_frame, values=valores, 
                                     state="readonly", width=38)
                widget.set(valor if valor else "Seleccionar...")
                widget.grid(row=row, column=1, pady=5, sticky="ew")
            
            elif tipo == "combo_estado":
                widget = ttk.Combobox(main_frame, values=["pendiente", "completada", "vencida"], 
                                     state="readonly", width=38)
                widget.set(valor)
                widget.grid(row=row, column=1, pady=5, sticky="ew")
            
            self.widgets[label_text.split()[0].lower()] = widget
            row += 1
        
        main_frame.columnconfigure(1, weight=1)
        
        # Separador
        ttk.Separator(main_frame, orient="horizontal").grid(row=row, column=0, 
                                                           columnspan=2, 
                                                           pady=20, sticky="ew")
        row += 1
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="💾 ACTUALIZAR", width=15,
                  command=self._actualizar).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="❌ CANCELAR", width=15,
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _formatear_fecha(self, fecha_sql):
        """Formatear fecha de SQL a DD/MM/AAAA"""
        if not fecha_sql:
            return ""
        try:
            fecha_obj = datetime.strptime(fecha_sql, "%Y-%m-%d")
            return fecha_obj.strftime("%d/%m/%Y")
        except:
            return fecha_sql
    
    def _actualizar(self):
        """Actualizar tarea en la base de datos"""
        titulo = self.widgets['título'].get().strip()
        if not titulo:
            messagebox.showerror("Error", "El título es obligatorio")
            return
        
        descripcion = ""
        if 'descripción' in self.widgets:
            descripcion = self.widgets['descripción'].get("1.0", tk.END).strip()
        
        fecha_text = self.widgets['fecha'].get().strip()
        fecha_sql = None
        if fecha_text:
            try:
                fecha_obj = datetime.strptime(fecha_text, "%d/%m/%Y")
                fecha_sql = fecha_obj.strftime("%Y-%m-%d")
                
                from datetime import date
                if fecha_obj.date() < date.today():
                    messagebox.showerror("Error", "La fecha límite no puede ser en el pasado")
                    return
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use DD/MM/AAAA")
                return
        
        prioridad = self.widgets['prioridad'].get()
        categoria_nombre = self.widgets['categoría'].get()
        estado = self.widgets['estado'].get()
        
        categoria_id = None
        if categoria_nombre and categoria_nombre != "Seleccionar...":
            categorias = db.obtener_categorias()
            for cat in categorias:
                if cat['nombre'] == categoria_nombre:
                    categoria_id = cat['id']
                    break
        
        try:
            # Actualizar tarea
            actualizado = db.actualizar_tarea(
                self.tarea_id,
                titulo=titulo,
                descripcion=descripcion,
                fecha_limite=fecha_sql,
                prioridad=prioridad,
                estado=estado,
                categoria_id=categoria_id
            )
            
            if actualizado:
                self.resultado = True
                if self.callback:
                    self.callback()
                
                self.top.destroy()
                messagebox.showinfo("Éxito", "Tarea actualizada correctamente")
            else:
                messagebox.showerror("Error", "No se pudo actualizar la tarea")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la tarea:\n{str(e)}")

class EliminarTareaDialog:
    """HU04 - Eliminar tarea con confirmación paso a paso"""
    def __init__(self, parent, tarea_id, callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("ELIMINAR TAREA - CONFIRMACIÓN")
        self.top.geometry("500x400")
        self.top.resizable(False, False)
        
        self.callback = callback
        self.tarea_id = tarea_id
        self.paso_actual = 1
        self.total_pasos = 3
        
        self._cargar_tarea()
        self._crear_widgets()
        self._centrar_ventana(parent)
    
    def _centrar_ventana(self, parent):
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _cargar_tarea(self):
        """Cargar datos de la tarea"""
        try:
            self.tarea = db.obtener_tarea(self.tarea_id)
            if not self.tarea:
                raise ValueError("Tarea no encontrada")
        except Exception as e:
            print(f"Error cargando tarea: {e}")
            self.tarea = None
    
    def _crear_widgets(self):
        if not self.tarea:
            ttk.Label(self.top, text="Error: Tarea no encontrada", 
                     font=("Arial", 12), foreground="red").pack(pady=50)
            ttk.Button(self.top, text="Cerrar", 
                      command=self.top.destroy).pack(pady=10)
            return
        
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Paso actual
        paso_frame = ttk.Frame(main_frame)
        paso_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(paso_frame, text=f"PASO {self.paso_actual} de {self.total_pasos}", 
                 font=("Arial", 11, "bold"), foreground="blue").pack(side=tk.LEFT)
        
        # Barra de progreso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        for i in range(self.total_pasos):
            color = "blue" if i < self.paso_actual else "gray"
            ttk.Label(progress_frame, text="⬤", 
                     font=("Arial", 20), foreground=color).pack(side=tk.LEFT, padx=5)
        
        # Mostrar paso actual
        self._mostrar_paso_actual(main_frame)
    
    def _mostrar_paso_actual(self, parent):
        """Mostrar contenido del paso actual"""
        # Limpiar contenido anterior
        for widget in parent.winfo_children():
            if widget not in [parent.winfo_children()[0], parent.winfo_children()[1]]:
                widget.destroy()
        
        if self.paso_actual == 1:
            self._mostrar_paso_1(parent)
        elif self.paso_actual == 2:
            self._mostrar_paso_2(parent)
        elif self.paso_actual == 3:
            self._mostrar_paso_3(parent)
    
    def _mostrar_paso_1(self, parent):
        """Paso 1: Confirmar tarea a eliminar"""
        # Título
        ttk.Label(parent, text="⚠️ CONFIRMAR TAREA A ELIMINAR", 
                 font=("Arial", 14, "bold"), foreground="orange").pack(pady=(0, 20))
        
        # Información de la tarea
        info_frame = ttk.LabelFrame(parent, text=" INFORMACIÓN DE LA TAREA ", padding="15")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_text = f"""TÍTULO: {self.tarea['titulo']}
        
DESCRIPCIÓN: {self.tarea['descripcion'] or 'Sin descripción'}
        
ESTADO: {self.tarea['estado'].upper()}
PRIORIDAD: {self.tarea['prioridad'].upper()}
CATEGORÍA: {self.tarea['categoria_nombre'] or 'Sin categoría'}"""
        
        ttk.Label(info_frame, text=info_text, font=("Arial", 10), 
                 justify=tk.LEFT).pack(anchor="w")
        
        # Advertencia
        ttk.Label(parent, text="Esta acción eliminará permanentemente la tarea.", 
                 font=("Arial", 10, "bold"), foreground="red").pack(pady=(0, 20))
        
        # Botones
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="✅ SÍ, CONTINUAR", 
                  command=self._avanzar_paso, style="Danger.TButton").pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="❌ NO, CANCELAR", 
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _mostrar_paso_2(self, parent):
        """Paso 2: Confirmación final"""
        ttk.Label(parent, text="🚨 ÚLTIMA CONFIRMACIÓN", 
                 font=("Arial", 14, "bold"), foreground="red").pack(pady=(0, 20))
        
        ttk.Label(parent, text="¿Estás absolutamente seguro de que deseas eliminar esta tarea?", 
                 font=("Arial", 12)).pack(pady=(0, 10))
        
        ttk.Label(parent, text=f"Título: {self.tarea['titulo']}", 
                 font=("Arial", 11, "bold")).pack(pady=(0, 20))
        
        # Icono de advertencia
        ttk.Label(parent, text="⚠️", font=("Arial", 40), 
                 foreground="red").pack(pady=(0, 20))
        
        ttk.Label(parent, text="Esta acción NO se puede deshacer.", 
                 font=("Arial", 10, "bold"), foreground="red").pack(pady=(0, 20))
        
        # Botones
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="🗑️ SÍ, ELIMINAR DEFINITIVAMENTE", 
                  command=self._avanzar_paso, style="Danger.TButton").pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="🔙 VOLVER", 
                  command=self._retroceder_paso).pack(side=tk.RIGHT, padx=5)
    
    def _mostrar_paso_3(self, parent):
        """Paso 3: Resultado"""
        # Intentar eliminar
        try:
            eliminado = db.eliminar_tarea(self.tarea_id)
            
            if eliminado:
                ttk.Label(parent, text="✅ TAREA ELIMINADA", 
                         font=("Arial", 16, "bold"), foreground="green").pack(pady=(0, 20))
                
                ttk.Label(parent, text="La tarea ha sido eliminada correctamente.", 
                         font=("Arial", 12)).pack(pady=(0, 20))
                
                ttk.Label(parent, text="✔️ Datos eliminados de la base de datos\n"
                         "✔️ Espacio liberado\n✔️ Cambios aplicados", 
                         font=("Arial", 10)).pack(pady=(0, 20))
                
                # Botón para cerrar
                ttk.Button(parent, text="🚪 CERRAR", 
                          command=self._cerrar_con_callback, 
                          style="Success.TButton").pack(pady=20)
                
            else:
                ttk.Label(parent, text="❌ ERROR AL ELIMINAR", 
                         font=("Arial", 16, "bold"), foreground="red").pack(pady=(0, 20))
                
                ttk.Label(parent, text="No se pudo eliminar la tarea.", 
                         font=("Arial", 12)).pack(pady=(0, 20))
                
                ttk.Button(parent, text="CERRAR", 
                          command=self.top.destroy).pack(pady=20)
                
        except Exception as e:
            ttk.Label(parent, text=f"❌ ERROR: {str(e)}", 
                     font=("Arial", 12), foreground="red").pack(pady=20)
            ttk.Button(parent, text="CERRAR", 
                      command=self.top.destroy).pack(pady=20)
    
    def _avanzar_paso(self):
        """Avanzar al siguiente paso"""
        if self.paso_actual < self.total_pasos:
            self.paso_actual += 1
            self._actualizar_paso()
    
    def _retroceder_paso(self):
        """Retroceder al paso anterior"""
        if self.paso_actual > 1:
            self.paso_actual -= 1
            self._actualizar_paso()
    
    def _actualizar_paso(self):
        """Actualizar la interfaz para el paso actual"""
        # Actualizar barra de progreso
        main_frame = self.top.winfo_children()[0]  # Frame principal
        
        # Actualizar texto del paso
        paso_frame = main_frame.winfo_children()[0]
        paso_label = paso_frame.winfo_children()[0]
        paso_label.config(text=f"PASO {self.paso_actual} de {self.total_pasos}")
        
        # Actualizar puntos de progreso
        progress_frame = main_frame.winfo_children()[1]
        for i, widget in enumerate(progress_frame.winfo_children()):
            color = "blue" if i < self.paso_actual else "gray"
            widget.config(foreground=color)
        
        # Mostrar contenido del paso
        self._mostrar_paso_actual(main_frame)
    
    def _cerrar_con_callback(self):
        """Cerrar ventana y ejecutar callback"""
        if self.callback:
            self.callback()
        self.top.destroy()
# pero por brevedad las omito. Si las necesitas, dime y te las paso completas)

# ============================================================================
# VENTANA PRINCIPAL
# ============================================================================

class SmartTaskApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("SmartTask Organizer - Gestor de Tareas")
        self.root.geometry("1200x800")
        
        # Variables
        self.filtro_categoria = tk.StringVar(value="TODAS")
        self.modo_voz_activo = False
        
        # Configurar estilos
        self._configurar_estilos()
        
        # Crear interfaz
        self._crear_interfaz()
        
        # Cargar tareas
        self._cargar_tareas()
        
        # Centrar ventana
        self._centrar_ventana()
        
        print("✅ Aplicación inicializada correctamente")
    
    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores
        style.configure('Accent.TButton', 
                       foreground='white', 
                       background='#007bff')
        style.map('Accent.TButton',
                 background=[('active', '#0069d9')])
        
        style.configure('Success.TButton',
                       foreground='white',
                       background='#28a745')
        style.map('Success.TButton',
                 background=[('active', '#218838')])
        
        style.configure('Danger.TButton',
                       foreground='white',
                       background='#dc3545')
        style.map('Danger.TButton',
                 background=[('active', '#c82333')])
    
    def _centrar_ventana(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabecera
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="SmartTask Organizer", 
                 font=("Arial", 20, "bold")).pack(side=tk.LEFT)
        
        # Botones de acción
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="🎤 VOZ", 
                  command=self._alternar_modo_voz,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="+ NUEVA", 
                  command=self._abrir_crear_tarea,
                  style="Success.TButton").pack(side=tk.LEFT, padx=2)
        
        # Filtros (HU02)
        filtro_frame = ttk.Frame(main_frame)
        filtro_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filtro_frame, text="Filtrar:", 
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
        
        categorias = db.obtener_categorias()
        filtros = ["TODAS"] + [cat['nombre'] for cat in categorias]
        
        for filtro in filtros:
            ttk.Radiobutton(filtro_frame, text=filtro, 
                           variable=self.filtro_categoria,
                           value=filtro, 
                           command=self._cargar_tareas).pack(side=tk.LEFT, padx=5)
        
        # Treeview para tareas
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Título", "Descripción", "Fecha Límite", "Estado", "Prioridad", "Categoría")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        # Configurar columnas
        column_widths = {
            "ID": 50,
            "Título": 200,
            "Descripción": 250,
            "Fecha Límite": 100,
            "Estado": 100,
            "Prioridad": 80,
            "Categoría": 100
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[col])
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configurar expansión
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Botones de acción
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="📝 Editar", 
                  command=self._editar_tarea).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="🗑️ Eliminar", 
                  command=self._eliminar_tarea,
                  style="Danger.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="✅ Completar", 
                  command=self._completar_tarea,
                  style="Success.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="🔄 Actualizar", 
                  command=self._cargar_tareas).pack(side=tk.RIGHT, padx=5)
        
        # Estadísticas
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.lbl_stats = ttk.Label(stats_frame, text="Cargando estadísticas...")
        self.lbl_stats.pack(anchor="w")
        
        # Configurar expansión
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def _cargar_tareas(self):
        """HU02 - Listar todas las tareas"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filtro = self.filtro_categoria.get()
        if filtro == "TODAS":
            filtro = None
        
        tareas = db.obtener_todas_tareas(filtro)
        
        for tarea in tareas:
            fecha = ""
            if tarea['fecha_limite']:
                try:
                    fecha_obj = datetime.strptime(tarea['fecha_limite'], "%Y-%m-%d")
                    fecha = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha = tarea['fecha_limite']
            
            estado = tarea['estado'].upper()
            
            # HU06 - Verificar si está vencida
            if tarea['estado'] == 'pendiente' and tarea['fecha_limite']:
                try:
                    fecha_limite = datetime.strptime(tarea['fecha_limite'], "%Y-%m-%d").date()
                    if fecha_limite < date.today():
                        estado = "VENCIDA"
                        db.actualizar_tarea(tarea['id'], estado='vencida')
                except:
                    pass
            
            item_id = self.tree.insert("", tk.END, values=(
                tarea['id'],
                tarea['titulo'],
                tarea['descripcion'] or "",
                fecha,
                estado,
                tarea['prioridad'].upper(),
                tarea['categoria_nombre'] or "Sin categoría"
            ))
            
            # Colorear
            if estado == "COMPLETADA":
                self.tree.item(item_id, tags=('completada',))
            elif estado == "VENCIDA":
                self.tree.item(item_id, tags=('vencida',))
            elif tarea['prioridad'] == 'alta':
                self.tree.item(item_id, tags=('alta',))
        
        self.tree.tag_configure('completada', background='#d4edda')
        self.tree.tag_configure('vencida', background='#f8d7da')
        self.tree.tag_configure('alta', background='#fff3cd')
        
        self._actualizar_estadisticas()
    
    def _actualizar_estadisticas(self):
        stats = db.obtener_estadisticas()
        texto = f"📊 Total: {stats['total']} | ✅ Completadas: {stats['completadas']} | ⏳ Pendientes: {stats['pendientes']} | ⚠️ Vencidas: {stats['vencidas']}"
        self.lbl_stats.config(text=texto)
   
    def _abrir_crear_tarea(self):
        """HU01 - Crear nueva tarea CON VOZ"""
        # Importar aquí para evitar problemas de importación circular
        try:
            from app.voice import voice_assistant
            voz_disponible = voice_assistant.voice_available
        except:
            voz_disponible = False
            voice_assistant = None
    
        dialog = CrearTareaDialog(self.root, self._cargar_tareas, voice_assistant)
        self.root.wait_window(dialog.top)
    
    def _editar_tarea(self):
        """HU03 - Editar tarea"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para editar")
            return
    
        item = seleccion[0]
        tarea_id = self.tree.item(item, 'values')[0]
    
        dialog = EditarTareaDialog(self.root, tarea_id, self._cargar_tareas)
        self.root.wait_window(dialog.top)
    
    def _eliminar_tarea(self):
        """HU04 - Eliminar tarea"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para eliminar")
            return
        
        item = seleccion[0]
        valores = self.tree.item(item, 'values')
        tarea_id = valores[0]
        titulo = valores[1]
        
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la tarea:\n\n'{titulo}'?\n\nEsta acción no se puede deshacer."
        )
        
        if respuesta:
            if db.eliminar_tarea(tarea_id):
                self._cargar_tareas()
                messagebox.showinfo("Éxito", "Tarea eliminada correctamente")
            else:
                messagebox.showerror("Error", "No se pudo eliminar la tarea")
    
    def _completar_tarea(self):
        """HU05 - Marcar como completada"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para completar")
            return
        
        item = seleccion[0]
        tarea_id = self.tree.item(item, 'values')[0]
        titulo = self.tree.item(item, 'values')[1]
        
        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿Marcar '{titulo}' como completada?"
        )
        
        if respuesta:
            if db.marcar_como_completada(tarea_id):
                self._cargar_tareas()
                messagebox.showinfo("Éxito", "Tarea marcada como completada")
            else:
                messagebox.showerror("Error", "No se pudo completar la tarea")
    
    def _alternar_modo_voz(self):
        """Alternar modo voz"""
        if not self.modo_voz_activo:
            self.modo_voz_activo = True
            
            if voice_assistant.iniciar_modo_voz():
                messagebox.showinfo(
                    "Modo Voz", 
                    "Modo voz activado.\n\n"
                    "Instrucciones:\n"
                    "1. Los comandos se ingresan por TECLADO en la terminal\n"
                    "2. La respuesta se escuchará por ALTAVOCES\n"
                    "3. Escribe 'ayuda' para ver comandos\n"
                    "4. Escribe 'salir' para terminar"
                )
                
                # Ejecutar en segundo plano
                thread = threading.Thread(target=self._ejecutar_modo_voz, daemon=True)
                thread.start()
            else:
                self.modo_voz_activo = False
                messagebox.showerror("Error", "No se pudo iniciar el modo voz")
        else:
            self.modo_voz_activo = False
            voice_assistant.detener_modo_voz()
            messagebox.showinfo("Modo Voz", "Modo voz desactivado")
    
    def _ejecutar_modo_voz(self):
        """Ejecutar modo voz en segundo plano"""
        while self.modo_voz_activo:
            try:
                comando = voice_assistant.escuchar(timeout=10)
                
                if comando:
                    if "salir" in comando or "terminar" in comando:
                        self.modo_voz_activo = False
                        voice_assistant.hablar("Saliendo del modo voz")
                        break
                    elif "crear tarea" in comando:
                        voice_assistant.hablar("Para crear una tarea, usa el botón 'NUEVA' en la interfaz")
                    elif "listar tareas" in comando:
                        voice_assistant.hablar(f"Tienes {len(self.tree.get_children())} tareas en la lista")
                    elif "ayuda" in comando:
                        voice_assistant.hablar("Comandos: crear tarea, listar tareas, ayuda, salir")
                    else:
                        voice_assistant.hablar(f"Comando '{comando}' recibido")
            except:
                pass

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    """Función principal"""
    try:
        root = tk.Tk()
        app = SmartTaskApp(root)
        root.mainloop()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    print("="*60)
    print("SMARTTASK ORGANIZER - Iniciando...")
    print("="*60)
    main()