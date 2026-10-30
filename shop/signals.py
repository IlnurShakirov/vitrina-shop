from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, Category, Review

@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """Сброс кэша при изменении или удалении смартфонов."""
    cache.delete('popular_products_block')
    cache.delete('new_products_block')
    cache.delete('global_categories_api')
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern("products_filter_*")


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """Сброс кэша при изменении структуры категорий в PostgreSQL."""
    cache.delete('global_categories_api')


@receiver([post_save, post_delete], sender=Review)
def invalidate_review_cache(sender, instance, **kwargs):

    print(f"--- СИГНАЛ: Отзыв к товару '{instance.product.name}' изменен/модерирован. Очистка кэша... ---")

    # Для полной страховки от жесткого кэширования полностью стираем кэш
    cache.clear()

    # Дополнительно чистим паттерны, если Redis поддерживает их
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern("products_filter_*")
