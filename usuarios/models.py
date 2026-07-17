from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('admin', '👑 Administrador'),
        ('empleado', '👩‍💼 Empleado'),
        ('cliente', '👤 Cliente'),
    )
    
    # ⭐ NUEVO: Opciones para el tema
    TEMA_CHOICES = [
        ('dark', '🌙 Oscuro'),
        ('light', '☀️ Claro'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    # ✅ CAMPOS PARA VERIFICACIÓN
    verificado = models.BooleanField(default=False, help_text="Indica si el usuario ha sido verificado por un administrador")
    verificado_por = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='verificados')
    fecha_verificacion = models.DateTimeField(null=True, blank=True)
    motivo_rechazo = models.TextField(blank=True, null=True, help_text="Motivo de rechazo si fue denegado")
    
    # ⭐ NUEVO CAMPO PARA TEMA (claro/oscuro)
    tema = models.CharField(
        max_length=10, 
        choices=TEMA_CHOICES, 
        default='dark',
        verbose_name='Tema preferido'
    )
    
    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"
    
    @property
    def es_admin(self):
        return self.rol == 'admin'
    
    @property
    def es_empleado(self):
        return self.rol in ['admin', 'empleado']
    
    @property
    def es_cliente(self):
        return self.rol == 'cliente'
    
    @property
    def puede_iniciar_sesion(self):
        """Verifica si el usuario puede iniciar sesión"""
        if self.rol == 'cliente':
            return True  # Los clientes pueden iniciar sesión siempre
        if self.rol in ['admin', 'empleado']:
            return self.verificado  # Solo si están verificados
        return False