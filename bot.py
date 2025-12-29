import admin
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "YOUR_BOT_TOKEN_HERE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Курсы")]
    ],
    resize_keyboard=True
)

courses_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Бесплатный курс")],
        [KeyboardButton(text="Платный курс")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user = message.from_user
    database.add_user(user.id, user.username, user.first_name)
    await message.answer("Добро пожаловать! Выберите опцию:", reply_markup=main_menu)

@dp.message(lambda message: message.text == "Курсы")
async def show_courses(message: types.Message):
    await message.answer("Выбери курс:", reply_markup=courses_menu)

@dp.message(lambda message: message.text == "Бесплатный курс")
async def free_course(message: types.Message):
    await message.answer("Вот бесплатный курс: link to group ", reply_markup=main_menu)

@dp.message(lambda message: message.text == "Платный курс")
async def paid_course_handler(message: types.Message):
    try:
        user_id = message.from_user.id
        if database.has_active_subscription(user_id):
            await message.answer(
                "У тебя есть подписка! Вот платный курс: link to group",
                reply_markup=main_menu
            )
        else:
            await message.answer(
                "Нужна подписка!\n\n"
                "Платный курс стоит 299тг месяц.\n"
                "Напиши /buy чтобы купить.",
                reply_markup=main_menu
            )
    except Exception as e:
        logger.error(f"Ошибка в paid_course_handler: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=main_menu)

@dp.message(lambda message: message.text == "Назад")
async def back_to_main(message: types.Message):
    await message.answer("Возвращаемся назад", reply_markup=main_menu)

@dp.message(Command("buy"))
async def buy_command(message: types.Message):
    text = """Оплата подписки:

Сумма: 299тг
Срок: 30 дней

Реквизиты:
Карта: 4400 4301 XXXX XXXX
Получатель: Аслан_Miller

После перевода напишите:
'оплатил 299'

Бот запомнит ваш запрос и выдаст подписку после проверки."""

    await message.answer(text)

@dp.message(lambda m: 'оплат' in m.text.lower() or 'перевел' in m.text.lower())
async def handle_payment(message: types.Message):
    user_id = message.from_user.id
    text = message.text.lower()

    amount = 299
    if '100' in text:
        amount = 100
    elif '299' in text:
        amount = 299
    elif '500' in text:
        amount = 500

    payment_id = database.add_payment(user_id, amount, message.text)

    await message.answer(f"Запрос на оплату #{payment_id} принят. Сумма: {amount}₸. Ожидайте проверки.")

ADMIN_ID = 123456789  # ID администратора

@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа")
        return

    await message.answer("Админ-панель:", reply_markup=admin.get_admin_menu())

@dp.message(lambda m: m.text == "Платежи")
async def show_payments(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    payments_text = admin.get_pending_payments_list()
    await message.answer(payments_text, reply_markup=admin.get_admin_menu())

@dp.message(lambda message: message.text == "Статистика")
async def stats_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    stats = admin.get_stats()
    await message.answer(
        f"Статистика:\n\n"
        f"Всего пользователей: {stats['total_users']}\n"
        f"Активные подписки: {stats['active_subs']}",
        reply_markup=admin.get_admin_menu()
    )

@dp.message(lambda message: message.text == "Пользователи")
async def users_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = admin.get_users_list()
    if not users:
        await message.answer("Нет пользователей.", reply_markup=admin.get_admin_menu())
        return
    text = "Список пользователей:\n\n"
    for user in users:
        user_id, username, first_name = user
        text += f"ID: {user_id}, @{username or 'нет'}, {first_name or 'нет'}\n"
    await message.answer(text, reply_markup=admin.get_admin_menu())

@dp.message(lambda message: message.text == "Выйти из админки")
async def exit_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Выход из админки.", reply_markup=main_menu)

@dp.message(lambda m: m.text and m.text.startswith("/approve_"))
async def approve_payment_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        payment_id = int(message.text.replace("/approve_", ""))
        if database.approve_payment(payment_id):
            await message.answer(f"Платеж {payment_id} подтвержден. Подписка выдана.")
        else:
            await message.answer(f"Платеж {payment_id} не найден.")
    except:
        await message.answer("Ошибка")

@dp.message(lambda m: m.text and m.text.startswith("/reject_"))
async def reject_payment_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        payment_id = int(message.text.replace("/reject_", ""))
        if database.reject_payment(payment_id):
            await message.answer(f"Платеж {payment_id} отклонен.")
        else:
            await message.answer(f"Платеж {payment_id} не найден.")
    except:
        await message.answer("Ошибка")

async def main():
    logger.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
