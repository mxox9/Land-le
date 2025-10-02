import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pymongo
from pymongo import MongoClient
import requests
import time
from datetime import datetime
import random
import urllib.parse
import threading
from bson import ObjectId
from dotenv import load_dotenv
import qrcode
import io
import json

# Load environment variables
load_dotenv()

# Configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN', '8052955693:AAGf3qd5VXfq1I7d0_lM0eE3YwKFuBXLxvw')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://saifulmolla79088179_db_user:17gNrX0pC3bPqVaG@cluster0.fusvqca.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '6052975324').split(',')]
CHANNEL_ID = os.getenv('CHANNEL_ID', '@prooflelo1')
SMM_API_URL = os.getenv('SMM_API_URL', 'https://smm-jupiter.com/api/v2')
SMM_API_KEY = os.getenv('SMM_API_KEY', 'c33fb3166621856879b2e486b99a30f0c442ac92')
PROOF_CHANNEL = "@prooflelo1"
SUPPORT_LINK = "https://t.me/your_support"
BOT_LINK = "https://t.me/your_bot"

# Payment API Keys
AUTODEP_API_KEY = "LY81vEV7"
AUTODEP_MERCHANT_KEY = "WYcmQI71591891985230"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# MongoDB connection for user data only
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.smm_bot
    users_collection = db.users
    orders_collection = db.orders
    deposits_collection = db.deposits
    user_sessions_collection = db.user_sessions
    admin_logs_collection = db.admin_logs
    print("✅ MᴏɴɢᴏDB ᴄᴏɴɴᴇᴄᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
except Exception as e:
    print(f"❌ MᴏɴɢᴏDB ᴄᴏɴɴᴇᴄᴛɪᴏɴ ᴇʀʀᴏʀ: {e}")
    exit(1)

# Image URLs
WELCOME_IMAGE = "https://t.me/prooflelo1/135?single"
SERVICE_IMAGE = "https://t.me/prooflelo1/138?single"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/136?single"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/137?single"
HISTORY_IMAGE = "https://t.me/prooflelo1/139?single"
REFER_IMAGE = "https://t.me/prooflelo1/17"
ADMIN_IMAGE = "https://t.me/prooflelo1/140?single"

# Services data (LOCAL STORAGE - same as bot2.py but with land.py font style)
SERVICES = {
    "Iɴsᴛᴀɢʀᴀᴍ": {
        "📸 Iɴsᴛᴀɢʀᴀᴍ Lɪᴋᴇs": {"id": 101, "price": 30, "min": 100, "max": 10000, "unit": 1000},
        "👁 Iɴsᴛᴀɢʀᴀᴍ Vɪᴇᴡs": {"id": 13685, "price": 50, "min": 100, "max": 50000, "unit": 1000},
        "👤 Iɴsᴛᴀɢʀᴀᴍ Fᴏʟʟᴏᴡᴇʀs": {"id": 103, "price": 80, "min": 100, "max": 10000, "unit": 1000}
    },
    "Fᴀᴄᴇʙᴏᴏᴋ": {
        "👍 Fᴀᴄᴇʙᴏᴏᴋ Lɪᴋᴇs": {"id": 201, "price": 40, "min": 100, "max": 20000, "unit": 1000},
        "👁 Fᴀᴄᴇʙᴏᴏᴋ Vɪᴇᴡs": {"id": 202, "price": 60, "min": 100, "max": 50000, "unit": 1000},
        "👥 Fᴀᴄᴇʙᴏᴏᴋ Fᴏʟʟᴏᴡᴇʀs": {"id": 203, "price": 90, "min": 100, "max": 15000, "unit": 1000}
    },
    "YᴏᴜTᴜʙᴇ": {
        "👍 YᴏᴜTᴜʙᴇ Lɪᴋᴇs": {"id": 301, "price": 35, "min": 100, "max": 50000, "unit": 1000},
        "👁 YᴏᴜTᴜʙᴇ Vɪᴇᴡs": {"id": 302, "price": 45, "min": 100, "max": 100000, "unit": 1000},
        "🔔 YᴏᴜTᴜʙᴇ Sᴜʙsᴄʀɪʙᴇʀs": {"id": 303, "price": 120, "min": 100, "max": 10000, "unit": 1000}
    },
    "Tᴇʟᴇɢʀᴀᴍ": {
        "👥 Tᴇʟᴇɢʀᴀᴍ Mᴇᴍʙᴇʀs": {"id": 401, "price": 25, "min": 100, "max": 50000, "unit": 1000},
        "👍 Tᴇʟᴇɢʀᴀᴍ Pᴏsᴛ Lɪᴋᴇs": {"id": 402, "price": 20, "min": 100, "max": 100000, "unit": 1000},
        "👁 Tᴇʟᴇɢʀᴀᴍ Pᴏsᴛ Vɪᴇᴡs": {"id": 403, "price": 15, "min": 100, "max": 100000, "unit": 1000}
    }
}

# Font style mapping for land.py style
FONT_STYLE = {
    'A': 'A', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'E', 'F': 'ғ', 'G': 'ɢ', 'H': 'ʜ', 
    'I': 'I', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'M', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ',
    'Q': 'Q', 'R': 'ʀ', 'S': 's', 'T': 'T', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'W', 'X': 'x',
    'Y': 'Y', 'Z': 'Z',
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ',
    'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
    'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
    'y': 'ʏ', 'z': 'ᴢ'
}

def convert_to_styled(text):
    """Cᴏɴᴠᴇʀᴛ ᴛᴇxᴛ ᴛᴏ ʟᴀɴᴅ.ᴘʏ ғᴏɴᴛ sᴛʏʟᴇ"""
    result = ""
    for char in text:
        if char in FONT_STYLE:
            result += FONT_STYLE[char]
        else:
            result += char
    return result

# MongoDB Helper Functions (for user balances only)
def get_user(user_id):
    """Gᴇᴛ ᴜsᴇʀ ғʀᴏᴍ MᴏɴɢᴏDB"""
    return users_collection.find_one({"user_id": user_id})

def create_user(user_id, username):
    """Cʀᴇᴀᴛᴇ ɴᴇᴡ ᴜsᴇʀ ɪɴ MᴏɴɢᴏDB"""
    if not get_user(user_id):
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0.0,
            "total_deposits": 0.0,
            "total_spent": 0.0,
            "banned": False,
            "joined_date": datetime.now()
        })

