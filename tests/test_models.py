"""
Pruebas unitarias para los modelos SQLAlchemy de SmartTask Organizer.

Verifica las validaciones, constraints, relaciones y campos por defecto
de los modelos Categoria, Tarea, Etiqueta e HistorialAccion.

Framework: pytest
Cobertura: src/models.py
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, Categoria, Tarea, Etiqueta, HistorialAccion


@pytest.fixture
def session():
    """Crea una sesión SQLAlchemy en memoria para tests de modelos.

    Yields:
        Session: Sesión activa con tablas creadas.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()
    engine.dispose()


class TestModeloCategoria:
    """Tests para el modelo Categoria."""

    def test_crear_categoria(self, session):
        """Verifica que se puede crear una categoría con nombre y descripción."""
        cat = Categoria(nombre="TestCat", descripcion="Desc test")
        session.add(cat)
        session.commit()
        assert cat.id is not None
        assert cat.nombre == "TestCat"

    def test_nombre_strip(self, session):
        """Verifica que el nombre se limpia de espacios."""
        cat = Categoria(nombre="  Espacios  ", descripcion="")
        session.add(cat)
        session.commit()
        assert cat.nombre == "Espacios"

    def test_nombre_vacio_falla(self, session):
        """Verifica que un nombre vacío lanza ValueError."""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            Categoria(nombre="", descripcion="")

    def test_nombre_none_falla(self, session):
        """Verifica que nombre None lanza ValueError."""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            Categoria(nombre=None, descripcion="")

    def test_to_dict(self, session):
        """Verifica la conversión a diccionario."""
        cat = Categoria(nombre="Dict", descripcion="Test dict")
        session.add(cat)
        session.commit()
        d = cat.to_dict()
        assert d['nombre'] == "Dict"
        assert d['descripcion'] == "Test dict"
        assert 'id' in d

    def test_repr(self, session):
        """Verifica la representación legible."""
        cat = Categoria(nombre="Repr", descripcion="")
        session.add(cat)
        session.commit()
        assert "Repr" in repr(cat)

    def test_nombre_unico(self, session):
        """Verifica que no se pueden crear dos categorías con el mismo nombre."""
        session.add(Categoria(nombre="Unica", descripcion=""))
        session.commit()
        session.add(Categoria(nombre="Unica", descripcion=""))
        with pytest.raises(Exception):
            session.commit()


class TestModeloTarea:
    """Tests para el modelo Tarea."""

    def test_crear_tarea(self, session):
        """Verifica la creación básica de una tarea."""
        tarea = Tarea(titulo="Test tarea", prioridad="media")
        session.add(tarea)
        session.commit()
        assert tarea.id is not None
        assert tarea.estado == 'pendiente'

    def test_titulo_obligatorio(self, session):
        """Verifica que el título no puede ser vacío."""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            Tarea(titulo="", prioridad="media")

    def test_titulo_strip(self, session):
        """Verifica que el título se limpia de espacios."""
        tarea = Tarea(titulo="  Titulo  ", prioridad="media")
        assert tarea.titulo == "Titulo"

    def test_estado_valido(self, session):
        """Verifica que solo se aceptan estados válidos."""
        tarea = Tarea(titulo="Test", estado="pendiente")
        assert tarea.estado == "pendiente"

    def test_estado_invalido(self, session):
        """Verifica que un estado inválido lanza ValueError."""
        with pytest.raises(ValueError, match="no válido"):
            Tarea(titulo="Test", estado="desconocido")

    def test_prioridad_valida(self, session):
        """Verifica que solo se aceptan prioridades válidas."""
        tarea = Tarea(titulo="Test", prioridad="alta")
        assert tarea.prioridad == "alta"

    def test_prioridad_invalida(self, session):
        """Verifica que una prioridad inválida lanza ValueError."""
        with pytest.raises(ValueError, match="no válida"):
            Tarea(titulo="Test", prioridad="urgente")

    def test_campos_default(self, session):
        """Verifica los valores por defecto de los campos."""
        tarea = Tarea(titulo="Defaults")
        session.add(tarea)
        session.commit()
        assert tarea.estado == 'pendiente'
        assert tarea.prioridad == 'media'
        assert tarea.descripcion == ''
        assert tarea.fecha_creacion is not None

    def test_to_dict_sin_categoria(self, session):
        """Verifica to_dict cuando no hay categoría asignada."""
        tarea = Tarea(titulo="Sin cat")
        session.add(tarea)
        session.commit()
        d = tarea.to_dict()
        assert d['categoria_nombre'] is None
        assert d['titulo'] == "Sin cat"

    def test_to_dict_con_categoria(self, session):
        """Verifica to_dict incluyendo nombre de categoría."""
        cat = Categoria(nombre="CatTest", descripcion="")
        session.add(cat)
        session.commit()
        tarea = Tarea(titulo="Con cat", categoria_id=cat.id)
        session.add(tarea)
        session.commit()
        d = tarea.to_dict()
        assert d['categoria_nombre'] == "CatTest"

    def test_repr(self, session):
        """Verifica la representación legible de Tarea."""
        tarea = Tarea(titulo="ReprTest")
        session.add(tarea)
        session.commit()
        assert "ReprTest" in repr(tarea)


