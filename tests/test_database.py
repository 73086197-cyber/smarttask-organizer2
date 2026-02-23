"""
Pruebas unitarias para la capa de acceso a datos (Database).

Verifica las operaciones CRUD sobre tareas, categorías, etiquetas
e historial usando una BD SQLite en memoria via SQLAlchemy.

Framework: pytest
Cobertura: src/database.py
"""
import pytest
from src.database import Database, DictRow


class TestDictRow:
    """Tests para la clase DictRow (compatibilidad sqlite3.Row)."""

    def test_acceso_por_clave(self):
        """Verifica acceso por nombre de columna con []."""
        row = DictRow({'id': 1, 'nombre': 'Test'})
        assert row['id'] == 1
        assert row['nombre'] == 'Test'

    def test_acceso_get(self):
        """Verifica el método get con y sin valor por defecto."""
        row = DictRow({'id': 1})
        assert row.get('id') == 1
        assert row.get('nope', 'default') == 'default'

    def test_keys(self):
        """Verifica que keys devuelve las claves del diccionario."""
        row = DictRow({'a': 1, 'b': 2})
        assert set(row.keys()) == {'a', 'b'}

    def test_items(self):
        """Verifica items para iteración."""
        row = DictRow({'x': 10})
        items_list = list(row.items())
        assert ('x', 10) in items_list

    def test_repr(self):
        """Verifica representación legible de DictRow."""
        row = DictRow({'id': 5})
        assert 'id' in repr(row)


class TestCrearTarea:
    """Tests para la creación de tareas."""

    def test_crear_tarea_basica(self, db_vacia):
        """Verifica la creación de una tarea con datos mínimos."""
        tarea_id = db_vacia.crear_tarea(titulo="Tarea básica")
        assert tarea_id is not None
        assert isinstance(tarea_id, int)

    def test_crear_tarea_completa(self, db_vacia):
        """Verifica la creación con todos los campos."""
        cats = db_vacia.obtener_categorias()
        cat_id = cats[0]['id']

        tarea_id = db_vacia.crear_tarea(
            titulo="Completa",
            descripcion="Desc",
            fecha_limite="2026-12-31",
            prioridad="alta",
            categoria_id=cat_id
        )
        tareas = db_vacia.obtener_todas_tareas()
        tarea = next(t for t in tareas if t['id'] == tarea_id)
        assert tarea['titulo'] == "Completa"
        assert tarea['prioridad'] == "alta"
        assert tarea['fecha_limite'] == "2026-12-31"

    def test_crear_sin_titulo_falla(self, db_vacia):
        """Verifica que crear sin título lanza error."""
        with pytest.raises((ValueError, Exception)):
            db_vacia.crear_tarea(titulo="")


class TestObtenerTareas:
    """Tests de consulta de tareas."""

    def test_obtener_todas(self, db_limpia):
        """Verifica que obtener_todas_tareas devuelve lista no vacía."""
        tareas = db_limpia.obtener_todas_tareas()
        assert isinstance(tareas, list)
        assert len(tareas) > 0

    def test_filtrar_por_categoria(self, tarea_ejemplo):
        """Verifica filtrado por nombre de categoría."""
        db, _ = tarea_ejemplo
        tareas = db.obtener_todas_tareas("Trabajo")
        assert all(t['categoria_nombre'] == "Trabajo" for t in tareas)

    def test_filtrar_categoria_inexistente(self, db_limpia):
        """Verifica que filtrar por categoría inexistente devuelve vacío."""
        tareas = db_limpia.obtener_todas_tareas("NoExiste")
        assert tareas == []

    def test_obtener_tarea_por_id(self, tarea_ejemplo):
        """Verifica obtener una tarea específica por su ID."""
        db, tarea_id = tarea_ejemplo
        tarea = db.obtener_tarea(tarea_id)
        assert tarea is not None
        assert tarea['id'] == tarea_id
        assert tarea['titulo'] == "Tarea de prueba"

    def test_obtener_tarea_inexistente(self, db_vacia):
        """Verifica que obtener una tarea inexistente retorna None."""
        tarea = db_vacia.obtener_tarea(99999)
        assert tarea is None


class TestActualizarTarea:
    """Tests de actualización de tareas."""

    def test_actualizar_titulo(self, tarea_ejemplo):
        """Verifica actualización del título."""
        db, tarea_id = tarea_ejemplo
        resultado = db.actualizar_tarea(tarea_id, titulo="Nuevo título")
        assert resultado is True
        tarea = db.obtener_tarea(tarea_id)
        assert tarea['titulo'] == "Nuevo título"

    def test_actualizar_estado(self, tarea_ejemplo):
        """Verifica el cambio de estado."""
        db, tarea_id = tarea_ejemplo
        resultado = db.actualizar_tarea(tarea_id, estado="completada")
        assert resultado is True
        tarea = db.obtener_tarea(tarea_id)
        assert tarea['estado'] == "completada"

    def test_actualizar_inexistente(self, db_vacia):
        """Verifica que actualizar tarea inexistente retorna False."""
        resultado = db_vacia.actualizar_tarea(99999, titulo="Nada")
        assert resultado is False