def update_balance(user_id, amount):
    """Uᴘᴅᴀᴛᴇ ᴜsᴇʀ ʙᴀʟᴀɴᴄᴇ ɪɴ MᴏɴɢᴏDB"""
    user = get_user(user_id)
    if not user:
        create_user(user_id, f"Usᴇʀ_{user_id}")
        user = get_user(user_id)
    
    new_balance = user.get("balance", 0) + amount
    
    if amount > 0:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"balance": new_balance}, "$inc": {"total_deposits": amount}}
        )
    else:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"balance": new_balance}, "$inc": {"total_spent": abs(amount)}}
        )
    
    return new_balance

def get_balance(user_id):
    """Gᴇᴛ ᴜsᴇʀ ʙᴀʟᴀɴᴄᴇ ғʀᴏᴍ MᴏɴɢᴏDB"""
    user = get_user(user_id)
    return user.get("balance", 0) if user else 0

def add_order(user_id, service_name, link, quantity, cost, api_order_id):
    """Aᴅᴅ ᴏʀᴅᴇʀ ᴛᴏ MᴏɴɢᴏDB"""
    orders_collection.insert_one({
        "user_id": user_id,
        "service_name": service_name,
        "link": link,
        "quantity": quantity,
        "cost": cost,
        "status": "Pᴇɴᴅɪɴɢ",
        "api_order_id": api_order_id,
        "order_date": datetime.now()
    })

def get_user_orders(user_id, limit=5):
    """Gᴇᴛ ᴜsᴇʀ ᴏʀᴅᴇʀs ғʀᴏᴍ MᴏɴɢᴏDB"""
    return list(orders_collection.find(
        {"user_id": user_id}
    ).sort("order_date", -1).limit(limit))

def add_deposit(user_id, amount, utr):
    """Aᴅᴅ ᴅᴇᴘᴏsɪᴛ ᴛᴏ MᴏɴɢᴏDB"""
    deposits_collection.insert_one({
        "user_id": user_id,
        "amount": amount,
        "utr": utr,
        "status": "Pᴇɴᴅɪɴɢ",
        "deposit_date": datetime.now()
    })

def update_deposit_status(utr, status):
    """Uᴘᴅᴀᴛᴇ ᴅᴇᴘᴏsɪᴛ sᴛᴀᴛᴜs ɪɴ MᴏɴɢᴏDB"""
    deposits_collection.update_one(
        {"utr": utr},
        {"$set": {"status": status}}
    )

# User session functions using MongoDB
def save_user_data(user_id, key, value):
    """Sᴀᴠᴇ ᴜsᴇʀ sᴇssɪᴏɴ ᴅᴀᴛᴀ ɪɴ MᴏɴɢᴏDB"""
    user_sessions_collection.update_one(
        {"user_id": user_id},
        {"$set": {key: value}},
        upsert=True
    )

def get_user_data(user_id, key):
    """Gᴇᴛ ᴜsᴇʀ sᴇssɪᴏɴ ᴅᴀᴛᴀ ғʀᴏᴍ MᴏɴɢᴏDB"""
    session = user_sessions_collection.find_one({"user_id": user_id})
    return session.get(key) if session else None

def delete_user_data(user_id, key):
    """Dᴇʟᴇᴛᴇ sᴘᴇᴄɪғɪᴄ ᴜsᴇʀ sᴇssɪᴏɴ ᴅᴀᴛᴀ"""
    user_sessions_collection.update_one(
        {"user_id": user_id},
        {"$unset": {key: ""}}
    )

def clear_all_user_data(user_id):
    """Cʟᴇᴀʀ ᴀʟʟ ᴜsᴇʀ sᴇssɪᴏɴ ᴅᴀᴛᴀ"""
    user_sessions_collection.delete_one({"user_id": user_id})

def get_all_users():
    """Gᴇᴛ ᴛᴏᴛᴀʟ ᴜsᴇʀs ᴄᴏᴜɴᴛ"""
    return users_collection.count_documents({})

def get_total_orders():
    """Gᴇᴛ ᴛᴏᴛᴀʟ ᴏʀᴅᴇʀs ᴄᴏᴜᴜɴᴛ"""
    return orders_collection.count_documents({})

