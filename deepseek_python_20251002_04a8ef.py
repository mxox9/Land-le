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
BOT_TOKEN = os.getenv('BOT_TOKEN', '8052955693:AAGoXnNg90jqvcC1X1fVo_qKV8Y0eHjDAZg')
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
    # Test connection
    client.admin.command('ismaster')
    print("✅ MᴏɴɢᴏDB ᴄᴏɴɴᴇᴄᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ")
except Exception as e:
    print(f"❌ MᴏɴɢᴏDB ᴄᴏɴɴᴇᴄᴛɪᴏɴ ᴇʀʀᴏʀ: {e}")
    exit(1)

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
            "balance": 0,
            "total_deposits": 0,
            "total_spent": 0,
            "banned": False,
            "joined_date": datetime.now()
        })
        user = users_collection.find_one({"user_id": user_id})
    return user

def update_balance(user_id, amount):
    user = get_user(user_id)
    new_balance = user["balance"] + amount
    
    update_data = {"$set": {"balance": new_balance}}
    
    if amount > 0:
        update_data["$inc"] = {"total_deposits": amount}
    else:
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

def get_user_orders(user_id, limit=5):
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
    return list(result)[0]["total"] if result else 0

def get_total_spent():
    result = orders_collection.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$cost"}}}
    ])
    return list(result)[0]["total"] if result else 0

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

# Admin Keyboards
def admin_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ", callback_data="admin_balance"),
        InlineKeyboardButton("📢 Bʀᴏᴀᴅᴄᴀsᴛ", callback_data="admin_broadcast"),
        InlineKeyboardButton("👤 Usᴇʀ Cᴏɴᴛʀᴏʟ", callback_data="admin_users"),
        InlineKeyboardButton("📊 Sᴛᴀᴛs", callback_data="admin_stats"),
        InlineKeyboardButton("🔙 Mᴀɪɴ Mᴇɴᴜ", callback_data="main_menu")
    ]
    markup.add(*buttons)
    return markup

