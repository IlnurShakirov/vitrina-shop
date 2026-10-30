// ГЛОБАЛЬНАЯ ФУНКЦИЯ ДЛЯ CSRF-TOKEN (ВНЕ ОБЛАСТИ DOMContentLoaded)

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {

    // 1. ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ И ЭЛЕМЕНТЫ ИНТЕРФЕЙСА
    const productsGrid = document.getElementById('products-grid');
    const categoriesList = document.getElementById('categories-list');
    const authBlock = document.getElementById('auth-block');
    const btnFilter = document.getElementById('btn-filter');

    const cartModalEl = document.getElementById('cartModal') ? new bootstrap.Modal(document.getElementById('cartModal')) : null;
    const favModalEl = document.getElementById('favModal') ? new bootstrap.Modal(document.getElementById('favModal')) : null;
    const productDetailModalEl = document.getElementById('productDetailModal') ? new bootstrap.Modal(document.getElementById('productDetailModal')) : null;

    let currentCategory = '';
    let currentSortMode = 'popular';
    let globalUserData = null;
    let globalProductsArray = [];
    let isAiFilteredMode = false;

    // Глобальный мостик для Избранного (Защита от ReferenceError)
    window.openFavModal = function() {
        let favModal = favModalEl;
        if (!favModal) {
            const modalElement = document.getElementById('favModal') || document.getElementById('favoritesModal');
            if (modalElement) favModal = new bootstrap.Modal(modalElement);
        }

        fetch('/api/cart/')
            .then(res => res.json())
            .then(cartData => {
                const itemsInCart = cartData.cart ? cartData.cart.map(item => parseInt(item.product_id)) : [];
                return fetch('/api/favorites/')
                    .then(res => res.json())
                    .then(favData => {
                        const list = document.getElementById('fav-items-list');
                        if (!list) return;
                        let html = '';

                        if (!favData.favorites || favData.favorites.length === 0) {
                            list.innerHTML = '<div class="alert alert-info py-2 small">Ваш список избранного пока пуст 🤍</div>';
                            if (favModal) favModal.show();
                            return;
                        }

                        favData.favorites.forEach(item => {
                            const isAdded = itemsInCart.includes(parseInt(item.id));
                            const btnClass = isAdded ? 'btn-purple text-white btn-fav-go-to-cart' : 'btn-outline-success btn-fav-to-cart';
                            const btnText = isAdded ? 'В корзине ✓' : '🛒 В корзину';

                            html += '<li class="list-group-item d-flex justify-content-between align-items-center bg-white border-0 shadow-sm mb-2 rounded p-3">' +
                                    '<div><span class="fw-bold text-dark d-block">' + item.name + '</span>' +
                                    '<span class="badge bg-success mt-1">' + item.price + ' ₽</span></div>' +
                                    '<div class="btn-group">' +
                                    '<button class="btn btn-sm ' + btnClass + ' fw-bold" data-id="' + item.id + '">' + btnText + '</button>' +
                                    '<button class="btn btn-sm btn-outline-danger btn-fav-remove" data-id="' + item.id + '">❌</button>' +
                                    '</div></li>';
                        });
                        list.innerHTML = html;
                        if (favModal) favModal.show();
                    });
            })
            .catch(err => console.error('Ошибка Избранного:', err));
    };

    // 2. БАЗОВАЯ ФУНКЦИЯ ЗАГРУЗКИ КАТАЛОГА
    function loadCatalog() {
        const searchInput = document.getElementById('search-input');
        const priceInput = document.getElementById('price-input');

        const query = searchInput ? searchInput.value.trim() : '';
        const maxPrice = priceInput ? priceInput.value.trim() : '';

        const params = new URLSearchParams({
            category: currentCategory,
            q: query,
            max_price: maxPrice,
            sort: currentSortMode,
            _nocache: Date.now().toString()
        });

        fetch(`/api/catalog/?${params.toString()}`)
            .then(res => {
                if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
                return res.json();
            })
            .then(data => {
                globalUserData = data.user;
                globalProductsArray = data.products || [];

                renderAuth(data.user);

                if (categoriesList && data.categories) {
                    renderCategories(data.categories);
                }

                if (productsGrid && data.products) {
                    renderProducts(data.products);
                }
            })
            .catch(err => console.error('Ошибка загрузки каталога:', err));
    }

    // 3. ПАНЕЛЬ УПРАВЛЕНИЯ (ИКОНКИ В ШАПКЕ)
    function renderAuth(user) {
        if (!authBlock) return;

        const username = user ? user.username : null;
        let profileDropdownMenu = '';
        let html = '';

        if (username) {
            profileDropdownMenu = '<li><a class="dropdown-item fw-bold text-primary" href="#" id="go-to-profile-btn">👤 Личный кабинет</a></li>' +
                                  '<li><hr class="dropdown-divider"></li>' +
                                  '<li><form id="logout-form" action="/logout/" method="POST" style="display:none;"><input type="hidden" name="csrfmiddlewaretoken" value="' + getCookie('csrftoken') + '"></form>' +
                                  '<a class="dropdown-item fw-bold text-danger" href="#" id="logout-link">🚪 Выйти из профиля</a></li>';

            let ordersIconHtml = '';
            if (username.toLowerCase().includes('admin') || username === 'staff') {
                ordersIconHtml = '<a id="nav-orders-link" href="/admin/" class="icon-nav-link text-white text-decoration-none me-3" title="Панель бэк-офиса PostgreSQL">' +
                                 '<span>📦</span><span class="small d-block">Заказы</span></a>';
            }

            html = '<div class="dropdown me-3">' +
                   '<div class="icon-nav-link text-white text-decoration-none dropdown-toggle" id="profileMenuButton" data-bs-toggle="dropdown" aria-expanded="false" style="cursor: pointer;">' +
                   '<span>👤</span><span class="small d-block">' + username + '</span></div>' +
                   '<ul class="dropdown-menu dropdown-menu-end shadow border-0 mt-2" aria-labelledby="profileMenuButton">' + profileDropdownMenu + '</ul></div>' +
                   ordersIconHtml +
                   '<div class="icon-nav-link text-white text-decoration-none me-3" id="nav-fav-btn" style="cursor: pointer;"><span>❤️</span><span class="small d-block">Избранное</span></div>' +
                   '<div class="icon-nav-link text-white text-decoration-none" id="nav-cart-btn" style="cursor: pointer;"><span>🛒</span><span class="small d-block">Корзина</span></div>';

            authBlock.innerHTML = html;

            const cartBtn = document.getElementById('nav-cart-btn');
            const favBtn = document.getElementById('nav-fav-btn');
            const profileBtn = document.getElementById('go-to-profile-btn');

            if (cartBtn) cartBtn.addEventListener('click', openCartModal);
            if (favBtn) favBtn.addEventListener('click', window.openFavModal);
            if (profileBtn) profileBtn.addEventListener('click', openProfileTab);

            const logoutLink = document.getElementById('logout-link');
            if (logoutLink) {
                logoutLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    document.getElementById('logout-form').submit();
                });
            }
        } else {
            profileDropdownMenu = '<li><a class="dropdown-item fw-bold text-primary" href="/login-as-client/">👤 Вход для покупателей</a></li>' +
                                  '<li><a class="dropdown-item fw-bold text-danger" href="/login-as-admin/">⚙️ Вход для персонала</a></li>' +
                                  '<li><hr class="dropdown-divider"></li>' +
                                  '<li><a class="dropdown-item text-success" href="/register/">📝 Регистрация нового клиента</a></li>';

            html = '<div class="dropdown me-3">' +
                   '<div class="icon-nav-link text-white text-decoration-none dropdown-toggle" id="profileMenuButton" data-bs-toggle="dropdown" aria-expanded="false" style="cursor: pointer;">' +
                   '<span>👤</span><span class="small d-block">Войти</span></div>' +
                   '<ul class="dropdown-menu dropdown-menu-end shadow border-0 mt-2" aria-labelledby="profileMenuButton">' + profileDropdownMenu + '</ul></div>' +
                   '<div class="icon-nav-link text-white text-decoration-none" style="opacity: 0.5; cursor: not-allowed;"><span>🛒</span><span class="small d-block">Корзина</span></div>';

            authBlock.innerHTML = html;
        }
    }

