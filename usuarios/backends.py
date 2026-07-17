from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class VerificacionBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is not None:
            # Los clientes pueden iniciar sesión siempre
            if user.rol == 'cliente':
                return user
            # Empleados y admin deben estar verificados
            if user.rol in ['admin', 'empleado'] and not user.verificado:
                return None
        return user