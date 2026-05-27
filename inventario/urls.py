from django.urls import path
from . import views

urlpatterns = [
    path('inventario/', views.dashboard_inventario, name='dashboard_inventario'),
    path('inventario/insumos/', views.lista_insumos, name='lista_insumos'),
    path('inventario/insumo/crear/', views.crear_insumo, name='crear_insumo'),
    path('inventario/insumo/editar/<int:id>/', views.editar_insumo, name='editar_insumo'),
    path('inventario/insumo/eliminar/<int:id>/', views.eliminar_insumo, name='eliminar_insumo'),
    path('inventario/entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('inventario/salida/', views.registrar_salida, name='registrar_salida'),
    path('inventario/historial/', views.historial_movimientos, name='historial_movimientos'),
    path('inventario/alerta/<int:id>/leer/', views.marcar_alerta_leida, name='marcar_alerta'),
    path('inventario/categoria/crear/', views.crear_categoria, name='crear_categoria'),
    path('inventario/activos/', views.gestion_activos, name='gestion_activos'),
    path('inventario/auditorias/', views.lista_auditorias, name='lista_auditorias'),
    path('inventario/auditoria/programar/', views.programar_auditoria, name='programar_auditoria'),
    path('inventario/auditoria/<int:id>/realizar/', views.realizar_auditoria, name='realizar_auditoria'),
    path('inventario/auditoria/<int:id>/conciliar/', views.conciliar_auditoria, name='conciliar_auditoria'),
    path('inventario/auditoria/<int:id>/reporte/', views.reporte_auditoria, name='reporte_auditoria'),
    path('inventario/activos/', views.gestion_activos, name='gestion_activos'),
    path('inventario/auditorias/', views.lista_auditorias, name='lista_auditorias'),
    path('inventario/auditoria/programar/', views.programar_auditoria, name='programar_auditoria'),
    path('inventario/auditoria/<int:id>/realizar/', views.realizar_auditoria, name='realizar_auditoria'),
    path('inventario/auditoria/<int:id>/conciliar/', views.conciliar_auditoria, name='conciliar_auditoria'),
    path('inventario/auditoria/<int:id>/reporte/', views.reporte_auditoria, name='reporte_auditoria'),
    path('inventario/categoria/crear/', views.crear_categoria, name='crear_categoria'),

]