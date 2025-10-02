import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pymongo
from pymongo import MongoClient
import requests
import time
from datetime import datetime, timedelta
import random
import urllib.parse
import threading
from bson import ObjectId
from dotenv import load_dotenv
import qrcode
import io
import base64
import re
import json
from urllib.parse import quote

# Load environment variables
load_dotenv()

# Configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN', '8052955693:AAGf3qd5VXfq1I7d0_lM0eE3YwKFuBXLxvw')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://saifulmolla79088179_db_user:17gNrX0pC3bPqVaG@cluster0.fusvqca.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '6052975324').split(',')]
CHANNEL_ID = os.getenv('CHANNEL_ID', '@prooflelo1')
PROOF_CHANNEL = "https://t.me/prooflelo1"
BOT_USERNAME = "@prank_ox_bot"
SUPPORT_LINK = "https://t.me/your_support"
BOT_LINK = "https://t.me/your_bot"

# API Keys
AUTODEP_API_KEY = "LY81vEV7"
AUTODEP_MERCHANT_KEY = "WYcmQI71591891985230"
SMM_API_KEY = "c33fb3166621856879b2e486b99a30f0c442ac92"
SMM_API_URL = "https://smm-jupiter.com/api/v2"

# Initialize bot with better error handling
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# MongoDB connection with improved error handling
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.smm_bot
    users_collection = db.users
    orders_collection = db.orders
    deposits_collection = db.deposits
    admin_logs_collection = db.admin_logs
    user_sessions_collection = db.user_sessions
    settings_collection = db.settings
    # Test connection
    client.admin.command('ismaster')
    print("✅ MᴏɴɢᴏDB ᴄᴏɴɴᴇᴄᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ")
except Exception as e:
    print(f"❌ MᴏɴɢᴏDB ᴄᴏɴɴᴇᴄᴛɪᴏɴ ᴇʀʀᴏʀ: {e}")
    exit(1)

# Initialize default settings
if not settings_collection.find_one({"_id": "bot_config"}):
    settings_collection.insert_one({
        "_id": "bot_config",
        "bot_status": "on",
        "accepting_orders": True,
        "maintenance_mode": False
    })

# Services data (categories and services) - HARDCODED like in bot (2).py
SERVICES = {
    "Instagram": {
        "📸 Iɴsᴛᴀɢʀᴀᴍ Lɪᴋᴇs": {"id": 101, "price": 30, "min": 100, "max": 10000, "unit": 1000},
        "👁 Iɴsᴛᴀɢʀᴀᴍ Vɪᴇᴡs": {"id": 13685, "price": 50, "min": 100, "max": 50000, "unit": 1000},
        "👤 Iɴsᴛᴀɢʀᴀᴍ Fᴏʟʟᴏᴡᴇʀs": {"id": 103, "price": 80, "min": 100, "max": 10000, "unit": 1000}
    },
    "Facebook": {
        "👍 Fᴀᴄᴇʙᴏᴏᴋ Lɪᴋᴇs": {"id": 201, "price": 40, "min": 100, "max": 20000, "unit": 1000},
        "👁 Fᴀᴄᴇʙᴏᴏᴋ Vɪᴇᴡs": {"id": 202, "price": 60, "min": 100, "max": 50000, "unit": 1000},
        "👥 Fᴀᴄᴇʙᴏᴏᴋ Fᴏʟʟᴏᴡᴇʀs": {"id": 203, "price": 90, "min": 100, "max": 15000, "unit": 1000}
    },
    "YouTube": {
        "👍 YᴏᴜTᴜʙᴇ Lɪᴋᴇs": {"id": 301, "price": 35, "min": 100, "max": 50000, "unit": 1000},
        "👁 YᴏᴜTᴜʙᴇ Vɪᴇᴡs": {"id": 302, "price": 45, "min": 100, "max": 100000, "unit": 1000},
        "🔔 YᴏᴜTᴜʙᴇ Sᴜʙsᴄʀɪʙᴇʀs": {"id": 303, "price": 120, "min": 100, "max": 10000, "unit": 1000}
    },
    "Telegram": {
        "👥 Tᴇʟᴇɢʀᴀᴍ Mᴇᴍʙᴇʀs": {"id": 401, "price": 25, "min": 100, "max": 50000, "unit": 1000},
        "👍 Tᴇʟᴇɢʀᴀᴍ Pᴏsᴛ Lɪᴋᴇs": {"id": 402, "price": 20, "min": 100, "max": 100000, "unit": 1000},
        "👁 Tᴇʟᴇɢʀᴀᴍ Pᴏsᴛ Vɪᴇᴡs": {"id": 403, "price": 15, "min": 100, "max": 100000, "unit": 1000}
    }
}

# User states for conversation flow
user_states = {}
admin_states = {}

# Image URLs
WELCOME_IMAGE = "https://t.me/prooflelo1/135?single"
SERVICE_IMAGE = "https://t.me/prooflelo1/138?single"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/136?single"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/137?single"
HISTORY_IMAGE = "https://t.me/prooflelo1/139?single"
REFER_IMAGE = "https://t.me/prooflelo1/17"
ADMIN_IMAGE = "https://t.me/prooflelo1/140?single"

# Text styling function
def style_text(text):
    """Cᴏɴᴠᴇʀᴛ ᴛᴇxᴛ ᴛᴏ sᴛʏʟɪsʜ ғᴏʀᴍᴀᴛ ᴡɪᴛʜ ғɪʀsᴛ ʟᴇᴛᴛᴇʀ ᴄᴀᴘɪᴛᴀʟɪᴢᴇᴅ ᴀɴᴅ ʀᴇsᴛ sᴍᴀʟʟ"""
    def style_word(word):
        if len(word) > 0:
            return word[0] + word[1:].lower()
        return word
    
    words = text.split()
    styled_words = []
    
    for word in words:
        if any(char.isalpha() for char in word):
            styled_words.append(style_word(word))
        else:
            styled_words.append(word)
    
    return ' '.join(styled_words)

