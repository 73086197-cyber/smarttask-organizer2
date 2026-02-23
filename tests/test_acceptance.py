"""
Pruebas de Aceptación para SmartTask Organizer.

Estas pruebas verifican los flujos completos de usuario (end-to-end)
simulando el comportamiento real del sistema desde la perspectiva del
usuario final. Cada test representa una Historia de Usuario completa.

Las pruebas de aceptación validan que el sistema cumpla los criterios
de aceptación definidos para cada funcionalidad, coordinando múltiples
capas (servicios, base de datos, modelos) en un flujo integrado.

Framework: pytest
Cobertura: Flujos end-to-end de HU01 a HU10 + funcionalidades extra
"""
import pytest
from src.database import Database
from src.services import TareaService, CategoriaService, EtiquetaService


# ===========================================================
# FIXTURES DE ACEPTACIÓN
# ===========================================================

@pytest.fixture
def sistema():
    """Sistema completo con servicios inicializados (BD en memoria).

    Simula el entorno real de la aplicación con todos los servicios
    disponibles, tal como los tendría un usuario real al ejecutar
    run.py, pero usando una BD en memoria para isolación.

    Yields:
        dict: Diccionario con claves 'db', 'tareas', 'categorias',
              'etiquetas' listo para pruebas de aceptación.
    """
    db = Database(db_name=":memory:")
    # Limpiar tareas de ejemplo para tests predecibles
    for t in db.obtener_todas_tareas():
        db.eliminar_tarea(t['id'])

    yield {
        'db': db,
        'tareas': TareaService(db),
        'categorias': CategoriaService(db),
        'etiquetas': EtiquetaService(db),
    }
    db.close()


# ===========================================================
# HU01 + HU02: CREAR Y LISTAR TAREAS
# ===========================================================

class TestAceptacionCrearYListarTareas:
    """
    HU01 + HU02: El usuario crea una tarea y la ve en el listado.

    Criterio de aceptación:
        Dado que el usuario abre la aplicación,
        Cuando crea una tarea con título, descripción, fecha y prioridad,
        Entonces la tarea aparece en el listado con los datos correctos.
    """

    def test_flujo_crear_tarea_aparece_en_listado(self, sistema):
        """CASO FELIZ: Tarea creada aparece en el listado con datos correctos."""
        svc = sistema['tareas']

        tarea_id = svc.crear(
            titulo="Preparar presentación del proyecto",
            descripcion="Slides con arquitectura y demo",
            fecha_limite="2026-12-15",
            prioridad="alta"
        )

        tareas = svc.obtener_todas()
        ids_en_lista = [t['id'] for t in tareas]

        assert tarea_id in ids_en_lista
        tarea = svc.obtener(tarea_id)
        assert tarea['titulo'] == "Preparar presentación del proyecto"
        assert tarea['prioridad'] == "alta"
        assert tarea['estado'] == "pendiente"

    def test_flujo_listar_multiples_tareas(self, sistema):
        """CASO FELIZ: Múltiples tareas creadas aparecen todas en el listado."""
        svc = sistema['tareas']

        titulos = ["Tarea A", "Tarea B", "Tarea C"]
        for titulo in titulos:
            svc.crear(titulo=titulo, prioridad="media")

        tareas = svc.obtener_todas()
        titulos_en_lista = [t['titulo'] for t in tareas]

        for titulo in titulos:
            assert titulo in titulos_en_lista

    def test_flujo_crear_sin_titulo_rechazado(self, sistema):
        """CASO INFELIZ: El sistema rechaza crear tarea sin título."""
        svc = sistema['tareas']

        with pytest.raises(ValueError, match="obligatorio"):
            svc.crear(titulo="")

        # El listado debe seguir vacío
        assert svc.obtener_todas() == []

    def test_flujo_crear_con_fecha_invalida_rechazado(self, sistema):
        """CASO INFELIZ: Fecha con formato incorrecto es rechazada."""
        svc = sistema['tareas']

        with pytest.raises(ValueError, match="Formato de fecha"):
            svc.crear(titulo="Tarea válida", fecha_limite="25-12-2026")

        assert svc.obtener_todas() == []


# ===========================================================
# HU03: EDITAR TAREA
# ===========================================================