def get_total_deposits():
    """Gᴇᴛ ᴛᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛs ᴀᴍᴏᴜɴᴛ"""
    pipeline = [
        {"$match": {"status": "Cᴏᴍᴘʟᴇᴛᴇᴅ"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    result = list(deposits_collection.aggregate(pipeline))
    return result[0]["total"] if result else 0

def get_total_spent():
    """Gᴇᴛ ᴛᴏᴛᴀʟ sᴘᴇɴᴛ ᴀᴍᴏᴜɴᴛ"""
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$cost"}}}
    ]
    result = list(orders_collection.aggregate(pipeline))
    return result[0]["total"] if result else 0

def log_admin_action(admin_id, action, details):
    """Lᴏɢ ᴀᴅᴍɪɴ ᴀᴄᴛɪᴏɴs ᴛᴏ ᴅᴀᴛᴀʙᴀsᴇ"""
    admin_logs_collection.insert_one({
        "admin_id": admin_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now()
    })

# Keyboard helpers with land.py font style
def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💰 Dᴇᴘᴏsɪᴛ", callback_data="deposit"),
        InlineKeyboardButton("🛒 Oʀᴅᴇʀ", callback_data="order"),
        InlineKeyboardButton("📋 Oʀᴅᴇʀs", callback_data="orders"),
        InlineKeyboardButton("👥 Rᴇғᴇʀ", callback_data="refer"),
        InlineKeyboardButton("👤 Aᴄᴄᴏᴜɴᴛ", callback_data="account"),
        InlineKeyboardButton("📊 Sᴛᴀᴛs", callback_data="stats"),
        InlineKeyboardButton("ℹ️ Sᴜᴘᴘᴏʀᴛ", callback_data="support")
    ]
    keyboard.add(*buttons)
    if 6052975324 in ADMIN_IDS:
        keyboard.add(InlineKeyboardButton("👑 Aᴅᴍɪɴ", callback_data="admin"))
    return keyboard

def categories_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for category in SERVICES.keys():
        emoji = "📸" if category == "Iɴsᴛᴀɢʀᴀᴍ" else "👍" if category == "Fᴀᴄᴇʙᴏᴏᴋ" else "📺" if category == "YᴏᴜTᴜʙᴇ" else "📱"
        buttons.append(InlineKeyboardButton(f"{emoji} {category}", callback_data=f"cat_{category}"))
    
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land"))
    return keyboard

def services_keyboard(category):
    keyboard = InlineKeyboardMarkup()
    for service_name in SERVICES[category].keys():
        keyboard.add(InlineKeyboardButton(service_name, callback_data=f"serv_{category}_{service_name}"))
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order"))
    return keyboard

def admin_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ", callback_data="admin_balance"),
        InlineKeyboardButton("👤 Usᴇʀ Cᴏɴᴛʀᴏʟ", callback_data="admin_users"),
        InlineKeyboardButton("📢 Bʀᴏᴀᴅᴄᴀsᴛ", callback_data="admin_broadcast"),
        InlineKeyboardButton("📊 Sᴛᴀᴛs", callback_data="admin_stats"),
        InlineKeyboardButton("🔙 Mᴀɪɴ Mᴇɴᴜ", callback_data="land")
    ]
    keyboard.add(*buttons)
    return keyboard

def back_button_only():
    """Bᴀᴄᴋ ʙᴜᴛᴛᴏɴ ᴏɴʟʏ ᴋᴇʏʙᴏᴀʀᴅ"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    return markup

def deposit_confirmation_keyboard():
    """Dᴇᴘᴏsɪᴛ ᴄᴏɴғɪʀᴍᴀᴛɪᴏɴ ᴋᴇʏʙᴏᴀʀᴅ"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ I Hᴀᴠᴇ Pᴀɪᴅ", callback_data="confirm_deposit"))
    markup.add(InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="main_menu"))
    return markup

