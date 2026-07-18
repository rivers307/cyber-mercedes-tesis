#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Crear o actualizar superusuario de forma segura
if [[ -n "$DJANGO_SUPERUSER_USERNAME" && -n "$DJANGO_SUPERUSER_PASSWORD" ]]; then
    python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
username = '$DJANGO_SUPERUSER_USERNAME';
password = '$DJANGO_SUPERUSER_PASSWORD';
email = '$DJANGO_SUPERUSER_EMAIL' or '';
try:
    user = User.objects.get(username=username);
    user.set_password(password);
    user.is_superuser = True;
    user.is_staff = True;
    user.email = email if email else user.email;
    user.save();
    print(f'Superusuario \"{username}\" actualizado correctamente.');
except User.DoesNotExist:
    User.objects.create_superuser(username=username, email=email, password=password);
    print(f'Superusuario \"{username}\" creado correctamente.');
"
fi