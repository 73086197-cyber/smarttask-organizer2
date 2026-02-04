"""
Base de datos SQLite para SmartTask Organizer
"""
import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_name="smarttask.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        """Obtiene conexión a la base de datos"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        return conn
    
    def init_db(self):
        """Inicializa la base de datos con todas las tablas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de categorías
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT
        )
        ''')
        
        # Tabla de tareas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            fecha_limite TEXT,
            estado TEXT CHECK(estado IN ('pendiente', 'completada', 'vencida')) DEFAULT 'pendiente',
            prioridad TEXT CHECK(prioridad IN ('baja', 'media', 'alta')) DEFAULT 'media',
            categoria_id INTEGER,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
        ''')
        
        # Tabla de notificaciones
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarea_id INTEGER NOT NULL,
            fecha_alerta TEXT NOT NULL,
            enviada BOOLEAN DEFAULT 0,
            FOREIGN KEY (tarea_id) REFERENCES tareas(id) ON DELETE CASCADE
        )
        ''')
        
        # Tabla de comandos de voz
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS comandos_voz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            accion TEXT,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Insertar categorías por defecto
        categorias_default = [
            ('Trabajo', 'Tareas relacionadas con el trabajo'),
            ('Personal', 'Tareas personales'),
            ('Hogar', 'Tareas del hogar'),
            ('Estudio', 'Tareas académicas'),
            ('Salud', 'Tareas relacionadas con salud'),
            ('Finanzas', 'Tareas financieras')
        ]
        
        for nombre, descripcion in categorias_default:
            cursor.execute('INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)', 
                          (nombre, descripcion))
        
        # Insertar tareas de ejemplo
        cursor.execute("SELECT COUNT(*) FROM tareas")
        if cursor.fetchone()[0] == 0:
            tareas_ejemplo = [
                ('Revisar informe trimestral', 'Revisar datos y preparar presentación para la junta', 
                 '2024-12-15', 'pendiente', 'alta', 1),
                ('Comprar víveres semanales', 'Ir al supermercado para comprar alimentos de la semana', 
                 '2024-11-30', 'pendiente', 'media', 3),
                ('Estudiar para examen final', 'Repasar capítulos 5-8 del libro de texto', 
                 '2024-12-10', 'pendiente', 'alta', 4),
                ('Llamar al médico', 'Pedir cita para revisión anual', 
                 None, 'completada', 'baja', 5),
                ('Enviar reporte semanal', 'Enviar reporte de progreso por correo al equipo', 
                 '2024-11-25', 'completada', 'media', 1),
                ('Pagar factura de luz', 'Realizar pago de la factura eléctrica antes del vencimiento', 
                 '2024-11-28', 'pendiente', 'alta', 6),
                ('Hacer ejercicio', 'Ir al gimnasio por 1 hora', 
                 '2024-11-27', 'pendiente', 'media', 5),
                ('Reunión con equipo', 'Reunión semanal para revisar proyectos', 
                 '2024-11-29', 'pendiente', 'alta', 1)
            ]
            
            for tarea in tareas_ejemplo:
                cursor.execute('''
                INSERT INTO tareas (titulo, descripcion, fecha_limite, estado, prioridad, categoria_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', tarea)
        
        conn.commit()
        conn.close()
        print(f"✅ Base de datos '{self.db_name}' inicializada correctamente")
    
    # ===== OPERACIONES PARA TAREAS =====
    
    def crear_tarea(self, titulo, descripcion="", fecha_limite=None, 
                   prioridad="media", categoria_id=None):
        """Crea una nueva tarea en la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO tareas (titulo, descripcion, fecha_limite, prioridad, categoria_id)
        VALUES (?, ?, ?, ?, ?)
        ''', (titulo, descripcion, fecha_limite, prioridad, categoria_id))
        
        conn.commit()
        tarea_id = cursor.lastrowid
        conn.close()
        return tarea_id
    
    def obtener_todas_tareas(self, categoria_filtro=None):
        """Obtiene todas las tareas, opcionalmente filtradas por categoría"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if categoria_filtro and categoria_filtro != "TODAS":
            cursor.execute('''
            SELECT t.*, c.nombre as categoria_nombre 
            FROM tareas t
            LEFT JOIN categorias c ON t.categoria_id = c.id
            WHERE c.nombre = ?
            ORDER BY 
                CASE t.estado 
                    WHEN 'pendiente' THEN 1
                    WHEN 'vencida' THEN 2
                    WHEN 'completada' THEN 3
                END,
                CASE t.prioridad
                    WHEN 'alta' THEN 1
                    WHEN 'media' THEN 2
                    WHEN 'baja' THEN 3
                END,
                t.fecha_limite ASC
            ''', (categoria_filtro,))
        else:
            cursor.execute('''
            SELECT t.*, c.nombre as categoria_nombre 
            FROM tareas t
            LEFT JOIN categorias c ON t.categoria_id = c.id
            ORDER BY 
                CASE t.estado 
                    WHEN 'pendiente' THEN 1
                    WHEN 'vencida' THEN 2
                    WHEN 'completada' THEN 3
                END,
                CASE t.prioridad
                    WHEN 'alta' THEN 1
                    WHEN 'media' THEN 2
                    WHEN 'baja' THEN 3
                END,
                t.fecha_limite ASC
            ''')
        
        tareas = cursor.fetchall()
        conn.close()
        return tareas
    
    def obtener_tarea(self, tarea_id):
        """Obtiene una tarea específica por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT t.*, c.nombre as categoria_nombre 
        FROM tareas t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        WHERE t.id = ?
        ''', (tarea_id,))
        
        tarea = cursor.fetchone()
        conn.close()
        return tarea
    
    def actualizar_tarea(self, tarea_id, **kwargs):
        """Actualiza una tarea existente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Construir consulta dinámica
        campos = []
        valores = []
        
        for key, value in kwargs.items():
            if value is not None:
                campos.append(f"{key} = ?")
                valores.append(value)
        
        if not campos:
            conn.close()
            return False
        
        valores.append(tarea_id)
        query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
        
        cursor.execute(query, valores)
        conn.commit()
        afectadas = cursor.rowcount
        conn.close()
        
        return afectadas > 0
    
    def eliminar_tarea(self, tarea_id):
        """Elimina una tarea por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tareas WHERE id = ?', (tarea_id,))
        conn.commit()
        afectadas = cursor.rowcount
        conn.close()
        
        return afectadas > 0
    
    def marcar_como_completada(self, tarea_id):
        """Marca una tarea como completada"""
        return self.actualizar_tarea(tarea_id, estado='completada')
    
    # ===== OPERACIONES PARA CATEGORÍAS =====
    
    def obtener_categorias(self):
        """Obtiene todas las categorías"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM categorias ORDER BY nombre')
        categorias = cursor.fetchall()
        conn.close()
        return categorias
    
    # ===== OPERACIONES PARA NOTIFICACIONES =====
    
    def crear_notificacion(self, tarea_id, fecha_alerta):
        """Crea una notificación para una tarea"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO notificaciones (tarea_id, fecha_alerta)
        VALUES (?, ?)
        ''', (tarea_id, fecha_alerta))
        
        conn.commit()
        notificacion_id = cursor.lastrowid
        conn.close()
        return notificacion_id
    
    # ===== OPERACIONES PARA VOZ =====
    
    def guardar_comando_voz(self, texto, accion=None):
        """Guarda un comando de voz en la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO comandos_voz (texto, accion)
        VALUES (?, ?)
        ''', (texto, accion))
        
        conn.commit()
        comando_id = cursor.lastrowid
        conn.close()
        return comando_id
    
    def obtener_comandos_voz(self, limite=10):
        """Obtiene los últimos comandos de voz"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM comandos_voz 
        ORDER BY fecha_creacion DESC 
        LIMIT ?
        ''', (limite,))
        
        comandos = cursor.fetchall()
        conn.close()
        return comandos
    
    # ===== ESTADÍSTICAS =====
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas de las tareas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN estado = 'completada' THEN 1 ELSE 0 END) as completadas,
            SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
            SUM(CASE WHEN estado = 'pendiente' AND fecha_limite < date('now') THEN 1 ELSE 0 END) as vencidas
        FROM tareas
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        return dict(stats)

# Instancia global de la base de datos
db = Database()