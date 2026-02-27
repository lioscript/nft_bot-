# nft_bot.py
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import sqlite3
from datetime import datetime

# Змінні беруться з Environment Variables
TOKEN = os.environ.get("8510013282:AAEJF_PdW4BxbTWjd1bq7DksjDndgIqAHFk")
ADMIN_ID = int(os.environ.get("5929338019"))

# Підключення до бази даних SQLite
conn = sqlite3.connect("nft_team.db", check_same_thread=False)
cursor = conn.cursor()

# --- Створення таблиць, якщо їх немає ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    rank INTEGER DEFAULT 1,
    confirmed_profits INTEGER DEFAULT 0,
    is_premium BOOLEAN DEFAULT 0,
    last_payment_date DATE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS profits (
    profit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL DEFAULT 0,
    confirmed BOOLEAN DEFAULT 0,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# --- Функції бота ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет! Я бот для NFT команды. Используйте /newprofit для добавления профита и /level для проверки ранга."
    )

def new_profit(update: Update, context: CallbackContext):
    user = update.message.from_user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user.id, user.username))
    cursor.execute("INSERT INTO profits (user_id, amount) VALUES (?, ?)", (user.id, 0))
    conn.commit()
    context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Пользователь @{user.username} хочет добавить профит. Подтвердите командой /confirm {user.id}"
    )
    update.message.reply_text("Профит отправлен на подтверждение администратору.")

def confirm(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        cursor.execute("UPDATE profits SET confirmed = 1 WHERE user_id = ? AND confirmed = 0", (user_id,))
        cursor.execute("UPDATE users SET confirmed_profits = confirmed_profits + 1 WHERE user_id = ?", (user_id,))
        conn.commit()

        # Автообновление ранга
        cursor.execute("SELECT confirmed_profits, rank FROM users WHERE user_id = ?", (user_id,))
        confirmed, rank = cursor.fetchone()
        new_rank = rank
        if confirmed >= 30:
            new_rank = 3
        elif confirmed >= 10:
            new_rank = 2
        if new_rank != rank:
            cursor.execute("UPDATE users SET rank = ? WHERE user_id = ?", (new_rank, user_id))
            conn.commit()
        update.message.reply_text(f"Профит пользователя {user_id} подтвержден! Новый ранг: {new_rank}")
    except:
        update.message.reply_text("Ошибка. Используйте /confirm <user_id>")

def level(update: Update, context: CallbackContext):
    user = update.message.from_user
    cursor.execute("SELECT confirmed_profits, rank, is_premium FROM users WHERE user_id = ?", (user.id,))
    data = cursor.fetchone()
    if not data:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user.id, user.username))
        conn.commit()
        data = (0, 1, 0)
    confirmed, rank, is_premium = data
    percent = 100 if is_premium else {1:50,2:60,3:70}.get(rank,50)
    update.message.reply_text(
        f"Ваш ранг: {rank}\nПодтвержденные профиты: {confirmed}\nПроцент от прибыли: {percent}%"
    )

# --- Настройка бота ---
updater = Updater(TOKEN)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("newprofit", new_profit))
dp.add_handler(CommandHandler("confirm", confirm))
dp.add_handler(CommandHandler("level", level))

print("Бот запущен...")
updater.start_polling()
updater.idle()
