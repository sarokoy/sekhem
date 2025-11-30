from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio
import keyboards
import config
import adm
from captcha import captcha_generator


# Состояния для FSM
class UserStates(StatesGroup):
    waiting_for_payment_amount = State()
    waiting_for_payment_method = State()
    waiting_for_payment_comment = State()
    waiting_for_address = State()
    waiting_for_pdf = State()
    waiting_for_captcha = State()


# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


async def complete_registration(message: Message, state: FSMContext):
    """Завершение регистрации после капчи"""
    data = await state.get_data()

    # Добавляем пользователя в БД
    adm.add_user_to_db(
        user_id=data.get('user_id', message.from_user.id),
        username=data.get('username', message.from_user.username),
        first_name=data.get('first_name', message.from_user.first_name),
        last_name=data.get('last_name', message.from_user.last_name)
    )

    welcome_text = config.WELCOME_MESSAGE.format(
        username=message.from_user.first_name or "пользователь",
        admin=config.ADMIN_USERNAME
    )

    await message.answer(welcome_text, reply_markup=keyboards.keyboard1)
    await state.clear()


# ==================== КАПЧА ====================

@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    # Генерируем капчу
    try:
        captcha_text, captcha_image = await captcha_generator.generate_captcha()

        # Сохраняем правильный ответ в состоянии
        await state.update_data(
            captcha_answer=captcha_text,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        await state.set_state(UserStates.waiting_for_captcha)

        # Отправляем капчу пользователю
        await message.answer_photo(
            photo=types.BufferedInputFile(
                captcha_image.getvalue(),
                filename="captcha.png"
            ),
            caption="🔐 <b>Пройдите проверку безопасности</b>\n\n"
                    "Введите цифры с картинки для продолжения:\n\n"
                    "⚠️ <i>Введите только цифры без пробелов</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"❌ Ошибка генерации капчи: {e}")
        # Если капча не работает, пропускаем проверку
        await complete_registration(message, state)


@dp.message(UserStates.waiting_for_captcha)
async def process_captcha(message: Message, state: FSMContext):
    try:
        user_input = message.text.strip()
        data = await state.get_data()
        correct_answer = data.get('captcha_answer', '')

        print(f"🔍 Капча: пользователь ввел '{user_input}', правильный ответ '{correct_answer}'")

        if user_input == correct_answer:
            # Капча пройдена успешно
            await message.answer("✅ Проверка пройдена успешно!")
            await complete_registration(message, state)
        else:
            # Неправильная капча
            await message.answer("❌ <b>Неверный код!</b> Попробуйте еще раз.", parse_mode="HTML")

            # Генерируем новую капчу
            captcha_text, captcha_image = await captcha_generator.generate_captcha()
            await state.update_data(captcha_answer=captcha_text)

            await message.answer_photo(
                photo=types.BufferedInputFile(
                    captcha_image.getvalue(),
                    filename="captcha.png"
                ),
                caption="🔐 <b>Повторная проверка</b>\n\n"
                        "Введите цифры с картинки:\n\n"
                        "⚠️ <i>Введите только цифры без пробелов</i>",
                parse_mode="HTML"
            )

    except Exception as e:
        print(f"❌ Ошибка обработки капчи: {e}")
        await message.answer("❌ Ошибка проверки. Попробуйте снова /start")
        await state.clear()


# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "🤖 Помощь по боту:\n\n"
        "🔸 /start - Главное меню\n"
        "🔸 /help - Эта справка\n"
        "🔸 /id - Узнать свой ID\n\n"
        "📞 Поддержка: " + config.SUPPORT_USERNAME
    )


@dp.message(Command("id"))
async def get_id_command(message: types.Message):
    await message.answer(
        f"📋 Ваши данные:\n\n"
        f"🆔 ID: `{message.from_user.id}`\n"
        f"👤 Username: @{message.from_user.username}\n"
        f"📛 Имя: {message.from_user.first_name}\n"
        f"🏷️ Фамилия: {message.from_user.last_name or 'Не указана'}",
        parse_mode='Markdown'
    )


@dp.message(F.text == '🔻Купить')
async def choose_city(message: types.Message):
    await message.answer("🧊 Выбери свой город 🧊", reply_markup=keyboards.keyboard2())


@dp.message(F.text == '💰Пополнить баланс')
async def replenish_balance(message: types.Message, state: FSMContext):
    payment_comment = f"@{message.from_user.username}" if message.from_user.username else f"user_{message.from_user.id}"

    balance_text = config.BALANCE_MESSAGE.format(
        username=message.from_user.username,
        card=config.CARD_NUMBER,
        card_holder=config.CARD_HOLDER,
        card_bank=config.CARD_BANK,
        qiwi=config.QIWI_NUMBER,
        qiwi_comment=config.QIWI_COMMENT,
        btc=config.BITCOIN_WALLET,
        user_comment=payment_comment
    )

    await message.answer(
        balance_text,
        parse_mode='Markdown',
        reply_markup=keyboards.payment_confirmation_keyboard()
    )


@dp.message(F.text == '☎️Поддержка')
async def support_info(message: types.Message):
    await message.answer(
        f"📞 Поддержка:\n\n"
        f"👤 {config.SUPPORT_USERNAME}\n"
        f"💬 {config.SUPPORT_CHAT}\n\n"
        f"⏰ Работаем 24/7",
        reply_markup=keyboards.support_keyboard()
    )


@dp.message(F.text == '👤О нас')
async def about_us(message: types.Message):
    await message.answer(config.ABOUT_US, reply_markup=keyboards.about_keyboard())


@dp.message(F.text == '📜Правила')
async def rules_info(message: types.Message):
    await message.answer(config.RULES, reply_markup=keyboards.rules_keyboard())


# ==================== ОБРАБОТКА ПОПОЛНЕНИЙ ====================

@dp.callback_query(F.data == "start_payment")
async def start_payment_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "💳 Введите сумму пополнения в рублях:\n\n"
        "💰 Минимальная сумма: 100 руб\n"
        "💎 Пример: 1500"
    )
    await state.set_state(UserStates.waiting_for_payment_amount)
    await callback_query.answer()


