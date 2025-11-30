from aiogram import Bot, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import sqlite3
import datetime
import asyncio
import re
import config


# Состояния для FSM админ-панели
class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()
    waiting_for_admin_message = State()
    waiting_for_stats = State()
    waiting_for_payment_check = State()


# Клавиатуры для админ-панели
def get_admin_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [types.InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
            [types.InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users_list")],
            [types.InlineKeyboardButton(text="✉️ Отправить сообщение", callback_data="admin_send_message")],
            [types.InlineKeyboardButton(text="💰 Проверить пополнения", callback_data="admin_check_payments")],
            [types.InlineKeyboardButton(text="⚙️ Настройки уведомлений", callback_data="admin_notify_settings")],
            [types.InlineKeyboardButton(text="❌ Закрыть админ-панель", callback_data="admin_close")]
        ]
    )


def get_broadcast_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Подтвердить рассылку", callback_data="broadcast_confirm")],
            [types.InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")]
        ]
    )


def get_admin_cancel_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel")]
        ]
    )


def get_payments_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔄 Проверить сейчас", callback_data="admin_check_payments_now")],
            [types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_payment_settings")],
            [types.InlineKeyboardButton(text="📋 История пополнений", callback_data="admin_payments_history")],
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ]
    )


def get_notify_settings_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔔 Включить уведомления", callback_data="notify_enable")],
            [types.InlineKeyboardButton(text="🔕 Выключить уведомления", callback_data="notify_disable")],
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ]
    )


# Проверка является ли пользователь админом
def is_admin(user_id):
    return user_id in config.ADMIN_IDS


# Инициализация базы данных для пользователей
def init_users_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Инициализация базы данных для платежей
def init_payments_db():
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            amount REAL,
            payment_method TEXT,
            status TEXT,
            comment TEXT,
            payment_date TEXT,
            admin_notified INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_settings (
            admin_id INTEGER PRIMARY KEY,
            notify_payments INTEGER DEFAULT 1,
            notify_new_users INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()


# Функция для добавления пользователя в БД
def add_user_to_db(user_id, username, first_name, last_name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, registration_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, registration_date))
    conn.commit()
    conn.close()


# Функция для добавления платежа
def add_payment(user_id, username, amount, payment_method, comment="", status="pending"):
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    payment_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO payments (user_id, username, amount, payment_method, status, comment, payment_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, amount, payment_method, status, comment, payment_date))

    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return payment_id


# Функция для получения всех пользователей
def get_all_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()
    return [user[0] for user in users]


# Функция для получения статистики
def get_stats():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    # Пользователи за сегодня
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute('SELECT COUNT(*) FROM users WHERE registration_date LIKE ?', (f'{today}%',))
    today_users = cursor.fetchone()[0]

    # Пользователи за неделю
    week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute('SELECT COUNT(*) FROM users WHERE registration_date >= ?', (week_ago,))
    week_users = cursor.fetchone()[0]

    conn.close()
    return total_users, today_users, week_users


# Функция для получения статистики платежей
def get_payments_stats():
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()

    # Общее количество платежей
    cursor.execute('SELECT COUNT(*) FROM payments')
    total_payments = cursor.fetchone()[0]

    # Платежи за сегодня
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute('SELECT COUNT(*) FROM payments WHERE payment_date LIKE ?', (f'{today}%',))
    today_payments = cursor.fetchone()[0]

    # Общая сумма платежей
    cursor.execute('SELECT SUM(amount) FROM payments WHERE status = "completed"')
    total_amount = cursor.fetchone()[0] or 0

    # Сумма за сегодня
    cursor.execute('SELECT SUM(amount) FROM payments WHERE status = "completed" AND payment_date LIKE ?',
                   (f'{today}%',))
    today_amount = cursor.fetchone()[0] or 0

    # Ожидающие проверки платежи
    cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
    pending_payments = cursor.fetchone()[0]

    conn.close()
    return total_payments, today_payments, total_amount, today_amount, pending_payments


