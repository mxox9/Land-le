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
CHANNEL_ID = -1003036132948
PROOF_CHANNEL = "@prooflelo1"
SUPPORT_LINK = "https://wa.me/+639941532149"
CHANNEL_USERNAME = "@prooflelo1"  # Channel for force join

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
refund_tracking_collection = db.refund_tracking

# Image URLs
WELCOME_IMAGE = "https://t.me/prooflelo1/372?single"
SERVICE_IMAGE = "https://t.me/prooflelo1/138?single"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/136?single"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/137?single"
HISTORY_IMAGE = "https://t.me/prooflelo1/139?single"
HOW_TO_USE_IMAGE = "https://t.me/prooflelo1/487?single"
ADMIN_IMAGE = "https://t.me/prooflelo1/140?single"
TRACK_IMAGE = "https://t.me/prooflelo1/139?single"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Storage (using MongoDB now)
user_states = {}
bot_enabled = True

# Price storage (local storage for real-time updates)
service_prices = {}
service_api_ids = {}

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

# Services and Categories (with styled text and emojis)
def get_services():
    return {
        "instagram": {
            "name": "📸 " + style_text("Instagram"),
            "services": {
                1: {"name": "❤️ " + style_text("Instagram Likes"), "rate": service_prices.get(1, 50), "min": 100, "max": 100000, "unit": 1000, "api_id": service_api_ids.get(1, 1)},
                2: {"name": "👀 " + style_text("Instagram Views"), "rate": service_prices.get(2, 1), "min": 100, "max": 100000, "unit": 1000, "api_id": service_api_ids.get(2, 13685)},
                3: {"name": "👥 " + style_text("Instagram Followers"), "rate": service_prices.get(3, 100), "min": 50, "max": 50000, "unit": 1000, "api_id": service_api_ids.get(3, 3)}
            }
        },
        "facebook": {
            "name": "📘 " + style_text("Facebook"), 
            "services": {
                4: {"name": "👍 " + style_text("Facebook Likes"), "rate": service_prices.get(4, 40), "min": 100, "max": 100000, "unit": 1000, "api_id": service_api_ids.get(4, 4)},
                5: {"name": "👀 " + style_text("Facebook Views"), "rate": service_prices.get(5, 35), "min": 100, "max": 100000, "unit": 1000, "api_id": service_api_ids.get(5, 5)},
                6: {"name": "👥 " + style_text("Facebook Followers"), "rate": service_prices.get(6, 80), "min": 50, "max": 50000, "unit": 1000, "api_id": service_api_ids.get(6, 6)}
            }
        },
        "youtube": {
            "name": "📺 " + style_text("YouTube"),
            "services": {
                7: {"name": "👍 " + style_text("YouTube Likes"), "rate": service_prices.get(7, 60), "min": 100, "max": 100000, "unit": 1000, "api_id": service_api_ids.get(7, 7)},
                8: {"name": "👀 " + style_text("YouTube Views"), "rate": service_prices.get(8, 45), "min": 100, "max": 100000, "unit": 1000, "api_id": service_api_ids.get(8, 8)},
                9: {"name": "🔔 " + style_text("YouTube Subscribers"), "rate": service_prices.get(9, 150), "min": 50, "max": 25000, "unit": 1000, "api_id": service_api_ids.get(9, 9)}
            }
        },
        "telegram": {
            "name": "✈️ " + style_text("Telegram"),
            "services": {
                10: {"name": "👥 " + style_text("Telegram Members"), "rate": service_prices.get(10, 200), "min": 50, "max": 10000, "unit": 1000, "api_id": service_api_ids.get(10, 10)},
                11: {"name": "❤️ " + style_text("Telegram Post Likes"), "rate": service_prices.get(11, 80), "min": 100, "max": 50000, "unit": 1000, "api_id": service_api_ids.get(11, 11)},
                12: {"name": "👀 " + style_text("Telegram Post Views"), "rate": service_prices.get(12, 50), "min": 100, "max": 50000, "unit": 1000, "api_id": service_api_ids.get(12, 12)}
            }
        }
    }

