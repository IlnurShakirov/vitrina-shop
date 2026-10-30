from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Главная страница: Отдает единственный HTML-файл (SPA)
    path('', views.index_view, name='index'),

    # Маршруты для системы аутентификации и авторизации клиентов
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # МГНОВЕННЫЙ ВХОД ДЛЯ ДЕМОНСТРАЦИИ КОМИССИИ ДИПЛОМА
    path('login-as-admin/', views.login_as_admin, name='login_as_admin'),
    path('login-as-client/', views.login_as_client, name='login_as_client'),

    # Серверная часть (Backend API): отдают чистый JSON для скрипта app.js
    path('api/catalog/', views.api_catalog, name='api_catalog'),
    path('api/cart/', views.api_cart, name='api_cart'),

    # API для получения списка избранного покупателя
    path('api/favorites/', views.api_favorites_list, name='api_favorites_list'),

    # Префикс изменен на 'api/favorites/toggle/...', чтобы точно соответствовать fetch-запросам из app.js
    path('api/favorites/toggle/<int:product_id>/', views.api_toggle_favorite, name='api_toggle_favorite'),

    # Запасной роут-перехватчик старого кэша фронтенда (обрабатывает GET /api/favorite/ID/)
    path('api/favorite/<int:product_id>/', views.api_toggle_favorite, name='old_toggle_favorite'),

    path('api/products/<int:product_id>/review/', views.api_add_review, name='api_add_review'),

    # ТОЧКА ВХОДА ДЛЯ СЕМАНТИЧЕСКОГО ИИ-АНАЛИЗАТОРА ТОВАРОВ ИЗ ТЗ
    path('api/ai-recommend/', views.api_ai_recommend, name='api_ai_recommend'),

    # Маршрут для скачивания PDF чеков из Личного Кабинета
    path('order/<int:order_id>/pdf/', views.download_order_receipt, name='download_order_receipt'),

]


