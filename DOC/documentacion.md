# 📚 Documentación Técnica — SmartTask Organizer

**Materia:** Construcción de Software  
**Proyecto:** SmartTask Organizer — Sistema de Gestión de Tareas  
**Año:** 2026  

**Integrantes del equipo:**
- Dickmar Wilber Julca Laureano
- Italo Eduardo Reyes Cordero
- Jack Joshua Bendezu Lagos
- Simon Ronaldo Gonzales Jacinto

## 1. Arquitectura General del Sistema

SmartTask Organizer sigue el patrón **MVC (Modelo–Vista–Controlador)** con una **capa de servicios** adicional que separa la lógica de negocio del acceso a datos.

```
┌─────────────────────────────────────────────────────────┐
│              CAPA DE VISTA (Presentación)                │
│   main.py (SmartTaskApp)  +  dialogos.py (Diálogos)     │
│   Tkinter + ttk — Interfaz gráfica de escritorio        │
├─────────────────────────────────────────────────────────┤
│              CAPA DE SERVICIOS (Negocio)                 │
│   services.py — TareaService, CategoriaService,         │
│                 EtiquetaService                          │
│   Validaciones, reglas de negocio, historial            │
├─────────────────────────────────────────────────────────┤
│              CAPA DE DATOS (Persistencia)                │
│   database.py — Database (CRUD via SQLAlchemy ORM)      │
│   SQLite como motor de base de datos                    │
├─────────────────────────────────────────────────────────┤
│              CAPA DE MODELOS (Dominio)                   │
│   models.py — Categoria, Tarea, Etiqueta,               │
│               HistorialAccion (SQLAlchemy DeclarativeBase)│
└─────────────────────────────────────────────────────────┘
```

### Diagrama de flujo de una operación típica

```
Usuario → Vista (main.py/dialogos.py)
       → Service (services.py) [validación de reglas]
       → Database (database.py) [operación CRUD]
       → Modelo ORM (models.py) [mapeo a SQLite]
       → smarttask.db (archivo SQLite físico)
```

### Entidades del dominio

| Entidad | Tabla SQLite | Descripción | Relaciones |
|---|---|---|---|
| `Categoria` | `categorias` | Clasificación de tareas | 1:N con Tarea |
| `Tarea` | `tareas` | Unidad de trabajo principal | N:1 Categoria, N:M Etiqueta |
| `Etiqueta` | `etiquetas` | Tags adicionales para tareas | N:M con Tarea |
| `HistorialAccion` | `historial_acciones` | Registro auditable de operaciones | Independiente |
| *(tabla intermedia)* | `tarea_etiqueta` | Relaciona tareas con etiquetas | FK tarea_id, etiqueta_id |

### Historias de Usuario implementadas

| HU | Nombre | Estado |
|---|---|---|
| HU01 | Crear tarea | ✅ |
| HU02 | Listar tareas | ✅ |
| HU03 | Editar tarea | ✅ |
| HU04 | Eliminar tarea | ✅ |
| HU05 | Completar tarea | ✅ |
| HU06 | Fecha límite con validación | ✅ |
| HU07 | Detectar tareas vencidas | ✅ |
| HU08 | Crear categoría (CRUD) | ✅ |
| HU09 | Asignar categoría a tarea | ✅ |
| HU10 | Filtrar tareas por categoría | ✅ |
| HU11 | Crear tarea por voz | ✅ |
| HU12 | Notificaciones de tareas vencidas | ✅ |

**Funcionalidades adicionales:**
- Gráficos estadísticos con matplotlib (tema Nord)
- Exportación a CSV compatible con Excel
- Deshacer acciones con Ctrl+Z (patrón Pila LIFO)
- Sistema de etiquetas N:M
- Historial completo de acciones del sistema
- Síntesis de voz (texto a voz, pyttsx3)

---

## 2. Principales Decisiones de Diseño

### 2.1 Uso de SQLAlchemy ORM en lugar de sqlite3 puro

