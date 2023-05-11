#!/bin/sh
python3 manage.py makemigrations
python3 manage.py migrate

daphne IM_Backend.asgi:application -b 0.0.0.0 -p 80
#python3 manage.py runserver 80

#uwsgi --module=IM_Backend.wsgi:application \
#      --env DJANGO_SETTINGS_MODULE=IM_Backend.settings \
#      --master \
#      --http=0.0.0.0:80 \
#      --processes=5 \
#      --harakiri=20 \
#      --max-requests=5000 \
#      --vacuum