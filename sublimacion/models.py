from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Usuario
from datetime import datetime

class Producto(models.Model):
    """Productos disponibles para sublimación"""
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, default='Taza', help_text="Ej: Taza, Camisa, Gorra, Llavero, Termo...")
    precio_base = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5, help_text="Stock mínimo para alerta")
    
    def __str__(self):
        return f"{self.nombre} - {self.tipo}"
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

class Pedido(models.Model):
    """Pedidos de sublimación"""
    ESTADOS = (
        ('pendiente', '📋 Pendiente'),
        ('diseño', '🎨 En Diseño'),
        ('produccion', '🖨️ En Producción'),
        ('listo', '✅ Listo para Entregar'),
        ('entregado', '🎁 Entregado'),
        ('cancelado', '❌ Cancelado'),
    )
    
    # Datos del cliente
    nombre_cliente = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True)
    
    # Datos del pedido
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    especificaciones = models.TextField(blank=True, help_text="Color, talla, diseño específico")
    
    # Estados y fechas
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    
    # Pagos
    precio_total = models.DecimalField(max_digits=8, decimal_places=2)
    abono = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Usuario que registró
    registrado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    
    def saldo_pendiente(self):
        return self.precio_total - self.abono
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.nombre_cliente} - {self.producto.nombre}"
    
    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_pedido']

class HistorialEstado(models.Model):
    """Historial de cambios de estado del pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    fecha = models.DateTimeField(auto_now_add=True)
    cambiado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.pedido} - {self.estado_anterior} → {self.estado_nuevo}"