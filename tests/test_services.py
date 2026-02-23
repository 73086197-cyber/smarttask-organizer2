"""
Pruebas unitarias para la capa de servicios (Business Logic).

Verifica la lógica de negocio implementada en TareaService,
CategoriaService y EtiquetaService, incluyendo validaciones,
registro de historial y manejo de errores.

Framework: pytest
Cobertura: src/services.py
"""
import pytest
from src.services import TareaService, CategoriaService, EtiquetaService


class TestTareaServiceCrear:
    """Tests de creación de tareas vía servicio."""

    def test_crear_tarea_exitosa(self, servicio_tareas):
        """Verifica creación exitosa con datos válidos."""
        svc, db = servicio_tareas
        tarea_id = svc.crear(
            titulo="Servicio test",
            descripcion="Desc",
            fecha_limite="2026-06-15",
            prioridad="alta"
        )
        assert tarea_id is not None
        assert isinstance(tarea_id, int)

    def test_crear_sin_titulo_falla(self, servicio_tareas):
        """Verifica que título vacío lanza ValueError."""
        svc, _ = servicio_tareas
        with pytest.raises(ValueError, match="obligatorio"):
            svc.crear(titulo="")

    def test_crear_titulo_vacio_falla(self, servicio_tareas):
        """Verifica que título solo espacios lanza ValueError."""
        svc, _ = servicio_tareas
        with pytest.raises(ValueError, match="obligatorio"):
            svc.crear(titulo="   ")

    def test_crear_fecha_invalida_falla(self, servicio_tareas):
        """Verifica que fecha con formato incorrecto lanza ValueError."""
        svc, _ = servicio_tareas
        with pytest.raises(ValueError, match="Formato de fecha"):
            svc.crear(titulo="Test", fecha_limite="31-12-2026")

    def test_crear_fecha_correcta(self, servicio_tareas):
        """Verifica que fecha YYYY-MM-DD es aceptada."""
        svc, _ = servicio_tareas
        tarea_id = svc.crear(titulo="Fecha ok", fecha_limite="2026-12-31")
        assert tarea_id is not None

    def test_crear_registra_historial(self, servicio_tareas):
        """Verifica que al crear se registra en el historial."""
        svc, db = servicio_tareas
        svc.crear(titulo="Con historial")
        historial = db.obtener_historial()
        acciones = [h['tipo_accion'] for h in historial]
        assert "CREAR" in acciones


class TestTareaServiceActualizar:
    """Tests de actualización de tareas vía servicio."""

    def test_actualizar_exitosa(self, servicio_tareas):
        """Verifica actualización exitosa del título."""
        svc, db = servicio_tareas
        tareas = db.obtener_todas_tareas()
        if tareas:
            tarea_id = tareas[0]['id']
            resultado = svc.actualizar(tarea_id, titulo="Actualizado")
            assert resultado is True

    def test_actualizar_fecha_invalida(self, servicio_tareas):
        """Verifica que actualizar con fecha inválida falla."""
        svc, db = servicio_tareas
        tareas = db.obtener_todas_tareas()
        if tareas:
            with pytest.raises(ValueError, match="Formato de fecha"):
                svc.actualizar(
                    tareas[0]['id'], fecha_limite="invalida"
                )


class TestTareaServiceEliminar:
    """Tests de eliminación de tareas vía servicio."""

    def test_eliminar_exitosa(self, servicio_tareas):
        """Verifica eliminación exitosa."""
        svc, db = servicio_tareas
        tarea_id = svc.crear(titulo="Para borrar")
        resultado = svc.eliminar(tarea_id)
        assert resultado is True

    def test_eliminar_registra_historial(self, servicio_tareas):
        """Verifica que al eliminar se registra en el historial."""
        svc, db = servicio_tareas
        tarea_id = svc.crear(titulo="Historial eliminar")
        svc.eliminar(tarea_id)
        historial = db.obtener_historial()
        acciones = [h['tipo_accion'] for h in historial]
        assert "ELIMINAR" in acciones