**Decisión:** Se eligió SQLAlchemy 2.0+ con el patrón DeclarativeBase en lugar de usar directamente el módulo `sqlite3` de Python.

**Justificación:**
- Permite definir los modelos como clases Python con validaciones via `@validates`
- Facilita las migraciones y extensión del esquema sin SQL manual
- Las relaciones (1:N, N:M) se gestionan automáticamente por el ORM
- Los tests pueden usar bases de datos en memoria (`:memory:`) sin cambiar el código
- Mayor legibilidad y mantenibilidad del código de acceso a datos

**Compatibilidad:** Se creó la clase auxiliar `DictRow` (en `database.py`) para que los resultados del ORM sean compatibles con el código de la vista que anteriormente usaba `sqlite3.Row`.

### 2.2 Patrón Service Layer (Capa de Servicios)

**Decisión:** Se introdujo una capa de servicios (`services.py`) entre la vista y la base de datos.

**Justificación:**
- Centraliza las validaciones de negocio (fechas, títulos vacíos, integridad referencial)
- Registra automáticamente el historial de acciones sin que la vista lo gestione
- Facilita el testing unitario: los servicios se pueden testear con cualquier implementación de Database
- Cumple con el principio de responsabilidad única (SRP)

### 2.3 Patrón Pila LIFO para Deshacer (undo_manager.py)

**Decisión:** Se implementó el patrón Memento/Pila para la funcionalidad de deshacer (Ctrl+Z).

**Justificación:**
- El `UndoManager` mantiene una pila de acciones reversibles
- Cada operación (crear, editar, eliminar) empuja un comando inverso a la pila
- Al presionar Ctrl+Z, se extrae (pop) y ejecuta el comando inverso
- Diseño extensible: agregar nuevas acciones reversibles solo requiere definir el inverso

### 2.4 Categorías dinámicas (no hardcodeadas)

**Decisión:** El número y nombres de categorías son completamente dinámicos (leídos de la BD), en lugar de ser valores fijos en el código.

**Justificación:**
- Los RadioButtons de filtro se generan programáticamente al cargar la interfaz
- Al agregar o eliminar una categoría, los filtros se actualizan automáticamente
- No requiere modificar código fuente para gestionar categorías

### 2.5 Tema visual Nord

**Decisión:** Se implementó un sistema de colores propio basado en el tema Nord.

**Justificación:**
- Mejora la experiencia visual y la legibilidad
- Los colores tienen semántica: rojo = vencida, verde = completada, amarillo = alta prioridad, cyan = media prioridad
- Definidos como constantes en `main.py` para facilitar cambios globales

### 2.6 Base de datos en memoria para tests

**Decisión:** Los tests usan `Database(db_name=":memory:")` en lugar del archivo `smarttask.db`.

**Justificación:**
- Los tests no afectan ni dependen de datos reales
- Cada test obtiene una BD limpia e independiente via fixtures de pytest
- Los tests son reproducibles y deterministas

---

## 3. Descripción Funcional de los Módulos

### 3.1 `src/models.py` — Modelos ORM

Define las 4 entidades del dominio usando SQLAlchemy DeclarativeBase.

| Clase | Tabla | Responsabilidad |
|---|---|---|
| `Base` | — | Clase base declarativa de SQLAlchemy |
| `Categoria` | `categorias` | Modelo de categoría con validación de nombre |
| `Tarea` | `tareas` | Modelo principal: título, estado, prioridad, fecha |
| `Etiqueta` | `etiquetas` | Etiquetas con color hexadecimal |
| `HistorialAccion` | `historial_acciones` | Registro de operaciones del sistema |

**Características destacadas:**
- `@validates` en todos los modelos para validación a nivel ORM
- `CheckConstraint` para estado (`pendiente/completada/vencida`) y prioridad (`baja/media/alta`)
- `UniqueConstraint` en nombres de categorías y etiquetas
- Índices compuestos para consultas frecuentes (estado + prioridad)
- Método `to_dict()` en cada modelo para serialización

---

### 3.2 `src/database.py` — Capa de Datos (CRUD)

