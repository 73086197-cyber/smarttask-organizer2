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
        conn.row_factory = sqlite3.Row
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
        
        # Insertar categorías por defecto
        categorias_default = [
            ('Trabajo', 'Tareas relacionadas con el trabajo'),
            ('Personal', 'Tareas personales'),
            ('Hogar', 'Tareas del hogar'),
            ('Estudio', 'Tareas académicas'),
            ('Salud', 'Tareas de salud'),
            ('Finanzas', 'Tareas financieras')
        ]
        
        for nombre, descripcion in categorias_default:
            cursor.execute('INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)', 
                          (nombre, descripcion))
        
        # Verificar si hay tareas de ejemplo
        cursor.execute("SELECT COUNT(*) FROM tareas")
        if cursor.fetchone()[0] == 0:
            # Obtener IDs de categorías
            cursor.execute("SELECT id, nombre FROM categorias")
            categorias = {row['nombre']: row['id'] for row in cursor.fetchall()}
            
            tareas_ejemplo = [
                ('Revisar informe trimestral', 'Revisar datos y preparar presentación', 
                 '2024-12-15', 'pendiente', 'alta', categorias.get('Trabajo')),
                ('Comprar víveres', 'Ir al supermercado', 
                 '2024-11-30', 'pendiente', 'media', categorias.get('Hogar')),
                ('Estudiar para examen', 'Repasar capítulos 5-8', 
                 '2024-12-10', 'pendiente', 'alta', categorias.get('Estudio')),
                ('Llamar al médico', 'Pedir cita para revisión', 
                 None, 'completada', 'baja', categorias.get('Salud')),
                ('Enviar reporte semanal', 'Enviar por correo al equipo', 
                 '2024-11-25', 'completada', 'media', categorias.get('Trabajo')),
            ]
            
            for tarea in tareas_ejemplo:
                cursor.execute('''
                INSERT INTO tareas (titulo, descripcion, fecha_limite, estado, prioridad, categoria_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', tarea)
        
        conn.commit()
        conn.close()
        print(f"✅ Base de datos '{self.db_name}' inicializada")
    
    # ===== OPERACIONES CRUD =====
    
    def crear_tarea(self, titulo, descripcion="", fecha_limite=None, 
                   prioridad="media", categoria_id=None):
        """HU01: Crear nueva tarea"""
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
        """HU02: Obtener todas las tareas"""
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
        """Obtener una tarea específica"""
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
        """HU03: Actualizar tarea existente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
        """HU04: Eliminar tarea por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tareas WHERE id = ?', (tarea_id,))
        conn.commit()
        afectadas = cursor.rowcount
        conn.close()
        
        return afectadas > 0
    
    def marcar_como_completada(self, tarea_id):
        """HU05: Marcar tarea como completada"""
        return self.actualizar_tarea(tarea_id, estado='completada')
    
    def obtener_categorias(self):
        """Obtener todas las categorías"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM categorias ORDER BY nombre')
        categorias = cursor.fetchall()
        conn.close()
        return categorias
    
    def obtener_estadisticas(self):
        """Obtener estadísticas de las tareas"""
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