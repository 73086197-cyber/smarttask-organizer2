"""
Modelos SQLAlchemy para SmartTask Organizer.

Define los modelos ORM que mapean las tablas de la base de datos SQLite.
Cada clase representa una tabla con sus campos, relaciones, índices y
validaciones. Utiliza SQLAlchemy 2.0+ con el patrón declarativo.

Modelos:
    - Categoria: Categorías para clasificar tareas (HU08, HU09).
    - Tarea: Tareas del usuario con estado, prioridad y fecha (HU01-HU07).
    - Etiqueta: Etiquetas adicionales para tareas (many-to-many).
    - HistorialAccion: Registro de todas las acciones del sistema.

Uso:
    from src.models import Base, Categoria, Tarea, Etiqueta, HistorialAccion
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Table,
    Index, CheckConstraint, UniqueConstraint, event
)
from sqlalchemy.orm import (
    DeclarativeBase, relationship, validates
)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos SQLAlchemy."""
    pass


# Tabla intermedia para relación many-to-many Tarea <-> Etiqueta
tarea_etiqueta = Table(
    'tarea_etiqueta',
    Base.metadata,
    Column('tarea_id', Integer, ForeignKey('tareas.id', ondelete='CASCADE'),
           primary_key=True),
    Column('etiqueta_id', Integer, ForeignKey('etiquetas.id', ondelete='CASCADE'),
           primary_key=True)
)


class Categoria(Base):
    """Modelo ORM para la tabla 'categorias'.

    Representa una categoría para clasificar tareas. Las categorías
    tienen nombre único y descripción opcional. Cada categoría puede
    tener múltiples tareas asignadas (relación 1:N).

    Attributes:
        id (int): Clave primaria autoincremental.
        nombre (str): Nombre único de la categoría (máx. 100 caracteres).
        descripcion (str): Descripción opcional de la categoría.
        tareas (list[Tarea]): Lista de tareas asignadas a esta categoría.

    Historias de usuario:
        - HU08: Crear categoría.
        - HU09: Asignar categoría a tarea.
        - HU10: Filtrar tareas por categoría.
    """

    __tablename__ = 'categorias'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)
    descripcion = Column(Text, default='')

    # Relación 1:N con Tarea
    tareas = relationship('Tarea', back_populates='categoria',
                          lazy='dynamic')

    @validates('nombre')
    def validar_nombre(self, key, valor):
        """Valida que el nombre de la categoría no esté vacío.

        Args:
            key (str): Nombre del campo ('nombre').
            valor (str): Valor a validar.

        Returns:
            str: Valor validado (strip aplicado).

        Raises:
            ValueError: Si el nombre está vacío o es None.
        """
        if not valor or not valor.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío")
        return valor.strip()

    def to_dict(self):
        """Convierte el modelo a diccionario para compatibilidad.

        Returns:
            dict: Diccionario con claves 'id', 'nombre', 'descripcion'.
        """
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion or ''
        }

    def __repr__(self):
        """Representación legible del modelo."""
        return f"<Categoria(id={self.id}, nombre='{self.nombre}')>"


class Tarea(Base):
    """Modelo ORM para la tabla 'tareas'.

    Representa una tarea del usuario con título, descripción, fecha
    límite, estado, prioridad y categoría asignada. Incluye validaciones
    para estado y prioridad mediante decoradores @validates.

    Attributes:
        id (int): Clave primaria autoincremental.
        titulo (str): Título de la tarea (obligatorio, máx. 200 caracteres).
        descripcion (str): Descripción detallada de la tarea.
        fecha_limite (str): Fecha límite en formato 'YYYY-MM-DD'. Nullable.
        estado (str): Estado actual. Valores: 'pendiente', 'completada', 'vencida'.
        prioridad (str): Nivel de prioridad. Valores: 'baja', 'media', 'alta'.
        categoria_id (int): FK a categorias.id. Nullable.
        fecha_creacion (str): Timestamp de creación (auto-generado).
        categoria (Categoria): Relación N:1 con Categoria.
        etiquetas (list[Etiqueta]): Relación N:M con Etiqueta.

    Historias de usuario:
        - HU01: Crear tarea.
        - HU02: Listar tareas.
        - HU03: Editar tarea.
        - HU04: Eliminar tarea.
        - HU05: Completar tarea.
        - HU06: Fecha límite.
        - HU07: Detectar vencidas.
    """

    __tablename__ = 'tareas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(200), nullable=False, index=True)
    descripcion = Column(Text, default='')
    fecha_limite = Column(String(10), nullable=True)
    estado = Column(
        String(20),
        CheckConstraint("estado IN ('pendiente', 'completada', 'vencida')"),
        default='pendiente'
    )
    prioridad = Column(
        String(10),
        CheckConstraint("prioridad IN ('baja', 'media', 'alta')"),
        default='media'
    )
    categoria_id = Column(Integer, ForeignKey('categorias.id'), nullable=True,
                          index=True)
    fecha_creacion = Column(String(30),
                            default=lambda: datetime.now().isoformat())

    # Relación N:1 con Categoria
    categoria = relationship('Categoria', back_populates='tareas')

    # Relación N:M con Etiqueta
    etiquetas = relationship('Etiqueta', secondary=tarea_etiqueta,
                             back_populates='tareas', lazy='select')

    # Índice compuesto para consultas frecuentes
    __table_args__ = (
        Index('idx_tarea_estado_prioridad', 'estado', 'prioridad'),
    )

    @validates('estado')
    def validar_estado(self, key, valor):
        """Valida que el estado sea uno de los valores permitidos.

        Args:
            key (str): Nombre del campo ('estado').
            valor (str): Valor a validar.

        Returns:
            str: Valor validado.

        Raises:
            ValueError: Si el estado no es válido.
        """
        estados_validos = ('pendiente', 'completada', 'vencida')
        if valor not in estados_validos:
            raise ValueError(
                f"Estado '{valor}' no válido. "
                f"Valores permitidos: {estados_validos}"
            )
        return valor

    @validates('prioridad')
    def validar_prioridad(self, key, valor):
        """Valida que la prioridad sea uno de los valores permitidos.

        Args:
            key (str): Nombre del campo ('prioridad').
            valor (str): Valor a validar.

        Returns:
            str: Valor validado.

        Raises:
            ValueError: Si la prioridad no es válida.
        """
        prioridades_validas = ('baja', 'media', 'alta')
        if valor not in prioridades_validas:
            raise ValueError(
                f"Prioridad '{valor}' no válida. "
                f"Valores permitidos: {prioridades_validas}"
            )
        return valor

    @validates('titulo')
    def validar_titulo(self, key, valor):
        """Valida que el título no esté vacío.

        Args:
            key (str): Nombre del campo ('titulo').
            valor (str): Valor a validar.

        Returns:
            str: Valor validado (strip aplicado).

        Raises:
            ValueError: Si el título está vacío o es None.
        """
        if not valor or not valor.strip():
            raise ValueError("El título de la tarea no puede estar vacío")
        return valor.strip()

    def to_dict(self):
        """Convierte el modelo a diccionario para compatibilidad.

        Incluye el nombre de la categoría si está asignada.

        Returns:
            dict: Diccionario con todos los campos de la tarea
                incluyendo 'categoria_nombre'.
        """
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion or '',
            'fecha_limite': self.fecha_limite,
            'estado': self.estado,
            'prioridad': self.prioridad,
            'categoria_id': self.categoria_id,
            'fecha_creacion': self.fecha_creacion,
            'categoria_nombre': self.categoria.nombre if self.categoria else None
        }

    def __repr__(self):
        """Representación legible del modelo."""
        return f"<Tarea(id={self.id}, titulo='{self.titulo}', estado='{self.estado}')>"


