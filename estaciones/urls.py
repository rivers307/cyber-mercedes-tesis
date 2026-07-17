from django.urls import path
from . import views

app_name = 'estaciones'

urlpatterns = [
    # Dashboard principal de PCs
    path('estaciones/', views.dashboard_estaciones, name='dashboard_estaciones'),
    
    # CRUD de estaciones (solo admin)
    path('estaciones/crear/', views.crear_estacion, name='crear_estacion'),
    path('estaciones/editar/<int:id>/', views.editar_estacion, name='editar_estacion'),
    path('estaciones/eliminar/<int:id>/', views.eliminar_estacion, name='eliminar_estacion'),
    path('estaciones/mantenimiento/<int:id>/', views.cambiar_estado_mantenimiento, name='cambiar_estado_mantenimiento'),
    
    # Gestión de sesiones
    path('estaciones/iniciar/<int:id>/', views.iniciar_sesion, name='iniciar_sesion'),
    path('estaciones/finalizar/<int:sesion_id>/', views.finalizar_sesion, name='finalizar_sesion'),
    
    # APIs
    path('api/estado-sesion/<int:sesion_id>/', views.obtener_estado_sesion, name='obtener_estado_sesion'),
    path('api/estacion/<int:id>/cambiar/', views.cambiar_estado, name='cambiar_estado'),
    path('api/estaciones/stats/', views.estadisticas_api, name='estadisticas_api'),
    path('api/estaciones/cerrar-vencidas/', views.cerrar_sesiones_vencidas, name='cerrar_sesiones_vencidas'),
]