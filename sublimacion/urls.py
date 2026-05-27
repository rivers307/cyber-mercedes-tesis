from django.urls import path
from . import views

urlpatterns = [
    path('sublimacion/', views.dashboard_pedidos, name='sublimacion_dashboard'),
    path('sublimacion/lista/', views.lista_pedidos, name='lista_pedidos'),
    path('sublimacion/crear/', views.crear_pedido_form, name='crear_pedido_form'),
    path('sublimacion/crear/guardar/', views.crear_pedido, name='crear_pedido'),
    path('sublimacion/pedido/<int:id>/', views.detalle_pedido, name='detalle_pedido'),
    path('sublimacion/pedido/<int:id>/estado/', views.cambiar_estado, name='cambiar_estado'),
    path('sublimacion/pedido/<int:id>/abono/', views.registrar_abono, name='registrar_abono'),
    path('sublimacion/productos/', views.gestionar_productos, name='gestionar_productos'),
    path('sublimacion/productos/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('sublimacion/productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
]