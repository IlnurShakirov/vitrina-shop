import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def translit_text(text):
    """Встроенная функция транслитерации для 100% защиты от черных квадратов в ReportLab"""
    if not text:
        return ""
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
    return "".join([translit_map.get(char, char) for char in str(text)])


def generate_order_pdf(file_path, order, items, admin_name="Smartphone Shop Systems"):
    """Генерирует официальный инвойс (чек) в формате PDF.
    Использует стандартные встроенные шрифты Helvetica, гарантируя 100% защиту от падения контейнера.
    Применяет сквозную транслитерацию для кириллицы.
    """
    # Использованы безопасные отступы по краям листа
    doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []

    styles = getSampleStyleSheet()

    # Стили текста (Используем встроенный Helvetica-Bold и Helvetica)
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#6f42c1'),
        spaceAfter=15
    )

    text_style = ParagraphStyle(
        'DocText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#333333')
    )

    # 1. Шапка документа
    story.append(Paragraph("<b>SMARTPHONE SHOP LLC</b>", title_style))
    story.append(Paragraph(
        "119019, Moscow, New Arbat St., 15<br/>TAX ID: 7704123456 | REG: 1027700123456<br/>Email: sales@smartphone-shop.ru",
        text_style))
    story.append(Spacer(1, 20))

    story.append(Paragraph(f"<b>COMMERCIAL INVOICE / RECEIPT # {order.id}</b>", title_style))

    # Автоматически транслитерируем имя покупателя
    customer_name = order.user.username
    if order.user.last_name or order.user.first_name:
        customer_name = f"{order.user.last_name} {order.user.first_name}".strip()

    clean_customer_name = translit_text(customer_name)

    # Автоматический перевод времени заказа из UTC сервера Docker в уфимский часовой пояс (+5 часов)
    from datetime import timedelta
    local_time = order.created_at + timedelta(hours=5)
    formatted_date = local_time.strftime('%d.%m.%Y %H:%M')

    story.append(Paragraph(
        f"Order Date: {formatted_date}<br/>Customer: {clean_customer_name} ({order.user.email})",
        text_style))
    story.append(Spacer(1, 15))


    # 2. Таблица с составом заказа
    table_data = [[
        Paragraph("<b>#</b>", text_style),
        Paragraph("<b>Product Name</b>", text_style),
        Paragraph("<b>Qty</b>", text_style),
        Paragraph("<b>Price</b>", text_style),
        Paragraph("<b>Total</b>", text_style)
    ]]

    # Заполняем строки из PostgreSQL
    for idx, item in enumerate(items, 1):
        item_price = float(item.price) if hasattr(item, 'price') else float(item.product.price)
        total_item_price = item_price * item.quantity

        # Автоматически транслитерируем русские символы в названиях моделей смартфонов
        prod_name = item.product.name if item.product else f"Smartphone Model ID {item.product_id}"
        clean_prod_name = translit_text(prod_name)

        table_data.append([
            Paragraph(str(idx), text_style),
            Paragraph(clean_prod_name, text_style),
            Paragraph(str(item.quantity), text_style),
            Paragraph(f"{int(item_price)} RUB", text_style),
            Paragraph(f"{int(total_item_price)} RUB", text_style)
        ])

    # Строка Итого
    table_data.append([
        Paragraph("<b>GRAND TOTAL:</b>", text_style),
        "", "", "",
        Paragraph(f"<b>{int(order.total_price)} RUB</b>", text_style)
    ])

    # Стилизуем таблицу чека в строгом корпоративном духе маркетплейса
    order_table = Table(table_data, colWidths=[30, 260, 40, 90, 100])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3ebff')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#dddddd')),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, colors.HexColor('#6f42c1')),
        ('SPAN', (0, -1), (3, -1)),
    ]))

    story.append(order_table)
    story.append(Spacer(1, 30))

    # 3. Подвал чека
    status_text = "PAID / SUCCESS" if order.is_paid else "PENDING"
    story.append(Paragraph(f"Payment Status: <b>{status_text}</b>", text_style))
    story.append(Spacer(1, 15))

    # Выводим реальное имя администратора из базы данных PostgreSQL
    story.append(Paragraph(f"Issued by: _____________________ ({admin_name})", text_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Electronic receipt generated automatically by system backend.", text_style))

    # Собираем документ
    doc.build(story)
