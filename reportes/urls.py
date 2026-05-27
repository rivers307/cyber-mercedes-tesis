from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_principal, name='dashboard'),  # Esta es la URL
    path('reportes/ventas/', views.ventas_view, name='reporte_ventas'),
    path('reportes/estaciones/', views.estaciones_view, name='reporte_estaciones'),
    path('reportes/sublimacion/', views.sublimacion_view, name='reporte_sublimacion'),
    path('reportes/inventario/', views.inventario_view, name='reporte_inventario'),
    path('reportes/cierre-caja/', views.cierre_caja, name='cierre_caja'),
    path('api/ventas-data/', views.api_ventas_data, name='api_ventas_data'),
    path('api/estaciones-stats/', views.api_estaciones_stats, name='api_estaciones_stats'),
    path('api/sublimacion-stats/', views.api_sublimacion_stats, name='api_sublimacion_stats'),
    path('api/inventario-stats/', views.api_inventario_stats, name='api_inventario_stats'),
    path('reportes/exportar/<str:tipo>/', views.exportar_reporte, name='exportar_reporte'),
    
]