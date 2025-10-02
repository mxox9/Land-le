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
    settings_collection = db.settings
    # Test connection
    client.admin.command('ismaster')
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
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
        "📱 Instagram Likes": {"id": 101, "price": 30, "min": 100, "max": 10000, "unit": 1000},
        "👤 Instagram Views": {"id": 13685, "price": 50, "min": 100, "max": 50000, "unit": 1000},
        "👥 Instagram Followers": {"id": 103, "price": 80, "min": 100, "max": 10000, "unit": 1000}
    },
    "Facebook": {
        "👨 Facebook Likes": {"id": 201, "price": 40, "min": 100, "max": 20000, "unit": 1000},
        "👤 Facebook Views": {"id": 202, "price": 60, "min": 100, "max": 50000, "unit": 1000},
        "👦 Facebook Followers": {"id": 203, "price": 90, "min": 100, "max": 15000, "unit": 1000}
    },
    "YouTube": {
        "👨 YouTube Likes": {"id": 301, "price": 35, "min": 100, "max": 50000, "unit": 1000},
        "👤 YouTube Views": {"id": 302, "price": 45, "min": 100, "max": 100000, "unit": 1000},
        "🔔 YouTube Subscribers": {"id": 303, "price": 120, "min": 100, "max": 10000, "unit": 1000}
    },
    "Telegram": {
        "👦 Telegram Members": {"id": 401, "price": 25, "min": 100, "max": 50000, "unit": 1000},
        "👨 Telegram Post Likes": {"id": 402, "price": 20, "min": 100, "max": 100000, "unit": 1000},
        "👤 Telegram Post Views": {"id": 403, "price": 15, "min": 100, "max": 100000, "unit": 1000}
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
    """Place order using SMM API"""
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
    """Verify payment using AutoDep API"""
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
    """Generate QR code for UPI payment"""
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

# Keyboard Builders
def main_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
        InlineKeyboardButton("🛒 Order", callback_data="order"),
        InlineKeyboardButton("📋 Orders", callback_data="orders"),
        InlineKeyboardButton("👥 Refer", callback_data="refer"),
        InlineKeyboardButton("👤 Account", callback_data="account"),
        InlineKeyboardButton("📊 Stats", callback_data="stats"),
        InlineKeyboardButton("ℹ️ Support", callback_data="support")
    ]
    markup.add(*buttons)
    
    return markup

def categories_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for category in SERVICES.keys():
        emoji = "📱" if category == "Instagram" else "👨" if category == "Facebook" else "📺" if category == "YouTube" else "📞"
        buttons.append(InlineKeyboardButton(f"{emoji} {category}", callback_data=f"cat_{category}"))
    
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    return markup

def services_keyboard(category):
    markup = InlineKeyboardMarkup()
    for service_name in SERVICES[category].keys():
        # Create safe callback data by replacing spaces with underscores
        callback_data = f"serv_{category}_{service_name.replace(' ', '_')}"
        markup.add(InlineKeyboardButton(service_name, callback_data=callback_data))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="order"))
    return markup

def back_to_main_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
    return markup

def channel_join_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    markup.add(InlineKeyboardButton("🔄 Check Join", callback_data="check_join"))
    return markup

def deposit_confirmation_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ I Have Paid", callback_data="check_txn"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    return markup

def support_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📞 Contact Us", url=SUPPORT_LINK))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    return markup

def order_confirmation_keyboard(cost):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Confirm Order", callback_data=f"confirm_order_{cost}"),
        InlineKeyboardButton("❌ Cancel", callback_data="main_menu")
    )
    return markup

