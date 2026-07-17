from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Usuario
from datetime import datetime
from decimal import Decimal


class Producto(models.Model):
    """Productos disponibles para sublimación"""
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, default='Taza', help_text="Ej: Taza, Camisa, Gorra, Llavero, Termo...")
    
    # ⭐ Precio en USD (se ingresa manualmente)
    precio_usd = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0,
        help_text="Precio en dólares (USD) - se usará para calcular el precio en Bs según la tasa del día"
    )
    
    # Precio en Bs (se calcula automáticamente al guardar)
    precio_base = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0,
        help_text="Precio en Bs (calculado automáticamente según la tasa de cambio)"
    )
    
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5, help_text="Stock mínimo para alerta")
    
    def precio_bs(self):
        """Calcula el precio en Bs según la tasa de cambio actual"""
        from reportes.models import TasaCambio
        # ✅ Convertir a Decimal por si acaso es una cadena
        precio_usd = Decimal(str(self.precio_usd))
        tasa = TasaCambio.objects.first()
        if tasa:
            return precio_usd * tasa.tasa
        # Fallback si no hay tasa registrada
        return precio_usd * Decimal('60')
    
    def save(self, *args, **kwargs):
        """Actualiza precio_base en Bs antes de guardar"""
        self.precio_base = self.precio_bs()
        super().save(*args, **kwargs)
    
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
    telefono_cliente = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono del cliente")
    id_cliente = models.CharField(max_length=30, blank=True, null=True, verbose_name="ID / RIF del cliente")
    direccion_cliente = models.TextField(blank=True, null=True, verbose_name="Dirección del cliente")
    
    # Datos del pedido
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    especificaciones = models.TextField(blank=True, help_text="Color, talla, diseño específico")
    
    # Estados y fechas
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    
    # Pagos
    precio_total = models.DecimalField(max_digits=8, decimal_places=2, help_text="Total en Bs")
    abono = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # ⭐ Auditoría de precios
    precio_usd_unitario = models.DecimalField(
        max_digits=8, decimal_places=2, 
        default=0,
        help_text="Precio unitario en USD al momento del pedido"
    )
    tasa_usada = models.DecimalField(
        max_digits=10, decimal_places=2, 
        default=0,
        help_text="Tasa de cambio Bs/USD usada al momento del pedido"
    )
    
    # Usuario que registró
    registrado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    
    archivo_diseno = models.FileField(upload_to='disenos/', blank=True, null=True, verbose_name="Archivo de diseño")
    notas_produccion = models.TextField(blank=True, null=True, help_text="Parámetros de producción: temperatura, tiempo, presión, etc.")

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