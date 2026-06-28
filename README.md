# Интернет-магазин "Витрина"

Веб-приложение каталога товаров с гибкой фильтрацией, системой отзывов, механизмом добавления в избранное и продвинутым кэшированием на базе Django ORM.

## Технологический стек
- Python 3.11+
- Django 5.x
- База данных: PostgreSQL / SQLite
- Кэширование: Redis

## Функционал
- **Авторизация**: Регистрация, вход, разграничение прав (только авторы удаляют свои отзывы).
- **Каталог**: Иерархические категории, фильтрация по цене, постраничная навигация (пагинация).
- **Кэширование**: Оптимизация QuerySet через `select_related`, кэширование фрагментов шаблонов (`{% cache %}`), инвалидация кэша сигналами.

## Развертывание проекта

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com
   cd vitrina-shop
   ```

2. **Cоздайте виртуальное окружение и установите зависимости:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Настройте переменные окружения:**
   Создайте файл `.env` в корне проекта по шаблону:
   ```env
   DEBUG=True
   SECRET_KEY=your_secret_key_here
   DATABASE_URL=sqlite:///db.sqlite3
   REDIS_URL=redis://127.0.0.1:6379/1
   ```

4. **Выполните миграции и соберите статику:**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

5. **Создайте суперпользователя админ-панели:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Запустите локальный сервер:**
   ```bash
   python manage.py runserver
   ```