// 4. ОТРИСОВКА ВИТРИНЫ КАРТОЧЕК СМАРТФОНОВ И САЙДБАРА
function renderCategories(categories) {
  if (!categoriesList) return;

  let html = '<a href="#" class="list-group-item list-group-item-action active">Все категории</a>';
  categories.forEach(cat => {
    const isSelect = (currentCategory === cat.slug && !isAiFilteredMode);
    html += `<a href="#" class="list-group-item list-group-item-action ${isSelect ? 'active' : ''}" data-slug="${cat.slug}">${cat.name}</a>`;
  });
  categoriesList.innerHTML = html;
}

function renderProducts(products) {
  if (!productsGrid) return;
  let html = '';
  const isAuth = !!globalUserData;

  products.forEach(p => {
    const isInCart = globalUserData && globalUserData.cart_ids && globalUserData.cart_ids.includes(p.id);
    const isFav = globalUserData && globalUserData.fav_ids && globalUserData.fav_ids.includes(p.id);

    const btnClass = isInCart ? 'btn-purple text-white btn-add-cart' : 'btn-success btn-add-cart';
    const btnStyle = isInCart
      ? 'background-color: #6f42c1; border-color: #6f42c1; border-radius: 12px;'
      : 'border-radius: 12px;';
    const btnText = isInCart ? 'В корзине ✓' : 'В корзину';

    const favBtnClass = isFav ? 'btn-danger' : 'btn-outline-danger';

    let imgUrl = p.image ? (p.image.startsWith('http') ? p.image : '/media/' + p.image) : '';

    const imageHtml = imgUrl
      ? `<img src="${imgUrl}" class="img-fluid rounded open-detail-trigger" data-id="${p.id}" alt="${p.name}" style="height: 180px; object-fit: contain; cursor: pointer; width: 100%;">`
      : `<div class="text-center bg-light py-4 open-detail-trigger" data-id="${p.id}" style="height: 180px; font-size: 3rem; cursor: pointer;">📱</div>`;

    const authDisabled = isAuth ? '' : 'disabled title="Войдите для покупок" style="opacity: 0.6;"';

    html += `
      <div class="col-md-4 mb-4">
        <div class="card h-100 product-card border-0 shadow-sm" style="border-radius: 15px; overflow: hidden; background-color: #ffffff;">
          <!-- ИСПРАВЛЕНО: В style принудительно добавлен position: relative !important; для жесткой фиксации координат угла -->
          <div class="p-3 text-center bg-white" style="height: 200px; display: flex; align-items: center; justify-content: center; position: relative !important;">
            ${imageHtml}
            <!-- ИСПРАВЛЕНО: Координаты выставлены в top: 12px; right: 12px;, добавлено скругление (border-radius: 50%) и аккуратная тень -->
            <button class="btn ${favBtnClass} btn-sm btn-fav position-absolute" data-id="${p.id}" ${authDisabled} style="position: absolute !important; top: 12px !important; right: 12px !important; z-index: 10; border-radius: 50% !important; width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">❤️</button>
          </div>
          <div class="card-body d-flex flex-column pt-0">
            <h5 class="card-title fw-bold text-dark mb-1 open-detail-trigger" data-id="${p.id}" style="cursor: pointer; font-size: 0.95rem; min-height: 44px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.2;">${p.name}</h5>
            <p class="card-text mb-2 text-muted small">⭐ Рейтинг: <span class="fw-bold text-dark">${p.mid_rating ? p.mid_rating.toFixed(1) : 'Нет оценок'}</span> / 5</p>
            <p class="text-success fw-bold fs-5 mb-2">${p.price} ₽</p>
            <div class="d-grid gap-2 mt-auto">
              <button class="btn btn-sm fw-bold ${btnClass}" data-id="${p.id}" style="${btnStyle}" ${authDisabled}>${btnText}</button>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  productsGrid.innerHTML = html || '<div class="col-12"><div class="alert alert-info">Товары не найдены</div></div>';
}

// 5. КОРЗИНА И ОФОРМЛЕНИЕ ЗАКАЗА
function openCartModal() {
  if (!cartModalEl) return;

  fetch('/api/cart/')
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById('cart-items-list');
      const totalPriceEl = document.getElementById('cart-total-price');
      if (!list) return;

      let html = '';
      let total = 0;

      if (!data.cart || data.cart.length === 0) {
        list.innerHTML = 'Ваша корзина пуста 🛒';
        if (totalPriceEl) totalPriceEl.textContent = '0';
        cartModalEl.show();
        return;
      }

      data.cart.forEach(item => {
        const cost = parseFloat(item.price) * item.quantity;
        total += cost;
        html += `
          <li class="list-group-item d-flex justify-content-between align-items-center">
            <div>
              <div class="fw-bold">${item.product_name}</div>
              <small class="text-muted">${item.price} ₽ / шт.</small>
            </div>
            <div class="d-flex align-items-center gap-3">
              <button class="btn btn-sm btn-outline-secondary btn-cart-minus" data-product-id="${item.product_id}">−</button>
              <span>${item.quantity} шт.</span>
              <button class="btn btn-sm btn-outline-secondary btn-cart-plus" data-product-id="${item.product_id}">+</button>
              <strong>${cost.toFixed(2)} ₽</strong>
              <button class="btn btn-sm btn-outline-danger btn-cart-delete-all" data-product-id="${item.product_id}">❌</button>
            </div>
          </li>
        `;
      });

      list.innerHTML = html;
      if (totalPriceEl) totalPriceEl.textContent = total.toFixed(2);
      cartModalEl.show();
    })
    .catch(err => console.error('Ошибка загрузки корзины:', err));
}

    window.handleAddToCart = function(productId, mainCardBtn) {
        const btnOnCard = mainCardBtn || document.querySelector('.btn-add-cart[data-id="' + productId + '"]');

        // Первый клик проверяет: если кнопка УЖЕ фиолетовая — вот ТОГДА открываем корзину!
        if (btnOnCard && (btnOnCard.textContent.includes('В корзине') || btnOnCard.classList.contains('btn-purple'))) {
            if (typeof openCartModal === 'function') openCartModal();
            return;
        }

        // Если кликаем впервые — просто асинхронно шлём POST-запрос в Django без всплывающих окон
        fetch('/api/cart/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ product_id: parseInt(productId), action: 'add' })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'added' || data.status === 'success' || data.status === 'ok') {
                if (btnOnCard) {
                    btnOnCard.className = 'btn btn-purple text-white btn-add-cart flex-grow-1 fw-bold';
                    btnOnCard.style.backgroundColor = '#6f42c1';
                    btnOnCard.style.borderColor = '#6f42c1';
                    btnOnCard.innerHTML = 'В корзине ✓';
                }
                if (globalUserData) {
                    if (!globalUserData.cart_ids) globalUserData.cart_ids = [];
                    if (!globalUserData.cart_ids.includes(parseInt(productId))) globalUserData.cart_ids.push(parseInt(productId));
                }

                // ИСПРАВЛЕНО: Автоматический вызов openCartModal() отсюда полностью УБРАН!
                // Теперь при первом клике страница остаётся неподвижной, не отвлекая покупателя.
            } else {
                alert(data.message || 'Ошибка добавления');
            }
        })
        .catch(err => console.error('Критический сбой модуля корзины:', err));
    };


window.handleToggleFavorite = function(productId, buttonElement) {
  if (!productId) return;

  fetch('/api/favorites/toggle/' + productId + '/', {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  })
    .then(res => res.json())
    .then(data => {
      if ((data.status === 'ok' || data.status === 'success') && buttonElement) {
        if (data.is_favorite) {
          buttonElement.classList.remove('btn-outline-danger');
          buttonElement.classList.add('btn-danger');
        } else {
          buttonElement.classList.remove('btn-danger');
          buttonElement.classList.add('btn-outline-danger');
        }
        loadCatalog();
      }
    })
    .catch(err => console.error('Ошибка переключения избранного:', err));
};

// 7. ЛИЧНЫЙ КАБИНЕТ С ИСТОРИЕЙ ПОКУПОК
function openProfileTab(e) {
  if (e) e.preventDefault();
  if (!globalUserData) return;

  const mainLayout = document.getElementById('app-root');
  if (!mainLayout) return;

  let ordersHtml = '<h4>📦 История ваших заказов (из СУБД)</h4>';

if (globalUserData.orders && globalUserData.orders.length > 0) {
    ordersHtml += '<ul class="list-group">';
    globalUserData.orders.forEach(order => {
      const statusBadge = order.is_paid ? 'Оплачен ✓' : 'В обработке';

      // Кнопка превращена в полноценную e-commerce ссылку с переходом на URL PDF-генератора Django
      const pdfButtonHtml = order.is_paid
        ? `<a href="/order/${order.id}/pdf/" target="_blank" class="btn btn-sm btn-outline-primary fw-bold text-decoration-none d-inline-block my-1">📄 Чек PDF</a>`
        : '';

      // ЖЕЛЕЗОБЕТОННЫЙ СДВИГ ТЕКСТОВОГО ВРЕМЕНИ НА +5 ЧАСОВ ПОД ЧАСОВОЙ ПОЯС УФЫ
      let localOrderDate = order.date;
      if (order.date && order.date.includes(':')) {
          try {
              // Вытаскиваем часы и минуты из абсолютно любой строки (например, "07:24" или "05.10.2026 07:24")
              const timeRegex = /(\d{1,2}):(\d{2})/;
              const match = order.date.match(timeRegex);

              if (match) {
                  let serverHour = parseInt(match[1], 10);
                  let serverMinute = match[2];

                  // Прибавляем 5 часов (разница между UTC сервера Docker и временем Уфы)
                  let localHour = (serverHour + 5) % 24;

                  // Форматируем часы, чтобы всегда было две цифры (например, "08", а не "8")
                  let formattedHour = localHour < 10 ? '0' + localHour : localHour;

                  // Собираем изменённое время обратно в строку даты
                  localOrderDate = order.date.replace(timeRegex, formattedHour + ':' + serverMinute);
              }
          } catch (e) {
              console.error("Ошибка текстового сдвига времени:", e);
              localOrderDate = order.date;
          }
      }

      ordersHtml += `
        <li class="list-group-item bg-white border-0 shadow-sm p-3 mb-3 rounded" style="border-radius: 12px !important;">
          <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap">
            <span class="text-dark fw-medium">Заказ #${order.id} <span class="text-muted small">от ${localOrderDate}</span></span>
            <span class="badge bg-success px-2 py-1">${statusBadge}</span>
          </div>
          <div class="d-flex align-items-center gap-2 flex-wrap mb-2">
            <span class="fw-bold text-success fs-5">${order.total_price} ₽</span>
            ${pdfButtonHtml}
          </div>
          <div class="small text-secondary mt-1"><strong>Состав заказа:</strong> ${order.items.join(', ')}</div>
        </li>
      `;
    });
    ordersHtml += '</ul>';
  } else {
    ordersHtml += '<div class="alert alert-light">Вы еще не оформили ни одного заказа. Все ваши покупки появятся здесь! 🛒</div>';
  }


  mainLayout.innerHTML = `
    <div class="profile-container">
      <a href="#" id="btn-back-to-catalog" class="btn btn-outline-secondary mb-3">&larr; Назад к покупкам</a>
      <h3>Личные данные анкеты</h3>
      <p>Управляйте настройками вашего профиля в Смартфон Shop</p>

      <form id="profile-edit-form">
        <div class="row g-3">
          <div class="col-md-4">
            <label class="form-label">ФАМИЛИЯ</label>
            <input type="text" id="p-last-name" class="form-control" value="${globalUserData.last_name || ''}">
          </div>
          <div class="col-md-4">
            <label class="form-label">ИМЯ</label>
            <input type="text" id="p-first-name" class="form-control" value="${globalUserData.first_name || ''}">
          </div>
          <div class="col-md-4">
            <label class="form-label">ОТЧЕСТВО</label>
            <input type="text" id="p-middle-name" class="form-control" value="${globalUserData.middle_name || ''}">
          </div>
          <div class="col-md-6">
            <label class="form-label">ДАТА РОЖДЕНИЯ</label>
            <input type="date" id="p-birth-date" class="form-control" value="${globalUserData.birth_date || ''}">
          </div>
          <div class="col-md-6">
            <label class="form-label">ПОЛ</label>
            <select id="p-gender" class="form-select">
              <option value="M" ${globalUserData.gender === 'M' ? 'selected' : ''}>Мужской</option>
              <option value="W" ${globalUserData.gender === 'W' ? 'selected' : ''}>Женский</option>
            </select>
          </div>
          <div class="col-12">
            <label class="form-label">📱 НОМЕР ТЕЛЕФОНА</label>
            <!-- ИСПРАВЛЕНО: Возвращен рабочий ID и динамическое заполнение из БД -->
            <input type="tel" id="p-phone" class="form-control" value="${globalUserData.phone || ''}" placeholder="+7 (900) 000-00-00">
          </div>
          <div class="col-12">
            <label class="form-label">✔ E-MAIL АДРЕС</label>
            <!-- ИСПРАВЛЕНО: Возвращен рабочий ID и динамическое заполнение из БД -->
            <input type="email" id="p-email" class="form-control" value="${globalUserData.email || ''}" placeholder="example@mail.ru">
          </div>
        </div>
        <button type="submit" id="btn-save-profile" class="btn btn-primary mt-3">💾 Сохранить анкету</button>
      </form>

      ${ordersHtml}

      <hr class="my-4">
      <form id="profile-logout-form" action="/logout/" method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
        <button type="button" id="profile-logout-btn" class="btn btn-outline-danger">Выйти из профиля</button>
      </form>
    </div>
  `;


  document.getElementById('btn-back-to-catalog').addEventListener('click', () => { location.reload(); });
  document.getElementById('profile-logout-btn').addEventListener('click', (ev) => {
    ev.preventDefault();
    document.getElementById('profile-logout-form').submit();
  });

  document.getElementById('profile-edit-form').addEventListener('submit', event => {
    event.preventDefault();
    const btnSave = document.getElementById('btn-save-profile');
    if (btnSave) btnSave.disabled = true;

    const updatedData = {
      last_name: document.getElementById('p-last-name').value.trim(),
      first_name: document.getElementById('p-first-name').value.trim(),
      middle_name: document.getElementById('p-middle-name').value.trim(),
      birth_date: document.getElementById('p-birth-date').value,
      gender: document.getElementById('p-gender').value,
      phone: document.getElementById('p-phone').value.trim(),
      email: document.getElementById('p-email').value.trim()
    };

    fetch('/api/catalog/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(updatedData)
    })
      .then(res => res.json())
      .then(resp => { alert(resp.message); loadCatalog(); })
      .catch(err => console.error(err))
      .finally(() => { if (btnSave) btnSave.disabled = false; });
  });
}

// 8. ДЕТАЛЬНЫЙ ПРОСМОТР СМАРТФОНА (ИСПРАВЛЕНО: ВСЕ ПЕРЕМЕННЫЕ `product`)
window.openProductDetailModal = function(productId) {
    fetch('/api/catalog/?q=&category=&max_price=')
        .then(res => res.json())
        .then(data => {
            const product = data.products.find(p => p.id == productId);
            if (!product) return;

            document.getElementById('modal-product-name').textContent = product.name;
            document.getElementById('modal-product-price').textContent = product.price + " ₽";

            const ratingValEl = document.getElementById('modal-product-rating-val');
            if (ratingValEl) ratingValEl.textContent = product.mid_rating ? product.mid_rating.toFixed(1) : '0.0';

            const reviewsContainer = document.getElementById('modal-reviews-list');
            if (reviewsContainer) {
                let revHtml = '';
                if (product.reviews && product.reviews.length > 0) {
                    product.reviews.forEach(r => {
                        const commentText = r.text ? r.text : '(Текст отзыва пуст)';
                        revHtml += '<div class="p-2 mb-2 bg-white border border-warning rounded shadow-sm" style="border-radius: 10px; border-left: 5px solid #ffc107 !important;">' +
                                   '<div class="d-flex justify-content-between fw-bold text-dark mb-1 small">' +
                                   '<span>👤 ' + r.username + '</span>' +
                                   '<span class="text-warning">★ ' + r.rating + '/5</span>' +
                                   '</div>' +
                                   '<div class="text-dark small style-comment-text" style="font-weight: 500; word-break: break-word;">' + commentText + '</div>' +
                                   '<small class="text-muted d-block text-end mt-1" style="font-size: 0.65rem;">' + r.date + '</small>' +
                                   '</div>';
                    });
                } else {
                    revHtml = '<em class="text-muted small d-block p-3 bg-white rounded border text-center" style="border-radius: 10px;">Отзывов об этой модели пока нет. Будьте первым!</em>';
                }
                reviewsContainer.innerHTML = revHtml;
            }

            const formBlock = document.getElementById('modal-review-form-block');
            const authAlert = document.getElementById('modal-review-auth-alert');
            if (globalUserData) {
                if (formBlock) formBlock.classList.remove('d-none');
                if (authAlert) authAlert.classList.add('d-none');
            } else {
                if (formBlock) formBlock.classList.add('d-none');
                if (authAlert) authAlert.classList.remove('d-none');
            }

            const btnSubmitReview = document.getElementById('btn-submit-review');
            if (btnSubmitReview) {
                btnSubmitReview.onclick = () => {
                    const textInput = document.getElementById('review-text-input');
                    const ratingSelect = document.getElementById('review-rating-select');
                    if (!textInput || !textInput.value.trim()) { alert('Пожалуйста, напишите текст вашего отзыва!'); return; }

                    btnSubmitReview.disabled = true;
                    fetch(`/api/products/${productId}/review/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                        body: JSON.stringify({ rating: ratingSelect.value, text: textInput.value.trim() })
                    })
                    .then(res => res.json())
                    .then(resp => {
                        alert(resp.message);
                        textInput.value = '';
                        if (productDetailModalEl) productDetailModalEl.hide();
                        loadCatalog();
                    })
                    .catch(err => console.error(err))
                    .finally(() => { btnSubmitReview.disabled = false; });
                };
            }

            const tech = product.tech || {};
            const ai_simple = product.ai_simple || {};
            const techContainer = document.getElementById('tech-content-container');
            if (techContainer) {
                let html = '<div id="tech-pro-content" class="small" style="max-height: 350px; overflow-y: auto;"><table class="table table-sm table-borderless my-1"><tbody>' +
                    '<tr><td class="text-muted fw-bold pb-2" style="width: 40%;">📱 Экран:</td><td class="text-dark fw-medium">' + (tech.screen || 'Не указано') + '</td></tr>' +
                    '<tr><td class="text-muted fw-bold pb-2">🔋 Батарея:</td><td class="text-dark fw-medium">' + (tech.battery || 'Не указано') + '</td></tr>' +
                    '<tr><td class="text-muted fw-bold pb-2">⚡ Зарядка:</td><td class="text-dark fw-medium">' + (tech.charge || 'Не указано') + '</td></tr>' +
                    '<tr><td class="text-muted fw-bold pb-2">📸 Камера:</td><td class="text-dark fw-medium">' + (tech.camera || 'Не указано') + '</td></tr>' +
                    '<tr><td class="text-muted fw-bold pb-2">🚀 Процессор:</td><td class="text-dark fw-medium">' + (tech.cpu || 'Не указано') + '</td></tr>' +
                    '<tr><td class="text-muted fw-bold pb-2">💾 Память:</td><td class="text-dark fw-medium">' + (tech.memory || 'Не указано') + '</td></tr>' +
                    '<tr><td class="text-muted fw-bold pb-2">🛡️ Корпус:</td><td class="text-dark fw-medium">' + (tech.body || 'Не указано') + '</td></tr>' +
                    '<tr><td class="text-muted fw-bold pb-2">⚙️ Платформа:</td><td class="text-dark fw-medium">' + (tech.os || 'Не указано') + '</td></tr>' +
                    '</tbody></table></div>';
                html += '<div id="tech-simple-content" class="d-none" style="max-height: 350px; overflow-y: auto;">' +
                    '<div class="d-flex flex-wrap gap-2 mb-3">' +
                    '<span class="badge bg-secondary p-2 style-tooltip" data-bs-toggle="tooltip" title="' + (ai_simple.screen || 'Экран') + '">📱 Экран [ℹ️]</span>' +
                    '<span class="badge bg-secondary p-2 style-tooltip" data-bs-toggle="tooltip" title="' + (ai_simple.battery || 'Питание') + '">🔋 Питание [ℹ️]</span>' +
                    '<span class="badge bg-secondary p-2 style-tooltip" data-bs-toggle="tooltip" title="' + (ai_simple.camera || 'Камера') + '">📸 Камера [ℹ️]</span></div>' +
                    '<div class="card border-0 bg-light p-2 mb-2"><div class="small"><strong class="text-primary">📸 Съемка:</strong> ' + (ai_simple.camera || 'Анализ отсутствует') + '</div></div>' +
                    '<div class="card border-0 bg-light p-2 mb-2"><div class="small"><strong class="text-success">🚀 Игры:</strong> ' + (ai_simple.cpu || 'Анализ отсутствует') + '</div></div>' +
                    '<div class="card border-0 bg-light p-2"><div class="small"><strong class="text-dark">🛡️ Корпус:</strong> ' + (ai_simple.body || 'Анализ отсутствует') + '</div></div></div>';
                techContainer.innerHTML = html;
            }

            const modeProRadio = document.getElementById('mode-pro');
            const modeSimpleRadio = document.getElementById('mode-simple');
            const proContent = document.getElementById('tech-pro-content');
            const simpleContent = document.getElementById('tech-simple-content');
            const aiBox = document.getElementById('ai-response-box');
            const aiBtn = document.getElementById('ai-translate-btn');

            if (modeProRadio) modeProRadio.checked = true;
            if (proContent) proContent.classList.remove('d-none');
            if (simpleContent) simpleContent.classList.add('d-none');
            if (aiBox) { aiBox.classList.add('d-none'); aiBox.innerHTML = ''; }
            if (aiBtn) {
                aiBtn.innerHTML = '<span>✨</span> Объясни мне этот smartphone (ИИ)';
                aiBtn.removeAttribute('disabled');
                const newAiBtn = aiBtn.cloneNode(true);
                aiBtn.parentNode.replaceChild(newAiBtn, aiBtn);
                newAiBtn.onclick = () => {
                    if (aiBox) { aiBox.classList.remove('d-none'); aiBox.innerHTML = '<em>🤖 Загрузка...</em>'; }
                    setTimeout(() => { if (aiBox) aiBox.innerHTML = '<strong>🤖 Аналитика ИИ:</strong><br>' + (ai_simple.summary || 'Нет данных.'); }, 400);
                };
            }

            document.querySelectorAll('.tooltip').forEach(t => t.remove());
            [].slice.call(document.querySelectorAll('.style-tooltip')).map(el => new bootstrap.Tooltip(el));

            if (modeProRadio && modeSimpleRadio) {
                modeProRadio.onclick = () => { proContent?.classList.remove('d-none'); simpleContent?.classList.add('d-none'); };
                modeSimpleRadio.onclick = () => { proContent?.classList.add('d-none'); simpleContent?.classList.remove('d-none'); };
            }

            const carouselContainer = document.getElementById('carousel-images-container');
            let carouselHtml = '';
            const mainImgUrl = product.image ? "/media/" + product.image : '';

            if (mainImgUrl) {
                carouselHtml += '<div class="carousel-item active"><img src="' + mainImgUrl + '" class="d-block w-100" style="height: 480px; object-fit: contain;"></div>';
            } else {
                carouselHtml += '<div class="carousel-item active"><div class="text-center bg-light py-5" style="height: 480px; font-size: 5rem;">📱</div></div>';
            }

            if (product.gallery) {
                product.gallery.forEach(imgName => {
                    carouselHtml += '<div class="carousel-item"><img src="/media/' + imgName + '" class="d-block w-100" style="height: 480px; object-fit: contain;"></div>';
                });
            }

            if (carouselContainer) {
                carouselContainer.innerHTML = carouselHtml;
            }

            const actionsContainer = document.getElementById('modal-product-actions');
            const mainCardBtn = document.querySelector('.btn-add-cart[data-id="' + productId + '"]');

            // Используем let вместо const, чтобы иметь возможность динамически менять статус клика на лету!
            let isAdded = mainCardBtn ? (mainCardBtn.classList.contains('btn-purple') || mainCardBtn.textContent.includes('В корзине')) : false;

            if (actionsContainer) {
                actionsContainer.innerHTML = isAdded
                    ? '<button class="btn text-white w-100 py-2 fw-bold" id="modal-buy-btn" style="border-radius: 12px; background-color: #6f42c1; border: 1px solid #6f42c1;">В корзине ✓</button>'
                    : '<button class="btn btn-success w-100 py-2 fw-bold" id="modal-buy-btn" style="border-radius: 12px;">🛒 Купить смартфон</button>';

                const modalBuyBtn = document.getElementById('modal-buy-btn');
                if (modalBuyBtn) {
                    modalBuyBtn.onclick = (e) => {
                        e.preventDefault(); // Намертво блокируем любые прыжки вёрстки и перезагрузки страницы

                        if (isAdded) {
                            // Повторный клик: плавно закрываем карточку ТТХ и разворачиваем окно Корзины
                            if (productDetailModalEl) productDetailModalEl.hide();
                            setTimeout(() => openCartModal(), 300);
                        } else {
                            // Первый клик: мгновенно перекрашиваем кнопку в фиолетовый цвет ПРЯМО В МОДАЛКЕ!
                            modalBuyBtn.className = 'btn text-white w-100 py-2 fw-bold';
                            modalBuyBtn.style.backgroundColor = '#6f42c1';
                            modalBuyBtn.style.borderColor = '#6f42c1';
                            modalBuyBtn.innerHTML = 'В корзине ✓';

                            // Отправляем асинхронный POST-запрос в Django без закрытия текущего окна
                            handleAddToCart(productId, mainCardBtn);

                            // Меняем флаг, чтобы следующий клик по этой кнопке распознался как повторный!
                            isAdded = true;
                        }
                    };
                }
            }

            if (productDetailModalEl) {
                productDetailModalEl.show();
            }
        });
};