@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.answer("❌ Пополнение баланса отменено")
    await callback_query.answer()


@dp.message(UserStates.waiting_for_payment_amount)
async def process_payment_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount < 100:
            await message.answer("❌ Минимальная сумма пополнения - 100 руб. Введите сумму больше:")
            return
        if amount > 50000:
            await message.answer("❌ Максимальная сумма пополнения - 50,000 руб. Введите меньшую сумму:")
            return

        await state.update_data(amount=amount)
        await message.answer(
            f"💳 Сумма: {amount} руб\n\n"
            "Выберите способ оплаты:",
            reply_markup=keyboards.payment_methods_keyboard()
        )
        await state.set_state(UserStates.waiting_for_payment_method)

    except ValueError:
        await message.answer("❌ Неверный формат суммы. Введите число:")


@dp.callback_query(UserStates.waiting_for_payment_method, F.data.startswith("method_"))
async def process_payment_method(callback_query: CallbackQuery, state: FSMContext):
    method_map = {
        "method_card": "банковская карта",
        "method_qiwi": "qiwi",
        "method_btc": "bitcoin"
    }

    method = method_map[callback_query.data]
    data = await state.get_data()
    amount = data['amount']

    await state.update_data(payment_method=method)

    await callback_query.message.answer(
        f"💰 Сумма: {amount} руб\n"
        f"💳 Метод: {method}\n\n"
        "📝 Введите комментарий к платежу (или отправьте '-' если без комментария):\n\n"
        "Пример: Пополнение баланса для заказа"
    )
    await state.set_state(UserStates.waiting_for_payment_comment)
    await callback_query.answer()