# Start command and main menu
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    
    get_user(user_id)  # Ensure user exists in DB
    
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

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        admin_text = """
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

💼 Mᴀɴᴀɢᴇ ʏᴏᴜʀ SMM ʙᴏᴛ ᴡɪᴛʜ ᴘᴏᴡᴇʀғᴜʟ ᴀᴅᴍɪɴ ᴛᴏᴏʟs.

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:
    """
        bot.send_photo(user_id, ADMIN_IMAGE, admin_text, reply_markup=admin_keyboard())
    else:
        bot.send_message(user_id, "❌ Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ.")

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    try:
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
        
        elif call.data.startswith("admin_"):
            if is_admin(user_id):
                handle_admin_commands(call)
            else:
                bot.answer_callback_query(call.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ!", show_alert=True)
                
    except Exception as e:
        print(f"Error in callback: {e}")
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!", show_alert=True)

# Deposit flow - FROM BOT (2).PY
def show_deposit_menu(user_id, message_id):
    clear_all_user_data(user_id)
    
    deposit_text = "Eɴᴛᴇʀ Tʜᴇ Aᴍᴏᴜɴᴛ Yᴏᴜ Wᴀɴᴛ Tᴏ Dᴇᴘᴏsɪᴛ 💰"
    
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
        bot.send_photo(user_id, DEPOSIT_IMAGE, deposit_text)
    
    msg = bot.send_message(user_id, "💳 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇᴘᴏsɪᴛ (ɪɴ ₹):")
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    user_id = message.from_user.id
    
    try:
        amount = float(message.text)
        utr = str(random.randint(100000000000, 999999999999))

        save_user_data(user_id, "deposit_utr", utr)
        save_user_data(user_id, "deposit_amount", amount)

        qr_img = generate_qr_code(amount)
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Pᴀɪᴅ ✅", callback_data="check_txn"),
            InlineKeyboardButton("Bᴀᴄᴋ 🔙", callback_data="main_menu")
        )

        sent = bot.send_photo(
            chat_id=user_id,
            photo=qr_img,
            caption=f"💰 *Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ*\n\n💵 Aᴍᴏᴜɴᴛ: ₹{amount}\n🔢 UTR: `{utr}`\n\n📲 Sᴄᴀɴ ᴛʜᴇ QR ᴄᴏᴅᴇ ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ ᴘᴀʏᴍᴇɴᴛ",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

        save_user_data(user_id, "deposit_qr_msg", sent.message_id)

    except Exception as e:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
        show_deposit_menu(user_id, message.message_id)

def check_transaction(call):
    user_id = call.from_user.id
    
    try:
        utr = get_user_data(user_id, "deposit_utr")
        amount = get_user_data(user_id, "deposit_amount")
        qr_msg_id = get_user_data(user_id, "deposit_qr_msg")

        if utr and amount:
            payment_verified = verify_payment(utr)
            
            if payment_verified:
                points = float(amount)
                new_balance = update_balance(user_id, points)
                add_deposit(user_id, amount, utr)
                update_deposit_status(utr, "Completed")

                try:
                    if qr_msg_id:
                        bot.delete_message(chat_id=user_id, message_id=qr_msg_id)
                except:
                    pass

                success_msg = bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Tʀᴀɴsᴀᴄᴛɪᴏɴ sᴜᴄᴄᴇssғᴜʟ! ₹{amount} ᴀᴅᴅᴇᴅ.\nNᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance}"
                )

                try:
                    bot.send_message(
                        chat_id=ADMIN_IDS[0],
                        text=f"✅ Sᴜᴄᴄᴇss\n\nUsᴇʀ {user_id} ᴅᴇᴘᴏsɪᴛᴇᴅ ₹{amount}.\nNᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance}"
                    )
                except:
                    pass

                clear_all_user_data(user_id)
                time.sleep(2)
                show_main_menu_for_message(success_msg)

            else:
                bot.answer_callback_query(
                    callback_query_id=call.id,
                    text="❌ Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴅᴇᴘᴏsɪᴛᴇᴅ ʏᴇᴛ. Pʟᴇᴀsᴇ ᴘᴀʏ ғɪʀsᴛ.",
                    show_alert=True
                )

        else:
            bot.answer_callback_query(callback_query_id=call.id, text="⚠️ Nᴏ ᴘᴇɴᴅɪɴɢ ᴅᴇᴘᴏsɪᴛ ғᴏᴜɴᴅ.", show_alert=True)

    except Exception as e:
        bot.answer_callback_query(callback_query_id=call.id, text="❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ.", show_alert=True)

# Order flow - FROM BOT (2).PY
def show_categories(user_id, message_id):
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=SERVICE_IMAGE,
                caption="🎯 *Sᴇʟᴇᴄᴛ ᴀ Cᴀᴛᴇɢᴏʀʏ*\n\nCʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ᴛᴏ ᴠɪᴇᴡ sᴇʀᴠɪᴄᴇs:"
            ),
            reply_markup=categories_keyboard(),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=SERVICE_IMAGE,
            caption="🎯 *Sᴇʟᴇᴄᴛ ᴀ Cᴀᴛᴇɢᴏʀʏ*\n\nCʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ᴛᴏ ᴠɪᴇᴡ sᴇʀᴠɪᴄᴇs:",
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
                caption=f"🛍️ *{category} Sᴇʀᴠɪᴄᴇs*\n\nSᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ:"
            ),
            reply_markup=services_keyboard(category),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=SERVICE_IMAGE,
            caption=f"🛍️ *{category} Sᴇʀᴠɪᴄᴇs*\n\nSᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ:",
            reply_markup=services_keyboard(category),
            parse_mode='Markdown'
        )