class TestAceptacionEditarTarea:
    """
    HU03: El usuario edita una tarea existente.

    Criterio de aceptación:
        Dado que existe una tarea en el sistema,
        Cuando el usuario modifica su título y prioridad,
        Entonces los cambios se reflejan inmediatamente en el listado.
    """

    def test_flujo_editar_titulo_y_prioridad(self, sistema):
        """CASO FELIZ: El usuario edita título y prioridad exitosamente."""
        svc = sistema['tareas']

        tarea_id = svc.crear(titulo="Título original", prioridad="baja")

        svc.actualizar(tarea_id, titulo="Título actualizado", prioridad="alta")

        tarea = svc.obtener(tarea_id)
        assert tarea['titulo'] == "Título actualizado"
        assert tarea['prioridad'] == "alta"

    def test_flujo_editar_registra_en_historial(self, sistema):
        """CASO FELIZ: La edición queda registrada en el historial del sistema."""
        svc = sistema['tareas']
        db = sistema['db']

        tarea_id = svc.crear(titulo="Para editar")
        svc.actualizar(tarea_id, titulo="Editada con historial")

        historial = db.obtener_historial()
        acciones = [h['tipo_accion'] for h in historial]
        assert "EDITAR" in acciones

    def test_flujo_editar_fecha_invalida_rechazado(self, sistema):
        """CASO INFELIZ: El sistema rechaza una fecha con formato incorrecto al editar."""
        svc = sistema['tareas']
        tarea_id = svc.crear(titulo="Original")

        with pytest.raises(ValueError, match="Formato de fecha"):
            svc.actualizar(tarea_id, fecha_limite="no-es-fecha")

        # La tarea debe quedar sin cambios
        tarea = svc.obtener(tarea_id)
        assert tarea['titulo'] == "Original"


# ===========================================================
# HU04: ELIMINAR TAREA
# ===========================================================

class TestAceptacionEliminarTarea:
    """
    HU04: El usuario elimina una tarea del sistema.

    Criterio de aceptación:
        Dado que existe una tarea en el sistema,
        Cuando el usuario confirma la eliminación,
        Entonces la tarea desaparece del listado permanentemente.
    """

    def test_flujo_eliminar_tarea_desaparece_del_listado(self, sistema):
        """CASO FELIZ: Tarea eliminada ya no aparece en el listado."""
        svc = sistema['tareas']

        tarea_id = svc.crear(titulo="Para eliminar")
        assert svc.obtener(tarea_id) is not None

        svc.eliminar(tarea_id)

        assert svc.obtener(tarea_id) is None
        ids_en_lista = [t['id'] for t in svc.obtener_todas()]
        assert tarea_id not in ids_en_lista

    def test_flujo_eliminar_registra_historial(self, sistema):
        """CASO FELIZ: La eliminación queda registrada en el historial."""
        svc = sistema['tareas']
        db = sistema['db']

        tarea_id = svc.crear(titulo="Historial eliminar")
        svc.eliminar(tarea_id)

        historial = db.obtener_historial()
        acciones = [h['tipo_accion'] for h in historial]
        assert "ELIMINAR" in acciones

    def test_flujo_eliminar_tarea_inexistente_retorna_false(self, sistema):
        """CASO INFELIZ: Intentar eliminar ID inexistente retorna False sin lanzar error."""
        svc = sistema['tareas']

        resultado = sistema['db'].eliminar_tarea(99999)
        assert resultado is False


# ===========================================================
# HU05: COMPLETAR TAREA
# ===========================================================

class TestAceptacionCompletarTarea:
    """
    HU05: El usuario marca una tarea como completada.

    Criterio de aceptación:
        Dado que existe una tarea pendiente,
        Cuando el usuario la marca como completada,
        Entonces su estado cambia a 'completada' y se registra en historial.
    """

    def test_flujo_completar_tarea_cambia_estado(self, sistema):
        """CASO FELIZ: Tarea completada cambia su estado a 'completada'."""
        svc = sistema['tareas']

        tarea_id = svc.crear(titulo="Para completar", prioridad="media")
        assert svc.obtener(tarea_id)['estado'] == "pendiente"

        svc.completar(tarea_id)

        assert svc.obtener(tarea_id)['estado'] == "completada"

    def test_flujo_completar_registra_historial(self, sistema):
        """CASO FELIZ: Completar tarea registra COMPLETAR en el historial."""
        svc = sistema['tareas']
        db = sistema['db']

        tarea_id = svc.crear(titulo="Completar historial")
        svc.completar(tarea_id)

        historial = db.obtener_historial()
        assert any(h['tipo_accion'] == "COMPLETAR" for h in historial)

    def test_flujo_completar_tarea_inexistente(self, sistema):
        """CASO INFELIZ: Completar tarea inexistente retorna False."""
        resultado = sistema['db'].marcar_como_completada(99999)
        assert resultado is False


# ===========================================================
# HU06 + HU07: FECHA LÍMITE Y DETECCIÓN DE VENCIDAS
# ===========================================================

