import telebot
import requests
import json
import random
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from urllib.parse import quote
from pymongo import MongoClient
from datetime import datetime, timedelta

# Bot Configuration
BOT_TOKEN = "8052955693:AAGf3qd5VXfq1I7d0_lM0eE3YwKFuBXLxvw"
ADMIN_ID = 6052975324
CHANNEL_ID = -1002587  # Replace with your channel ID
PROOF_CHANNEL = "@prooflelo1"  # Replace with your proof channel
SUPPORT_LINK = "https://t.me/your_support"  # Replace with your support

# API Keys
AUTODEP_API_KEY = "LY81vEV7"
AUTODEP_MERCHANT_KEY = "WYcmQI71591891985230"
SMM_API_KEY = "c33fb3166621856879b2e486b99a30f0c442ac92"
SMM_API_URL = "https://smm-jupiter.com/api/v2"

# MongoDB Configuration
MONGO_URI = "mongodb+srv://saifulmolla79088179_db_user:17gNrX0pC3bPqVaG@cluster0.fusvqca.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.smm_bot
users_collection = db.users
orders_collection = db.orders
services_collection = db.services
refund_tracking_collection = db.refund_tracking

# Image URLs
WELCOME_IMAGE = "https://t.me/prooflelo1/135?single"
SERVICE_IMAGE = "https://t.me/prooflelo1/138?single"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/136?single"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/137?single"
HISTORY_IMAGE = "https://t.me/prooflelo1/139?single"
REFER_IMAGE = "https://t.me/prooflelo1/17"
ADMIN_IMAGE = "https://t.me/prooflelo1/140?single"
TRACK_IMAGE = "https://t.me/prooflelo1/139?single"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Storage (using MongoDB now)
user_states = {}
bot_enabled = True

# Font style conversion function
def style_text(text):
    conversion_map = {
        'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'H': 'H', 'I': 'I', 
        'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R',
        'S': 'S', 'T': 'T', 'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z',
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ',
        'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ',
        's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
    }
    
    styled_text = ""
    for char in text:
        if char in conversion_map:
            styled_text += conversion_map[char]
        else:
            styled_text += char
    return styled_text

# Initialize services in database
def init_services():
    default_services = {
        "instagram": {
            "name": "📸 " + style_text("Iɴsᴛᴀɢʀᴀᴍ"),
            "services": {
                1: {"name": "❤️ " + style_text("Iɴsᴛᴀ Lɪᴋᴇs"), "rate": 50, "min": 100, "max": 100000, "unit": 1000, "api_id": 1},
                2: {"name": "👀 " + style_text("Iɴsᴛᴀ Vɪᴇᴡ's"), "rate": 50, "min": 100, "max": 100000, "unit": 1000, "api_id": 13685},
                3: {"name": "👥 " + style_text("Iɴsᴛᴀ Fᴏʟʟᴏᴡᴇʀs"), "rate": 100, "min": 50, "max": 50000, "unit": 1000, "api_id": 3}
            }
        },
        "facebook": {
            "name": "📘 " + style_text("Facebook"), 
            "services": {
                4: {"name": "👍 " + style_text("Facebook Likes"), "rate": 40, "min": 100, "max": 100000, "unit": 1000, "api_id": 4},
                5: {"name": "👀 " + style_text("Facebook Views"), "rate": 35, "min": 100, "max": 100000, "unit": 1000, "api_id": 5},
                6: {"name": "👥 " + style_text("Facebook Followers"), "rate": 80, "min": 50, "max": 50000, "unit": 1000, "api_id": 6}
            }
        },
        "youtube": {
            "name": "📺 " + style_text("YouTube"),
            "services": {
                7: {"name": "👍 " + style_text("YouTube Likes"), "rate": 60, "min": 100, "max": 100000, "unit": 1000, "api_id": 7},
                8: {"name": "👀 " + style_text("YouTube Views"), "rate": 45, "min": 100, "max": 100000, "unit": 1000, "api_id": 8},
                9: {"name": "🔔 " + style_text("YouTube Subscribers"), "rate": 150, "min": 50, "max": 25000, "unit": 1000, "api_id": 9}
            }
        },
        "telegram": {
            "name": "✈️ " + style_text("Telegram"),
            "services": {
                10: {"name": "👥 " + style_text("Telegram Members"), "rate": 200, "min": 50, "max": 10000, "unit": 1000, "api_id": 10},
                11: {"name": "❤️ " + style_text("Telegram Post Likes"), "rate": 80, "min": 100, "max": 50000, "unit": 1000, "api_id": 11},
                12: {"name": "👀 " + style_text("Telegram Post Views"), "rate": 50, "min": 100, "max": 50000, "unit": 1000, "api_id": 12}
            }
        }
    }
    
    # Save to database if not exists
    if services_collection.count_documents({}) == 0:
        services_collection.insert_one(default_services)

# Get services from database
def get_services():
    services_data = services_collection.find_one({})
    if not services_data:
        init_services()
        services_data = services_collection.find_one({})
    return services_data

# Update service in database
def update_service(category, service_id, new_data):
    services_data = get_services()
    key = f"{category}.services.{service_id}"
    services_collection.update_one({}, {"$set": {key: new_data}})

# Initialize user data in MongoDB
def init_user(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        users_collection.insert_one({
            "user_id": user_id,
            "balance": 0.0,
            "total_deposits": 0.0,
            "total_spent": 0.0,
            "joined_date": datetime.now(),
            "banned": False,
            "orders_count": 0
        })
    return users_collection.find_one({"user_id": user_id})

def get_user_balance(user_id):
    user = init_user(user_id)
    return user["balance"]

def update_user_balance(user_id, amount):
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": amount}}
    )