def start_order_flow(user_id, message_id, category, service_name):
    if category not in SERVICES or service_name not in SERVICES[category]:
        bot.answer_callback_query(message_id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!", show_alert=True)
        return
        
    service = SERVICES[category][service_name]
    
    service_info = f"""
*{service_name}*

💰 Pʀɪᴄᴇ: ₹{service['price']}/1000
📦 Mɪɴɪᴍᴜᴍ: {service['min']}
📈 Mᴀxɪᴍᴜᴍ: {service['max']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ ғᴏʀ ʏᴏᴜʀ ᴏʀᴅᴇʀ:
    """
    
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
        show_main_menu_for_message(message)
        return
    
    service = json.loads(service_data)
    
    save_user_data(user_id, "order_link", link)
    
    service_info = f"""
*{service_name}*

🔗 Lɪɴᴋ: `{link}`
💰 Pʀɪᴄᴇ: ₹{service['price']}/1000
📦 Mɪɴɪᴍᴜᴍ: {service['min']}
📈 Mᴀxɪᴍᴜᴍ: {service['max']}

Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ǫᴜᴀɴᴛɪᴛʏ:
    """
    
    bot.send_message(user_id, service_info, parse_mode='Markdown')
    
    msg = bot.send_message(user_id, "🔢 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ǫᴜᴀɴᴛɪᴛʏ:")
    bot.register_next_step_handler(msg, process_order_quantity)

def process_order_quantity(message):
    user_id = message.from_user.id
    
    try:
        quantity = int(message.text)
        
        category = get_user_data(user_id, "order_category")
        service_name = get_user_data(user_id, "order_service_name")
        service_data = get_user_data(user_id, "order_service_data")
        link = get_user_data(user_id, "order_link")
        
        if not all([category, service_name, service_data, link]):
            bot.send_message(user_id, "❌ Sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ. Pʟᴇᴀsᴇ sᴛᴀʀᴛ ᴏᴠᴇʀ.")
            show_main_menu_for_message(message)
            return
        
        service = json.loads(service_data)
        
        if quantity < service['min']:
            bot.send_message(user_id, f"❌ Qᴜᴀɴᴛɪᴛʏ ʙᴇʟᴏᴡ ᴍɪɴɪᴍᴜᴍ ({service['min']}).")
            return
        elif quantity > service['max']:
            bot.send_message(user_id, f"❌ Qᴜᴀɴᴛɪᴛʏ ᴇxᴄᴇᴇᴅs ᴍᴀxɪᴍᴜᴍ ({service['max']}).")
            return
        
        cost = (quantity / service['unit']) * service['price']
        cost = round(cost, 2)
        
        user_balance = get_balance(user_id)
        
        if user_balance < cost:
            bot.send_message(
                user_id,
                f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!\n\n💰 Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ: ₹{user_balance}\n💳 Rᴇǫᴜɪʀᴇᴅ: ₹{cost}\n\nPʟᴇᴀsᴇ ᴅᴇᴘᴏsɪᴛ ғᴜɴᴅs ғɪʀsᴛ.",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("💰 Dᴇᴘᴏsɪᴛ", callback_data="deposit")
                )
            )
            return
        
        # Confirm order
        order_summary = f"""
*Oʀᴅᴇʀ Sᴜᴍᴍᴀʀʏ*

📦 Sᴇʀᴠɪᴄᴇ: {service_name}
🔗 Lɪɴᴋ: `{link}`
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: ₹{cost}

Pʀᴏᴄᴇᴇᴅ ᴡɪᴛʜ ᴛʜɪs ᴏʀᴅᴇʀ?
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ", callback_data=f"confirm_order_{cost}"),
            InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="main_menu")
        )
        
        bot.send_message(user_id, order_summary, parse_mode='Markdown', reply_markup=markup)
        
        save_user_data(user_id, "order_quantity", quantity)
        save_user_data(user_id, "order_cost", cost)
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_order_'))
def confirm_order(call):
    user_id = call.from_user.id
    
    try:
        cost = float(call.data.split('_')[2])
        
        category = get_user_data(user_id, "order_category")
        service_name = get_user_data(user_id, "order_service_name")
        service_data = get_user_data(user_id, "order_service_data")
        link = get_user_data(user_id, "order_link")
        quantity = get_user_data(user_id, "order_quantity")
        
        if not all([category, service_name, service_data, link, quantity, cost]):
            bot.answer_callback_query(call.id, "❌ Sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ!", show_alert=True)
            return
        
        service = json.loads(service_data)
        
        user_balance = get_balance(user_id)
        
        if user_balance < cost:
            bot.answer_callback_query(call.id, "❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!", show_alert=True)
            return
        
        # Place order via API
        api_order_id = place_smm_order(service['id'], link, quantity)
        
        if api_order_id:
            # Deduct balance
            new_balance = update_balance(user_id, -cost)
            
            # Save order
            order = add_order(user_id, service_name, link, quantity, cost, api_order_id)
            
            # Success message
            success_msg = f"""
