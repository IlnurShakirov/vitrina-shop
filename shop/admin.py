from django.contrib import admin
from django.db import models
from django.forms import Textarea
from .models import Category, Product, Review, CartItem, UserProfile, ProductImage
from django.core.cache import cache


# 1. КЛАСС ГАЛЕРЕИ ДЛЯ ЗАГРУЗКИ НЕСКОЛЬКИХ ФОТОГРАФИЙ (INLINE)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Количество пустых полей для загрузки новых фото по умолчанию
    max_num = 10 # Лимит фотографий в галерее одного смартфона


# 2. РЕГИСТРАЦИЯ МОДЕЛЕЙ В БЭК-ОФИСЕ МАГАЗИНА

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.safestring import mark_safe


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # ДОБАВЛЕНО: 'is_available' в список колонок таблицы
    list_display = ['name', 'price', 'category', 'is_popular', 'is_available', 'created_at']

    # Быстрый фильтр по наличию в правом сайдбаре админки
    list_filter = ['is_available', 'is_popular', 'category', 'created_at']

    # Возможность менять флаг "В наличии" прямо из таблицы (list_editable)
    list_editable = ['price', 'is_popular', 'is_available']

    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    inlines = [ProductImageInline]

    readonly_fields = ['generate_ai_button']

    fieldsets = (
        ('Основная информация', {
            # ДОБАВЛЕНО: 'is_available в форму редактирования карточки смартфона
            'fields': ('name', 'slug', 'category', 'price', 'is_popular', 'is_available', 'image')
        }),
        ('⚙️ Технические характеристики смартфона', {
            'fields': (
                'tech_screen', 'tech_battery', 'tech_charge',
                'tech_camera', 'tech_cpu', 'tech_memory',
                'tech_body', 'tech_os'
            )
        }),
        ('✨ Интеллектуальный бэк-офис', {
            'fields': ('generate_ai_button',),
        }),
        ('📊 Сгенерированный ИИ-перевод', {
            'classes': ('collapse',),
            'fields': ('ai_summary', 'ai_screen_simple', 'ai_battery_simple', 'ai_camera_simple', 'ai_cpu_simple',
                       'ai_body_simple'),
        }),
    )

    def generate_ai_button(self, obj):
        if obj.pk:
            return mark_safe(
                f'<a class="button" href="/admin/shop/product/{obj.pk}/generate-ai/" '
                f'style="background: #6f42c1; color: white; font-weight: bold; padding: 12px 20px; display: inline-block; border-radius: 6px; text-decoration: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                f'✨ Сгенерировать понятное описание (ИИ)</a>'
            )
        return "Сначала сохраните созданный смартфон"

    generate_ai_button.short_description = "Действие"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:product_id>/generate-ai/', self.admin_site.admin_view(self.generate_ai_description),
                 name='product-generate-ai'),
        ]
        return custom_urls + urls

    def generate_ai_description(self, request, product_id):
        product = self.get_object(request, product_id)

        if not product.tech_screen or not product.tech_battery:
            self.message_user(request, "Ошибка: Заполните базовые технические характеристики!", messages.ERROR)
            return HttpResponseRedirect("../change/")

        try:
            # --- Динамический ИИ-анализ цены и позиционирования ---
            price = float(product.price)
            if price >= 80000:
                status_text = "Бескомпромиссный флагманский девайс"
                summary_text = "Идеально подойдёт для тех, кто ищет максимальную скорость, премиальные материалы корпуса и профессиональный уровень съемки."
                cpu_text = f"Топовый чипсет '{product.tech_cpu}' и огромный запас памяти '{product.tech_memory}' означают, что смартфон с легкостью потянет любые тяжелые 3D-игры на ультра-настройках и не будет 'тупить' в режиме многозадачности."
            elif 25000 <= price < 80000:
                status_text = "Сбалансированный смартфон среднего класса"
                summary_text = "Отличный выбор по соотношению цена/качество для повседневной работы, качественных фото и плавной работы интерфейса."
                cpu_text = f"Процессор '{product.tech_cpu}' совместно с памятью '{product.tech_memory}' обеспечивают быструю работу всех повседневных приложений и стабильный запуск популярных игр."
            else:
                status_text = "Надежный бюджетный смартфон"
                summary_text = "Прекрасно подойдет для базовых задач: общения в мессенджерах, просмотра видео, навигации и стабильной связи каждый день."
                cpu_text = f"Энергоэффективный чип '{product.tech_cpu}' и память '{product.tech_memory}' оптимизированы для стабильной работы базовых программ, социальных сетей и плавного воспроизведения видео."

            # --- Динамический анализ частоты экрана (Герц) ---
            screen_lower = product.tech_screen.lower()
            if "120" in screen_lower or "144" in screen_lower:
                screen_text = f"Экран с повышенной частотой '{product.tech_screen}' обновляется в 2 раза быстрее обычного. Прокрутка ленты новостей и картинка в динамичных сценах будут идеально плавными."
            else:
                screen_text = f"Дисплей с параметрами '{product.tech_screen}' обеспечивает естественную цветопередачу и комфортен для чтения или просмотра контента при любом освещении."

            # --- Динамический анализ быстрой зарядки ---
            charge_lower = product.tech_charge.lower() if product.tech_charge else ""
            if "вт" in charge_lower:
                battery_text = f"Батареи на '{product.tech_battery}' гарантированно хватит на весь день. Благодаря поддержке быстрой зарядки '{product.tech_charge}' вам не придется долго сидеть у розетки."
            else:
                battery_text = f"Емкий аккумулятор '{product.tech_battery}' обеспечивает отличную автономность, позволяя оставаться на связи до полутора дней без подзарядки."

            # --- Динамический анализ мегапикселей камеры ---
            camera_lower = product.tech_camera.lower()
            if "200" in camera_lower or "108" in camera_lower or "50" in camera_lower:
                camera_text = f"Продвинутая камера ({product.tech_camera}) позволяет делать сверхчеткие снимки с высокой детализацией даже при плохом ночном освещении."
            else:
                camera_text = f"Камера с параметрами '{product.tech_camera}' отлично справляется со стандартными дневными снимками, сканированием документов и видеозвонками."

            # --- Сохраняем индивидуальные результаты в модель ---
            product.ai_summary = f"{status_text} {product.name} на базе {product.tech_os or 'актуальной ОС'}. {summary_text}"
            product.ai_screen_simple = screen_text
            product.ai_battery_simple = battery_text
            product.ai_camera_simple = camera_text
            product.ai_cpu_simple = cpu_text
            product.ai_body_simple = f"Продуманный корпус ({product.tech_body or 'качественные материалы'}) разработан для комфортного ежедневного использования и защиты внутренних компонентов."

            product.save()
            self.message_user(request, f"✨ Успешно! Спецификации '{product.name}' проанализированы индивидуально.",
                              messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Ошибка генерации: {str(e)}", messages.ERROR)

        return HttpResponseRedirect("../change/")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'created_at']
    search_fields = ['text', 'user__username', 'product__name']
    list_editable = ['is_approved']

    actions = ['approve_reviews', 'reject_reviews']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        print("--- АДМИНКА: Одиночный отзыв модерирован. Очистка кэша каталога... ---")
        # ИСПРАВЛЕНО: Удаляем только ключ каталога API, чтобы сессии в Redis не сбрасывались!
        cache.delete('global_categories_api')
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern("products_filter_*")

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        print("--- АДМИНКА: Отзыв удален. Очистка кэша каталога... ---")
        cache.delete('global_categories_api')
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern("products_filter_*")

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        print("--- АДМИНКА: Массовое одобрение отзывов. Очистка кэша каталога... ---")
        cache.delete('global_categories_api')
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern("products_filter_*")
        self.message_user(request, "Выбранные отзывы успешно допущены к публикации на витрине.")
    approve_reviews.short_description = "✅ Утвердить выбранные отзывы (Опубликовать)"

    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        print("--- АДМИНКА: Массовая блокировка отзывов. Очистка кэша каталога... ---")
        cache.delete('global_categories_api')
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern("products_filter_*")
        self.message_user(request, "Выбранные отзывы успешно скрыты с витрины маркетплейса.")
    reject_reviews.short_description = "❌ Заблокировать выбранные отзывы (Скрыть)"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity']
    list_filter = ['user', 'product']
    search_fields = ['user__username', 'product__name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'last_name_display', 'first_name_display', 'middle_name', 'phone', 'gender']
    search_fields = ['user__username', 'phone', 'middle_name']
    list_filter = ['gender']

    def last_name_display(self, obj):
        return obj.user.last_name
    last_name_display.short_description = 'Фамилия'

    def first_name_display(self, obj):
        return obj.user.first_name
    first_name_display.short_description = 'Имя'

from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_price', 'is_paid', 'created_at']
    list_filter = ['is_paid', 'created_at']
    search_fields = ['user__username', 'id']
    inlines = [OrderItemInline]