def update_user_deposits(user_id, amount):
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"total_deposits": amount}}
    )

def update_user_spent(user_id, amount):
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"total_spent": amount, "orders_count": 1}}
    )

def is_user_banned(user_id):
    user = init_user(user_id)
    return user.get("banned", False)

def ban_user(user_id):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"banned": True}}
    )

def unban_user(user_id):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"banned": False}}
    )

def save_order(user_id, order_data):
    orders_collection.insert_one({
        "user_id": user_id,
        "order_id": order_data["order_id"],
        "service": order_data["service"],
        "link": order_data["link"],
        "quantity": order_data["quantity"],
        "cost": order_data["cost"],
        "status": order_data["status"],
        "api_id": order_data.get("api_id"),
        "timestamp": datetime.now(),
        "refunded": False,
        "checked_for_refund": False
    })

def get_user_orders(user_id, limit=5):
    return list(orders_collection.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(limit))

def get_order_by_id(order_id):
    return orders_collection.find_one({"order_id": order_id})

def update_order_status(order_id, status):
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"status": status}}
    )

def mark_order_refunded(order_id):
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"refunded": True, "checked_for_refund": True}}
    )

def mark_order_checked(order_id):
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"checked_for_refund": True}}
    )

def get_orders_for_refund_check():
    return list(orders_collection.find({
        "checked_for_refund": False,
        "timestamp": {"$lt": datetime.now() - timedelta(seconds=30)}
    }))

def get_all_users():
    return list(users_collection.find({}))

def get_total_users():
    return users_collection.count_documents({})

def get_total_orders():
    return orders_collection.count_documents({})

def get_total_deposits():
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_deposits"}}}]
    result = list(users_collection.aggregate(pipeline))
    return result[0]["total"] if result else 0

def get_total_spent():
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_spent"}}}]
    result = list(users_collection.aggregate(pipeline))
    return result[0]["total"] if result else 0

# Main Menu Keyboard with emojis
def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton("💳 " + style_text("Deposit"), callback_data="deposit"),
        InlineKeyboardButton("🛒 " + style_text("Order"), callback_data="order"),
        InlineKeyboardButton("📦 " + style_text("Orders"), callback_data="orders"),
        InlineKeyboardButton("🔍 " + style_text("Track"), callback_data="track"),
        InlineKeyboardButton("👥 " + style_text("Refer"), callback_data="refer"),
        InlineKeyboardButton("👤 " + style_text("Account"), callback_data="account"),
        InlineKeyboardButton("📊 " + style_text("Stats"), callback_data="stats"),
        InlineKeyboardButton("🆘 " + style_text("Support"), callback_data="support")
    ]
    # Add buttons in rows of 3
    for i in range(0, len(buttons), 3):
        keyboard.add(*buttons[i:i+3])
    return keyboard

# Categories Keyboard with emojis
def categories_keyboard():
    keyboard = InlineKeyboardMarkup()
    services_data = get_services()
    for category_key, category_data in services_data.items():
        if category_key != "_id":
            keyboard.add(InlineKeyboardButton(category_data["name"], callback_data=f"category_{category_key}"))
    keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land"))
    return keyboard

# Admin Keyboard with emojis
def admin_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💰 " + style_text("Balance Control"), callback_data="admin_balance"))
    keyboard.add(InlineKeyboardButton("📊 " + style_text("Manage Prices"), callback_data="admin_prices"))
    keyboard.add(InlineKeyboardButton("📢 " + style_text("Broadcast"), callback_data="admin_broadcast"))
    keyboard.add(InlineKeyboardButton("👥 " + style_text("User Control"), callback_data="admin_users"))
    keyboard.add(InlineKeyboardButton("⚙️ " + style_text("Bot Control"), callback_data="admin_control"))
    keyboard.add(InlineKeyboardButton("📈 " + style_text("Stats"), callback_data="admin_stats"))
    keyboard.add(InlineKeyboardButton("🔙 " + style_text("Main Menu"), callback_data="land"))
    return keyboard