✅ *Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!*

📦 Sᴇʀᴠɪᴄᴇ: {service_name}
🔗 Lɪɴᴋ: `{link}`
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: ₹{cost}
📋 Oʀᴅᴇʀ ID: `{order['order_id']}`
💳 Rᴇᴍᴀɪɴɪɴɢ Bᴀʟᴀɴᴄᴇ: ₹{new_balance}

Tʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ʏᴏᴜʀ ᴏʀᴅᴇʀ!
            """
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=success_msg,
                parse_mode='Markdown'
            )
            
            # Notify admin
            try:
                bot.send_message(
                    ADMIN_IDS[0],
                    f"🛒 Nᴇᴡ Oʀᴅᴇʀ!\n\n👤 Usᴇʀ: {user_id}\n📦 Sᴇʀᴠɪᴄᴇ: {service_name}\n💰 Aᴍᴏᴜɴᴛ: ₹{cost}\n📋 Oʀᴅᴇʀ ID: {order['order_id']}"
                )
            except:
                pass
            
        else:
            bot.answer_callback_query(call.id, "❌ Oʀᴅᴇʀ ғᴀɪʟᴇᴅ! Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", show_alert=True)
        
        clear_all_user_data(user_id)
        
    except Exception as e:
        print(f"Order error: {e}")
        bot.answer_callback_query(call.id, "❌ Oʀᴅᴇʀ ғᴀɪʟᴇᴅ!", show_alert=True)

# Other menu functions
def show_orders(user_id, message_id):
    orders = get_user_orders(user_id)
    
    if not orders:
        try:
            bot.edit_message_media(
                chat_id=user_id,
                message_id=message_id,
                media=telebot.types.InputMediaPhoto(
                    media=HISTORY_IMAGE,
                    caption="📋 *Yᴏᴜʀ Oʀᴅᴇʀs*\n\nNᴏ ᴏʀᴅᴇʀs ғᴏᴜɴᴅ."
                ),
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
                parse_mode='Markdown'
            )
        except:
            bot.send_photo(
                chat_id=user_id,
                photo=HISTORY_IMAGE,
                caption="📋 *Yᴏᴜʀ Oʀᴅᴇʀs*\n\nNᴏ ᴏʀᴅᴇʀs ғᴏᴜɴᴅ.",
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
                parse_mode='Markdown'
            )
        return
    
    orders_text = "📋 *Yᴏᴜʀ Rᴇᴄᴇɴᴛ Oʀᴅᴇʀs*\n\n"
    
    for order in orders[:5]:
        status_emoji = "✅" if order['status'] == 'Completed' else "⏳" if order['status'] == 'Processing' else "❌"
        orders_text += f"{status_emoji} *{order['service_name']}*\n"
        orders_text += f"🔗 `{order['link'][:30]}...`\n"
        orders_text += f"🔢 {order['quantity']} | ₹{order['cost']}\n"
        orders_text += f"📅 {order['order_date'].strftime('%d/%m/%Y %H:%M')}\n\n"
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=HISTORY_IMAGE,
                caption=orders_text
            ),
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=HISTORY_IMAGE,
            caption=orders_text,
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
            parse_mode='Markdown'
        )

def show_refer(user_id, message_id):
    user = get_user(user_id)
    
    refer_text = f"""
👥 *Rᴇғᴇʀ & Eᴀʀɴ*

Iɴᴠɪᴛᴇ ʏᴏᴜʀ ғʀɪᴇɴᴅs ᴀɴᴅ ᴇᴀʀɴ 10% ᴏғ ᴛʜᴇɪʀ ᴇᴠᴇʀʏ ᴅᴇᴘᴏsɪᴛ!