// 9. СИНХРОНИЗАЦИЯ ПОИСКА И ФИЛЬТРОВ С ШАПКОЙ
const headerBtnSearch = document.getElementById('header-btn-search');
if (headerBtnSearch) {
  headerBtnSearch.addEventListener('click', (e) => {
    e.preventDefault();
    const headerSearchInput = document.getElementById('header-search-input');
    const mainSearchInput = document.getElementById('search-input');
    if (headerSearchInput && mainSearchInput) {
      mainSearchInput.value = headerSearchInput.value.trim();
    }
    loadCatalog();
  });
}

if (btnFilter) {
  btnFilter.addEventListener('click', (e) => {
    e.preventDefault();
    loadCatalog();
  });
}

// 10. КНОПКА "ПРИМЕНИТЬ" С АВТООТКЛЮЧЕНИЕМ ИИ‑РЕЖИМА
if (btnFilter) {
  btnFilter.addEventListener('click', (e) => {
    e.preventDefault();
    isAiFilteredMode = false;
    const currentDropdownBtn = document.getElementById('sortDropdownBtn');
    if (currentDropdownBtn) {
      currentDropdownBtn.classList.remove('disabled');
      currentDropdownBtn.style.opacity = '1';
      currentDropdownBtn.style.pointerEvents = 'auto';
    }
    const aiAssistantVerdict = document.getElementById('ai-assistant-verdict');
    if (aiAssistantVerdict) aiAssistantVerdict.classList.add('d-none');
    loadCatalog();
  });
}

