from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def admin_required(view_func):
    """Solo usuarios con rol 'admin' pueden acceder"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.rol == 'admin':
            return view_func(request, *args, **kwargs)
        # Clientes van a panel_cliente, empleados van a dashboard_empleado
        if request.user.is_authenticated and request.user.rol == 'cliente':
            return redirect('panel_cliente')
        return redirect('login')
    return wrapper

def empleado_required(view_func):
    """Usuarios con rol 'admin' o 'empleado' pueden acceder"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.rol in ['admin', 'empleado']:
            return view_func(request, *args, **kwargs)
        # Clientes van a panel_cliente
        if request.user.is_authenticated and request.user.rol == 'cliente':
            return redirect('panel_cliente')
        return redirect('login')
    return wrapper

def cliente_required(view_func):
    """Solo usuarios con rol 'cliente' pueden acceder"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.rol == 'cliente':
            return view_func(request, *args, **kwargs)
        # Admin o empleado van a dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')
        return redirect('login')
    return wrapper