Encapsula todas las operaciones sobre la base de datos SQLite via SQLAlchemy.

| Método principal | Descripción |
|---|---|
| `__init__(db_name)` | Crea engine, sesiones, tablas y datos por defecto |
| `crear_tarea(titulo, ...)` | Inserta nueva tarea. Retorna ID. |
| `obtener_todas_tareas(filtro)` | Lista ordenada por estado/prioridad. Filtro por categoría. |
| `obtener_tarea(id)` | Tarea por ID como DictRow. None si no existe. |
| `actualizar_tarea(id, **kwargs)` | Actualiza campos dinámicamente. Retorna bool. |
| `eliminar_tarea(id)` | Elimina por ID. Retorna bool. |
| `marcar_como_completada(id)` | Cambia estado a 'completada'. |
| `obtener_categorias()` | Lista todas las categorías ordenadas por nombre. |
| `crear_categoria(nombre, desc)` | Crea con validación de unicidad. |
| `actualizar_categoria(id, ...)` | Actualiza nombre/descripción con validación. |
| `eliminar_categoria(id)` | Valida integridad referencial antes de eliminar. |
| `crear_etiqueta(nombre, color)` | Crea etiqueta con validación de unicidad. |
| `obtener_etiquetas()` | Lista todas las etiquetas. |
| `eliminar_etiqueta(id)` | Elimina etiqueta por ID. |
| `registrar_historial(tipo, ...)` | Inserta registro en historial. |
| `obtener_historial(limite)` | Historial reciente (desc por fecha). |
| `obtener_estadisticas()` | Conteos: total, completadas, pendientes, vencidas. |
| `actualizar_vencidas()` | Marca pendientes con fecha pasada como vencidas. |
| `close()` | Cierra sesiones y engine. |

**Clase auxiliar `DictRow`:** Subclase de `dict` que simula la interfaz de `sqlite3.Row` para compatibilidad con la capa de vista.

---

### 3.3 `src/services.py` — Capa de Servicios (Lógica de Negocio)

Implementa el patrón Service Layer. Cada servicio recibe una instancia de `Database`.

#### `TareaService`

| Método | Descripción |
|---|---|
| `crear(titulo, ...)` | Valida título y fecha. Crea tarea. Registra historial. |
| `obtener_todas(filtro)` | Delega a Database con filtro opcional. |
| `obtener(id)` | Obtiene tarea por ID. |
| `actualizar(id, **kwargs)` | Valida fecha si se modifica. Registra historial. |
| `eliminar(id)` | Registra historial antes de eliminar. |
| `completar(id)` | Marca como completada. Registra historial. |
| `detectar_vencidas()` | Marca pendientes con fecha pasada. Retorna cantidad. |
| `obtener_estadisticas()` | Estadísticas generales. |
| `_validar_fecha(str)` | Privado. Valida formato YYYY-MM-DD. |

#### `CategoriaService`

| Método | Descripción |
|---|---|
| `crear(nombre, desc)` | Valida nombre no vacío. Crea categoría. |
| `obtener_todas()` | Lista todas las categorías. |
| `actualizar(id, ...)` | Actualiza nombre y/o descripción. |
| `eliminar(id)` | Elimina con validación de integridad. |
| `puede_eliminar(id)` | Verifica si tiene tareas asignadas. |
| `contar()` | Número total de categorías. |

#### `EtiquetaService`

| Método | Descripción |
|---|---|
| `crear(nombre, color)` | Valida nombre. Crea etiqueta. |
| `obtener_todas()` | Lista todas las etiquetas. |
| `eliminar(id)` | Elimina etiqueta por ID. |

---

### 3.4 `src/main.py` — Ventana Principal (Vista)

Clase `SmartTaskApp` basada en `tkinter.Tk`. Es el punto de entrada visual de la aplicación.

