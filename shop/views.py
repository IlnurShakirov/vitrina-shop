import json
import re
import urllib.request
import os

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.cache import cache
from django.db.models import Avg, Prefetch
from django.http import JsonResponse, Http404, FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView

from .models import (
    Product, Category, Review, CartItem, UserProfile,
    Order, OrderItem, ProductImage,
)
from .forms import ReviewForm

# 1. SPA — базовый шаблон клиента
def index_view(request):
    """Отдаёт базовый SPA-шаблон для фронтенд-приложения."""
    return render(request, 'shop/index.html')

# 2. API каталога и сохранения анкеты личного кабинета
@csrf_exempt
def api_catalog(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            user = request.user
            user.last_name = data.get('last_name', '')
            user.first_name = data.get('first_name', '')
            user.email = data.get('email', '')
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.middle_name = data.get('middle_name', '')
            profile.birth_date = data.get('birth_date', None) or None
            profile.gender = data.get('gender', 'M')
            profile.phone = data.get('phone', '')
            profile.save()

            return JsonResponse({'status': 'success', 'message': 'Анкета успешно сохранена.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    categories = cache.get_or_set(
        'global_categories_api',
        lambda: list(Category.objects.values('id', 'name', 'slug')),
        3600,
    )
    popular = list(
        Product.objects.filter(is_popular=True)
        .values('id', 'name', 'price', 'slug')[:4]
    )

    queryset = Product.objects.select_related('category').filter(is_available=True)

    cat_slug = request.GET.get('category', '').strip()
    search = request.GET.get('q', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    sort_mode = request.GET.get('sort', '').strip().lower()

    if sort_mode == 'cheap':
        queryset = queryset.order_by('price')
    elif sort_mode == 'expensive':
        queryset = queryset.order_by('-price')
    elif sort_mode == 'popular':
        queryset = queryset.order_by('-is_popular', 'id')
    else:
        queryset = queryset.order_by('id')

    if cat_slug and cat_slug != '':
        queryset = queryset.filter(category__slug=cat_slug)
    if search and search != '':
        queryset = queryset.filter(name__icontains=search)
    if max_price and max_price != '':
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass

    queryset = queryset.prefetch_related('images')

    products = []
    for p in queryset:
        approved_reviews = Review.objects.filter(product=p, is_approved=True).select_related('user')

        products.append({
            'id': p.id,
            'name': p.name,
            'price': str(p.price),
            'slug': p.slug,
            'is_popular': p.is_popular,
            'image': p.image.name if p.image else '',
            'gallery': [img.image.name for img in p.images.all()],
            'tech': {
                'screen': p.tech_screen or '',
                'battery': p.tech_battery or '',
                'charge': p.tech_charge or '',
                'camera': p.tech_camera or '',
                'cpu': p.tech_cpu or '',
                'memory': p.tech_memory or '',
                'body': p.tech_body or '',
                'os': p.tech_os or '',
            },
            'ai_simple': {
                'summary': p.ai_summary or 'Описание ещё не сгенерировано.',
                'screen': p.ai_screen_simple or '',
                'battery': p.ai_battery_simple or '',
                'camera': p.ai_camera_simple or '',
                'cpu': p.ai_cpu_simple or '',
                'body': p.ai_body_simple or '',
            },
            'mid_rating': p.mid_rating,
            'reviews': [{
                'id': r.id,
                'username': str(r.user.username),
                'rating': int(r.rating),
                'text': str(r.text).strip(),
                'date': r.created_at.strftime('%d.%m.%Y')
            } for r in approved_reviews],
        })

    user_data = None
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user_orders = []
        orders_qs = Order.objects.filter(user=request.user).order_by('-created_at')

        for o in orders_qs:
            items_list = []
            for item in o.items.all():
                items_list.append(f"{item.product.name} ({item.quantity} шт.)")

            user_orders.append({
                'id': o.id,
                'total_price': str(o.total_price),
                'is_paid': o.is_paid,
                'date': o.created_at.strftime('%d.%m.%Y в %H:%M'),
                'items': items_list
            })

        user_data = {
            'username': request.user.username,
            'last_name': request.user.last_name,
            'first_name': request.user.first_name,
            'email': request.user.email,
            'middle_name': profile.middle_name,
            'birth_date': str(profile.birth_date) if profile.birth_date else '',
            'gender': profile.gender,
            'phone': profile.phone,
            'date_joined': request.user.date_joined.strftime('%d %B %Y года'),
            'orders': user_orders,
        }

    return JsonResponse({
        'categories': categories,
        'popular_products': popular,
        'products': products,
        'user': user_data,
    })

# 3. Корзина и оформление заказа
@csrf_exempt
@login_required
def api_cart(request):
    if request.method == 'GET':
        items = CartItem.objects.filter(user=request.user).select_related('product')
        cart_data = [{
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'price': str(item.product.price),
            'quantity': item.quantity,
        } for item in items]
        return JsonResponse({'cart': cart_data})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'status': 'error', 'message': 'Некорректный JSON'}, status=400)

        product_id = data.get('product_id')
        action = data.get('action', 'add')

        if not product_id:
            return JsonResponse({'status': 'error', 'message': 'Не указан product_id'}, status=400)

        product = get_object_or_404(Product, id=product_id)
        item, created = CartItem.objects.get_or_create(user=request.user, product=product)

        if action == 'remove':
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
                return JsonResponse({'status': 'decreased', 'message': 'Количество уменьшено'})
            else:
                item.delete()
                return JsonResponse({'status': 'removed', 'message': 'Товар удалён из корзины'})
        elif action == 'delete_all':
            item.delete()
            return JsonResponse({'status': 'deleted', 'message': 'Товар полностью удалён из корзины'})
        else:
            if not created:
                item.quantity += 1
                item.save()
            return JsonResponse({'status': 'added', 'message': 'Товар добавлен в корзину'})

    elif request.method == 'DELETE':
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        if not cart_items.exists():
            return JsonResponse({'status': 'error', 'message': 'Корзина пуста, нечего оформлять!'}, status=400)

        total = sum(item.product.price * item.quantity for item in cart_items)
        order = Order.objects.create(user=request.user, total_price=total, is_paid=True)

        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, price=item.product.price, quantity=item.quantity)
        cart_items.delete()

        return JsonResponse({'status': 'paid', 'message': f'Оплата прошла успешно! Создан заказ №{order.id} на сумму {total} ₽.'})
    return JsonResponse({'status': 'error', 'message': 'Метод не поддерживается'}, status=405)