class TestEliminarTarea:
    """Tests de eliminación de tareas."""

    def test_eliminar_tarea(self, tarea_ejemplo):
        """Verifica la eliminación exitosa."""
        db, tarea_id = tarea_ejemplo
        resultado = db.eliminar_tarea(tarea_id)
        assert resultado is True
        assert db.obtener_tarea(tarea_id) is None

    def test_eliminar_inexistente(self, db_vacia):
        """Verifica que eliminar tarea inexistente retorna False."""
        resultado = db_vacia.eliminar_tarea(99999)
        assert resultado is False


class TestCategorias:
    """Tests para CRUD de categorías."""

    def test_obtener_categorias(self, db_limpia):
        """Verifica que hay categorías por defecto."""
        cats = db_limpia.obtener_categorias()
        assert len(cats) >= 1
        assert all('nombre' in c for c in cats)

    def test_crear_categoria(self, db_vacia):
        """Verifica la creación de una nueva categoría."""
        cat_id = db_vacia.crear_categoria("NuevaCategoria", "Descripción")
        assert cat_id is not None
        cats = db_vacia.obtener_categorias()
        nombres = [c['nombre'] for c in cats]
        assert "NuevaCategoria" in nombres

    def test_crear_categoria_duplicada_falla(self, db_vacia):
        """Verifica que no se pueden crear categorías duplicadas."""
        db_vacia.crear_categoria("Unica", "")
        with pytest.raises((ValueError, Exception)):
            db_vacia.crear_categoria("Unica", "")

    def test_actualizar_categoria(self, db_vacia):
        """Verifica la actualización del nombre de categoría."""
        cat_id = db_vacia.crear_categoria("Original", "")
        resultado = db_vacia.actualizar_categoria(
            cat_id, nombre="Actualizada"
        )
        assert resultado is True

    def test_eliminar_categoria_sin_tareas(self, db_vacia):
        """Verifica eliminación de categoría sin tareas."""
        cat_id = db_vacia.crear_categoria("Borrable", "")
        resultado = db_vacia.eliminar_categoria(cat_id)
        assert resultado is True

    def test_eliminar_categoria_con_tareas_falla(self, tarea_ejemplo):
        """Verifica que no se puede eliminar categoría con tareas."""
        db, _ = tarea_ejemplo
        cats = db.obtener_categorias()
        cat_trabajo = next(c for c in cats if c['nombre'] == 'Trabajo')
        with pytest.raises(ValueError, match="tiene.*tarea"):
            db.eliminar_categoria(cat_trabajo['id'])


class TestEtiquetas:
    """Tests para CRUD de etiquetas."""

    def test_crear_etiqueta(self, db_vacia):
        """Verifica la creación de una etiqueta."""
        etiq_id = db_vacia.crear_etiqueta("Urgente")
        assert etiq_id is not None

    def test_obtener_etiquetas(self, db_vacia):
        """Verifica que se pueden obtener las etiquetas."""
        db_vacia.crear_etiqueta("Tag1")
        db_vacia.crear_etiqueta("Tag2")
        etiquetas = db_vacia.obtener_etiquetas()
        assert len(etiquetas) >= 2

    def test_eliminar_etiqueta(self, db_vacia):
        """Verifica la eliminación de una etiqueta."""
        etiq_id = db_vacia.crear_etiqueta("Temporal")
        resultado = db_vacia.eliminar_etiqueta(etiq_id)
        assert resultado is True


class TestHistorial:
    """Tests para el registro de historial de acciones."""

    def test_registrar_historial(self, db_vacia):
        """Verifica que se registra una acción en el historial."""
        db_vacia.registrar_historial("CREAR", "Tarea test", "Detalles")
        historial = db_vacia.obtener_historial()
        assert len(historial) >= 1
        assert historial[0]['tipo_accion'] == "CREAR"

    def test_obtener_historial_limitado(self, db_vacia):
        """Verifica que el historial respeta el límite."""
        for i in range(15):
            db_vacia.registrar_historial("TEST", f"Tarea {i}")
        historial = db_vacia.obtener_historial(limite=5)
        assert len(historial) == 5


class TestEstadisticas:
    """Tests de estadísticas y tareas vencidas."""

    def test_detectar_vencidas(self, db_vacia):
        """Verifica la actualización automática de tareas vencidas."""
        db_vacia.crear_tarea(
            titulo="Vencida",
            fecha_limite="2020-01-01",
            prioridad="media"
        )
        cantidad = db_vacia.actualizar_vencidas()
        assert cantidad >= 1

    def test_no_falsas_vencidas(self, db_vacia):
        """Verifica que tareas futuras no se marcan como vencidas."""
        db_vacia.crear_tarea(
            titulo="Futura",
            fecha_limite="2030-12-31",
            prioridad="media"
        )
        db_vacia.actualizar_vencidas()
        tareas = db_vacia.obtener_todas_tareas()
        futura = next(
            (t for t in tareas if t['titulo'] == "Futura"), None
        )
        assert futura is not None
        assert futura['estado'] == "pendiente"


