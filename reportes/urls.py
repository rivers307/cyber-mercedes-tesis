from django.urls import path
from . import views

urlpatterns = [
    # Dashboards y reportes
    path('dashboard/', views.dashboard_principal, name='dashboard'),
    path('reportes/ventas/', views.ventas_view, name='reporte_ventas'),
    path('reportes/estaciones/', views.estaciones_view, name='reporte_estaciones'),
    path('reportes/sublimacion/', views.sublimacion_view, name='reporte_sublimacion'),
    path('reportes/inventario/', views.inventario_view, name='reporte_inventario'),
    path('reportes/cierre-caja/', views.cierre_caja, name='cierre_caja'),
    
    # Exportar reportes
    path('reportes/exportar/<str:tipo>/', views.exportar_reporte, name='exportar_reporte'),
    path('reportes/exportar/ventas/excel/', views.exportar_ventas_excel, name='exportar_ventas_excel'),
    path('reportes/exportar/estaciones/excel/', views.exportar_estaciones_excel, name='exportar_estaciones_excel'),
    path('reportes/exportar/sublimacion/excel/', views.exportar_sublimacion_excel, name='exportar_sublimacion_excel'),
    path('reportes/exportar/inventario/excel/', views.exportar_inventario_excel, name='exportar_inventario_excel'),
    path('reportes/exportar/auditoria-ventas/excel/', views.exportar_auditoria_ventas_excel, name='exportar_auditoria_ventas_excel'),
    
    # Registro de ventas
    path('reportes/registrar-venta/', views.registrar_venta_page, name='registrar_venta_page'),
    path('reportes/procesar-venta/', views.registrar_venta, name='registrar_venta'),
    
    # Tabulador de precios
    path('reportes/tabulador-precios/', views.tabulador_precios, name='tabulador_precios'),
    path('reportes/actualizar-tasa/', views.actualizar_tasa, name='actualizar_tasa'),
    path('reportes/actualizar-tasa-api/', views.actualizar_tasa_api, name='actualizar_tasa_api'),
    path('reportes/editar-precio/', views.editar_precio, name='editar_precio'),
    
    # Auditoría de ventas (admin)
    path('reportes/auditoria-ventas/', views.auditoria_ventas, name='auditoria_ventas'),
    
    # APIs
    path('api/ventas-data/', views.api_ventas_data, name='api_ventas_data'),
    path('api/estaciones-stats/', views.api_estaciones_stats, name='api_estaciones_stats'),
    path('api/sublimacion-stats/', views.api_sublimacion_stats, name='api_sublimacion_stats'),
    path('api/inventario-stats/', views.api_inventario_stats, name='api_inventario_stats'),
    path('api/insumos-lista/', views.api_insumos_lista, name='api_insumos_lista'),
    
    # Panel cliente
    path('panel-cliente/', views.panel_cliente, name='panel_cliente'),
    path('perfil-cliente/', views.perfil_cliente, name='perfil_cliente'),
    path('api/tasa-actual/', views.api_tasa_actual, name='api_tasa_actual'),
]