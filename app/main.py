"""
SmartTask Organizer - Aplicación principal
Gestor de tareas con voz, categorías y fechas límite
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import threading
import time

# Importar nuestros módulos
from app.database import db
from app.voice import voice_assistant

# ============================================================================
# CLASES PARA DIÁLOGOS
# ============================================================================

class CrearTareaDialog:
    def __init__(self, parent, callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("NUEVA TAREA")
        self.top.geometry("500x500")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()
        
        self.callback = callback
        self.resultado = False
        
        self._crear_widgets()
        self._centrar_ventana()
    
    def _centrar_ventana(self):
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _crear_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="NUEVA TAREA", 
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, 
                                                 pady=(0, 20), sticky="w")
        
        # Campos
        campos = [
            ("Título *", "entry", ""),
            ("Descripción", "text", ""),
            ("Fecha Límite (DD/MM/AAAA)", "entry", ""),
            ("Prioridad", "combo_pri", "media"),
            ("Categoría", "combo_cat", "")
        ]
        
        self.widgets = {}
        row = 1
        
        for label_text, tipo, valor_default in campos:
            # Etiqueta
            ttk.Label(main_frame, text=label_text).grid(row=row, column=0, 
                                                       padx=(0, 10), pady=5, 
                                                       sticky="w")
            
            # Widget
            if tipo == "entry":
                widget = ttk.Entry(main_frame, width=40)
                if valor_default:
                    widget.insert(0, valor_default)
                widget.grid(row=row, column=1, pady=5, sticky="ew")
                
            elif tipo == "text":
                widget = tk.Text(main_frame, width=40, height=4)
                widget.grid(row=row, column=1, pady=5, sticky="ew")
                
            elif tipo == "combo_pri":
                widget = ttk.Combobox(main_frame, values=["baja", "media", "alta"], 
                                     state="readonly", width=38)
                widget.set(valor_default)
                widget.grid(row=row, column=1, pady=5, sticky="ew")
                
            elif tipo == "combo_cat":
                categorias = db.obtener_categorias()
                valores = ["Seleccionar..."] + [cat['nombre'] for cat in categorias]
                widget = ttk.Combobox(main_frame, values=valores, 
                                     state="readonly", width=38)
                widget.set("Seleccionar...")
                widget.grid(row=row, column=1, pady=5, sticky="ew")
            
            self.widgets[label_text.split()[0].lower()] = widget
            row += 1
        
        # Expansión
        main_frame.columnconfigure(1, weight=1)
        
        # Separador
        ttk.Separator(main_frame, orient="horizontal").grid(row=row, column=0, 
                                                           columnspan=2, 
                                                           pady=20, sticky="ew")
        row += 1
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="GUARDAR", width=15,
                  command=self._guardar,
                  style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="CANCELAR", width=15,
                  command=self._cancelar).pack(side=tk.RIGHT, padx=5)
    
    def _guardar(self):
        titulo = self.widgets['título'].get().strip()
        if not titulo:
            messagebox.showerror("Error", "El título es obligatorio")
            return
        
        # Descripción
        descripcion = ""
        if 'descripción' in self.widgets:
            descripcion = self.widgets['descripción'].get("1.0", tk.END).strip()
        
        # Fecha
        fecha_text = self.widgets['fecha'].get().strip()
        fecha_sql = None
        if fecha_text:
            try:
                fecha_obj = datetime.strptime(fecha_text, "%d/%m/%Y")
                fecha_sql = fecha_obj.strftime("%Y-%m-%d")
                
                if fecha_obj.date() < date.today():
                    messagebox.showerror("Error", "La fecha límite no puede ser en el pasado")
                    return
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use DD/MM/AAAA")
                return
        
        # Prioridad y categoría
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
            messagebox.showinfo("Éxito", "Tarea creada correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la tarea:\n{str(e)}")
    
    def _cancelar(self):
        self.top.destroy()

class EditarTareaDialog:
    def __init__(self, parent, tarea_id, callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("EDITAR TAREA")
        self.top.geometry("500x550")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()
        
        self.tarea_id = tarea_id
        self.callback = callback
        self.resultado = False
        
        self.tarea = db.obtener_tarea(tarea_id)
        if not self.tarea:
            messagebox.showerror("Error", "No se encontró la tarea")
            self.top.destroy()
            return
        
        self._crear_widgets()
        self._centrar_ventana()
    
    def _centrar_ventana(self):
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _crear_widgets(self):
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="EDITAR TAREA", 
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, 
                                                 pady=(0, 20), sticky="w")
        
        # Campos
        fecha_formateada = ""
        if self.tarea['fecha_limite']:
            try:
                fecha_obj = datetime.strptime(self.tarea['fecha_limite'], "%Y-%m-%d")
                fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
            except:
                fecha_formateada = self.tarea['fecha_limite']
        
        campos = [
            ("Título *", "entry", self.tarea['titulo']),
            ("Descripción", "text", self.tarea['descripcion'] or ""),
            ("Fecha Límite (DD/MM/AAAA)", "entry", fecha_formateada),
            ("Estado", "combo_estado", self.tarea['estado']),
            ("Prioridad", "combo_pri", self.tarea['prioridad']),
            ("Categoría", "combo_cat", self.tarea['categoria_nombre'] or "")
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
                
            elif tipo == "combo_estado":
                widget = ttk.Combobox(main_frame, values=["pendiente", "completada", "vencida"], 
                                     state="readonly", width=38)
                widget.set(valor)
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
            
            self.widgets[label_text.split()[0].lower()] = widget
            row += 1
        
        main_frame.columnconfigure(1, weight=1)
        
        ttk.Separator(main_frame, orient="horizontal").grid(row=row, column=0, 
                                                           columnspan=2, 
                                                           pady=20, sticky="ew")
        row += 1
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="ACTUALIZAR", width=15,
                  command=self._actualizar,
                  style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="CANCELAR", width=15,
                  command=self._cancelar).pack(side=tk.RIGHT, padx=5)
    
    def _actualizar(self):
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
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use DD/MM/AAAA")
                return
        
        estado = self.widgets['estado'].get()
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
            resultado = db.actualizar_tarea(
                self.tarea_id,
                titulo=titulo,
                descripcion=descripcion,
                fecha_limite=fecha_sql,
                estado=estado,
                prioridad=prioridad,
                categoria_id=categoria_id
            )
            
            if resultado:
                self.resultado = True
                if self.callback:
                    self.callback()
                
                self.top.destroy()
                messagebox.showinfo("Éxito", "Tarea actualizada correctamente")
            else:
                messagebox.showerror("Error", "No se pudo actualizar la tarea")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la tarea:\n{str(e)}")
    
    def _cancelar(self):
        self.top.destroy()

class EliminarTareaDialog:
    def __init__(self, parent, tarea_id, callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("ELIMINAR TAREA")
        self.top.geometry("450x350")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()
        
        self.tarea_id = tarea_id
        self.callback = callback
        self.resultado = False
        
        self.tarea = db.obtener_tarea(tarea_id)
        if not self.tarea:
            messagebox.showerror("Error", "No se encontró la tarea")
            self.top.destroy()
            return
        
        self._crear_widgets()
        self._centrar_ventana()
    
    def _centrar_ventana(self):
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _crear_widgets(self):
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Primera pantalla: Información
        self.frame_info = ttk.Frame(main_frame)
        self.frame_info.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(self.frame_info, text="LISTA", 
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        ttk.Label(self.frame_info, text=f"Título: {self.tarea['titulo']}", 
                 font=("Arial", 10)).pack(anchor="w", pady=2)
        
        if self.tarea['descripcion']:
            desc = self.tarea['descripcion']
            if len(desc) > 50:
                desc = desc[:50] + "..."
            ttk.Label(self.frame_info, text=f"Descripción: {desc}",
                     font=("Arial", 10)).pack(anchor="w", pady=2)
        
        cat = self.tarea['categoria_nombre'] or 'Sin categoría'
        ttk.Label(self.frame_info, text=f"ID: #{self.tarea['id']} | Cat: {cat}",
                 font=("Arial", 10)).pack(anchor="w", pady=2)
        
        ttk.Separator(self.frame_info, orient="horizontal").pack(fill=tk.X, pady=20)
        
        ttk.Button(self.frame_info, text="ELIMINAR", 
                  command=self._mostrar_confirmacion,
                  style="Danger.TButton").pack(pady=10)
        
        # Segunda pantalla: Confirmación
        self.frame_confirm = ttk.Frame(main_frame)
    
    def _mostrar_confirmacion(self):
        self.frame_info.pack_forget()
        self.frame_confirm.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(self.frame_confirm, text="¿ELIMINAR TAREA?", 
                 font=("Arial", 12, "bold")).pack(pady=(30, 10))
        
        ttk.Label(self.frame_confirm, 
                 text="Esta acción no se puede deshacer.\nNOTA: También se eliminarán las notificaciones asociadas",
                 justify="center").pack(pady=10)
        
        btn_frame = ttk.Frame(self.frame_confirm)
        btn_frame.pack(pady=30)
        
        ttk.Button(btn_frame, text="SÍ, ELIMINAR", 
                  command=self._ejecutar_eliminacion,
                  style="Danger.TButton").pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="CANCELAR",
                  command=self._cancelar).pack(side=tk.LEFT, padx=10)
    
    def _ejecutar_eliminacion(self):
        try:
            resultado = db.eliminar_tarea(self.tarea_id)
            
            if resultado:
                self._mostrar_exito()
            else:
                messagebox.showerror("Error", "No se pudo eliminar la tarea")
                self.top.destroy()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar: {str(e)}")
            self.top.destroy()
    
    def _mostrar_exito(self):
        self.frame_confirm.pack_forget()
        
        frame_exito = ttk.Frame(self.top)
        frame_exito.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame_exito, text="✓ Tarea eliminada", 
                 font=("Arial", 12, "bold"), foreground="green").pack(pady=50)
        
        ttk.Label(frame_exito, text="La tarea ha sido eliminada del sistema").pack()
        
        self.top.after(2000, self._cerrar_con_exito)
    
    def _cerrar_con_exito(self):
        self.resultado = True
        if self.callback:
            self.callback()
        self.top.destroy()
    
    def _cancelar(self):
        self.top.destroy()

# ============================================================================
# VENTANA PRINCIPAL
# ============================================================================

class SmartTaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartTask Organizer")
        self.root.geometry("1100x750")
        
        # Variables
        self.filtro_categoria = tk.StringVar(value="TODAS")
        self.modo_voz_activo = False
        
        # Configurar estilos
        self._configurar_estilos()
        
        # Crear interfaz
        self._crear_interfaz()
        
        # Cargar datos iniciales
        self._cargar_tareas()
        
        # Centrar ventana
        self._centrar_ventana()
        
        # Iniciar verificación de tareas vencidas
        self._verificar_vencimientos()
    
    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Botones de peligro (rojo)
        style.configure('Danger.TButton', 
                       foreground='white',
                       background='#dc3545',
                       bordercolor='#dc3545')
        
        style.map('Danger.TButton',
                 background=[('active', '#c82333')],
                 bordercolor=[('active', '#c82333')])
        
        # Botones de éxito (verde)
        style.configure('Success.TButton',
                       foreground='white',
                       background='#28a745')
        
        style.map('Success.TButton',
                 background=[('active', '#218838')])
        
        # Botones primarios (azul)
        style.configure('Accent.TButton',
                       foreground='white',
                       background='#007bff')
        
        style.map('Accent.TButton',
                 background=[('active', '#0069d9')])
    
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
        
        # ===== CABECERA =====
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Título
        ttk.Label(header_frame, text="SmartTask Organizer", 
                 font=("Arial", 20, "bold")).pack(side=tk.LEFT)
        
        # Botones de acción rápida
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="🎤 VOZ", 
                  command=self._alternar_modo_voz,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="+ NUEVA", 
                  command=self._abrir_crear_tarea,
                  style="Success.TButton").pack(side=tk.LEFT, padx=2)
        
        # ===== FILTROS =====
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
        
        # ===== LISTA DE TAREAS =====
        # Frame para Treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
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
        
        # ===== BOTONES DE ACCIÓN =====
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
        
        # ===== ESTADÍSTICAS =====
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.lbl_stats = ttk.Label(stats_frame, text="Cargando estadísticas...")
        self.lbl_stats.pack(anchor="w")
        
        # ===== CONFIGURAR EXPANSIÓN =====
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def _cargar_tareas(self):
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener filtro
        filtro = self.filtro_categoria.get()
        if filtro == "TODAS":
            filtro = None
        
        # Obtener tareas
        tareas = db.obtener_todas_tareas(filtro)
        
        # Insertar en treeview
        for tarea in tareas:
            # Formatear fecha
            fecha = ""
            if tarea['fecha_limite']:
                try:
                    fecha_obj = datetime.strptime(tarea['fecha_limite'], "%Y-%m-%d")
                    fecha = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha = tarea['fecha_limite']
            
            # Determinar estado
            estado = tarea['estado'].upper()
            
            # Verificar si está vencida
            if tarea['estado'] == 'pendiente' and tarea['fecha_limite']:
                try:
                    fecha_limite = datetime.strptime(tarea['fecha_limite'], "%Y-%m-%d").date()
                    if fecha_limite < date.today():
                        estado = "VENCIDA"
                        # Actualizar en base de datos
                        db.actualizar_tarea(tarea['id'], estado='vencida')
                except:
                    pass
            
            # Insertar
            item_id = self.tree.insert("", tk.END, values=(
                tarea['id'],
                tarea['titulo'],
                tarea['descripcion'] or "",
                fecha,
                estado,
                tarea['prioridad'].upper(),
                tarea['categoria_nombre'] or "Sin categoría"
            ))
            
            # Colorear según estado
            if estado == "COMPLETADA":
                self.tree.item(item_id, tags=('completada',))
            elif estado == "VENCIDA":
                self.tree.item(item_id, tags=('vencida',))
            elif tarea['prioridad'] == 'alta':
                self.tree.item(item_id, tags=('alta',))
        
        # Configurar tags
        self.tree.tag_configure('completada', background='#d4edda')
        self.tree.tag_configure('vencida', background='#f8d7da', foreground='#721c24')
        self.tree.tag_configure('alta', background='#fff3cd')
        
        # Actualizar estadísticas
        self._actualizar_estadisticas()
    
    def _actualizar_estadisticas(self):
        stats = db.obtener_estadisticas()
        texto = f"📊 Total: {stats['total']} | ✅ Completadas: {stats['completadas']} | ⏳ Pendientes: {stats['pendientes']} | ⚠️ Vencidas: {stats['vencidas']}"
        self.lbl_stats.config(text=texto)
    
    def _verificar_vencimientos(self):
        """Verifica tareas vencidas periódicamente"""
        tareas = db.obtener_todas_tareas()
        hoy = date.today()
        
        for tarea in tareas:
            if tarea['estado'] == 'pendiente' and tarea['fecha_limite']:
                try:
                    fecha_limite = datetime.strptime(tarea['fecha_limite'], "%Y-%m-%d").date()
                    if fecha_limite < hoy:
                        db.actualizar_tarea(tarea['id'], estado='vencida')
                except:
                    pass
        
        # Programar próxima verificación (cada minuto)
        self.root.after(60000, self._verificar_vencimientos)
    
    def _abrir_crear_tarea(self):
        dialog = CrearTareaDialog(self.root, self._cargar_tareas)
        self.root.wait_window(dialog.top)
    
    def _editar_tarea(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para editar")
            return
        
        item = seleccion[0]
        tarea_id = self.tree.item(item, 'values')[0]
        
        dialog = EditarTareaDialog(self.root, tarea_id, self._cargar_tareas)
        self.root.wait_window(dialog.top)
    
    def _eliminar_tarea(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para eliminar")
            return
        
        item = seleccion[0]
        valores = self.tree.item(item, 'values')
        tarea_id = valores[0]
        
        dialog = EliminarTareaDialog(self.root, tarea_id, self._cargar_tareas)
        self.root.wait_window(dialog.top)
    
    def _completar_tarea(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para completar")
            return
        
        item = seleccion[0]
        tarea_id = self.tree.item(item, 'values')[0]
        tarea_titulo = self.tree.item(item, 'values')[1]
        
        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿Marcar '{tarea_titulo}' como completada?"
        )
        
        if respuesta:
            if db.marcar_como_completada(tarea_id):
                self._cargar_tareas()
                messagebox.showinfo("Éxito", "Tarea marcada como completada")
            else:
                messagebox.showerror("Error", "No se pudo completar la tarea")
    
    def _alternar_modo_voz(self):
        if not self.modo_voz_activo:
            self.modo_voz_activo = True
            messagebox.showinfo("Modo Voz", "Modo voz activado. Di 'ayuda' para ver comandos.")
            
            # Iniciar modo voz en un hilo separado
            thread = threading.Thread(target=self._ejecutar_modo_voz)
            thread.daemon = True
            thread.start()
        else:
            self.modo_voz_activo = False
            voice_assistant.detener_modo_voz()
            messagebox.showinfo("Modo Voz", "Modo voz desactivado")
    
    def _ejecutar_modo_voz(self):
        voice_assistant.iniciar_modo_voz()
        self.modo_voz_activo = False

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    try:
        root = tk.Tk()
        app = SmartTaskApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()