# Initialize service prices and API IDs
def initialize_service_prices():
    global service_prices, service_api_ids
    # Set default prices
    default_prices = {
        1: 50, 2: 1, 3: 100, 4: 40, 5: 35, 6: 80, 7: 60, 8: 45, 9: 150, 10: 200, 11: 80, 12: 50
    }
    service_prices = default_prices.copy()
    
    # Set default API IDs
    default_api_ids = {
        1: 1, 2: 13685, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11, 12: 12
    }
    service_api_ids = default_api_ids.copy()

# Check if user is member of channel
def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return True  # Return True if there's an error to avoid blocking users

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
        InlineKeyboardButton("📚 " + style_text("Guide"), callback_data="guide"),
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
    keyboard.add(InlineKeyboardButton("📸 " + style_text("Instagram"), callback_data="category_instagram"))
    keyboard.add(InlineKeyboardButton("📘 " + style_text("Facebook"), callback_data="category_facebook"))
    keyboard.add(InlineKeyboardButton("📺 " + style_text("YouTube"), callback_data="category_youtube"))
    keyboard.add(InlineKeyboardButton("✈️ " + style_text("Telegram"), callback_data="category_telegram"))
    keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land"))
    return keyboard

# Admin Keyboard with emojis
def admin_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💰 " + style_text("Balance Control"), callback_data="admin_balance"))
    keyboard.add(InlineKeyboardButton("📊 " + style_text("Manage Prices"), callback_data="admin_prices"))
    keyboard.add(InlineKeyboardButton("🆔 " + style_text("Manage Service IDs"), callback_data="admin_service_ids"))
    keyboard.add(InlineKeyboardButton("📢 " + style_text("Broadcast"), callback_data="admin_broadcast"))
    keyboard.add(InlineKeyboardButton("👥 " + style_text("User Control"), callback_data="admin_users"))
    keyboard.add(InlineKeyboardButton("⚙️ " + style_text("Bot Control"), callback_data="admin_control"))
    keyboard.add(InlineKeyboardButton("📈 " + style_text("Stats"), callback_data="admin_stats"))
    keyboard.add(InlineKeyboardButton("🔙 " + style_text("Main Menu"), callback_data="land"))
    return keyboard