@dp.message(UserStates.waiting_for_payment_comment)
async def process_payment_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    if comment == "-":
        comment = ""

    # Получаем все данные из состояния
    data = await state.get_data()
    amount = data['amount']
    payment_method = data['payment_method']

    # Добавляем платеж в БД
    payment_id = adm.add_payment(
        user_id=message.from_user.id,
        username=message.from_user.username,
        amount=amount,
        payment_method=payment_method,
        comment=comment,
        status="pending"
    )

    # Отправляем уведомление админам
    if config.ENABLE_ADMIN_NOTIFICATIONS:
        await adm.send_payment_notification(
            bot=bot,
            payment_id=payment_id,
            user_id=message.from_user.id,
            username=message.from_user.username,
            amount=amount,
            payment_method=payment_method,
            comment=comment
        )

    await message.answer(
        f"✅ Заявка на пополнение принята!\n\n"
        f"💳 Сумма: {amount} руб\n"
        f"📱 Метод: {payment_method}\n"
        f"📝 Комментарий: {comment if comment else 'нет'}\n"
        f"🆔 Номер заявки: #{payment_id}\n\n"
        f"⏳ Ожидайте проверки модератора в течение {config.PAYMENT_CHECK_INTERVAL} минут.\n"
        f"📞 При проблемах свяжитесь с поддержкой: {config.SUPPORT_USERNAME}"
    )

    await state.clear()


# ==================== ОБРАБОТЧИКИ ДЛЯ 20 ГОРОДОВ ====================

@dp.callback_query(F.data.in_(config.CITIES.keys()))
async def city_handler(callback_query: CallbackQuery):
    city_name = config.CITIES.get(callback_query.data, callback_query.data)
    await bot.send_message(
        callback_query.from_user.id,
        f"🏙️ {city_name}\n📍 Выбери район 🔹",
        reply_markup=keyboards.get_districts_keyboard(callback_query.data)
    )
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)


# ==================== ОБРАБОТЧИКИ РАЙОНОВ ====================

@dp.callback_query(F.data.startswith('district_'))
async def district_handler(callback_query: CallbackQuery):
    # Парсим данные: district_город_индекс
    parts = callback_query.data.split('_')
    city_code = parts[1]
    district_index = int(parts[2])

    city_name = config.CITIES.get(city_code, "Город")
    districts = config.DISTRICTS.get(city_code, [])
    district_name = districts[district_index] if district_index < len(districts) else "Район"

    await bot.send_message(
        callback_query.from_user.id,
        f"🏙️ {city_name}\n📍 {district_name}\n🔹 Выбери товар 🔹",
        reply_markup=keyboards.get_product_keyboard(city_code)
    )
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)


# ==================== ОБРАБОТЧИКИ ТОВАРОВ ====================

def get_product_price(city: str, product: str) -> int:
    """Получить цену товара для города"""
    city_prices = config.PRICES.get(city, {})
    return city_prices.get(product, 0)


@dp.callback_query(
    F.data.in_(['shishki', 'sol', 'mef', 'gashish', 'ext', 'cox', 'lsd', 'gbl', 'amf', 'mdma', 'keta', 'alpha']))
async def product_handler(callback_query: CallbackQuery):
    product_names = {
        'shishki': '🍁 Шишки', 'sol': '💎 Соль', 'mef': '💊 Меф',
        'gashish': '🌿 Гашиш', 'ext': '🧪 Экстази', 'cox': '💉 Кокаин',
        'lsd': '🌈 LSD', 'gbl': '💧 GBL', 'amf': '⚡ Амф',
        'mdma': '💊 MDMA', 'keta': '🎯 Кета', 'alpha': '🔮 Альфа'
    }

    product_name = product_names.get(callback_query.data, callback_query.data)
    city = 'msk'  # Можно улучшить логику определения города
    price = get_product_price(city, callback_query.data)

    await bot.send_message(
        callback_query.from_user.id,
        f"{product_name}\n💰 1г стоит {price} {config.CURRENCY}\n🔹 Выбери фасовку 🔹",
        reply_markup=keyboards.buy()
    )
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)