class TestAceptacionFechaLimiteYVencidas:
    """
    HU06 + HU07: Gestión de fechas límite y detección de tareas vencidas.

    Criterio de aceptación:
        Dado que una tarea tiene fecha límite en el pasado,
        Cuando el sistema ejecuta la detección de vencidas,
        Entonces la tarea se marca automáticamente como 'vencida'.
    """

    def test_flujo_tarea_vencida_detectada_automaticamente(self, sistema):
        """CASO FELIZ: Tarea con fecha pasada es marcada como vencida."""
        svc = sistema['tareas']

        tarea_id = svc.crear(
            titulo="Tarea atrasada",
            fecha_limite="2020-01-01",
            prioridad="alta"
        )
        assert svc.obtener(tarea_id)['estado'] == "pendiente"

        cantidad = svc.detectar_vencidas()

        assert cantidad >= 1
        assert svc.obtener(tarea_id)['estado'] == "vencida"

    def test_flujo_tarea_futura_no_se_marca_vencida(self, sistema):
        """CASO FELIZ: Tarea con fecha futura no se marca como vencida."""
        svc = sistema['tareas']

        tarea_id = svc.crear(
            titulo="Tarea futura",
            fecha_limite="2030-12-31",
            prioridad="media"
        )
        svc.detectar_vencidas()

        assert svc.obtener(tarea_id)['estado'] == "pendiente"

    def test_flujo_fecha_formato_incorrecto_rechazada(self, sistema):
        """CASO INFELIZ: Fecha con formato incorrecto (DD/MM/YYYY) es rechazada."""
        svc = sistema['tareas']

        with pytest.raises(ValueError):
            svc.crear(titulo="Test", fecha_limite="01/01/2026")


# ===========================================================
# HU08 + HU09 + HU10: CATEGORÍAS
# ===========================================================

class TestAceptacionCategorias:
    """
    HU08 + HU09 + HU10: Crear categorías, asignarlas y filtrar por ellas.

    Criterio de aceptación:
        Dado que el usuario crea una categoría y se la asigna a una tarea,
        Cuando filtra las tareas por esa categoría,
        Entonces solo aparecen las tareas de esa categoría.
    """

    def test_flujo_crear_categoria_y_asignar_a_tarea(self, sistema):
        """CASO FELIZ: Crear categoría, asignar a tarea y verificar."""
        svc_cat = sistema['categorias']
        svc_tar = sistema['tareas']

        cat_id = svc_cat.crear("Proyecto Final", "Tareas del proyecto")

        tarea_id = svc_tar.crear(
            titulo="Entregar documentación",
            prioridad="alta",
            categoria_id=cat_id
        )

        tarea = svc_tar.obtener(tarea_id)
        assert tarea['categoria_id'] == cat_id
        assert tarea['categoria_nombre'] == "Proyecto Final"

    def test_flujo_filtrar_tareas_por_categoria(self, sistema):
        """CASO FELIZ: Filtrar tareas por categoría muestra solo las correctas."""
        svc_cat = sistema['categorias']
        svc_tar = sistema['tareas']

        cat_id = svc_cat.crear("Filtrada", "")

        svc_tar.crear(titulo="En Filtrada 1", categoria_id=cat_id)
        svc_tar.crear(titulo="En Filtrada 2", categoria_id=cat_id)
        svc_tar.crear(titulo="Sin categoría específica")

        tareas_filtradas = svc_tar.obtener_todas(filtro_categoria="Filtrada")

        assert len(tareas_filtradas) == 2
        for t in tareas_filtradas:
            assert t['categoria_nombre'] == "Filtrada"

    def test_flujo_no_eliminar_categoria_con_tareas(self, sistema):
        """CASO INFELIZ: No se puede eliminar categoría que tiene tareas asignadas."""
        svc_cat = sistema['categorias']
        svc_tar = sistema['tareas']

        cat_id = svc_cat.crear("Con Tareas", "")
        svc_tar.crear(titulo="Tarea asignada", categoria_id=cat_id)

        with pytest.raises(ValueError, match="tarea"):
            svc_cat.eliminar(cat_id)

    def test_flujo_eliminar_categoria_sin_tareas(self, sistema):
        """CASO FELIZ: Se puede eliminar una categoría que no tiene tareas."""
        svc_cat = sistema['categorias']

        cat_id = svc_cat.crear("Sin Tareas", "")
        resultado = svc_cat.eliminar(cat_id)

        assert resultado is True
        cats_nombres = [c['nombre'] for c in svc_cat.obtener_todas()]
        assert "Sin Tareas" not in cats_nombres

    def test_flujo_categoria_duplicada_rechazada(self, sistema):
        """CASO INFELIZ: No se puede crear una categoría con nombre ya existente."""
        svc_cat = sistema['categorias']

        svc_cat.crear("Única", "")
        with pytest.raises((ValueError, Exception)):
            svc_cat.crear("Única", "Duplicada")


# ===========================================================
# FLUJO COMPLETO: CICLO DE VIDA DE UNA TAREA
# ===========================================================

