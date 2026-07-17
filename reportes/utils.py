from functools import wraps
from inventario.models import Auditoria

def registrar_auditoria(accion, modulo, obtener_descripcion=None):
    """Decorador para registrar automáticamente acciones en auditoría"""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            response = func(request, *args, **kwargs)
            
            try:
                descripcion = ""
                if obtener_descripcion:
                    descripcion = obtener_descripcion(request, *args, **kwargs)
                else:
                    descripcion = f"Se ejecutó {accion} en {modulo}"
                
                # Obtener IP del cliente
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                
                Auditoria.objects.create(
                    usuario=request.user,
                    accion=accion,
                    modulo=modulo,
                    descripcion=descripcion,
                    ip_origen=ip,
                    registro_id=kwargs.get('id', None),
                    registro_nombre=request.POST.get('nombre', '') or request.POST.get('username', '')
                )
            except Exception as e:
                print(f"Error al registrar auditoría: {e}")
            
            return response
        return wrapper
    return decorator