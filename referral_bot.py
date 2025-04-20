import telebot
from telebot import types
import sqlite3
import logging

# Replace with your bot's token
BOT_TOKEN = "7398067602:AAHkJ183lUT-3s4Y40TIP7hosvYKyFR2CQY"

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Database connection
conn = sqlite3.connect('referral_bot.db')
cursor = conn.cursor()

# Create tables if they don't exist
def create_tables():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            referred_by INTEGER,
            points INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referee_id INTEGER,
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referee_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()

create_tables()

# Function to get user's referral link
def get_referral_link(user_id):
    return f"https://t.me/{bot.get_me().username}?start={user_id}"

# Function to add a new user
def add_user(user_id, username, referred_by=None):
    try:
        cursor.execute("INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)", (user_id, username, referred_by))
        conn.commit()
        logging.info(f"User {user_id} added to database.")
        return True
    except sqlite3.IntegrityError:
        logging.info(f"User {user_id} already exists.")
        return False

# Function to get user's points
def get_user_points(user_id):
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return 0

def update_user_points(user_id, points):
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()

# Function to record referral
def record_referral(referrer_id, referee_id):
    try:
        cursor.execute("INSERT INTO referrals (referrer_id, referee_id) VALUES (?, ?)", (referrer_id, referee_id))
        conn.commit()
        logging.info(f"Referral recorded: {referrer_id} referred {referee_id}")
        return True
    except sqlite3.IntegrityError:
        logging.info(f"Referral already exists: {referrer_id} referred {referee_id}")
        return False

# Function to handle /start command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    referred_by = None

    if len(message.text.split()) > 1:
        referred_by = message.text.split()[1]
        if referred_by.isdigit():
            referred_by = int(referred_by)
        else:
            referred_by = None # Invalid referral format

    if add_user(user_id, username, referred_by):
        if referred_by and referred_by != user_id:
            # Award points to the referrer.  You can adjust the points.
            referrer_points = 10  # Example points
            update_user_points(referred_by, referrer_points)
            record_referral(referred_by, user_id)  # Corrected order
            bot.send_message(referred_by, f"🎉 बधाई हो! आपके रेफ़रल के लिए आपको {referrer_points} पॉइंट्स मिले हैं।")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("🔗 Refer Link")
        item2 = types.KeyboardButton("💰 Points")
        markup.add(item1, item2)

        bot.send_message(user_id, "👋 स्वागत है! अपने दोस्तों को आमंत्रित करें और कमाएं!", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("🔗 Refer Link")
        item2 = types.KeyboardButton("💰 Points")
        markup.add(item1, item2)
        bot.send_message(user_id, "👋 आपका स्वागत है! अपने दोस्तों को आमंत्रित करें और कमाएं!", reply_markup=markup)

# Function to handle text messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if message.text == "🔗 Refer Link":
        referral_link = get_referral_link(user_id)
        bot.send_message(user_id, f"यह आपका रेफ़रल लिंक है: {referral_link}")
    elif message.text == "💰 Points":
        points = get_user_points(user_id)
        bot.send_message(user_id, f"आपके पॉइंट्स: {points}")

# Error handler
@bot.polling_handler(none_stop=True, skip_pending=True)
def error(ex):
    logging.error(ex)

# Main function to start the bot
if __name__ == '__main__':
    bot.polling(none_stop=True, skip_pending=True)