# Database helper functions for MongoDB
def get_user(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        users_collection.insert_one({
            "user_id": user_id,
            "username": f"User_{user_id}",
            "balance": 0.0,
            "total_deposits": 0.0,
            "total_spent": 0.0,
            "banned": False,
            "joined_date": datetime.now()
        })
        user = users_collection.find_one({"user_id": user_id})
    return user

def update_balance(user_id, amount):
    user = get_user(user_id)
    new_balance = round(user["balance"] + amount, 2)
    
    update_data = {"$set": {"balance": new_balance}}
    
    if amount > 0:
        update_data["$inc"] = {"total_deposits": amount}
    elif amount < 0:
        update_data["$inc"] = {"total_spent": abs(amount)}
    
    users_collection.update_one({"user_id": user_id}, update_data)
    return new_balance

def get_balance(user_id):
    user = get_user(user_id)
    return user["balance"]

def add_order(user_id, service_name, link, quantity, cost, api_order_id=None):
    order_id = f"ORD{random.randint(100000, 999999)}"
    
    order = {
        "order_id": order_id,
        "user_id": user_id,
        "service_name": service_name,
        "link": link,
        "quantity": quantity,
        "cost": cost,
        "status": "Pending",
        "api_order_id": api_order_id,
        "order_date": datetime.now()
    }
    
    orders_collection.insert_one(order)
    return order

def get_user_orders(user_id, limit=10):
    return list(orders_collection.find(
        {"user_id": user_id}
    ).sort("order_date", -1).limit(limit))

def add_deposit(user_id, amount, utr):
    deposit = {
        "user_id": user_id,
        "amount": amount,
        "utr": utr,
        "status": "Pending",
        "deposit_date": datetime.now()
    }
    
    deposits_collection.insert_one(deposit)
    return deposit

def update_deposit_status(utr, status):
    deposits_collection.update_one(
        {"utr": utr},
        {"$set": {"status": status}}
    )

def get_user_deposits(user_id, limit=10):
    return list(deposits_collection.find(
        {"user_id": user_id}
    ).sort("deposit_date", -1).limit(limit))

# User session functions for deposit data
def save_user_data(user_id, key, value):
    user_sessions_collection.update_one(
        {"user_id": user_id},
        {"$set": {key: value}},
        upsert=True
    )

def get_user_data(user_id, key):
    session = user_sessions_collection.find_one({"user_id": user_id})
    return session.get(key) if session else None

def delete_user_data(user_id, key):
    user_sessions_collection.update_one(
        {"user_id": user_id},
        {"$unset": {key: ""}}
    )

def clear_all_user_data(user_id):
    user_sessions_collection.delete_one({"user_id": user_id})

def get_all_users():
    return users_collection.count_documents({})

def get_total_orders():
    return orders_collection.count_documents({})

def get_total_deposits():
    result = deposits_collection.aggregate([
        {"$match": {"status": "Completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    result_list = list(result)
    return result_list[0]["total"] if result_list else 0.0

def get_total_spent():
    result = orders_collection.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$cost"}}}
    ])
    result_list = list(result)
    return result_list[0]["total"] if result_list else 0.0

def is_bot_accepting_orders():
    config = settings_collection.find_one({"_id": "bot_config"})
    return config.get("accepting_orders", True) if config else True

def set_bot_accepting_orders(status):
    settings_collection.update_one(
        {"_id": "bot_config"},
        {"$set": {"accepting_orders": status}},
        upsert=True
    )

# API Functions
def place_smm_order(service_id, link, quantity):
    """Pʟᴀᴄᴇ ᴏʀᴅᴇʀ ᴠɪᴀ SMM API"""
    try:
        params = {
            "key": SMM_API_KEY,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        response = requests.get(SMM_API_URL, params=params, timeout=30)
        api_response = response.json()
        
        api_order_id = api_response.get("order", "UNKNOWN")
        return api_order_id
        
    except Exception as e:
        print(f"SMM API order error: {e}")
        return None

def verify_payment(utr):
    """Vᴇʀɪғʏ ᴘᴀʏᴍᴇɴᴛ ᴜsɪɴɢ Aᴜᴛᴏᴅᴇᴘ API"""
    try:
        url = f"https://erox-autodep-api.onrender.com/api?key={AUTODEP_API_KEY}&merchantkey={AUTODEP_MERCHANT_KEY}&transactionid={utr}"
        resp = requests.get(url, timeout=10).json()
        
        if resp.get("result", {}).get("STATUS") == "TXN_SUCCESS":
            return True
        return False
    except Exception as e:
        print(f"Payment verification error: {e}")
        return False

def generate_qr_code(amount, upi_id="paytm.s1m11be@pty"):
    """Gᴇɴᴇʀᴀᴛᴇ QR ᴄᴏᴅᴇ ғᴏʀ UPI ᴘᴀʏᴍᴇɴᴛ"""
    upi_url = f"upi://pay?pa={upi_id}&pn=Paytm&am={amount}&tn=Deposit"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

# Helper Functions
def is_admin(user_id):
    return user_id in ADMIN_IDS

def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Channel check error: {e}")
        return False

def log_admin_action(admin_id, action, details):
    admin_logs_collection.insert_one({
        "admin_id": admin_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now()
    })

# Keyboard Builders with stylish text
def main_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💰 Dᴇᴘᴏsɪᴛ", callback_data="deposit"),
        InlineKeyboardButton("🛒 Oʀᴅᴇʀ", callback_data="order"),
        InlineKeyboardButton("📋 Oʀᴅᴇʀs", callback_data="orders"),
        InlineKeyboardButton("👥 Rᴇғᴇʀ", callback_data="refer"),
        InlineKeyboardButton("👤 Aᴄᴄᴏᴜɴᴛ", callback_data="account"),
        InlineKeyboardButton("📊 Sᴛᴀᴛs", callback_data="stats"),
        InlineKeyboardButton("ℹ️ Sᴜᴘᴘᴏʀᴛ", callback_data="support")
    ]
    markup.add(*buttons)
    
    return markup

def categories_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for category in SERVICES.keys():
        emoji = "📸" if category == "Instagram" else "👍" if category == "Facebook" else "📺" if category == "YouTube" else "📱"
        buttons.append(InlineKeyboardButton(f"{emoji} {category}", callback_data=f"cat_{category}"))
    
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    return markup

def services_keyboard(category):
    markup = InlineKeyboardMarkup()
    for service_name in SERVICES[category].keys():
        markup.add(InlineKeyboardButton(service_name, callback_data=f"serv_{category}_{service_name}"))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order"))
    return markup

def back_button_only():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    return markup

def back_to_main_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ ᴛᴏ Mᴀɪɴ Mᴇɴᴜ", callback_data="main_menu"))
    return markup

def channel_join_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Jᴏɪɴ Cʜᴀɴɴᴇʟ", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    markup.add(InlineKeyboardButton("🔍 Cʜᴇᴄᴋ Jᴏɪɴ", callback_data="check_join"))
    return markup

def deposit_confirmation_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ I Hᴀᴠᴇ Pᴀɪᴅ", callback_data="check_txn"))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    return markup

def support_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📞 Cᴏɴᴛᴀᴄᴛ Us", url=SUPPORT_LINK))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    return markup

def order_confirmation_keyboard(cost):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ Oʀᴅᴇʀ", callback_data=f"confirm_order_{cost}"),
        InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="main_menu")
    )
    return markup

# Admin Keyboards
def admin_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ", callback_data="admin_balance"),
        InlineKeyboardButton("📢 Bʀᴏᴀᴅᴄᴀsᴛ", callback_data="admin_broadcast"),
        InlineKeyboardButton("👤 Usᴇʀ Cᴏɴᴛʀᴏʟ", callback_data="admin_users"),
        InlineKeyboardButton("⚙️ Bᴏᴛ Sᴇᴛᴛɪɴɢs", callback_data="admin_settings"),
        InlineKeyboardButton("📊 Sᴛᴀᴛs", callback_data="admin_stats"),
        InlineKeyboardButton("🔙 Mᴀɪɴ Mᴇɴᴜ", callback_data="main_menu")
    ]
    markup.add(*buttons)
    return markup

def admin_balance_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Aᴅᴅ Bᴀʟᴀɴᴄᴇ", callback_data="admin_add_balance"),
        InlineKeyboardButton("➖ Rᴇᴍᴏᴠᴇ Bᴀʟᴀɴᴄᴇ", callback_data="admin_remove_balance")
    )
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin_panel"))
    return markup

def admin_users_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Usᴇʀ Sᴛᴀᴛs", callback_data="admin_user_stats"),
        InlineKeyboardButton("🔍 Fɪɴᴅ Usᴇʀ", callback_data="admin_find_user"),
        InlineKeyboardButton("🚫 Bᴀɴ Usᴇʀ", callback_data="admin_ban_user"),
        InlineKeyboardButton("✅ Uɴʙᴀɴ Usᴇʀ", callback_data="admin_unban_user")
    )
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin_panel"))
    return markup

def admin_settings_keyboard():
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"🔄 Bᴏᴛ Sᴛᴀᴛᴜs: {bot_status}", callback_data="admin_toggle_bot"),
        InlineKeyboardButton("📊 Bᴏᴛ Iɴғᴏ", callback_data="admin_bot_info")
    )
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin_panel"))
    return markup

