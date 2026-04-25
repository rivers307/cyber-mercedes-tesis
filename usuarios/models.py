from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='operador')
    
    def __str__(self):
        return self.username