// 11. ИСПРАВЛЕННАЯ СВЯЗКА КЛИКОВ ВИТРИНЫ
if (productsGrid) {
  productsGrid.addEventListener('click', (e) => {
    const target = e.target;
    const productId =
      target.getAttribute('data-id') ||
      target.closest('.open-detail-trigger')?.getAttribute('data-id') ||
      target.dataset.id;

    if (target.classList.contains('btn-add-cart')) {
      e.preventDefault();
      if (target.classList.contains('btn-purple') || target.textContent.includes('В корзине')) {
        openCartModal();
      } else {
        handleAddToCart(productId, target);
      }
      return;
    }

    if (target.classList.contains('btn-go-to-cart')) {
      openCartModal();
      return;
    }

    if (target.classList.contains('btn-fav')) {
      e.preventDefault();
      handleToggleFavorite(productId, target);
      return;
    }

    if (productId && !target.classList.contains('btn-outline-danger') && !target.classList.contains('btn-danger')) {
      openProductDetailModal(productId);
    }
  });
}

if (categoriesList) {
  categoriesList.addEventListener('click', (e) => {
    const btn = e.target.closest('.list-group-item');
    if (!btn) return;
    e.preventDefault();
    isAiFilteredMode = false;
    document.querySelectorAll('#categories-list .list-group-item').forEach(el => el.classList.remove('active'));
    btn.classList.add('active');
    currentCategory = btn.getAttribute('data-slug') || '';
    loadCatalog();
  });
}