class TestModeloEtiqueta:
    """Tests para el modelo Etiqueta."""

    def test_crear_etiqueta(self, session):
        """Verifica la creación básica de una etiqueta."""
        etiq = Etiqueta(nombre="Urgente")
        session.add(etiq)
        session.commit()
        assert etiq.id is not None
        assert etiq.color == '#88C0D0'

    def test_color_personalizado(self, session):
        """Verifica que se puede asignar un color personalizado."""
        etiq = Etiqueta(nombre="Custom", color="#FF0000")
        session.add(etiq)
        session.commit()
        assert etiq.color == "#FF0000"

    def test_nombre_vacio_falla(self, session):
        """Verifica que nombre vacío lanza ValueError."""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            Etiqueta(nombre="")

    def test_to_dict(self, session):
        """Verifica la conversión a diccionario de Etiqueta."""
        etiq = Etiqueta(nombre="TagDict", color="#ABCDEF")
        session.add(etiq)
        session.commit()
        d = etiq.to_dict()
        assert d['nombre'] == "TagDict"
        assert d['color'] == "#ABCDEF"

    def test_repr(self, session):
        """Verifica la representación legible de Etiqueta."""
        etiq = Etiqueta(nombre="ReprTag")
        session.add(etiq)
        session.commit()
        assert "ReprTag" in repr(etiq)


class TestModeloHistorial:
    """Tests para el modelo HistorialAccion."""

    def test_crear_historial(self, session):
        """Verifica la creación de un registro de historial."""
        hist = HistorialAccion(tipo_accion="CREAR", tarea_titulo="Test")
        session.add(hist)
        session.commit()
        assert hist.id is not None
        assert hist.fecha is not None

    def test_tipo_accion_vacio_falla(self, session):
        """Verifica que tipo_accion vacío lanza ValueError."""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            HistorialAccion(tipo_accion="")

    def test_to_dict(self, session):
        """Verifica la conversión a diccionario de HistorialAccion."""
        hist = HistorialAccion(
            tipo_accion="ELIMINAR", tarea_titulo="Borrada",
            detalles="Eliminación total"
        )
        session.add(hist)
        session.commit()
        d = hist.to_dict()
        assert d['tipo_accion'] == "ELIMINAR"
        assert d['tarea_titulo'] == "Borrada"
        assert d['detalles'] == "Eliminación total"

    def test_repr(self, session):
        """Verifica la representación legible de HistorialAccion."""
        hist = HistorialAccion(tipo_accion="EDITAR", tarea_titulo="Editada")
        session.add(hist)
        session.commit()
        assert "EDITAR" in repr(hist)


class TestRelaciones:
    """Tests para relaciones entre modelos."""

    def test_tarea_pertenece_a_categoria(self, session):
        """Verifica la relación N:1 entre Tarea y Categoria."""
        cat = Categoria(nombre="RelCat", descripcion="")
        session.add(cat)
        session.commit()
        tarea = Tarea(titulo="Rel tarea", categoria_id=cat.id)
        session.add(tarea)
        session.commit()
        assert tarea.categoria.nombre == "RelCat"

    def test_categoria_tiene_tareas(self, session):
        """Verifica la relación 1:N desde Categoria a Tarea."""
        cat = Categoria(nombre="ParentCat", descripcion="")
        session.add(cat)
        session.commit()
        session.add(Tarea(titulo="Hija 1", categoria_id=cat.id))
        session.add(Tarea(titulo="Hija 2", categoria_id=cat.id))
        session.commit()
        assert cat.tareas.count() == 2

    def test_etiqueta_many_to_many(self, session):
        """Verifica la relación N:M entre Tarea y Etiqueta."""
        tarea = Tarea(titulo="Tagged")
        etiq = Etiqueta(nombre="ManyTag")
        session.add_all([tarea, etiq])
        session.commit()
        tarea.etiquetas.append(etiq)
        session.commit()
        assert len(tarea.etiquetas) == 1
        assert tarea.etiquetas[0].nombre == "ManyTag"
        assert len(etiq.tareas) == 1
