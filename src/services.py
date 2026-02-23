"""
Capa de servicios para SmartTask Organizer (Patrón Service Layer).

Implementa la lógica de negocio entre las vistas (main.py, dialogos.py)
y la capa de datos (database.py). Centraliza validaciones, reglas
de negocio y orquestación de operaciones.

Servicios:
    - TareaService: Gestión de tareas con validaciones.
    - CategoriaService: Gestión de categorías con integridad referencial.
    - EtiquetaService: Gestión de etiquetas.

Uso:
    from src.services import TareaService, CategoriaService
    tarea_svc = TareaService(db)
    tarea_svc.crear("Mi tarea", prioridad="alta")
"""
from datetime import datetime, date


class TareaService:
    """Servicio de lógica de negocio para tareas.

    Encapsula las reglas de negocio de las tareas, como validaciones
    de fechas, detección de vencidas y cálculo de estadísticas.
    Delega las operaciones de persistencia a Database.

    Attributes:
        db (Database): Instancia de Database para persistencia.

    Historias de usuario:
        - HU01: Crear tarea.
        - HU02: Listar tareas.
        - HU03: Editar tarea.
        - HU04: Eliminar tarea.
        - HU05: Completar tarea.
        - HU06: Validar fecha límite.
        - HU07: Detectar tareas vencidas.
    """

    def __init__(self, db):
        """Inicializa el servicio con una instancia de Database.

        Args:
            db (Database): Instancia de Database para operaciones CRUD.
        """
        self.db = db

    def crear(self, titulo, descripcion="", fecha_limite=None,
              prioridad="media", categoria_id=None):
        """Crea una nueva tarea con validaciones de negocio.

        Valida la fecha límite si se proporciona. Registra la acción
        en el historial del sistema.

        Args:
            titulo (str): Título de la tarea. Obligatorio.
            descripcion (str): Descripción detallada. Por defecto vacía.
            fecha_limite (str): Fecha en formato 'YYYY-MM-DD'. Opcional.
            prioridad (str): 'baja', 'media' o 'alta'. Por defecto 'media'.
            categoria_id (int): ID de categoría. Opcional.

        Returns:
            int: ID de la tarea creada.

        Raises:
            ValueError: Si el título está vacío o la fecha es inválida.
        """
        if not titulo or not titulo.strip():
            raise ValueError("El título es obligatorio")

        if fecha_limite:
            self._validar_fecha(fecha_limite)

        tarea_id = self.db.crear_tarea(
            titulo=titulo,
            descripcion=descripcion,
            fecha_limite=fecha_limite,
            prioridad=prioridad,
            categoria_id=categoria_id
        )

        self.db.registrar_historial(
            "CREAR", titulo,
            f"Tarea creada con prioridad {prioridad}"
        )

        return tarea_id

    def obtener_todas(self, filtro_categoria=None):
        """Obtiene todas las tareas con filtro opcional.

        Args:
            filtro_categoria (str): Nombre de categoría para filtrar.
                None o 'TODAS' para obtener todas.

        Returns:
            list[dict]: Lista de tareas como diccionarios.
        """
        return self.db.obtener_todas_tareas(filtro_categoria)

    def obtener(self, tarea_id):
        """Obtiene una tarea por su ID.

        Args:
            tarea_id (int): ID de la tarea.

        Returns:
            dict: Datos de la tarea, o None si no existe.
        """
        return self.db.obtener_tarea(tarea_id)

    def actualizar(self, tarea_id, **kwargs):
        """Actualiza una tarea existente con validaciones.

        Args:
            tarea_id (int): ID de la tarea a actualizar.
            **kwargs: Campos a actualizar.

        Returns:
            bool: True si se actualizó correctamente.

        Raises:
            ValueError: Si la fecha límite es inválida.
        """
        if 'fecha_limite' in kwargs and kwargs['fecha_limite']:
            self._validar_fecha(kwargs['fecha_limite'])

        resultado = self.db.actualizar_tarea(tarea_id, **kwargs)

        if resultado:
            tarea = self.db.obtener_tarea(tarea_id)
            titulo = tarea['titulo'] if tarea else 'Desconocida'
            self.db.registrar_historial(
                "EDITAR", titulo,
                f"Campos actualizados: {list(kwargs.keys())}"
            )

        return resultado

    def eliminar(self, tarea_id):
        """Elimina una tarea por su ID.

        Registra la acción en el historial antes de eliminar.

        Args:
            tarea_id (int): ID de la tarea a eliminar.

        Returns:
            bool: True si se eliminó correctamente.
        """
        tarea = self.db.obtener_tarea(tarea_id)
        resultado = self.db.eliminar_tarea(tarea_id)

        if resultado and tarea:
            self.db.registrar_historial(
                "ELIMINAR", tarea['titulo'],
                "Tarea eliminada permanentemente"
            )

        return resultado

    def completar(self, tarea_id):
        """Marca una tarea como completada (HU05).

        Args:
            tarea_id (int): ID de la tarea a completar.

        Returns:
            bool: True si se completó correctamente.
        """
        tarea = self.db.obtener_tarea(tarea_id)
        resultado = self.db.marcar_como_completada(tarea_id)

        if resultado and tarea:
            self.db.registrar_historial(
                "COMPLETAR", tarea['titulo'],
                "Tarea marcada como completada"
            )

        return resultado

    def detectar_vencidas(self):
        """Detecta y marca tareas pendientes que han vencido (HU07).

        Revisa todas las tareas pendientes y marca como 'vencida'
        aquellas cuya fecha límite ya ha pasado.

        Returns:
            int: Número de tareas detectadas como vencidas.
        """
        tareas = self.db.obtener_todas_tareas()
        hoy = date.today().isoformat()
        conteo = 0

        for tarea in tareas:
            if (tarea['estado'] == 'pendiente' and
                    tarea['fecha_limite'] and
                    tarea['fecha_limite'] < hoy):
                self.db.actualizar_tarea(
                    tarea['id'], estado='vencida'
                )
                conteo += 1

        return conteo

    def obtener_estadisticas(self):
        """Obtiene estadísticas de las tareas.

        Returns:
            dict: Diccionario con 'total', 'completadas',
                'pendientes', 'vencidas'.
        """
        return self.db.obtener_estadisticas()

    def _validar_fecha(self, fecha_str):
        """Valida que la fecha tenga formato correcto YYYY-MM-DD.

        Args:
            fecha_str (str): Fecha a validar.

        Raises:
            ValueError: Si el formato es inválido.
        """
        try:
            datetime.strptime(fecha_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError(
                f"Formato de fecha inválido: '{fecha_str}'. "
                f"Use el formato YYYY-MM-DD"
            )


class CategoriaService:
    """Servicio de lógica de negocio para categorías.

    Gestiona categorías con validaciones de integridad referencial
    y unicidad. El número de categorías es dinámico.

    Attributes:
        db (Database): Instancia de Database para persistencia.
    """

    def __init__(self, db):
        """Inicializa el servicio con una instancia de Database.

        Args:
            db (Database): Instancia de Database.
        """
        self.db = db

    def crear(self, nombre, descripcion=""):
        """Crea una nueva categoría.

        Args:
            nombre (str): Nombre de la categoría. Debe ser único.
            descripcion (str): Descripción opcional.

        Returns:
            int: ID de la categoría creada.

        Raises:
            ValueError: Si el nombre está vacío o ya existe.
        """
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la categoría es obligatorio")

        return self.db.crear_categoria(nombre, descripcion)

    def obtener_todas(self):
        """Obtiene todas las categorías disponibles.

        Returns:
            list[dict]: Lista de categorías con 'id', 'nombre',
                'descripcion'. Cantidad dinámica (no fija).
        """
        return self.db.obtener_categorias()

    def actualizar(self, cat_id, nombre=None, descripcion=None):
        """Actualiza una categoría existente.

        Args:
            cat_id (int): ID de la categoría.
            nombre (str): Nuevo nombre. Opcional.
            descripcion (str): Nueva descripción. Opcional.

        Returns:
            bool: True si se actualizó correctamente.
        """
        kwargs = {}
        if nombre is not None:
            kwargs['nombre'] = nombre
        if descripcion is not None:
            kwargs['descripcion'] = descripcion

        return self.db.actualizar_categoria(cat_id, **kwargs)

    def eliminar(self, cat_id):
        """Elimina una categoría validando integridad referencial.

        No permite eliminar categorías que tengan tareas asignadas.

        Args:
            cat_id (int): ID de la categoría a eliminar.

        Returns:
            bool: True si se eliminó correctamente.

        Raises:
            ValueError: Si la categoría tiene tareas asignadas.
        """
        return self.db.eliminar_categoria(cat_id)

    def puede_eliminar(self, cat_id):
        """Verifica si una categoría se puede eliminar.

        Args:
            cat_id (int): ID de la categoría.

        Returns:
            bool: True si la categoría no tiene tareas asignadas.
        """
        try:
            self.db.eliminar_categoria(cat_id)
            return True
        except ValueError:
            return False

    def contar(self):
        """Cuenta el número total de categorías.

        Returns:
            int: Número de categorías. Dinámico, sin límite fijo.
        """
        return len(self.db.obtener_categorias())


class EtiquetaService:
    """Servicio de lógica de negocio para etiquetas.

    Attributes:
        db (Database): Instancia de Database para persistencia.
    """

    def __init__(self, db):
        """Inicializa el servicio con una instancia de Database.

        Args:
            db (Database): Instancia de Database.
        """
        self.db = db

    def crear(self, nombre, color="#88C0D0"):
        """Crea una nueva etiqueta.

        Args:
            nombre (str): Nombre de la etiqueta. Debe ser único.
            color (str): Color hexadecimal. Por defecto '#88C0D0'.

        Returns:
            int: ID de la etiqueta creada.

        Raises:
            ValueError: Si el nombre está vacío o ya existe.
        """
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la etiqueta es obligatorio")

        return self.db.crear_etiqueta(nombre, color)

    def obtener_todas(self):
        """Obtiene todas las etiquetas disponibles.

        Returns:
            list[dict]: Lista de etiquetas con 'id', 'nombre', 'color'.
        """
        return self.db.obtener_etiquetas()

    def eliminar(self, etiq_id):
        """Elimina una etiqueta por su ID.

        Args:
            etiq_id (int): ID de la etiqueta a eliminar.

        Returns:
            bool: True si se eliminó correctamente.
        """
        return self.db.eliminar_etiqueta(etiq_id)