# ==================== ОБРАБОТЧИКИ ПОКУПОК ====================

@dp.callback_query(F.data.startswith('buy'))
async def buy_handler(callback_query: CallbackQuery):
    weight = callback_query.data.replace('buy', '') + 'г'
    await bot.send_message(
        callback_query.from_user.id,
        f"🔹 Подтвердите покупку 🔹\n\n"
        f"⚖️ Фасовка: {weight}\n\n"
        f"После подтверждения вы получите реквизиты для оплаты",
        reply_markup=keyboards.buy_confirmation_keyboard()
    )
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)


@dp.callback_query(F.data == 'success')
async def success_purchase(callback_query: CallbackQuery):
    await bot.send_message(
        callback_query.from_user.id,
        "✅ Заказ подтвержден!\n\n"
        "💳 Реквизиты для оплаты:\n"
        f"Карта: `{config.CARD_NUMBER}`\n"
        f"QIWI: `{config.QIWI_NUMBER}`\n"
        f"BTC: `{config.BITCOIN_WALLET}`\n\n"
        "После оплаты нажмите кнопку ✅ Я оплатил",
        parse_mode='Markdown',
        reply_markup=keyboards.payment_after_order_keyboard()
    )
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)


@dp.callback_query(F.data == 'order_paid')
async def order_paid_handler(callback_query: CallbackQuery, state: FSMContext):
    await bot.send_message(
        callback_query.from_user.id,
        "✅ Оплата получена!\n\n"
        "📋 Теперь нужно:\n"
        "1. Скиньте PDF файл с подтверждением оплаты\n"
        "2. Напишите свой адрес доставки\n\n"
        "Начнем с адреса 📍",
        reply_markup=keyboards.file_upload_keyboard()
    )

    # Запрашиваем адрес
    await callback_query.message.answer(
        "📍 Напишите ваш адрес доставки:\n\n"
        "Пример: г. Москва, ул. Примерная, д. 10, кв. 25, подъезд 3, код 1234\n\n"
        "⚠️ Адрес должен быть точным для успешной доставки!"
    )
    await state.set_state(UserStates.waiting_for_address)
    await callback_query.answer()


@dp.message(UserStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    address = message.text.strip()

    # Сохраняем адрес в состоянии
    await state.update_data(address=address)

    await message.answer(
        f"✅ Адрес сохранен:\n{address}\n\n"
        f"📎 Теперь обязательно прикрепите PDF файл с подтверждением оплаты\n\n"
        f"⚠️ Без подтверждения оплаты заказ не будет выполнен!",
        reply_markup=keyboards.file_upload_keyboard()
    )
    await state.set_state(UserStates.waiting_for_pdf)


@dp.callback_query(F.data == 'attach_pdf')
async def attach_pdf_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "📎 Пожалуйста, прикрепите PDF файл с подтверждением оплаты\n\n"
        "Файл должен быть в формате PDF\n\n"
        "⚠️ Это обязательное требование для выполнения заказа!"
    )
    await callback_query.answer()


@dp.message(UserStates.waiting_for_pdf, F.document)
async def process_pdf_file(message: Message, state: FSMContext):
    if message.document.mime_type == 'application/pdf':
        # Сохраняем информацию о файле
        file_id = message.document.file_id
        file_name = message.document.file_name

        data = await state.get_data()
        address = data.get('address', 'Не указан')

        await message.answer(
            f"✅ PDF файл получен!\n\n"
            f"📍 Адрес: {address}\n"
            f"📎 Файл: {file_name}\n\n"
            f"🔄 Заказ передан на обработку",
            reply_markup=keyboards.final_order_keyboard()
        )

        # Отправляем уведомление админу
        await adm.send_order_notification(
            bot=bot,
            user_id=message.from_user.id,
            username=message.from_user.username,
            product="Товар",
            weight="Фасовка",
            address=address,
            has_pdf=True
        )

        # Здесь можно сохранить file_id для дальнейшего использования
        print(f"PDF file received: {file_name} (ID: {file_id})")

    else:
        await message.answer(
            "❌ Пожалуйста, прикрепите файл в формате PDF\n\n⚠️ Без подтверждения оплаты заказ не будет выполнен!")


