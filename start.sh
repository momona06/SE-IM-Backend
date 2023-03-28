#!/bin/sh
python3 manage.py makemigrations UserManage
python3 manage.py migrate

# python3 manage.py runserver 80
uwsgi --module=DjangoHW.wsgi:application \
      --env DJANGO_SETTINGS_MODULE=DjangoHW.settings \
      --master \
      --http=0.0.0.0:80 \
      --processes=5 \
      --harakiri=20 \
      --max-requests=5000 \
      --vacuum