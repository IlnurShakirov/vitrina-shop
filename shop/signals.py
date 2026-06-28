#Для автоматического сброса закэшированных данных при изменении товаров или категорий в админ-панели используем сигналы post_save и post_delete

# shop/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, Category

@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    # Удаляем кэш блоков главной страницы
    cache.delete('popular_products_block')
    cache.delete('new_products_block')
    # Очищаем кэш фильтрации (поскольку ключи динамические, можно использовать паттерны, если бэкенд Redis)
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern("products_filter_*")

@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    cache.delete('global_categories')