🔗 Yᴏᴜʀ Rᴇғᴇʀʀᴀʟ Lɪɴᴋ:
`https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}`

💡 Sʜᴀʀᴇ ᴛʜɪs ʟɪɴᴋ ᴡɪᴛʜ ʏᴏᴜʀ ғʀɪᴇɴᴅs. Wʜᴇɴ ᴛʜᴇʏ ᴊᴏɪɴ ᴀɴᴅ ᴅᴇᴘᴏsɪᴛ, ʏᴏᴜ ɢᴇᴛ 10% ʀᴇᴡᴀʀᴅ!
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=REFER_IMAGE,
                caption=refer_text
            ),
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=REFER_IMAGE,
            caption=refer_text,
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
            parse_mode='Markdown'
        )

def show_account(user_id, message_id):
    user = get_user(user_id)
    
    account_text = f"""
👤 *Aᴄᴄᴏᴜɴᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ*

🆔 Usᴇʀ ID: `{user_id}`
👤 Usᴇʀɴᴀᴍᴇ: @{user['username']}
💰 Bᴀʟᴀɴᴄᴇ: ₹{user['balance']}
💳 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛᴇᴅ: ₹{user.get('total_deposits', 0)}
🛒 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{user.get('total_spent', 0)}
📅 Jᴏɪɴᴇᴅ: {user['joined_date'].strftime('%d/%m/%Y')}
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ACCOUNT_IMAGE,
                caption=account_text
            ),
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=ACCOUNT_IMAGE,
            caption=account_text,
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
            parse_mode='Markdown'
        )

def show_stats(user_id, message_id):
    user = get_user(user_id)
    
    stats_text = f"""
📊 *Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs*

👥 Tᴏᴛᴀʟ Usᴇʀs: {get_all_users()}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {get_total_orders()}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{get_total_deposits()}
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{get_total_spent()}

👤 *Yᴏᴜʀ Sᴛᴀᴛs*
💰 Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ: ₹{user['balance']}
💳 Yᴏᴜʀ Dᴇᴘᴏsɪᴛs: ₹{user.get('total_deposits', 0)}
🛒 Yᴏᴜʀ Sᴘᴇɴᴅɪɴɢ: ₹{user.get('total_spent', 0)}
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=HISTORY_IMAGE,
                caption=stats_text
            ),
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=HISTORY_IMAGE,
            caption=stats_text,
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu")),
            parse_mode='Markdown'
        )

def show_support(user_id, message_id):
    support_text = """
ℹ️ *Sᴜᴘᴘᴏʀᴛ*

Iғ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ ᴏʀ ʜᴀᴠᴇ ᴀɴʏ ǫᴜᴇsᴛɪᴏɴs, ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ᴛᴇᴀᴍ.

Oᴜʀ sᴜᴘᴘᴏʀᴛ ᴛᴇᴀᴍ ɪs ᴀᴠᴀɪʟᴀʙʟᴇ 24/7 ᴛᴏ ᴀssɪsᴛ ʏᴏᴜ.
    """
    
    try:
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
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=SERVICE_IMAGE,
            caption=support_text,
            reply_markup=support_keyboard(),
            parse_mode='Markdown'
        )

