from django.shortcuts import redirect
from django.urls import reverse

class RolePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Clientes solo pueden ver su perfil y pedidos
            if request.user.rol == 'cliente':
                restricted_paths = ['/admin/', '/inventario/', '/estaciones/', '/reportes/']
                for path in restricted_paths:
                    if request.path.startswith(path):
                        return redirect('perfil_cliente')
        
        response = self.get_response(request)
        return response