# Start command with land.py font style
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"Usᴇʀ_{user_id}"
    
    create_user(user_id, username)
    
    welcome_text = convert_to_styled(f"""
Wᴇʟᴄᴏᴍᴇ ᴛᴏ SMM Bᴏᴛ!

Bᴜʏ sᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ sᴇʀᴠɪᴄᴇs ᴀᴛ ᴄʜᴇᴀᴘᴇsᴛ ʀᴀᴛᴇs!

Iɴsᴛᴀɢʀᴀᴍ, Fᴀᴄᴇʙᴏᴏᴋ, YᴏᴜTᴜʙᴇ & Tᴇʟᴇɢʀᴀᴍ sᴇʀᴠɪᴄᴇs
Hɪɢʜ Qᴜᴀʟɪᴛʏ & Fᴀsᴛ Dᴇʟɪᴠᴇʀʏ
Sᴇᴄᴜʀᴇ Pᴀʏᴍᴇɴᴛs & 24/7 Sᴜᴘᴘᴏʀᴛ

Sᴛᴀʀᴛ ʙʏ ᴅᴇᴘᴏsɪᴛɪɴɢ ғᴜɴᴅs ᴏʀ ᴘʟᴀᴄɪɴɢ ᴀɴ ᴏʀᴅᴇʀ!
    """)
    
    bot.send_photo(
        chat_id=user_id,
        photo=WELCOME_IMAGE,
        caption=welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='HTML'
    )

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    try:
        if call.data == "land":
            try:
                bot.delete_message(user_id, message_id)
            except:
                pass
            start_command(call.message)
        
        elif call.data == "main_menu":
            show_main_menu(call)
        
        elif call.data == "deposit":
            show_deposit_menu(user_id, message_id)
        
        elif call.data == "order":
            show_categories(user_id, message_id)
        
        elif call.data == "orders":
            show_orders(user_id, message_id)
        
        elif call.data == "refer":
            show_refer(user_id, message_id)
        
        elif call.data == "account":
            show_account(user_id, message_id)
        
        elif call.data == "stats":
            show_stats(user_id, message_id)
        
        elif call.data == "support":
            show_support(user_id, message_id)
        
        elif call.data.startswith("cat_"):
            category = call.data[4:]
            show_services(user_id, message_id, category)
        
        elif call.data.startswith("serv_"):
            parts = call.data.split("_")
            if len(parts) >= 3:
                category = parts[1]
                service_name = " ".join(parts[2:])
                start_order_flow(user_id, message_id, category, service_name)
        
        elif call.data == "check_txn":
            check_transaction(call)
        
        elif call.data == "confirm_deposit":
            process_deposit_confirmation(call)
        
        elif call.data == "admin":
            if user_id in ADMIN_IDS:
                show_admin_panel(user_id, message_id)
            else:
                bot.answer_callback_query(call.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ!", show_alert=True)
        
        elif call.data.startswith("admin_"):
            if user_id in ADMIN_IDS:
                handle_admin_commands(call)
            else:
                bot.answer_callback_query(call.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ!", show_alert=True)
                
    except Exception as e:
        print(f"Eʀʀᴏʀ ɪɴ ᴄᴀʟʟʙᴀᴄᴋ: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!", show_alert=True)

# Deposit flow with land.py font style
def show_deposit_menu(user_id, message_id):
    # Clear old data
    delete_user_data(user_id, "deposit_utr")
    delete_user_data(user_id, "deposit_amount")
    delete_user_data(user_id, "deposit_qr_msg")
    
    deposit_text = convert_to_styled("Eɴᴛᴇʀ Tʜᴇ Aᴍᴏᴜɴᴛ Yᴏᴜ Wᴀɴᴛ Tᴏ Dᴇᴘᴏsɪᴛ")
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=DEPOSIT_IMAGE,
                caption=deposit_text
            ),
            reply_markup=None
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=DEPOSIT_IMAGE,
            caption=deposit_text
        )
    
    msg = bot.send_message(user_id, "💳 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇᴘᴏsɪᴛ (ɪɴ ₹):")
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    user_id = message.from_user.id
    
    try:
        amount = float(message.text)

        # Generate random 12-digit numeric UTR
        utr = str(random.randint(100000000000, 999999999999))

        # Save UTR + amount
        save_user_data(user_id, "deposit_utr", utr)
        save_user_data(user_id, "deposit_amount", amount)

        # Create UPI payment link
        upi_link = f"upi://pay?pa=paytm.s1m11be@pty&pn=Paytm&am={amount}&tn=Deposit&tr={utr}"

        # Generate QR using QuickChart API
        qr_api = f"https://quickchart.io/qr?text={urllib.parse.quote(upi_link)}&size=300"

        # Send QR with Paid ✅ + Back 🔙 buttons
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("𝗣𝗮𝗶𝗱 ✅", callback_data="check_txn"),
            InlineKeyboardButton("Bᴀᴄᴋ 🔙", callback_data="land")
        )

        sent = bot.send_photo(
            chat_id=user_id,
            photo=qr_api,
            caption=convert_to_styled(f"""
Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ

Aᴍᴏᴜɴᴛ: ₹{amount}
UTR: `{utr}`

Sᴄᴀɴ ᴛʜᴇ QR ᴄᴏᴅᴇ ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ ᴘᴀʏᴍᴇɴᴛ
            """),
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

        # Save QR message id for later deletion
        save_user_data(user_id, "deposit_qr_msg", sent.message_id)

    except Exception as e:
        bot.send_message(
            user_id,
            "❌ Iɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ."
        )
        show_deposit_menu(user_id, message.message_id)

def check_transaction(call):
    user_id = call.from_user.id
    
    try:
        utr = get_user_data(user_id, "deposit_utr")
        amount = get_user_data(user_id, "deposit_amount")
        qr_msg_id = get_user_data(user_id, "deposit_qr_msg")

        if utr and amount:
            # Autodep API call
            url = f"https://erox-autodep-api.onrender.com/api?key={AUTODEP_API_KEY}&merchantkey={AUTODEP_MERCHANT_KEY}&transactionid={utr}"
            
            try:
                resp = requests.get(url, timeout=10).json()
                
                if resp.get("result", {}).get("STATUS") == "TXN_SUCCESS":
                    # Update balance in MongoDB
                    points = float(amount)
                    update_balance(user_id, points)
                    add_deposit(user_id, amount, utr)
                    update_deposit_status(utr, "Cᴏᴍᴘʟᴇᴛᴇᴅ")

                    # Delete QR scanner if exists
                    try:
                        if qr_msg_id:
                            bot.delete_message(chat_id=user_id, message_id=qr_msg_id)
                    except Exception as e:
                        pass

                    # Get updated balance
                    balance = get_balance(user_id)

                    # Notify user
                    success_msg = bot.send_message(
                        chat_id=user_id,
                        text=convert_to_styled(f"✅ Tʀᴀɴsᴀᴄᴛɪᴏɴ sᴜᴄᴄᴇssғᴜʟ! ₹{amount} ᴀᴅᴅᴇᴅ.\nNᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{balance}")
                    )

                    # Notify admin
                    try:
                        bot.send_message(
                            chat_id=ADMIN_IDS[0],
                            text=convert_to_styled(f"✅ SUCCESS\n\nUsᴇʀ {user_id} ᴅᴇᴘᴏsɪᴛᴇᴅ ₹{amount}.\nNᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{balance}")
                        )
                    except:
                        pass

                    # Clear deposit data
                    delete_user_data(user_id, "deposit_utr")
                    delete_user_data(user_id, "deposit_amount")
                    delete_user_data(user_id, "deposit_qr_msg")

                    # Show main menu after 2 seconds
                    time.sleep(2)
                    start_command(success_msg)

                else:
                    bot.answer_callback_query(
                        callback_query_id=call.id,
                        text="❌ Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴅᴇᴘᴏsɪᴛᴇᴅ ʏᴇᴛ. Pʟᴇᴀsᴇ ᴘᴀʏ ғɪʀsᴛ.",
                        show_alert=True
                    )

            except Exception as api_error:
                bot.answer_callback_query(callback_query_id=call.id, text="❌ API ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ.", show_alert=True)

        else:
            bot.answer_callback_query(callback_query_id=call.id, text="⚠️ Nᴏ ᴘᴇɴᴅɪɴɢ ᴅᴇᴘᴏsɪᴛ ғᴏᴜɴᴅ.", show_alert=True)

    except Exception as e:
        bot.answer_callback_query(callback_query_id=call.id, text="❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ.", show_alert=True)

def process_deposit_confirmation(call):
    """Pʀᴏᴄᴇss ᴅᴇᴘᴏsɪᴛ ᴄᴏɴғɪʀᴍᴀᴛɪᴏɴ"""
    user_id = call.from_user.id
    bot.answer_callback_query(call.id, "Pʟᴇᴀsᴇ ᴜsᴇ ᴛʜᴇ 'Pᴀɪᴅ ✅' ʙᴜᴛᴛᴏɴ ᴛᴏ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴛʀᴀɴsᴀᴄᴛɪᴏɴ.")

# Order flow with land.py font style
def show_categories(user_id, message_id):
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=SERVICE_IMAGE,
                caption=convert_to_styled("Sᴇʟᴇᴄᴛ ᴀ Cᴀᴛᴇɢᴏʀʏ\n\nCʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ᴛᴏ ᴠɪᴇᴡ sᴇʀᴠɪᴄᴇs:")
            ),
            reply_markup=categories_keyboard(),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=SERVICE_IMAGE,
            caption=convert_to_styled("Sᴇʟᴇᴄᴛ ᴀ Cᴀᴛᴇɢᴏʀʏ\n\nCʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ᴛᴏ ᴠɪᴇᴡ sᴇʀᴠɪᴄᴇs:"),
            reply_markup=categories_keyboard(),
            parse_mode='Markdown'
        )