class Etiqueta(Base):
    """Modelo ORM para la tabla 'etiquetas'.

    Representa una etiqueta adicional para clasificar tareas.
    Las etiquetas tienen relación many-to-many con las tareas
    a través de la tabla intermedia 'tarea_etiqueta'.

    Attributes:
        id (int): Clave primaria autoincremental.
        nombre (str): Nombre único de la etiqueta (máx. 50 caracteres).
        color (str): Color en formato hexadecimal (ej: '#88C0D0').
        tareas (list[Tarea]): Tareas que tienen esta etiqueta.
    """

    __tablename__ = 'etiquetas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True, index=True)
    color = Column(String(7), default='#88C0D0')

    # Relación N:M con Tarea
    tareas = relationship('Tarea', secondary=tarea_etiqueta,
                          back_populates='etiquetas', lazy='select')

    @validates('nombre')
    def validar_nombre(self, key, valor):
        """Valida que el nombre de la etiqueta no esté vacío.

        Args:
            key (str): Nombre del campo ('nombre').
            valor (str): Valor a validar.

        Returns:
            str: Valor validado (strip aplicado).

        Raises:
            ValueError: Si el nombre está vacío o es None.
        """
        if not valor or not valor.strip():
            raise ValueError("El nombre de la etiqueta no puede estar vacío")
        return valor.strip()

    def to_dict(self):
        """Convierte el modelo a diccionario.

        Returns:
            dict: Diccionario con claves 'id', 'nombre', 'color'.
        """
        return {
            'id': self.id,
            'nombre': self.nombre,
            'color': self.color
        }

    def __repr__(self):
        """Representación legible del modelo."""
        return f"<Etiqueta(id={self.id}, nombre='{self.nombre}')>"


class HistorialAccion(Base):
    """Modelo ORM para la tabla 'historial_acciones'.

    Registra todas las acciones realizadas en el sistema para
    trazabilidad y auditoría. Cada registro almacena el tipo
    de acción, la tarea afectada y detalles adicionales.

    Attributes:
        id (int): Clave primaria autoincremental.
        tipo_accion (str): Tipo de acción realizada
            ('CREAR', 'EDITAR', 'ELIMINAR', 'COMPLETAR').
        tarea_titulo (str): Título de la tarea afectada.
        detalles (str): Descripción detallada de la acción.
        fecha (str): Timestamp de la acción (auto-generado).
    """

    __tablename__ = 'historial_acciones'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_accion = Column(String(20), nullable=False, index=True)
    tarea_titulo = Column(String(200), default='')
    detalles = Column(Text, default='')
    fecha = Column(String(30),
                   default=lambda: datetime.now().isoformat())

    @validates('tipo_accion')
    def validar_tipo_accion(self, key, valor):
        """Valida que el tipo de acción no esté vacío.

        Args:
            key (str): Nombre del campo ('tipo_accion').
            valor (str): Valor a validar.

        Returns:
            str: Valor validado.

        Raises:
            ValueError: Si el tipo de acción está vacío o es None.
        """
        if not valor or not valor.strip():
            raise ValueError("El tipo de acción no puede estar vacío")
        return valor.strip()

    def to_dict(self):
        """Convierte el modelo a diccionario.

        Returns:
            dict: Diccionario con claves 'id', 'tipo_accion',
                'tarea_titulo', 'detalles', 'fecha'.
        """
        return {
            'id': self.id,
            'tipo_accion': self.tipo_accion,
            'tarea_titulo': self.tarea_titulo,
            'detalles': self.detalles,
            'fecha': self.fecha
        }

    def __repr__(self):
        """Representación legible del modelo."""
        return (f"<HistorialAccion(id={self.id}, "
                f"tipo='{self.tipo_accion}', "
                f"tarea='{self.tarea_titulo}')>")
