from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from usuarios.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('dashboard')),
    path('login/', CustomLoginView.as_view(), name='login'),

    # Recuperación de contraseña
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/password-reset/complete/'
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # ============================================================
    # ⭐ IMPORTANTE: Las URLs específicas van PRIMERO
    # ============================================================
    
    # 1. App de estaciones (control de PCs)
    path('', include('estaciones.urls')),  # <- Mueve esto ANTES de reportes
    
    # 2. App de usuarios
    path('', include('usuarios.urls')),
    
    # 3. App de reportes (tiene rutas como /reportes/ y /estaciones/ que no deben interferir)
    path('', include('reportes.urls')),
    
    # 4. Otras apps
    path('', include('sublimacion.urls')),
    path('', include('inventario.urls')),
    path('asistente/', include('asistente.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)