class TestAceptacionCicloDeVidaCompleto:
    """
    FLUJO COMPLETO: Ciclo de vida completo de una tarea.

    Criterio de aceptación:
        Dado un usuario que usa la aplicación,
        Cuando ejecuta el ciclo completo (crear → editar → completar),
        Entonces cada paso se refleja correctamente y queda en el historial.
    """

    def test_flujo_ciclo_vida_crear_editar_completar(self, sistema):
        """CASO FELIZ: Ciclo de vida completo crear → editar → completar."""
        svc = sistema['tareas']
        db = sistema['db']

        # 1. Crear tarea
        tarea_id = svc.crear(
            titulo="Ciclo completo",
            descripcion="Test end-to-end",
            fecha_limite="2026-06-30",
            prioridad="baja"
        )
        assert svc.obtener(tarea_id)['estado'] == "pendiente"

        # 2. Editar la tarea
        svc.actualizar(tarea_id, titulo="Ciclo completo (editado)", prioridad="alta")
        assert svc.obtener(tarea_id)['titulo'] == "Ciclo completo (editado)"
        assert svc.obtener(tarea_id)['prioridad'] == "alta"

        # 3. Completar la tarea
        svc.completar(tarea_id)
        assert svc.obtener(tarea_id)['estado'] == "completada"

        # 4. Verificar historial completo
        historial = db.obtener_historial()
        acciones = [h['tipo_accion'] for h in historial]
        assert "CREAR" in acciones
        assert "EDITAR" in acciones
        assert "COMPLETAR" in acciones

    def test_flujo_estadisticas_reflejan_estado_real(self, sistema):
        """CASO FELIZ: Las estadísticas reflejan correctamente el estado del sistema."""
        svc = sistema['tareas']

        # Crear tareas en diferentes estados
        id_c1 = svc.crear(titulo="Completar 1")
        id_c2 = svc.crear(titulo="Completar 2")
        svc.crear(titulo="Vencida histórica", fecha_limite="2020-01-01")
        svc.crear(titulo="Pendiente futura", fecha_limite="2030-12-31")

        svc.completar(id_c1)
        svc.completar(id_c2)
        svc.detectar_vencidas()

        stats = svc.obtener_estadisticas()

        assert stats['total'] == 4
        assert stats['completadas'] == 2
        assert stats['vencidas'] >= 1
        assert stats['pendientes'] >= 0
        assert stats['total'] == (
            stats['completadas'] + stats['vencidas'] + stats['pendientes']
        )

    def test_flujo_ciclo_vida_crear_y_eliminar(self, sistema):
        """CASO FELIZ: Ciclo de vida alternativo: crear → eliminar."""
        svc = sistema['tareas']

        tarea_id = svc.crear(titulo="Para eliminar eventualmente")
        assert tarea_id in [t['id'] for t in svc.obtener_todas()]

        svc.eliminar(tarea_id)

        assert svc.obtener(tarea_id) is None
        assert tarea_id not in [t['id'] for t in svc.obtener_todas()]


# ===========================================================
# FUNCIONALIDADES EXTRA: ETIQUETAS E HISTORIAL
# ===========================================================

class TestAceptacionEtiquetasEHistorial:
    """
    Pruebas de aceptación para etiquetas e historial de acciones.

    Criterio de aceptación:
        El sistema gestiona etiquetas como tags adicionales
        y mantiene un historial auditable de todas las operaciones.
    """

    def test_flujo_crear_y_listar_etiquetas(self, sistema):
        """CASO FELIZ: El usuario crea etiquetas y las ve en el listado."""
        svc = sistema['etiquetas']

        svc.crear("Urgente", "#BF616A")
        svc.crear("Revisión", "#EBCB8B")

        etiquetas = svc.obtener_todas()
        nombres = [e['nombre'] for e in etiquetas]

        assert "Urgente" in nombres
        assert "Revisión" in nombres

    def test_flujo_etiqueta_duplicada_rechazada(self, sistema):
        """CASO INFELIZ: No se puede crear una etiqueta con nombre duplicado."""
        svc = sistema['etiquetas']

        svc.crear("TagUnica")
        with pytest.raises(ValueError, match="Ya existe"):
            svc.crear("TagUnica")

    def test_flujo_historial_registra_todas_las_acciones(self, sistema):
        """CASO FELIZ: El historial registra CREAR, EDITAR, COMPLETAR y ELIMINAR."""
        svc = sistema['tareas']
        db = sistema['db']

        id1 = svc.crear(titulo="Para historial completo")
        id2 = svc.crear(titulo="Para eliminar con historial")
        svc.actualizar(id1, titulo="Editada en historial")
        svc.completar(id1)
        svc.eliminar(id2)

        historial = db.obtener_historial()
        acciones = {h['tipo_accion'] for h in historial}

        assert "CREAR" in acciones
        assert "EDITAR" in acciones
        assert "COMPLETAR" in acciones
        assert "ELIMINAR" in acciones
