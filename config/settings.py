import os
from pathlib import Path
import environ

# Определяем корневую директорию проекта (vitrina_shop)
BASE_DIR = Path(__file__).resolve().parent.parent

# Инициализируем библиотеку django-environ для работы с переменными окружения
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Ключи безопасности и отладки приложения
SECRET_KEY = env('SECRET_KEY', default='django-insecure-vitrina-shop-secret-key-12345')
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost', '0.0.0.0'])

# Регистрация подсистем и приложений маркетплейса
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop.apps.ShopConfig',  # Основное приложение интернет-магазина
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Конфигурация путей для HTML-шаблонов веб-приложения (SPA)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'shop' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ПОДКЛЮЧЕНИЕ БАЗЫ ДАННЫХ POSTGRESQL (УНИВЕРСАЛЬНОЕ ДЛЯ DOCKER)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='vitrina_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='secret_password_123'),
        'HOST': env('DB_HOST', default='db'),  # Смотрит на контейнер db из docker-compose
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Валидация паролей пользователей СУБД
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Настройки локализации системы интернет-магазина
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Yekaterinburg' # Выставляет время Екатеринбурга/Уфы (UTC+5)
USE_I18N = True
USE_TZ = True

# Настройки статических файлов фронтенда (CSS, JS, Иконки)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'shop' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# УНИВЕРСАЛЬНАЯ НАСТРОЙКА КЭШИРОВАНИЯ REDIS ДЛЯ DOCKER

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        # Сначала пробуем взять REDIS_URL из окружения докера,
        # а если его нет — по умолчанию смотрим на имя контейнера 'redis' вместо 127.0.0.1
        "LOCATION": env('REDIS_URL', default="redis://redis:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "protocol": 2,  # Отключает команду 'HELLO' для образов Alpine Linux
            "socket_timeout": 0.5,
            "socket_connect_timeout": 0.5,
        }
    }
}


# Хранение и кэширование сессий авторизации покупателей в Redis
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Настройки загружаемых медиафайлов (картинки смартфонов и галерея)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'