**Responsabilidades:**
- Crea y muestra la ventana principal con tema Nord
- Barra superior: botones Gráficos, Voz, Nueva Tarea, ⚙️ Categorías
- Panel de filtros dinámicos (RadioButtons por categoría)
- Tabla central (`ttk.Treeview`) con tareas y colores por estado
- Barra de estadísticas en tiempo real
- Maneja atajos de teclado (Ctrl+Z para deshacer)
- Coordina con `TareaService` y `CategoriaService` vía inyección de dependencias

---

### 3.5 `src/dialogos.py` — Diálogos de la Interfaz

Contiene los diálogos modales para operaciones CRUD:

| Diálogo | Descripción |
|---|---|
| `DialogoNuevaTarea` | Formulario completo para crear tarea con validación de campos |
| `DialogoEditarTarea` | Formulario prellenado para editar tarea existente |
| `DialogoEliminarTarea` | Confirmación en 3 pasos para eliminar |
| `DialogoCategorias` | CRUD completo de categorías con Treeview |
| `DialogoGraficos` | Gráficos estadísticos con matplotlib integrado en Tkinter |

---

### 3.6 `src/voice.py` — Módulo de Voz

Gestiona las funcionalidades de entrada y salida de voz:

| Componente | Descripción |
|---|---|
| Reconocimiento de voz | Usa `SpeechRecognition` + `sounddevice` + Google Speech API |
| Síntesis de voz | Usa `pyttsx3` (offline) para confirmaciones verbales |
| Parser inteligente | Extrae título, fecha, prioridad y categoría del texto dictado |

**Palabras clave del parser:**
- `detalle` → descripción
- `fecha` → fecha límite (convierte "quince diciembre" → `2026-12-15`)
- `prioridad` → prioridad (alta/media/baja)
- `categoría` → categoría
- `terminar` → señal de fin del dictado

---

### 3.7 `src/undo_manager.py` — Gestión de Deshacer

Implementa el patrón **Memento/Pila LIFO** para la funcionalidad Ctrl+Z.

| Componente | Descripción |
|---|---|
| `UndoManager` | Pila de acciones reversibles |
| `push(accion)` | Agrega acción reversible a la pila |
| `undo()` | Extrae y ejecuta la última acción inversa |
| `can_undo()` | Verifica si hay acciones para deshacer |

---

### 3.8 `run.py` — Punto de Entrada

Script principal que inicializa la base de datos, crea los servicios y lanza la aplicación Tkinter.

```
run.py
└── Database("smarttask.db")       # Inicializa BD SQLite
    └── TareaService(db)           # Servicio de tareas
    └── CategoriaService(db)       # Servicio de categorías
        └── SmartTaskApp(servicios) # Lanza ventana principal
```

---

## 4. Instrucciones de Mantenimiento y Extensión

### 4.1 Requisitos del entorno

| Herramienta | Versión mínima |
|---|---|
| Python | 3.8+ |
| pip | Incluido con Python |
| Sistema Operativo | Windows 10/11 |

### 4.2 Configuración del entorno

```bash
# 1. Clonar el repositorio
git clone <URL_REPOSITORIO>
cd smarttask-organizer4-main

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno virtual (Windows)
.venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar la aplicación
python run.py
```

### 4.3 Ejecutar los tests

```bash
# Activar entorno virtual primero
.venv\Scripts\activate

# Todos los tests
pytest tests/ -v

# Con reporte de cobertura
pytest tests/ -v --cov=src --cov-report=term-missing

# Un módulo específico
pytest tests/test_models.py -v
pytest tests/test_database.py -v
pytest tests/test_services.py -v
pytest tests/test_acceptance.py -v
```

### 4.4 Agregar una nueva funcionalidad

Para extender el sistema con una nueva funcionalidad (siguiendo el patrón existente):

**Paso 1 — Modelo** (si se necesita nueva tabla):
```python
# En src/models.py
class NuevoModelo(Base):
    __tablename__ = 'nueva_tabla'
    id = Column(Integer, primary_key=True)
    # ... campos
```

