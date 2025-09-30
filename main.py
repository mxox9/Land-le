import os
import logging
import threading
from datetime import datetime
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
load_dotenv()

# Initialize bot
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

# MongoDB setup
client = MongoClient(os.getenv('MONGO_URI'))
db = client.smm_bot
users_collection = db.users
deposits_collection = db.deposits
orders_collection = db.orders

# Global variables
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS').split(',')]
CHANNEL_ID = os.getenv('CHANNEL_ID')
BOT_USERNAME = os.getenv('BOT_USERNAME')
SMM_API_KEY = os.getenv('SMM_API_KEY')
SMM_API_URL = os.getenv('SMM_API_URL')
BHARATPE_TOKEN = os.getenv('BHARATPE_TOKEN')
BHARATPE_MERCHANT_ID = os.getenv('BHARATPE_MERCHANT_ID')
SUPPORT_WHATSAPP = os.getenv('SUPPORT_WHATSAPP')

# Import modules
from services import services_list, add_service, edit_service, delete_service
from payment import create_bharatpe_payment, verify_bharatpe_payment
from smm_api import create_smm_order, check_smm_order

# Bot control flags
bot_active = True

# Stylized text function
def stylize(text):
    mapping = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ',
        'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
        'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
        'y': 'ʏ', 'z': 'ᴢ'
    }
    result = ""
    for char in text:
        if char.lower() in mapping:
            if char.isupper():
                result += char  # Keep first letter as normal capital
            else:
                result += mapping[char]
        else:
            result += char
    return result

# Check channel membership
def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    # Check if user exists
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        # Check for referral
        referral_id = None
        if len(message.text.split()) > 1:
            ref_id = message.text.split()[1]
            if ref_id.startswith('ref_'):
                referral_id = int(ref_id[4:])
        
        # Create new user
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "total_deposit": 0,
            "total_spent": 0,
            "join_date": datetime.now(),
            "referred_by": referral_id,
            "banned": False
        })
        
        # Add referral bonus if applicable
        if referral_id:
            referrer = users_collection.find_one({"user_id": referral_id})
            if referrer:
                bonus = 500  # 5₹ bonus
                users_collection.update_one(
                    {"user_id": referral_id},
                    {"$inc": {"balance": bonus}}
                )
                try:
                    bot.send_message(
                        referral_id,
                        stylize(f"Rᴇғᴇʀʀᴀʟ Bᴏɴᴜs: Yᴏᴜ ɢᴏᴛ {bonus} ᴘᴏɪɴᴛs ғᴏʀ ʀᴇғᴇʀʀɪɴɢ {username}!")
                    )
                except:
                    pass
    
    # Check channel membership
    if not check_channel_membership(user_id):
        show_channel_join(message)
        return
    
    show_main_menu(message)

