#!/usr/bin/env bash
set -e

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

echo "import os; from django.contrib.auth import get_user_model; User = get_user_model(); username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin'); email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com'); password = os.environ.get('DJANGO_SUPERUSER_PASSWORD'); if password: user, created = User.objects.get_or_create(username=username, defaults={'email': email}); user.set_password(password); user.is_superuser = True; user.is_staff = True; user.save(); print('Superusuario configurado') else: print('Contraseña no definida')" | python manage.py shell