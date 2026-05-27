from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Usuario

class Ingreso(models.Model):
    """Registro de todos los ingresos del negocio"""
    TIPOS = (
        ('estacion', '🖥️ Uso de PC'),
        ('sublimacion_pedido', '🎨 Pedido Completo de Sublimación'),
        ('sublimacion_abono', '💰 Abono de Sublimación'),
        ('papeleria', '📄 Papelería'),
        ('insumo', '📦 Venta de Insumo'),
        ('otros', '📌 Otros'),
    )
    
    METODOS_PAGO = (
        ('efectivo', '💵 Efectivo'),
        ('transferencia', '🏦 Transferencia Bancaria'),
        ('pago_movil', '📱 Pago Móvil'),
        ('tarjeta', '💳 Tarjeta de Débito/Crédito'),
        ('mixto', '🔄 Mixto (Varios métodos)'),
    )
    
    tipo = models.CharField(max_length=30, choices=TIPOS)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='efectivo')
    descripcion = models.CharField(max_length=200)
    fecha = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    
    # Relaciones opcionales
    pedido_relacionado = models.ForeignKey('sublimacion.Pedido', on_delete=models.SET_NULL, null=True, blank=True)
    sesion_relacionada = models.ForeignKey('estaciones.SesionPC', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y %H:%M')} - {self.get_tipo_display()} - Bs {self.monto:.2f}"
    
    class Meta:
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"
        ordering = ['-fecha']