from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('registro/', views.RegistroUsuarioView.as_view(), name='registro'),
    path('lista/', views.lista_usuarios_pendientes, name='lista_usuarios_pendientes'),
    path('verificar/<int:id>/', views.verificar_usuario, name='verificar_usuario'),
    path('crear-usuario/', views.admin_crear_usuario, name='admin_crear_usuario'),
    path('cambiar-tema/', views.cambiar_tema, name='cambiar_tema'),  # ⭐ NUEVA RUTA
]