# Start command and main menu
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or f"User_{user_id}"
        
        # Update user in database
        user = get_user(user_id)
        if user.get('username') != username:
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"username": username}}
            )
        
        # Check if user is banned
        if user.get('banned'):
            bot.reply_to(message, "❌ Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ.")
            return
        
        # Check channel membership
        if not check_channel_membership(user_id):
            welcome_text = f"""
✨ Wᴇʟᴄᴏᴍᴇ {message.from_user.first_name}!

📢 Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ:

{CHANNEL_ID}

Aғᴛᴇʀ ᴊᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴛʜᴇ ᴄʜᴇᴄᴋ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.
            """
            bot.send_photo(user_id, WELCOME_IMAGE, welcome_text, reply_markup=channel_join_keyboard())
            return
        
        welcome_text = f"""
✨ Wᴇʟᴄᴏᴍᴇ Tᴏ SMM Bᴏᴛ ✨

🚀 Bᴜʏ Sᴏᴄɪᴀʟ Mᴇᴅɪᴀ Sᴇʀᴠɪᴄᴇs ᴀᴛ Cʜᴇᴀᴘᴇsᴛ Rᴀᴛᴇs!

📊 Iɴsᴛᴀɢʀᴀᴍ, Fᴀᴄᴇʙᴏᴏᴋ, YᴏᴜTᴜʙᴇ & Tᴇʟᴇɢʀᴀᴍ Sᴇʀᴠɪᴄᴇs
💎 Hɪɢʜ Qᴜᴀʟɪᴛʏ & Fᴀsᴛ Dᴇʟɪᴠᴇʀʏ
🔒 Sᴇᴄᴜʀᴇ Pᴀʏᴍᴇɴᴛs & 24/7 Sᴜᴘᴘᴏʀᴛ

💫 Sᴛᴀʀᴛ ʙʏ ᴅᴇᴘᴏsɪᴛɪɴɢ ғᴜɴᴅs ᴏʀ ᴘʟᴀᴄɪɴɢ ᴀɴ ᴏʀᴅᴇʀ!
        """
        
        bot.send_photo(user_id, WELCOME_IMAGE, welcome_text, reply_markup=main_menu_keyboard())
        
    except Exception as e:
        print(f"Start command error: {e}")
        bot.reply_to(message, "❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

@bot.message_handler(commands=['admin'])
def admin_command(message):
    try:
        user_id = message.from_user.id
        if is_admin(user_id):
            admin_text = """
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

💼 Mᴀɴᴀɢᴇ ʏᴏᴜʀ SMM ʙᴏᴛ ᴡɪᴛʜ ᴘᴏᴡᴇʀғᴜʟ ᴀᴅᴍɪɴ ᴛᴏᴏʟs.

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:
            """
            bot.send_photo(user_id, ADMIN_IMAGE, admin_text, reply_markup=admin_keyboard())
        else:
            bot.send_message(user_id, "❌ Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ. Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ.")
    except Exception as e:
        print(f"Admin command error: {e}")
        bot.reply_to(message, "❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ.")

@bot.message_handler(commands=['balance'])
def balance_command(message):
    try:
        user_id = message.from_user.id
        user = get_user(user_id)
        
        balance_text = f"""
💰 Aᴄᴄᴏᴜɴᴛ Bᴀʟᴀɴᴄᴇ

💳 Cᴜʀʀᴇɴᴛ Bᴀʟᴀɴᴄᴇ: ₹{user['balance']:.2f}
📥 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛᴇᴅ: ₹{user.get('total_deposits', 0):.2f}
📤 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{user.get('total_spent', 0):.2f}

💡 Dᴇᴘᴏsɪᴛ ᴍᴏʀᴇ ғᴜɴᴅs ᴛᴏ ᴘʟᴀᴄᴇ ᴏʀᴅᴇʀs!
        """
        
        bot.send_photo(user_id, ACCOUNT_IMAGE, balance_text, reply_markup=back_to_main_button())
        
    except Exception as e:
        print(f"Balance command error: {e}")
        bot.reply_to(message, "❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ.")

# Callback query handler - MAIN HANDLER
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    try:
        # Check if user is banned
        user = get_user(user_id)
        if user.get('banned'):
            bot.answer_callback_query(call.id, "❌ Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ.", show_alert=True)
            return
        
        # Main menu and navigation
        if call.data == "main_menu":
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
        
        elif call.data == "check_join":
            check_channel_join(call)
        
        # Category and service selection
        elif call.data.startswith("cat_"):
            category = call.data[4:]
            show_services(user_id, message_id, category)
        
        elif call.data.startswith("serv_"):
            parts = call.data.split("_")
            if len(parts) >= 3:
                category = parts[1]
                service_name = "_".join(parts[2:])
                start_order_flow(user_id, message_id, category, service_name)
        
        # Deposit and payment
        elif call.data == "check_txn":
            check_transaction(call)
        
        # Order confirmation
        elif call.data.startswith("confirm_order_"):
            confirm_order_processing(call)
        
        # Admin panel
        elif call.data == "admin_panel":
            if is_admin(user_id):
                show_admin_panel(user_id, message_id)
            else:
                bot.answer_callback_query(call.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ!", show_alert=True)
        
        # Admin sub-menus
        elif call.data.startswith("admin_"):
            if is_admin(user_id):
                handle_admin_commands(call)
            else:
                bot.answer_callback_query(call.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ!", show_alert=True)
        
        else:
            bot.answer_callback_query(call.id, "❌ Uɴᴋɴᴏᴡɴ ᴄᴏᴍᴍᴀɴᴅ!", show_alert=True)
                
    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ! Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", show_alert=True)

# Main menu functions
def show_main_menu(call):
    try:
        user_id = call.from_user.id
        
        welcome_text = f"""
✨ Wᴇʟᴄᴏᴍᴇ Tᴏ SMM Bᴏᴛ ✨

Hᴇʟʟᴏ {call.from_user.first_name}! 

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ᴛʜᴇ ᴍᴇɴᴜ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ:
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=WELCOME_IMAGE,
                caption=welcome_text
            ),
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        print(f"Show main menu error: {e}")
        try:
            bot.send_message(call.from_user.id, "✨ Wᴇʟᴄᴏᴍᴇ Tᴏ SMM Bᴏᴛ ✨\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:", reply_markup=main_menu_keyboard())
        except:
            pass

def show_main_menu_for_message(message):
    try:
        user_id = message.from_user.id
        bot.send_photo(
            chat_id=user_id,
            photo=WELCOME_IMAGE,
            caption="✨ Wᴇʟᴄᴏᴍᴇ Tᴏ SMM Bᴏᴛ ✨\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ᴛʜᴇ ᴍᴇɴᴜ ʙᴇʟᴏᴡ:",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        print(f"Show main menu for message error: {e}")

# Deposit flow
def show_deposit_menu(user_id, message_id):
    try:
        # Clear any existing session data
        clear_all_user_data(user_id)
        
        deposit_text = """
💰 Dᴇᴘᴏsɪᴛ Fᴜɴᴅs

Eɴᴛᴇʀ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇᴘᴏsɪᴛ ɪɴ ʀᴜᴘᴇᴇs.

💡 Mɪɴɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ: ₹10
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=DEPOSIT_IMAGE,
                caption=deposit_text
            ),
            reply_markup=None
        )
        
        msg = bot.send_message(user_id, "💳 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇᴘᴏsɪᴛ (ɪɴ ₹):")
        bot.register_next_step_handler(msg, process_deposit_amount)
        
    except Exception as e:
        print(f"Show deposit menu error: {e}")
        bot.send_message(user_id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴅᴇᴘᴏsɪᴛ ᴍᴇɴᴜ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", reply_markup=back_to_main_button())

def process_deposit_amount(message):
    try:
        user_id = message.from_user.id
        
        # Check if message is a command
        if message.text.startswith('/'):
            show_main_menu_for_message(message)
            return
        
        amount = float(message.text)
        
        if amount < 10:
            bot.send_message(user_id, "❌ Mɪɴɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ ᴀᴍᴏᴜɴᴛ ɪs ₹10. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ʜɪɢʜᴇʀ ᴀᴍᴏᴜɴᴛ.")
            show_deposit_menu(user_id, message.message_id)
            return
        
        # Generate random UTR
        utr = str(random.randint(100000000000, 999999999999))
        
        # Save deposit data
        save_user_data(user_id, "deposit_utr", utr)
        save_user_data(user_id, "deposit_amount", amount)
        
        # Generate QR code
        qr_img = generate_qr_code(amount)
        
        deposit_info = f"""
💰 Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ Cʀᴇᴀᴛᴇᴅ

💵 Aᴍᴏᴜɴᴛ: ₹{amount}
🔢 UTR: `{utr}`

📲 Sᴄᴀɴ ᴛʜᴇ QR ᴄᴏᴅᴇ ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ ᴘᴀʏᴍᴇɴᴛ.

💡 Aғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ, ᴄʟɪᴄᴋ "I Hᴀᴠᴇ Pᴀɪᴅ" ᴛᴏ ᴠᴇʀɪғʏ.
        """
        
        bot.send_photo(
            chat_id=user_id,
            photo=qr_img,
            caption=deposit_info,
            reply_markup=deposit_confirmation_keyboard(),
            parse_mode='Markdown'
        )
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
        show_deposit_menu(user_id, message.message_id)
    except Exception as e:
        print(f"Process deposit amount error: {e}")
        bot.send_message(user_id, "❌ Eʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ᴅᴇᴘᴏsɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", reply_markup=back_to_main_button())

def check_transaction(call):
    try:
        user_id = call.from_user.id
        
        utr = get_user_data(user_id, "deposit_utr")
        amount = get_user_data(user_id, "deposit_amount")
        
        if not utr or not amount:
            bot.answer_callback_query(call.id, "❌ Nᴏ ᴘᴇɴᴅɪɴɢ ᴅᴇᴘᴏsɪᴛ ғᴏᴜɴᴅ.", show_alert=True)
            return
        
        # Show verifying message
        verifying_msg = bot.send_message(user_id, "🔍 Vᴇʀɪғʏɪɴɢ ᴘᴀʏᴍᴇɴᴛ...")
        
        # Verify payment
        payment_verified = verify_payment(utr)
        
        if payment_verified:
            # Update user balance
            new_balance = update_balance(user_id, amount)
            
            # Record deposit
            add_deposit(user_id, amount, utr)
            update_deposit_status(utr, "Completed")
            
            # Clear session data
            clear_all_user_data(user_id)
            
            success_text = f"""
✅ Pᴀʏᴍᴇɴᴛ Vᴇʀɪғɪᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

💰 Aᴍᴏᴜɴᴛ: ₹{amount}
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance:.2f}

Tʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ʏᴏᴜʀ ᴅᴇᴘᴏsɪᴛ!
            """
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=verifying_msg.message_id,
                text=success_text,
                reply_markup=back_to_main_button()
            )
            
            # Notify admin
            try:
                for admin_id in ADMIN_IDS:
                    bot.send_message(
                        admin_id,
                        f"💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ!\n\n👤 Usᴇʀ: {user_id}\n💵 Aᴍᴏᴜɴᴛ: ₹{amount}\n💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance:.2f}"
                    )
            except:
                pass
            
        else:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=verifying_msg.message_id,
                text="❌ Pᴀʏᴍᴇɴᴛ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ. Pʟᴇᴀsᴇ ᴍᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ ʜᴀᴠᴇ ᴘᴀɪᴅ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.",
                reply_markup=deposit_confirmation_keyboard()
            )
            
    except Exception as e:
        print(f"Check transaction error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴠᴇʀɪғʏɪɴɢ ᴘᴀʏᴍᴇɴᴛ.", show_alert=True)

