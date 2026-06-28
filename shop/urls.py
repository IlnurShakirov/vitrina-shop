from django.urls import path
from . import views

# Имя приложения для пространства имен (используется как {% url 'shop:...' %})
app_name = 'shop'

urlpatterns = [
    # Главная страница: каталог товаров с фильтрацией и пагинацией
    path('', views.ProductListView.as_view(), name='product_list'),

    # Детальная страница товара (Create/Read для CRUD отзывов)
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # Маршруты для системы аутентификации и авторизации (п. 2.2.1 ТЗ)
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # AJAX-обработчик для асинхронного добавления товара в Избранное
    path('product/<int:product_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
]