@dp.message(UserStates.waiting_for_pdf)
async def process_non_pdf_message(message: Message):
    await message.answer(
        "❌ Пожалуйста, прикрепите PDF файл с подтверждением оплаты\n\n"
        "⚠️ Это обязательное требование!\n"
        "📞 Если возникли проблемы с загрузкой файла, свяжитесь с поддержкой: " + config.SUPPORT_USERNAME
    )


@dp.callback_query(F.data == 'finish_order')
async def finish_order_handler(callback_query: CallbackQuery, state: FSMContext):
    await bot.send_message(
        callback_query.from_user.id,
        "🎉 Заказ завершен!\n\n"
        "📦 Ваш заказ передан в работу\n"
        "⏱️ Ожидайте доставку\n"
        "📞 При необходимости с вами свяжется оператор\n\n"
        "Для нового заказа нажмите /start"
    )
    await state.clear()
    await callback_query.answer()


@dp.callback_query(F.data == 'cancel_order')
async def cancel_order_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.send_message(
        callback_query.from_user.id,
        "❌ Заказ отменен\n\n"
        "Для нового заказа нажмите /start"
    )
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)


# ==================== ОБРАБОТЧИКИ АДМИН-ПАНЕЛИ ====================

@dp.callback_query(F.data == "broadcast_confirm")
async def broadcast_confirm_handler(callback_query: CallbackQuery, state: FSMContext):
    # Получаем сохраненное сообщение из состояния
    data = await state.get_data()
    broadcast_message = data.get('broadcast_message')

    if not broadcast_message:
        await callback_query.answer("❌ Сообщение для рассылки не найдено", show_alert=True)
        return

    # Получаем всех пользователей
    users = adm.get_all_users()
    success_count = 0
    fail_count = 0

    # Отправляем уведомление о начале рассылки
    processing_msg = await callback_query.message.edit_text(
        f"🔄 Начинаем рассылку...\nОбработано: 0/{len(users)}"
    )

    # Рассылаем сообщение всем пользователям
    for i, user_id in enumerate(users, 1):
        try:
            await bot.send_message(
                user_id,
                broadcast_message['text'],
                parse_mode=broadcast_message.get('parse_mode', None)
            )
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Ошибка отправки пользователю {user_id}: {e}")

        # Обновляем прогресс каждые 10 сообщений
        if i % 10 == 0 or i == len(users):
            await processing_msg.edit_text(
                f"🔄 Рассылка...\nОбработано: {i}/{len(users)}\n"
                f"✅ Успешно: {success_count}\n"
                f"❌ Ошибок: {fail_count}"
            )

    # Завершаем рассылку
    await processing_msg.edit_text(
        f"✅ Рассылка завершена!\n\n"
        f"📊 Результаты:\n"
        f"👥 Всего пользователей: {len(users)}\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Не отправлено: {fail_count}\n"
        f"📈 Процент доставки: {round((success_count / len(users)) * 100, 2) if users else 0}%"
    )

    await state.clear()
    await callback_query.answer()


@dp.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.edit_text(
        "❌ Рассылка отменена",
        reply_markup=adm.get_admin_keyboard()
    )
    await callback_query.answer()