# Start Command with channel join check
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        user_id = message.from_user.id
        
        if not bot_enabled and user_id != ADMIN_ID:
            bot.send_message(message.chat.id, "🔧 " + style_text("Bot is currently under maintenance. Please try again later."))
            return
            
        if is_user_banned(user_id):
            bot.send_message(message.chat.id, "🚫 " + style_text("You are banned from using this bot."))
            return
        
        # Check if user is member of channel
        if not is_member(user_id) and user_id != ADMIN_ID:
            caption = "👋 " + style_text("""
Welcome to Next Grow Bot

📢 Please join our channel to use this bot:

1. Join our channel: {channel}
2. Then click /start again

We provide the best SMM services with 24/7 support!
            """).format(channel=CHANNEL_USERNAME)
            
            bot.send_photo(
                chat_id=message.chat.id,
                photo=HOW_TO_USE_IMAGE,
                caption=caption,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
                    InlineKeyboardButton("🔄 Check Join", callback_data="check_join")
                ),
                parse_mode='HTML'
            )
            return
            
        init_user(user_id)
        
        caption = "👋 " + style_text("""
Welcome to Next Grow Bot

🎯 High Quality Service 
🛡️ 24/7 Support &
👮 Refund Available!

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
    try:
        user_id = call.from_user.id
        
        if not bot_enabled and user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "🔧 " + style_text("Bot is currently under maintenance."))
            return
            
        if is_user_banned(user_id):
            bot.answer_callback_query(call.id, "🚫 " + style_text("You are banned from using this bot."))
            return
        
        # Check channel membership for non-admin users
        if not is_member(user_id) and user_id != ADMIN_ID and call.data != "check_join":
            bot.answer_callback_query(call.id, "❌ " + style_text("Please join our channel first!"))
            return
            
        init_user(user_id)
        
        if call.data == "land":
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            start_command(call.message)
            
        elif call.data == "admin":
            admin_command(call.message)
            
        elif call.data == "check_join":
            if is_member(user_id) or user_id == ADMIN_ID:
                bot.answer_callback_query(call.id, "✅ " + style_text("Thanks for joining! Now you can use the bot."))
                start_command(call.message)
            else:
                bot.answer_callback_query(call.id, "❌ " + style_text("You haven't joined the channel yet!"))
            
        elif call.data == "deposit":
            show_deposit(call)
            
        elif call.data == "order":
            show_categories(call)
            
        elif call.data == "orders":
            show_orders(call)
            
        elif call.data == "track":
            start_track_order(call)
            
        elif call.data == "guide":
            show_guide(call)
            
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
            admin_manage_prices(call)
            
        elif call.data == "admin_service_ids":
            admin_manage_service_ids(call)
            
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
            
        elif call.data == "enable_bot":
            enable_bot(call)
            
        elif call.data == "disable_bot":
            disable_bot(call)
            
        elif call.data.startswith("refill_"):
            order_id = call.data.split("_")[1]
            handle_refill(call, order_id)
            
        elif call.data.startswith("set_price_"):
            service_id = int(call.data.split("_")[2])
            start_set_price(call, service_id)
            
        elif call.data.startswith("set_service_id_"):
            service_id = int(call.data.split("_")[3])
            start_set_service_id(call, service_id)
            
    except Exception as e:
        print(f"Callback handler error: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ " + style_text("An error occurred. Please try again."))
        except:
            pass

# Guide (previously How to Use)
def show_guide(call):
    try:
        video_url = "https://t.me/prooflelo1/26"
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaVideo(
                media=video_url,
                caption=style_text("📹 Guide\n\nWatch this video to learn how to use our bot:"),
                parse_mode='HTML'
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land")
            )
        )
    except Exception as e:
        print(f"Guide error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error showing guide. Please try again."))

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
        services = get_services()
        if category not in services:
            bot.answer_callback_query(call.id, "❌ " + style_text("Category not found"))
            return
            
        category_data = services[category]
        keyboard = InlineKeyboardMarkup()
        
        for service_id, service in category_data["services"].items():
            keyboard.add(InlineKeyboardButton(
                service['name'],
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
        services = get_services()
        service = None
        category_name = None
        for cat_name, cat_data in services.items():
            if service_id in cat_data["services"]:
                service = cat_data["services"][service_id]
                category_name = cat_data["name"]
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
        
        # Find the category key for back button
        category_key = None
        for cat_key, cat_data in services.items():
            if service_id in cat_data["services"]:
                category_key = cat_key
                break
        
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
            
            # Confirm to user with Main Menu button
            bot.send_message(
                user_id,
                style_text(f"✅ Order Placed Successfully!\n\n📦 Order ID: {order_id}\n💳 Amount: ₹{cost:.2f}\n💰 Balance: ₹{updated_balance:.2f}"),
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🏠 " + style_text("Main Menu"), callback_data="land")
                )
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

# Track Order Feature - NEW FIXED VERSION
def start_track_order(call):
    try:
        user_id = call.from_user.id
        
        # Create keyboard with cancel button
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton("❌ Cancel"))
        
        bot.send_message(
            chat_id=call.message.chat.id,
            text="🔍 Enter Order ID For Check Order Status",
            reply_markup=keyboard
        )
        
        user_states[user_id] = {"state": "waiting_track_order_id"}
        
    except Exception as e:
        print(f"Start track order error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting track order. Please try again."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == "waiting_track_order_id")
def handle_track_order_id(message):
    user_id = message.from_user.id
    
    # Check if user wants to cancel
    if message.text == "❌ Cancel":
        bot.send_message(user_id, "❌ Process Cancelled")
        user_states[user_id] = None
        start_command(message)
        return
    
    order_id = message.text.strip()
    
    try:
        # Check order status via SMM API
        url = f"https://smm-jupiter.com/api/v2?key={SMM_API_KEY}&action=status&order={order_id}"
        response = requests.get(url, timeout=30)
        content = response.json()
        
        status = content.get('status')
        
        if status:
            count = content.get('start_count', 'N/A')
            remain = content.get('remains', 'N/A')
            rem = content.get('refill', 'N/A')
            
            # Try to get order details from database if exists
            order = get_order_by_id(order_id)
            if order:
                service_name = order['service']
                cost = order['cost']
            else:
                service_name = "Unknown"
                cost = "Unknown"
            
            # Prepare response
            response_text = style_text(f"""
🔍 Order Status Extracted

✅ Order Status: {status}
📊 Start Count: {count}
🎯 Remains: {remain}
💎 Refill: {rem}
📦 Service: {service_name}
💳 Cost: ₹{cost if cost != 'Unknown' else 'Unknown'}
            """)
            
            keyboard = InlineKeyboardMarkup()
            
            # Check if refill is available
            if str(rem).lower() in ['true', '1', 'yes']:
                response_text += style_text("\n\n🔄 Refill is available for this order!")
                keyboard.add(InlineKeyboardButton("🔄 " + style_text("Refill Order"), callback_data=f"refill_{order_id}"))
            else:
                response_text += style_text("\n\n❌ Refill is not available for this order.")
            
            keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="land"))
            
            # Remove the custom keyboard
            remove_keyboard = telebot.types.ReplyKeyboardRemove()
            
            bot.send_message(
                user_id,
                response_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            bot.send_message(
                user_id,
                "🚫 Order ID is not valid."
            )
            
    except Exception as e:
        print(f"Track order error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error tracking order. Please try again."))
    
    user_states[user_id] = None

def handle_refill(call, order_id):
    try:
        user_id = call.from_user.id
        
        # Process refill via SMM API
        refill_result = process_refill(order_id)
        
        if refill_result["success"]:
            bot.answer_callback_query(call.id, "✅ " + style_text("Refill request submitted successfully!"))
            
            # Update message
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=style_text(f"✅ Refill Request Submitted!\n\n🆔 Order ID: {order_id}\n\n🔄 Your order is being refilled."),
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

# Orders History
def show_orders(call):
    try:
        user_id = call.from_user.id
        user_orders = get_user_orders(user_id, 5)  # Last 5 orders
        
        if not user_orders:
            caption = "📦 " + style_text("No orders found for your account.")
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

def show_account(call):
    try:
        user_id = call.from_user.id
        user = init_user(user_id)
        
        caption = style_text(f"""
👤 Account Information

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

# Admin Functions with inline buttons - FIXED BACK BUTTONS
def admin_balance_control(call):
    try:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("➕ " + style_text("Add Balance"), callback_data="admin_add_balance"))
        keyboard.add(InlineKeyboardButton("➖ " + style_text("Deduct Balance"), callback_data="admin_deduct_balance"))
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin"))
        
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
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin"))
        
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