# Функция для получения ожидающих платежей
def get_pending_payments():
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, u.first_name, u.username 
        FROM payments p 
        LEFT JOIN users u ON p.user_id = u.user_id 
        WHERE p.status = "pending"
        ORDER BY p.payment_date DESC
    ''')
    payments = cursor.fetchall()
    conn.close()
    return payments


# Функция для обновления статуса платежа
def update_payment_status(payment_id, status):
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE payments SET status = ? WHERE id = ?', (status, payment_id))
    conn.commit()
    conn.close()


# Функция для получения настроек уведомлений
def get_notify_settings(admin_id):
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    cursor.execute('SELECT notify_payments, notify_new_users FROM admin_settings WHERE admin_id = ?', (admin_id,))
    result = cursor.fetchone()
    if not result:
        # Создаем настройки по умолчанию
        cursor.execute('INSERT INTO admin_settings (admin_id, notify_payments, notify_new_users) VALUES (?, 1, 1)',
                       (admin_id,))
        conn.commit()
        notify_payments, notify_new_users = 1, 1
    else:
        notify_payments, notify_new_users = result
    conn.close()
    return notify_payments, notify_new_users


# Функция для обновления настроек уведомлений
def update_notify_settings(admin_id, notify_payments=None, notify_new_users=None):
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()

    if notify_payments is not None:
        cursor.execute('UPDATE admin_settings SET notify_payments = ? WHERE admin_id = ?', (notify_payments, admin_id))
    if notify_new_users is not None:
        cursor.execute('UPDATE admin_settings SET notify_new_users = ? WHERE admin_id = ?',
                       (notify_new_users, admin_id))

    conn.commit()
    conn.close()


# Функция для отправки уведомления админам о новом платеже
async def send_payment_notification(bot: Bot, payment_id, user_id, username, amount, payment_method, comment):
    for admin_id in config.ADMIN_IDS:
        try:
            notify_payments, _ = get_notify_settings(admin_id)
            if notify_payments:
                await bot.send_message(
                    admin_id,
                    f"💰 НОВОЕ ПОПОЛНЕНИЕ!\n\n"
                    f"👤 Пользователь: {username or 'Без username'}\n"
                    f"🆔 ID: {user_id}\n"
                    f"💳 Сумма: {amount} руб\n"
                    f"📱 Метод: {payment_method}\n"
                    f"📝 Комментарий: {comment or 'Нет'}\n"
                    f"🆔 Платеж: #{payment_id}\n"
                    f"🕒 Время: {datetime.datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
                    f"Для проверки используйте /admin",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                types.InlineKeyboardButton(text="✅ Подтвердить",
                                                           callback_data=f"confirm_payment_{payment_id}"),
                                types.InlineKeyboardButton(text="❌ Отклонить",
                                                           callback_data=f"reject_payment_{payment_id}")
                            ],
                            [types.InlineKeyboardButton(text="📋 В админку", callback_data="admin_stats")]
                        ]
                    )
                )
        except Exception as e:
            print(f"Ошибка отправки уведомления админу {admin_id}: {e}")


# Функция для отправки уведомления админам о новом заказе
async def send_order_notification(bot: Bot, user_id, username, product, weight, address, has_pdf=False):
    for admin_id in config.ADMIN_IDS:
        try:
            notify_payments, _ = get_notify_settings(admin_id)
            if notify_payments:
                pdf_status = "✅ Прикреплен" if has_pdf else "❌ ОЖИДАЕТ ПОДТВЕРЖДЕНИЯ"

                await bot.send_message(
                    admin_id,
                    f"🆕 НОВЫЙ ЗАКАЗ!\n\n"
                    f"👤 Пользователь: {username or 'Без username'}\n"
                    f"🆔 ID: {user_id}\n"
                    f"📦 Товар: {product}\n"
                    f"⚖️ Фасовка: {weight}\n"
                    f"📍 Адрес: {address}\n"
                    f"📎 PDF: {pdf_status}\n"
                    f"🕒 Время: {datetime.datetime.now().strftime('%H:%M %d.%m.%Y')}",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [types.InlineKeyboardButton(text="📋 В админку", callback_data="admin_stats")]
                        ]
                    )
                )
        except Exception as e:
            print(f"Ошибка отправки уведомления о заказе админу {admin_id}: {e}")


# Команда админ-панели
async def admin_command(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к админ-панели")
        return

    await message.answer(
        "👨‍💻 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )


# Обработчики callback-запросов админ-панели
async def admin_callback_handler(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return

    data = callback_query.data

    if data == "admin_stats":
        total_users, today_users, week_users = get_stats()
        total_payments, today_payments, total_amount, today_amount, pending_payments = get_payments_stats()

        await callback_query.message.edit_text(
            f"📊 Статистика бота:\n\n"
            f"👥 Пользователи:\n"
            f"• Всего: {total_users}\n"
            f"• За сегодня: {today_users}\n"
            f"• За неделю: {week_users}\n\n"
            f"💰 Финансы:\n"
            f"• Всего пополнений: {total_payments}\n"
            f"• Пополнений за сегодня: {today_payments}\n"
            f"• Ожидают проверки: {pending_payments}\n"
            f"• Общая сумма: {total_amount:.2f} руб\n"
            f"• Сумма за сегодня: {today_amount:.2f} руб\n\n"
            f"🕒 Время: {datetime.datetime.now().strftime('%H:%M %d.%m.%Y')}",
            reply_markup=get_admin_keyboard()
        )

    elif data == "admin_broadcast":
        await callback_query.message.edit_text(
            "📢 Отправьте сообщение для рассылки:\n\n"
            "Поддерживается HTML разметка:\n"
            "<b>Жирный текст</b>\n"
            "<i>Курсив</i>\n"
            "<code>Моноширинный</code>\n"
            "<a href='url'>Ссылка</a>",
            reply_markup=get_admin_cancel_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_broadcast_message)

    elif data == "admin_users_list":
        users = get_all_users()
        if not users:
            await callback_query.message.edit_text(
                "📝 Список пользователей пуст",
                reply_markup=get_admin_keyboard()
            )
            return

        users_text = "👥 Список пользователей (первые 10):\n\n"
        for i, user_id in enumerate(users[:10], 1):
            try:
                user = await bot.get_chat(user_id)
                username = f"@{user.username}" if user.username else "Нет username"
                users_text += f"{i}. {user.first_name} ({username}) - ID: {user_id}\n"
            except:
                users_text += f"{i}. Пользователь ID: {user_id} (недоступен)\n"

        if len(users) > 10:
            users_text += f"\n... и еще {len(users) - 10} пользователей"

        await callback_query.message.edit_text(
            users_text,
            reply_markup=get_admin_keyboard()
        )

    elif data == "admin_send_message":
        await callback_query.message.edit_text(
            "✉️ Введите ID пользователя и сообщение в формате:\n"
            "<code>ID_пользователя</code>\n"
            "Текст сообщения",
            reply_markup=get_admin_cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_for_admin_message)

    elif data == "admin_check_payments":
        pending_payments = get_pending_payments()

        if not pending_payments:
            await callback_query.message.edit_text(
                "✅ Нет ожидающих проверки пополнений",
                reply_markup=get_payments_keyboard()
            )
            return

        payments_text = "⏳ Ожидающие проверки пополнения:\n\n"
        for payment in pending_payments[:5]:  # Показываем первые 5
            payment_id, user_id, username, amount, method, status, comment, date, notified, first_name, user_username = payment
            user_display = f"{first_name} (@{user_username})" if user_username else f"{first_name} (без @)"
            payments_text += f"🆔 #{payment_id}\n👤 {user_display}\n💳 {amount} руб ({method})\n📝 {comment or 'Нет комментария'}\n🕒 {date}\n\n"

        if len(pending_payments) > 5:
            payments_text += f"... и еще {len(pending_payments) - 5} платежей"

        await callback_query.message.edit_text(
            payments_text,
            reply_markup=get_payments_keyboard()
        )

    elif data == "admin_check_payments_now":
        pending_payments = get_pending_payments()
        await callback_query.answer(f"Найдено {len(pending_payments)} ожидающих платежей", show_alert=True)
        await admin_callback_handler(callback_query, bot, state)  # Обновляем сообщение

    elif data == "admin_notify_settings":
        notify_payments, notify_new_users = get_notify_settings(callback_query.from_user.id)

        status_payments = "🔔 ВКЛ" if notify_payments else "🔕 ВЫКЛ"
        status_users = "🔔 ВКЛ" if notify_new_users else "🔕 ВЫКЛ"

        await callback_query.message.edit_text(
            f"⚙️ Настройки уведомлений:\n\n"
            f"💰 Уведомления о пополнениях: {status_payments}\n"
            f"👥 Уведомления о новых пользователях: {status_users}\n\n"
            f"Выберите действие:",
            reply_markup=get_notify_settings_keyboard()
        )

    elif data == "notify_enable":
        update_notify_settings(callback_query.from_user.id, notify_payments=1, notify_new_users=1)
        await callback_query.answer("✅ Уведомления включены", show_alert=True)
        await admin_callback_handler(callback_query, bot, state)

    elif data == "notify_disable":
        update_notify_settings(callback_query.from_user.id, notify_payments=0, notify_new_users=0)
        await callback_query.answer("🔕 Уведомления выключены", show_alert=True)
        await admin_callback_handler(callback_query, bot, state)

    elif data.startswith("confirm_payment_"):
        payment_id = int(data.split("_")[2])
        update_payment_status(payment_id, "completed")

        # Получаем информацию о платеже
        conn = sqlite3.connect('payments.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, amount FROM payments WHERE id = ?', (payment_id,))
        payment = cursor.fetchone()
        conn.close()

        if payment:
            user_id, amount = payment
            try:
                await bot.send_message(
                    user_id,
                    f"✅ Ваше пополнение на {amount} руб подтверждено!\n\n"
                    f"💰 Баланс пополнен. Можете совершать покупки."
                )
            except:
                pass

        await callback_query.answer("✅ Платеж подтвержден", show_alert=True)
        await callback_query.message.edit_text(
            "✅ Платеж подтвержден и пользователь уведомлен",
            reply_markup=get_admin_keyboard()
        )

    elif data.startswith("reject_payment_"):
        payment_id = int(data.split("_")[2])
        update_payment_status(payment_id, "rejected")

        # Получаем информацию о платеже
        conn = sqlite3.connect('payments.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, amount FROM payments WHERE id = ?', (payment_id,))
        payment = cursor.fetchone()
        conn.close()

        if payment:
            user_id, amount = payment
            try:
                await bot.send_message(
                    user_id,
                    f"❌ Ваше пополнение на {amount} руб отклонено!\n\n"
                    f"📞 Свяжитесь с поддержкой для выяснения причин."
                )
            except:
                pass

        await callback_query.answer("❌ Платеж отклонен", show_alert=True)
        await callback_query.message.edit_text(
            "❌ Платеж отклонен и пользователь уведомлен",
            reply_markup=get_admin_keyboard()
        )

    elif data == "admin_close":
        await callback_query.message.delete()
        await callback_query.answer("Админ-панель закрыта")

    elif data == "admin_cancel" or data == "admin_back":
        await state.clear()
        await callback_query.message.edit_text(
            "👨‍💻 Админ-панель\n\nВыберите действие:",
            reply_markup=get_admin_keyboard()
        )


# Обработчик сообщения для рассылки
async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    # Сохраняем сообщение для рассылки
    broadcast_data = {
        'text': message.text or message.caption,
        'parse_mode': 'HTML' if message.html_text else None,
        'reply_markup': message.reply_markup
    }

    await state.update_data(broadcast_message=broadcast_data)

    # Показываем превью и кнопку подтверждения
    preview_text = f"📋 Превью сообщения:\n\n{broadcast_data['text']}\n\n" \
                   f"✅ Подтвердите рассылку для {len(get_all_users())} пользователей"

    await message.answer(
        preview_text,
        reply_markup=get_broadcast_keyboard(),
        parse_mode=broadcast_data['parse_mode']
    )


# Обработчик личного сообщения пользователю
async def process_admin_message(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    try:
        # Парсим ID пользователя и сообщение
        lines = message.text.split('\n')
        user_id = int(lines[0].strip())
        admin_message = '\n'.join(lines[1:]).strip()

        # Отправляем сообщение пользователю
        await bot.send_message(
            user_id,
            f"📨 Сообщение от администратора:\n\n{admin_message}"
        )

        await message.answer(
            f"✅ Сообщение отправлено пользователю ID: {user_id}",
            reply_markup=get_admin_keyboard()
        )

    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите в формате:\n"
            "<code>ID_пользователя</code>\n"
            "Текст сообщения",
            reply_markup=get_admin_cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    except Exception as e:
        await message.answer(
            f"❌ Ошибка отправки: {str(e)}",
            reply_markup=get_admin_keyboard()
        )

    await state.clear()


# Инициализация баз данных при импорте
init_users_db()
init_payments_db()