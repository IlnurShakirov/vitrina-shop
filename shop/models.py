# shop/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children', verbose_name="Родительская категория"
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name="Категория")
    name = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="Цена")
    is_popular = models.BooleanField(default=False, verbose_name="Популярный товар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    favorites = models.ManyToManyField(User, blank=True, related_name='favorite_products', verbose_name="В избранном у")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Товар")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="Автор")
    text = models.TextField(verbose_name="Текст отзыва")
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="Оценка")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