def admin_manage_prices(call):
    try:
        services = get_services()
        keyboard = InlineKeyboardMarkup()
        
        for category_name, category_data in services.items():
            for service_id, service in category_data["services"].items():
                keyboard.add(InlineKeyboardButton(
                    f"{service['name']} - ₹{service['rate']}",
                    callback_data=f"set_price_{service_id}"
                ))
        
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="📊 " + style_text("Manage Prices\n\nSelect a service to update its price:"),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin manage prices error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error accessing price management."))

# NEW: Service ID Management
def admin_manage_service_ids(call):
    try:
        services = get_services()
        keyboard = InlineKeyboardMarkup()
        
        for category_name, category_data in services.items():
            for service_id, service in category_data["services"].items():
                keyboard.add(InlineKeyboardButton(
                    f"{service['name']} - ID: {service['api_id']}",
                    callback_data=f"set_service_id_{service_id}"
                ))
        
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="🆔 " + style_text("Manage Service IDs\n\nSelect a service to update its API ID:"),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin manage service IDs error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error accessing service ID management."))

def start_set_price(call, service_id):
    try:
        services = get_services()
        service_name = ""
        for category_data in services.values():
            if service_id in category_data["services"]:
                service_name = category_data["services"][service_id]["name"]
                break
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"💰 " + style_text(f"Set Price for {service_name}\n\nPlease enter the new price:"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin_prices")
            ),
            parse_mode='HTML'
        )
        
        user_states[call.from_user.id] = {
            "state": "admin_set_price",
            "service_id": service_id,
            "service_name": service_name
        }
        
    except Exception as e:
        print(f"Start set price error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting price setting."))

