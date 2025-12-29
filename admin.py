import sqlite3
from datetime import datetime
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton



def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Платежи")],
            [KeyboardButton(text="Статистика")],
            [KeyboardButton(text="Пользователи")],
            [KeyboardButton(text="Выйти из админки")]
        ],
        resize_keyboard=True
    )

def get_stats():
    conn = sqlite3.connect('english_bot.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE end_date > datetime('now')")
    active_subs = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'active_subs': active_subs
    }

def get_users_list(limit=20):
    conn = sqlite3.connect('english_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name FROM users LIMIT ?", (limit,))
    users = cursor.fetchall()
    conn.close()
    return users

def get_pending_payments_list():
    import database
    payments = database.get_pending_payments()
    
    if not payments:
        return "Нет ожидающих платежей"
    
    text = "Ожидающие платежи:\n\n"
    for payment in payments:
        pay_id, user_id, username, first_name, amount, message, created = payment
        text += f"ID: {pay_id}\n"
        text += f"Пользователь: {first_name} (@{username})\n"
        text += f"Сумма: {amount}₸\n"
        text += f"Сообщение: {message}\n"
        text += f"Дата: {created}\n"
        text += f"Подтвердить: /approve_{pay_id}\n"
        text += f"Отклонить: /reject_{pay_id}\n"
        text += "---\n\n"
    
    return text

def is_admin(user_id, admin_id):
    return user_id == admin_id