def show_services(user_id, message_id, category):
    if category not in SERVICES:
        bot.answer_callback_query(message_id, "❌ Cᴀᴛᴇɢᴏʀʏ ɴᴏᴛ ғᴏᴜɴᴅ!", show_alert=True)
        return
        
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=SERVICE_IMAGE,
                caption=convert_to_styled(f"{category} Sᴇʀᴠɪᴄᴇs\n\nSᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ:")
            ),
            reply_markup=services_keyboard(category),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=SERVICE_IMAGE,
            caption=convert_to_styled(f"{category} Sᴇʀᴠɪᴄᴇs\n\nSᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ:"),
            reply_markup=services_keyboard(category),
            parse_mode='Markdown'
        )

def start_order_flow(user_id, message_id, category, service_name):
    if category not in SERVICES or service_name not in SERVICES[category]:
        bot.answer_callback_query(message_id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!", show_alert=True)
        return
        
    service = SERVICES[category][service_name]
    
    service_info = convert_to_styled(f"""
{service_name}

Pʀɪᴄᴇ: ₹{service['price']}/1000
Mɪɴɪᴍᴜᴍ: {service['min']}
Mᴀxɪᴍᴜᴍ: {service['max']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ ғᴏʀ ʏᴏᴜʀ ᴏʀᴅᴇʀ:
    """)
    
    try:
        bot.edit_message_caption(
            chat_id=user_id,
            message_id=message_id,
            caption=service_info,
            reply_markup=None,
            parse_mode='Markdown'
        )
    except:
        bot.send_message(user_id, service_info, parse_mode='Markdown')
    
    # Store service info in session using MongoDB
    save_user_data(user_id, "order_category", category)
    save_user_data(user_id, "order_service_name", service_name)
    save_user_data(user_id, "order_service_data", json.dumps(service))
    
    msg = bot.send_message(user_id, "🔗 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ʟɪɴᴋ:")
    bot.register_next_step_handler(msg, process_order_link)

def process_order_link(message):
    user_id = message.from_user.id
    link = message.text.strip()
    
    category = get_user_data(user_id, "order_category")
    service_name = get_user_data(user_id, "order_service_name")
    service_data = get_user_data(user_id, "order_service_data")
    
    if not all([category, service_name, service_data]):
        bot.send_message(user_id, "❌ Sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ sᴛᴀʀᴛ ᴏᴠᴇʀ.")
        return
    
    service = json.loads(service_data)
    save_user_data(user_id, "order_link", link)
    
    bot.send_message(
        user_id,
        convert_to_styled(f"""
Eɴᴛᴇʀ Qᴜᴀɴᴛɪᴛʏ

Sᴇʀᴠɪᴄᴇ: {service_name}
Lɪɴᴋ: {link}

Mɪɴɪᴍᴜᴍ: {service['min']}
Mᴀxɪᴍᴜᴍ: {service['max']}

Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ:
        """),
        parse_mode='Markdown'
    )
    
    bot.register_next_step_handler(message, process_order_quantity)

def process_order_quantity(message):
    user_id = message.from_user.id
    
    category = get_user_data(user_id, "order_category")
    service_name = get_user_data(user_id, "order_service_name")
    service_data = get_user_data(user_id, "order_service_data")
    link = get_user_data(user_id, "order_link")
    
    if not all([category, service_name, service_data, link]):
        bot.send_message(user_id, "❌ Sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ sᴛᴀʀᴛ ᴏᴠᴇʀ.")
        return
    
    try:
        quantity = int(message.text)
        service = json.loads(service_data)
        
        # Validate quantity
        if quantity < service['min'] or quantity > service['max']:
            bot.send_message(
                user_id,
                f"❌ Qᴜᴀɴᴛɪᴛʏ ᴍᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ {service['min']} ᴀɴᴅ {service['max']}. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ."
            )
            return
        
        # Calculate cost
        cost = (quantity / service['unit']) * service['price']
        
        # Check balance from MongoDB
        balance = get_balance(user_id)
        if balance < cost:
            bot.send_message(
                user_id,
                convert_to_styled(f"""
Iɴsᴜғғɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ

Rᴇǫᴜɪʀᴇᴅ: ₹{cost:.2f}
Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ: ₹{balance:.2f}

Pʟᴇᴀsᴇ ᴅᴇᴘᴏsɪᴛ ғɪʀsᴛ.
                """)
            )
            return
        
        # Place order via SMM API
        try:
            # Actual SMM API call
            params = {
                "key": SMM_API_KEY,
                "action": "add",
                "service": service['id'],
                "link": link,
                "quantity": quantity
            }
            response = requests.get(SMM_API_URL, params=params, timeout=30)
            api_response = response.json()
            
            api_order_id = api_response.get("order", "UNKNOWN")
            
            # Deduct balance and save order in MongoDB
            update_balance(user_id, -cost)
            add_order(user_id, service_name, link, quantity, cost, api_order_id)
            
            # Get updated balance
            new_balance = get_balance(user_id)
            
            # Confirm to user
            confirmation_text = convert_to_styled(f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

Sᴇʀᴠɪᴄᴇ: {service_name}
Lɪɴᴋ: {link}
Qᴜᴀɴᴛɪᴛʏ: {quantity}
Cᴏsᴛ: ₹{cost:.2f}
Oʀᴅᴇʀ ID: {api_order_id}
Bᴀʟᴀɴᴄᴇ: ₹{new_balance:.2f}

Yᴏᴜ ᴄᴀɴ ᴄʜᴇᴄᴋ ᴏʀᴅᴇʀ sᴛᴀᴛᴜs ɪɴ Oʀᴅᴇʀs ᴍᴇɴᴜ.
            """)
            
            bot.send_message(user_id, confirmation_text, parse_mode='Markdown')
            
            # Send to proof channel
            proof_text = convert_to_styled(f"""
🎉 Nᴇᴡ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ!

Usᴇʀ: @{message.from_user.username or user_id}
Sᴇʀᴠɪᴄᴇ: {service_name}
Qᴜᴀɴᴛɪᴛʏ: {quantity}
Aᴍᴏᴜɴᴛ: ₹{cost:.2f}
Oʀᴅᴇʀ ID: {api_order_id}

Bᴏᴛ Hᴇʀᴇ 🈴
            """)
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🤖 Bᴏᴛ Hᴇʀᴇ 🈴", url=BOT_LINK))
            
            try:
                bot.send_message(
                    PROOF_CHANNEL,
                    proof_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            except:
                pass
            
            # Clear session data
            clear_all_user_data(user_id)
            
        except Exception as e:
            bot.send_message(user_id, f"❌ Eʀʀᴏʀ ᴘʟᴀᴄɪɴɢ ᴏʀᴅᴇʀ: {str(e)}")
            
    except ValueError:
        bot.send_message(user_id, "❌ Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")

# Other user menus with land.py font style
def show_orders(user_id, message_id):
    orders = get_user_orders(user_id)
    
    if not orders:
        orders_text = convert_to_styled("Nᴏ ᴏʀᴅᴇʀs ғᴏᴜɴᴅ.\n\nYᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴘʟᴀᴄᴇᴅ ᴀɴʏ ᴏʀᴅᴇʀs ʏᴇᴛ.")
    else:
        orders_text = convert_to_styled("Yᴏᴜʀ Lᴀsᴛ 5 Oʀᴅᴇʀs\n\n")
        for order in orders[:5]:
            status_emoji = {
                'Pᴇɴᴅɪɴɢ': '⏳',
                'Iɴ Pʀᴏɢʀᴇss': '🔄', 
                'Cᴏᴍᴘʟᴇᴛᴇᴅ': '✅',
                'Cᴀɴᴄᴇʟʟᴇᴅ': '❌'
            }.get(order.get("status", "Pᴇɴᴅɪɴɢ"), '⏳')
            
            orders_text += convert_to_styled(f"""
{status_emoji} Oʀᴅᴇʀ
Sᴇʀᴠɪᴄᴇ: {order.get('service_name', 'N/A')}
Lɪɴᴋ: {order.get('link', 'N/A')[:30]}...
Qᴜᴀɴᴛɪᴛʏ: {order.get('quantity', 0)}
Cᴏsᴛ: ₹{order.get('cost', 0):.2f}
Tɪᴍᴇ: {order.get('order_date', datetime.now()).strftime('%Y-%m-%d %H:%M')}
Sᴛᴀᴛᴜs: {order.get('status', 'Pᴇɴᴅɪɴɢ')}

""")
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=HISTORY_IMAGE,
                caption=orders_text
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land")
            ),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=HISTORY_IMAGE,
            caption=orders_text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land")
            ),
            parse_mode='Markdown'
        )

def show_refer(user_id, message_id):
    refer_link = f"https://t.me/share/url?url={BOT_LINK}&text=Join%20this%20awesome%20SMM%20bot!"
    bonus = 10
    
    refer_text = convert_to_styled(f"""
Rᴇғᴇʀʀᴀʟ Pʀᴏɢʀᴀᴍ

Yᴏᴜʀ Rᴇғᴇʀʀᴀʟ Lɪɴᴋ:
`{refer_link}`

Rᴇғᴇʀʀᴀʟ Bᴏɴᴜs: ₹{bonus} ᴘᴇʀ sᴜᴄᴄᴇssғᴜʟ ʀᴇғᴇʀʀᴀʟ

Hᴏᴡ ɪᴛ ᴡᴏʀᴋs:
1. Sʜᴀʀᴇ ʏᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ
2. Wʜᴇɴ sᴏᴍᴇᴏɴᴇ ᴊᴏɪɴs ᴜsɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ
3. Yᴏᴜ ɢᴇᴛ ₹{bonus} ʙᴏɴᴜs ᴡʜᴇɴ ᴛʜᴇʏ ᴅᴇᴘᴏsɪᴛ

Sᴛᴀʀᴛ ʀᴇғᴇʀʀɪɴɢ ᴀɴᴅ ᴇᴀʀɴ ᴍᴏʀᴇ!
    """)
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📤 Sʜᴀʀᴇ Lɪɴᴋ", url=f"tg://msg_url?url={urllib.parse.quote(refer_link)}"))
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land"))
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=REFER_IMAGE,
                caption=refer_text
            ),
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=REFER_IMAGE,
            caption=refer_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

def show_account(user_id, message_id):
    user = get_user(user_id)
    if not user:
        create_user(user_id, f"Usᴇʀ_{user_id}")
        user = get_user(user_id)
    
    account_text = convert_to_styled(f"""
Aᴄᴄᴏᴜɴᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ

Usᴇʀ ID: `{user.get('user_id', 'N/A')}`
Usᴇʀɴᴀᴍᴇ: @{user.get('username', 'N/A') or 'N/A'}
Bᴀʟᴀɴᴄᴇ: ₹{user.get('balance', 0):.2f}
Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{user.get('total_deposits', 0):.2f}
Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{user.get('total_spent', 0):.2f}
Mᴇᴍʙᴇʀ Sɪɴᴄᴇ: {user.get('joined_date', datetime.now()).strftime('%Y-%m-%d')}
    """)
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ACCOUNT_IMAGE,
                caption=account_text
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land")
            ),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=ACCOUNT_IMAGE,
            caption=account_text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land")
            ),
            parse_mode='Markdown'
        )

def show_stats(user_id, message_id):
    total_users = get_all_users()
    total_orders = get_total_orders()
    total_deposits = get_total_deposits()
    total_spent = get_total_spent()
    
    stats_text = convert_to_styled(f"""
Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs

Tᴏᴛᴀʟ Usᴇʀs: {total_users}
Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposits:.2f}
Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{total_spent:.2f}

Aᴄᴛɪᴠᴇ Sᴇʀᴠɪᴄᴇs: {sum(len(services) for services in SERVICES.values())}
Cᴀᴛᴇɢᴏʀɪᴇs: {len(SERVICES)}
    """)
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=HISTORY_IMAGE,
                caption=stats_text
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land")
            ),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=HISTORY_IMAGE,
            caption=stats_text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land")
            ),
            parse_mode='Markdown'
        )

def show_support(user_id, message_id):
    support_text = convert_to_styled(f"""
Sᴜᴘᴘᴏʀᴛ & Hᴇʟᴘ

Nᴇᴇᴅ ʜᴇʟᴘ? Cᴏɴᴛᴀᴄᴛ ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ᴛᴇᴀᴍ:

Sᴜᴘᴘᴏʀᴛ: {SUPPORT_LINK}
Bᴏᴛ: {BOT_LINK}

Bᴇғᴏʀᴇ ᴄᴏɴᴛᴀᴄᴛɪɴɢ sᴜᴘᴘᴏʀᴛ:
• Cʜᴇᴄᴋ ʏᴏᴜʀ ᴏʀᴅᴇʀ sᴛᴀᴛᴜs ɪɴ Oʀᴅᴇʀs
• Eɴsᴜʀᴇ ʏᴏᴜ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ
• Pʀᴏᴠɪᴅᴇ ʏᴏᴜʀ Usᴇʀ ID ɪғ ɴᴇᴇᴅᴇᴅ

Sᴜᴘᴘᴏʀᴛ ᴀᴠᴀɪʟᴀʙʟᴇ 24/7
    """)
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📞 Cᴏɴᴛᴀᴄᴛ Sᴜᴘᴘᴏʀᴛ", url=SUPPORT_LINK))
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land"))
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=WELCOME_IMAGE,
                caption=support_text
            ),
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=WELCOME_IMAGE,
            caption=support_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

def show_main_menu(call):
    """Sʜᴏᴡ ᴍᴀɪɴ ᴍᴇɴᴜ"""
    user_id = call.message.chat.id
    user_name = call.message.chat.first_name
    
    text = convert_to_styled(f"""
Hᴇʟʟᴏ {user_name}!

Wᴇʟᴄᴏᴍᴇ ᴛᴏ Oᴜʀ Bᴏᴛ Mᴀɪɴ Mᴇɴᴜ

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:
    """)
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(WELCOME_IMAGE, text),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

# Admin functions with land.py font style
def show_admin_panel(user_id, message_id):
    admin_text = convert_to_styled(f"""
Aᴅᴍɪɴ Pᴀɴᴇʟ

Wᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ, Aᴅᴍɪɴ!

Cʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:
    """)
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ADMIN_IMAGE,
                caption=admin_text
            ),
            reply_markup=admin_keyboard(),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=ADMIN_IMAGE,
            caption=admin_text,
            reply_markup=admin_keyboard(),
            parse_mode='Markdown'
        )

def handle_admin_commands(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    if call.data == "admin_stats":
        total_users = get_all_users()
        total_orders = get_total_orders()
        total_deposits = get_total_deposits()
        total_spent = get_total_spent()
        
        stats_text = convert_to_styled(f"""
Aᴅᴍɪɴ Sᴛᴀᴛɪsᴛɪᴄs

Tᴏᴛᴀʟ Usᴇʀs: {total_users}
Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposits:.2f}
Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{total_spent:.2f}