# Admin Keyboards
def admin_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💰 Balance Control", callback_data="admin_balance"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        InlineKeyboardButton("👤 User Control", callback_data="admin_users"),
        InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_settings"),
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
    ]
    markup.add(*buttons)
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
            bot.reply_to(message, "❌ You are banned from using this bot.")
            return
        
        # Check channel membership
        if not check_channel_membership(user_id):
            welcome_text = f"""
✨ Welcome {message.from_user.first_name}!

📢 Please join our channel to use the bot:

{CHANNEL_ID}

After joining, click the check button below.
            """
            bot.send_photo(user_id, WELCOME_IMAGE, welcome_text, reply_markup=channel_join_keyboard())
            return
        
        welcome_text = f"""
✨ Welcome To SMM Bot ✨

🚀 Buy Social Media Services at Cheapest Rates!

📱 Instagram, Facebook, YouTube & Telegram Services
💸 High Quality & Fast Delivery
⚡ Secure Payments & 24/7 Support

💳 Start by depositing funds to place orders!
        """
        
        bot.send_photo(user_id, WELCOME_IMAGE, welcome_text, reply_markup=main_menu_keyboard())
        
    except Exception as e:
        print(f"Start command error: {e}")
        bot.reply_to(message, "❌ An error occurred. Please try again.")

@bot.message_handler(commands=['admin'])
def admin_command(message):
    try:
        user_id = message.from_user.id
        if is_admin(user_id):
            admin_text = """
👑 Admin Panel

🎛️ Manage your SMM bot from admin dashboard.

Select an option below:
            """
            bot.send_photo(user_id, ADMIN_IMAGE, admin_text, reply_markup=admin_keyboard())
        else:
            bot.send_message(user_id, "❌ Access denied. You are not an admin.")
    except Exception as e:
        print(f"Admin command error: {e}")
        bot.reply_to(message, "❌ An error occurred.")

@bot.message_handler(commands=['balance'])
def balance_command(message):
    try:
        user_id = message.from_user.id
        user = get_user(user_id)
        
        balance_text = f"""
💰 Account Balance

💳 Current Balance: ₹{user['balance']:.2f}
📥 Total Deposited: ₹{user.get('total_deposits', 0):.2f}
📤 Total Spent: ₹{user.get('total_spent', 0):.2f}

💳 Deposit more funds to place orders!
        """
        
        bot.send_photo(user_id, ACCOUNT_IMAGE, balance_text, reply_markup=back_to_main_button())
        
    except Exception as e:
        print(f"Balance command error: {e}")
        bot.reply_to(message, "❌ An error occurred.")

# Callback query handler - MAIN HANDLER
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    try:
        # Check if user is banned
        user = get_user(user_id)
        if user.get('banned'):
            bot.answer_callback_query(call.id, "❌ You are banned from using this bot.", show_alert=True)
            return
        
        # Main menu and navigation
        if call.data == "main_menu":
            show_main_menu(call)
        
        elif call.data == "deposit":
            show_deposit_menu(call)
        
        elif call.data == "order":
            show_categories(call)
        
        elif call.data == "orders":
            show_orders(call)
        
        elif call.data == "refer":
            show_refer(call)
        
        elif call.data == "account":
            show_account(call)
        
        elif call.data == "stats":
            show_stats(call)
        
        elif call.data == "support":
            show_support(call)
        
        elif call.data == "check_join":
            check_channel_join(call)
        
        # Category and service selection
        elif call.data.startswith("cat_"):
            category = call.data[4:]
            show_services(call, category)
        
        elif call.data.startswith("serv_"):
            parts = call.data.split("_")
            if len(parts) >= 3:
                category = parts[1]
                service_name = "_".join(parts[2:])
                start_order_flow(call, category, service_name)
        
        # Deposit and payment
        elif call.data == "check_txn":
            check_transaction(call)
        
        # Order confirmation
        elif call.data.startswith("confirm_order_"):
            confirm_order_processing(call)
        
        # Admin panel
        elif call.data == "admin_panel":
            if is_admin(user_id):
                show_admin_panel(call)
            else:
                bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
        
        # Admin sub-menus
        elif call.data.startswith("admin_"):
            if is_admin(user_id):
                handle_admin_commands(call)
            else:
                bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
        
        else:
            bot.answer_callback_query(call.id, "❌ Unknown command!", show_alert=True)
                
    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred! Please try again.", show_alert=True)

