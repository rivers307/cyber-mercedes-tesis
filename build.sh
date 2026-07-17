#!/usr/bin/env bash
# Salir si algún comando falla
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Recopilar archivos estáticos
python manage.py collectstatic --no-input

# Aplicar migraciones
python manage.py migrate

# Crear superusuario si se proporcionan las variables de entorno
if [[ -n "$DJANGO_SUPERUSER_USERNAME" && -n "$DJANGO_SUPERUSER_PASSWORD" ]]; then
    python manage.py createsuperuser --no-input \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL"
fi