class TestDatabase:
    """Tests generales del Database."""

    def test_init_en_memoria(self):
        """Verifica que se puede crear una BD en memoria."""
        db = Database(db_name=":memory:")
        cats = db.obtener_categorias()
        assert len(cats) >= 1
        db.close()

    def test_close(self):
        """Verifica el cierre limpio de la sesión."""
        db = Database(db_name=":memory:")
        db.close()
        # No debería lanzar error


class TestMarcarCompletada:
    """Tests para marcar_como_completada."""

    def test_marcar_completada(self, tarea_ejemplo):
        """Verifica que marcar completada cambia el estado."""
        db, tarea_id = tarea_ejemplo
        resultado = db.marcar_como_completada(tarea_id)
        assert resultado is True
        tarea = db.obtener_tarea(tarea_id)
        assert tarea['estado'] == 'completada'


class TestEstadisticasDB:
    """Tests para obtener_estadisticas del Database."""

    def test_estadisticas_basicas(self, db_vacia):
        """Verifica las estadísticas con datos variados."""
        db_vacia.crear_tarea(titulo="Pendiente", prioridad="media")
        db_vacia.crear_tarea(
            titulo="Vencida", fecha_limite="2020-01-01",
            prioridad="baja"
        )
        tarea_c = db_vacia.crear_tarea(titulo="Completar", prioridad="alta")
        db_vacia.marcar_como_completada(tarea_c)

        stats = db_vacia.obtener_estadisticas()
        assert stats['total'] == 3
        assert stats['completadas'] == 1
        assert stats['pendientes'] >= 0
        assert stats['vencidas'] >= 1

    def test_estadisticas_vacias(self, db_vacia):
        """Verifica estadísticas con BD vacía."""
        stats = db_vacia.obtener_estadisticas()
        assert stats['total'] == 0
        assert stats['completadas'] == 0


class TestActualizarTareaSinCambios:
    """Tests para edge cases de actualización."""

    def test_actualizar_sin_kwargs(self, tarea_ejemplo):
        """Verifica que actualizar sin campos retorna False."""
        db, tarea_id = tarea_ejemplo
        resultado = db.actualizar_tarea(tarea_id)
        assert resultado is False

    def test_actualizar_campo_none(self, tarea_ejemplo):
        """Verifica que pasar None no actualiza."""
        db, tarea_id = tarea_ejemplo
        resultado = db.actualizar_tarea(tarea_id, titulo=None)
        assert resultado is False


class TestEtiquetasDuplicadas:
    """Tests para validación de etiquetas duplicadas."""

    def test_crear_etiqueta_duplicada_falla(self, db_vacia):
        """Verifica que etiqueta duplicada lanza ValueError."""
        db_vacia.crear_etiqueta("MismaTag")
        with pytest.raises(ValueError, match="Ya existe"):
            db_vacia.crear_etiqueta("MismaTag")

    def test_obtener_etiquetas_vacias(self, db_vacia):
        """Verifica que sin etiquetas devuelve lista vacía."""
        etiquetas = db_vacia.obtener_etiquetas()
        assert isinstance(etiquetas, list)


class TestActualizarCategoriaEdge:
    """Tests para edge cases de categorías."""

    def test_actualizar_nombre_duplicado_falla(self, db_vacia):
        """Verifica que renombrar a nombre existente falla."""
        db_vacia.crear_categoria("CatA", "")
        cat_b = db_vacia.crear_categoria("CatB", "")
        with pytest.raises(ValueError, match="Ya existe"):
            db_vacia.actualizar_categoria(cat_b, nombre="CatA")

    def test_actualizar_cat_inexistente(self, db_vacia):
        """Verifica que actualizar cat inexistente retorna False."""
        resultado = db_vacia.actualizar_categoria(99999, nombre="Nada")
        assert resultado is False

    def test_eliminar_cat_inexistente(self, db_vacia):
        """Verifica que eliminar cat inexistente retorna False."""
        resultado = db_vacia.eliminar_categoria(99999)
        assert resultado is False

    def test_eliminar_etiqueta_inexistente(self, db_vacia):
        """Verifica que eliminar etiqueta inexistente retorna False."""
        resultado = db_vacia.eliminar_etiqueta(99999)
        assert resultado is False


class TestHistorialRegistrar:
    """Tests adicionales para registro de historial."""

    def test_registrar_sin_detalles(self, db_vacia):
        """Verifica registro de historial sin detalles."""
        db_vacia.registrar_historial("CREAR", "Tarea minima")
        historial = db_vacia.obtener_historial()
        assert len(historial) >= 1

    def test_historial_orden_reciente(self, db_vacia):
        """Verifica que el historial viene en orden reciente."""
        db_vacia.registrar_historial("ACCION1", "Primera")
        db_vacia.registrar_historial("ACCION2", "Segunda")
        historial = db_vacia.obtener_historial()
        assert historial[0]['tipo_accion'] == "ACCION2"