def show_channel_join(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(stylize("✅ Jᴏɪɴ Cʜᴀɴɴᴇʟ"), url=f"https://t.me/{CHANNEL_ID[1:]}"),
        InlineKeyboardButton(stylize("🔃 Cʜᴇᴄᴋ"), callback_data="check_join")
    )
    bot.send_message(
        message.chat.id,
        stylize("Pʟᴇᴀsᴇ Jᴏɪɴ Oᴜʀ Cʜᴀɴɴᴇʟ Tᴏ Usᴇ Tʜᴇ Bᴏᴛ"),
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if check_channel_membership(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message)
    else:
        bot.answer_callback_query(call.id, stylize("Pʟᴇᴀsᴇ Jᴏɪɴ Tʜᴇ Cʜᴀɴɴᴇʟ Fɪʀsᴛ"), show_alert=True)

def show_main_menu(message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(stylize("💰 Dᴇᴘᴏsɪᴛ"), callback_data="deposit"),
        InlineKeyboardButton(stylize("🛒 Nᴇᴡ Oʀᴅᴇʀ"), callback_data="new_order"),
        InlineKeyboardButton(stylize("📋 Tʀᴀᴄᴋ Oʀᴅᴇʀ"), callback_data="track_order"),
        InlineKeyboardButton(stylize("👤 Aᴄᴄᴏᴜɴᴛ"), callback_data="account"),
        InlineKeyboardButton(stylize("👥 Rᴇғᴇʀ"), callback_data="refer"),
        InlineKeyboardButton(stylize("📊 Sᴛᴀᴛs"), callback_data="stats"),
        InlineKeyboardButton(stylize("ℹ️ Sᴜᴘᴘᴏʀᴛ"), callback_data="support")
    )
    keyboard.row(
        InlineKeyboardButton(stylize("Hᴏᴡ Tᴏ Usᴇ"), callback_data="how_to_use"),
        InlineKeyboardButton(stylize("Rᴇsᴛᴀʀᴛ"), callback_data="restart")
    )
    
    bot.send_message(
        message.chat.id,
        stylize("Wᴇʟᴄᴏᴍᴇ Tᴏ Sᴍᴍ Bᴏᴛ! Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ:"),
        reply_markup=keyboard
    )

# Deposit handler
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit_callback(call):
    msg = bot.send_message(call.message.chat.id, stylize("Eɴᴛᴇʀ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ ɪɴ ₹:"))
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, stylize("Mɪɴɪᴍᴜᴍ Dᴇᴘᴏsɪᴛ ɪs ₹10"))
            return
        
        # Create payment
        payment_data = create_bharatpe_payment(amount, message.from_user.id)
        if payment_data:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(stylize("Pᴀɪᴅ ✅"), callback_data=f"verify_{payment_data['transaction_id']}"))
            
            bot.send_message(
                message.chat.id,
                stylize(f"Pʟᴇᴀsᴇ Pᴀʏ ₹{amount} ᴜsɪɴɢ BʜᴀʀᴀᴛPᴇ\n\nUPI: {payment_data['upi_id']}\nQR Code: {payment_data['qr_code']}"),
                reply_markup=keyboard
            )
        else:
            bot.send_message(message.chat.id, stylize("Pᴀʏᴍᴇɴᴛ Fᴀɪʟᴇᴅ. Tʀʏ Aɢᴀɪɴ Lᴀᴛᴇʀ."))
    except ValueError:
        bot.send_message(message.chat.id, stylize("Iɴᴠᴀʟɪᴅ Aᴍᴏᴜɴᴛ. Pʟᴇᴀsᴇ Eɴᴛᴇʀ Nᴜᴍʙᴇʀ."))

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def verify_payment_callback(call):
    transaction_id = call.data[7:]
    if verify_bharatpe_payment(transaction_id):
        deposit = deposits_collection.find_one({"transaction_id": transaction_id})
        if deposit:
            points = int(deposit['amount'] * 100)
            users_collection.update_one(
                {"user_id": call.from_user.id},
                {"$inc": {"balance": points, "total_deposit": deposit['amount']}}
            )
            
            bot.send_message(call.message.chat.id, stylize(f"Pᴀʏᴍᴇɴᴛ Vᴇʀɪғɪᴇᴅ! {points} ᴘᴏɪɴᴛs ᴀᴅᴅᴇᴅ."))
            
            # Notify admin
            for admin_id in ADMIN_IDS:
                bot.send_message(admin_id, stylize(f"Nᴇᴡ Dᴇᴘᴏsɪᴛ: ₹{deposit['amount']} ғʀᴏᴍ ᴜsᴇʀ {call.from_user.id}"))
    else:
        bot.answer_callback_query(call.id, stylize("Pᴀʏᴍᴇɴᴛ Nᴏᴛ Vᴇʀɪғɪᴇᴅ ʏᴇᴛ"), show_alert=True)

