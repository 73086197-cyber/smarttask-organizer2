"""
Configuración global de pytest para SmartTask Organizer.

Define fixtures reutilizables que configuran bases de datos en memoria
con SQLAlchemy para aislar cada prueba. Las fixtures proporcionan
entornos limpios y predecibles para las pruebas unitarias.

Fixtures disponibles:
    - db_limpia: Database con categorías por defecto y tareas de ejemplo.
    - db_vacia: Database solo con categorías, sin tareas.
    - tarea_ejemplo: Tarea de prueba creada en db_vacia.
    - categorias_ids: Diccionario {nombre: id} de categorías.
    - servicio_tareas: Instancia de TareaService.
    - servicio_categorias: Instancia de CategoriaService.
    - servicio_etiquetas: Instancia de EtiquetaService.
"""
import pytest
from src.database import Database
from src.services import TareaService, CategoriaService, EtiquetaService


@pytest.fixture
def db_limpia():
    """Crea una instancia de Database con BD en memoria, con datos por defecto.

    Yields:
        Database: Instancia con tablas creadas, categorías por defecto
            y tareas de ejemplo insertadas automáticamente.
    """
    db = Database(db_name=":memory:")
    yield db
    db.close()


@pytest.fixture
def db_vacia():
    """Crea una instancia de Database con BD en memoria, sin tareas.

    Las categorías por defecto se crean pero las tareas de ejemplo
    se eliminan para tener un entorno limpio.

    Yields:
        Database: Instancia con categorías pero sin tareas.
    """
    db = Database(db_name=":memory:")
    # Eliminar tareas de ejemplo para tener BD limpia
    tareas = db.obtener_todas_tareas()
    for tarea in tareas:
        db.eliminar_tarea(tarea['id'])
    yield db
    db.close()


@pytest.fixture
def tarea_ejemplo(db_vacia):
    """Crea una tarea de ejemplo en la base de datos vacía.

    Args:
        db_vacia (Database): Fixture de base de datos vacía.

    Returns:
        tuple: (Database, int) tupla con la instancia de DB y el ID
            de la tarea creada.
    """
    cats = db_vacia.obtener_categorias()
    cat_trabajo = next(c for c in cats if c['nombre'] == 'Trabajo')

    tarea_id = db_vacia.crear_tarea(
        titulo="Tarea de prueba",
        descripcion="Descripción de prueba",
        fecha_limite="2026-12-31",
        prioridad="alta",
        categoria_id=cat_trabajo['id']
    )
    return db_vacia, tarea_id


@pytest.fixture
def categorias_ids(db_vacia):
    """Obtiene un diccionario dinámico de categorías {nombre: id}.

    El número de categorías NO está hardcoded — se obtiene
    dinámicamente de la base de datos.

    Args:
        db_vacia (Database): Fixture de base de datos vacía.

    Returns:
        tuple: (Database, dict) tupla con DB y diccionario de categorías.
    """
    cats = db_vacia.obtener_categorias()
    cats_dict = {c['nombre']: c['id'] for c in cats}
    return db_vacia, cats_dict


@pytest.fixture
def servicio_tareas(db_limpia):
    """Instancia de TareaService con base de datos limpia.

    Args:
        db_limpia (Database): Fixture de base de datos con datos.

    Returns:
        tuple: (TareaService, Database) para pruebas de servicio.
    """
    svc = TareaService(db_limpia)
    return svc, db_limpia


@pytest.fixture
def servicio_categorias(db_vacia):
    """Instancia de CategoriaService con base de datos vacía.

    Args:
        db_vacia (Database): Fixture de base de datos vacía.

    Returns:
        tuple: (CategoriaService, Database) para pruebas de servicio.
    """
    svc = CategoriaService(db_vacia)
    return svc, db_vacia


@pytest.fixture
def servicio_etiquetas(db_vacia):
    """Instancia de EtiquetaService con base de datos vacía.

    Args:
        db_vacia (Database): Fixture de base de datos vacía.

    Returns:
        tuple: (EtiquetaService, Database) para pruebas de servicio.
    """
    svc = EtiquetaService(db_vacia)
    return svc, db_vacia