# Start Command
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        if not bot_enabled and message.from_user.id != ADMIN_ID:
            bot.send_message(message.chat.id, "🔧 " + style_text("Bot is currently under maintenance. Please try again later."))
            return
            
        if is_user_banned(message.from_user.id):
            bot.send_message(message.chat.id, "🚫 " + style_text("You are banned from using this bot."))
            return
            
        init_user(message.from_user.id)
        
        caption = "👋 " + style_text("""
Welcome to SMM Bot

🌟 Your Trusted SMM Panel

✨ Features:
⚡ Instant Start
🎯 High Quality Services
🛡️ 24/7 Support

🚀 Start Growing Your Social Media Now!
        """)
        
        bot.send_photo(
            chat_id=message.chat.id,
            photo=WELCOME_IMAGE,
            caption=caption,
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Start command error: {e}")
        bot.send_message(message.chat.id, "❌ " + style_text("An error occurred. Please try again."))

# Admin Command
@bot.message_handler(commands=['admin'])
def admin_command(message):
    try:
        if message.from_user.id != ADMIN_ID:
            bot.send_message(message.chat.id, "🚫 " + style_text("Access denied."))
            return
            
        caption = "🛠️ " + style_text("""
Admin Panel

🎛️ Full Control Over Bot

Manage all bot operations from here
        """)
        
        bot.send_photo(
            chat_id=message.chat.id,
            photo=ADMIN_IMAGE,
            caption=caption,
            reply_markup=admin_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin command error: {e}")
        bot.send_message(message.chat.id, "❌ " + style_text("An error occurred. Please try again."))

# Callback Query Handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global bot_enabled
    try:
        user_id = call.from_user.id
        
        if not bot_enabled and user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "🔧 " + style_text("Bot is currently under maintenance."))
            return
            
        if is_user_banned(user_id):
            bot.answer_callback_query(call.id, "🚫 " + style_text("You are banned from using this bot."))
            return
            
        init_user(user_id)
        
        if call.data == "land":
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            start_command(call.message)
            
        elif call.data == "deposit":
            show_deposit(call)
            
        elif call.data == "order":
            show_categories(call)
            
        elif call.data == "orders":
            show_orders(call)
            
        elif call.data == "track":
            start_track_order(call)
            
        elif call.data == "refer":
            show_refer(call)
            
        elif call.data == "account":
            show_account(call)
            
        elif call.data == "stats":
            show_stats(call)
            
        elif call.data == "support":
            show_support(call)
            
        elif call.data.startswith("category_"):
            category = call.data.split("_")[1]
            show_services(call, category)
            
        elif call.data.startswith("service_"):
            service_id = int(call.data.split("_")[1])
            start_order(call, service_id)
            
        elif call.data == "check_txn":
            check_transaction(call)
            
        elif call.data == "admin_balance":
            admin_balance_control(call)
            
        elif call.data == "admin_prices":
            admin_manage_prices_menu(call)
            
        elif call.data == "admin_broadcast":
            admin_broadcast(call)
            
        elif call.data == "admin_users":
            admin_user_control(call)
            
        elif call.data == "admin_control":
            admin_bot_control(call)
            
        elif call.data == "admin_stats":
            admin_stats(call)
            
        elif call.data == "admin_add_balance":
            start_admin_add_balance(call)
            
        elif call.data == "admin_deduct_balance":
            start_admin_deduct_balance(call)
            
        elif call.data == "admin_ban_user":
            start_admin_ban_user(call)
            
        elif call.data == "admin_unban_user":
            start_admin_unban_user(call)
            
        elif call.data.startswith("refill_"):
            order_id = call.data.split("_")[1]
            handle_refill(call, order_id)
            
        elif call.data == "back_to_admin":
            admin_command(call.message)
            
        elif call.data.startswith("edit_service_"):
            parts = call.data.split("_")
            category = parts[2]
            service_id = int(parts[3])
            start_edit_service(call, category, service_id)
            
        elif call.data.startswith("change_rate_"):
            parts = call.data.split("_")
            category = parts[2]
            service_id = int(parts[3])
            start_change_rate(call, category, service_id)
            
        elif call.data.startswith("change_api_"):
            parts = call.data.split("_")
            category = parts[2]
            service_id = int(parts[3])
            start_change_api(call, category, service_id)
            

# Deposit Flow
def show_deposit(call):
    try:
        user_id = call.from_user.id
        
        caption = "💳 " + style_text("""
Deposit Funds

💰 Enter The Amount You Want To Deposit

📊 Minimum Deposit: ₹10
        """)
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=DEPOSIT_IMAGE,
                caption=caption,
                parse_mode='HTML'
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")
            )
        )
        
        # Set user state to wait for deposit amount
        user_states[user_id] = "waiting_deposit_amount"
        
    except Exception as e:
        print(f"Show deposit error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error showing deposit. Please try again."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_deposit_amount")
def handle_deposit_amount(message):
    user_id = message.from_user.id
    
    try:
        amount = float(message.text)
        
        if amount < 10:
            bot.send_message(user_id, "⚠️ " + style_text("Minimum deposit amount is ₹10"))
            return
            
        # Generate random 12-digit UTR
        utr = str(random.randint(100000000000, 999999999999))
        
        # Save deposit data
        user_states[user_id] = {
            "state": "deposit_pending",
            "deposit_utr": utr,
            "deposit_amount": amount
        }
        
        # Create UPI payment link
        upi_link = f"upi://pay?pa=paytm.s1m11be@pty&pn=Paytm&am={amount}&tn=Deposit&tr={utr}"
        
        # Generate QR code
        qr_url = f"https://quickchart.io/qr?text={quote(upi_link)}&size=300"
        
        caption = style_text(f"""
💳 Deposit Request

💰 Amount: ₹{amount}
🔢 UTR: {utr}

📱 Scan the QR code to complete your deposit
        """)
        
        # Send QR code
        bot.send_photo(
            chat_id=user_id,
            photo=qr_url,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ " + style_text("Paid"), callback_data="check_txn")],
                [InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")]
            ]),
            parse_mode='HTML'
        )
        
    except ValueError:
        bot.send_message(user_id, "❌ " + style_text("Please enter a valid amount (numbers only)"))
    except Exception as e:
        print(f"Deposit amount error: {e}")
        bot.send_message(user_id, "❌ " + style_text("An error occurred. Please try again."))

# Check Transaction
def check_transaction(call):
    user_id = call.from_user.id
    
    try:
        if user_id not in user_states or user_states[user_id].get("state") != "deposit_pending":
            bot.answer_callback_query(call.id, "❌ " + style_text("No pending deposit found."), show_alert=True)
            return
            
        utr = user_states[user_id]["deposit_utr"]
        amount = user_states[user_id]["deposit_amount"]
        
        # Check transaction via Autodep API
        url = f"https://erox-autodep-api.onrender.com/api?key={AUTODEP_API_KEY}&merchantkey={AUTODEP_MERCHANT_KEY}&transactionid={utr}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("result", {}).get("STATUS") == "TXN_SUCCESS":
            # Update user balance in MongoDB
            update_user_balance(user_id, amount)
            update_user_deposits(user_id, amount)
            
            current_balance = get_user_balance(user_id)
            
            # Clear deposit data
            if user_id in user_states:
                user_states[user_id] = None
            
            # Notify user
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption="✅ " + style_text(f"Transaction Successful!\n\n💰 ₹{amount} added to your balance\n💳 New Balance: ₹{current_balance}"),
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🏠 " + style_text("Main Menu"), callback_data="land")
                )
            )
            
            # Notify admin
            try:
                bot.send_message(
                    ADMIN_ID,
                    "💰 " + style_text(f"New Deposit\n\n👤 User: {user_id}\n💳 Amount: ₹{amount}\n💰 Balance: ₹{current_balance}")
                )
            except:
                pass
            
        else:
            bot.answer_callback_query(
                call.id,
                "❌ " + style_text("You have not deposited yet. Please pay first."),
                show_alert=True
            )
            
    except Exception as e:
        print(f"Check transaction error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error checking transaction. Please try again."), show_alert=True)