Aᴄᴛɪᴠᴇ Sᴇʀᴠɪᴄᴇs: {sum(len(services) for services in SERVICES.values())}
        """)
        
        bot.edit_message_caption(
            chat_id=user_id,
            message_id=message_id,
            caption=stats_text,
            reply_markup=admin_keyboard(),
            parse_mode='Markdown'
        )
    
    elif call.data == "admin_balance":
        bot.edit_message_caption(
            chat_id=user_id,
            message_id=message_id,
            caption=convert_to_styled("Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ\n\nSᴇɴᴅ ᴜsᴇʀ ID ᴀɴᴅ ᴀᴍᴏᴜɴᴛ ɪɴ ғᴏʀᴍᴀᴛ:\n`ᴜsᴇʀ_ɪᴅ ᴀᴍᴏᴜɴᴛ`\n\nExᴀᴍᴘʟᴇ: `123456789 100`"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin")
            ),
            parse_mode='Markdown'
        )
        msg = bot.send_message(user_id, "👤 Eɴᴛᴇʀ ᴜsᴇʀ ID ᴀɴᴅ ᴀᴍᴏᴜɴᴛ:")
        bot.register_next_step_handler(msg, process_balance_update)
    
    elif call.data == "admin_broadcast":
        bot.edit_message_caption(
            chat_id=user_id,
            message_id=message_id,
            caption=convert_to_styled("Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ\n\nSᴇɴᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ:"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin")
            ),
            parse_mode='Markdown'
        )
        msg = bot.send_message(user_id, "💬 Eɴᴛᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ:")
        bot.register_next_step_handler(msg, process_broadcast)
    
    elif call.data == "admin_users":
        show_user_control(user_id, message_id)

def process_balance_update(message):
    user_id = message.from_user.id
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ғᴏʀᴍᴀᴛ. Usᴇ: `ᴜsᴇʀ_ɪᴅ ᴀᴍᴏᴜɴᴛ`")
            return
        
        target_user_id = int(parts[0])
        amount = float(parts[1])
        
        target_user = get_user(target_user_id)
        if not target_user:
            create_user(target_user_id, f"Usᴇʀ_{target_user_id}")
        
        new_balance = update_balance(target_user_id, amount)
        
        bot.send_message(
            user_id,
            convert_to_styled(f"""