# New Order flow
@bot.callback_query_handler(func=lambda call: call.data == "new_order")
def new_order_callback(call):
    if not bot_active:
        bot.answer_callback_query(call.id, stylize("Bᴏᴛ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ"), show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    categories = set(service['category'] for service in services_list if service['active'])
    for category in categories:
        keyboard.add(InlineKeyboardButton(stylize(category), callback_data=f"category_{category}"))
    
    bot.send_message(call.message.chat.id, stylize("Sᴇʟᴇᴄᴛ Cᴀᴛᴇɢᴏʀʏ:"), reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def category_callback(call):
    category = call.data[9:]
    services = [s for s in services_list if s['category'] == category and s['active']]
    
    keyboard = InlineKeyboardMarkup()
    for service in services:
        keyboard.add(InlineKeyboardButton(
            stylize(f"{service['name']} - ₹{service['price_per_unit']}/{service['unit']}"),
            callback_data=f"service_{service['id']}"
        ))
    
    bot.send_message(call.message.chat.id, stylize("Sᴇʟᴇᴄᴛ Sᴇʀᴠɪᴄᴇ:"), reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("service_"))
def service_callback(call):
    service_id = int(call.data[8:])
    service = next((s for s in services_list if s['id'] == service_id), None)
    
    if service:
        msg = bot.send_message(
            call.message.chat.id,
            stylize(f"Sᴇʀᴠɪᴄᴇ: {service['name']}\nDᴇsᴄʀɪᴘᴛɪᴏɴ: {service['description']}\nPʀɪᴄᴇ: ₹{service['price_per_unit']} ᴘᴇʀ {service['unit']}\nMɪɴ: {service['min']}, Mᴀx: {service['max']}\n\nSᴇɴᴅ Lɪɴᴋ:")
        )
        bot.register_next_step_handler(msg, process_order_link, service)

def process_order_link(message, service):
    link = message.text
    msg = bot.send_message(message.chat.id, stylize(f"Eɴᴛᴇʀ Qᴜᴀɴᴛɪᴛʏ ({service['min']}-{service['max']}):"))
    bot.register_next_step_handler(msg, process_order_quantity, service, link)

def process_order_quantity(message, service, link):
    try:
        quantity = int(message.text)
        if quantity < service['min'] or quantity > service['max']:
            bot.send_message(message.chat.id, stylize(f"Qᴜᴀɴᴛɪᴛʏ Mᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ {service['min']} ᴀɴᴅ {service['max']}"))
            return
        
        cost = quantity * service['price_per_unit']
        user = users_collection.find_one({"user_id": message.from_user.id})
        
        if user['balance'] < cost:
            bot.send_message(message.chat.id, stylize("Iɴsᴜғғɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ. Pʟᴇᴀsᴇ Dᴇᴘᴏsɪᴛ Fɪʀsᴛ."))
            return
        
        # Create order
        order_result = create_smm_order(service, link, quantity)
        if order_result:
            # Deduct balance
            users_collection.update_one(
                {"user_id": message.from_user.id},
                {"$inc": {"balance": -cost, "total_spent": cost}}
            )
            
            # Save order to database
            order_data = {
                "user_id": message.from_user.id,
                "service_id": service['id'],
                "service_name": service['name'],
                "link": link,
                "quantity": quantity,
                "cost": cost,
                "status": "Pending",
                "order_id": order_result['order_id'],
                "created_at": datetime.now(),
                "api_id": order_result.get('api_id')
            }
            orders_collection.insert_one(order_data)
            
            # Notify user
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(stylize("Bᴏᴛ Hᴇʀᴇ 🈴"), url=f"https://t.me/{BOT_USERNAME}"))
            
            bot.send_message(
                message.chat.id,
                stylize(f"Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!\nOʀᴅᴇʀ ID: {order_result['order_id']}\nSᴇʀᴠɪᴄᴇ: {service['name']}\nQᴜᴀɴᴛɪᴛʏ: {quantity}\nCᴏsᴛ: {cost} ᴘᴏɪɴᴛs"),
                reply_markup=keyboard
            )
            
            # Notify admin
            for admin_id in ADMIN_IDS:
                bot.send_message(
                    admin_id,
                    stylize(f"Nᴇᴡ Oʀᴅᴇʀ!\nUsᴇʀ: {message.from_user.id}\nSᴇʀᴠɪᴄᴇ: {service['name']}\nOʀᴅᴇʀ ID: {order_result['order_id']}"),
                    reply_markup=keyboard
                )
        else:
            bot.send_message(message.chat.id, stylize("Oʀᴅᴇʀ Fᴀɪʟᴇᴅ. Pʟᴇᴀsᴇ Tʀʏ Aɢᴀɪɴ Lᴀᴛᴇʀ."))
    except ValueError:
        bot.send_message(message.chat.id, stylize("Iɴᴠᴀʟɪᴅ Qᴜᴀɴᴛɪᴛʏ. Pʟᴇᴀsᴇ Eɴᴛᴇʀ Nᴜᴍʙᴇʀ."))

# Track Order
@bot.callback_query_handler(func=lambda call: call.data == "track_order")
def track_order_callback(call):
    msg = bot.send_message(call.message.chat.id, stylize("Eɴᴛᴇʀ Oʀᴅᴇʀ ID:"))
    bot.register_next_step_handler(msg, process_track_order)

def process_track_order(message):
    order_id = message.text
    order = orders_collection.find_one({"order_id": order_id, "user_id": message.from_user.id})
    
    if order:
        # Check status from SMM API
        status = check_smm_order(order['api_id']) if order.get('api_id') else order['status']
        
        bot.send_message(
            message.chat.id,
            stylize(f"Oʀᴅᴇʀ Dᴇᴛᴀɪʟs:\nSᴇʀᴠɪᴄᴇ: {order['service_name']}\nOʀᴅᴇʀ ID: {order['order_id']}\nQᴜᴀɴᴛɪᴛʏ: {order['quantity']}\nCᴏsᴛ: {order['cost']} ᴘᴏɪɴᴛs\nSᴛᴀᴛᴜs: {status}")
        )
    else:
        bot.send_message(message.chat.id, stylize("Oʀᴅᴇʀ Nᴏᴛ Fᴏᴜɴᴅ"))

# Account
@bot.callback_query_handler(func=lambda call: call.data == "account")
def account_callback(call):
    user = users_collection.find_one({"user_id": call.from_user.id})
    if user:
        balance_rupees = user['balance'] / 100
        
        bot.send_message(
            call.message.chat.id,
            stylize(f"Aᴄᴄᴏᴜɴᴛ Dᴇᴛᴀɪʟs:\n\nUsᴇʀ ID: {user['user_id']}\nBᴀʟᴀɴᴄᴇ: {user['balance']} ᴘᴏɪɴᴛs (₹{balance_rupees:.2f})\nTᴏᴛᴀʟ Dᴇᴘᴏsɪᴛ: ₹{user['total_deposit']}\nTᴏᴛᴀʟ Sᴘᴇɴᴛ: {user['total_spent']} ᴘᴏɪɴᴛs\nJᴏɪɴ Dᴀᴛᴇ: {user['join_date'].strftime('%Y-%m-%d %H:%M')}")
        )

# Referral
@bot.callback_query_handler(func=lambda call: call.data == "refer")
def refer_callback(call):
    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{call.from_user.id}"
    bot.send_message(
        call.message.chat.id,
        stylize(f"Rᴇғᴇʀ & Eᴀʀɴ!\n\nSʜᴀʀᴇ Yᴏᴜʀ Rᴇғᴇʀʀᴀʟ Lɪɴᴋ:\n{referral_link}\n\nYᴏᴜ ɢᴇᴛ 500 ᴘᴏɪɴᴛs ғᴏʀ ᴇᴀᴄʜ ʀᴇғᴇʀʀᴀʟ!")
    )

# Stats
@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats_callback(call):
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    total_deposit = users_collection.aggregate([{"$group": {"_id": None, "total": {"$sum": "$total_deposit"}}}]).next()['total']
    
    bot.send_message(
        call.message.chat.id,
        stylize(f"Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs:\n\nTᴏᴛᴀʟ Usᴇʀs: {total_users}\nTᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}\nTᴏᴛᴀʟ Dᴇᴘᴏsɪᴛ: ₹{total_deposit}")
    )

# Support
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support_callback(call):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(stylize("Cᴏɴᴛᴀᴄᴛ Us"), url=SUPPORT_WHATSAPP),
        InlineKeyboardButton(stylize("Bᴀᴄᴋ"), callback_data="main_menu")
    )
    
    bot.send_photo(
        call.message.chat.id,
        photo=open('support.jpg', 'rb') if os.path.exists('support.jpg') else None,
        caption=stylize("Cᴏɴᴛᴀᴄᴛ Oᴜʀ Sᴜᴘᴘᴏʀᴛ Tᴇᴀᴍ Fᴏʀ Aɴʏ Hᴇʟᴘ:"),
        reply_markup=keyboard
    )