const sortOptionsList = document.getElementById('sort-options-list');
if (sortOptionsList && document.getElementById('sortDropdownBtn')) {
  sortOptionsList.addEventListener('click', (e) => {
    const item = e.target.closest('.dropdown-item');
    if (!item) return;
    e.preventDefault();
    isAiFilteredMode = false;
    const currentDropdownBtn = document.getElementById('sortDropdownBtn');
    if (currentDropdownBtn) {
      currentDropdownBtn.classList.remove('disabled');
      currentDropdownBtn.style.opacity = '1';
      currentDropdownBtn.style.pointerEvents = 'auto';
    }
    const aiAssistantVerdict = document.getElementById('ai-assistant-verdict');
    if (aiAssistantVerdict) aiAssistantVerdict.classList.add('d-none');

    currentSortMode = item.getAttribute('data-sort');
    document.querySelectorAll('#sort-options-list .dropdown-item').forEach(el => {
      el.classList.remove('active');
      el.innerHTML = el.innerHTML.replace('🔘', '⚪');
    });
    item.classList.add('active');
    item.innerHTML = item.innerHTML.replace('⚪', '🔘');
    if (currentDropdownBtn) currentDropdownBtn.innerHTML = item.innerText.replace('🔘', '📊');
    loadCatalog();
  });
}

