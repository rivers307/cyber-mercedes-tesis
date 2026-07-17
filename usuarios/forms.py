from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full input-field rounded-xl px-4 py-3 text-white placeholder-white/30'
    }))
    
    # ⭐ TODOS los roles disponibles (incluyendo admin)
    ROLES_CHOICES = (
        ('cliente', '👤 Cliente'),
        ('empleado', '👩‍💼 Empleado'),
        ('admin', '👑 Administrador'),
    )
    
    rol = forms.ChoiceField(
        choices=ROLES_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full input-field rounded-xl px-4 py-3 text-white bg-black/30'}),
        label='Tipo de usuario',
        initial='cliente'
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2', 'rol']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full input-field rounded-xl px-4 py-3 text-white placeholder-white/30'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full input-field rounded-xl px-4 py-3 text-white placeholder-white/30'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full input-field rounded-xl px-4 py-3 text-white placeholder-white/30'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.rol = self.cleaned_data['rol']
        
        # ⭐ El tema se guarda con el valor por defecto 'dark'
        user.tema = 'dark'
        
        # Si el usuario se registra como admin o empleado, necesita verificación
        if user.rol in ['admin', 'empleado']:
            user.verificado = False
        else:
            user.verificado = True
        
        if commit:
            user.save()
        return user


# ============================================================
# ========== FORMULARIO PARA ADMIN (CREAR USUARIOS) ==========
# ============================================================
class AdminCrearUsuarioForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'w-full input-field rounded-xl px-4 py-3 text-white placeholder-white/30'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'w-full input-field rounded-xl px-4 py-3 text-white placeholder-white/30'})
    )
    
    # ⭐ TODOS los roles disponibles (incluyendo admin)
    ROLES_CHOICES = (
        ('cliente', '👤 Cliente'),
        ('empleado', '👩‍💼 Empleado'),
        ('admin', '👑 Administrador'),
    )
    
    rol = forms.ChoiceField(
        choices=ROLES_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full input-field rounded-xl px-4 py-3 text-white bg-black/30'}),
        label='Rol del usuario',
        initial='cliente'
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'rol']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full input-field rounded-xl px-4 py-3 text-white placeholder-white/30'}),
            'email': forms.EmailInput(attrs={'class': 'w-full input-field rounded-xl px-4 py-3 text-white placeholder-white/30'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.verificado = True  # El admin lo verifica automáticamente
        user.tema = 'dark'  # Tema por defecto
        if commit:
            user.save()
        return user