class TestTareaServiceCompletar:
    """Tests para marcar tareas como completadas."""

    def test_completar_exitosa(self, servicio_tareas):
        """Verifica que completar cambia el estado."""
        svc, db = servicio_tareas
        tarea_id = svc.crear(titulo="Para completar")
        resultado = svc.completar(tarea_id)
        assert resultado is True
        tarea = db.obtener_tarea(tarea_id)
        assert tarea['estado'] == "completada"

    def test_completar_registra_historial(self, servicio_tareas):
        """Verifica que al completar se registra en el historial."""
        svc, db = servicio_tareas
        tarea_id = svc.crear(titulo="Completar historial")
        svc.completar(tarea_id)
        historial = db.obtener_historial()
        acciones = [h['tipo_accion'] for h in historial]
        assert "COMPLETAR" in acciones


class TestTareaServiceListar:
    """Tests para listar y obtener tareas."""

    def test_listar_todas(self, servicio_tareas):
        """Verifica la obtención de todas las tareas."""
        svc, _ = servicio_tareas
        tareas = svc.obtener_todas()
        assert isinstance(tareas, list)

    def test_listar_con_filtro(self, servicio_tareas):
        """Verifica el filtrado por categoría."""
        svc, _ = servicio_tareas
        tareas = svc.obtener_todas(filtro_categoria="Trabajo")
        # Pueden ser 0 si no hay tareas en esa categoría
        assert isinstance(tareas, list)

    def test_obtener_por_id(self, servicio_tareas):
        """Verifica obtener una tarea por ID."""
        svc, _ = servicio_tareas
        tarea_id = svc.crear(titulo="Obtener test")
        tarea = svc.obtener(tarea_id)
        assert tarea is not None
        assert tarea['titulo'] == "Obtener test"


class TestCategoriaService:
    """Tests para el servicio de categorías."""

    def test_crear_categoria(self, servicio_categorias):
        """Verifica creación exitosa de categoría."""
        svc, _ = servicio_categorias
        cat_id = svc.crear("CatService", "Desc service")
        assert cat_id is not None

    def test_crear_duplicada_falla(self, servicio_categorias):
        """Verifica que duplicadas lanzan error."""
        svc, _ = servicio_categorias
        svc.crear("UniService", "")
        with pytest.raises((ValueError, Exception)):
            svc.crear("UniService", "")

    def test_crear_nombre_vacio_falla(self, servicio_categorias):
        """Verifica que nombre vacío lanza ValueError."""
        svc, _ = servicio_categorias
        with pytest.raises(ValueError, match="obligatorio"):
            svc.crear("", "")

    def test_eliminar_categoria(self, servicio_categorias):
        """Verifica eliminación exitosa."""
        svc, _ = servicio_categorias
        cat_id = svc.crear("Borrable", "")
        resultado = svc.eliminar(cat_id)
        assert resultado is True

    def test_listar_categorias(self, servicio_categorias):
        """Verifica que se listan las categorías."""
        svc, _ = servicio_categorias
        cats = svc.obtener_todas()
        assert isinstance(cats, list)
        assert len(cats) >= 1


class TestEtiquetaService:
    """Tests para el servicio de etiquetas."""

    def test_crear_etiqueta(self, servicio_etiquetas):
        """Verifica creación exitosa de etiqueta."""
        svc, _ = servicio_etiquetas
        etiq_id = svc.crear("TagService")
        assert etiq_id is not None

    def test_crear_nombre_vacio_falla(self, servicio_etiquetas):
        """Verifica que nombre vacío lanza ValueError."""
        svc, _ = servicio_etiquetas
        with pytest.raises(ValueError, match="obligatorio"):
            svc.crear("")

    def test_listar_etiquetas(self, servicio_etiquetas):
        """Verifica que se listan las etiquetas."""
        svc, _ = servicio_etiquetas
        svc.crear("Listar1")
        svc.crear("Listar2")
        etiquetas = svc.obtener_todas()
        assert len(etiquetas) >= 2

    def test_eliminar_etiqueta(self, servicio_etiquetas):
        """Verifica eliminación exitosa de etiqueta."""
        svc, _ = servicio_etiquetas
        etiq_id = svc.crear("Temporal")
        resultado = svc.eliminar(etiq_id)
        assert resultado is True


