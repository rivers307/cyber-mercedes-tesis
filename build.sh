#!/usr/bin/env bash

# Salir si pip, migrate o collectstatic fallan
set -e

echo "=== 1. Instalando dependencias ==="
pip install -r requirements.txt

echo "=== 2. Recopilando archivos estáticos ==="
python manage.py collectstatic --no-input

echo "=== 3. Aplicando migraciones ==="
python manage.py migrate

echo "=== 4. Configurando superusuario (sin fallar) ==="
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not password:
    print('⚠️  Contraseña no definida. Omitiendo creación de superusuario.')
else:
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.email = email
        user.save()
        print(f'✅ Superusuario \"{username}\" ACTUALIZADO correctamente.')
    except User.DoesNotExist:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f'✅ Superusuario \"{username}\" CREADO correctamente.')
    except Exception as e:
        print(f'⚠️  Error inesperado: {e}. El despliegue continúa...')
"

echo "=== 🎉 Build completado exitosamente ==="