# How to Use
@bot.callback_query_handler(func=lambda call: call.data == "how_to_use")
def how_to_use_callback(call):
    instructions = """
1. 💰 Dᴇᴘᴏsɪᴛ - Aᴅᴅ ғᴜɴᴅs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ
2. 🛒 Nᴇᴡ Oʀᴅᴇʀ - Pʟᴀᴄᴇ ɴᴇᴡ SMM ᴏʀᴅᴇʀs
3. 📋 Tʀᴀᴄᴋ Oʀᴅᴇʀ - Cʜᴇᴄᴋ ᴏʀᴅᴇʀ sᴛᴀᴛᴜs
4. 👤 Aᴄᴄᴏᴜɴᴛ - Vɪᴇᴡ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ɪɴғᴏ
5. 👥 Rᴇғᴇʀ - Eᴀʀɴ ʙʏ ʀᴇғᴇʀʀɪɴɢ ғʀɪᴇɴᴅs
6. 📊 Sᴛᴀᴛs - Vɪᴇᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs
7. ℹ️ Sᴜᴘᴘᴏʀᴛ - Gᴇᴛ ʜᴇʟᴘ
"""
    bot.send_message(call.message.chat.id, stylize(instructions))

# Restart
@bot.callback_query_handler(func=lambda call: call.data == "restart")
def restart_callback(call):
    start_command(call.message)

