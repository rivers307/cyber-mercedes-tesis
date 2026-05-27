from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('admin', '👑 Administrador'),
        ('empleado', '👩‍💼 Empleado'),
        ('cliente', '👤 Cliente'),
    )
    
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
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