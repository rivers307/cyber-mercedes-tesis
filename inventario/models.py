from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Usuario
from sublimacion.models import Producto
from datetime import datetime

class Categoria(models.Model):
    """Categorías de insumos"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

class Insumo(models.Model):
    """Insumos/Materiales del inventario"""
    UNIDADES = (
        ('unidad', 'Unidad'),
        ('docena', 'Docena'),
        ('paquete', 'Paquete'),
        ('metro', 'Metro'),
        ('litro', 'Litro'),
        ('gramo', 'Gramo'),
    )
    
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True, blank=True)
    codigo = models.CharField(max_length=50, unique=True, blank=True)
    unidad = models.CharField(max_length=20, choices=UNIDADES, default='unidad')
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5, help_text="Stock mínimo para alerta")
    stock_maximo = models.IntegerField(default=100, help_text="Stock máximo recomendado")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ubicacion = models.CharField(max_length=100, blank=True, help_text="Ubicación en el almacén")
    proveedor = models.CharField(max_length=200, blank=True)
    notas = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock_actual} {self.unidad}"
    
    def necesita_reabastecimiento(self):
        return self.stock_actual <= self.stock_minimo
    
    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"
        ordering = ['nombre']

class MovimientoInventario(models.Model):
    """Registro de auditoría - TODOS los movimientos quedan registrados"""
    TIPOS_MOVIMIENTO = (
        ('entrada', '📥 Entrada - Compra'),
        ('salida', '📤 Salida - Uso'),
        ('ajuste', '🔧 Ajuste Manual'),
        ('devolucion', '🔄 Devolución'),
        ('perdida', '⚠️ Pérdida/Merma'),
    )
    
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=TIPOS_MOVIMIENTO)
    cantidad = models.IntegerField()
    stock_anterior = models.IntegerField(help_text="Stock antes del movimiento")
    stock_nuevo = models.IntegerField(help_text="Stock después del movimiento")
    motivo = models.TextField(blank=True, help_text="Razón del movimiento")
    
    # Relación con pedidos de sublimación (si aplica)
    pedido_relacionado = models.ForeignKey('sublimacion.Pedido', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Auditoría
    fecha = models.DateTimeField(auto_now_add=True)
    realizado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y %H:%M')} - {self.insumo.nombre} - {self.tipo} - {self.cantidad}"
    
    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-fecha']

class AlertaStock(models.Model):
    """Alertas automáticas de stock bajo"""
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    stock_actual = models.IntegerField()
    stock_minimo = models.IntegerField()
    leida = models.BooleanField(default=False)

    def __str__(self):
        return f"Alerta: {self.insumo.nombre} - Stock: {self.stock_actual}"
    
    # ========== NUEVOS MODELOS PARA AUDITORÍA COMUNAL ==========

class ActivoFijo(models.Model):
    """Activos fijos del cyber: PCs, routers, mobiliario"""
    TIPOS = (
        ('computadora', '🖥️ Computadora'),
        ('monitor', '🖥️ Monitor'),
        ('teclado', '⌨️ Teclado'),
        ('mouse', '🖱️ Mouse'),
        ('router', '📡 Router'),
        ('impresora', '🖨️ Impresora'),
        ('mobiliario', '🪑 Mobiliario'),
        ('otro', '📦 Otro'),
    )
    
    ESTADOS = (
        ('operativo', '✅ 100% Operativo'),
        ('parcial', '⚠️ Parcialmente Operativo'),
        ('dañado', '🔧 Dañado/Reparación'),
        ('obsoleto', '📦 Obsoleto/Desincorporado'),
    )
    
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='operativo')
    ubicacion = models.CharField(max_length=100, help_text="Estación, oficina, almacén")
    fecha_adquisicion = models.DateField(null=True, blank=True)
    valor_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    class Meta:
        verbose_name = "Activo Fijo"
        verbose_name_plural = "Activos Fijos"

class AuditoriaProgramada(models.Model):
    """Programación de auditorías de inventario"""
    TIPOS = (
        ('mensual', '📅 Mensual'),
        ('trimestral', '📅 Trimestral'),
        ('semestral', '📅 Semestral'),
        ('anual', '📅 Anual'),
    )
    
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.fecha_inicio} a {self.fecha_fin}"
    
    class Meta:
        verbose_name = "Auditoría Programada"
        verbose_name_plural = "Auditorías Programadas"

class InventarioTeorico(models.Model):
    """Inventario teórico (lo que DEBERÍA haber según registros)"""
    auditoria = models.ForeignKey(AuditoriaProgramada, on_delete=models.CASCADE, related_name='inventario_teorico')
    
    # Para consumibles
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, null=True, blank=True)
    cantidad_teorica = models.IntegerField()
    
    # Para activos fijos
    activo = models.ForeignKey(ActivoFijo, on_delete=models.CASCADE, null=True, blank=True)
    estado_teorico = models.CharField(max_length=20, choices=ActivoFijo.ESTADOS, null=True, blank=True)
    
    def __str__(self):
        if self.insumo:
            return f"{self.auditoria.nombre} - {self.insumo.nombre}: {self.cantidad_teorica}"
        return f"{self.auditoria.nombre} - {self.activo.codigo if self.activo else 'Activo'}"

class HallazgoAuditoria(models.Model):
    """Hallazgos encontrados en la auditoría física"""
    auditoria = models.ForeignKey(AuditoriaProgramada, on_delete=models.CASCADE, related_name='hallazgos')
    
    # Para consumibles
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, null=True, blank=True)
    cantidad_fisica = models.IntegerField(null=True, blank=True)
    
    # Para activos fijos
    activo = models.ForeignKey(ActivoFijo, on_delete=models.CASCADE, null=True, blank=True)
    estado_fisico = models.CharField(max_length=20, choices=ActivoFijo.ESTADOS, null=True, blank=True)
    observaciones = models.TextField()
    
    fecha_hallazgo = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    
    def __str__(self):
        if self.insumo:
            return f"Hallazgo: {self.insumo.nombre} - Físico: {self.cantidad_fisica}"
        return f"Hallazgo: {self.activo.nombre if self.activo else 'Activo'}"

class ConciliacionInventario(models.Model):
    """Conciliación entre inventario teórico y físico"""
    JUSTIFICACIONES = (
        ('uso_administrativo', '📋 Uso Administrativo (actas, reportes)'),
        ('falla_tecnica', '🔧 Falla Técnica (atasco, daño)'),
        ('perdida', '⚠️ Pérdida/Desincorporación'),
        ('robo', '🚨 Robo/Extravió'),
        ('error_registro', '📝 Error en registro'),
        ('otro', '📌 Otro'),
    )
    
    auditoria = models.ForeignKey(AuditoriaProgramada, on_delete=models.CASCADE, related_name='conciliaciones')
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, null=True, blank=True)
    activo = models.ForeignKey(ActivoFijo, on_delete=models.CASCADE, null=True, blank=True)
    
    cantidad_teorica = models.IntegerField(null=True, blank=True)
    cantidad_fisica = models.IntegerField(null=True, blank=True)
    variacion = models.IntegerField(null=True, blank=True, help_text="Diferencia: teórico - físico")
    
    estado_teorico = models.CharField(max_length=20, choices=ActivoFijo.ESTADOS, null=True, blank=True)
    estado_fisico = models.CharField(max_length=20, choices=ActivoFijo.ESTADOS, null=True, blank=True)
    
    justificacion = models.CharField(max_length=50, choices=JUSTIFICACIONES)
    detalle_justificacion = models.TextField(blank=True)
    costo_reposicion = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Costo estimado para reponer")
    
    conciliado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_conciliacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.insumo:
            return f"{self.auditoria.nombre} - {self.insumo.nombre}: {self.variacion}"
        return f"{self.auditoria.nombre} - {self.activo.nombre if self.activo else 'Activo'}"