from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория товаров"
        verbose_name_plural = "Категории товаров"


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    favorites = models.ManyToManyField(User, blank=True, related_name='favorite_products')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Изображение товара')

    # --- ⚙️ ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ ---
    tech_screen = models.CharField(max_length=100, blank=True, verbose_name="Экран")
    tech_battery = models.CharField(max_length=100, blank=True, verbose_name="Батарея")
    tech_charge = models.CharField(max_length=100, blank=True, verbose_name="Быстрая зарядка")
    tech_camera = models.CharField(max_length=100, blank=True, verbose_name="Основная камера")
    tech_cpu = models.CharField(max_length=100, blank=True, verbose_name="Процессор")
    tech_memory = models.CharField(max_length=100, blank=True, verbose_name="Память")
    tech_body = models.CharField(max_length=100, blank=True, verbose_name="Корпус и защита")
    tech_os = models.CharField(max_length=100, blank=True, verbose_name="Операционная система")

    # --- ✨ ИИ-ХАРАКТЕРИСТИКИ ---
    ai_summary = models.TextField(blank=True, verbose_name="ИИ: Краткое резюме")
    ai_screen_simple = models.TextField(blank=True, verbose_name="ИИ: Экран")
    ai_battery_simple = models.TextField(blank=True, verbose_name="ИИ: Батарея")
    ai_camera_simple = models.TextField(blank=True, verbose_name="ИИ: Камера")
    ai_cpu_simple = models.TextField(blank=True, verbose_name="ИИ: Скорость работы")
    ai_body_simple = models.TextField(blank=True, verbose_name="ИИ: Надежность корпуса")

    # Флаг доступности товара на складе (указывается администратором)
    is_available = models.BooleanField(default=True, verbose_name="В наличии")


    # Динамический расчет рейтинга на основе ТОЛЬКО одобренных модератором отзывов
    @property
    def mid_rating(self):
        approved_reviews = self.reviews.filter(is_approved=True)
        if approved_reviews.exists():
            return round(sum(r.rating for r in approved_reviews) / approved_reviews.count(), 1)
        return 0.0

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Смартфон / Товар"
        verbose_name_plural = "Каталог смартфонов"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField(verbose_name="Текст отзыва")
    # Валидация рейтинга строго от 1 до 5 звезд
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка (1-5)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Флаг модерации. Новый отзыв скрыт (False), пока админ не одобрит его в панели
    is_approved = models.BooleanField(default=False, verbose_name="Одобрен модератором")

    class Meta:
        verbose_name = "Отзыв о товаре"
        verbose_name_plural = "Отзывы покупателей"
        ordering = ['-created_at']


# Новая модель корзины
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    class Meta:
        verbose_name = "Активный заказ (Товар в корзине)"
        verbose_name_plural = "Текущие заказы клиентов"


# Создаем таблицу профиля
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    birth_date = models.CharField(max_length=20, blank=True, verbose_name="Дата рождения")
    gender = models.CharField(max_length=2, default='M', verbose_name="Пол")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")

    def __str__(self):
        return f"Профиль для {self.user.username}"

    class Meta:
        verbose_name = "Анкета личного кабинета"
        verbose_name_plural = "Клиентская база (Профили)"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Товар")
    image = models.ImageField(upload_to='products/gallery/', verbose_name="Фотография")

    class Meta:
        verbose_name = "Дополнительное фото"
        verbose_name_plural = "Галерея фотографий товара"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Покупатель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время заказа")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Итоговая сумма")
    is_paid = models.BooleanField(default=True, verbose_name="Статус оплаты")

    def __html__(self):
        return f"Заказ №{self.id} от {self.created_at.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = "Оформленный заказ"
        verbose_name_plural = "История заказов (Покупки в СУБД)"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Смартфон")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена при покупке")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