# Main menu functions
def show_main_menu(call):
    try:
        user_id = call.from_user.id
        
        welcome_text = f"""
✨ Welcome To SMM Bot ✨

Hello {call.from_user.first_name}! 

Select an option from the menu below:
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
            bot.send_message(call.from_user.id, "✨ Welcome To SMM Bot ✨\n\nSelect an option:", reply_markup=main_menu_keyboard())
        except:
            pass

def show_main_menu_for_message(message):
    try:
        user_id = message.from_user.id
        bot.send_photo(
            chat_id=user_id,
            photo=WELCOME_IMAGE,
            caption="✨ Welcome To SMM Bot ✨\n\nSelect an option from the menu:",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        print(f"Show main menu for message error: {e}")

# Deposit flow
def show_deposit_menu(call):
    try:
        user_id = call.from_user.id
        
        # Clear any existing session data
        clear_all_user_data(user_id)
        
        deposit_text = """
💰 Deposit Funds

Enter the amount you want to deposit in rupees.

💳 Minimum deposit: ₹10
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=deposit_text,
            reply_markup=None
        )
        
        msg = bot.send_message(user_id, "💳 Please enter the amount you want to deposit (in ₹):")
        bot.register_next_step_handler(msg, process_deposit_amount)
        
    except Exception as e:
        print(f"Show deposit menu error: {e}")
        bot.answer_callback_query(call.id, "❌ Error showing deposit menu. Please try again.", show_alert=True)

def process_deposit_amount(message):
    try:
        user_id = message.from_user.id
        
        # Check if message is a command
        if message.text.startswith('/'):
            show_main_menu_for_message(message)
            return
        
        amount = float(message.text)
        
        if amount < 10:
            bot.send_message(user_id, "❌ Minimum deposit amount is ₹10. Please enter a higher amount.")
            show_deposit_menu_standalone(user_id)
            return
        
        # Generate random UTR
        utr = str(random.randint(100000000000, 999999999999))
        
        # Save deposit data
        save_user_data(user_id, "deposit_utr", utr)
        save_user_data(user_id, "deposit_amount", amount)
        
        # Generate QR code
        qr_img = generate_qr_code(amount)
        
        deposit_info = f"""
💰 Deposit Request Created

💳 Amount: ₹{amount}
🔢 UTR: `{utr}`

📲 Scan the QR code to make payment.

💳 After payment, click \"I Have Paid\" to verify.
        """
        
        bot.send_photo(
            chat_id=user_id,
            photo=qr_img,
            caption=deposit_info,
            reply_markup=deposit_confirmation_keyboard(),
            parse_mode='Markdown'
        )
        
    except ValueError:
        bot.send_message(user_id, "❌ Invalid amount. Please enter a valid number.")
        show_deposit_menu_standalone(user_id)
    except Exception as e:
        print(f"Process deposit amount error: {e}")
        bot.send_message(user_id, "❌ Error processing deposit. Please try again.", reply_markup=back_to_main_button())

def show_deposit_menu_standalone(user_id):
    try:
        deposit_text = """
💰 Deposit Funds

Enter the amount you want to deposit in rupees.

💳 Minimum deposit: ₹10
        """
        
        bot.send_message(user_id, deposit_text)
        
        msg = bot.send_message(user_id, "💳 Please enter the amount you want to deposit (in ₹):")
        bot.register_next_step_handler(msg, process_deposit_amount)
        
    except Exception as e:
        print(f"Show deposit menu standalone error: {e}")
        bot.send_message(user_id, "❌ Error showing deposit menu. Please try again.", reply_markup=back_to_main_button())

def check_transaction(call):
    try:
        user_id = call.from_user.id
        
        utr = get_user_data(user_id, "deposit_utr")
        amount = get_user_data(user_id, "deposit_amount")
        
        if not utr or not amount:
            bot.answer_callback_query(call.id, "❌ No pending deposit found.", show_alert=True)
            return
        
        # Show verifying message
        verifying_msg = bot.send_message(user_id, "🔄 Verifying payment...")
        
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
✅ Payment Verified Successfully!