def check_channel_join(call):
    user_id = call.from_user.id
    
    if check_channel_membership(user_id):
        bot.answer_callback_query(call.id, "✅ Tʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ᴊᴏɪɴɪɴɢ! Nᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ.", show_alert=True)
        start_command(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ʏᴇᴛ. Pʟᴇᴀsᴇ ᴊᴏɪɴ ғɪʀsᴛ.", show_alert=True)

def show_main_menu(call):
    try:
        bot.edit_message_media(
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=WELCOME_IMAGE,
                caption="✨ Wᴇʟᴄᴏᴍᴇ Tᴏ SMM Bᴏᴛ ✨\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ᴛʜᴇ ᴍᴇɴᴜ ʙᴇʟᴏᴡ:"
            ),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(
            chat_id=call.from_user.id,
            photo=WELCOME_IMAGE,
            caption="✨ Wᴇʟᴄᴏᴍᴇ Tᴏ SMM Bᴏᴛ ✨\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ᴛʜᴇ ᴍᴇɴᴜ ʙᴇʟᴏᴡ:",
            reply_markup=main_menu_keyboard()
        )

def show_main_menu_for_message(message):
    bot.send_photo(
        chat_id=message.from_user.id,
        photo=WELCOME_IMAGE,
        caption="✨ Wᴇʟᴄᴏᴍᴇ Tᴏ SMM Bᴏᴛ ✨\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ᴛʜᴇ ᴍᴇɴᴜ ʙᴇʟᴏᴡ:",
        reply_markup=main_menu_keyboard()
    )

# Admin functions
def handle_admin_commands(call):
    user_id = call.from_user.id
    command = call.data
    
    if command == "admin_balance":
        show_admin_balance_menu(user_id, call.message.message_id)
    
    elif command == "admin_broadcast":
        start_broadcast(call)
    
    elif command == "admin_users":
        show_admin_users_menu(user_id, call.message.message_id)
    
    elif command == "admin_stats":
        show_admin_stats(user_id, call.message.message_id)

def show_admin_balance_menu(user_id, message_id):
    admin_text = """
💰 *Aᴅᴍɪɴ Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ*

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴜsᴇʀ ʙᴀʟᴀɴᴄᴇs:
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("➕ Aᴅᴅ Bᴀʟᴀɴᴄᴇ", callback_data="admin_add_balance"),
        InlineKeyboardButton("➖ Rᴇᴍᴏᴠᴇ Bᴀʟᴀɴᴄᴇ", callback_data="admin_remove_balance")
    )
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin"))
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ADMIN_IMAGE,
                caption=admin_text
            ),
            reply_markup=markup,
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=ADMIN_IMAGE,
            caption=admin_text,
            reply_markup=markup,
            parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_balance")
def admin_add_balance_start(call):
    user_id = call.from_user.id
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text="👤 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ᴀᴅᴅ ʙᴀʟᴀɴᴄᴇ:",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_balance"))
    )
    
    admin_states[user_id] = {"action": "add_balance", "step": "user_id"}

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_balance")
def admin_remove_balance_start(call):
    user_id = call.from_user.id
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text="👤 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ʀᴇᴍᴏᴠᴇ ʙᴀʟᴀɴᴄᴇ:",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_balance"))
    )
    
    admin_states[user_id] = {"action": "remove_balance", "step": "user_id"}

@bot.message_handler(func=lambda message: message.from_user.id in ADMIN_IDS and message.from_user.id in admin_states)
def handle_admin_states(message):
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
                success_msg = f"✅ Bᴀʟᴀɴᴄᴇ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!\n\n👤 Usᴇʀ: {target_user_id}\n💰 Aᴍᴏᴜɴᴛ: ₹{amount}\n💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance}"
            else:
                new_balance = update_balance(target_user_id, -amount)
                success_msg = f"✅ Bᴀʟᴀɴᴄᴇ ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!\n\n👤 Usᴇʀ: {target_user_id}\n💰 Aᴍᴏᴜɴᴛ: ₹{amount}\n💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance}"
            
            bot.send_message(user_id, success_msg)
            
            # Notify target user if possible
            try:
                if action == "add_balance":
                    bot.send_message(target_user_id, f"🎉 Aᴅᴍɪɴ ᴀᴅᴅᴇᴅ ₹{amount} ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ!\n💰 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance}")
                else:
                    bot.send_message(target_user_id, f"ℹ️ Aᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ ₹{amount} ғʀᴏᴍ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.\n💰 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance}")
            except:
                pass
            
            del admin_states[user_id]
            show_admin_balance_menu(user_id, message.message_id)
            
        except ValueError:
            bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
            del admin_states[user_id]

def start_broadcast(call):
    user_id = call.from_user.id
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text="📢 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ:",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin"))
    )
    
    admin_states[user_id] = {"action": "broadcast", "step": "message"}

@bot.message_handler(func=lambda message: message.from_user.id in ADMIN_IDS and message.from_user.id in admin_states and admin_states[message.from_user.id]["action"] == "broadcast")
def handle_broadcast_message(message):
    user_id = message.from_user.id
    
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

def show_admin_users_menu(user_id, message_id):
    admin_text = """
👤 *Aᴅᴍɪɴ Usᴇʀ Cᴏɴᴛʀᴏʟ*

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴜsᴇʀs:
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📊 Usᴇʀ Sᴛᴀᴛs", callback_data="admin_user_stats"),
        InlineKeyboardButton("🔍 Fɪɴᴅ Usᴇʀ", callback_data="admin_find_user")
    )
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin"))
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ADMIN_IMAGE,
                caption=admin_text
            ),
            reply_markup=markup,
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=ADMIN_IMAGE,
            caption=admin_text,
            reply_markup=markup,
            parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_stats")
