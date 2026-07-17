from django import forms
from django.core.exceptions import ValidationError
from .models import Pedido, Producto
import re


class PedidoForm(forms.ModelForm):
    # Hacemos obligatorios los campos que antes eran opcionales
    telefono_cliente = forms.CharField(
        required=True,
        label="Teléfono",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-purple-500/50 transition-all',
            'placeholder': 'Ej: +58 412-5551234 o 0412-5551234'
        })
    )
    id_cliente = forms.CharField(
        required=True,
        label="ID / RIF",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-purple-500/50 transition-all',
            'placeholder': 'Ej: V-12345678 o J-123456789'
        })
    )
    direccion_cliente = forms.CharField(
        required=True,
        label="Dirección",
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-purple-500/50 transition-all',
            'rows': 2,
            'placeholder': 'Dirección completa del cliente'
        })
    )

    class Meta:
        model = Pedido
        fields = [
            'nombre_cliente', 'telefono_cliente', 'id_cliente', 'direccion_cliente',
            'producto', 'cantidad', 'abono', 'especificaciones', 'archivo_diseno'
        ]
        widgets = {
            'nombre_cliente': forms.TextInput(attrs={
                'class': 'w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-purple-500/50 transition-all',
                'placeholder': 'Ej: Juan Pérez'
            }),
            'producto': forms.Select(attrs={
                'class': 'w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-purple-500/50 transition-all'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-purple-500/50 transition-all',
                'min': 1
            }),
            'abono': forms.NumberInput(attrs={
                'class': 'w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-purple-500/50 transition-all',
                'step': '0.50',
                'min': 0
            }),
            'especificaciones': forms.Textarea(attrs={
                'class': 'w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-purple-500/50 transition-all',
                'rows': 3,
                'placeholder': 'Color, talla, diseño, texto, imagen, etc...'
            }),
            'archivo_diseno': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*,application/pdf,application/postscript'
            }),
        }
        labels = {
            'nombre_cliente': 'Nombre Completo *',
            'producto': 'Producto Base *',
            'cantidad': 'Cantidad *',
            'abono': 'Abono Inicial (Bs)',
            'especificaciones': 'Especificaciones del Diseño',
            'archivo_diseno': 'Carga de Diseño Digital',
        }

    def clean_telefono_cliente(self):
        telefono = self.cleaned_data.get('telefono_cliente', '').strip()
        if not telefono:
            raise ValidationError('El número de teléfono es obligatorio.')
        
        # Limpiar espacios y guiones
        telefono_limpio = re.sub(r'[\s\-\(\)]', '', telefono)
        
        # Formatos permitidos:
        # - Nacional: 0412-1234567, 04141234567, +58-412-1234567
        # - Internacional: +58 412 1234567
        patrones = [
            r'^\+?58?\d{10}$',           # +58 4121234567 o 4121234567
            r'^0[4,9]\d{9}$',            # 0412-1234567 sin guiones
            r'^\+?58\s?[0,4,9]\d{9}$',   # +58 0412 1234567
        ]
        
        valido = any(re.match(p, telefono_limpio) for p in patrones)
        if not valido:
            raise ValidationError('Formato inválido. Use: +58 412-5551234, 0412-5551234 o 412-5551234.')
        
        return telefono

    def clean_id_cliente(self):
        id_cliente = self.cleaned_data.get('id_cliente', '').strip()
        if not id_cliente:
            raise ValidationError('El ID / RIF es obligatorio.')
        
        id_cliente = id_cliente.upper().strip()
        
        # Limpiar espacios y guiones extras
        id_limpio = re.sub(r'[\s\-]', '', id_cliente)
        
        # Formatos permitidos:
        # - Cédula venezolana: V-12345678, V12345678, E-12345678, etc.
        # - RIF venezolano: J-123456789, J123456789, G-123456789, etc.
        patron_cedula = r'^[V,E,J,G,P]\d{6,9}$'   # Letra + 6 a 9 dígitos
        patron_rif = r'^[J,G,V,E]\d{9}$'          # Letra + 9 dígitos (RIF)
        
        if re.match(patron_cedula, id_limpio) or re.match(patron_rif, id_limpio):
            return id_cliente  # Retorna el original con guiones o espacios (para mostrar)
        
        raise ValidationError('Formato inválido. Use: V-12345678, J-123456789, E-12345678, etc.')

    def clean_nombre_cliente(self):
        nombre = self.cleaned_data.get('nombre_cliente', '').strip()
        if not nombre:
            raise ValidationError('El nombre del cliente es obligatorio.')
        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')
        return nombre