💳 Amount: ₹{amount}
💳 New Balance: ₹{new_balance:.2f}

Thank you for your deposit!
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
                        f"💰 New Deposit!\n\n👤 User: {user_id}\n💳 Amount: ₹{amount}\n💳 New Balance: ₹{new_balance:.2f}"
                    )
            except:
                pass
            
        else:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=verifying_msg.message_id,
                text="❌ Payment not verified. Please wait some time after payment and try again.",
                reply_markup=deposit_confirmation_keyboard()
            )
            
    except Exception as e:
        print(f"Check transaction error: {e}")
        bot.answer_callback_query(call.id, "❌ Error verifying payment.", show_alert=True)

# Order flow
def show_categories(call):
    try:
        user_id = call.from_user.id
        
        if not is_bot_accepting_orders():
            bot.answer_callback_query(call.id, "❌ Bot is currently not accepting orders.", show_alert=True)
            return
        
        categories_text = """
🛒 Select Category

Choose a category to view available services:
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=categories_text,
            reply_markup=categories_keyboard()
        )
    except Exception as e:
        print(f"Show categories error: {e}")
        bot.answer_callback_query(call.id, "❌ Error showing categories.", show_alert=True)

def show_services(call, category):
    try:
        user_id = call.from_user.id
        
        if category not in SERVICES:
            bot.answer_callback_query(call.id, "❌ Category not found.", show_alert=True)
            return
        
        services_text = f"""
📦 {category} Services

Select a service to order:
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=services_text,
            reply_markup=services_keyboard(category)
        )
    except Exception as e:
        print(f"Show services error: {e}")
        bot.answer_callback_query(call.id, "❌ Error showing services.", show_alert=True)