# Order flow
def show_categories(user_id, message_id):
    try:
        if not is_bot_accepting_orders():
            bot.answer_callback_query(call.id, "❌ Bᴏᴛ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ɴᴏᴛ ᴀᴄᴄᴇᴘᴛɪɴɢ ᴏʀᴅᴇʀs.", show_alert=True)
            return
        
        categories_text = """
🛒 Sᴇʟᴇᴄᴛ Cᴀᴛᴇɢᴏʀʏ

Cʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ᴛᴏ ᴠɪᴇᴡ ᴀᴠᴀɪʟᴀʙʟᴇ sᴇʀᴠɪᴄᴇs:
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=SERVICE_IMAGE,
                caption=categories_text
            ),
            reply_markup=categories_keyboard()
        )
    except Exception as e:
        print(f"Show categories error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴄᴀᴛᴇɢᴏʀɪᴇs.", show_alert=True)

def show_services(user_id, message_id, category):
    try:
        if category not in SERVICES:
            bot.answer_callback_query(call.id, "❌ Cᴀᴛᴇɢᴏʀʢ ɴᴏᴛ ғᴏᴜɴᴅ.", show_alert=True)
            return
        
        services_text = f"""
📦 {category} Sᴇʀᴠɪᴄᴇs

Sᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴏʀᴅᴇʀ:
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=SERVICE_IMAGE,
                caption=services_text
            ),
            reply_markup=services_keyboard(category)
        )
    except Exception as e:
        print(f"Show services error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ sᴇʀᴠɪᴄᴇs.", show_alert=True)

def start_order_flow(user_id, message_id, category, service_name):
    try:
        # Replace underscores with spaces for service name
        service_name = service_name.replace('_', ' ')
        
        if category not in SERVICES or service_name not in SERVICES[category]:
            bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ.", show_alert=True)
            return
        
        service = SERVICES[category][service_name]
        
        service_info = f"""
📦 Sᴇʀᴠɪᴄᴇ: {service_name}

💰 Pʀɪᴄᴇ: ₹{service['price']}/1000
📦 Mɪɴɪᴍᴜᴍ: {service['min']:,}
📈 Mᴀxɪᴍᴜᴍ: {service['max']:,}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ ғᴏʀ ʏᴏᴜʀ ᴏʀᴅᴇʀ:
        """
        
        # Save service data
        save_user_data(user_id, "order_category", category)
        save_user_data(user_id, "order_service_name", service_name)
        save_user_data(user_id, "order_service_data", json.dumps(service))
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=service_info,
            parse_mode='Markdown'
        )
        
        msg = bot.send_message(user_id, "🔗 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ʟɪɴᴋ:")
        bot.register_next_step_handler(msg, process_order_link)
        
    except Exception as e:
        print(f"Start order flow error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ᴏʀᴅᴇʀ.", show_alert=True)

def process_order_link(message):
    try:
        user_id = message.from_user.id
        
        # Check if message is a command
        if message.text.startswith('/'):
            show_main_menu_for_message(message)
            return
        
        link = message.text.strip()
        
        # Validate link
        if not link.startswith(('http://', 'https://')):
            bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ʟɪɴᴋ. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ URL sᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ http:// ᴏʀ https://")
            msg = bot.send_message(user_id, "🔗 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ʟɪɴᴋ:")
            bot.register_next_step_handler(msg, process_order_link)
            return
        
        # Get service data
        category = get_user_data(user_id, "order_category")
        service_name = get_user_data(user_id, "order_service_name")
        service_data = get_user_data(user_id, "order_service_data")
        
        if not all([category, service_name, service_data]):
            bot.send_message(user_id, "❌ Sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ sᴛᴀʀᴛ ᴏᴠᴇʀ.")
            show_main_menu_for_message(message)
            return
        
        service = json.loads(service_data)
        
        # Save link
        save_user_data(user_id, "order_link", link)
        
        service_info = f"""
📦 Sᴇʀᴠɪᴄᴇ: {service_name}
🔗 Lɪɴᴋ: {link[:50]}...

💰 Pʀɪᴄᴇ: ₹{service['price']}/1000
📦 Mɪɴɪᴍᴜᴍ: {service['min']:,}
📈 Mᴀxɪᴍᴜᴍ: {service['max']:,}

Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ǫᴜᴀɴᴛɪᴛʏ:
        """
        
        bot.send_message(user_id, service_info, parse_mode='Markdown')
        
        msg = bot.send_message(user_id, "🔢 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ǫᴜᴀɴᴛɪᴛʏ:")
        bot.register_next_step_handler(msg, process_order_quantity)
        
    except Exception as e:
        print(f"Process order link error: {e}")
        bot.send_message(user_id, "❌ Eʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ʟɪɴᴋ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", reply_markup=back_to_main_button())

