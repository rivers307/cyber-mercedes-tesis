from django.contrib import admin
from .models import Ingreso  # Auditoria ya no está aquí

@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'tipo', 'monto', 'registrado_por', 'metodo_pago')
    list_filter = ('tipo', 'metodo_pago', 'fecha')
    search_fields = ('descripcion', 'registrado_por__username')
    ordering = ('-fecha',)

# La clase AuditoriaAdmin se eliminó o se comentó
# Si quieres mantenerla, tienes que importar desde inventario:
# from inventario.models import Auditoria
# @admin.register(Auditoria)
# class AuditoriaAdmin(admin.ModelAdmin):
#     list_display = ('fecha', 'usuario', 'accion', 'modulo', 'ip_origen')
#     list_filter = ('accion', 'modulo', 'fecha')
#     search_fields = ('usuario__username', 'descripcion', 'registro_nombre')
#     ordering = ('-fecha',)