@dp.callback_query(F.data == "admin_check_payments")
async def admin_check_payments_handler(callback_query: CallbackQuery):
    pending_payments = adm.get_pending_payments()

    if not pending_payments:
        await callback_query.message.edit_text(
            "✅ Нет ожидающих проверки пополнений",
            reply_markup=adm.get_payments_keyboard()
        )
        return

    payments_text = "⏳ Ожидающие проверки пополнения:\n\n"
    for payment in pending_payments[:5]:
        payment_id, user_id, username, amount, method, status, comment, date, notified, first_name, user_username = payment
        user_display = f"{first_name} (@{user_username})" if user_username else f"{first_name} (без @)"
        payments_text += f"🆔 #{payment_id}\n👤 {user_display}\n💳 {amount} руб ({method})\n📝 {comment or 'Нет комментария'}\n🕒 {date}\n\n"

    if len(pending_payments) > 5:
        payments_text += f"... и еще {len(pending_payments) - 5} платежей"

    await callback_query.message.edit_text(
        payments_text,
        reply_markup=adm.get_payments_keyboard()
    )
    await callback_query.answer()


@dp.callback_query(F.data == "admin_check_payments_now")
async def admin_check_payments_now_handler(callback_query: CallbackQuery):
    pending_payments = adm.get_pending_payments()
    await callback_query.answer(f"Найдено {len(pending_payments)} ожидающих платежей", show_alert=True)
    await admin_check_payments_handler(callback_query)


@dp.callback_query(F.data == "admin_payment_settings")
async def admin_payment_settings_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        "⚙️ Настройки платежей:\n\n"
        "Функционал в разработке...",
        reply_markup=adm.get_payments_keyboard()
    )
    await callback_query.answer()


@dp.callback_query(F.data == "admin_payments_history")
async def admin_payments_history_handler(callback_query: CallbackQuery):
    total_payments, today_payments, total_amount, today_amount, pending_payments = adm.get_payments_stats()

    await callback_query.message.edit_text(
        f"📋 История пополнений:\n\n"
        f"📊 Общая статистика:\n"
        f"• Всего пополнений: {total_payments}\n"
        f"• За сегодня: {today_payments}\n"
        f"• Ожидают проверки: {pending_payments}\n"
        f"• Общая сумма: {total_amount:.2f} руб\n"
        f"• Сумма за сегодня: {today_amount:.2f} руб",
        reply_markup=adm.get_payments_keyboard()
    )
    await callback_query.answer()


@dp.callback_query(F.data == "admin_back")
async def admin_back_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        "👨‍💻 Админ-панель\n\nВыберите действие:",
        reply_markup=adm.get_admin_keyboard()
    )
    await callback_query.answer()


@dp.callback_query(F.data == "notify_enable")
async def notify_enable_handler(callback_query: CallbackQuery):
    adm.update_notify_settings(callback_query.from_user.id, notify_payments=1, notify_new_users=1)
    await callback_query.answer("✅ Уведомления включены", show_alert=True)
    # Возвращаем к настройкам уведомлений
    await admin_notify_settings_handler(callback_query)


@dp.callback_query(F.data == "notify_disable")
async def notify_disable_handler(callback_query: CallbackQuery):
    adm.update_notify_settings(callback_query.from_user.id, notify_payments=0, notify_new_users=0)
    await callback_query.answer("🔕 Уведомления выключены", show_alert=True)
    # Возвращаем к настройкам уведомлений
    await admin_notify_settings_handler(callback_query)


@dp.callback_query(F.data == "admin_notify_settings")
async def admin_notify_settings_handler(callback_query: CallbackQuery):
    notify_payments, notify_new_users = adm.get_notify_settings(callback_query.from_user.id)

    status_payments = "🔔 ВКЛ" if notify_payments else "🔕 ВЫКЛ"
    status_users = "🔔 ВКЛ" if notify_new_users else "🔕 ВЫКЛ"

    await callback_query.message.edit_text(
        f"⚙️ Настройки уведомлений:\n\n"
        f"💰 Уведомления о пополнениях: {status_payments}\n"
        f"👥 Уведомления о новых пользователях: {status_users}\n\n"
        f"Выберите действие:",
        reply_markup=adm.get_notify_settings_keyboard()
    )
    await callback_query.answer()


