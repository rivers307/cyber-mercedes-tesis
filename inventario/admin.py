from django.contrib import admin
from .models import Insumo, Categoria, MovimientoInventario, AlertaStock, ActivoFijo

@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'categoria', 'stock_actual', 'precio_usd', 'precio_unitario', 'unidad')
    list_filter = ('categoria', 'unidad')
    search_fields = ('nombre', 'codigo')
    list_editable = ('stock_actual', 'precio_usd')
    readonly_fields = ('precio_unitario',)  # Se calcula automáticamente

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'insumo', 'tipo', 'cantidad', 'fecha', 'realizado_por')
    list_filter = ('tipo', 'fecha')
    search_fields = ('insumo__nombre', 'motivo')
    readonly_fields = ('fecha',)

@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'insumo', 'stock_actual', 'stock_minimo', 'fecha_alerta', 'leida')
    list_filter = ('leida', 'fecha_alerta')
    search_fields = ('insumo__nombre',)

@admin.register(ActivoFijo)
class ActivoFijoAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre', 'tipo', 'estado', 'ubicacion')
    list_filter = ('tipo', 'estado')
    search_fields = ('codigo', 'nombre')