def start_order_flow(call, category, service_name):
    try:
        user_id = call.from_user.id
        
        # Replace underscores with spaces for service name
        service_name = service_name.replace('_', ' ')
        
        if category not in SERVICES or service_name not in SERVICES[category]:
            bot.answer_callback_query(call.id, "❌ Service not found.", show_alert=True)
            return
        
        service = SERVICES[category][service_name]
        
        service_info = f"""
📦 Service: {service_name}

💰 Price: ₹{service['price']}/1000
📉 Minimum: {service['min']:,}
📈 Maximum: {service['max']:,}

Please send the link for your order:
        """
        
        # Save service data
        save_user_data(user_id, "order_category", category)
        save_user_data(user_id, "order_service_name", service_name)
        save_user_data(user_id, "order_service_data", json.dumps(service))
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=service_info
        )
        
        msg = bot.send_message(user_id, "🔗 Please enter the link:")
        bot.register_next_step_handler(msg, process_order_link)
        
    except Exception as e:
        print(f"Start order flow error: {e}")
        bot.answer_callback_query(call.id, "❌ Error starting order.", show_alert=True)

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
            bot.send_message(user_id, "❌ Invalid link. Please enter a valid URL starting with http:// or https://")
            msg = bot.send_message(user_id, "🔗 Please enter the link:")
            bot.register_next_step_handler(msg, process_order_link)
            return
        
        # Get service data
        category = get_user_data(user_id, "order_category")
        service_name = get_user_data(user_id, "order_service_name")
        service_data = get_user_data(user_id, "order_service_data")
        
        if not all([category, service_name, service_data]):
            bot.send_message(user_id, "❌ Session expired. Please start over.")
            show_main_menu_for_message(message)
            return
        
        service = json.loads(service_data)
        
        # Save link
        save_user_data(user_id, "order_link", link)
        
        service_info = f"""
📦 Service: {service_name}
🔗 Link: {link[:50]}...

💰 Price: ₹{service['price']}/1000
📉 Minimum: {service['min']:,}
📈 Maximum: {service['max']:,}

Please enter the quantity:
        """
        
        bot.send_message(user_id, service_info)
        
        msg = bot.send_message(user_id, "🔢 Please enter the quantity:")
        bot.register_next_step_handler(msg, process_order_quantity)
        
    except Exception as e:
        print(f"Process order link error: {e}")
        bot.send_message(user_id, "❌ Error processing link. Please try again.", reply_markup=back_to_main_button())

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
            bot.send_message(user_id, "❌ Session expired. Please start over.")
            show_main_menu_for_message(message)
            return
        
        service = json.loads(service_data)
        
        # Validate quantity
        if quantity < service['min']:
            bot.send_message(user_id, f"❌ Minimum quantity is {service['min']:,}. Please enter a higher quantity.")
            msg = bot.send_message(user_id, "🔢 Please enter the quantity:")
            bot.register_next_step_handler(msg, process_order_quantity)
            return
        
        if quantity > service['max']:
            bot.send_message(user_id, f"❌ Maximum quantity is {service['max']:,}. Please enter a lower quantity.")
            msg = bot.send_message(user_id, "🔢 Please enter the quantity:")
            bot.register_next_step_handler(msg, process_order_quantity)
            return
        
        # Calculate cost
        cost = round((quantity / service['unit']) * service['price'], 2)
        
        # Check user balance
        user_balance = get_balance(user_id)
        
        if user_balance < cost:
            bot.send_message(
                user_id,
                f"❌ Insufficient balance!\n\n💳 Your Balance: ₹{user_balance:.2f}\n💰 Required: ₹{cost:.2f}\n\nPlease deposit funds first.",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("💰 Deposit", callback_data="deposit")
                )
            )
            return
        
        # Save quantity and cost
        save_user_data(user_id, "order_quantity", quantity)
        save_user_data(user_id, "order_cost", cost)
        
        order_summary = f"""
📦 Order Summary

📋 Service: {service_name}
🔗 Link: {link[:50]}...
🔢 Quantity: {quantity:,}
💰 Total Cost: ₹{cost:.2f}

💳 Your Balance: ₹{user_balance:.2f}

Click \"Confirm Order\" to proceed:
        """
        
        bot.send_message(
            user_id,
            order_summary,
            reply_markup=order_confirmation_keyboard(cost)
        )
        
    except ValueError:
        bot.send_message(user_id, "❌ Invalid quantity. Please enter a valid number.")
        msg = bot.send_message(user_id, "🔢 Please enter the quantity:")
        bot.register_next_step_handler(msg, process_order_quantity)
    except Exception as e:
        print(f"Process order quantity error: {e}")
        bot.send_message(user_id, "❌ Error processing quantity. Please try again.", reply_markup=back_to_main_button())

def confirm_order_processing(call):
    try:
        user_id = call.from_user.id
        
        # Get order data
        category = get_user_data(user_id, "order_category")
        service_name = get_user_data(user_id, "order_service_name")
        service_data = get_user_data(user_id, "order_service_data")
        link = get_user_data(user_id, "order_link")
        quantity = get_user_data(user_id, "order_quantity")
        cost = get_user_data(user_id, "order_cost")
        
        if not all([category, service_name, service_data, link, quantity, cost]):
            bot.answer_callback_query(call.id, "❌ Session expired. Please start over.", show_alert=True)
            return
        
        service = json.loads(service_data)
        
        # Check balance
        user_balance = get_balance(user_id)
        if user_balance < cost:
            bot.answer_callback_query(call.id, f"❌ Insufficient balance. You need ₹{cost:.2f}, but have ₹{user_balance:.2f}", show_alert=True)
            return
        
        # Show processing message
        processing_msg = bot.send_message(user_id, "🔄 Processing your order...")
        
        # Place order via API
        api_order_id = place_smm_order(service['id'], link, quantity)
        
        if api_order_id:
            # Deduct balance
            new_balance = update_balance(user_id, -cost)
            
            # Record order
            order = add_order(user_id, service_name, link, quantity, cost, api_order_id)
            
            success_text = f"""
✅ Order Placed Successfully!

📦 Service: {service_name}
🔗 Link: {link[:50]}...
🔢 Quantity: {quantity:,}
💰 Cost: ₹{cost:.2f}
💳 Remaining Balance: ₹{new_balance:.2f}
🆔 Order ID: {order['order_id']}

Thank you for your order!
            """
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=success_text
            )
            
            # Clear session data
            clear_all_user_data(user_id)
            
            # Notify admin
            try:
                for admin_id in ADMIN_IDS:
                    bot.send_message(
                        admin_id,
                        f"🛒 New Order!\n\n👤 User: {user_id}\n📦 Service: {service_name}\n💰 Amount: ₹{cost:.2f}\n🆔 Order ID: {order['order_id']}"
                    )
            except:
                pass
            
        else:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text="❌ Failed to place order. Please try again later or contact support.",
                reply_markup=back_to_main_button()
            )
            
    except Exception as e:
        print(f"Confirm order processing error: {e}")
        bot.answer_callback_query(call.id, "❌ Error processing order.", show_alert=True)