def process_order_quantity(message):
    try:
        user_id = message.from_user.id
        
        # Check if message is a command
        if message.text.startswith('/'):
            show_main_menu_for_message(message)
            return
        
        quantity = int(message.text)
        
        # Get order data
        category = get_user_data(user_id, "order_category")
        service_name = get_user_data(user_id, "order_service_name")
        service_data = get_user_data(user_id, "order_service_data")
        link = get_user_data(user_id, "order_link")
        
        if not all([category, service_name, service_data, link]):
            bot.send_message(user_id, "❌ Sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ sᴛᴀʀᴛ ᴏᴠᴇʀ.")
            show_main_menu_for_message(message)
            return
        
        service = json.loads(service_data)
        
        # Validate quantity
        if quantity < service['min']:
            bot.send_message(user_id, f"❌ Qᴜᴀɴᴛɪᴛʏ ʙᴇʟᴏᴡ ᴍɪɴɪᴍᴜᴍ ({service['min']:,}). Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ʜɪɢʜᴇʀ ǫᴜᴀɴᴛɪᴛʏ.")
            msg = bot.send_message(user_id, "🔢 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ǫᴜᴀɴᴛɪᴛʏ:")
            bot.register_next_step_handler(msg, process_order_quantity)
            return
        
        if quantity > service['max']:
            bot.send_message(user_id, f"❌ Qᴜᴀɴᴛɪᴛʏ ᴇxᴄᴇᴇᴅs ᴍᴀxɪᴍᴜᴍ ({service['max']:,}). Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ʟᴏᴡᴇʀ ǫᴜᴀɴᴛɪᴛʏ.")
            msg = bot.send_message(user_id, "🔢 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ǫᴜᴀɴᴛɪᴛʏ:")
            bot.register_next_step_handler(msg, process_order_quantity)
            return
        
        # Calculate cost
        cost = (quantity / service['unit']) * service['price']
        cost = round(cost, 2)
        
        # Check user balance
        user_balance = get_balance(user_id)
        
        if user_balance < cost:
            bot.send_message(
                user_id,
                f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!\n\n💰 Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ: ₹{user_balance:.2f}\n💳 Rᴇǫᴜɪʀᴇᴅ: ₹{cost:.2f}\n\nPʟᴇᴀsᴇ ᴅᴇᴘᴏsɪᴛ ғᴜɴᴅs ғɪʀsᴛ.",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("💰 Dᴇᴘᴏsɪᴛ", callback_data="deposit")
                )
            )
            return
        
        # Save quantity and cost
        save_user_data(user_id, "order_quantity", quantity)
        save_user_data(user_id, "order_cost", cost)
        
        # Show order summary
        order_summary = f"""
📦 Oʀᴅᴇʀ Sᴜᴍᴍᴀʀʏ

🛒 Sᴇʀᴠɪᴄᴇ: {service_name}
🔗 Lɪɴᴋ: {link[:50]}...
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity:,}
💰 Cᴏsᴛ: ₹{cost:.2f}
💳 Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ: ₹{user_balance:.2f}

Pʀᴏᴄᴇᴇᴅ ᴡɪᴛʜ ᴛʜɪs ᴏʀᴅᴇʀ?
        """
        
        bot.send_message(
            user_id, 
            order_summary, 
            parse_mode='Markdown', 
            reply_markup=order_confirmation_keyboard(cost)
        )
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
        msg = bot.send_message(user_id, "🔢 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ǫᴜᴀɴᴛɪᴛʏ:")
        bot.register_next_step_handler(msg, process_order_quantity)
    except Exception as e:
        print(f"Process order quantity error: {e}")
        bot.send_message(user_id, "❌ Eʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ǫᴜᴀɴᴛɪᴛʏ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", reply_markup=back_to_main_button())

def confirm_order_processing(call):
    try:
        user_id = call.from_user.id
        
        # Extract cost from callback data
        cost = float(call.data.split('_')[2])
        
        # Get order data
        category = get_user_data(user_id, "order_category")
        service_name = get_user_data(user_id, "order_service_name")
        service_data = get_user_data(user_id, "order_service_data")
        link = get_user_data(user_id, "order_link")
        quantity = get_user_data(user_id, "order_quantity")
        
        if not all([category, service_name, service_data, link, quantity, cost]):
            bot.answer_callback_query(call.id, "❌ Sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ! Pʟᴇᴀsᴇ sᴛᴀʀᴛ ᴏᴠᴇʀ.", show_alert=True)
            return
        
        service = json.loads(service_data)
        
        # Double-check balance
        user_balance = get_balance(user_id)
        
        if user_balance < cost:
            bot.answer_callback_query(call.id, "❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!", show_alert=True)
            return
        
        # Show processing message
        processing_msg = bot.send_message(user_id, "⏳ Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ᴏʀᴅᴇʀ...")
        
        # Place order via API
        api_order_id = place_smm_order(service['id'], link, quantity)
        
        if api_order_id:
            # Deduct balance
            new_balance = update_balance(user_id, -cost)
            
            # Save order
            order = add_order(user_id, service_name, link, quantity, cost, api_order_id)
            
            # Success message
            success_msg = f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

📦 Sᴇʀᴠɪᴄᴇ: {service_name}
🔗 Lɪɴᴋ: {link[:50]}...
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity:,}
💰 Cᴏsᴛ: ₹{cost:.2f}
📋 Oʀᴅᴇʀ ID: `{order['order_id']}`
💳 Rᴇᴍᴀɪɴɪɴɢ Bᴀʟᴀɴᴄᴇ: ₹{new_balance:.2f}

Tʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ʏᴏᴜʀ ᴏʀᴅᴇʀ! Yᴏᴜ ᴄᴀɴ ᴛʀᴀᴄᴋ ʏᴏᴜʀ ᴏʀᴅᴇʀ ɪɴ ᴛʜᴇ "Oʀᴅᴇʀs" sᴇᴄᴛɪᴏɴ.
            """
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=success_msg,
                parse_mode='Markdown',
                reply_markup=back_to_main_button()
            )
            
            # Notify admin
            try:
                for admin_id in ADMIN_IDS:
                    bot.send_message(
                        admin_id,
                        f"🛒 Nᴇᴡ Oʀᴅᴇʀ!\n\n👤 Usᴇʀ: {user_id}\n📦 Sᴇʀᴠɪᴄᴇ: {service_name}\n💰 Aᴍᴏᴜɴᴛ: ₹{cost:.2f}\n📋 Oʀᴅᴇʀ ID: {order['order_id']}"
                    )
            except:
                pass
            
        else:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text="❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴘʟᴀᴄᴇ ᴏʀᴅᴇʀ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ.",
                reply_markup=back_to_main_button()
            )
        
        # Clear session data
        clear_all_user_data(user_id)
        
    except Exception as e:
        print(f"Confirm order error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ᴏʀᴅᴇʀ!", show_alert=True)

# Other menu functions
def show_orders(user_id, message_id):
    try:
        orders = get_user_orders(user_id, 10)
        
        if not orders:
            orders_text = """
📋 Yᴏᴜʀ Oʀᴅᴇʀs

Nᴏ ᴏʀᴅᴇʀs ғᴏᴜɴᴅ. Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴘʟᴀᴄᴇᴅ ᴀɴʏ ᴏʀᴅᴇʀs ʏᴇᴛ.

