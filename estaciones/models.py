from django.db import models
from django.utils import timezone

class Estacion(models.Model):
    ESTADOS = (
        ('libre', '🟢 Libre'),
        ('ocupada', '🔴 Ocupada'),
        ('mantenimiento', '🟡 Mantenimiento'),
    )
    
    numero = models.IntegerField(unique=True, verbose_name="Número de PC")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='libre')
    precio_hora = models.DecimalField(max_digits=5, decimal_places=2, default=1.50)
    hora_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Hora de inicio de uso")
    tiempo_acumulado = models.IntegerField(default=0, verbose_name="Tiempo acumulado (minutos)")
    
    def obtener_tiempo_actual(self):
        """Calcula el tiempo actual de uso si la PC está ocupada"""
        if self.estado == 'ocupada' and self.hora_inicio:
            ahora = timezone.now()
            delta = ahora - self.hora_inicio
            minutos = int(delta.total_seconds() / 60)
            return self.tiempo_acumulado + minutos
        return self.tiempo_acumulado
    
    def __str__(self):
        return f"PC {self.numero}"
    
    class Meta:
        verbose_name = "Estación"
        verbose_name_plural = "Estaciones"
        ordering = ['numero']
class SesionPC(models.Model):
    """Registro de sesiones de uso de PCs"""

    COBRO_TIPOS = (
        ('acumulado_horas', 'Cobro acumulado por horas libres'),
        ('tiempo_fijo', 'Pago por tiempo especifico'),
    )

    METODOS_PAGO = (
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('pago_movil', 'Pago Móvil'),
    )

    estacion = models.ForeignKey(Estacion, on_delete=models.CASCADE)

    # Tiempos
    hora_inicio = models.DateTimeField()
    hora_fin = models.DateTimeField(null=True, blank=True)

    # Cobro
    tipo_cobro = models.CharField(max_length=30, choices=COBRO_TIPOS, default='acumulado_horas')
    duracion_programada_minutos = models.IntegerField(null=True, blank=True)
    termina_en = models.DateTimeField(null=True, blank=True, help_text='Se usa para cerrar automáticamente en cobro por tiempo fijo')

    # Resultados
    tiempo_minutos = models.IntegerField(default=0)
    monto_cobrado = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    pagado = models.BooleanField(default=False)

    # Pago
    metodo_pago = models.CharField(max_length=30, choices=METODOS_PAGO, null=True, blank=True)
    cerrada_automaticamente = models.BooleanField(default=False)

    # Cliente
    cliente_nombre = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"PC {self.estacion.numero} - {self.hora_inicio.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Sesión de PC"
        verbose_name_plural = "Sesiones de PC"
        ordering = ['-hora_inicio']