def show_admin_user_stats(call):
    user_id = call.from_user.id
    
    total_users = get_all_users()
    total_deposits = get_total_deposits()
    total_spent = get_total_spent()
    
    stats_text = f"""
📊 *Aᴅᴍɪɴ Usᴇʀ Sᴛᴀᴛɪsᴛɪᴄs*

👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposits}
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{total_spent}
📈 Aᴠɢ Dᴇᴘᴏsɪᴛ: ₹{round(total_deposits/total_users, 2) if total_users > 0 else 0}
    """
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text=stats_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin_users"))
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_find_user")
def admin_find_user_start(call):
    user_id = call.from_user.id
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text="👤 Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ғɪɴᴅ:",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Cᴀɴᴄᴇʟ", callback_data="admin_users"))
    )
    
    admin_states[user_id] = {"action": "find_user", "step": "user_id"}

@bot.message_handler(func=lambda message: message.from_user.id in ADMIN_IDS and message.from_user.id in admin_states and admin_states[message.from_user.id]["action"] == "find_user")
def handle_find_user(message):
    user_id = message.from_user.id
    
    try:
        target_user_id = int(message.text)
        target_user = get_user(target_user_id)
        
        user_info = f"""
👤 *Usᴇʀ Iɴғᴏʀᴍᴀᴛɪᴏɴ*

🆔 Usᴇʀ ID: `{target_user_id}`
👤 Usᴇʀɴᴀᴍᴇ: @{target_user['username']}
💰 Bᴀʟᴀɴᴄᴇ: ₹{target_user['balance']}
💳 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛᴇᴅ: ₹{target_user.get('total_deposits', 0)}
🛒 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{target_user.get('total_spent', 0)}
📅 Jᴏɪɴᴇᴅ: {target_user['joined_date'].strftime('%d/%m/%Y %H:%M')}
        """
        
        bot.send_message(user_id, user_info, parse_mode='Markdown')
        del admin_states[user_id]
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID. Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
        del admin_states[user_id]

def show_admin_stats(user_id, message_id):
    total_users = get_all_users()
    total_orders = get_total_orders()
    total_deposits = get_total_deposits()
    total_spent = get_total_spent()
    
    stats_text = f"""
📊 *Aᴅᴍɪɴ Sᴛᴀᴛɪsᴛɪᴄs*

👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposits}
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{total_spent}
📈 Rᴇᴠᴇɴᴜᴇ: ₹{total_deposits - total_spent}
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                media=ADMIN_IMAGE,
                caption=stats_text
            ),
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin")),
            parse_mode='Markdown'
        )
    except:
        bot.send_photo(
            chat_id=user_id,
            photo=ADMIN_IMAGE,
            caption=stats_text,
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin")),
            parse_mode='Markdown'
        )

# Error handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ Uɴᴋɴᴏᴡɴ ᴄᴏᴍᴍᴀɴᴅ. Usᴇ /start ᴛᴏ ʙᴇɢɪɴ.")
    else:
        bot.send_message(message.chat.id, "💡 Usᴇ ᴛʜᴇ ᴍᴇɴᴜ ʙᴜᴛᴛᴏɴs ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ.")

# Start polling
if __name__ == "__main__":
    print("🤖 Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Pᴏʟʟɪɴɢ ᴇʀʀᴏʀ: {e}")
            time.sleep(5)