🛒 Pʟᴀᴄᴇ ʏᴏᴜʀ ғɪʀsᴛ ᴏʀᴅᴇʀ ɴᴏᴡ!
            """
        else:
            orders_text = "📋 Yᴏᴜʀ Rᴇᴄᴇɴᴛ Oʀᴅᴇʀs\n\n"
            
            for order in orders:
                status_emoji = "✅" if order['status'] == 'Completed' else "⏳" if order['status'] == 'Processing' else "❌"
                orders_text += f"{status_emoji} *{order['service_name']}*\n"
                orders_text += f"🔗 `{order['link'][:30]}...`\n"
                orders_text += f"🔢 {order['quantity']:,} | ₹{order['cost']:.2f}\n"
                orders_text += f"📅 {order['order_date'].strftime('%d/%m/%Y %H:%M')}\n"
                orders_text += f"📋 ID: `{order['order_id']}`\n\n"
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=HISTORY_IMAGE,
                caption=orders_text
            ),
            reply_markup=back_to_main_button(),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Show orders error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴏʀᴅᴇʀs.", show_alert=True)

def show_refer(user_id, message_id):
    try:
        user = get_user(user_id)
        
        refer_text = f"""
👥 Rᴇғᴇʀ & Eᴀʀɴ

Iɴᴠɪᴛᴇ ʏᴏᴜʀ ғʀɪᴇɴᴅs ᴀɴᴅ ᴇᴀʀɴ 10% ᴏғ ᴛʜᴇɪʀ ᴇᴠᴇʀʏ ᴅᴇᴘᴏsɪᴛ!

🔗 Yᴏᴜʀ Rᴇғᴇʀʀᴀʟ Lɪɴᴋ:
`https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}`

💡 Sʜᴀʀᴇ ᴛʜɪs ʟɪɴᴋ ᴡɪᴛʜ ʏᴏᴜʀ ғʀɪᴇɴᴅs. Wʜᴇɴ ᴛʜᴇʏ ᴊᴏɪɴ ᴀɴᴅ ᴅᴇᴘᴏsɪᴛ, ʏᴏᴜ ɢᴇᴛ 10% ʀᴇᴡᴀʀᴅ!

💰 Rᴇғᴇʀʀᴀʟ Cᴏᴍᴍɪssɪᴏɴ: 10%
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=REFER_IMAGE,
                caption=refer_text
            ),
            reply_markup=back_to_main_button(),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Show refer error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ʀᴇғᴇʀʀᴀʟ ɪɴғᴏ.", show_alert=True)

def show_account(user_id, message_id):
    try:
        user = get_user(user_id)
        user_orders = get_user_orders(user_id, 5)
        
        account_text = f"""
👤 Aᴄᴄᴏᴜɴᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ

🆔 Usᴇʀ ID: `{user_id}`
👤 Usᴇʀɴᴀᴍᴇ: @{user['username']}
💰 Bᴀʟᴀɴᴄᴇ: ₹{user['balance']:.2f}
💳 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛᴇᴅ: ₹{user.get('total_deposits', 0):.2f}
🛒 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{user.get('total_spent', 0):.2f}
📅 Jᴏɪɴᴇᴅ: {user['joined_date'].strftime('%d/%m/%Y')}
📦 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {len(user_orders)}
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ACCOUNT_IMAGE,
                caption=account_text
            ),
            reply_markup=back_to_main_button(),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Show account error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴀᴄᴄᴏᴜɴᴛ ɪɴғᴏ.", show_alert=True)

def show_stats(user_id, message_id):
    try:
        user = get_user(user_id)
        
        stats_text = f"""
📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs

👥 Tᴏᴛᴀʟ Usᴇʀs: {get_all_users():,}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {get_total_orders():,}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{get_total_deposits():.2f}
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{get_total_spent():.2f}

👤 Yᴏᴜʀ Sᴛᴀᴛs
💰 Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ: ₹{user['balance']:.2f}
💳 Yᴏᴜʀ Dᴇᴘᴏsɪᴛs: ₹{user.get('total_deposits', 0):.2f}
🛒 Yᴏᴜʀ Sᴘᴇɴᴅɪɴɢ: ₹{user.get('total_spent', 0):.2f}
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=HISTORY_IMAGE,
                caption=stats_text
            ),
            reply_markup=back_to_main_button(),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Show stats error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ sᴛᴀᴛs.", show_alert=True)

def show_support(user_id, message_id):
    try:
        support_text = """
ℹ️ Sᴜᴘᴘᴏʀᴛ

Iғ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ ᴏʀ ʜᴀᴠᴇ ᴀɴʏ ǫᴜᴇsᴛɪᴏɴs, ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ᴛᴇᴀᴍ.

Oᴜʀ sᴜᴘᴘᴏʀᴛ ᴛᴇᴀᴍ ɪs ᴀᴠᴀɪʟᴀʙʟᴇ 24/7 ᴛᴏ ᴀssɪsᴛ ʏᴏᴜ ᴡɪᴛʜ:

• Aᴄᴄᴏᴜɴᴛ ɪssᴜᴇs
• Dᴇᴘᴏsɪᴛ ʜᴇʟᴘ
• Oʀᴅᴇʀ ᴘʀᴏʙʟᴇᴍs
• Gᴇɴᴇʀᴀʟ ǫᴜᴇsᴛɪᴏɴs
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=SERVICE_IMAGE,
                caption=support_text
            ),
            reply_markup=support_keyboard(),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Show support error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ sᴜᴘᴘᴏʀᴛ.", show_alert=True)

def check_channel_join(call):
    try:
        user_id = call.from_user.id
        
        if check_channel_membership(user_id):
            bot.answer_callback_query(call.id, "✅ Tʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ᴊᴏɪɴɪɴɢ! Nᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ.", show_alert=True)
            start_command(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ʏᴇᴛ. Pʟᴇᴀsᴇ ᴊᴏɪɴ ғɪʀsᴛ.", show_alert=True)
    except Exception as e:
        print(f"Check channel join error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴄʜᴇᴄᴋɪɴɢ ᴄʜᴀɴɴᴇʟ ᴍᴇᴍʙᴇʀsʜɪᴘ.", show_alert=True)

# Admin functions
def show_admin_panel(user_id, message_id):
    try:
        admin_text = """
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

💼 Mᴀɴᴀɢᴇ ʏᴏᴜʀ SMM ʙᴏᴛ ᴡɪᴛʜ ᴘᴏᴡᴇʀғᴜʟ ᴀᴅᴍɪɴ ᴛᴏᴏʟs.

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ADMIN_IMAGE,
                caption=admin_text
            ),
            reply_markup=admin_keyboard()
        )
    except Exception as e:
        print(f"Show admin panel error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ.", show_alert=True)

def handle_admin_commands(call):
    try:
        user_id = call.from_user.id
        command = call.data
        
        if command == "admin_balance":
            show_admin_balance_menu(user_id, call.message.message_id)
        
        elif command == "admin_broadcast":
            start_admin_broadcast(call)
        
        elif command == "admin_users":
            show_admin_users_menu(user_id, call.message.message_id)
        
        elif command == "admin_settings":
            show_admin_settings_menu(user_id, call.message.message_id)
        
        elif command == "admin_stats":
            show_admin_stats_menu(user_id, call.message.message_id)
        
        elif command == "admin_add_balance":
            start_admin_add_balance(call)
        
        elif command == "admin_remove_balance":
            start_admin_remove_balance(call)
        
        elif command == "admin_user_stats":
            show_admin_user_stats(call)
        
        elif command == "admin_find_user":
            start_admin_find_user(call)
        
        elif command == "admin_ban_user":
            start_admin_ban_user(call)
        
        elif command == "admin_unban_user":
            start_admin_unban_user(call)
        
        elif command == "admin_toggle_bot":
            toggle_bot_status(call)
        
        elif command == "admin_bot_info":
            show_admin_bot_info(call)
        
    except Exception as e:
        print(f"Handle admin commands error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅ.", show_alert=True)