**Paso 2 — Database** (operaciones CRUD):
```python
# En src/database.py, dentro de la clase Database
def crear_nuevo(self, dato):
    """Docstring explicando la operación."""
    session = self._get_session()
    try:
        obj = NuevoModelo(dato=dato)
        session.add(obj)
        session.commit()
        return obj.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```

**Paso 3 — Service** (lógica de negocio):
```python
# En src/services.py, nueva clase de servicio
class NuevoService:
    def __init__(self, db):
        self.db = db

    def crear(self, dato):
        if not dato:
            raise ValueError("El dato es obligatorio")
        return self.db.crear_nuevo(dato)
```

**Paso 4 — Vista** (si es necesaria interfaz):
- Agregar botón en `main.py` o nuevo diálogo en `dialogos.py`
- Conectar el botón al servicio correspondiente

**Paso 5 — Tests**:
```python
# En tests/test_nuevo.py
class TestNuevoService:
    def test_crear_exitoso(self, db_vacia):
        svc = NuevoService(db_vacia)
        resultado = svc.crear("dato válido")
        assert resultado is not None

    def test_crear_vacio_falla(self, db_vacia):
        svc = NuevoService(db_vacia)
        with pytest.raises(ValueError):
            svc.crear("")
```

### 4.5 Agregar nueva categoría por defecto

Las categorías por defecto se definen en `src/database.py`, método `_init_db()`:

```python
categorias_default = [
    ('Trabajo', 'Tareas relacionadas con el trabajo'),
    ('Personal', 'Tareas personales'),
    # Agregar aquí nuevas categorías:
    ('NuevaCategoria', 'Descripción de la nueva categoría'),
]
```

> **Nota:** Solo se insertan si no existen ya en la base de datos. No hay riesgo de duplicados.

### 4.6 Modificar los colores del tema Nord

Los colores están definidos como constantes al inicio de `src/main.py`:

```python
# Tema Nord — modificar aquí para cambiar la paleta global
NORD = {
    'bg': '#2E3440',       # Fondo principal
    'fg': '#D8DEE9',       # Texto principal
    'accent': '#88C0D0',   # Acento azul
    'verde': '#A3BE8C',    # Tareas completadas
    'rojo': '#BF616A',     # Tareas vencidas
    'amarillo': '#EBCB8B', # Alta prioridad
    ...
}
```

### 4.7 Gestión de la base de datos

La base de datos `smarttask.db` se crea automáticamente al ejecutar `run.py`.

- **Resetear la BD:** Borrar el archivo `smarttask.db` y ejecutar `python run.py`. Se recreará con datos por defecto.
- **Backup:** Copiar el archivo `smarttask.db` a otra ubicación.
- **Inspección manual:** Abrirlo con [DB Browser for SQLite](https://sqlitebrowser.org/).

### 4.8 Estructura de archivos relevante para mantenimiento

```
smarttask-organizer4-main/
├── run.py                  ← Punto de entrada. Modificar para cambiar configuración inicial
├── requirements.txt        ← Agregar nuevas dependencias aquí
├── pytest.ini              ← Configuración de pytest (cobertura, paths)
│
├── src/
│   ├── models.py           ← Agregar nuevas entidades/tablas aquí
│   ├── database.py         ← Agregar nuevas operaciones CRUD aquí
│   ├── services.py         ← Agregar nueva lógica de negocio aquí
│   ├── main.py             ← Modificar interfaz principal aquí
│   ├── dialogos.py         ← Agregar nuevos diálogos aquí
│   ├── voice.py            ← Modificar reconocimiento/síntesis de voz aquí
│   └── undo_manager.py     ← Agregar nuevas acciones deshacer aquí
│
└── tests/
    ├── conftest.py         ← Agregar nuevos fixtures de testing aquí
    ├── test_models.py      ← Tests de modelos ORM
    ├── test_database.py    ← Tests de operaciones CRUD
    ├── test_services.py    ← Tests de lógica de negocio
    ├── test_undo_manager.py← Tests del gestor de deshacer
    └── test_acceptance.py  ← Tests de aceptación (flujos de usuario)
```
