from django.views.generic import ListView, DetailView
from django.core.cache import cache
from django.db.models import Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product, Category, Review
from .forms import ReviewForm


class ProductListView(ListView):
    """
    Представление каталога товаров с поддержкой пагинации,
    фильтрации и низкоуровневого кэширования тяжелых запросов.
    """
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        # Получаем параметры фильтрации из GET-запроса
        category_slug = self.request.GET.get('category')
        max_price = self.request.GET.get('max_price')
        search_query = self.request.GET.get('q')

        # Формируем уникальный ключ кэша на основе фильтров
        cache_key = f"products_filter_{category_slug}_{max_price}_{search_query}"
        queryset = cache.get(cache_key)

        if queryset is None:
            # Оптимизируем SQL-запрос через select_related для связи с категориями.
            # Фильтрация по 'is_available' удалена, так как этого поля нет в модели.
            queryset = Product.objects.select_related('category').all()


            # Применяем существующие фильтры к QuerySet
            if category_slug:
                queryset = queryset.filter(category__slug=category_slug)
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            if search_query:
                queryset = queryset.filter(name__icontains=search_query)

            # Переводим в список, чтобы выполнить запрос и сохранить в кэш
            queryset = list(queryset)
            cache.set(cache_key, queryset, 60 * 15)  # Кэш на 15 минут

        # ListView автоматически разобьет этот список на страницы по 12 элементов
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Кэшируем список родительских категорий с подкатегориями на 1 час
        context['categories'] = cache.get_or_set(
            'global_categories',
            lambda: list(Category.objects.filter(parent=None).prefetch_related('children')),
            3600
        )

        # 2. Кэшируем блок "Популярные товары" на 10 минут
        context['popular_products'] = cache.get_or_set(
            'popular_products_block',
            lambda: list(Product.objects.select_related('category').filter(is_popular=True)[:4]),
            600
        )

        return context


class ProductDetailView(DetailView):
    """
    Детальная страница товара с выводом оптимизированного списка отзывов,
    обработкой отправки новых отзывов и проверкой статуса 'Избранное'.
    """
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        # Оптимизируем загрузку связанных моделей: категорию и отзывы вместе с авторами
        return Product.objects.select_related('category').prefetch_related(
            Prefetch('reviews', queryset=Review.objects.select_related('user'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаем пустую форму отзыва, настроенную в forms.py
        context['review_form'] = ReviewForm()

        # Проверяем, добавлен ли данный товар в избранное текущим пользователем
        if self.request.user.is_authenticated:
            context['is_favorite'] = self.object.favorites.filter(id=self.request.user.id).exists()
        return context

    def post(self, request, *args, **kwargs):
        """Обработка отправки формы нового отзыва авторизованным пользователем (Create в CRUD)"""
        if not request.user.is_authenticated:
            return redirect('shop:login')

        self.object = self.get_object()
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.product = self.object
            review.user = request.user
            review.save()
            return redirect('shop:product_detail', slug=self.object.slug)

        # Если форма невалидна, возвращаем страницу с ошибками валидации
        context = self.get_context_data(object=self.object)
        context['review_form'] = form
        return self.render_to_response(context)


# =====================================================================
# Контроллеры для Аутентификации, Авторизации и Регистрации (п. 2.2.1 ТЗ)
# =====================================================================

def register_view(request):
    """Регистрация нового аккаунта через встроенную форму Django"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматический вход после успешной регистрации
            return redirect('shop:product_list')
    else:
        form = UserCreationForm()
    return render(request, 'shop/register.html', {'form': form})


def login_view(request):
    """Аутентификация и вход в систему"""
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('shop:product_list')
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})


def logout_view(request):
    """Выход пользователя из учетной записи"""
    if request.method == 'POST' or request.method == 'GET':
        logout(request)
    return redirect('shop:product_list')


# =====================================================================
# Дополнительный AJAX-контроллер (Асинхронное Избранное)
# =====================================================================

@login_required
def toggle_favorite(request, product_id):
    """Добавление/удаление товара из избранного без перезагрузки всей страницы"""
    product = get_object_or_404(Product, id=product_id)
    if product.favorites.filter(id=request.user.id).exists():
        product.favorites.remove(request.user)
        is_favorite = False
    else:
        product.favorites.add(request.user)
        is_favorite = True
    return JsonResponse({'status': 'ok', 'is_favorite': is_favorite})
