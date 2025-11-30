from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import config

# ==================== ОСНОВНЫЕ КЛАВИАТУРЫ ====================

keyboard1 = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔻Купить"), KeyboardButton(text="💰Пополнить баланс")],
        [KeyboardButton(text="☎️Поддержка"), KeyboardButton(text="👤О нас")],
        [KeyboardButton(text="📜Правила")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие..."
)


# Клавиатура выбора города (20 городов в 4 колонки)
def keyboard2():
    cities = config.CITIES
    keyboard = []

    # Создаем ряды по 4 города в каждом
    city_items = list(cities.items())
    for i in range(0, len(city_items), 4):
        row = []
        for j in range(4):
            if i + j < len(city_items):
                city_code, city_name = city_items[i + j]
                row.append(InlineKeyboardButton(text=f"🏙️ {city_name}", callback_data=city_code))
        if row:
            keyboard.append(row)

    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_main")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==================== КЛАВИАТУРЫ РАЙОНОВ ====================

def get_districts_keyboard(city: str):
    """Клавиатура выбора района для города"""
    districts = config.DISTRICTS.get(city, [])
    buttons = []

    # Создаем кнопки районов (по 2 в ряд)
    for i in range(0, len(districts), 2):
        row = []
        for j in range(2):
            if i + j < len(districts):
                district = districts[i + j]
                row.append(InlineKeyboardButton(
                    text=f"📍 {district}",
                    callback_data=f"district_{city}_{i + j}"
                ))
        if row:
            buttons.append(row)

    # Добавляем кнопки навигации
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад к городам", callback_data="back_to_cities"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== КЛАВИАТУРЫ ТОВАРОВ ДЛЯ ГОРОДОВ ====================

def get_product_keyboard(city: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру товаров для конкретного города"""
    prices = config.PRICES.get(city, {})

    buttons = []

    # Все товары в два столбца
    products = [
        ("🍁 Шишки", "shishki"),
        ("💎 Соль", "sol"),
        ("💊 Меф", "mef"),
        ("🌿 Гашиш", "gashish"),
        ("🧪 Экстази", "ext"),
        ("💉 Кокаин", "cox"),
        ("🌈 LSD", "lsd"),
        ("💧 GBL", "gbl"),
        ("⚡ Амф", "amf"),
        ("💊 MDMA", "mdma"),
        ("🎯 Кета", "keta"),
        ("🔮 Альфа", "alpha")
    ]

    # Создаем ряды по 2 товара
    for i in range(0, len(products), 2):
        row = []
        for j in range(2):
            if i + j < len(products):
                product_name, product_code = products[i + j]
                if product_code in prices:
                    price = prices[product_code]
                    row.append(InlineKeyboardButton(
                        text=f"{product_name} | {price}{config.CURRENCY}",
                        callback_data=product_code
                    ))
        if row:
            buttons.append(row)

    # Добавляем кнопку назад
    buttons.append([InlineKeyboardButton(text="🔙 Назад к районам", callback_data="back_to_districts")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Конкретные клавиатуры для каждого города
def keyboard3(): return get_product_keyboard("msk")


def keyboard4(): return get_product_keyboard("spb")


def keyboard5(): return get_product_keyboard("ekb")


def keyboard6(): return get_product_keyboard("nnov")


def keyboard7(): return get_product_keyboard("kzn")


def keyboard8(): return get_product_keyboard("smr")


def keyboard9(): return get_product_keyboard("chely")


def keyboard10(): return get_product_keyboard("omsk")


def keyboard11(): return get_product_keyboard("rostov")


def keyboard12(): return get_product_keyboard("ufa")


def keyboard13(): return get_product_keyboard("krasn")


def keyboard14(): return get_product_keyboard("perm")


def keyboard15(): return get_product_keyboard("voron")


def keyboard16(): return get_product_keyboard("volg")


def keyboard17(): return get_product_keyboard("krasd")


def keyboard18(): return get_product_keyboard("sarat")


def keyboard19(): return get_product_keyboard("toly")


def keyboard20(): return get_product_keyboard("tyumen")


def keyboard21(): return get_product_keyboard("izhev")


def keyboard22(): return get_product_keyboard("barna")


# ==================== КЛАВИАТУРЫ ПОКУПКИ ====================

def buy():
    """Клавиатура выбора фасовки"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1г", callback_data="buy1"),
                InlineKeyboardButton(text="2г", callback_data="buy2")
            ],
            [
                InlineKeyboardButton(text="3г", callback_data="buy3"),
                InlineKeyboardButton(text="5г", callback_data="buy5")
            ],
            [
                InlineKeyboardButton(text="10г", callback_data="buy10"),
                InlineKeyboardButton(text="Другое", callback_data="buy_custom")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад к товарам", callback_data="back_to_products"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_main")
            ]
        ]
    )


def buy_confirmation_keyboard():
    """Клавиатура подтверждения заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="success"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")
            ]
        ]
    )


def payment_after_order_keyboard():
    """Клавиатура после подтверждения заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Я оплатил", callback_data="order_paid"),
                InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_order")
            ]
        ]
    )


# ==================== КЛАВИАТУРЫ ДЛЯ АДРЕСА И ФАЙЛОВ ====================

def file_upload_keyboard():
    """Клавиатура для загрузки PDF"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📎 Прикрепить PDF", callback_data="attach_pdf")
            ]
        ]
    )


def final_order_keyboard():
    """Финальная клавиатура заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Завершить заказ", callback_data="finish_order"),
                InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_order")
            ]
        ]
    )


# ==================== КЛАВИАТУРЫ ОПЛАТЫ ====================

def payment_methods_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Банковская карта", callback_data="method_card")],
            [InlineKeyboardButton(text="🥝 QIWI", callback_data="method_qiwi")],
            [InlineKeyboardButton(text="₿ Bitcoin", callback_data="method_btc")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_balance"),
             InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
        ]
    )


def payment_confirmation_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data="start_payment")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"),
             InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
        ]
    )


# ==================== СЕРВИСНЫЕ КЛАВИАТУРЫ ====================

def support_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать в поддержку", url=config.SUPPORT_CHAT)],
            [InlineKeyboardButton(text="👤 Создатель", url=f"https://t.me/{config.ADMIN_USERNAME[1:]}")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
        ]
    )


def rules_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен с правилами", callback_data="agree_rules")],
            [InlineKeyboardButton(text="❌ Не согласен", callback_data="disagree_rules")]
        ]
    )


def about_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📞 Связь с нами", url=config.SUPPORT_CHAT)],
            [InlineKeyboardButton(text="💎 Наш канал", url="https://t.me/your_channel")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
        ]
    )


# ==================== УНИВЕРСАЛЬНЫЕ КЛАВИАТУРЫ ====================

def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_main")]
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )


def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
        ]
    )