import os
from django.core.wsgi import get_wsgi_application

# Указываем путь к настройкам проекта
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем WSGI-приложение, которое ищет Django
application = get_wsgi_application()