# Main menu callback
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def main_menu_callback(call):
    show_main_menu(call.message)

# Admin Panel
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(stylize("📦 Mᴀɴᴀɢᴇ Sᴇʀᴠɪᴄᴇs"), callback_data="admin_services"),
        InlineKeyboardButton(stylize("💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ"), callback_data="admin_balance"),
        InlineKeyboardButton(stylize("👥 Usᴇʀ Cᴏɴᴛʀᴏʟ"), callback_data="admin_users"),
        InlineKeyboardButton(stylize("📢 Bʀᴏᴀᴅᴄᴀsᴛ"), callback_data="admin_broadcast"),
        InlineKeyboardButton(stylize("⚙️ Bᴏᴛ Cᴏɴᴛʀᴏʟ"), callback_data="admin_bot")
    )
    
    bot.send_message(message.chat.id, stylize("Aᴅᴍɪɴ Pᴀɴᴇʟ:"), reply_markup=keyboard)

# Refund system
def check_pending_orders():
    pending_orders = orders_collection.find({"status": {"$in": ["Pending", "In progress"]}})
    
    for order in pending_orders:
        status = check_smm_order(order.get('api_id'))
        if status in ["Cancelled", "Partial"]:
            # Refund points
            users_collection.update_one(
                {"user_id": order['user_id']},
                {"$inc": {"balance": order['cost']}}
            )
            
            # Update order status
            orders_collection.update_one(
                {"_id": order['_id']},
                {"$set": {"status": status}}
            )
            
            # Notify user
            try:
                bot.send_message(
                    order['user_id'],
                    stylize(f"Oʀᴅᴇʀ Rᴇғᴜɴᴅᴇᴅ!\nOʀᴅᴇʀ ID: {order['order_id']}\nSᴛᴀᴛᴜs: {status}\nAᴍᴏᴜɴᴛ: {order['cost']} ᴘᴏɪɴᴛs ʀᴇғᴜɴᴅᴇᴅ")
                )
            except:
                pass
            
            # Notify admin
            for admin_id in ADMIN_IDS:
                bot.send_message(
                    admin_id,
                    stylize(f"Oʀᴅᴇʀ Rᴇғᴜɴᴅᴇᴅ!\nUsᴇʀ: {order['user_id']}\nOʀᴅᴇʀ ID: {order['order_id']}\nAᴍᴏᴜɴᴛ: {order['cost']} ᴘᴏɪɴᴛs")
                )

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(check_pending_orders, 'interval', minutes=30)
scheduler.start()

# Start bot
if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