# Other menu functions
def show_orders(call):
    try:
        user_id = call.from_user.id
        
        orders = get_user_orders(user_id, 10)
        
        if not orders:
            orders_text = """
📋 Order History

No orders found.

Place your first order using the Order button!
            """
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=orders_text,
                reply_markup=back_to_main_button()
            )
            return
        
        orders_text = "📋 Recent Orders\n\n"
        
        for order in orders[:5]:  # Show last 5 orders
            status_emoji = "✅" if order["status"] == "Completed" else "🔄" if order["status"] == "Processing" else "⏳" if order["status"] == "Pending" else "❌"
            orders_text += f"""
{status_emoji} {order["service_name"]}
🔢 {order["quantity"]:,} | 💰 ₹{order["cost"]:.2f}
🆔 {order["order_id"]} | 📅 {order["order_date"].strftime("%d/%m/%Y")}
🔗 {order["link"][:30]}...
"""
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=orders_text,
            reply_markup=back_to_main_button()
        )
        
    except Exception as e:
        print(f"Show orders error: {e}")
        bot.answer_callback_query(call.id, "❌ Error loading orders.", show_alert=True)

def show_refer(call):
    try:
        user_id = call.from_user.id
        
        refer_text = f"""
👥 Refer & Earn

🔗 Your Referral Link:
`{BOT_LINK}?start={user_id}`

📊 Referral Stats:
👥 Total Referrals: 0
💰 Earned: ₹0.00

💸 Earn 5% commission on every deposit made by your referrals!
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=refer_text,
            reply_markup=back_to_main_button(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Show refer error: {e}")
        bot.answer_callback_query(call.id, "❌ Error loading referral info.", show_alert=True)

def show_account(call):
    try:
        user_id = call.from_user.id
        user = get_user(user_id)
        
        account_text = f"""
👤 Account Information

🆔 User ID: {user_id}
👤 Username: @{user['username']}
💳 Balance: ₹{user['balance']:.2f}

📊 Statistics:
📥 Total Deposits: ₹{user.get('total_deposits', 0):.2f}
📤 Total Spent: ₹{user.get('total_spent', 0):.2f}
📅 Member Since: {user['joined_date'].strftime("%d/%m/%Y")}
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=account_text,
            reply_markup=back_to_main_button()
        )
        
    except Exception as e:
        print(f"Show account error: {e}")
        bot.answer_callback_query(call.id, "❌ Error loading account info.", show_alert=True)

def show_stats(call):
    try:
        user_id = call.from_user.id
        user = get_user(user_id)
        
        stats_text = f"""
📊 Your Statistics

💳 Balance: ₹{user['balance']:.2f}
📥 Total Deposits: ₹{user.get('total_deposits', 0):.2f}
📤 Total Spent: ₹{user.get('total_spent', 0):.2f}

📈 Overall Bot Stats:
👥 Total Users: {get_all_users():,}
🛒 Total Orders: {get_total_orders():,}
💰 Total Deposits: ₹{get_total_deposits():.2f}
💸 Total Spent: ₹{get_total_spent():.2f}
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=stats_text,
            reply_markup=back_to_main_button()
        )
        
    except Exception as e:
        print(f"Show stats error: {e}")
        bot.answer_callback_query(call.id, "❌ Error loading statistics.", show_alert=True)

def show_support(call):
    try:
        support_text = f"""
