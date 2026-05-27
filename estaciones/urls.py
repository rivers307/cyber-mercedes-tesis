from django.urls import path
from . import views

urlpatterns = [
    path('estaciones/', views.dashboard_estaciones, name='dashboard_estaciones'),
    path('estaciones/crear/', views.crear_estacion, name='crear_estacion'),
    path('estaciones/editar/<int:id>/', views.editar_estacion, name='editar_estacion'),
    path('estaciones/eliminar/<int:id>/', views.eliminar_estacion, name='eliminar_estacion'),
    path('api/estacion/<int:id>/cambiar/', views.cambiar_estado, name='cambiar_estado'),
    path('api/estaciones/stats/', views.estadisticas_api, name='estadisticas_api'),
    path('api/estaciones/cerrar-vencidas/', views.cerrar_sesiones_vencidas, name='cerrar_sesiones_vencidas'),
]