# Order Flow
def show_categories(call):
    try:
        caption = "🛒 " + style_text("""
Services Menu

🎯 Choose a category to start ordering:
        """)
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=SERVICE_IMAGE,
                caption=caption,
                parse_mode='HTML'
            ),
            reply_markup=categories_keyboard()
        )
    except Exception as e:
        print(f"Show categories error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error showing categories. Please try again."))

def show_services(call, category):
    try:
        services_data = get_services()
        if category not in services_data:
            bot.answer_callback_query(call.id, "❌ " + style_text("Category not found"))
            return
            
        category_data = services_data[category]
        keyboard = InlineKeyboardMarkup()
        
        for service_id, service in category_data["services"].items():
            keyboard.add(InlineKeyboardButton(
                f"{service['name']} - ₹{service['rate']}/{service['unit']}",
                callback_data=f"service_{service_id}"
            ))
        
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="order"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=style_text(f"🛒 Services - {category_data['name']}\n\n🎯 Select a service to order:"),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Show services error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error showing services. Please try again."))

def start_order(call, service_id):
    try:
        user_id = call.from_user.id
        
        # Find service
        service = None
        category_name = None
        category_key = None
        services_data = get_services()
        for cat_key, cat_data in services_data.items():
            if cat_key != "_id" and service_id in cat_data["services"]:
                service = cat_data["services"][service_id]
                category_name = cat_data["name"]
                category_key = cat_key
                break
        
        if not service:
            bot.answer_callback_query(call.id, "❌ " + style_text("Service not found"))
            return
            
        # Save service selection
        user_states[user_id] = {
            "state": "waiting_order_link",
            "selected_service": service_id,
            "service_details": service
        }
        
        caption = style_text(f"""
🛒 Order Details

📦 Service: {service['name']}
💰 Price: ₹{service['rate']}/{service['unit']}
📊 Min: {service['min']}
📈 Max: {service['max']}

🔗 Please send the link:
        """)
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data=f"category_{category_key}")
            ),
            parse_mode='HTML'
        )
        
    except Exception as e:
        print(f"Start order error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting order. Please try again."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == "waiting_order_link")
def handle_order_link(message):
    user_id = message.from_user.id
    
    try:
        if user_id not in user_states or "selected_service" not in user_states[user_id]:
            bot.send_message(user_id, "❌ " + style_text("No service selected. Please start over."))
            user_states[user_id] = None
            return
            
        link = message.text
        user_states[user_id]["order_link"] = link
        user_states[user_id]["state"] = "waiting_order_quantity"
        
        service = user_states[user_id]["service_details"]
        
        bot.send_message(
            user_id,
            style_text(f"✅ Link Saved: {link}\n\n📊 Now please enter the quantity:\n(Min: {service['min']}, Max: {service['max']})")
        )
        
    except Exception as e:
        print(f"Order link error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error processing link. Please try again."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == "waiting_order_quantity")
def handle_order_quantity(message):
    user_id = message.from_user.id
    
    try:
        if user_id not in user_states or "selected_service" not in user_states[user_id]:
            bot.send_message(user_id, "❌ " + style_text("No service selected. Please start over."))
            user_states[user_id] = None
            return
            
        quantity = int(message.text)
        service = user_states[user_id]["service_details"]
        link = user_states[user_id]["order_link"]
        
        # Validate quantity
        if quantity < service["min"] or quantity > service["max"]:
            bot.send_message(
                user_id,
                style_text(f"⚠️ Quantity must be between {service['min']} and {service['max']}")
            )
            return
            
        # Calculate cost
        cost = (quantity / service["unit"]) * service["rate"]
        
        # Check balance
        current_balance = get_user_balance(user_id)
        if current_balance < cost:
            bot.send_message(
                user_id,
                style_text(f"❌ Insufficient Balance\n\n💳 Required: ₹{cost:.2f}\n💰 Available: ₹{current_balance:.2f}\n\n💸 Please deposit first.")
            )
            user_states[user_id] = None
            return
            
        # Place order via SMM API
        order_result = place_smm_order(
            service_id=service["api_id"],  # Use API service ID
            link=link,
            quantity=quantity
        )
        
        if order_result["success"]:
            # Deduct balance in MongoDB
            update_user_balance(user_id, -cost)
            update_user_spent(user_id, cost)
            
            # Save order to MongoDB
            order_id = order_result["order_id"]
            order_data = {
                "order_id": order_id,
                "service": service["name"],
                "link": link,
                "quantity": quantity,
                "cost": cost,
                "status": "Pending",
                "api_id": service["api_id"]
            }
            save_order(user_id, order_data)
            
            # Get updated balance
            updated_balance = get_user_balance(user_id)
            
            # Confirm to user
            bot.send_message(
                user_id,
                style_text(f"✅ Order Placed Successfully!\n\n📦 Order ID: {order_id}\n💳 Amount: ₹{cost:.2f}\n💰 Balance: ₹{updated_balance:.2f}")
            )
            
            # Send to proof channel
            send_proof_message(user_id, service["name"], quantity, cost, order_id)
            
        else:
            bot.send_message(
                user_id,
                style_text(f"❌ Order Failed\n\nError: {order_result['error']}")
            )
            
    except ValueError:
        bot.send_message(user_id, "❌ " + style_text("Please enter a valid number for quantity"))
        return
    except Exception as e:
        print(f"Order quantity error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error processing order. Please try again."))
        
    user_states[user_id] = None