ℹ️ Support

📞 Contact Us: {SUPPORT_LINK}
📢 Channel: {CHANNEL_ID}

🛠️ Need help? Contact our support team for assistance with orders, deposits, or any other issues.

We're here to help 24/7!
        """
        
        bot.edit_message_text(
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            text=support_text,
            reply_markup=support_keyboard()
        )
        
    except Exception as e:
        print(f"Show support error: {e}")
        bot.answer_callback_query(call.id, "❌ Error loading support info.", show_alert=True)

def check_channel_join(call):
    try:
        user_id = call.from_user.id
        
        if check_channel_membership(user_id):
            bot.answer_callback_query(call.id, "✅ Thank you for joining! Welcome to the bot.", show_alert=True)
            start_command(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet. Please join and try again.", show_alert=True)
            
    except Exception as e:
        print(f"Check channel join error: {e}")
        bot.answer_callback_query(call.id, "❌ Error checking membership.", show_alert=True)

# Admin functions
def show_admin_panel(call):
    try:
        admin_text = """
👑 Admin Panel

🎛️ Manage your SMM bot from admin dashboard.

Select an option below:
        """
        
        bot.edit_message_text(
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            text=admin_text,
            reply_markup=admin_keyboard()
        )
        
    except Exception as e:
        print(f"Show admin panel error: {e}")
        bot.answer_callback_query(call.id, "❌ Error loading admin panel.", show_alert=True)

def handle_admin_commands(call):
    try:
        user_id = call.from_user.id
        
        if call.data == "admin_balance":
            admin_balance_text = """
💰 Balance Control

Manage user balances:
            """
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=admin_balance_text,
                reply_markup=admin_balance_keyboard()
            )
            
        elif call.data == "admin_stats":
            show_admin_stats(call)
            
        else:
            bot.answer_callback_query(call.id, "❌ Admin feature not implemented yet.", show_alert=True)
            
    except Exception as e:
        print(f"Handle admin commands error: {e}")
        bot.answer_callback_query(call.id, "❌ Error processing admin command.", show_alert=True)

def show_admin_stats(call):
    try:
        user_id = call.from_user.id
        
        total_users = get_all_users()
        total_orders = get_total_orders()
        total_deposits = get_total_deposits()
        total_spent = get_total_spent()
        
        admin_stats_text = f"""
📊 Admin Statistics

👥 Total Users: {total_users:,}
🛒 Total Orders: {total_orders:,}
💰 Total Deposits: ₹{total_deposits:.2f}
💸 Total Spent: ₹{total_spent:.2f}

📈 Bot Status: {'🟢 ONLINE' if is_bot_accepting_orders() else '🔴 OFFLINE'}
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=admin_stats_text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats"),
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            )
        )
        
    except Exception as e:
        print(f"Show admin stats error: {e}")
        bot.answer_callback_query(call.id, "❌ Error loading admin statistics.", show_alert=True)

def admin_balance_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Add Balance", callback_data="admin_add_balance"),
        InlineKeyboardButton("➖ Remove Balance", callback_data="admin_remove_balance")
    )
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    return markup

# Error handler
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    try:
        user_id = message.from_user.id
        
        # Check if user is banned
        user = get_user(user_id)
        if user.get('banned'):
            return
        
        # Check channel membership
        if not check_channel_membership(user_id):
            welcome_text = f"""
✨ Welcome {message.from_user.first_name}!

📢 Please join our channel to use the bot:

{CHANNEL_ID}

After joining, click the check button below.
            """
            bot.send_message(user_id, welcome_text, reply_markup=channel_join_keyboard())
            return
        
        # Show main menu for any other message
        show_main_menu_for_message(message)
        
    except Exception as e:
        print(f"Handle other messages error: {e}")

# Start polling
if __name__ == "__main__":
    print("🤖 SMM Bot Started Successfully!")
    print(f"👑 Admin IDs: {ADMIN_IDS}")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Bot polling error: {e}")
        time.sleep(5)