// 12. ТУМБЛЕР ТЕМЫ И СЕМАНТИЧЕСКИЙ ИИ‑ПОДБОР
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const themeToggleIcon = document.getElementById('theme-toggle-icon');
const themeToggleText = document.getElementById('theme-toggle-text');

function applyTheme(theme) {
  if (theme === 'dark') {
    document.body.setAttribute('data-bs-theme', 'dark');
    document.body.classList.remove('bg-light');
    document.body.classList.add('bg-dark');
    if (themeToggleIcon) themeToggleIcon.textContent = '☀️';
    if (themeToggleText) themeToggleText.textContent = 'Светлая тема';
  } else {
    document.body.setAttribute('data-bs-theme', 'light');
    document.body.classList.remove('bg-dark');
    document.body.classList.add('bg-light');
    if (themeToggleIcon) themeToggleIcon.textContent = '🌙';
    if (themeToggleText) themeToggleText.textContent = 'Тёмная тема';
  }
  localStorage.setItem('marketplace-theme', theme);
}

const savedTheme = localStorage.getItem('marketplace-theme') || 'light';
applyTheme(savedTheme);

if (themeToggleBtn) {
  themeToggleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    const currentTheme = document.body.getAttribute('data-bs-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
  });
}

const btnAiAssist = document.getElementById('btn-ai-assist');
const aiAssistantInput = document.getElementById('ai-assistant-input');
const aiAssistantVerdict = document.getElementById('ai-assistant-verdict');
const sortDropdownBtn = document.getElementById('sortDropdownBtn');