def place_smm_order(service_id, link, quantity):
    try:
        # Actual SMM API call
        params = {
            "key": SMM_API_KEY,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        
        response = requests.post(SMM_API_URL, data=params, timeout=30)
        data = response.json()
        
        if data.get("order"):
            return {
                "success": True,
                "order_id": data["order"]
            }
        else:
            return {
                "success": False,
                "error": data.get("error", "Unknown error from SMM API")
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def send_proof_message(user_id, service_name, quantity, cost, order_id):
    proof_text = style_text(f"""
🆕 New Order Placed!

👤 User: {user_id}
📦 Service: {service_name}
📊 Quantity: {quantity}
💳 Amount: ₹{cost:.2f}
🆔 Order ID: {order_id}

⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
    """)
    
    try:
        bot.send_message(
            PROOF_CHANNEL,
            proof_text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🤖 " + style_text("Bot Here"), url=f"https://t.me/{(bot.get_me()).username}")
            )
        )
    except Exception as e:
        print(f"Proof channel error: {e}")

# Track Order Feature - FIXED
def start_track_order(call):
    try:
        user_id = call.from_user.id
        
        caption = "🔍 " + style_text("""
Track Order

📦 Enter your Order ID to check status
        """)
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=TRACK_IMAGE,
                caption=caption,
                parse_mode='HTML'
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")
            )
        )
        
        user_states[user_id] = {"state": "waiting_track_order_id"}
        
    except Exception as e:
        print(f"Start track order error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting track order. Please try again."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == "waiting_track_order_id")
def handle_track_order_id(message):
    user_id = message.from_user.id
    order_id = message.text
    
    try:
        # Check order in database first - FIXED: Convert order_id to string for consistency
        order = get_order_by_id(str(order_id))
        if not order:
            bot.send_message(user_id, "❌ " + style_text("Order ID not found in database."))
            user_states[user_id] = None
            return
        
        # Check order status via SMM API
        status_result = check_order_status(order_id)
        
        if status_result["success"]:
            status = status_result["status"]
            # Update order status in database
            update_order_status(str(order_id), status)
            
            # Prepare response
            response_text = style_text(f"""
📦 Order Tracking

🆔 Order ID: {order_id}
📦 Service: {order['service']}
🔗 Link: {order['link']}
📊 Quantity: {order['quantity']}
💳 Cost: ₹{order['cost']:.2f}
📊 Status: {status}
            """)
            
            keyboard = InlineKeyboardMarkup()
            
            # Check if refill is available
            if status.lower() in ["completed", "complete"] and status_result.get("refill_available", False):
                response_text += style_text("\n\n🔄 Refill is available for this order!")
                keyboard.add(InlineKeyboardButton("🔄 " + style_text("Refill Order"), callback_data=f"refill_{order_id}"))
            else:
                response_text += style_text("\n\n❌ Refill is not available for this order.")
            
            keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land"))
            
            bot.send_message(
                user_id,
                response_text,
                reply_markup=keyboard
            )
        else:
            bot.send_message(
                user_id,
                style_text(f"❌ Error checking order status: {status_result['error']}")
            )
            
    except Exception as e:
        print(f"Track order error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error tracking order. Please try again."))
    
    user_states[user_id] = None

def check_order_status(order_id):
    try:
        # Check order status via SMM API
        params = {
            "key": SMM_API_KEY,
            "action": "status",
            "order": order_id
        }
        
        response = requests.post(SMM_API_URL, data=params, timeout=30)
        data = response.json()
        
        if data:
            status = data.get("status", "Unknown")
            # Check if refill is available (this depends on your SMM API)
            refill_available = False
            if status.lower() in ["completed", "complete"]:
                # You might need to check additional fields from your SMM API
                refill_available = data.get("refill", False) or data.get("refill_available", False)
            
            return {
                "success": True,
                "status": status,
                "refill_available": refill_available
            }
        else:
            return {
                "success": False,
                "error": "No data received from API"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def handle_refill(call, order_id):
    try:
        user_id = call.from_user.id
        
        # Check if order exists and belongs to user - FIXED: Convert order_id to string
        order = get_order_by_id(str(order_id))
        if not order or order["user_id"] != user_id:
            bot.answer_callback_query(call.id, "❌ " + style_text("Order not found or access denied."))
            return
        
        # Process refill via SMM API
        refill_result = process_refill(order_id)
        
        if refill_result["success"]:
            bot.answer_callback_query(call.id, "✅ " + style_text("Refill request submitted successfully!"))
            
            # Update message
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=style_text(f"✅ Refill Request Submitted!\n\n🆔 Order ID: {order_id}\n📦 Service: {order['service']}\n\n🔄 Your order is being refilled."),
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")
                )
            )
        else:
            bot.answer_callback_query(call.id, "❌ " + style_text(f"Refill failed: {refill_result['error']}"))
            
    except Exception as e:
        print(f"Handle refill error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error processing refill. Please try again."))