# NEW: Start set service ID
def start_set_service_id(call, service_id):
    try:
        services = get_services()
        service_name = ""
        current_api_id = ""
        for category_data in services.values():
            if service_id in category_data["services"]:
                service_name = category_data["services"][service_id]["name"]
                current_api_id = category_data["services"][service_id]["api_id"]
                break
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"🆔 " + style_text(f"Set API ID for {service_name}\n\nCurrent API ID: {current_api_id}\n\nPlease enter the new API ID:"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin_service_ids")
            ),
            parse_mode='HTML'
        )
        
        user_states[call.from_user.id] = {
            "state": "admin_set_service_id",
            "service_id": service_id,
            "service_name": service_name
        }
        
    except Exception as e:
        print(f"Start set service ID error: {e}")
        bot.answer_callback_query(call.id, "❌ " + style_text("Error starting service ID setting."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == "admin_set_price")
def handle_admin_set_price(message):
    user_id = message.from_user.id
    
    try:
        new_price = float(message.text)
        service_id = user_states[user_id]["service_id"]
        service_name = user_states[user_id]["service_name"]
        
        # Update price in local storage
        service_prices[service_id] = new_price
        
        bot.send_message(
            user_id,
            style_text(f"✅ Price updated!\n\n📦 Service: {service_name}\n💰 New Price: ₹{new_price}")
        )
        
    except ValueError:
        bot.send_message(user_id, "❌ " + style_text("Please enter a valid number for price."))
    except Exception as e:
        print(f"Admin set price error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error setting price."))
    
    user_states[user_id] = None

# NEW: Handle set service ID
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == "admin_set_service_id")
def handle_admin_set_service_id(message):
    user_id = message.from_user.id
    
    try:
        new_api_id = int(message.text)
        service_id = user_states[user_id]["service_id"]
        service_name = user_states[user_id]["service_name"]
        
        # Update API ID in local storage
        service_api_ids[service_id] = new_api_id
        
        bot.send_message(
            user_id,
            style_text(f"✅ API ID updated!\n\n📦 Service: {service_name}\n🆔 New API ID: {new_api_id}")
        )
        
    except ValueError:
        bot.send_message(user_id, "❌ " + style_text("Please enter a valid number for API ID."))
    except Exception as e:
        print(f"Admin set service ID error: {e}")
        bot.send_message(user_id, "❌ " + style_text("Error setting API ID."))
    
    user_states[user_id] = None

def admin_broadcast(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="📢 " + style_text("Broadcast\n\nPlease send your broadcast message:"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin")
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
            
        keyboard.add(InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin"))
        
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

def enable_bot(call):
    global bot_enabled
    bot_enabled = True
    bot.answer_callback_query(call.id, "✅ " + style_text("Bot enabled!"))
    admin_bot_control(call)

def disable_bot(call):
    global bot_enabled
    bot_enabled = False
    bot.answer_callback_query(call.id, "✅ " + style_text("Bot disabled!"))
    admin_bot_control(call)

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
                InlineKeyboardButton("🔙 " + style_text("Back"), callback_data="admin")
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

def check_order_status(order_id):
    try:
        # Check order status via SMM API
        url = f"https://smm-jupiter.com/api/v2?key={SMM_API_KEY}&action=status&order={order_id}"
        response = requests.get(url, timeout=30)
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
            
        # Check if user is member of channel
        if not is_member(message.from_user.id) and message.from_user.id != ADMIN_ID:
            caption = "👋 " + style_text("""
Welcome to Next Grow Bot

📢 Please join our channel to use this bot:

1. Join our channel: {channel}
2. Then click /start again

We provide the best SMM services with 24/7 support!
            """).format(channel=CHANNEL_USERNAME)
            
            bot.send_photo(
                chat_id=message.chat.id,
                photo=HOW_TO_USE_IMAGE,
                caption=caption,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
                    InlineKeyboardButton("🔄 Check Join", callback_data="check_join")
                ),
                parse_mode='HTML'
            )
            return
            
        # Show main menu for unknown commands
        start_command(message)
    except Exception as e:
        print(f"Unknown message handler error: {e}")
        bot.send_message(message.chat.id, "❌ " + style_text("An error occurred. Please try /start"))

# Initialize service prices and API IDs
initialize_service_prices()

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