# ==================== ДОПОЛНИТЕЛЬНЫЕ ОБРАБОТЧИКИ НАВИГАЦИИ ====================

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback_query: CallbackQuery):
    await send_welcome(callback_query.message)
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_cities")
async def back_to_cities_handler(callback_query: CallbackQuery):
    await choose_city(callback_query.message)
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_districts")
async def back_to_districts_handler(callback_query: CallbackQuery):
    await choose_city(callback_query.message)
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_products")
async def back_to_products_handler(callback_query: CallbackQuery):
    await choose_city(callback_query.message)
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_weights")
async def back_to_weights_handler(callback_query: CallbackQuery):
    await bot.send_message(
        callback_query.from_user.id,
        "🔹 Выбери фасовку 🔹",
        reply_markup=keyboards.buy()
    )
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_balance")
async def back_to_balance_handler(callback_query: CallbackQuery, state: FSMContext):
    await replenish_balance(callback_query.message, state)
    await callback_query.answer()


@dp.callback_query(F.data == "cancel_main")
async def cancel_main_handler(callback_query: CallbackQuery):
    await callback_query.message.answer("❌ Действие отменено")
    await send_welcome(callback_query.message)
    await callback_query.answer()


@dp.callback_query(F.data == "to_balance")
async def to_balance_handler(callback_query: CallbackQuery, state: FSMContext):
    await replenish_balance(callback_query.message, state)
    await callback_query.answer()


@dp.callback_query(F.data == "agree_rules")
async def agree_rules_handler(callback_query: CallbackQuery):
    await callback_query.message.answer("✅ Вы согласились с правилами. Можете продолжать использование бота.")
    await callback_query.answer()


@dp.callback_query(F.data == "disagree_rules")
async def disagree_rules_handler(callback_query: CallbackQuery):
    await callback_query.message.answer("❌ Вы не согласились с правилами. Использование бота невозможно.")
    await callback_query.answer()


# ==================== АДМИН-КОМАНДЫ И ОБРАБОТЧИКИ ====================

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message, state: FSMContext):
    await adm.admin_command(message, bot)


# Обработчики админ-панели
@dp.callback_query(F.data.startswith('admin_') | F.data.startswith('broadcast_') | F.data.startswith('notify_'))
async def admin_callbacks(callback_query: CallbackQuery, state: FSMContext):
    await adm.admin_callback_handler(callback_query, bot, state)


# Обработчики подтверждения/отклонения платежей
@dp.callback_query(F.data.startswith('confirm_payment_') | F.data.startswith('reject_payment_'))
async def payment_management(callback_query: CallbackQuery, state: FSMContext):
    await adm.admin_callback_handler(callback_query, bot, state)


# Обработчики состояний админ-панели
@dp.message(adm.AdminStates.waiting_for_broadcast_message)
async def process_broadcast_msg(message: Message, state: FSMContext):
    await adm.process_broadcast_message(message, state, bot)


@dp.message(adm.AdminStates.waiting_for_admin_message)
async def process_admin_msg(message: Message, state: FSMContext):
    await adm.process_admin_message(message, state, bot)


# ==================== ОБРАБОТКА ОШИБОК ====================

@dp.message()
async def unknown_message(message: Message):
    await message.answer(
        "❌ Неизвестная команда\n\n"
        "📋 Используйте кнопки меню или команды:\n"
        "🔸 /start - Главное меню\n"
        "🔸 /help - Помощь\n"
        "🔸 /id - Ваш ID",
        reply_markup=keyboards.main_menu_keyboard()
    )


# ==================== ЗАПУСК БОТА ====================

async def main():
    print("🤖 Бот запущен...")
    print(f"👑 Админ: {config.ADMIN_USERNAME}")
    print(f"📞 Поддержка: {config.SUPPORT_USERNAME}")
    print("🔧 Админ-панель доступна по команде /admin")
    print("🏙️ Доступно 20 городов России с районами")
    print("📦 Улучшенная система заказов с адресом и PDF")
    print("🔐 Система капчи активирована")
    print("⚠️ PDF подтверждение оплаты - ОБЯЗАТЕЛЬНО")
    print("⚡ Ожидаем сообщения...")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")