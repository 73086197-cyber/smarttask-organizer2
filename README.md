# 🚀 SmartTask Organizer

Sistema de gestión de tareas de escritorio con reconocimiento de voz, categorías dinámicas, fechas límite, gráficos estadísticos y base de datos SQLAlchemy ORM.

Desarrollado como proyecto de fin de curso para la materia de **Construcción de Software**.

---

## 📋 Historias de Usuario Implementadas

| HU   | Nombre                | Descripción                                                    |
|------|-----------------------|----------------------------------------------------------------|
| HU01 | Crear tarea           | Formulario completo con validación de campos                   |
| HU02 | Listar tareas         | Vista en tabla con ordenamiento por estado y prioridad         |
| HU03 | Editar tarea          | Modificación de todos los campos de una tarea existente        |
| HU04 | Eliminar tarea        | Diálogo de confirmación paso a paso (3 pasos)                  |
| HU05 | Completar tarea       | Marcar tareas como completadas con un clic                     |
| HU06 | Fecha límite          | Validación de formato YYYY-MM-DD y restricción de fechas       |
| HU07 | Detectar vencidas     | Detección automática de tareas con fecha límite pasada         |
| HU08 | Crear categoría       | Categorías dinámicas con CRUD completo                         |
| HU09 | Asignar categoría     | Selección de categoría en formularios de creación/edición      |
| HU10 | Filtrar por categoría | RadioButtons dinámicos según categorías existentes             |
| HU11 | Tarea por voz         | Dictado por micrófono con parseo inteligente de datos          |
| HU12 | Notificaciones        | Alertas de Windows para tareas vencidas y del día              |

**Funcionalidades adicionales:**
- 📊 Gráficos estadísticos con matplotlib (tema Nord)
- 📄 Exportación a CSV compatible con Excel
- ↩️ Deshacer acciones con Ctrl+Z (patrón Pila LIFO)
- 🎨 Tema visual Nord con colores personalizados
- ⚙️ Gestión dinámica de categorías (agregar, eliminar)
- 🏷️ Sistema de etiquetas (modelo N:M)
- 📜 Historial completo de acciones

---

## 🏗️ Arquitectura del Proyecto

El proyecto sigue el patrón **MVC (Modelo-Vista-Controlador)** con una capa de servicios:

```
┌─────────────────────────────────────────────┐
│  Vista (main.py, dialogos.py)               │
│  Tkinter + ttk — Interfaz gráfica          │
├─────────────────────────────────────────────┤
│  Servicios (services.py)                    │
│  Lógica de negocio — Validaciones           │
├─────────────────────────────────────────────┤
│  Datos (database.py)                        │
│  SQLAlchemy ORM — CRUD                      │
├─────────────────────────────────────────────┤
│  Modelos (models.py)                        │
│  SQLAlchemy DeclarativeBase — Entidades     │
└─────────────────────────────────────────────┘
```

### Entidades del dominio

| Entidad          | Descripción                           | Relaciones                      |
|------------------|---------------------------------------|---------------------------------|
| `Categoria`      | Clasificación de tareas               | 1:N con Tarea                   |
| `Tarea`          | Unidad de trabajo principal           | N:1 Categoria, N:M Etiqueta    |
| `Etiqueta`       | Tags para clasificación adicional     | N:M con Tarea                   |
| `HistorialAccion`| Registro auditable de operaciones     | Independiente                   |

---

## 🛠️ Tecnologías Utilizadas

| Tecnología         | Versión    | Uso                                           |
|--------------------|------------|-----------------------------------------------|
| Python             | 3.8+       | Lenguaje principal                             |
| Tkinter + ttk      | (incluido) | Interfaz gráfica de escritorio                 |
| **SQLAlchemy**     | ≥2.0.0     | ORM para persistencia con SQLite               |
| SpeechRecognition  | ≥3.10.0    | Reconocimiento de voz (Google Speech API)      |
| pyttsx3            | ≥2.90      | Síntesis de voz offline (texto a voz)          |
| sounddevice        | ≥0.4.6     | Grabación de audio del micrófono               |
| numpy              | ≥1.21.0    | Procesamiento de arrays de audio               |
| scipy              | ≥1.7.0     | Escritura de archivos WAV temporales           |
| matplotlib         | ≥3.3.0     | Gráficos estadísticos                          |
| plyer              | ≥2.1.0     | Notificaciones nativas de Windows              |
| **pytest**         | ≥7.0.0     | Framework de testing                           |
| **pytest-cov**     | ≥4.0.0     | Cobertura de pruebas                           |

---

## 📦 Requisitos Previos