✅ Bᴀʟᴀɴᴄᴇ ᴜᴘᴅᴀᴛᴇᴅ!

Usᴇʀ: {target_user_id}
Aᴍᴏᴜɴᴛ: ₹{amount}
Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance}
            """)
        )
        
        # Notify user
        try:
            bot.send_message(
                target_user_id,
                convert_to_styled(f"""
💰 Yᴏᴜʀ ʙᴀʟᴀɴᴄᴇ ʜᴀs ʙᴇᴇɴ ᴜᴘᴅᴀᴛᴇᴅ!

Aᴍᴏᴜɴᴛ: ₹{amount}
Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance}
                """)
            )
        except:
            pass
            
    except Exception as e:
        bot.send_message(user_id, f"❌ Eʀʀᴏʀ: {str(e)}")

def process_broadcast(message):
    admin_id = message.from_user.id
    broadcast_text = message.text
    
    users = users_collection.find({})
    total_users = 0
    success_count = 0
    
    progress_msg = bot.send_message(admin_id, "📤 Sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ...")
    
    for user in users:
        try:
            bot.send_message(user["user_id"], convert_to_styled(f"📢 Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ\n\n{broadcast_text}"), parse_mode='Markdown')
            success_count += 1
            total_users += 1
            
            # Update progress every 10 users
            if total_users % 10 == 0:
                bot.edit_message_text(
                    convert_to_styled(f"📤 Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ...\n\nSᴇɴᴛ: {success_count}/{users.count()}"),
                    admin_id,
                    progress_msg.message_id
                )
                
        except Exception as e:
            total_users += 1
            continue
    
    bot.edit_message_text(
        convert_to_styled(f"✅ Bʀᴏᴀᴅᴄᴀsᴛ Cᴏᴍᴘʟᴇᴛᴇᴅ!\n\nSᴜᴄᴄᴇss: {success_count}\nFᴀɪʟᴇᴅ: {total_users - success_count}"),
        admin_id,
        progress_msg.message_id
    )

def show_user_control(user_id, message_id):
    total_users = get_all_users()
    
    user_control_text = convert_to_styled(f"""