def show_admin_balance_menu(user_id, message_id):
    try:
        admin_text = """
💰 Aᴅᴍɪɴ Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴜsᴇʀ ʙᴀʟᴀɴᴄᴇs:
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ADMIN_IMAGE,
                caption=admin_text
            ),
            reply_markup=admin_balance_keyboard()
        )
    except Exception as e:
        print(f"Show admin balance menu error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴀᴅᴍɪɴ ʙᴀʟᴀɴᴄᴇ ᴍᴇɴᴜ.", show_alert=True)

def show_admin_users_menu(user_id, message_id):
    try:
        admin_text = """
👤 Aᴅᴍɪɴ Usᴇʀ Cᴏɴᴛʀᴏʟ

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴜsᴇʀs:
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ADMIN_IMAGE,
                caption=admin_text
            ),
            reply_markup=admin_users_keyboard()
        )
    except Exception as e:
        print(f"Show admin users menu error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴀᴅᴍɪɴ ᴜsᴇʀs ᴍᴇɴᴜ.", show_alert=True)

def show_admin_settings_menu(user_id, message_id):
    try:
        bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
        
        admin_text = f"""
⚙️ Aᴅᴍɪɴ Bᴏᴛ Sᴇᴛᴛɪɴɢs

Cᴜʀʀᴇɴᴛ Bᴏᴛ Sᴛᴀᴛᴜs: {bot_status}

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ʙᴏᴛ sᴇᴛᴛɪɴɢs:
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ADMIN_IMAGE,
                caption=admin_text
            ),
            reply_markup=admin_settings_keyboard()
        )
    except Exception as e:
        print(f"Show admin settings menu error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴀᴅᴍɪɴ sᴇᴛᴛɪɴɢs ᴍᴇɴᴜ.", show_alert=True)

def show_admin_stats_menu(user_id, message_id):
    try:
        total_users = get_all_users()
        total_orders = get_total_orders()
        total_deposits = get_total_deposits()
        total_spent = get_total_spent()
        revenue = total_deposits - total_spent
        
        stats_text = f"""
📊 Aᴅᴍɪɴ Sᴛᴀᴛɪsᴛɪᴄs

👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users:,}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders:,}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposits:.2f}
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{total_spent:.2f}
📈 Rᴇᴠᴇɴᴜᴇ: ₹{revenue:.2f}
🟢 Bᴏᴛ Sᴛᴀᴛᴜs: {'ON' if is_bot_accepting_orders() else 'OFF'}
        """
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ADMIN_IMAGE,
                caption=stats_text
            ),
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin_panel")),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Show admin stats menu error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴀᴅᴍɪɴ sᴛᴀᴛs.", show_alert=True)

# Admin action handlers
def start_admin_add_balance(call):
    try:
        user_id = call.from_user.id
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="👤 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ᴀᴅᴅ ʙᴀʟᴀɴᴄᴇ:",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_balance"))
        )
        
        admin_states[user_id] = {"action": "add_balance", "step": "user_id"}
        
    except Exception as e:
        print(f"Start admin add balance error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ᴀᴅᴅ ʙᴀʟᴀɴᴄᴇ.", show_alert=True)

def start_admin_remove_balance(call):
    try:
        user_id = call.from_user.id
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="👤 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ʀᴇᴍᴏᴠᴇ ʙᴀʟᴀɴᴄᴇ:",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_balance"))
        )
        
        admin_states[user_id] = {"action": "remove_balance", "step": "user_id"}
        
    except Exception as e:
        print(f"Start admin remove balance error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ʀᴇᴍᴏᴠᴇ ʙᴀʟᴀɴᴄᴇ.", show_alert=True)

def start_admin_broadcast(call):
    try:
        user_id = call.from_user.id
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="📢 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ:",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_panel"))
        )
        
        admin_states[user_id] = {"action": "broadcast", "step": "message"}
        
    except Exception as e:
        print(f"Start admin broadcast error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ.", show_alert=True)

def start_admin_find_user(call):
    try:
        user_id = call.from_user.id
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="👤 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ғɪɴᴅ:",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_users"))
        )
        
        admin_states[user_id] = {"action": "find_user", "step": "user_id"}
        
    except Exception as e:
        print(f"Start admin find user error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ғɪɴᴅ ᴜsᴇʀ.", show_alert=True)

def start_admin_ban_user(call):
    try:
        user_id = call.from_user.id
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="👤 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ʙᴀɴ:",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_users"))
        )
        
        admin_states[user_id] = {"action": "ban_user", "step": "user_id"}
        
    except Exception as e:
        print(f"Start admin ban user error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ʙᴀɴ ᴜsᴇʀ.", show_alert=True)

def start_admin_unban_user(call):
    try:
        user_id = call.from_user.id
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="👤 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ᴜɴʙᴀɴ:",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_users"))
        )
        
        admin_states[user_id] = {"action": "unban_user", "step": "user_id"}
        
    except Exception as e:
        print(f"Start admin unban user error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ᴜɴʙᴀɴ ᴜsᴇʀ.", show_alert=True)

def show_admin_user_stats(call):
    try:
        user_id = call.from_user.id
        
        total_users = get_all_users()
        total_deposits = get_total_deposits()
        total_spent = get_total_spent()
        avg_deposit = total_deposits / total_users if total_users > 0 else 0
        
        stats_text = f"""
📊 Aᴅᴍɪɴ Usᴇʀ Sᴛᴀᴛɪsᴛɪᴄs

👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users:,}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposits:.2f}
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{total_spent:.2f}
📈 Aᴠɢ Dᴇᴘᴏsɪᴛ: ₹{avg_deposit:.2f}
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=stats_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin_users"))
        )
        
    except Exception as e:
        print(f"Show admin user stats error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ᴜsᴇʀ sᴛᴀᴛs.", show_alert=True)

def toggle_bot_status(call):
    try:
        user_id = call.from_user.id
        current_status = is_bot_accepting_orders()
        new_status = not current_status
        
        set_bot_accepting_orders(new_status)
        
        status_text = "🟢 ON" if new_status else "🔴 OFF"
        bot.answer_callback_query(call.id, f"✅ Bᴏᴛ sᴛᴀᴛᴜs ᴄʜᴀɴɢᴇᴅ ᴛᴏ: {status_text}", show_alert=True)
        
        show_admin_settings_menu(user_id, call.message.message_id)
        
    except Exception as e:
        print(f"Toggle bot status error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴛᴏɢɢʟɪɴɢ ʙᴏᴛ sᴛᴀᴛᴜs.", show_alert=True)

