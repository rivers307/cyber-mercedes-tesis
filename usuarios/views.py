from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from usuarios.decorators import admin_required
from .forms import RegistroClienteForm, AdminCrearUsuarioForm
from .models import Usuario
from reportes.utils import registrar_auditoria


# ============================================================
# ========== LOGIN PERSONALIZADO CON AUDITORÍA ==========
# ============================================================
class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    
    def form_valid(self, form):
        """Registrar login exitoso en auditoría"""
        response = super().form_valid(form)
        
        # Registrar login en auditoría
        try:
            from reportes.utils import registrar_auditoria
            registrar_auditoria(
                accion='login',
                modulo='Autenticación',
                obtener_descripcion=lambda r, **k: f"Inicio de sesión exitoso - Usuario: {self.request.user.username}"
            )(self.request)
        except Exception as e:
            print(f"Error al registrar login: {e}")
        
        return response
    
    def form_invalid(self, form):
        """Mensaje de error cuando falla el login"""
        messages.error(self.request, '❌ Usuario o contraseña incorrectos. Por favor intente nuevamente.')
        return super().form_invalid(form)


# ============================================================
# ========== CIERRE DE SESIÓN ==========
# ============================================================
@login_required
@registrar_auditoria(
    accion='logout',
    modulo='Autenticación',
    obtener_descripcion=lambda r, **k: f"Cierre de sesión - Usuario: {r.user.username}"
)
def custom_logout(request):
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente.')
    return redirect('usuarios:login')


# ============================================================
# ========== REGISTRO DE USUARIOS (CLIENTES) ==========
# ============================================================
class RegistroUsuarioView(CreateView):
    form_class = RegistroClienteForm
    template_name = 'usuarios/registro.html'
    success_url = reverse_lazy('usuarios:login')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.rol = form.cleaned_data.get('rol', 'cliente')
        user.verificado = False
        user.save()
        
        messages.success(
            self.request, 
            '✅ Registro exitoso. Espera la verificación del administrador para acceder al sistema.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'❌ {error}')
        return super().form_invalid(form)


# ============================================================
# ========== LISTA DE USUARIOS PENDIENTES ==========
# ============================================================
@admin_required
def lista_usuarios_pendientes(request):
    """Lista de usuarios pendientes de verificación"""
    usuarios_pendientes = Usuario.objects.filter(
        verificado=False,
        rol__in=['admin', 'empleado']
    ).exclude(username='admin')
    usuarios_verificados = Usuario.objects.filter(verificado=True)
    return render(request, 'usuarios/pendientes.html', {
        'pendientes': usuarios_pendientes,
        'verificados': usuarios_verificados,
    })


# ============================================================
# ========== VERIFICAR USUARIO ==========
# ============================================================
@admin_required
@registrar_auditoria(
    accion='verificar_usuario',
    modulo='Usuarios - Verificación',
    obtener_descripcion=lambda r, id, **k: f"{'Aprobó' if r.POST.get('accion') == 'aprobar' else 'Rechazó'} al usuario {r.POST.get('nombre', '')}"
)
def verificar_usuario(request, id):
    """Aprobar o rechazar un usuario"""
    usuario = get_object_or_404(Usuario, id=id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        motivo = request.POST.get('motivo', '')
        
        if accion == 'aprobar':
            usuario.verificado = True
            usuario.verificado_por = request.user
            from django.utils import timezone
            usuario.fecha_verificacion = timezone.now()
            usuario.save()
            messages.success(request, f'✅ Usuario {usuario.username} verificado exitosamente')
        elif accion == 'rechazar':
            usuario.motivo_rechazo = motivo
            usuario.is_active = False
            usuario.save()
            messages.warning(request, f'❌ Usuario {usuario.username} rechazado')
        
        return redirect('usuarios:lista_usuarios_pendientes')
    
    return redirect('usuarios:lista_usuarios_pendientes')


# ============================================================
# ========== CREAR USUARIO (SOLO ADMIN) ==========
# ============================================================
@admin_required
@registrar_auditoria(
    accion='crear_usuario',
    modulo='Usuarios - Administración',
    obtener_descripcion=lambda r, **k: f"Creó usuario {r.POST.get('username', '')} con rol {r.POST.get('rol', '')}"
)
def admin_crear_usuario(request):
    """Vista para que el administrador cree usuarios manualmente"""
    if request.method == 'POST':
        form = AdminCrearUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'✅ Usuario "{user.username}" creado exitosamente.')
            return redirect('usuarios:lista_usuarios_pendientes')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'❌ {error}')
    else:
        form = AdminCrearUsuarioForm()
    
    return render(request, 'usuarios/admin_crear_usuario.html', {'form': form})


# ============================================================
# ========== CAMBIAR TEMA (CLARO/OSCURO) ==========
# ============================================================
@login_required
@require_POST
@csrf_exempt
def cambiar_tema(request):
    """Vista para cambiar el tema del usuario (claro/oscuro)"""
    tema = request.POST.get('tema')
    
    if tema in ['dark', 'light']:
        request.user.tema = tema
        request.user.save()
        return JsonResponse({'success': True, 'tema': tema})
    
    return JsonResponse({'success': False, 'error': 'Tema inválido'})