def process_refill(order_id):
    try:
        # Process refill via SMM API
        params = {
            "key": SMM_API_KEY,
            "action": "refill",
            "order": order_id
        }
        
        response = requests.post(SMM_API_URL, data=params, timeout=30)
        data = response.json()
        
        if data and data.get("status") == "success":
            return {
                "success": True
            }
        else:
            return {
                "success": False,
                "error": data.get("error", "Unknown error from SMM API")
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Other Menu Functions - FIXED Account Function
def show_orders(call):
    try:
        user_id = call.from_user.id
        user_orders = get_user_orders(user_id, 5)  # Last 5 orders
        
        if not user_orders:
            caption = "📦 " + style_text("No orders found")
        else:
            caption = "📦 " + style_text("Last 5 Orders:\n\n")
            for order in user_orders:
                caption += f"🆔 {order['order_id']}\n"
                caption += f"📦 {order['service']}\n"
                caption += f"📊 {order['quantity']}\n"
                caption += f"💳 ₹{order['cost']:.2f}\n"
                caption += f"📊 {order['status']}\n"
                caption += "─" * 20 + "\n"
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=HISTORY_IMAGE,
                caption=caption,
                parse_mode='HTML'
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")
            )
        )
    except Exception as e:
        print(f"Show orders error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error showing orders. Please try again."))

def show_refer(call):
    try:
        user_id = call.from_user.id
        bot_username = (bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        
        caption = style_text(f"""
👥 Referral System

🔗 Your Referral Link:
{referral_link}

🎁 Referral Bonus:
• 10% of your friend's first deposit
• Unlimited earnings

📤 Share this link and earn more!
        """)
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=REFER_IMAGE,
                caption=caption,
                parse_mode='HTML'
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")
            )
        )
    except Exception as e:
        print(f"Show refer error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error showing referral. Please try again."))

def show_account(call):
    try:
        user_id = call.from_user.id
        user = init_user(user_id)
        
        # FIXED: Properly format the account information
        caption = style_text(f"""
👤 Account Information

🆔 User ID: {user_id}
💰 Balance: ₹{user.get('balance', 0):.2f}
💳 Total Deposits: ₹{user.get('total_deposits', 0):.2f}
🛒 Total Spent: ₹{user.get('total_spent', 0):.2f}
📦 Total Orders: {user.get('orders_count', 0)}
⏰ Joined: {user.get('joined_date', 'N/A')}
        """)
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=ACCOUNT_IMAGE,
                caption=caption,
                parse_mode='HTML'
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")
            )
        )
    except Exception as e:
        print(f"Show account error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error showing account. Please try again."))

def show_stats(call):
    try:
        total_users = get_total_users()
        total_orders = get_total_orders()
        total_deposits = get_total_deposits()
        total_spent = get_total_spent()
        
        caption = style_text(f"""
📊 Bot Statistics

👥 Total Users: {total_users}
📦 Total Orders: {total_orders}
💳 Total Deposits: ₹{total_deposits:.2f}
🛒 Total Spent: ₹{total_spent:.2f}

🤖 Bot Status: {'🟢 Online' if bot_enabled else '🔴 Offline'}
        """)
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Show stats error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error showing stats. Please try again."))

def show_support(call):
    try:
        caption = "🆘 " + style_text("""
Support

❓ Need help? Contact our support team:

🕒 Available 24/7
⚡ Quick responses
🔧 Technical support
        """)
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 " + style_text("Contact Support"), url=SUPPORT_LINK)],
                [InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")]
            ]),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Show support error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error showing support. Please try again."))

# Admin Functions with inline buttons - FIXED All Admin Functions
def admin_balance_control(call):
    try:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("➕ " + style_text("Add Balance"), callback_data="admin_add_balance"))
        keyboard.add(InlineKeyboardButton("➖ " + style_text("Deduct Balance"), callback_data="admin_deduct_balance"))
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="back_to_admin"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="💰 " + style_text("Balance Control\n\nManage user balances:"),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin balance control error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error accessing balance control."))

def start_admin_add_balance(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="➕ " + style_text("Add Balance\n\nPlease send user ID and amount in format:\nuser_id amount"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin_balance")
            ),
            parse_mode='HTML'
        )
        
        user_states[call.from_user.id] = {"state": "admin_add_balance"}
        
    except Exception as e:
        print(f"Start admin add balance error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting add balance."))

def start_admin_deduct_balance(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="➖ " + style_text("Deduct Balance\n\nPlease send user ID and amount in format:\nuser_id amount"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin_balance")
            ),
            parse_mode='HTML'
        )
        
        user_states[call.from_user.id] = {"state": "admin_deduct_balance"}
        
    except Exception as e:
        print(f"Start admin deduct balance error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting deduct balance."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") in ["admin_add_balance", "admin_deduct_balance"])
def handle_admin_balance_operation(message):
    user_id = message.from_user.id
    state = user_states[user_id]["state"]
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(user_id, "❌ " + style_text("Invalid format. Use: user_id amount"))
            return
            
        target_user_id = int(parts[0])
        amount = float(parts[1])
        
        # Initialize target user
        init_user(target_user_id)
        
        if state == "admin_add_balance":
            update_user_balance(target_user_id, amount)
            action_text = "added to"
            notification_text = f"💰 ₹{amount} has been added to your balance by admin."
        else:
            update_user_balance(target_user_id, -amount)
            action_text = "deducted from"
            notification_text = f"💰 ₹{amount} has been deducted from your balance by admin."
        
        current_balance = get_user_balance(target_user_id)
        
        # Notify admin
        bot.send_message(
            user_id,
            style_text(f"✅ Balance {action_text}!\n👤 User: {target_user_id}\n💳 Amount: ₹{amount}\n💰 New Balance: ₹{current_balance}")
        )
        
        # Notify user
        try:
            bot.send_message(target_user_id, "ℹ️ " + notification_text)
        except:
            pass
        
    except ValueError:
        bot.send_message(user_id, "❌ " + style_text("Invalid format. Use numbers for user_id and amount"))
    except Exception as e:
        print(f"Admin balance operation error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error processing balance operation."))
    
    user_states[user_id] = None

