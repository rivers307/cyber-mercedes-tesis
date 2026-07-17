from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Usuario
from decimal import Decimal


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
    registrado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='ingresos_registrados')
    pedido_relacionado = models.ForeignKey('sublimacion.Pedido', on_delete=models.SET_NULL, null=True, blank=True)
    sesion_relacionada = models.ForeignKey('estaciones.SesionPC', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y %H:%M')} - {self.get_tipo_display()} - Bs {self.monto:.2f}"
    
    class Meta:
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"
        ordering = ['-fecha']


# ========== NUEVOS MODELOS PARA TABULADOR DE PRECIOS ==========

class TasaCambio(models.Model):
    """Registro de la tasa de cambio del día"""
    fecha = models.DateField(auto_now_add=True, unique=True)
    tasa = models.DecimalField(max_digits=10, decimal_places=2, help_text="Tasa de cambio Bs/USD")
    actualizada_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    fuente = models.CharField(max_length=50, default='Manual', help_text="API o Manual")
    
    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y')} - Bs {self.tasa:.2f} / USD"
    
    class Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        ordering = ['-fecha']


class PrecioServicio(models.Model):
    """Precios de servicios en USD (se convierten a Bs con la tasa del día)"""
    SERVICIOS = (
        ('pc_hora', '🖥️ PC por Hora'),
        ('sublimacion_taza', '🎨 Taza Sublimada'),
        ('sublimacion_camiseta', '👕 Camiseta Sublimada'),
        ('sublimacion_gorra', '🧢 Gorra Sublimada'),
        ('sublimacion_termo', '🫖 Termo Sublimado'),
        ('impresion_bn', '📄 Impresión B/N'),
        ('impresion_color', '🎨 Impresión Color'),
        ('fotocopia_bn', '📋 Fotocopia B/N'),
        ('fotocopia_color', '📋 Fotocopia Color'),
        ('insumo_venta', '📦 Venta de Insumo'),
        ('servicio_extra', '🔧 Servicio Extra'),
    )
    
    servicio = models.CharField(max_length=30, choices=SERVICIOS, unique=True)
    nombre_mostrar = models.CharField(max_length=100, help_text="Nombre amigable para mostrar")
    precio_usd = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio en USD")
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    actualizado_el = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre_mostrar}: ${self.precio_usd:.2f} USD"
    
    def precio_bs(self, tasa=None):
        """Calcula el precio en Bs según la tasa actual"""
        if tasa is None:
            tasa = TasaCambio.objects.first()
            if tasa:
                tasa = tasa.tasa
            else:
                return 0
        return self.precio_usd * tasa
    
    class Meta:
        verbose_name = "Precio de Servicio"
        verbose_name_plural = "Precios de Servicios"
        ordering = ['servicio']


# CORRECCIÓN: Se sacó la clase del bloque de 'Ingreso' desindentándola al nivel principal
# Datos afectados (opcional)