class TestValidacionFechaService:
    """Tests específicos para la validación de fechas."""

    def test_fecha_valida(self, servicio_tareas):
        """Verifica que el formato YYYY-MM-DD es aceptado."""
        svc, _ = servicio_tareas
        tarea_id = svc.crear(titulo="F ok", fecha_limite="2026-03-15")
        assert tarea_id is not None

    def test_fecha_formato_dd_mm_yyyy_falla(self, servicio_tareas):
        """Verifica que DD/MM/YYYY no es aceptado."""
        svc, _ = servicio_tareas
        with pytest.raises(ValueError, match="Formato de fecha"):
            svc.crear(titulo="F mal", fecha_limite="15/03/2026")

    def test_fecha_texto_falla(self, servicio_tareas):
        """Verifica que texto libre no es aceptado como fecha."""
        svc, _ = servicio_tareas
        with pytest.raises(ValueError, match="Formato de fecha"):
            svc.crear(titulo="F texto", fecha_limite="mañana")

    def test_fecha_none_es_valida(self, servicio_tareas):
        """Verifica que no pasar fecha es válido."""
        svc, _ = servicio_tareas
        tarea_id = svc.crear(titulo="Sin fecha")
        assert tarea_id is not None


class TestTareaServiceVencidas:
    """Tests para detección de tareas vencidas via servicio."""

    def test_detectar_vencidas(self, servicio_tareas):
        """Verifica que detectar_vencidas marca tareas pasadas."""
        svc, db = servicio_tareas
        svc.crear(titulo="Vieja", fecha_limite="2020-01-01")
        cantidad = svc.detectar_vencidas()
        assert cantidad >= 1

    def test_detectar_sin_vencidas(self, servicio_tareas):
        """Verifica que no marca tareas futuras."""
        svc, db = servicio_tareas
        # Eliminar tareas existentes para empezar limpio
        for t in db.obtener_todas_tareas():
            db.eliminar_tarea(t['id'])
        svc.crear(titulo="Futura", fecha_limite="2030-12-31")
        cantidad = svc.detectar_vencidas()
        assert cantidad == 0

    def test_obtener_estadisticas(self, servicio_tareas):
        """Verifica que obtener_estadisticas retorna dict."""
        svc, _ = servicio_tareas
        stats = svc.obtener_estadisticas()
        assert 'total' in stats
        assert 'completadas' in stats
        assert 'pendientes' in stats
        assert 'vencidas' in stats


class TestCategoriaServiceExtras:
    """Tests adicionales para CategoriaService."""

    def test_puede_eliminar_sin_tareas(self, servicio_categorias):
        """Verifica puede_eliminar cuando no hay tareas."""
        svc, db = servicio_categorias
        cat_id = svc.crear("Eliminable", "")
        resultado = svc.puede_eliminar(cat_id)
        assert resultado is True

    def test_contar_categorias(self, servicio_categorias):
        """Verifica conteo dinámico de categorías."""
        svc, _ = servicio_categorias
        antes = svc.contar()
        svc.crear("Extra", "")
        despues = svc.contar()
        assert despues == antes + 1

    def test_actualizar_nombre_y_descripcion(self, servicio_categorias):
        """Verifica actualización de nombre y descripción."""
        svc, _ = servicio_categorias
        cat_id = svc.crear("Original", "Desc original")
        resultado = svc.actualizar(
            cat_id, nombre="Renombrada", descripcion="Nueva desc"
        )
        assert resultado is True

    def test_actualizar_solo_descripcion(self, servicio_categorias):
        """Verifica actualización solo de descripción."""
        svc, _ = servicio_categorias
        cat_id = svc.crear("NoRenombrar", "")
        resultado = svc.actualizar(cat_id, descripcion="Actualizada")
        assert resultado is True