def admin_user_control(call):
    try:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🚫 " + style_text("Ban User"), callback_data="admin_ban_user"))
        keyboard.add(InlineKeyboardButton("✅ " + style_text("Unban User"), callback_data="admin_unban_user"))
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="back_to_admin"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="👥 " + style_text("User Control\n\nManage users:"),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin user control error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error accessing user control."))

def start_admin_ban_user(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="🚫 " + style_text("Ban User\n\nPlease send user ID to ban:"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin_users")
            ),
            parse_mode='HTML'
        )
        
        user_states[call.from_user.id] = {"state": "admin_ban_user"}
        
    except Exception as e:
        print(f"Start admin ban user error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting ban user."))

def start_admin_unban_user(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="✅ " + style_text("Unban User\n\nPlease send user ID to unban:"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin_users")
            ),
            parse_mode='HTML'
        )
        
        user_states[call.from_user.id] = {"state": "admin_unban_user"}
        
    except Exception as e:
        print(f"Start admin unban user error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting unban user."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") in ["admin_ban_user", "admin_unban_user"])
def handle_admin_user_operation(message):
    user_id = message.from_user.id
    state = user_states[user_id]["state"]
    
    try:
        target_user_id = int(message.text)
        
        # Initialize target user
        init_user(target_user_id)
        
        if state == "admin_ban_user":
            ban_user(target_user_id)
            action_text = "banned"
            notification_text = "🚫 You have been banned from using this bot."
        else:
            unban_user(target_user_id)
            action_text = "unbanned"
            notification_text = "✅ You have been unbanned and can now use the bot."
        
        # Notify admin
        bot.send_message(
            user_id,
            style_text(f"✅ User {action_text}!\n👤 User ID: {target_user_id}")
        )
        
        # Notify user
        try:
            bot.send_message(target_user_id, "ℹ️ " + notification_text)
        except:
            pass
        
    except ValueError:
        bot.send_message(user_id, "❌ " + style_text("Invalid user ID. Please enter a valid number."))
    except Exception as e:
        print(f"Admin user operation error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error processing user operation."))
    
    user_states[user_id] = None

# FIXED: Complete Price Management System
def admin_manage_prices_menu(call):
    try:
        services_data = get_services()
        keyboard = InlineKeyboardMarkup()
        
        for category_key, category_data in services_data.items():
            if category_key != "_id":
                for service_id, service in category_data["services"].items():
                    keyboard.add(InlineKeyboardButton(
                        f"{service['name']} - ₹{service['rate']}",
                        callback_data=f"edit_service_{category_key}_{service_id}"
                    ))
        
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="back_to_admin"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="📊 " + style_text("Manage Prices\n\nSelect a service to edit:"),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin manage prices error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error accessing price management."))

def start_edit_service(call, category, service_id):
    try:
        services_data = get_services()
        service = services_data[category]["services"][service_id]
        
        caption = style_text(f"""
📊 Edit Service

📦 Service: {service['name']}
💰 Current Rate: ₹{service['rate']}/{service['unit']}
🆔 API ID: {service['api_id']}
📊 Min: {service['min']}
📈 Max: {service['max']}

Select what you want to change:
        """)
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("💰 " + style_text("Change Rate"), callback_data=f"change_rate_{category}_{service_id}"))
        keyboard.add(InlineKeyboardButton("🆔 " + style_text("Change API ID"), callback_data=f"change_api_{category}_{service_id}"))
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin_prices"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Start edit service error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error editing service."))

def start_change_rate(call, category, service_id):
    try:
        services_data = get_services()
        service = services_data[category]["services"][service_id]
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"💰 Change Rate for {service['name']}\n\nCurrent Rate: ₹{service['rate']}/{service['unit']}\n\nPlease send the new rate:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data=f"edit_service_{category}_{service_id}")
            ),
            parse_mode='HTML'
        )
        
        user_states[call.from_user.id] = {
            "state": "admin_change_rate",
            "category": category,
            "service_id": service_id
        }
        
    except Exception as e:
        print(f"Start change rate error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting rate change."))

def start_change_api(call, category, service_id):
    try:
        services_data = get_services()
        service = services_data[category]["services"][service_id]
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"🆔 Change API ID for {service['name']}\n\nCurrent API ID: {service['api_id']}\n\nPlease send the new API ID:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data=f"edit_service_{category}_{service_id}")
            ),
            parse_mode='HTML'
        )
        
        user_states[call.from_user.id] = {
            "state": "admin_change_api",
            "category": category,
            "service_id": service_id
        }
        
    except Exception as e:
        print(f"Start change api error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting API ID change."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") in ["admin_change_rate", "admin_change_api"])
def handle_admin_service_change(message):
    user_id = message.from_user.id
    state_data = user_states[user_id]
    state = state_data["state"]
    category = state_data["category"]
    service_id = state_data["service_id"]
    
    try:
        services_data = get_services()
        service = services_data[category]["services"][service_id]
        
        if state == "admin_change_rate":
            new_rate = float(message.text)
            # Update service rate
            service["rate"] = new_rate
            update_service(category, service_id, service)
            
            bot.send_message(
                user_id,
                style_text(f"✅ Rate updated successfully!\n\n📦 Service: {service['name']}\n💰 New Rate: ₹{new_rate}/{service['unit']}")
            )
            
        elif state == "admin_change_api":
            new_api_id = int(message.text)
            # Update service API ID
            service["api_id"] = new_api_id
            update_service(category, service_id, service)
            
            bot.send_message(
                user_id,
                style_text(f"✅ API ID updated successfully!\n\n📦 Service: {service['name']}\n🆔 New API ID: {new_api_id}")
            )
        
    except ValueError:
        bot.send_message(user_id, "❌ " + style_text("Please enter a valid number."))
    except Exception as e:
        print(f"Admin service change error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error updating service."))
    
    user_states[user_id] = None

