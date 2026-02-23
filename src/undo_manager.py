"""
Módulo de gestión de deshacer (Undo) para SmartTask Organizer.

Implementa el patrón de diseño Pila LIFO (Last In, First Out) para
permitir revertir las últimas acciones del usuario, como eliminar
o completar tareas. Se activa con el atajo de teclado Ctrl+Z.

Funcionalidad adicional que complementa las historias de usuario
HU04 (Eliminar tarea) y HU05 (Completar tarea).
"""
from datetime import datetime
from src.database import db

class UndoManager:
    """Administra la pila de acciones reversibles para la función Deshacer.

    Utiliza una pila LIFO (Last In, First Out) donde cada acción registrada
    contiene el tipo de operación y los datos necesarios para revertirla.

    Acciones soportadas:
        - ELIMINAR: Restaura una tarea eliminada recreándola en la BD.
        - COMPLETAR: Devuelve una tarea completada al estado 'pendiente'.

    Attributes:
        pila (list): Lista que funciona como pila LIFO. Cada elemento es
            un diccionario con las claves 'tipo', 'datos' y 'timestamp'.

    Example:
        >>> undo = UndoManager()
        >>> undo.registrar_accion("ELIMINAR", {'titulo': 'Mi tarea', ...})
        >>> resultado = undo.deshacer()  # Restaura la tarea eliminada
    """
    
    def __init__(self):
        """Inicializa el UndoManager con una pila vacía."""
        self.pila = []  # Pila LIFO (Last In, First Out)
        
    def registrar_accion(self, tipo, datos):
        """Registra una acción reversible en la pila.

        Almacena la acción con su tipo, datos asociados y una marca
        de tiempo para trazabilidad.

        Args:
            tipo (str): Tipo de acción realizada. Valores soportados:
                - 'ELIMINAR': Se eliminó una tarea (HU04).
                - 'COMPLETAR': Se completó una tarea (HU05).
            datos (dict): Datos necesarios para revertir la acción.
                Para 'ELIMINAR': debe contener 'titulo', 'descripcion',
                    'fecha_limite', 'prioridad', 'categoria_id', 'estado'.
                Para 'COMPLETAR': debe contener 'id' de la tarea.
        """
        accion = {
            'tipo': tipo,
            'datos': datos,
            'timestamp': datetime.now()
        }
        self.pila.append(accion)
        print(f"📝 Acción registrada en historial: {tipo}")
        
    def deshacer(self):
        """Revierte la última acción registrada en la pila.

        Saca el último elemento de la pila (LIFO) y ejecuta la operación
        inversa según el tipo de acción:
            - ELIMINAR: Recrea la tarea en la base de datos con los datos
              originales, incluyendo su estado previo.
            - COMPLETAR: Cambia el estado de la tarea de vuelta a 'pendiente'.

        Returns:
            str: Mensaje descriptivo del resultado de la operación.
                Ejemplo: "Tarea 'Estudiar' restaurada".
            None: Si la pila está vacía o el tipo de acción no es reconocido.

        Raises:
            No lanza excepciones; los errores se capturan internamente
            y se retorna un mensaje de error como string.
        """
        if not self.pila:
            return None
            
        ultimo = self.pila.pop()
        tipo = ultimo['tipo']
        datos = ultimo['datos']
        
        print(f"⏪ Deshaciendo acción: {tipo}")
        
        try:
            if tipo == 'ELIMINAR':
                # Re-crear la tarea eliminada usando SQLAlchemy API
                tarea_id = db.crear_tarea(
                    titulo=datos['titulo'],
                    descripcion=datos.get('descripcion', ''),
                    fecha_limite=datos.get('fecha_limite'),
                    prioridad=datos.get('prioridad', 'media'),
                    categoria_id=datos.get('categoria_id')
                )

                # Restaurar estado original si era diferente a 'pendiente'
                estado = datos.get('estado')
                if estado and estado != 'pendiente':
                    db.actualizar_tarea(tarea_id, estado=estado)

                return f"Tarea '{datos['titulo']}' restaurada"

            elif tipo == 'COMPLETAR':
                # Volver a estado 'pendiente' usando SQLAlchemy API
                tarea_id = datos['id']
                db.actualizar_tarea(tarea_id, estado='pendiente')

                # Obtener título para el mensaje
                t = db.obtener_tarea(tarea_id)
                titulo = t['titulo'] if t else "Tarea"
                return f"Tarea '{titulo}' marcada como pendiente"

        except Exception as e:
            print(f"❌ Error al deshacer: {e}")
            return f"Error al deshacer: {str(e)}"

        return None
