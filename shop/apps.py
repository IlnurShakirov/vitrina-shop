from django.apps import AppConfig
from django.contrib import admin

class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    verbose_name = 'Управление магазином «Смартфон Shop»'  # Красивое имя блока в админке

    def ready(self):
        # Полная кастомизация текстов и заголовков админки под бэк-офис магазина
        admin.site.site_header = 'Панель управления «Смартфон Shop»'
        admin.site.site_title = 'Бэк-офис Персонала'
        admin.site.index_title = 'Добро пожаловать в систему управления маркетплейсом'