def admin_broadcast(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="📢 " + style_text("Broadcast\n\nPlease send your broadcast message:"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="back_to_admin")
            ),
            parse_mode='HTML'
        )
        
        user_states[call.from_user.id] = {"state": "admin_broadcast"}
        
    except Exception as e:
        print(f"Admin broadcast error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error accessing broadcast."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == "admin_broadcast")
def handle_admin_broadcast(message):
    user_id = message.from_user.id
    broadcast_text = message.text
    
    try:
        sent = 0
        failed = 0
        
        all_users = get_all_users()
        
        for user in all_users:
            try:
                bot.send_message(user["user_id"], "📢 " + style_text(f"Broadcast:\n\n{broadcast_text}"))
                sent += 1
            except:
                failed += 1
                
        bot.send_message(
            user_id,
            style_text(f"✅ Broadcast completed!\n📤 Sent: {sent}\n❌ Failed: {failed}")
        )
        
    except Exception as e:
        print(f"Broadcast error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error broadcasting."))
    
    user_states[user_id] = None

def admin_bot_control(call):
    try:
        status = "🟢 ENABLED" if bot_enabled else "🔴 DISABLED"
        keyboard = InlineKeyboardMarkup()
        
        if bot_enabled:
            keyboard.add(InlineKeyboardButton("🔴 " + style_text("Disable Bot"), callback_data="disable_bot"))
        else:
            keyboard.add(InlineKeyboardButton("🟢 " + style_text("Enable Bot"), callback_data="enable_bot"))
            
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="back_to_admin"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="⚙️ " + style_text(f"Bot Control\n\nCurrent Status: {status}"),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin bot control error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error accessing bot control."))

def admin_stats(call):
    try:
        total_users = get_total_users()
        total_orders = get_total_orders()
        total_deposits = get_total_deposits()
        total_spent = get_total_spent()
        
        # Count banned users
        banned_count = users_collection.count_documents({"banned": True})
        
        caption = style_text(f"""
📈 Admin Stats

👥 Total Users: {total_users}
📦 Total Orders: {total_orders}
💳 Total Deposits: ₹{total_deposits:.2f}
🛒 Total Spent: ₹{total_spent:.2f}
🚫 Banned Users: {banned_count}
🤖 Bot Status: {'🟢 Online' if bot_enabled else '🔴 Offline'}
        """)
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="back_to_admin")
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin stats error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error accessing admin stats."))

# Auto Refund System
def auto_refund_system():
    while True:
        try:
            if not bot_enabled:
                time.sleep(30)
                continue
                
            # Get orders that need to be checked for refund (older than 30 seconds and not checked)
            orders_to_check = get_orders_for_refund_check()
            
            for order in orders_to_check:
                try:
                    # Check order status via SMM API
                    status_result = check_order_status(order["order_id"])
                    
                    if status_result["success"]:
                        status = status_result["status"]
                        
                        # Update order status in database
                        update_order_status(order["order_id"], status)
                        
                        # If order is cancelled, process refund
                        if status.lower() in ["cancelled", "canceled", "refunded"] and not order.get("refunded", False):
                            # Refund the amount to user
                            user_id = order["user_id"]
                            refund_amount = order["cost"]
                            
                            # Update user balance
                            update_user_balance(user_id, refund_amount)
                            
                            # Mark order as refunded
                            mark_order_refunded(order["order_id"])
                            
                            # Notify user
                            try:
                                current_balance = get_user_balance(user_id)
                                bot.send_message(
                                    user_id,
                                    style_text(f"💰 Auto Refund Processed!\n\n🆔 Order ID: {order['order_id']}\n💳 Refund Amount: ₹{refund_amount:.2f}\n💰 New Balance: ₹{current_balance:.2f}\n\n❓ Reason: Order was cancelled by the service provider.")
                                )
                            except:
                                pass
                            
                            # Notify admin
                            try:
                                bot.send_message(
                                    ADMIN_ID,
                                    style_text(f"🔄 Auto Refund Processed\n\n👤 User: {user_id}\n🆔 Order ID: {order['order_id']}\n💳 Amount: ₹{refund_amount:.2f}")
                                )
                            except:
                                pass
                        else:
                            # Mark as checked but not refunded
                            mark_order_checked(order["order_id"])
                    else:
                        # Mark as checked even if there was an error
                        mark_order_checked(order["order_id"])
                        
                except Exception as e:
                    print(f"Error processing auto refund for order {order['order_id']}: {e}")
                    # Mark as checked to avoid repeated errors
                    mark_order_checked(order["order_id"])
            
            # Sleep for 30 seconds before next check
            time.sleep(30)
            
        except Exception as e:
            print(f"Auto refund system error: {e}")
            time.sleep(30)

# Initialize services on startup
init_services()

# Start auto refund system in background thread
refund_thread = threading.Thread(target=auto_refund_system, daemon=True)
refund_thread.start()

# Default handler for unknown commands/messages
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    try:
        # If user is in a state, don't show main menu
        if message.from_user.id in user_states and user_states[message.from_user.id] is not None:
            return
            
        # Show main menu for unknown commands
        start_command(message)
    except Exception as e:
        print(f"Unknown message handler error: {e}")
        bot.send_message(message.chat.id, "❌ " + style_text("An error occurred. Please try /start"))

# Start polling with error handling
if __name__ == "__main__":
    print("🤖 Bot is running...")
    print("🔄 Auto refund system started...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            print("🔄 Restarting bot in 10 seconds...")
            time.sleep(10)