# 3.1 Избранное
@login_required
def api_favorites_list(request):
    products = Product.objects.filter(favorites=request.user)
    fav_data = [{'id': p.id, 'name': p.name, 'price': str(p.price), 'slug': p.slug} for p in products]
    return JsonResponse({'favorites': fav_data})

@csrf_exempt
def api_toggle_favorite(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Войдите в аккаунт.'}, status=401)
    product = get_object_or_404(Product, id=product_id)
    if product.favorites.filter(id=request.user.id).exists():
        product.favorites.remove(request.user)
        is_fav = False
    else:
        product.favorites.add(request.user)
        is_fav = True
    return JsonResponse({'status': 'ok', 'is_favorite': is_fav})

# 4. Авторизация, регистрация и демо-входы
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('shop:index')
    else:
        form = UserCreationForm()
    return render(request, 'shop/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('shop:index')
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('shop:index')

def login_as_admin(request):
    from django.contrib.auth.models import User
    user = User.objects.filter(is_superuser=True).first()
    if user:
        login(request, user)
    return redirect('shop:index')

def login_as_client(request):
    from django.contrib.auth.models import User
    user, created = User.objects.get_or_create(username='client_test', defaults={'is_superuser': False})
    if created:
        user.set_password('secret_password_123')
        user.save()
    login(request, user)
    return redirect('shop:index')


@csrf_exempt
@login_required
def api_add_review(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не поддерживается'}, status=405)
    try:
        data = json.loads(request.body)
        rating = int(data.get('rating', 5))
        text = data.get('text', '').strip()
        if not text:
            return JsonResponse({'status': 'error', 'message': 'Напишите текст вашего отзыва'}, status=400)

        bad_words = ['хуй', 'хуе', 'хуи', 'пезд', 'пизд', 'ебан', 'ебат', 'ебн', 'бля', 'сука', 'мудак', 'говно',
                     'дебил']
        text_lower = text.lower()
        for bad_root in bad_words:
            if bad_root in text_lower:
                return JsonResponse({'status': 'error', 'message': 'Обнаружена ненормативная лексика.'}, status=400)

        product = get_object_or_404(Product, id=product_id)
        Review.objects.create(product=product, user=request.user, text=text, rating=rating, is_approved=False)
        cache.delete('global_categories_api')
        return JsonResponse({'status': 'success', 'message': 'Отзыв отправлен на модерацию.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# 5. Классические CBV (для совместимости со серверным рендерингом)
class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12


class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'


@csrf_exempt
@login_required
def api_ai_recommend(request):
    """Железобетонный гибридный e-commerce подборщик с разделением контекста.
    Исключает дублирование интернета/склада и защищен от обрывов текста.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не поддерживается'}, status=405)

    try:
        data = json.loads(request.body)
        user_query = data.get('text', '').strip()

        if not user_query:
            return JsonResponse({'status': 'error', 'message': 'Запрос пуст'}, status=400)

        # Извлечение бюджета из текста запроса покупателя
        prices_found = [int(x) for x in re.findall(r'\d+', user_query)]
        max_price_limit = next((p for p in prices_found if p >= 1000), None)

        # 🌐 Глобальный контекст из мирового интернета
        live_web_context = "Флагманы Apple: iPhone 17 Pro Max (экран 6.9, чип A19 Pro). Бюджетные: Samsung Galaxy A26 5G, iPhone 12 mini."

        # 📦 Выгрузка локального контекста нашего склада из PostgreSQL
        all_products = Product.objects.filter(is_available=True)

        query_lower = user_query.lower()

        # ИСПРАВЛЕНО: Сверхточные триггеры по усеченным корням слов (ловит любые падежи: 'для школьника', 'ребенку'!)
        is_budget_query = any(
            w in query_lower for w in ['школьн', 'ребен', 'ребён', 'дет', 'недорог', 'дешев', 'бюджет'])
        is_battery_query = any(w in query_lower for w in
                               ['разъезд', 'командировк', 'батаре', 'заряд', 'автономн', 'емкост', 'суток', 'дня'])
        is_apple_query = any(w in query_lower for w in ['apple', 'iphone', 'айфон', 'айфонка'])
        is_android_query = any(w in query_lower for w in
                               ['андроид', 'android', 'самсунг', 'samsung', 'huawei', 'хуавей', 'техно', 'tecno',
                                'xiaomi', 'сяоми'])

        # Принудительная фильтрация бюджета для детских/бюджетных запросов (скрываем все флагманы дороже 40 000 руб!)
        if is_budget_query:
            all_products = all_products.filter(price__lte=40000)

        # Применяем изолированную фильтрацию склада PostgreSQL
        if is_android_query:
            if is_battery_query:
                filtered_products = all_products.filter(name__icontains='Samsung') | all_products.filter(
                    name__icontains='Huawei')
            else:
                filtered_products = all_products.exclude(name__icontains='iPhone').exclude(name__icontains='Apple')
        elif is_apple_query:
            if is_battery_query:
                filtered_products = all_products.filter(name__icontains='iPhone').filter(name__icontains='Pro Max')
            else:
                filtered_products = all_products.filter(name__icontains='iPhone')
        elif is_battery_query:
            filtered_products = all_products.filter(name__icontains='Samsung')
        else:
            filtered_products = all_products.filter(is_popular=True)

        # Собираем ID отфильтрованных товаров
        matched_ids = [p.id for p in filtered_products]

        # Защитный фоллбэк: если после фильтрации по бюджету склад пуст
        if not matched_ids:
            filtered_products = Product.objects.filter(is_available=True,
                                                       price__lte=40000) if is_budget_query else Product.objects.filter(
                is_available=True)
            matched_ids = [p.id for p in filtered_products]

        # Формируем список наших товаров строго для Шага 2
        db_context = "\n".join([f"[ТОВАР СТРОКА]: {p.name} (Цена: {int(p.price)} руб)" for p in filtered_products])

        system_prompt = (
            "Ты — опытный ИИ-консультант маркетплейса «Смартфон Shop».\n"
            "Напиши подробный, развернутый ответ для покупателя СТРОГО на русском языке.\n"
            "Наши клиенты — обычные люди, школьники и пожилые граждане. Пиши максимально понятно и просто, без англицизмов.\n\n"
            f"Запрос клиента: \"{user_query}\"\n\n"
            "ПРАВИЛО ДЛЯ ШАГА 1 (ГЛОБАЛЬНЫЙ РЫНОК):\n"
            "Опиши общие мировые тренды интернета по этому запросу. ОБЯЗАТЕЛЬНО приведи в пример 2 классные модели, которых НЕТ в нашем магазине (например, Google Pixel 7 Pro, Xiaomi Redmi Note 12 Pro+ или OnePlus). Опиши их технологии.\n\n"
            "ПРАВИЛО ДЛЯ ШАГА 2 (НАШ МАГАЗИН):\n"
            f"А из того, что есть в наличии на нашем личном складе прямо сейчас, мы выведем на витрину вот эти модели:\n{db_context}\n"
            "Подробно объясни простым языком в 3-4 предложениях, почему именно эти наши товары со склада идеально подходят под проблему клиента. Распиши пользу их характеристик.\n\n"
            "СТРОГИЙ ПОРЯДОК ОФОРМЛЕНИЯ ТЕКСТА:\n"
            "Шаг 1. ОБЗОР МИРОВЫХ МОДЕЛЕЙ (ИНТЕРНЕТ):\n"
            "[Твой текст обзора рынка]\n\n"
            "Шаг 2. 🛒 А из того, что есть в наличии в нашем магазине прямо сейчас, лучше всего купить:\n"
            "[Твой текст обоснования наших моделей со склада]"
        )

        ollama_url = "http://vitrina_ai_ollama:11434/api/generate"
        payload = {
            "model": "llama3.2",
            "prompt": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "repeat_penalty": 1.3,
                "num_predict": 550
            }
        }

        clean_verdict = ""
        try:
            req = urllib.request.Request(ollama_url, data=json.dumps(payload).encode('utf-8'),
                                         headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=45) as response:
                ai_response = json.loads(response.read().decode('utf-8'))
                raw_verdict = ai_response.get('response', '').strip()

                # ИСПРАВЛЕНО: Сквозной очиститель текста от любых капризных англицизмов Лламы
                replacements = {
                    r'(?i)Обозначение:.*?Шаг 1\.': 'Шаг 1.',
                    r'(?i)Обозначения:.*?Шаг 1\.': 'Шаг 1.',
                    r'[^а-яА-Яa-zA-Z0-9\s]rtfon': 'Смартфон',
                    r'[^а-яА-Яa-zA-Z0-9\s]smartfon': 'Смартфон',
                    r'smartfon': 'смартфон',
                    r'smartfony': 'смартфоны',
                    r'smarfon': 'смартфон',
                    r'phone': 'телефон',
                    r'(?i)perfect': 'идеальный',
                    r'(?i)popularity': 'популярность',
                    r'(?i)reviews': 'отзывы',
                    r'(?i)long-lasting': 'мощный',
                    r'(?i)high-end': 'премиальный флагман',
                    r'(?i)good': 'хороший',
                    r'(?i)excellent camera': 'отличная камера',
                    r'(?i)advanced camera features': 'продвинутые возможности камеры',
                    r'(?i)excellent battery life': 'отличное время автономной работы',
                    r'(?i)excellent': 'отличный',
                    r'(?i)affordable': 'доступный по цене',
                    r'(?i)display': 'экран',
                    r'(?i)chipset': 'процессор',
                    r'(?i)processor': 'процессор',
                    r'(?i)of RAM': 'оперативной памяти',
                    r'(?i)internal storage': 'встроенной памяти',
                    r'(?i)advanced features': 'продвинутые возможности',
                    r'(?i)flagship': 'флагман',
                    r'(?i)significantly': 'значительно',
                    r'(?i)boasts': 'оснащен',
                    r'(?i)choice': 'выбор',
                    r'(?i)watch video': 'смотреть видео',
                    r'(?i)listen music': 'слушать музыку',
                    r'\brub\b': 'руб.',
                    r'\bруб\b': 'руб.'
                }

                for eng_word, rus_word in replacements.items():
                    raw_verdict = re.sub(eng_word, rus_word, raw_verdict)

                clean_verdict = raw_verdict.replace('\n', '<br>')
                clean_verdict = re.sub(r'(<br\s*/?>\s*){2,}', '<br><br>', clean_verdict)
                clean_verdict = re.sub(r'(Шаг\s*\d+:.*?)(?:<br>|$)', r'<b>\1</b><br>', clean_verdict)
        except Exception as ollama_err:
            print(f"--- Автономный режим подбора: {str(ollama_err)} ---")
            clean_verdict = "<b>Шаг 1. ОБЗОР МИРОВЫХ МОДЕЛЕЙ (ИНТЕРНЕТ):</b><br>Современные тренды диктуют спрос на повышенную автономность, качественные экраны и процессоры с ИИ-ядрами.<br><br><b>🛒 А из того, что есть в наличии в нашем магазине прямо сейчас, лучше всего купить:</b><br>Рекомендуем обратить внимание на представленные ниже модели, полностью соответствующие вашему семантическому запросу."

        # Вычисляем финальную цену для ползунка фильтра на фронтенде
        final_price_slider = 200000
        if max_price_limit:
            final_price_slider = max_price_limit
        elif matched_ids:
            matched_products = Product.objects.filter(id__in=matched_ids)
            if matched_products.exists():
                final_price_slider = int(max(p.price for p in matched_products))

        if not final_price_slider:
            final_price_slider = 200000

        return JsonResponse({
            'status': 'success',
            'matched_ids': matched_ids,
            'verdict': clean_verdict,
            'suggested_price': final_price_slider
        })

    except Exception as e:
        print(f"--- КРИТИЧЕСКИЙ СБОЙ ИИ-ДВИЖКА: {str(e)} ---")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=200)


# --- ВЫДАЧА PDF ТОВАРНЫХ ЧЕКОВ НА REPORTLAB ---
from .utils import generate_order_pdf


@login_required
def download_order_receipt(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        raise Http404("Заказ не найден")

    items = order.items.all()
    from django.contrib.auth.models import User

    translit_map = {
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E', 'Ж': 'Zh', 'З': 'Z',
        'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R',
        'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z',
        'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }

    admin_user = User.objects.filter(is_superuser=True, is_active=True).first()

    if admin_user and admin_user.last_name and admin_user.first_name:
        raw_last = admin_user.last_name.strip()
        raw_first = admin_user.first_name.strip()
        profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        raw_middle = profile.middle_name.strip() if profile.middle_name else ""

        first_init = f"{raw_first}." if raw_first else ""
        middle_init = f"{raw_middle}." if raw_middle else ""
        russian_fio = f"{raw_last} {first_init}{middle_init}"
        admin_name = "".join([translit_map.get(char, char) for char in russian_fio])
    elif admin_user:
        admin_name = "".join([translit_map.get(char, char) for char in admin_user.username])
    else:
        admin_name = "Smartphone Shop Systems"

    temp_dir = "/tmp/receipts"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"receipt_order_{order.id}.pdf")

    generate_order_pdf(file_path, order, items, admin_name)

    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_order_{order.id}.pdf"'
    return response



