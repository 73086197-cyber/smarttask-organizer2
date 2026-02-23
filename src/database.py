"""
Módulo de base de datos para SmartTask Organizer (SQLAlchemy ORM).

Gestiona la persistencia de datos mediante SQLAlchemy con SQLite como
backend. Define la clase Database que encapsula todas las operaciones
CRUD (Crear, Leer, Actualizar, Eliminar) sobre las tablas del sistema.

Tablas gestionadas:
    - categorias: Categorías para clasificar tareas (HU08).
    - tareas: Tareas del usuario (HU01-HU07).
    - etiquetas: Etiquetas adicionales (many-to-many con tareas).
    - historial_acciones: Registro de acciones del sistema.
    - tarea_etiqueta: Tabla intermedia para relación N:M.

Uso:
    from src.database import db
    db.crear_tarea(titulo="Mi tarea", prioridad="alta")
"""
import os
from datetime import datetime, date

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session

from src.models import Base, Categoria, Tarea, Etiqueta, HistorialAccion


class Database:
    """Clase que gestiona la conexión y operaciones con SQLAlchemy ORM.

    Encapsula todas las operaciones CRUD necesarias para el manejo de
    tareas, categorías, etiquetas e historial. Al instanciarse, crea
    automáticamente las tablas si no existen e inserta datos por defecto.

    Attributes:
        db_name (str): Nombre del archivo de base de datos SQLite.
        engine: Motor de SQLAlchemy para la conexión.
        Session: Fábrica de sesiones con scope.

    Historias de usuario relacionadas:
        - HU01: Crear tarea.
        - HU02: Listar tareas.
        - HU03: Editar tarea.
        - HU04: Eliminar tarea.
        - HU05: Completar tarea.
        - HU06: Fecha límite.
        - HU07: Detectar vencidas (consulta de estadísticas).
        - HU08: Crear categoría (categorías por defecto).
        - HU09: Asignar categoría (campo categoria_id en tareas).
        - HU10: Filtrar por categoría (consulta con filtro).
    """

    def __init__(self, db_name="smarttask.db"):
        """Inicializa la instancia de Database con SQLAlchemy.

        Crea el engine, la fábrica de sesiones y las tablas si no
        existen. Inserta categorías por defecto y tareas de ejemplo.

        Args:
            db_name (str): Nombre del archivo de base de datos. Por
                defecto es 'smarttask.db'. Usar ':memory:' para tests.
        """
        self.db_name = db_name

        if db_name == ":memory:":
            self.engine = create_engine(
                "sqlite:///:memory:",
                echo=False
            )
        else:
            # Crear BD en la raíz del proyecto (junto a run.py)
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            db_path = os.path.join(project_root, db_name)
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                echo=False
            )

        self.Session = scoped_session(sessionmaker(bind=self.engine))

        self._init_db()

    def _get_session(self):
        """Obtiene una sesión de SQLAlchemy.

        Returns:
            Session: Sesión activa de SQLAlchemy.
        """
        return self.Session()

    def _init_db(self):
        """Inicializa la base de datos creando tablas y datos por defecto.

        Crea todas las tablas definidas en los modelos si no existen.
        Inserta 6 categorías por defecto y 5 tareas de ejemplo si la
        base de datos está vacía.
        """
        Base.metadata.create_all(self.engine)

        session = self._get_session()
        try:
            # Insertar categorías por defecto si no existen
            categorias_default = [
                ('Trabajo', 'Tareas relacionadas con el trabajo'),
                ('Personal', 'Tareas personales'),
                ('Hogar', 'Tareas del hogar'),
                ('Estudio', 'Tareas académicas'),
                ('Salud', 'Tareas de salud'),
                ('Finanzas', 'Tareas financieras')
            ]

            for nombre, descripcion in categorias_default:
                existente = session.query(Categoria).filter_by(
                    nombre=nombre
                ).first()
                if not existente:
                    categoria = Categoria(
                        nombre=nombre, descripcion=descripcion
                    )
                    session.add(categoria)

            session.commit()

            # Verificar si hay tareas de ejemplo
            conteo_tareas = session.query(func.count(Tarea.id)).scalar()
            if conteo_tareas == 0:
                # Obtener IDs de categorías
                categorias = {
                    cat.nombre: cat.id
                    for cat in session.query(Categoria).all()
                }

                tareas_ejemplo = [
                    Tarea(
                        titulo='Revisar informe trimestral',
                        descripcion='Revisar datos y preparar presentación',
                        fecha_limite='2024-12-15',
                        estado='pendiente',
                        prioridad='alta',
                        categoria_id=categorias.get('Trabajo')
                    ),
                    Tarea(
                        titulo='Comprar víveres',
                        descripcion='Ir al supermercado',
                        fecha_limite='2024-11-30',
                        estado='pendiente',
                        prioridad='media',
                        categoria_id=categorias.get('Hogar')
                    ),
                    Tarea(
                        titulo='Estudiar para examen',
                        descripcion='Repasar capítulos 5-8',
                        fecha_limite='2024-12-10',
                        estado='pendiente',
                        prioridad='alta',
                        categoria_id=categorias.get('Estudio')
                    ),
                    Tarea(
                        titulo='Llamar al médico',
                        descripcion='Pedir cita para revisión',
                        fecha_limite=None,
                        estado='completada',
                        prioridad='baja',
                        categoria_id=categorias.get('Salud')
                    ),
                    Tarea(
                        titulo='Enviar reporte semanal',
                        descripcion='Enviar por correo al equipo',
                        fecha_limite='2024-11-25',
                        estado='completada',
                        prioridad='media',
                        categoria_id=categorias.get('Trabajo')
                    ),
                ]

                for tarea in tareas_ejemplo:
                    session.add(tarea)

                session.commit()

            print(f"✅ Base de datos '{self.db_name}' inicializada (SQLAlchemy ORM)")

        except Exception as e:
            session.rollback()
            print(f"❌ Error inicializando BD: {e}")
        finally:
            session.close()

    # ===== OPERACIONES CRUD — TAREAS =====

    def crear_tarea(self, titulo, descripcion="", fecha_limite=None,
                    prioridad="media", categoria_id=None):
        """Crea una nueva tarea en la base de datos (HU01).

        Inserta un registro en la tabla 'tareas' con los datos
        proporcionados. El estado inicial siempre es 'pendiente'.

        Args:
            titulo (str): Título de la tarea. Campo obligatorio.
            descripcion (str): Descripción detallada. Por defecto vacía.
            fecha_limite (str): Fecha límite en formato 'YYYY-MM-DD' (HU06).
                None si no tiene fecha límite.
            prioridad (str): Nivel de prioridad. Valores permitidos:
                'baja', 'media' (por defecto), 'alta'.
            categoria_id (int): ID de la categoría a asignar (HU09).
                None si no se asigna categoría.

        Returns:
            int: ID autogenerado de la tarea recién creada.
        """
        session = self._get_session()
        try:
            tarea = Tarea(
                titulo=titulo,
                descripcion=descripcion,
                fecha_limite=fecha_limite,
                prioridad=prioridad,
                categoria_id=categoria_id
            )
            session.add(tarea)
            session.commit()
            tarea_id = tarea.id
            return tarea_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def obtener_todas_tareas(self, categoria_filtro=None):
        """Obtiene todas las tareas, opcionalmente filtradas por categoría (HU02, HU10).

        Los resultados se ordenan por:
            1. Estado (pendiente > vencida > completada)
            2. Prioridad (alta > media > baja)
            3. Fecha límite ascendente

        Args:
            categoria_filtro (str): Nombre de la categoría para filtrar (HU10).
                Si es None o 'TODAS', retorna todas las tareas sin filtro.

        Returns:
            list[dict]: Lista de tareas como diccionarios. Cada elemento
                incluye 'categoria_nombre' con el nombre de la categoría.
        """
        session = self._get_session()
        try:
            query = session.query(Tarea)

            if categoria_filtro and categoria_filtro != "TODAS":
                query = query.join(Categoria).filter(
                    Categoria.nombre == categoria_filtro
                )

            tareas = query.all()

            # Ordenar en Python para mantener compatibilidad exacta
            orden_estado = {'pendiente': 1, 'vencida': 2, 'completada': 3}
            orden_prioridad = {'alta': 1, 'media': 2, 'baja': 3}

            tareas.sort(key=lambda t: (
                orden_estado.get(t.estado, 4),
                orden_prioridad.get(t.prioridad, 4),
                t.fecha_limite or 'zzzz'
            ))

            return [self._tarea_a_dict(t) for t in tareas]

        finally:
            session.close()

    def obtener_tarea(self, tarea_id):
        """Obtiene una tarea específica por su ID.

        Args:
            tarea_id (int): ID único de la tarea a buscar.

        Returns:
            dict: Datos de la tarea con 'categoria_nombre'.
                Retorna None si la tarea no existe.
        """
        session = self._get_session()
        try:
            tarea = session.query(Tarea).filter_by(
                id=int(tarea_id)
            ).first()

            if tarea:
                return self._tarea_a_dict(tarea)
            return None

        finally:
            session.close()

    def actualizar_tarea(self, tarea_id, **kwargs):
        """Actualiza los campos de una tarea existente (HU03).

        Permite actualizar cualquier combinación de campos de la tarea
        usando argumentos con nombre.

        Args:
            tarea_id (int): ID de la tarea a actualizar.
            **kwargs: Campos a actualizar. Claves válidas:
                - titulo (str): Nuevo título.
                - descripcion (str): Nueva descripción.
                - fecha_limite (str): Nueva fecha en formato 'YYYY-MM-DD'.
                - estado (str): Nuevo estado.
                - prioridad (str): Nueva prioridad.
                - categoria_id (int): Nueva categoría.

        Returns:
            bool: True si se actualizó al menos un campo, False en caso
                contrario.
        """
        session = self._get_session()
        try:
            tarea = session.query(Tarea).filter_by(
                id=int(tarea_id)
            ).first()

            if not tarea:
                return False

            campos_actualizados = False
            for key, value in kwargs.items():
                if value is not None and hasattr(tarea, key):
                    setattr(tarea, key, value)
                    campos_actualizados = True

            if not campos_actualizados:
                return False

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def eliminar_tarea(self, tarea_id):
        """Elimina una tarea de la base de datos por su ID (HU04).

        Args:
            tarea_id (int): ID de la tarea a eliminar.

        Returns:
            bool: True si se eliminó la tarea, False si no se encontró.
        """
        session = self._get_session()
        try:
            tarea = session.query(Tarea).filter_by(
                id=int(tarea_id)
            ).first()

            if not tarea:
                return False

            session.delete(tarea)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def marcar_como_completada(self, tarea_id):
        """Marca una tarea como completada cambiando su estado (HU05).

        Args:
            tarea_id (int): ID de la tarea a completar.

        Returns:
            bool: True si se actualizó correctamente, False si no existe.
        """
        return self.actualizar_tarea(tarea_id, estado='completada')

    def actualizar_vencidas(self):
        """Detecta y marca como 'vencida' todas las tareas pendientes cuya
        fecha límite ya ha pasado (HU07).

        Recorre todas las tareas con estado 'pendiente' y fecha_limite
        definida. Si la fecha es anterior a hoy, actualiza el estado a
        'vencida' en la BD.

        Returns:
            int: Número de tareas marcadas como vencidas en esta llamada.
        """
        session = self._get_session()
        hoy = date.today()
        actualizadas = 0
        try:
            tareas = session.query(Tarea).filter(
                Tarea.estado == 'pendiente',
                Tarea.fecha_limite.isnot(None)
            ).all()
            for tarea in tareas:
                try:
                    fecha = datetime.strptime(tarea.fecha_limite, "%Y-%m-%d").date()
                    if fecha < hoy:
                        tarea.estado = 'vencida'
                        actualizadas += 1
                except (ValueError, TypeError):
                    pass
            if actualizadas:
                session.commit()
        except Exception:
            session.rollback()
        return actualizadas

    # ===== OPERACIONES CRUD — CATEGORÍAS =====


    def obtener_categorias(self):
        """Obtiene todas las categorías disponibles (HU08).

        Retorna las categorías ordenadas alfabéticamente por nombre.
        El número de categorías es dinámico (no está limitado a 6).

        Returns:
            list[dict]: Lista de categorías como diccionarios.
                Cada elemento tiene: 'id', 'nombre', 'descripcion'.
        """
        session = self._get_session()
        try:
            categorias = session.query(Categoria).order_by(
                Categoria.nombre
            ).all()
            return [cat.to_dict() for cat in categorias]
        finally:
            session.close()

    def crear_categoria(self, nombre, descripcion=""):
        """Crea una nueva categoría en la base de datos.

        Valida que el nombre sea único antes de insertar.

        Args:
            nombre (str): Nombre de la categoría. Debe ser único.
            descripcion (str): Descripción opcional. Por defecto vacía.

        Returns:
            int: ID de la categoría creada.

        Raises:
            ValueError: Si el nombre ya existe o está vacío.
        """
        session = self._get_session()
        try:
            # Verificar unicidad
            existente = session.query(Categoria).filter_by(
                nombre=nombre.strip()
            ).first()
            if existente:
                raise ValueError(
                    f"Ya existe una categoría con el nombre '{nombre}'"
                )

            categoria = Categoria(
                nombre=nombre, descripcion=descripcion
            )
            session.add(categoria)
            session.commit()
            return categoria.id

        except ValueError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def actualizar_categoria(self, cat_id, **kwargs):
        """Actualiza los campos de una categoría existente.

        Args:
            cat_id (int): ID de la categoría a actualizar.
            **kwargs: Campos a actualizar ('nombre', 'descripcion').

        Returns:
            bool: True si se actualizó, False si no se encontró.

        Raises:
            ValueError: Si el nuevo nombre ya existe en otra categoría.
        """
        session = self._get_session()
        try:
            categoria = session.query(Categoria).filter_by(
                id=int(cat_id)
            ).first()

            if not categoria:
                return False

            # Verificar unicidad del nombre si se está cambiando
            if 'nombre' in kwargs and kwargs['nombre']:
                nuevo_nombre = kwargs['nombre'].strip()
                existente = session.query(Categoria).filter(
                    Categoria.nombre == nuevo_nombre,
                    Categoria.id != int(cat_id)
                ).first()
                if existente:
                    raise ValueError(
                        f"Ya existe una categoría con el nombre "
                        f"'{nuevo_nombre}'"
                    )

            for key, value in kwargs.items():
                if value is not None and hasattr(categoria, key):
                    setattr(categoria, key, value)

            session.commit()
            return True

        except ValueError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def eliminar_categoria(self, cat_id):
        """Elimina una categoría de la base de datos.

        Valida integridad referencial: no permite eliminar una
        categoría que tenga tareas asignadas.

        Args:
            cat_id (int): ID de la categoría a eliminar.

        Returns:
            bool: True si se eliminó correctamente.

        Raises:
            ValueError: Si la categoría tiene tareas asignadas.
        """
        session = self._get_session()
        try:
            categoria = session.query(Categoria).filter_by(
                id=int(cat_id)
            ).first()

            if not categoria:
                return False

            # Validar integridad referencial
            tareas_count = session.query(func.count(Tarea.id)).filter_by(
                categoria_id=int(cat_id)
            ).scalar()

            if tareas_count > 0:
                raise ValueError(
                    f"No se puede eliminar la categoría "
                    f"'{categoria.nombre}' porque tiene "
                    f"{tareas_count} tarea(s) asignada(s). "
                    f"Reasigna o elimina las tareas primero."
                )

            session.delete(categoria)
            session.commit()
            return True

        except ValueError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ===== OPERACIONES CRUD — ETIQUETAS =====

    def crear_etiqueta(self, nombre, color="#88C0D0"):
        """Crea una nueva etiqueta en la base de datos.

        Args:
            nombre (str): Nombre de la etiqueta. Debe ser único.
            color (str): Color hexadecimal. Por defecto '#88C0D0'.

        Returns:
            int: ID de la etiqueta creada.

        Raises:
            ValueError: Si el nombre ya existe o está vacío.
        """
        session = self._get_session()
        try:
            existente = session.query(Etiqueta).filter_by(
                nombre=nombre.strip()
            ).first()
            if existente:
                raise ValueError(
                    f"Ya existe una etiqueta con el nombre '{nombre}'"
                )

            etiqueta = Etiqueta(nombre=nombre, color=color)
            session.add(etiqueta)
            session.commit()
            return etiqueta.id

        except ValueError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def obtener_etiquetas(self):
        """Obtiene todas las etiquetas disponibles.

        Returns:
            list[dict]: Lista de etiquetas como diccionarios.
        """
        session = self._get_session()
        try:
            etiquetas = session.query(Etiqueta).order_by(
                Etiqueta.nombre
            ).all()
            return [etiq.to_dict() for etiq in etiquetas]
        finally:
            session.close()

    def eliminar_etiqueta(self, etiq_id):
        """Elimina una etiqueta de la base de datos.

        Args:
            etiq_id (int): ID de la etiqueta a eliminar.

        Returns:
            bool: True si se eliminó, False si no se encontró.
        """
        session = self._get_session()
        try:
            etiqueta = session.query(Etiqueta).filter_by(
                id=int(etiq_id)
            ).first()

            if not etiqueta:
                return False

            session.delete(etiqueta)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ===== HISTORIAL DE ACCIONES =====

    def registrar_historial(self, tipo_accion, tarea_titulo="",
                            detalles=""):
        """Registra una acción en el historial del sistema.

        Args:
            tipo_accion (str): Tipo de acción ('CREAR', 'EDITAR',
                'ELIMINAR', 'COMPLETAR').
            tarea_titulo (str): Título de la tarea afectada.
            detalles (str): Descripción detallada de la acción.

        Returns:
            int: ID del registro de historial creado.
        """
        session = self._get_session()
        try:
            registro = HistorialAccion(
                tipo_accion=tipo_accion,
                tarea_titulo=tarea_titulo,
                detalles=detalles
            )
            session.add(registro)
            session.commit()
            return registro.id

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def obtener_historial(self, limite=50):
        """Obtiene el historial de acciones recientes.

        Args:
            limite (int): Número máximo de registros. Por defecto 50.

        Returns:
            list[dict]: Lista de registros ordenados por fecha desc.
        """
        session = self._get_session()
        try:
            registros = session.query(HistorialAccion).order_by(
                HistorialAccion.id.desc()
            ).limit(limite).all()
            return [reg.to_dict() for reg in registros]
        finally:
            session.close()

    # ===== ESTADÍSTICAS =====

    def obtener_estadisticas(self):
        """Obtiene estadísticas generales de las tareas.

        Calcula conteos agregados de tareas por estado. Las tareas
        pendientes con fecha límite pasada se cuentan como vencidas (HU07).

        Returns:
            dict: Diccionario con las claves:
                - 'total' (int): Número total de tareas.
                - 'completadas' (int): Tareas completadas.
                - 'pendientes' (int): Tareas pendientes no vencidas.
                - 'vencidas' (int): Tareas vencidas o pendientes con
                  fecha límite pasada.
        """
        session = self._get_session()
        try:
            tareas = session.query(Tarea).all()

            total = len(tareas)
            completadas = 0
            pendientes = 0
            vencidas = 0
            hoy = date.today().isoformat()

            for tarea in tareas:
                if tarea.estado == 'completada':
                    completadas += 1
                elif tarea.estado == 'vencida':
                    vencidas += 1
                elif tarea.estado == 'pendiente':
                    if tarea.fecha_limite and tarea.fecha_limite < hoy:
                        vencidas += 1
                    else:
                        pendientes += 1

            return {
                'total': total,
                'completadas': completadas,
                'pendientes': pendientes,
                'vencidas': vencidas
            }

        finally:
            session.close()

    # ===== UTILIDADES INTERNAS =====

    def _tarea_a_dict(self, tarea):
        """Convierte un objeto Tarea a diccionario compatible.

        Crea un objeto tipo DictRow que soporta acceso por clave
        (como sqlite3.Row) para mantener compatibilidad con el
        código existente de main.py y dialogos.py.

        Args:
            tarea (Tarea): Instancia del modelo Tarea.

        Returns:
            DictRow: Objeto con acceso por clave y por .keys().
        """
        data = {
            'id': tarea.id,
            'titulo': tarea.titulo,
            'descripcion': tarea.descripcion or '',
            'fecha_limite': tarea.fecha_limite,
            'estado': tarea.estado,
            'prioridad': tarea.prioridad,
            'categoria_id': tarea.categoria_id,
            'fecha_creacion': tarea.fecha_creacion,
            'categoria_nombre': (
                tarea.categoria.nombre if tarea.categoria else None
            )
        }
        return DictRow(data)

    def actualizar_vencidas(self):
        """Detecta y marca tareas pendientes vencidas (HU07).

        Revisa todas las tareas con estado 'pendiente' y fecha límite
        anterior a hoy, cambiando su estado a 'vencida'.

        Returns:
            int: Número de tareas marcadas como vencidas.
        """
        session = self._get_session()
        try:
            hoy = date.today().isoformat()
            tareas = session.query(Tarea).filter(
                Tarea.estado == 'pendiente',
                Tarea.fecha_limite.isnot(None),
                Tarea.fecha_limite < hoy
            ).all()
            for tarea in tareas:
                tarea.estado = 'vencida'
            session.commit()
            return len(tareas)
        except Exception as e:
            session.rollback()
            print(f"Error actualizando vencidas: {e}")
            return 0

    def close(self):
        """Cierra todas las sesiones y el engine.

        Libera los recursos de la conexión a la base de datos.
        """
        self.Session.remove()
        self.engine.dispose()


class DictRow(dict):
    """Diccionario que simula sqlite3.Row para compatibilidad.

    Permite acceso por clave tanto con notación de corchetes
    como con el método .keys(), manteniendo compatibilidad con
    el código que usaba sqlite3.Row anteriormente.

    Example:
        >>> row = DictRow({'titulo': 'Test', 'estado': 'pendiente'})
        >>> row['titulo']
        'Test'
        >>> 'titulo' in row.keys()
        True
    """

    def keys(self):
        """Retorna las claves del diccionario.

        Returns:
            dict_keys: Claves disponibles.
        """
        return super().keys()


# Instancia global de la base de datos
db = Database()