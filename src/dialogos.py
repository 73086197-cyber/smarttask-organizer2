"""
Módulo de diálogos (ventanas emergentes) para SmartTask Organizer.

Contiene las clases de diálogo que implementan las operaciones CRUD
sobre tareas. Cada diálogo es una ventana Toplevel de Tkinter con
el tema visual Nord.

Clases:
    - CrearTareaDialog: Formulario de creación con dictado por voz (HU01, HU11).
    - EditarTareaDialog: Formulario de edición de tareas existentes (HU03).
    - EliminarTareaDialog: Confirmación paso a paso para eliminar (HU04).
    - GestionCategoriasDialog: Gestión de categorías (crear, eliminar).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
from src.database import db

class CrearTareaDialog:
    """Diálogo para crear una nueva tarea con soporte de dictado por voz (HU01, HU11).

    Presenta un formulario con campos para título, descripción, fecha
    límite (HU06), prioridad y categoría (HU09). Incluye un botón de
    dictado por voz que permite rellenar los campos automáticamente
    usando el micrófono (HU11).

    Attributes:
        top (tk.Toplevel): Ventana del diálogo.
        callback (callable): Función a ejecutar tras guardar exitosamente.
        resultado (bool): True si la tarea se guardó correctamente.
        voice_assistant: Instancia del asistente de voz (o DummyVoice).
        datos_voz (dict): Datos extraídos del último dictado por voz.
        widgets (dict): Diccionario de widgets del formulario por nombre.
    """

    def __init__(self, parent, callback=None, voice_assistant=None):
        """Inicializa el diálogo de creación de tarea.

        Args:
            parent (tk.Tk): Ventana padre sobre la cual se centra el diálogo.
            callback (callable): Función sin argumentos que se ejecuta
                después de guardar exitosamente (para refrescar la lista).
            voice_assistant: Instancia de VoiceAssistant o DummyVoice.
                Si tiene voice_available=True, habilita el botón de dictado.
        """
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
        """Centra el diálogo respecto a la ventana padre.

        Args:
            parent (tk.Tk): Ventana padre para calcular la posición central.
        """
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _crear_widgets(self):
        """Construye todos los widgets del formulario de creación.

        Crea: cabecera con botón de voz, instrucciones de dictado,
        campos del formulario (título, descripción, fecha, prioridad,
        categoría) y botones de acción (Guardar, Limpiar, Cancelar).
        """
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
                widget = tk.Text(main_frame, width=45, height=5, 
                                bg="#3B4252", fg="#ECEFF4", insertbackground="#ECEFF4", relief="flat")
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
        """Activa el reconocimiento de voz para dictar una tarea completa (HU11).

        Verifica que el asistente de voz esté disponible, muestra una
        ventana de espera y ejecuta el reconocimiento en un hilo separado
        para no bloquear la interfaz. Al terminar, rellena los campos
        del formulario con los datos del dictado.
        """
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
        """Callback ejecutado desde el hilo de voz al recibir datos.

        Args:
            datos (dict): Datos parseados del dictado con claves:
                'titulo', 'descripcion', 'fecha', 'prioridad',
                'categoria', 'autoguardar'.
        """
        self.datos_voz = datos
        print(f"Datos de voz recibidos en callback: {datos}")
    
    def _rellenar_campos_desde_voz(self, datos):
        """Rellena los campos del formulario con los datos del dictado (HU11).

        Asigna cada valor del diccionario al widget correspondiente.
        Si se detectó la palabra 'terminar' (autoguardar=True), pregunta
        al usuario si desea guardar automáticamente.

        Args:
            datos (dict): Datos parseados del dictado por voz.
        """
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
        """Limpia todos los campos del formulario a sus valores por defecto.

        Entries se vacían, Text se limpia, y Comboboxes vuelven a
        'media' (prioridad) o 'Seleccionar...' (categoría).
        """
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
        """Valida los campos y guarda la nueva tarea en la base de datos (HU01).

        Validaciones:
            - Título obligatorio.
            - Fecha en formato DD/MM/AAAA si se proporciona (HU06).
            - Fecha no puede ser en el pasado.

        Si la validación pasa, crea la tarea, ejecuta el callback
        y cierra el diálogo.
        """
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


class EditarTareaDialog:
    """Diálogo para editar una tarea existente (HU03).

    Carga los datos actuales de la tarea desde la base de datos y
    presenta un formulario prellenado con los valores existentes.
    Permite modificar: título, descripción, fecha límite, prioridad,
    categoría y estado.

    Attributes:
        top (tk.Toplevel): Ventana del diálogo.
        callback (callable): Función a ejecutar tras actualizar.
        tarea_id (int): ID de la tarea a editar.
        resultado (bool): True si se actualizó correctamente.
        tarea (sqlite3.Row): Datos actuales de la tarea.
        widgets (dict): Diccionario de widgets del formulario.
    """

    def __init__(self, parent, tarea_id, callback=None):
        """Inicializa el diálogo de edición.

        Args:
            parent (tk.Tk): Ventana padre.
            tarea_id (int): ID de la tarea a editar.
            callback (callable): Función para refrescar la lista.
        """
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
        """Centra el diálogo respecto a la ventana padre.

        Args:
            parent (tk.Tk): Ventana padre.
        """
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _cargar_tarea(self):
        """Carga los datos de la tarea desde la base de datos.

        Consulta la tarea por su ID. Si no se encuentra, establece
        self.tarea como None y el diálogo mostrará un mensaje de error.
        """
        try:
            self.tarea = db.obtener_tarea(self.tarea_id)
            if not self.tarea:
                raise ValueError("Tarea no encontrada")
        except Exception as e:
            print(f"Error cargando tarea: {e}")
            self.tarea = None
    
    def _crear_widgets(self):
        """Construye los widgets del formulario de edición.

        Si la tarea no se encontró, muestra un mensaje de error.
        Si se encontró, crea campos prellenados con los valores
        actuales de la tarea y botones Actualizar/Cancelar.
        """
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
                widget = tk.Text(main_frame, width=40, height=4,
                                bg="#3B4252", fg="#ECEFF4", insertbackground="#ECEFF4", relief="flat")
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
        """Convierte una fecha de formato SQL a formato de visualización.

        Args:
            fecha_sql (str): Fecha en formato SQL 'YYYY-MM-DD'.

        Returns:
            str: Fecha formateada como 'DD/MM/AAAA'. Vacío si es None.
        """
        if not fecha_sql:
            return ""
        try:
            fecha_obj = datetime.strptime(fecha_sql, "%Y-%m-%d")
            return fecha_obj.strftime("%d/%m/%Y")
        except ValueError:
            return fecha_sql
    
    def _actualizar(self):
        """Valida los campos y actualiza la tarea en la base de datos (HU03).

        Realiza las mismas validaciones que _guardar en CrearTareaDialog.
        Actualiza todos los campos de la tarea incluyendo el estado.
        """
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
    """Diálogo de eliminación con confirmación paso a paso (HU04).

    Implementa un flujo de 3 pasos para evitar eliminaciones accidentales:
        - Paso 1: Muestra la información de la tarea y pide confirmación.
        - Paso 2: Última confirmación con advertencia.
        - Paso 3: Ejecuta la eliminación y muestra el resultado.

    Attributes:
        top (tk.Toplevel): Ventana del diálogo.
        callback (callable): Función a ejecutar tras eliminar.
        tarea_id (int): ID de la tarea a eliminar.
        paso_actual (int): Paso actual del flujo (1, 2 o 3).
        total_pasos (int): Total de pasos (siempre 3).
        tarea (sqlite3.Row): Datos de la tarea a eliminar.
    """

    def __init__(self, parent, tarea_id, callback=None):
        """Inicializa el diálogo de eliminación.

        Args:
            parent (tk.Tk): Ventana padre.
            tarea_id (int): ID de la tarea a eliminar.
            callback (callable): Función para refrescar la lista.
        """
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
        """Centra el diálogo respecto a la ventana padre.

        Args:
            parent (tk.Tk): Ventana padre.
        """
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _cargar_tarea(self):
        """Carga los datos de la tarea a eliminar desde la base de datos."""
        try:
            self.tarea = db.obtener_tarea(self.tarea_id)
            if not self.tarea:
                raise ValueError("Tarea no encontrada")
        except Exception as e:
            print(f"Error cargando tarea: {e}")
            self.tarea = None
    
    def _crear_widgets(self):
        """Construye los widgets iniciales del diálogo de eliminación.

        Muestra indicador de paso actual, barra de progreso visual
        y el contenido del paso 1.
        """
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
                 font=("Arial", 11, "bold"), foreground="#88C0D0").pack(side=tk.LEFT)
        
        # Barra de progreso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        for i in range(self.total_pasos):
            color = "#88C0D0" if i < self.paso_actual else "gray"
            ttk.Label(progress_frame, text="⬤", 
                     font=("Arial", 20), foreground=color).pack(side=tk.LEFT, padx=5)
        
        # Mostrar paso actual
        self._mostrar_paso_actual(main_frame)
    
    def _mostrar_paso_actual(self, parent):
        """Renderiza el contenido correspondiente al paso actual.

        Limpia el contenido anterior (excepto cabecera y barra de
        progreso) y llama al método del paso correspondiente.

        Args:
            parent (ttk.Frame): Frame padre donde renderizar el contenido.
        """
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
        """Paso 1: Muestra la información de la tarea y pide confirmación.

        Args:
            parent (ttk.Frame): Frame donde renderizar.
        """
        # Título
        ttk.Label(parent, text="⚠️ CONFIRMAR TAREA A ELIMINAR", 
                 font=("Arial", 14, "bold"), foreground="#EBCB8B").pack(pady=(0, 20))
        
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
                 font=("Arial", 10, "bold"), foreground="#BF616A").pack(pady=(0, 20))
        
        # Botones
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="✅ SÍ, CONTINUAR", 
                  command=self._avanzar_paso, style="Danger.TButton").pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="❌ NO, CANCELAR", 
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _mostrar_paso_2(self, parent):
        """Paso 2: Última confirmación antes de eliminar.

        Args:
            parent (ttk.Frame): Frame donde renderizar.
        """
        ttk.Label(parent, text="🚨 ÚLTIMA CONFIRMACIÓN", 
                 font=("Arial", 14, "bold"), foreground="#BF616A").pack(pady=(0, 20))
        
        ttk.Label(parent, text="¿Estás absolutamente seguro de que deseas eliminar esta tarea?", 
                 font=("Arial", 12)).pack(pady=(0, 10))
        
        ttk.Label(parent, text=f"Título: {self.tarea['titulo']}", 
                 font=("Arial", 11, "bold")).pack(pady=(0, 20))
        
        # Icono de advertencia
        ttk.Label(parent, text="⚠️", font=("Arial", 40), 
                 foreground="#BF616A").pack(pady=(0, 20))
        
        ttk.Label(parent, text="Esta acción NO se puede deshacer.", 
                 font=("Arial", 10, "bold"), foreground="#BF616A").pack(pady=(0, 20))
        
        # Botones
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="🗑️ SÍ, ELIMINAR DEFINITIVAMENTE", 
                  command=self._avanzar_paso, style="Danger.TButton").pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="🔙 VOLVER", 
                  command=self._retroceder_paso).pack(side=tk.RIGHT, padx=5)
    
    def _mostrar_paso_3(self, parent):
        """Paso 3: Ejecuta la eliminación y muestra el resultado.

        Llama a db.eliminar_tarea() y muestra éxito o error.

        Args:
            parent (ttk.Frame): Frame donde renderizar.
        """
        # Intentar eliminar
        try:
            eliminado = db.eliminar_tarea(self.tarea_id)
            
            if eliminado:
                ttk.Label(parent, text="✅ TAREA ELIMINADA", 
                         font=("Arial", 16, "bold"), foreground="#A3BE8C").pack(pady=(0, 20))
                
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
                         font=("Arial", 16, "bold"), foreground="#BF616A").pack(pady=(0, 20))
                
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
        """Avanza al siguiente paso del flujo de eliminación."""
        if self.paso_actual < self.total_pasos:
            self.paso_actual += 1
            self._actualizar_paso()
    
    def _retroceder_paso(self):
        """Retrocede al paso anterior del flujo de eliminación."""
        if self.paso_actual > 1:
            self.paso_actual -= 1
            self._actualizar_paso()
    
    def _actualizar_paso(self):
        """Actualiza la interfaz visual para reflejar el paso actual.

        Actualiza el texto del indicador de paso, los colores de la
        barra de progreso y renderiza el contenido del nuevo paso.
        """
        # Actualizar barra de progreso
        main_frame = self.top.winfo_children()[0]  # Frame principal
        
        # Actualizar texto del paso
        paso_frame = main_frame.winfo_children()[0]
        paso_label = paso_frame.winfo_children()[0]
        paso_label.config(text=f"PASO {self.paso_actual} de {self.total_pasos}")
        
        # Actualizar puntos de progreso
        progress_frame = main_frame.winfo_children()[1]
        for i, widget in enumerate(progress_frame.winfo_children()):
            color = "#88C0D0" if i < self.paso_actual else "gray"
            widget.config(foreground=color)
        
        # Mostrar contenido del paso
        self._mostrar_paso_actual(main_frame)
    
    def _cerrar_con_callback(self):
        """Cierra el diálogo y ejecuta el callback para refrescar la lista."""
        if self.callback:
            self.callback()
        self.top.destroy()


class GestionCategoriasDialog:
    """Diálogo para gestionar categorías (crear y eliminar).

    Permite al usuario agregar nuevas categorías y eliminar categorías
    existentes. Valida integridad referencial: no permite eliminar
    categorías que tengan tareas asignadas.

    Attributes:
        top (tk.Toplevel): Ventana del diálogo.
        callback (callable): Función a ejecutar al cerrar.
        tree (ttk.Treeview): Tabla de categorías existentes.
    """

    def __init__(self, parent, callback=None):
        """Inicializa el diálogo de gestión de categorías.

        Args:
            parent (tk.Tk): Ventana padre.
            callback (callable): Función a ejecutar al cerrar el diálogo
                para refrescar filtros y tareas.
        """
        self.top = tk.Toplevel(parent)
        self.top.title("GESTIÓN DE CATEGORÍAS")
        self.top.geometry("650x620")
        self.top.minsize(600, 550)
        self.top.configure(bg='#2E3440')
        self.top.transient(parent)
        self.top.grab_set()

        self.callback = callback

        self._crear_interfaz()
        self._cargar_categorias()

        self.top.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _crear_interfaz(self):
        """Construye los widgets del diálogo de gestión.

        Crea la tabla de categorías, formulario para agregar
        y botones de acción (agregar, eliminar, cerrar).
        """
        main_frame = ttk.Frame(self.top, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame, text="⚙️ GESTIÓN DE CATEGORÍAS",
            font=("Segoe UI", 16, "bold"), foreground="#88C0D0"
        ).pack(pady=(0, 10))

        # === TABLA DE CATEGORÍAS ===
        ttk.Label(
            main_frame, text="Categorías existentes:",
            font=("Segoe UI", 10), foreground="#D8DEE9"
        ).pack(anchor=tk.W)

        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        columns = ("ID", "Nombre", "Descripción", "Tareas")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            selectmode="browse", height=5
        )

        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.heading("Tareas", text="Nº Tareas")

        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Nombre", width=150)
        self.tree.column("Descripción", width=250)
        self.tree.column("Tareas", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # === BOTÓN ELIMINAR (debajo de la tabla) ===
        tk.Button(
            main_frame, text="🗑️  ELIMINAR CATEGORÍA SELECCIONADA",
            command=self._eliminar_categoria,
            bg="#BF616A", fg="#ECEFF4", activebackground="#A5505A",
            font=("Segoe UI", 10, "bold"), relief="flat",
            cursor="hand2", padx=10, pady=5
        ).pack(fill=tk.X, pady=(0, 15))

        # === SEPARADOR ===
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(
            fill=tk.X, pady=5
        )

        # === FORMULARIO AGREGAR ===
        form_frame = ttk.LabelFrame(
            main_frame, text="  ➕ AGREGAR NUEVA CATEGORÍA  ",
            padding="15"
        )
        form_frame.pack(fill=tk.X, pady=(10, 10))

        # Nombre
        row1 = ttk.Frame(form_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(
            row1, text="Nombre:", width=12,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        self.entry_nombre = ttk.Entry(row1, width=35)
        self.entry_nombre.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Descripción
        row2 = ttk.Frame(form_frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(
            row2, text="Descripción:", width=12,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        self.entry_desc = ttk.Entry(row2, width=35)
        self.entry_desc.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # BOTÓN AGREGAR — grande, verde, ancho completo
        tk.Button(
            form_frame, text="✅  AGREGAR CATEGORÍA",
            command=self._agregar_categoria,
            bg="#A3BE8C", fg="#2E3440", activebackground="#8FAA7B",
            font=("Segoe UI", 12, "bold"), relief="flat",
            cursor="hand2", padx=20, pady=8
        ).pack(fill=tk.X, pady=(10, 0))

        # === BOTÓN CERRAR ===
        tk.Button(
            main_frame, text="🚪  CERRAR",
            command=self._cerrar,
            bg="#4C566A", fg="#ECEFF4", activebackground="#3B4252",
            font=("Segoe UI", 10), relief="flat",
            cursor="hand2", padx=10, pady=5
        ).pack(fill=tk.X, pady=(10, 0))

    def _cargar_categorias(self):
        """Carga las categorías en la tabla.

        Consulta la base de datos y muestra cada categoría con
        el número de tareas asignadas a ella.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        categorias = db.obtener_categorias()
        tareas = db.obtener_todas_tareas()

        for cat in categorias:
            num_tareas = sum(
                1 for t in tareas
                if t.get('categoria_id') == cat['id']
            )
            self.tree.insert("", tk.END, values=(
                cat['id'],
                cat['nombre'],
                cat.get('descripcion', ''),
                num_tareas
            ))

    def _agregar_categoria(self):
        """Agrega una nueva categoría a la base de datos.

        Valida que el nombre no esté vacío y no sea duplicado.
        Muestra mensaje de éxito o error según corresponda.
        """
        nombre = self.entry_nombre.get().strip()
        descripcion = self.entry_desc.get().strip()

        if not nombre:
            messagebox.showwarning(
                "Campo requerido",
                "El nombre de la categoría es obligatorio.",
                parent=self.top
            )
            return

        try:
            db.crear_categoria(nombre, descripcion)
            messagebox.showinfo(
                "Éxito",
                f"Categoría '{nombre}' creada correctamente.",
                parent=self.top
            )
            self.entry_nombre.delete(0, tk.END)
            self.entry_desc.delete(0, tk.END)
            self._cargar_categorias()

        except ValueError as e:
            messagebox.showwarning(
                "Error de validación", str(e),
                parent=self.top
            )
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo crear la categoría: {e}",
                parent=self.top
            )

    def _eliminar_categoria(self):
        """Elimina la categoría seleccionada de la tabla.

        Valida integridad referencial: no permite eliminar
        categorías con tareas asignadas. Pide confirmación
        antes de eliminar.
        """
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Selección requerida",
                "Selecciona una categoría de la tabla.",
                parent=self.top
            )
            return

        values = self.tree.item(selected[0], 'values')
        cat_id = int(values[0])
        cat_nombre = values[1]
        num_tareas = int(values[3])

        if num_tareas > 0:
            messagebox.showwarning(
                "No se puede eliminar",
                f"La categoría '{cat_nombre}' tiene {num_tareas} "
                f"tarea(s) asignada(s).\n\n"
                f"Reasigna o elimina las tareas primero.",
                parent=self.top
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la categoría '{cat_nombre}'?",
            parent=self.top
        )

        if confirmar:
            try:
                db.eliminar_categoria(cat_id)
                messagebox.showinfo(
                    "Éxito",
                    f"Categoría '{cat_nombre}' eliminada.",
                    parent=self.top
                )
                self._cargar_categorias()

            except ValueError as e:
                messagebox.showwarning(
                    "Error", str(e), parent=self.top
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"No se pudo eliminar: {e}",
                    parent=self.top
                )

    def _cerrar(self):
        """Cierra el diálogo y ejecuta el callback."""
        if self.callback:
            self.callback()
        self.top.destroy()