Usᴇʀ Cᴏɴᴛʀᴏʟ

Tᴏᴛᴀʟ Usᴇʀs: {total_users}

Sᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ:
    """)
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📋 Usᴇʀ Lɪsᴛ", callback_data="admin_user_list"),
        InlineKeyboardButton("🔍 Fɪɴᴅ Usᴇʀ", callback_data="admin_find_user"),
        InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin")
    )
    
    bot.edit_message_caption(
        chat_id=user_id,
        message_id=message_id,
        caption=user_control_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# Error handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ Uɴᴋɴᴏᴡɴ ᴄᴏᴍᴍᴀɴᴅ. Usᴇ /start ᴛᴏ ʙᴇɢɪɴ.")
    else:
        bot.send_message(message.chat.id, "🤖 Pʟᴇᴀsᴇ ᴜsᴇ ᴛʜᴇ ᴍᴇɴᴜ ʙᴜᴛᴛᴏɴs ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ.")

# Start polling
if __name__ == "__main__":
    print("🤖 Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
    print(f"📊 Tᴏᴛᴀʟ ᴜsᴇʀs ɪɴ ᴅᴀᴛᴀʙᴀsᴇ: {get_all_users()}")
    print(f"📦 Tᴏᴛᴀʟ ᴏʀᴅᴇʀs ɪɴ ᴅᴀᴛᴀʙᴀsᴇ: {get_total_orders()}")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"❌ Pᴏʟʟɪɴɢ ᴇʀʀᴏʀ: {e}")
            time.sleep(5)
            print("🔄 Rᴇsᴛᴀʀᴛɪɴɢ ʙᴏᴛ...")
