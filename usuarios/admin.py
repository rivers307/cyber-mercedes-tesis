from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    # ⭐ Agregamos 'tema' al list_display
    list_display = ('username', 'email', 'rol', 'tema', 'verificado', 'is_active')
    list_filter = ('rol', 'verificado', 'tema', 'is_active')
    search_fields = ('username', 'email', 'telefono')
    
    # ⭐ Agregamos el campo 'tema' a los fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('rol', 'telefono', 'direccion', 'verificado', 'verificado_por', 'fecha_verificacion', 'motivo_rechazo')
        }),
        ('Preferencias', {
            'fields': ('tema',),
            'classes': ('collapse',)
        }),
    )
    
    # ⭐ Agregamos campos para el formulario de creación
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {
            'fields': ('rol', 'tema'),
        }),
    )

admin.site.register(Usuario, UsuarioAdmin)