- **Sistema Operativo:** Windows 10/11
- **Python:** 3.8 o superior ([Descargar Python](https://www.python.org/downloads/))
  - ⚠️ Marcar la casilla **"Add Python to PATH"** al instalar
- **Micrófono** (opcional, solo para funcionalidad de voz)
- **Conexión a internet** (solo para reconocimiento de voz con Google)

---

## 🚀 Instalación Paso a Paso

### Opción 1: Instalación automática (Recomendado)

```bash
# 1. Clonar o descargar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd smarttask-organizer5

# 2. Ejecutar el instalador automático (doble clic o desde terminal)
setup.bat
```

### Opción 2: Instalación manual

```bash
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno virtual
.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
python run.py
```

---

## ▶️ Uso

### Ejecutar la aplicación

```bash
.venv\Scripts\activate
python run.py
```

### Interfaz principal

La ventana principal contiene:
- **Barra superior:** Botones Gráficos, Voz, Nueva Tarea y ⚙️ Categorías
- **Panel de filtros:** RadioButtons dinámicos según categorías existentes
- **Tabla central:** Lista de tareas con columnas ID, Título, Descripción, Fecha, Estado, Prioridad, Categoría
- **Leyenda de colores:** Verde (completada), Rojo (vencida), Amarillo (alta), Cyan (media)
- **Barra inferior:** Estadísticas en tiempo real

### Crear una tarea

1. Clic en **"+ NUEVA TAREA"**
2. Completar: Título (obligatorio), Descripción, Fecha Límite (YYYY-MM-DD), Prioridad y Categoría
3. Clic en **"GUARDAR"**

### Gestionar categorías (CRUD Dinámico)

1. Clic en **"⚙️ CATEGORÍAS"** en la barra superior
2. Se abre el diálogo de gestión con la tabla de categorías existentes
3. **Agregar:**
   - Escribir el nombre y descripción en los campos del formulario
   - Clic en el botón verde **"✅ AGREGAR CATEGORÍA"**
   - La categoría aparece en la tabla inmediatamente
4. **Eliminar:**
   - Seleccionar una categoría en la tabla
   - Clic en **"🗑️ ELIMINAR CATEGORÍA SELECCIONADA"**
   - ⚠️ No permite eliminar categorías con tareas asignadas (integridad referencial)
5. Al cerrar, los filtros de la ventana principal se actualizan dinámicamente

### Crear tarea por voz (HU11)

1. Clic en **"🎤 DICTAR TAREA COMPLETA"** dentro del formulario de nueva tarea
2. Hablar claramente. Ejemplo:
   > "Reunión equipo **detalle** preparar presentación **fecha** quince diciembre **prioridad** alta **categoría** trabajo **terminar**"
3. Los campos se rellenan automáticamente

### Editar / Eliminar / Completar

- **Editar:** Seleccionar tarea → clic en "✏️ EDITAR"
- **Eliminar:** Seleccionar tarea → clic en "🗑️ ELIMINAR" → Confirmación en 3 pasos
- **Completar:** Seleccionar tarea → clic en "✅ COMPLETAR"
- **Deshacer:** Presionar **Ctrl+Z** para revertir la última acción

---

## 📁 Estructura del Proyecto

```
smarttask-organizer5/
├── run.py                  # Punto de entrada principal
├── requirements.txt        # Dependencias del proyecto
├── setup.bat               # Instalador automático
├── pytest.ini              # Configuración de pytest
├── .gitignore              # Archivos excluidos de Git
├── README.md               # Este archivo
│
├── src/                    # Código fuente principal
│   ├── __init__.py
│   ├── main.py             # Ventana principal (SmartTaskApp)
│   ├── models.py           # Modelos SQLAlchemy ORM (4 entidades)
│   ├── database.py         # Capa de datos SQLAlchemy (CRUD)
│   ├── services.py         # Capa de servicios (lógica de negocio)
│   ├── dialogos.py         # Diálogos de creación, edición, eliminación y categorías
│   ├── voice.py            # Reconocimiento y síntesis de voz
│   └── undo_manager.py     # Gestor de deshacer (Pila LIFO)
│
├── tests/                  # Pruebas unitarias (122 tests)
│   ├── __init__.py
│   ├── conftest.py         # Fixtures reutilizables (SQLAlchemy en memoria)
│   ├── test_models.py      # Tests modelos ORM (~30 tests)
│   ├── test_database.py    # Tests CRUD (~50 tests)
│   ├── test_services.py    # Tests lógica de negocio (~35 tests)
│   └── test_undo_manager.py # Tests deshacer (~11 tests)
│
├── DOC/                    # Documentación adicional
│   └── Proyecto de Fin de Curso.docx.pdf
│
└── smarttask.db            # Base de datos SQLite (se genera automáticamente)
```

---

## 🧪 Ejecutar Pruebas Unitarias

```bash
# Activar entorno virtual
.venv\Scripts\activate

# Ejecutar todos los tests (122 tests)
pytest tests/ -v

# Ejecutar con reporte de cobertura
pytest tests/ -v --cov=src --cov-report=term-missing

# Ejecutar solo tests de un módulo
pytest tests/test_models.py -v
pytest tests/test_database.py -v
pytest tests/test_services.py -v
```

### Cobertura por módulo (backend testable)

| Módulo           | Cobertura | Tests |
|------------------|-----------|-------|
| `models.py`      | 100%      | 30    |
| `services.py`    | 98%       | 35    |
| `database.py`    | 88%       | 50    |
| `undo_manager.py`| 73%       | 11    |

> **Nota:** `main.py`, `dialogos.py` y `voice.py` son módulos de interfaz gráfica (Tkinter) y hardware (micrófono) que requieren interacción humana y no son unitariamente testeables.

---

## � Integrantes del Equipo

| # | Nombre completo |
|---|---|
| 1 | **Dickmar Wilber Julca Laureano** |
| 2 | **Italo Eduardo Reyes Cordero** |
| 3 | **Jack Joshua Bendezu Lagos** |
| 4 | **Simon Ronaldo Gonzales Jacinto** |

Proyecto de Fin de Curso — Materia: **Construcción de Software** — Año: 2026