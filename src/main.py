"""
Aplicación principal de SmartTask Organizer.

Contiene la clase SmartTaskApp que implementa la ventana principal de la
aplicación usando Tkinter con el tema visual Nord. Coordina todos los
módulos del sistema: base de datos, diálogos, voz y deshacer.

Historias de usuario implementadas directamente en este módulo:
    - HU01: Crear tarea (abre diálogo de creación)
    - HU02: Listar tareas (carga y muestra en Treeview)
    - HU03: Editar tarea (abre diálogo de edición / doble clic)
    - HU04: Eliminar tarea (confirmación y eliminación)
    - HU05: Completar tarea (marca como completada)
    - HU06: Fecha límite (validación y visualización)
    - HU07: Detectar vencidas (cambia estado automáticamente)
    - HU10: Filtrar por categoría (RadioButtons de filtro)
    - HU11: Tarea por voz (modo voz interactivo)
    - HU12: Notificaciones (alerta de tareas vencidas al iniciar)

Funcionalidades adicionales:
    - Estadísticas y gráficos con matplotlib
    - Exportación a CSV compatible con Excel
    - Deshacer acciones con Ctrl+Z (UndoManager)
    - Tema visual Nord oscuro / Nord claro (toggle día/noche)
    - Buscador en tiempo real por título de tarea
    - Doble clic para editar tarea
    - Panel de detalle al seleccionar tarea
    - Tooltips informativos en botones
    - Mensaje amigable cuando no hay tareas
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import threading
import sys
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv

# Asegurar que Python encuentra los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar base de datos
try:
    from src.database import db
    print("✅ Base de datos importada")
except ImportError as e:
    print(f"❌ Error importando base de datos: {e}")
    from database import db

# Importar módulo de voz con manejo de errores
try:
    from src.voice import voice_assistant
    print("✅ Módulo de voz importado")
except ImportError as e:
    print(f"⚠️  Error importando voz: {e}")
    print("Usando voz simulada...")

    class DummyVoice:
        """Clase sustituta cuando el módulo de voz no está disponible.

        Proporciona la misma interfaz que VoiceAssistant pero sin
        funcionalidad real. Los métodos imprimen mensajes simulados
        en la consola en lugar de usar el micrófono o altavoces.
        """

        def __init__(self):
            """Inicializa el DummyVoice con voz simulada disponible."""
            self.voice_available = True
            self.is_listening = False

        def hablar(self, texto):
            """Simula hablar imprimiendo el texto en consola.

            Args:
                texto (str): Texto que se simula hablar.
            """
            print(f"🤖 [Simulado]: {texto}")

        def escuchar(self, timeout=5):
            """Simula escuchar. Siempre retorna None.

            Args:
                timeout (int): Tiempo de espera en segundos (ignorado).

            Returns:
                None: Siempre retorna None al ser simulado.
            """
            return None

        def iniciar_modo_voz(self):
            """Simula activar el modo voz.

            Returns:
                bool: Siempre retorna True.
            """
            print("🎤 Modo voz simulado activado")
            return True

        def detener_modo_voz(self):
            """Simula desactivar el modo voz."""
            print("🎤 Modo voz desactivado")

    voice_assistant = DummyVoice()

# Diálogos y gestor de deshacer
from src.dialogos import CrearTareaDialog, EditarTareaDialog, EliminarTareaDialog
from src.undo_manager import UndoManager


# ============================================================================
# TEMAS VISUALES (Nord Dark y Nord Light)
# ============================================================================

TEMA_OSCURO = {
    "nombre": "oscuro",
    "bg":         "#2E3440",
    "bg2":        "#3B4252",
    "bg3":        "#434C5E",
    "bg4":        "#4C566A",
    "fg":         "#D8DEE9",
    "fg2":        "#E5E9F0",
    "fg3":        "#ECEFF4",
    "accent":     "#88C0D0",
    "accent2":    "#81A1C1",
    "accent3":    "#5E81AC",
    "verde":      "#A3BE8C",
    "rojo":       "#BF616A",
    "amarillo":   "#EBCB8B",
    "morado":     "#B48EAD",
    "btn_icon":   "🌙",   # icono que se muestra cuando está en oscuro (para cambiar a claro)
    "tree_sel":   "#4C566A",
}

TEMA_CLARO = {
    "nombre": "claro",
    "bg":         "#ECEFF4",
    "bg2":        "#E5E9F0",
    "bg3":        "#D8DEE9",
    "bg4":        "#C8D4E0",
    "fg":         "#2E3440",
    "fg2":        "#3B4252",
    "fg3":        "#434C5E",
    "accent":     "#5E81AC",
    "accent2":    "#81A1C1",
    "accent3":    "#88C0D0",
    "verde":      "#4A7C3F",
    "rojo":       "#C0392B",
    "amarillo":   "#B7860B",
    "morado":     "#8E44AD",
    "btn_icon":   "☀️",   # icono que se muestra cuando está en claro (para cambiar a oscuro)
    "tree_sel":   "#C8D4E0",
}


# ============================================================================
# CLASE TOOLTIP
# ============================================================================

class _ToolTip:
    """Tooltip flotante que aparece al pasar el mouse sobre un widget.

    Muestra un pequeño cuadro de texto con información adicional
    cerca del widget cuando el cursor se detiene sobre él.

    Attributes:
        widget: Widget al que se adjunta el tooltip.
        texto (str): Texto a mostrar en el tooltip.
        ventana_tip: Ventana Toplevel del tooltip (None si no visible).
    """

    def __init__(self, widget, texto):
        """Inicializa el tooltip y enlaza eventos de mouse.

        Args:
            widget: Widget de Tkinter al que se adjunta el tooltip.
            texto (str): Texto informativo a mostrar.
        """
        self.widget = widget
        self.texto = texto
        self.ventana_tip = None
        widget.bind("<Enter>", self._mostrar)
        widget.bind("<Leave>", self._ocultar)

    def _mostrar(self, event=None):
        """Muestra el tooltip al entrar el cursor al widget.

        Args:
            event: Evento de Tkinter (no utilizado).
        """
        if self.ventana_tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.ventana_tip = tk.Toplevel(self.widget)
        self.ventana_tip.wm_overrideredirect(True)
        self.ventana_tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            self.ventana_tip,
            text=self.texto,
            background="#EBCB8B",
            foreground="#2E3440",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
            wraplength=300,
        )
        lbl.pack()

    def _ocultar(self, event=None):
        """Oculta el tooltip al salir el cursor del widget.

        Args:
            event: Evento de Tkinter (no utilizado).
        """
        if self.ventana_tip:
            self.ventana_tip.destroy()
            self.ventana_tip = None


def agregar_tooltip(widget, texto):
    """Agrega un tooltip informativo a un widget de Tkinter.

    Args:
        widget: Widget de Tkinter sobre el que aparecerá el tooltip.
        texto (str): Texto informativo a mostrar en el tooltip.

    Returns:
        _ToolTip: Instancia del tooltip creado.
    """
    return _ToolTip(widget, texto)


# ============================================================================
# VENTANA PRINCIPAL
# ============================================================================

class SmartTaskApp:
    """Ventana principal de SmartTask Organizer.

    Implementa la interfaz gráfica completa de la aplicación utilizando
    Tkinter con soporte para temas Nord oscuro y claro. Gestiona la
    lista de tareas, filtros por categoría, búsqueda en tiempo real,
    panel de detalle, acciones CRUD, estadísticas y exportación.

    Attributes:
        root (tk.Tk): Ventana raíz de Tkinter.
        tema (dict): Diccionario del tema activo (TEMA_OSCURO o TEMA_CLARO).
        filtro_categoria (tk.StringVar): Filtro de categoría activo.
        busqueda_var (tk.StringVar): Variable del buscador en tiempo real.
        modo_voz_activo (bool): Indica si el modo voz está activado.
        undo_manager (UndoManager): Gestor de acciones reversibles.
        tree (ttk.Treeview): Tabla de tareas.
        lbl_stats (ttk.Label): Barra de estadísticas inferior.
        _tareas_cache (list): Cache de tareas para el filtrado en memoria.
    """

    def __init__(self, root):
        """Inicializa la aplicación y construye la interfaz completa.

        Args:
            root (tk.Tk): Ventana raíz de Tkinter.
        """
        self.root = root
        self.root.title("SmartTask Organizer - Gestor de Tareas")
        self.root.geometry("1280x820")

        # Estado
        self.filtro_categoria = tk.StringVar(value="TODAS")
        self.busqueda_var = tk.StringVar()
        self.modo_voz_activo = False
        self.undo_manager = UndoManager()
        self.tema = TEMA_OSCURO
        self._tareas_cache = []

        # Atajos de teclado
        self.root.bind('<Control-z>', lambda e: self._deshacer_accion())

        # Construir UI
        self._configurar_estilos()
        self._crear_interfaz()
        self._cargar_tareas()
        self._centrar_ventana()

        # Suscribir buscador en tiempo real
        self.busqueda_var.trace_add("write", lambda *_: self._filtrar_en_memoria())

        # Notificaciones al inicio
        self.root.after(1000, self._verificar_notificaciones)
        print("✅ Aplicación inicializada correctamente")

    # -----------------------------------------------------------------------
    # TEMA
    # -----------------------------------------------------------------------

    def _configurar_estilos(self):
        """Configura los estilos ttk usando el tema activo (oscuro o claro).

        Aplica la paleta de colores del tema actual a todos los widgets
        de tkinter/ttk. Soporta re-invocarse para cambiar de tema en
        caliente sin reiniciar la aplicación.
        """
        t = self.tema
        self.root.configure(background=t["bg"])

        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background=t["bg"], foreground=t["fg"],
                        font=("Segoe UI", 10))
        style.configure('TFrame', background=t["bg"])
        style.configure('TLabelframe', background=t["bg"],
                        foreground=t["accent"], bordercolor=t["bg4"])
        style.configure('TLabelframe.Label', background=t["bg"],
                        foreground=t["accent"], font=("Segoe UI", 10, "bold"))
        style.configure('TLabel', background=t["bg"], foreground=t["fg"])
        style.configure('TEntry', fieldbackground=t["bg2"],
                        foreground=t["fg3"], insertcolor=t["fg3"],
                        bordercolor=t["bg4"], lightcolor=t["bg4"],
                        darkcolor=t["bg4"], padding=5)
        style.configure('TButton', background=t["bg4"], foreground=t["fg3"],
                        borderwidth=0, focuscolor=t["accent"], padding=(10, 5))
        style.map('TButton',
                  background=[('active', t["bg3"]), ('pressed', t["bg2"])],
                  foreground=[('active', t["fg3"])])

        style.configure('Accent.TButton', background=t["accent3"],
                        foreground=t["fg3"], font=("Segoe UI", 10, "bold"))
        style.map('Accent.TButton',
                  background=[('active', t["accent2"]), ('pressed', t["accent3"])])

        style.configure('Success.TButton', background=t["verde"],
                        foreground=t["bg"], font=("Segoe UI", 10, "bold"))
        style.map('Success.TButton',
                  background=[('active', '#8FBCBB')])

        style.configure('Danger.TButton', background=t["rojo"],
                        foreground=t["fg3"], font=("Segoe UI", 10, "bold"))
        style.map('Danger.TButton',
                  background=[('active', '#D08770')])

        style.configure('Theme.TButton', background=t["bg3"],
                        foreground=t["fg3"], font=("Segoe UI", 11, "bold"),
                        padding=(8, 4))
        style.map('Theme.TButton',
                  background=[('active', t["bg4"])])

        style.configure("Treeview", background=t["bg2"], foreground=t["fg3"],
                        fieldbackground=t["bg2"], rowheight=30,
                        borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=t["bg3"],
                        foreground=t["fg"], relief="flat",
                        font=("Segoe UI", 10, "bold"), padding=5)
        style.map("Treeview",
                  background=[('selected', t["tree_sel"])],
                  foreground=[('selected', t["fg3"])])

        style.configure("Vertical.TScrollbar", background=t["bg4"],
                        troughcolor=t["bg"], borderwidth=0,
                        arrowcolor=t["fg"])
        style.configure("Horizontal.TScrollbar", background=t["bg4"],
                        troughcolor=t["bg"], borderwidth=0,
                        arrowcolor=t["fg"])
        style.configure("TRadiobutton", background=t["bg"],
                        foreground=t["fg"], font=("Segoe UI", 10))
        style.map("TRadiobutton", background=[('active', t["bg2"])])
        style.configure("TEntry", selectbackground=t["accent"],
                        selectforeground=t["bg"])

    def _cambiar_tema(self):
        """Alterna entre el tema oscuro (Nord Dark) y el tema claro (Nord Light).

        Cambia el tema activo, re-aplica todos los estilos ttk y
        actualiza el texto del botón de tema. Recarga la tabla de
        tareas para que los colores de las filas se actualicen.
        """
        self.tema = TEMA_CLARO if self.tema["nombre"] == "oscuro" else TEMA_OSCURO
        self._configurar_estilos()
        # Actualizar botón de tema
        icono = "🌙" if self.tema["nombre"] == "oscuro" else "☀️"
        self.btn_tema.config(text=icono)
        # Recargar tabla con los nuevos colores
        self._cargar_tareas()

    # -----------------------------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ
    # -----------------------------------------------------------------------

    def _centrar_ventana(self):
        """Centra la ventana principal en la pantalla del usuario."""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')

    def _crear_interfaz(self):
        """Construye todos los widgets de la interfaz gráfica principal.

        Estructura del layout:
            - Cabecera: Título + botones superiores + toggle Día/Noche.
            - Barra de búsqueda: Campo de texto con filtrado en tiempo real.
            - Filtros: RadioButtons dinámicos por categoría.
            - Tabla (Treeview): Lista de tareas con 7 columnas.
            - Leyenda de colores.
            - Panel de detalle: Información de la tarea seleccionada.
            - Botones de acción: Editar, Eliminar, Completar, Exportar.
            - Barra de estadísticas.
        """
        t = self.tema
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---- CABECERA ----
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="SMARTTASK ORGANIZER",
            font=("Segoe UI", 22, "bold"),
            foreground=t["accent"]
        ).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)

        # Botón toggle Día/Noche (Grupo A)
        self.btn_tema = ttk.Button(
            btn_frame, text="🌙",
            command=self._cambiar_tema,
            style="Theme.TButton"
        )
        self.btn_tema.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(self.btn_tema, "Cambiar entre tema oscuro (Noche) y claro (Día)")

        btn_graficos = ttk.Button(btn_frame, text="📊 GRÁFICOS",
                                  command=self._mostrar_graficos,
                                  style="Accent.TButton")
        btn_graficos.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(btn_graficos, "Ver gráfico de distribución de tareas por estado")

        btn_voz = ttk.Button(btn_frame, text="🎤 VOZ",
                             command=self._alternar_modo_voz,
                             style="Accent.TButton")
        btn_voz.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(btn_voz, "Activar/desactivar el asistente de voz para dictar tareas")

        btn_cats = ttk.Button(btn_frame, text="⚙️ CATEGORÍAS",
                              command=self._gestionar_categorias,
                              style="Accent.TButton")
        btn_cats.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(btn_cats, "Agregar, editar o eliminar categorías de tareas")

        btn_nueva = ttk.Button(btn_frame, text="+ NUEVA TAREA",
                               command=self._abrir_crear_tarea,
                               style="Success.TButton")
        btn_nueva.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(btn_nueva, "Crear una nueva tarea (también puedes dictar por voz dentro del formulario)")

        # ---- BUSCADOR EN TIEMPO REAL (Grupo B) ----
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(
            search_frame,
            text="🔍",
            font=("Segoe UI", 13)
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.entry_busqueda = ttk.Entry(
            search_frame,
            textvariable=self.busqueda_var,
            font=("Segoe UI", 11),
            width=35
        )
        self.entry_busqueda.pack(side=tk.LEFT, ipady=4)
        agregar_tooltip(self.entry_busqueda,
                        "Escribe para buscar tareas por título en tiempo real")

        # Placeholder visual
        self._placeholder_activo = True
        self.entry_busqueda.insert(0, "Buscar tarea por nombre...")
        self.entry_busqueda.config(foreground="#888888")
        self.entry_busqueda.bind("<FocusIn>",  self._on_busqueda_focus_in)
        self.entry_busqueda.bind("<FocusOut>", self._on_busqueda_focus_out)

        btn_limpiar = ttk.Button(
            search_frame, text="✖",
            command=self._limpiar_busqueda, width=3
        )
        btn_limpiar.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(btn_limpiar, "Limpiar búsqueda")

        self.lbl_resultados = ttk.Label(
            search_frame,
            text="",
            font=("Segoe UI", 9),
            foreground=t["accent2"]
        )
        self.lbl_resultados.pack(side=tk.LEFT, padx=10)

        # ---- FILTROS POR CATEGORÍA (HU10) ----
        self.filtro_frame = ttk.LabelFrame(main_frame, text="FILTROS POR CATEGORÍA",
                                           padding="8")
        self.filtro_frame.pack(fill=tk.X, pady=(0, 8))
        self._construir_filtros()

        # ---- TABLA DE TAREAS ----
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Título", "Descripción", "Fecha Límite",
                   "Estado", "Prioridad", "Categoría")
        self.tree = ttk.Treeview(tree_frame, columns=columns,
                                 show="headings", selectmode="browse")

        col_widths = {
            "ID": 50, "Título": 220, "Descripción": 260,
            "Fecha Límite": 105, "Estado": 100, "Prioridad": 85, "Categoría": 110
        }
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[col], minwidth=40)

        v_sb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self.tree.yview)
        h_sb = ttk.Scrollbar(tree_frame, orient="horizontal",
                             command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_sb.set,
                            xscrollcommand=h_sb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_sb.grid(row=0, column=1, sticky="ns")
        h_sb.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Doble clic para editar (Grupo C)
        self.tree.bind("<Double-1>", lambda e: self._abrir_editar_tarea())
        agregar_tooltip(self.tree, "💡 Doble clic en una fila para editar esa tarea")

        # Selección → actualiza panel de detalle (Grupo F)
        self.tree.bind("<<TreeviewSelect>>", self._on_seleccion_tarea)

        # ---- LEYENDA DE COLORES ----
        legend_frame = ttk.Frame(main_frame)
        legend_frame.pack(fill=tk.X, pady=4)

        ttk.Label(
            legend_frame, text="LEYENDA:",
            font=("Segoe UI", 9, "bold"),
            foreground=t["accent"]
        ).pack(side=tk.LEFT, padx=5)

        legends = [
            ("● COMPLETADA",   t["verde"]),
            ("● VENCIDA",      t["rojo"]),
            ("● ALTA PRIOR.",  t["amarillo"]),
            ("● MEDIA PRIOR.", t["accent"]),
        ]
        for texto, color in legends:
            tk.Label(legend_frame, text=texto, fg=color,
                     bg=t["bg"], font=("Segoe UI", 9, "bold"),
                     padx=6).pack(side=tk.LEFT)

        # ---- PANEL DE DETALLE (Grupo F) ----
        self.detalle_frame = ttk.LabelFrame(main_frame, text="DETALLE DE TAREA SELECCIONADA",
                                            padding="8")
        self.detalle_frame.pack(fill=tk.X, pady=(4, 0))

        self.lbl_detalle = ttk.Label(
            self.detalle_frame,
            text="Selecciona una tarea para ver sus detalles aquí.",
            font=("Segoe UI", 10),
            foreground=t["fg2"],
            wraplength=900,
            justify=tk.LEFT
        )
        self.lbl_detalle.pack(anchor="w")

        # ---- BOTONES DE ACCIÓN ----
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=8)

        btn_editar = ttk.Button(action_frame, text="✏️ EDITAR",
                                command=self._abrir_editar_tarea)
        btn_editar.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(btn_editar, "Editar la tarea seleccionada (también doble clic en la fila)")

        btn_eliminar = ttk.Button(action_frame, text="🗑️ ELIMINAR",
                                  command=self._abrir_eliminar_tarea,
                                  style="Danger.TButton")
        btn_eliminar.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(btn_eliminar, "Eliminar la tarea seleccionada (se puede deshacer con Ctrl+Z)")

        btn_completar = ttk.Button(action_frame, text="✅ COMPLETAR",
                                   command=self._completar_tarea,
                                   style="Success.TButton")
        btn_completar.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(btn_completar, "Marcar la tarea seleccionada como completada (Ctrl+Z para deshacer)")

        btn_exportar = ttk.Button(action_frame, text="📄 EXPORTAR CSV",
                                  command=self._exportar_csv)
        btn_exportar.pack(side=tk.LEFT, padx=5)
        agregar_tooltip(btn_exportar, "Exportar todas las tareas a un archivo CSV compatible con Excel")

        btn_actualizar = ttk.Button(action_frame, text="🔄 ACTUALIZAR",
                                    command=self._cargar_tareas)
        btn_actualizar.pack(side=tk.RIGHT, padx=5)
        agregar_tooltip(btn_actualizar, "Recargar la lista de tareas desde la base de datos")

        # ---- BARRA DE ESTADÍSTICAS ----
        self.lbl_stats = ttk.Label(main_frame, text="",
                                   font=("Segoe UI", 10))
        self.lbl_stats.pack(fill=tk.X, pady=(2, 0))

    # -----------------------------------------------------------------------
    # BUSCADOR EN TIEMPO REAL (Grupo B) — placeholder
    # -----------------------------------------------------------------------

    def _on_busqueda_focus_in(self, event):
        """Elimina el placeholder al hacer foco en el campo de búsqueda.

        Args:
            event: Evento de Tkinter (no utilizado directamente).
        """
        if self._placeholder_activo:
            self.entry_busqueda.delete(0, tk.END)
            t = self.tema
            self.entry_busqueda.config(foreground=t["fg3"])
            self._placeholder_activo = False

    def _on_busqueda_focus_out(self, event):
        """Restaura el placeholder si el campo de búsqueda queda vacío.

        Args:
            event: Evento de Tkinter (no utilizado directamente).
        """
        if not self.busqueda_var.get():
            self.entry_busqueda.insert(0, "Buscar tarea por nombre...")
            self.entry_busqueda.config(foreground="#888888")
            self._placeholder_activo = True

    def _limpiar_busqueda(self):
        """Limpia el campo de búsqueda y muestra todas las tareas del filtro activo."""
        self.busqueda_var.set("")
        self.entry_busqueda.delete(0, tk.END)
        self._placeholder_activo = True
        self.entry_busqueda.insert(0, "Buscar tarea por nombre...")
        self.entry_busqueda.config(foreground="#888888")
        self._mostrar_tareas(self._tareas_cache)

    def _filtrar_en_memoria(self):
        """Filtra las tareas del cache en memoria según el texto de búsqueda.

        Se llama automáticamente en cada pulsación de tecla gracias al
        trace de StringVar. No realiza consultas a la BD — trabaja con
        el cache de tareas ya cargadas, por lo que es instantáneo.
        """
        if self._placeholder_activo:
            return
        termino = self.busqueda_var.get().strip().lower()
        if not termino:
            filtradas = self._tareas_cache
        else:
            filtradas = [
                t for t in self._tareas_cache
                if termino in t['titulo'].lower()
            ]
        self._mostrar_tareas(filtradas)

    # -----------------------------------------------------------------------
    # FILTROS DE CATEGORÍA
    # -----------------------------------------------------------------------

    def _construir_filtros(self):
        """Construye dinámicamente los RadioButtons de filtro por categoría.

        Limpia los filtros existentes y los reconstruye consultando las
        categorías actuales de la base de datos (HU10). Esto permite
        que al agregar o eliminar categorías los filtros se actualicen.
        """
        for w in self.filtro_frame.winfo_children():
            w.destroy()

        categorias = db.obtener_categorias()
        filtros = ["TODAS"] + [cat['nombre'] for cat in categorias]

        for filtro in filtros:
            ttk.Radiobutton(
                self.filtro_frame, text=filtro,
                variable=self.filtro_categoria,
                value=filtro,
                command=self._cargar_tareas
            ).pack(side=tk.LEFT, padx=5)

    def _gestionar_categorias(self):
        """Abre el diálogo de gestión de categorías (HU08, HU09, HU10).

        Al cerrar, reconstruye filtros dinámicos y recarga la tabla.
        """
        try:
            from src.dialogos import GestionCategoriasDialog
        except ImportError:
            from dialogos import GestionCategoriasDialog

        def _on_close():
            """Callback al cerrar: refresca filtros y tareas."""
            self.filtro_categoria.set("TODAS")
            self._construir_filtros()
            self._cargar_tareas()

        GestionCategoriasDialog(self.root, _on_close)

    # -----------------------------------------------------------------------
    # CARGA Y VISUALIZACIÓN DE TAREAS
    # -----------------------------------------------------------------------

    def _cargar_tareas(self):
        """Carga tareas desde la BD al cache y las muestra en la tabla (HU02, HU07, HU10).

        Consulta la BD, aplica filtro de categoría, detecta vencidas
        automáticamente (HU07) y guarda el resultado en _tareas_cache.
        Luego aplica el filtro de búsqueda si hay texto activo.
        """
        filtro = self.filtro_categoria.get()
        if filtro == "TODAS":
            filtro = None

        # Detectar vencidas
        db.actualizar_vencidas()

        tareas = db.obtener_todas_tareas(filtro)
        self._tareas_cache = list(tareas)

        # Aplicar búsqueda activa si existe
        termino = "" if self._placeholder_activo else self.busqueda_var.get().strip().lower()
        if termino:
            filtradas = [t for t in self._tareas_cache if termino in t['titulo'].lower()]
        else:
            filtradas = self._tareas_cache

        self._mostrar_tareas(filtradas)

    def _mostrar_tareas(self, tareas):
        """Renderiza una lista de tareas en el Treeview y actualiza contadores.

        Se encarga de limpiar la tabla, insertar filas con colores Nord
        según estado/prioridad, mostrar mensaje vacío si no hay tareas
        (Grupo D), y actualizar el label de resultados de búsqueda.

        Args:
            tareas (list[dict]): Lista de tareas a mostrar. Pueden ser
                todas o un subconjunto filtrado por búsqueda.
        """
        t = self.tema

        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        # ---- Grupo D: Mensaje vacío amigable ----
        if not tareas:
            termino = "" if self._placeholder_activo else self.busqueda_var.get().strip()
            if termino:
                msg = f'🔍 No se encontraron tareas con "{termino}".'
            elif self.filtro_categoria.get() != "TODAS":
                msg = f'📂 No hay tareas en la categoría "{self.filtro_categoria.get()}".'
            else:
                msg = "📋 No hay tareas todavía. ¡Crea tu primera tarea con el botón + NUEVA TAREA!"
            self.tree.insert("", tk.END, values=(msg, "", "", "", "", "", ""))
            self.lbl_resultados.config(text="Sin resultados")
            self._actualizar_estadisticas()
            return

        # Insertar filas
        for tarea in tareas:
            fecha = ""
            if tarea['fecha_limite']:
                try:
                    fecha = datetime.strptime(
                        tarea['fecha_limite'], "%Y-%m-%d"
                    ).strftime("%d/%m/%Y")
                except ValueError:
                    fecha = tarea['fecha_limite']

            estado = tarea['estado'].upper()

            item_id = self.tree.insert("", tk.END, values=(
                tarea['id'],
                tarea['titulo'],
                tarea['descripcion'] or "",
                fecha,
                estado,
                tarea['prioridad'].upper(),
                tarea['categoria_nombre'] or "Sin categoría"
            ))

            # Colores Nord por estado/prioridad
            if estado == "COMPLETADA":
                self.tree.item(item_id, tags=('completada',))
            elif estado == "VENCIDA":
                self.tree.item(item_id, tags=('vencida',))
            elif tarea['prioridad'] == 'alta':
                self.tree.item(item_id, tags=('alta',))
            elif tarea['prioridad'] == 'media':
                self.tree.item(item_id, tags=('media',))

        # Aplicar colores via tags
        self.tree.tag_configure('completada', foreground=t["verde"])
        self.tree.tag_configure('vencida',    foreground=t["rojo"])
        self.tree.tag_configure('alta',       foreground=t["amarillo"])
        self.tree.tag_configure('media',      foreground=t["accent"])

        # Actualizar contador de resultados
        total = len(self._tareas_cache)
        mostrando = len(tareas)
        if mostrando < total:
            self.lbl_resultados.config(
                text=f"Mostrando {mostrando} de {total} tareas"
            )
        else:
            self.lbl_resultados.config(text=f"{total} tarea(s)")

        self._actualizar_estadisticas()

    # -----------------------------------------------------------------------
    # PANEL DE DETALLE (Grupo F)
    # -----------------------------------------------------------------------

    def _on_seleccion_tarea(self, event=None):
        """Actualiza el panel de detalle cuando el usuario selecciona una tarea.

        Obtiene los datos de la tarea seleccionada y muestra su
        información completa en el panel de detalle inferior.

        Args:
            event: Evento <<TreeviewSelect>> de Tkinter.
        """
        seleccion = self.tree.selection()
        if not seleccion:
            self.lbl_detalle.config(
                text="Selecciona una tarea para ver sus detalles aquí."
            )
            return

        valores = self.tree.item(seleccion[0], 'values')
        if not valores or len(valores) < 7:
            return

        tarea_id_str = str(valores[0])
        # Verificar que sea un ID numérico (no el mensaje vacío)
        if not tarea_id_str.strip().lstrip('-').isdigit():
            self.lbl_detalle.config(text="")
            return

        tarea = db.obtener_tarea(int(tarea_id_str))
        if not tarea:
            return

        fecha = tarea['fecha_limite'] or "Sin fecha límite"
        if tarea['fecha_limite']:
            try:
                fecha = datetime.strptime(
                    tarea['fecha_limite'], "%Y-%m-%d"
                ).strftime("%d/%m/%Y")
            except ValueError:
                pass

        desc = tarea['descripcion'] or "Sin descripción"
        cat = tarea['categoria_nombre'] or "Sin categoría"

        texto = (
            f"📌 {tarea['titulo']}    "
            f"│  📝 {desc}    "
            f"│  🏷️ Categoría: {cat}    "
            f"│  📅 Fecha límite: {fecha}    "
            f"│  Estado: {tarea['estado'].upper()}    "
            f"│  Prioridad: {tarea['prioridad'].upper()}"
        )
        self.lbl_detalle.config(text=texto)

    # -----------------------------------------------------------------------
    # ESTADÍSTICAS
    # -----------------------------------------------------------------------

    def _actualizar_estadisticas(self):
        """Actualiza la barra de estado con estadísticas en tiempo real.

        Consulta los conteos desde la BD y los muestra en el label
        inferior de la ventana principal.
        """
        stats = db.obtener_estadisticas()
        texto = (
            f"📊 TOTAL: {stats['total']}  │  "
            f"✅ COMPLETADAS: {stats['completadas']}  │  "
            f"⏳ PENDIENTES: {stats['pendientes']}  │  "
            f"⚠️ VENCIDAS: {stats['vencidas']}"
        )
        self.lbl_stats.config(text=texto, foreground=self.tema["accent"])

    # -----------------------------------------------------------------------
    # NOTIFICACIONES
    # -----------------------------------------------------------------------

    def _verificar_notificaciones(self):
        """Verifica tareas vencidas o para hoy y envía notificación de Windows (HU12).

        Se ejecuta automáticamente 1 segundo después de iniciar la app.
        Usa la librería 'plyer' para enviar notificaciones nativas.
        """
        try:
            from plyer import notification
            stats = db.obtener_estadisticas()
            tareas = db.obtener_todas_tareas()
            hoy = date.today()
            para_hoy = sum(
                1 for t in tareas
                if t['estado'] == 'pendiente' and t['fecha_limite']
                and _safe_parse_date(t['fecha_limite']) == hoy
            )
            vencidas = stats['vencidas']
            mensaje = ""
            if vencidas > 0:
                mensaje += f"⚠️ {vencidas} tarea(s) vencida(s)!\n"
            if para_hoy > 0:
                mensaje += f"📅 {para_hoy} tarea(s) para hoy!"
            if mensaje:
                notification.notify(
                    title='SmartTask Organizer',
                    message=mensaje,
                    app_name='SmartTask',
                    timeout=10
                )
                print("🔔 Notificación enviada a Windows")
        except Exception as e:
            print(f"⚠️ No se pudo enviar notificación: {e}")

    # -----------------------------------------------------------------------
    # GRÁFICOS
    # -----------------------------------------------------------------------

    def _mostrar_graficos(self):
        """Muestra una ventana con gráficos estadísticos de tareas.

        Crea una ventana Toplevel con un gráfico de pastel matplotlib
        usando la paleta de colores Nord. Refleja el estado actual
        de todas las tareas del sistema.
        """
        stats = db.obtener_estadisticas()
        t = self.tema

        graph_window = tk.Toplevel(self.root)
        graph_window.title("Estadísticas SmartTask")
        graph_window.geometry("700x620")
        graph_window.configure(background=t["bg"])

        ttk.Label(
            graph_window, text="ESTADÍSTICAS DE TAREAS",
            font=("Segoe UI", 18, "bold"),
            foreground=t["accent"],
            background=t["bg"]
        ).pack(pady=15)

        info_frame = tk.Frame(graph_window, bg=t["bg2"], padx=20, pady=15)
        info_frame.pack(fill=tk.X, padx=40)

        resumen = (
            f"Total Tareas: {stats['total']}\n"
            f"✅ Completadas: {stats['completadas']}\n"
            f"⏳ Pendientes: {stats['pendientes']}\n"
            f"⚠️ Vencidas: {stats['vencidas']}"
        )
        tk.Label(info_frame, text=resumen, font=("Segoe UI", 12),
                 bg=t["bg2"], fg=t["fg3"], justify=tk.LEFT).pack()

        labels_base = ['Completadas', 'Pendientes', 'Vencidas']
        sizes_base  = [stats['completadas'], stats['pendientes'], stats['vencidas']]
        colors_base = [t["verde"], t["accent"], t["rojo"]]
        explode_b   = (0.05, 0, 0.05)

        final = [(l, s, c, e) for l, s, c, e in
                 zip(labels_base, sizes_base, colors_base, explode_b) if s > 0]

        if not final:
            tk.Label(graph_window, text="\nNo hay datos aún.",
                     bg=t["bg"], fg=t["fg2"]).pack()
        else:
            fl, fs, fc, fe = zip(*final)
            try:
                plt.style.use('dark_background')
                fig, ax = plt.subplots(figsize=(6, 4.5), facecolor=t["bg"])
                wedges, texts, autotexts = ax.pie(
                    fs, explode=fe, labels=fl,
                    colors=fc, autopct='%1.1f%%',
                    shadow=True, startangle=90,
                    textprops={'color': t["fg3"], 'weight': 'bold'}
                )
                for at in autotexts:
                    at.set_color(t["bg"])
                    at.set_fontsize(10)
                ax.axis('equal')
                ax.set_title("Distribución de Tareas", color=t["accent"],
                             fontsize=13, pad=15)
                canvas = FigureCanvasTkAgg(fig, master=graph_window)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
                canvas.get_tk_widget().configure(bg=t["bg"])
            except Exception as e:
                tk.Label(graph_window, text=f"Error: {e}", bg="red").pack()

        ttk.Button(graph_window, text="Cerrar",
                   command=graph_window.destroy).pack(pady=10)

    # -----------------------------------------------------------------------
    # CRUD DE TAREAS
    # -----------------------------------------------------------------------

    def _abrir_crear_tarea(self):
        """Abre el diálogo para crear una nueva tarea (HU01, HU11).

        Importa el asistente de voz disponible y abre CrearTareaDialog.
        """
        try:
            from src.voice import voice_assistant as va
        except ImportError:
            class _DummyVoice:
                """Voz simulada local."""
                voice_available = False
                is_listening = False
                def hablar(self, t): pass
                def escuchar_y_parsear(self, cb=None): return None
            va = _DummyVoice()

        dialog = CrearTareaDialog(self.root, self._cargar_tareas, va)
        self.root.wait_window(dialog.top)

    def _abrir_editar_tarea(self):
        """Abre el diálogo para editar la tarea seleccionada (HU03).

        Soporta apertura por clic en botón Editar o por doble clic
        en la fila del Treeview (Grupo C).
        """
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para editar")
            return

        item = seleccion[0]
        tarea_id_str = str(self.tree.item(item, 'values')[0])
        if not tarea_id_str.strip().lstrip('-').isdigit():
            return  # es mensaje de "Sin tareas"

        dialog = EditarTareaDialog(self.root, int(tarea_id_str), self._cargar_tareas)
        self.root.wait_window(dialog.top)

    def _abrir_eliminar_tarea(self):
        """Elimina la tarea seleccionada con confirmación (HU04).

        Registra la acción en UndoManager para poder deshacerla con Ctrl+Z.
        """
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para eliminar")
            return

        item = seleccion[0]
        valores = self.tree.item(item, 'values')
        tarea_id_str = str(valores[0])
        if not tarea_id_str.strip().lstrip('-').isdigit():
            return

        titulo = valores[1]
        tarea_id = int(tarea_id_str)

        if messagebox.askyesno("Confirmar eliminación",
                               f"¿Eliminar la tarea '{titulo}'?"):
            tarea_obj = db.obtener_tarea(tarea_id)
            if tarea_obj:
                self.undo_manager.registrar_accion("ELIMINAR", dict(tarea_obj))

            if db.eliminar_tarea(tarea_id):
                self.lbl_detalle.config(text="Selecciona una tarea para ver sus detalles aquí.")
                self._cargar_tareas()
                messagebox.showinfo("Éxito", "Tarea eliminada\n(Ctrl+Z para deshacer)")
            else:
                messagebox.showerror("Error", "No se pudo eliminar la tarea")

    def _completar_tarea(self):
        """Marca la tarea seleccionada como completada (HU05).

        Pide confirmación y registra la acción en UndoManager.
        """
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para completar")
            return

        item = seleccion[0]
        valores = self.tree.item(item, 'values')
        tarea_id_str = str(valores[0])
        if not tarea_id_str.strip().lstrip('-').isdigit():
            return

        titulo = valores[1]
        tarea_id = int(tarea_id_str)

        if messagebox.askyesno("Completar Tarea", f"¿Marcar '{titulo}' como completada?"):
            self.undo_manager.registrar_accion("COMPLETAR", {'id': tarea_id})
            if db.marcar_como_completada(tarea_id):
                self._cargar_tareas()
                messagebox.showinfo("Éxito",
                                    "Tarea marcada como completada\n(Ctrl+Z para deshacer)")
            else:
                messagebox.showerror("Error", "No se pudo completar la tarea")

    # -----------------------------------------------------------------------
    # EXPORTAR CSV
    # -----------------------------------------------------------------------

    def _exportar_csv(self):
        """Exporta todas las tareas a un archivo CSV compatible con Excel.

        Usa codificación UTF-8 BOM y punto y coma como delimitador
        para compatibilidad con Excel en español. Permite elegir la
        ubicación de guardado mediante un diálogo del sistema.
        """
        try:
            tareas = db.obtener_todas_tareas()
            if not tareas:
                messagebox.showinfo("Info", "No hay tareas para exportar")
                return

            tareas_lista = sorted([dict(t) for t in tareas], key=lambda x: x['id'])
            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filedialog.asksaveasfilename(
                initialfile=f"smarttask_export_{fecha_str}.csv",
                defaultextension=".csv",
                filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
            )
            if not filename:
                return

            with open(filename, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["ID", "Título", "Descripción", "Fecha Límite",
                                 "Estado", "Prioridad", "Categoría"])
                for t in tareas_lista:
                    writer.writerow([t['id'], t['titulo'], t['descripcion'],
                                     t['fecha_limite'], t['estado'],
                                     t['prioridad'], t['categoria_nombre']])

            messagebox.showinfo("Éxito", f"Exportado correctamente:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    # -----------------------------------------------------------------------
    # DESHACER (Ctrl+Z)
    # -----------------------------------------------------------------------

    def _deshacer_accion(self):
        """Revierte la última acción realizada por el usuario.

        Se activa con Ctrl+Z. Muestra un mensaje toast que desaparece
        automáticamente después de 2 segundos.
        """
        resultado = self.undo_manager.deshacer()
        if resultado:
            self._cargar_tareas()
            t = self.tema
            lbl = tk.Label(self.root, text=f"↩️  {resultado}",
                           bg=t["accent"], fg=t["bg"],
                           font=("Segoe UI", 12, "bold"),
                           padx=20, pady=10)
            lbl.place(relx=0.5, rely=0.92, anchor="center")
            self.root.after(2000, lbl.destroy)
        else:
            print("Nada que deshacer")

    # -----------------------------------------------------------------------
    # MODO VOZ (HU11)
    # -----------------------------------------------------------------------

    def _alternar_modo_voz(self):
        """Activa o desactiva el modo voz interactivo (HU11).

        Cuando se activa, inicia el asistente de voz y ejecuta
        el bucle de escucha en un hilo daemon separado.
        """
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
                threading.Thread(target=self._ejecutar_modo_voz,
                                 daemon=True).start()
            else:
                self.modo_voz_activo = False
                messagebox.showerror("Error", "No se pudo iniciar el modo voz")
        else:
            self.modo_voz_activo = False
            voice_assistant.detener_modo_voz()
            messagebox.showinfo("Modo Voz", "Modo voz desactivado")

    def _ejecutar_modo_voz(self):
        """Bucle principal del modo voz en un hilo separado (HU11).

        Escucha continuamente comandos mientras modo_voz_activo sea True.
        Comandos soportados: 'salir', 'crear tarea', 'listar tareas', 'ayuda'.
        """
        while self.modo_voz_activo:
            try:
                comando = voice_assistant.escuchar(timeout=10)
                if comando:
                    if "salir" in comando or "terminar" in comando:
                        self.modo_voz_activo = False
                        voice_assistant.hablar("Saliendo del modo voz")
                        break
                    elif "crear tarea" in comando:
                        voice_assistant.hablar(
                            "Para crear una tarea, usa el botón NUEVA en la interfaz")
                    elif "listar tareas" in comando:
                        voice_assistant.hablar(
                            f"Tienes {len(self.tree.get_children())} tareas en la lista")
                    elif "ayuda" in comando:
                        voice_assistant.hablar(
                            "Comandos: crear tarea, listar tareas, ayuda, salir")
                    else:
                        voice_assistant.hablar(f"Comando '{comando}' recibido")
            except Exception:
                pass


# ============================================================================
# UTILIDADES
# ============================================================================

def _safe_parse_date(fecha_str):
    """Parsea una cadena de fecha en formato YYYY-MM-DD de forma segura.

    Args:
        fecha_str (str): Fecha en formato ISO 'YYYY-MM-DD'.

    Returns:
        date | None: Objeto date si el parseo es exitoso, None si falla.
    """
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    """Función principal que inicia la aplicación SmartTask Organizer.

    Crea la ventana raíz de Tkinter, instancia SmartTaskApp y
    ejecuta el bucle principal de eventos.
    """
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
    print("=" * 60)
    print("SMARTTASK ORGANIZER - Iniciando...")
    print("=" * 60)
    main()