def show_admin_bot_info(call):
    try:
        user_id = call.from_user.id
        
        bot_info = f"""
🤖 Bᴏᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ

📊 Tᴏᴛᴀʟ Usᴇʀs: {get_all_users():,}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {get_total_orders():,}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{get_total_deposits():.2f}
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{get_total_spent():.2f}
🟢 Bᴏᴛ Sᴛᴀᴛᴜs: {'ON' if is_bot_accepting_orders() else 'OFF'}
👑 Aᴅᴍɪɴs: {len(ADMIN_IDS)}
📦 Sᴇʀᴠɪᴄᴇs: {sum(len(services) for services in SERVICES.values())}
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=bot_info,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin_settings"))
        )
        
    except Exception as e:
        print(f"Show admin bot info error: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ sʜᴏᴡɪɴɢ ʙᴏᴛ ɪɴғᴏ.", show_alert=True)

# Admin message handlers for conversation states
@bot.message_handler(func=lambda message: message.from_user.id in ADMIN_IDS and message.from_user.id in admin_states)
def handle_admin_states(message):
    try:
        user_id = message.from_user.id
        state = admin_states[user_id]
        
        if state["step"] == "user_id":
            try:
                target_user_id = int(message.text)
                state["target_user_id"] = target_user_id
                state["step"] = "amount"
                
                action_text = "ᴀᴅᴅ" if state["action"] == "add_balance" else "ʀᴇᴍᴏᴠᴇ"
                
                bot.send_message(
                    user_id,
                    f"💰 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ᴛᴏ {action_text}:",
                    reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_balance"))
                )
                
            except ValueError:
                bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
                del admin_states[user_id]
        
        elif state["step"] == "amount":
            try:
                amount = float(message.text)
                target_user_id = state["target_user_id"]
                action = state["action"]
                
                target_user = get_user(target_user_id)
                
                if action == "add_balance":
                    new_balance = update_balance(target_user_id, amount)
                    success_msg = f"✅ Bᴀʟᴀɴᴄᴇ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!\n\n👤 Usᴇʀ: {target_user_id}\n💰 Aᴍᴏᴜɴᴛ: ₹{amount:.2f}\n💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance:.2f}"
                else:
                    if target_user['balance'] < amount:
                        bot.send_message(user_id, f"❌ Usᴇʀ ʜᴀs ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ. Cᴜʀʀᴇɴᴛ ʙᴀʟᴀɴᴄᴇ: ₹{target_user['balance']:.2f}")
                        del admin_states[user_id]
                        return
                    
                    new_balance = update_balance(target_user_id, -amount)
                    success_msg = f"✅ Bᴀʟᴀɴᴄᴇ ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!\n\n👤 Usᴇʀ: {target_user_id}\n💰 Aᴍᴏᴜɴᴛ: ₹{amount:.2f}\n💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance:.2f}"
                
                bot.send_message(user_id, success_msg)
                
                # Notify target user if possible
                try:
                    if action == "add_balance":
                        bot.send_message(target_user_id, f"🎉 Aᴅᴍɪɴ ᴀᴅᴅᴇᴅ ₹{amount:.2f} ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ!\n💰 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance:.2f}")
                    else:
                        bot.send_message(target_user_id, f"ℹ️ Aᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ ₹{amount:.2f} ғʀᴏᴍ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.\n💰 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance:.2f}")
                except:
                    pass
                
                del admin_states[user_id]
                show_admin_balance_menu(user_id, message.message_id)
                
            except ValueError:
                bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
                del admin_states[user_id]
        
        elif state["action"] == "broadcast" and state["step"] == "message":
            broadcast_msg = message.text
            users = users_collection.find({})
            total_users = users_collection.count_documents({})
            success_count = 0
            
            progress_msg = bot.send_message(user_id, f"📤 Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴛᴏ {total_users} ᴜsᴇʀs...\n\n✅ Sᴇɴᴛ: 0/{total_users}")
            
            for user in users:
                try:
                    bot.send_message(user["user_id"], f"📢 Aᴅᴍɪɴ Aɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ:\n\n{broadcast_msg}")
                    success_count += 1
                    
                    if success_count % 10 == 0:
                        bot.edit_message_text(
                            chat_id=user_id,
                            message_id=progress_msg.message_id,
                            text=f"📤 Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴛᴏ {total_users} ᴜsᴇʀs...\n\n✅ Sᴇɴᴛ: {success_count}/{total_users}"
                        )
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    continue
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=progress_msg.message_id,
                text=f"✅ Bʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!\n\n📤 Sᴇɴᴛ ᴛᴏ: {success_count}/{total_users} ᴜsᴇʀs"
            )
            
            del admin_states[user_id]
        
        elif state["action"] == "find_user" and state["step"] == "user_id":
            try:
                target_user_id = int(message.text)
                target_user = get_user(target_user_id)
                
                user_orders = get_user_orders(target_user_id, 5)
                user_deposits = get_user_deposits(target_user_id, 5)
                
                user_info = f"""
👤 Usᴇʀ Iɴғᴏʀᴍᴀᴛɪᴏɴ

🆔 Usᴇʀ ID: `{target_user_id}`
👤 Usᴇʀɴᴀᴍᴇ: @{target_user['username']}
💰 Bᴀʟᴀɴᴄᴇ: ₹{target_user['balance']:.2f}
💳 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛᴇᴅ: ₹{target_user.get('total_deposits', 0):.2f}
🛒 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{target_user.get('total_spent', 0):.2f}
📅 Jᴏɪɴᴇᴅ: {target_user['joined_date'].strftime('%d/%m/%Y %H:%M')}
🚫 Bᴀɴɴᴇᴅ: {'Yes' if target_user.get('banned') else 'No'}
📦 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {len(user_orders)}
                """
                
                bot.send_message(user_id, user_info, parse_mode='Markdown')
                del admin_states[user_id]
                
            except ValueError:
                bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
                del admin_states[user_id]
        
        elif state["action"] == "ban_user" and state["step"] == "user_id":
            try:
                target_user_id = int(message.text)
                
                # Ban user
                users_collection.update_one(
                    {"user_id": target_user_id},
                    {"$set": {"banned": True}}
                )
                
                bot.send_message(user_id, f"✅ Usᴇʀ {target_user_id} ʜᴀs ʙᴇᴇɴ ʙᴀɴɴᴇᴅ.")
                del admin_states[user_id]
                
            except ValueError:
                bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
                del admin_states[user_id]
        
        elif state["action"] == "unban_user" and state["step"] == "user_id":
            try:
                target_user_id = int(message.text)
                
                # Unban user
                users_collection.update_one(
                    {"user_id": target_user_id},
                    {"$set": {"banned": False}}
                )
                
                bot.send_message(user_id, f"✅ Usᴇʀ {target_user_id} ʜᴀs ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ.")
                del admin_states[user_id]
                
            except ValueError:
                bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
                del admin_states[user_id]
                
    except Exception as e:
        print(f"Handle admin states error: {e}")
        bot.send_message(message.from_user.id, "❌ Eʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ᴀᴅᴍɪɴ ʀᴇǫᴜᴇsᴛ.")
        if message.from_user.id in admin_states:
            del admin_states[message.from_user.id]

# Default message handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        user_id = message.from_user.id
        
        # Check if user is banned
        user = get_user(user_id)
        if user.get('banned'):
            return
        
        # If message is not a command and user is not in any state, show main menu
        if not message.text.startswith('/') and user_id not in admin_states and user_id not in user_states:
            show_main_menu_for_message(message)
            
    except Exception as e:
        print(f"Handle all messages error: {e}")

# Background tasks for order status updates (simplified)
def update_orders_status():
    """Bᴀᴄᴋɢʀᴏᴜɴᴅ ᴛᴀsᴋ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ᴏʀᴅᴇʀ sᴛᴀᴛᴜsᴇs"""
    while True:
        try:
            # Get pending orders
            pending_orders = orders_collection.find({
                "status": {"$in": ["Pending", "Processing"]}
            })
            
            for order in pending_orders:
                # Simulate status updates (in real implementation, check with API)
                if random.random() < 0.1:  # 10% chance to update status
                    new_status = random.choice(["Completed", "Processing", "Cancelled"])
                    orders_collection.update_one(
                        {"_id": order["_id"]},
                        {"$set": {"status": new_status}}
                    )
            
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            print(f"Order status update error: {e}")
            time.sleep(60)

# Start background tasks
def start_background_tasks():
    """Sᴛᴀʀᴛ ᴀʟʟ ʙᴀᴄᴋɢʀᴏᴜɴᴅ ᴛᴀsᴋs"""
    threading.Thread(target=update_orders_status, daemon=True).start()

if __name__ == "__main__":
    print("🤖 Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
    start_background_tasks()
    
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Pᴏʟʟɪɴɢ ᴇʀʀᴏʀ: {e}")
            time.sleep(5)