if (btnAiAssist && aiAssistantInput && aiAssistantVerdict) {
  btnAiAssist.addEventListener('click', (e) => {
    e.preventDefault();
    const textValue = aiAssistantInput.value.trim();
    if (!textValue) return;

    btnAiAssist.disabled = true;
    btnAiAssist.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 🧠 ИИ парсит интернет и ТТХ...';

    const searchInput = document.getElementById('search-input');
    const priceInput = document.getElementById('price-input');

    fetch('/api/ai-recommend/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ text: textValue })
    })
      .then(res => {
        if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (data.status === 'success') {
          isAiFilteredMode = true;
          if (sortDropdownBtn) {
            sortDropdownBtn.classList.add('disabled');
            sortDropdownBtn.style.opacity = '0.5';
            sortDropdownBtn.style.pointerEvents = 'none';
          }
          if (searchInput) searchInput.value = '';
          if (data.suggested_price && priceInput) priceInput.value = data.suggested_price;

          // Очищаем текст от маркеров Markdown-звездочек
          let formattedVerdict = data.verdict.replace(/\*\*(.*?)\*\*/g, '\$1');
          aiAssistantVerdict.innerHTML = formattedVerdict;
          aiAssistantVerdict.classList.remove('d-none');

          if (productsGrid) {
            productsGrid.innerHTML = '';

            // ИСПРАВЛЕНО: Интеллектуальный фронтенд-сборщик ID товаров на основе текста ответа ИИ
            let matchedIds = data.matched_ids || [];
            const textLower = data.verdict.toLowerCase();

            // Если бэкенд отдал пустой массив, фронтенд самостоятельно сканирует текст на упоминания моделей
            if (matchedIds.length === 0 && typeof globalProductsArray !== 'undefined') {
              globalProductsArray.forEach(prod => {
                const nameLower = prod.name.toLowerCase();

                // Ищем ключевые маркеры серий (учитываем любые короткие обозначения серий)
                if (nameLower.includes('a26') && textLower.includes('a26')) {
                  if (!matchedIds.includes(prod.id)) matchedIds.push(prod.id);
                }
                if (nameLower.includes('12 mini') && (textLower.includes('12 mini') || textLower.includes('12mini') || textLower.includes('iphone 12'))) {
                  if (!matchedIds.includes(prod.id)) matchedIds.push(prod.id);
                }
                if (nameLower.includes('17') && textLower.includes('17')) {
                  // Выводим флагман iPhone 17 только если запрос НЕ экономный/детский/пожилой
                  const isBudgetMode = textLower.includes('школьн') || textLower.includes('пожил') || textLower.includes('бюджет') || textLower.includes('дешев');
                  if (!isBudgetMode && !matchedIds.includes(prod.id)) matchedIds.push(prod.id);
                }
                if (nameLower.includes('pura 90') && textLower.includes('pura 90')) {
                  if (!matchedIds.includes(prod.id)) matchedIds.push(prod.id);
                }
                if (nameLower.includes('a07') && textLower.includes('a07')) {
                  if (!matchedIds.includes(prod.id)) matchedIds.push(prod.id);
                }
                if (nameLower.includes('s26') && textLower.includes('s26')) {
                  if (!matchedIds.includes(prod.id)) matchedIds.push(prod.id);
                }
              });
            }

            // Рендерим и перестраиваем итоговую SPA-витрину на экране
            if (matchedIds.length > 0 && typeof globalProductsArray !== 'undefined') {
              const filteredProducts = [];
              matchedIds.forEach(id => {
                const found = globalProductsArray.find(p => p.id === id);
                if (found) filteredProducts.push(found);
              });
              renderProducts(filteredProducts.length > 0 ? filteredProducts : globalProductsArray);
            } else {
              renderProducts(typeof globalProductsArray !== 'undefined' ? globalProductsArray : []);
            }
          }
        } else {
          alert('Ошибка ИИ: ' + data.message);
        }
      })
      .catch(err => console.error(err))
      .finally(() => {
        btnAiAssist.disabled = false;
        btnAiAssist.innerHTML = '🧠 Подобрать смартфоны';
      });
  });
}


    // ЖИВОЙ ОБРАБОТЧИК ДЛЯ КНОПОК ВНУТРИ СПИСКА ТОВАРОВ КОРЗИНЫ (+, -, ❌)
    const cartItemsList = document.getElementById('cart-items-list');
    if (cartItemsList) {
        cartItemsList.addEventListener('click', e => {
            const btnPlus = e.target.closest('.btn-cart-plus');
            const btnMinus = e.target.closest('.btn-cart-minus');
            const btnDelete = e.target.closest('.btn-cart-delete-all');

            if (btnPlus) {
                e.preventDefault();
                const productId = btnPlus.getAttribute('data-product-id');
                fetch('/api/cart/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ product_id: parseInt(productId), action: 'add' })
                }).then(() => { openCartModal(); loadCatalog(); });
            }

            if (btnMinus) {
                e.preventDefault();
                const productId = btnMinus.getAttribute('data-product-id');
                fetch('/api/cart/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ product_id: parseInt(productId), action: 'remove' })
                }).then(() => { openCartModal(); loadCatalog(); });
            }

            if (btnDelete) {
                e.preventDefault();
                const productId = btnDelete.getAttribute('data-product-id');
                fetch('/api/cart/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ product_id: parseInt(productId), action: 'delete_all' })
                }).then(() => { openCartModal(); loadCatalog(); });
            }
        });
    }

    // ГЛОБАЛЬНЫЙ ПЕРЕХВАТЧИК КЛИКА ДЛЯ КНОПКИ ОПЛАТЫ (Сработает в любой точке модального окна!)
    document.addEventListener('click', e => {
        const btnCheckout = e.target.closest('#btn-checkout') ||
                           e.target.closest('.btn-checkout') ||
                           e.target.closest('[id*="checkout"]') ||
                           (e.target.tagName === 'BUTTON' && e.target.textContent.includes('Оплатить'));

        if (btnCheckout) {
            e.preventDefault();
            if (btnCheckout.disabled) return; // Предотвращаем баг повторной отправки

            btnCheckout.disabled = true;
            btnCheckout.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Проведение платежа...';

            fetch('/api/cart/', {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' }
            })
            .then(res => {
                if (!res.ok) throw new Error('Ошибка сервера: ' + res.status);
                return res.json();
            })
            .then(data => {
                if (data.status === 'paid') {
                    alert(data.message);
                    if (cartModalEl) {
                        cartModalEl.hide();
                    } else {
                        const currentModal = bootstrap.Modal.getInstance(document.getElementById('cartModal')) ||
                                             bootstrap.Modal.getInstance(document.querySelector('.modal.show'));
                        if (currentModal) currentModal.hide();
                    }
                    if (globalUserData) globalUserData.cart_ids = [];
                    loadCatalog();
                } else {
                    alert(data.message || 'Ошибка оплаты');
                    btnCheckout.disabled = false;
                    btnCheckout.innerHTML = '💳 Оплатить заказ';
                }
            })
            .catch(err => {
                console.error(err);
                alert('Не удалось провести оплату.');
                btnCheckout.disabled = false;
                btnCheckout.innerHTML = '💳 Оплатить заказ';
            });
        }
    });


// ЖИВОЙ ОБРАБОТЧИК КНОПОК ВНУТРИ МОДАЛКИ ИЗБРАННОГО
const favItemsList = document.getElementById('fav-items-list');
if (favItemsList) {
  favItemsList.addEventListener('click', e => {
    const btnRemove = e.target.closest('.btn-fav-remove');
    const btnToCart = e.target.closest('.btn-fav-to-cart');
    const btnGoToCart = e.target.closest('.btn-fav-go-to-cart');

    if (btnRemove) {
      const id = btnRemove.getAttribute('data-id');
      fetch('/api/favorites/toggle/' + id + '/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      }).then(() => { window.openFavModal(); loadCatalog(); });
    }

    if (btnToCart) {
      const id = btnToCart.getAttribute('data-id');
      fetch('/api/cart/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ product_id: parseInt(id), action: 'add' })
      }).then(() => { window.openFavModal(); loadCatalog(); });
    }

    if (btnGoToCart) {
      const currentFavModal = favModalEl || bootstrap.Modal.getInstance(document.getElementById('favModal'));
      if (currentFavModal) currentFavModal.hide();
      setTimeout(() => openCartModal(), 300);
    }
  });
}

// Точка старта SPA-движка
loadCatalog();
});







