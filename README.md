для запуска нужно использовать:
daphne -b 0.0.0.0 -p 8000 socket_conf.asgi:application

для установки зависимостей:
pip install -r requiremtns.txt

перед запуском нужно прописать комманду:
py manage.py migrate

потом нужно создать админа:
py manage.py createsuperuser