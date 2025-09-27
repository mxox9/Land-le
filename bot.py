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

# Load environment variables
load_dotenv()

# Configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN', '8052955693:AAGoXnNg90jqvcC1X1fVo_qKV8Y0eHjDAZg')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://saifulmolla79088179_db_user:17gNrX0pC3bPqVaG@cluster0.fusvqca.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '6052975324').split(',')]
CHANNEL_ID = os.getenv('CHANNEL_ID', '@prooflelo1')
SMM_API_URL = os.getenv('SMM_API_URL', 'https://mysmmapi.com/api/v2?')
SMM_API_KEY = os.getenv('SMM_API_KEY', 'a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d')

# Use your existing deposit API credentials
AUTODEP_API_KEY = os.getenv('AUTODEP_API_KEY', 'LY81vEV7')
MERCHANT_KEY = os.getenv('MERCHANT_KEY', 'WYcmQI71591891985230')

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# MongoDB connection
try:
    client = MongoClient(MONGO_URI)
    db = client.smm_bot
    users_collection = db.users
    services_collection = db.services
    orders_collection = db.orders
    deposits_collection = db.deposits
    admin_logs_collection = db.admin_logs
    processed_refunds_collection = db.processed_refunds
    config_collection = db.config
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    exit(1)

# Initialize default config
if not config_collection.find_one({"_id": "bot_config"}):
    config_collection.insert_one({
        "_id": "bot_config",
        "accepting_orders": True,
        "maintenance_mode": False
    })

# User states for conversation flow
user_states = {}

# Image URLs
WELCOME_IMAGE = "https://t.me/prooflelo1/16"
SERVICE_IMAGE = "https://t.me/prooflelo1/16"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/16"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/16"
HISTORY_IMAGE = "https://t.me/prooflelo1/16"
REFER_IMAGE = "https://t.me/prooflelo1/16"

# Helper Functions
def log_admin_action(admin_id, action, details):
    """Log admin actions to database"""
    admin_logs_collection.insert_one({
        "admin_id": admin_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now()
    })

def get_user_balance(user_id):
    """Get user balance in points"""
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        # Create new user
        users_collection.insert_one({
            "user_id": user_id,
            "balance_points": 0,
            "total_deposits_points": 0,
            "total_spent_points": 0,
            "joined_at": datetime.now(),
            "banned": False
        })
        return 0
    return user.get("balance_points", 0)

def update_user_balance(user_id, points_change, is_deposit=False, is_spent=False):
    """Update user balance and related stats"""
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        return 0
    
    update_data = {"$inc": {"balance_points": points_change}}
    
    if is_deposit:
        update_data["$inc"]["total_deposits_points"] = points_change
    elif is_spent:
        update_data["$inc"]["total_spent_points"] = points_change
    
    users_collection.update_one({"user_id": user_id}, update_data)
    return get_user_balance(user_id)

def check_channel_membership(user_id):
    """Check if user is member of required channel"""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Channel check error: {e}")
        return False

def get_services_by_category(category):
    """Get active services by category"""
    return list(services_collection.find({
        "category": category,
        "active": True
    }))

def get_service_by_id(service_id):
    """Get service by ID"""
    return services_collection.find_one({
        "_id": ObjectId(service_id)
    })

def create_order(user_id, service_id, link, quantity, cost_points):
    """Create new order"""
    service = get_service_by_id(service_id)
    if not service:
        return None
    
    order_id = f"ORD{random.randint(100000, 999999)}"
    order = {
        "order_id": order_id,
        "user_id": user_id,
        "service_id": service_id,
        "service_name": service["name"],
        "link": link,
        "quantity": quantity,
        "cost_points": cost_points,
        "status": "Pending",
        "created_at": datetime.now(),
        "last_check": datetime.now()
    }
    
    result = orders_collection.insert_one(order)
    return order

def get_user_orders(user_id, limit=5):
    """Get user's recent orders"""
    return list(orders_collection.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit))

def get_order_by_id(order_id):
    """Get order by order ID"""
    return orders_collection.find_one({"order_id": order_id})

# Keyboard Builders
def main_menu_keyboard():
    """Main menu inline keyboard"""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("💰 Dᴇᴘᴏsɪᴛ", callback_data="deposit"),
        InlineKeyboardButton("🛒 Oʀᴅᴇʀ", callback_data="order_menu")
    )
    markup.add(
        InlineKeyboardButton("📋 Oʀᴅᴇʀs", callback_data="history"),
        InlineKeyboardButton("👥 Rᴇғᴇʀ", callback_data="refer")
    )
    markup.add(
        InlineKeyboardButton("👤 Aᴄᴄᴏᴜɴᴛ", callback_data="account"),
        InlineKeyboardButton("📊 Sᴛᴀᴛs", callback_data="stats")
    )
    markup.add(InlineKeyboardButton("ℹ️ Sᴜᴘᴘᴏʀᴛ", callback_data="support"))
    
    # Persistent buttons
    markup.add(
        InlineKeyboardButton("📺 How To Use", url="https://t.me/prooflelo1/26"),
        InlineKeyboardButton("🔄 Restart", callback_data="restart")
    )
    
    return markup

def service_category_keyboard():
    """Service category selection keyboard"""
    markup = InlineKeyboardMarkup()
    
    # Get unique categories from services
    categories = services_collection.distinct("category", {"active": True})
    
    for category in categories:
        emoji = "📱" if category == "instagram" else "🎥" if category == "youtube" else "📢"
        markup.add(InlineKeyboardButton(
            f"{emoji} {category.title()}", 
            callback_data=f"category_{category}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    return markup

def services_keyboard(category):
    """Services list for a category"""
    markup = InlineKeyboardMarkup()
    services = get_services_by_category(category)
    
    for service in services:
        price = service["price_per_unit"]
        unit = service["unit"]
        button_text = f"{service['name']} - {price} Points/{unit}"
        markup.add(InlineKeyboardButton(
            button_text, 
            callback_data=f"service_{service['_id']}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="order_menu"))
    return markup

def channel_join_keyboard():
    """Channel join requirement keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    markup.add(InlineKeyboardButton("🔄 Check Join", callback_data="check_join"))
    return markup

def support_keyboard():
    """Support options keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📞 Contact Us", url="https://wa.me/639941532149"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    return markup

def track_order_keyboard():
    """Track order keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📦 Track Order", callback_data="track_order"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    return markup

# Message Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    user_id = message.chat.id
    user_name = message.from_user.first_name
    
    # Check channel membership
    if not check_channel_membership(user_id):
        welcome_text = f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

📢 Pʟᴇᴀsᴇ Jᴏɪɴ Oᴜʀ Cʜᴀɴɴᴇʟ Tᴏ Usᴇ Tʜɪs Bᴏᴛ!

Jᴏɪɴ Tʜᴇ Cʜᴀɴɴᴇʟ Bᴇʟᴏᴡ Aɴᴅ Tʜᴇɴ Cʟɪᴄᴋ "Cʜᴇᴄᴋ Jᴏɪɴ" ✅
        """
        bot.send_photo(user_id, WELCOME_IMAGE, welcome_text, reply_markup=channel_join_keyboard())
        return
    
    # Initialize user
    get_user_balance(user_id)
    
    welcome_text = f"""
✅ Wᴇʟᴄᴏᴍᴇ {user_name}! ✅

🚀 Aᴅᴠᴀɴᴄᴇᴅ SMM Pᴀɴᴇʟ Bᴏᴛ

⚡ Fᴀsᴛ Dᴇʟɪᴠᴇʀʏ | 🔒 Sᴇᴄᴜʀᴇ | 💰 Cʜᴇᴀᴘ

Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ Fʀᴏᴍ Bᴇʟᴏᴡ:
    """
    bot.send_photo(user_id, WELCOME_IMAGE, welcome_text, reply_markup=main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle all callback queries"""
    user_id = call.message.chat.id
    
    try:
        if call.data == "check_join":
            if check_channel_membership(user_id):
                bot.delete_message(user_id, call.message.message_id)
                send_welcome(call.message)
            else:
                bot.answer_callback_query(call.id, "❌ Pʟᴇᴀsᴇ Jᴏɪɴ Tʜᴇ Cʜᴀɴɴᴇʟ Fɪʀsᴛ!", show_alert=True)
        
        elif call.data == "main_menu":
            show_main_menu(call)
        
        elif call.data == "deposit":
            start_deposit(call)
        
        elif call.data == "order_menu":
            show_categories(call)
        
        elif call.data.startswith("category_"):
            category = call.data.replace("category_", "")
            show_services(call, category)
        
        elif call.data.startswith("service_"):
            service_id = call.data.replace("service_", "")
            start_order(call, service_id)
        
        elif call.data == "history":
            show_history(call)
        
        elif call.data == "account":
            show_account(call)
        
        elif call.data == "refer":
            show_refer(call)
        
        elif call.data == "support":
            show_support(call)
        
        elif call.data == "stats":
            show_stats(call)
        
        elif call.data == "track_order":
            start_track_order(call)
        
        elif call.data == "restart":
            bot.delete_message(user_id, call.message.message_id)
            send_welcome(call.message)
        
        elif call.data == "check_deposit":
            verify_deposit(call)
            
    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!")

# Deposit System - Using YOUR existing API
def start_deposit(call):
    """Start deposit process"""
    user_id = call.message.chat.id
    
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    
    deposit_text = """
💰 Eɴᴛᴇʀ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ (ɪɴ ₹):

Exᴀᴍᴘʟᴇ: 10, 50, 100

Mɪɴɪᴍᴜᴍ: ₹10
    """
    
    bot.send_photo(user_id, DEPOSIT_IMAGE, deposit_text)
    user_states[user_id] = {"action": "awaiting_deposit_amount"}
    bot.register_next_step_handler(call.message, process_deposit_amount)

def process_deposit_amount(message):
    """Process deposit amount"""
    user_id = message.chat.id
    
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(user_id, "❌ Mɪɴɪᴍᴜᴍ ₹10 Rᴇǫᴜɪʀᴇᴅ!")
            return
        
        # Generate UTR
        utr = str(random.randint(100000000000, 999999999999))
        user_states[user_id] = {"utr": utr, "amount": amount}
        
        # Create deposit record
        deposits_collection.insert_one({
            "user_id": user_id,
            "amount": amount,
            "utr": utr,
            "status": "pending",
            "created_at": datetime.now()
        })
        
        # Create UPI link and QR using YOUR existing UPI ID
        upi_link = f"upi://pay?pa=paytm.s1m11be@pty&pn=Paytm&am={amount}&tn=Deposit&tr={utr}"
        qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(upi_link)}&size=200"
        
        deposit_text = f"""
💰 Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ 💰

📱 UPI ID: `paytm.s1m11be@pty`
💰 Aᴍᴏᴜɴᴛ: ₹{amount}
🔢 UTR: `{utr}`

Sᴄᴀɴ QR ᴏʀ ᴜsᴇ UPI ID ᴛᴏ ᴘᴀʏ.
Aғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ, ᴄʟɪᴄᴋ 'Pᴀɪᴅ ✅'
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💰 Pᴀɪᴅ ✅", callback_data="check_deposit"))
        markup.add(InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu"))
        
        bot.send_photo(user_id, qr_url, deposit_text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def verify_deposit(call):
    """Verify deposit payment using YOUR existing API"""
    user_id = call.message.chat.id
    
    if user_id not in user_states or "utr" not in user_states[user_id]:
        bot.answer_callback_query(call.id, "❌ Nᴏ ᴅᴇᴘᴏsɪᴛ ʀᴇǫᴜᴇsᴛ ғᴏᴜɴᴅ!", show_alert=True)
        return
    
    deposit_data = user_states[user_id]
    utr = deposit_data["utr"]
    amount = deposit_data["amount"]
    
    try:
        # Use YOUR existing AutoDep API exactly as in your original code
        api_url = f"https://erox-autodep-api.onrender.com/api?key=LY81vEV7&merchantkey=WYcmQI71591891985230&transactionid={utr}"
        response = requests.get(api_url, timeout=10).json()
        
        if response.get("result", {}).get("STATUS") == "TXN_SUCCESS":
            points = int(amount * 100)  # 1₹ = 100 points
            new_balance = update_user_balance(user_id, points, is_deposit=True)
            
            # Update deposit status
            deposits_collection.update_one(
                {"utr": utr}, 
                {"$set": {"status": "completed", "completed_at": datetime.now()}}
            )
            
            # Delete QR message
            try:
                bot.delete_message(user_id, call.message.message_id)
            except:
                pass
            
            success_text = f"""
✅ Pᴀʏᴍᴇɴᴛ Sᴜᴄᴄᴇssғᴜʟ! ✅

💰 Dᴇᴘᴏsɪᴛᴇᴅ: ₹{amount}
🎯 Pᴏɪɴᴛs Aᴅᴅᴇᴅ: {points}
🏦 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance}

Tʜᴀɴᴋ ʏᴏᴜ! 🎉
            """
            bot.send_photo(user_id, DEPOSIT_IMAGE, success_text, reply_markup=main_menu_keyboard())
            
            # Notify admin
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, f"💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ!\nUsᴇʀ: {user_id}\nAᴍᴏᴜɴᴛ: ₹{amount}")
                except:
                    pass
            
            # Clear state
            if user_id in user_states:
                del user_states[user_id]
                
        else:
            bot.answer_callback_query(call.id, 
                "❌ Pᴀʏᴍᴇɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! Pʟᴇᴀsᴇ ᴘᴀʏ ғɪʀsᴛ.", show_alert=True)
            
    except Exception as e:
        print(f"Deposit API error: {e}")
        bot.answer_callback_query(call.id, f"❌ API ᴇʀʀᴏʀ: {str(e)}", show_alert=True)

# Order System
def start_order(call, service_id):
    """Start order process"""
    user_id = call.message.chat.id
    service = get_service_by_id(service_id)
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    user_states[user_id] = {
        "action": "ordering", 
        "service_id": service_id,
        "service": service
    }
    
    price_info = f"💰 {service['price_per_unit']} Points/{service['unit']}"
    
    service_text = f"""
🛒 {service['name']}

{service.get('description', '')}

{price_info}
📊 Mɪɴ: {service['min']} | Mᴀx: {service['max']}

🔗 Sᴇɴᴅ ʏᴏᴜʀ ʟɪɴᴋ:
    """
    
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    
    bot.send_photo(user_id, SERVICE_IMAGE, service_text)
    bot.send_message(user_id, "🌐 Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ:")
    bot.register_next_step_handler(call.message, process_order_link)

def process_order_link(message):
    """Process order link"""
    user_id = message.chat.id
    state = user_states.get(user_id, {})
    
    if state.get("action") != "ordering":
        return
    
    link = message.text.strip()
    if not link.startswith(('http://', 'https://')):
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ʟɪɴᴋ! Usᴇ HTTP/HTTPS.")
        return
    
    state["link"] = link
    user_states[user_id] = state
    
    service = state["service"]
    bot.send_message(user_id, f"🔢 Eɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ:\nMɪɴ: {service['min']} | Mᴀx: {service['max']}")
    bot.register_next_step_handler(message, process_order_quantity)

def process_order_quantity(message):
    """Process order quantity"""
    user_id = message.chat.id
    state = user_states.get(user_id, {})
    
    if state.get("action") != "ordering":
        return
    
    try:
        quantity = int(message.text)
        service = state["service"]
        
        if quantity < service['min'] or quantity > service['max']:
            bot.send_message(user_id, f"❌ Qᴜᴀɴᴛɪᴛʏ ᴍᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ {service['min']} ᴀɴᴅ {service['max']}")
            return
        
        # Calculate cost
        unit = service['unit']
        cost = (quantity // unit) * service['price_per_unit']
        if quantity % unit != 0:
            cost += service['price_per_unit']  # Round up
        
        balance = get_user_balance(user_id)
        if balance < cost:
            bot.send_message(user_id, f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!\nNᴇᴇᴅ: {cost} | Hᴀᴠᴇ: {balance}")
            return
        
        # Create order
        order = create_order(user_id, service['_id'], state["link"], quantity, cost)
        if not order:
            bot.send_message(user_id, "❌ Eʀʀᴏʀ ᴄʀᴇᴀᴛɪɴɢ ᴏʀᴅᴇʀ!")
            return
        
        # Deduct balance
        update_user_balance(user_id, -cost, is_spent=True)
        
        success_text = f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ!

🛒 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: {cost} ᴘᴏɪɴᴛs
🆔 ID: {order['order_id']}

Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ ⏳
        """
        bot.send_photo(user_id, SERVICE_IMAGE, success_text, reply_markup=main_menu_keyboard())
        
        # Notify admin and channel
        notify_text = f"""
🛒 Nᴇᴡ Oʀᴅᴇʀ!

Usᴇʀ: {user_id}
Sᴇʀᴠɪᴄᴇ: {service['name']}
Qᴜᴀɴᴛɪᴛʏ: {quantity}
Oʀᴅᴇʀ ID: {order['order_id']}

Bot Here 🈴: https://t.me/prank_ox_bot
        """
        
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, notify_text)
            except:
                pass
        
        try:
            bot.send_message(CHANNEL_ID, notify_text)
        except:
            pass
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

# Track Order System
def start_track_order(call):
    """Start track order process"""
    user_id = call.message.chat.id
    
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    
    bot.send_message(user_id, "🔍 Pʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ Oʀᴅᴇʀ ID:")
    user_states[user_id] = {"action": "tracking_order"}
    bot.register_next_step_handler(call.message, process_track_order)

def process_track_order(message):
    """Process track order request"""
    user_id = message.chat.id
    order_id = message.text.strip()
    
    order = get_order_by_id(order_id)
    if not order:
        bot.send_message(user_id, "❌ Oʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    status_emoji = {
        "Pending": "⏳",
        "In Progress": "🔄", 
        "Completed": "✅",
        "Cancelled": "❌",
        "Partial": "⚠️",
        "Refunded": "💸"
    }
    
    emoji = status_emoji.get(order['status'], "📊")
    
    track_text = f"""
📦 Oʀᴅᴇʀ Tʀᴀᴄᴋɪɴɢ

🆔 Oʀᴅᴇʀ ID: {order['order_id']}
🛒 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💰 Cᴏsᴛ: {order['cost_points']} ᴘᴏɪɴᴛs
📊 Sᴛᴀᴛᴜs: {emoji} {order['status']}
📅 Cʀᴇᴀᴛᴇᴅ: {order['created_at'].strftime('%Y-%m-%d %H:%M')}
    """
    
    bot.send_message(user_id, track_text, reply_markup=main_menu_keyboard())

# Menu Display Functions
def show_main_menu(call):
    """Show main menu"""
    text = "🏠 Mᴀɪɴ Mᴇɴᴜ - Cʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:"
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(WELCOME_IMAGE, caption=text),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(call.message.chat.id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

def show_categories(call):
    """Show service categories"""
    text = "📱 Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴄᴀᴛᴇɢᴏʀʏ:"
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(SERVICE_IMAGE, caption=text),
            reply_markup=service_category_keyboard()
        )
    except:
        bot.send_photo(call.message.chat.id, SERVICE_IMAGE, text, reply_markup=service_category_keyboard())

def show_services(call, category):
    """Show services for a category"""
    text = f"📋 {category.title()} Sᴇʀᴠɪᴄᴇs:"
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(SERVICE_IMAGE, caption=text),
            reply_markup=services_keyboard(category)
        )
    except:
        bot.send_photo(call.message.chat.id, SERVICE_IMAGE, text, reply_markup=services_keyboard(category))

def show_history(call):
    """Show order history"""
    user_id = call.message.chat.id
    orders = get_user_orders(user_id)
    
    if not orders:
        text = "📭 Nᴏ ᴏʀᴅᴇʀs ʜɪsᴛᴏʀʏ ғᴏᴜɴᴅ."
    else:
        text = "📋 Lᴀsᴛ 5 Oʀᴅᴇʀs:\n\n"
        for order in orders:
            status_emoji = "⏳" if order['status'] == "Pending" else "✅" if order['status'] == "Completed" else "🔄"
            text += f"""🛒 {order['service_name']}
🔢 {order['quantity']} | 💰 {order['cost_points']}ᴘ
🆔 {order['order_id']}
{status_emoji} {order['status']}
📅 {order['created_at'].strftime('%Y-%m-%d %H:%M')}
────────────────
"""
    
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(HISTORY_IMAGE, caption=text),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(call.message.chat.id, HISTORY_IMAGE, text, reply_markup=main_menu_keyboard())

def show_account(call):
    """Show user account"""
    user_id = call.message.chat.id
    user = users_collection.find_one({"user_id": user_id})
    
    if not user:
        user = {
            "balance_points": 0,
            "total_spent_points": 0,
            "total_deposits_points": 0,
            "joined_at": datetime.now()
        }
    
    balance_rs = user.get("balance_points", 0) / 100
    
    text = f"""
👤 Aᴄᴄᴏᴜɴᴛ Iɴғᴏ

💰 Bᴀʟᴀɴᴄᴇ: {user.get('balance_points', 0)} ᴘᴏɪɴᴛs (₹{balance_rs:.2f})
🛒 Tᴏᴛᴀʟ sᴘᴇɴᴛ: {user.get('total_spent_points', 0)} ᴘᴏɪɴᴛs
💳 Tᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛ: {user.get('total_deposits_points', 0)} ᴘᴏɪɴᴛs
📅 Jᴏɪɴᴇᴅ: {user.get('joined_at', datetime.now()).strftime('%Y-%m-%d')}

🆔 Usᴇʀ ID: {user_id}
"""
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(ACCOUNT_IMAGE, caption=text),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(call.message.chat.id, ACCOUNT_IMAGE, text, reply_markup=main_menu_keyboard())

def show_refer(call):
    """Show referral information"""
    user_id = call.message.chat.id
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    text = f"""
👥 Rᴇғᴇʀ & Eᴀʀɴ

🔗 Rᴇғᴇʀʀᴀʟ ʟɪɴᴋ:
{ref_link}

🎯 Yᴏᴜ ɢᴇᴛ: 100 ᴘᴏɪɴᴛs ᴘᴇʀ ʀᴇғᴇʀʀᴀʟ
👥 Fʀɪᴇɴᴅ ɢᴇᴛs: 50 ᴘᴏɪɴᴛs ʙᴏɴᴜs
"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📤 Sʜᴀʀᴇ Lɪɴᴋ", url=f"tg://msg_url?text=Join%20this%20SMM%20bot:%20{ref_link}"))
    markup.add(InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu"))
    
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(REFER_IMAGE, caption=text),
            reply_markup=markup
        )
    except:
        bot.send_photo(call.message.chat.id, REFER_IMAGE, text, reply_markup=markup)

def show_support(call):
    """Show support information"""
    text = """📞 Sᴜᴘᴘᴏʀᴛ

ɪғ ʏᴏᴜ ʜᴀᴠᴇ ᴀɴʏ ᴘʀᴏʙʟᴇᴍ (Oʀᴅᴇʀ ʀᴇʟᴀᴛᴇᴅ / Dᴇᴘᴏsɪᴛ ʀᴇʟᴀᴛᴇᴅ / Oᴛʜᴇʀs)

Wᴇ'ʀᴇ ʜᴇʀᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ! 🤝
"""
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(WELCOME_IMAGE, caption=text),
            reply_markup=support_keyboard()
        )
    except:
        bot.send_photo(call.message.chat.id, WELCOME_IMAGE, text, reply_markup=support_keyboard())

def show_stats(call):
    """Show bot statistics"""
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    total_points = sum(order['cost_points'] for order in orders_collection.find())
    
    text = f"""
📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs

👥 Tᴏᴛᴀʟ ᴜsᴇʀs: {total_users}
🛒 Tᴏᴛᴀʟ ᴏʀᴅᴇʀs: {total_orders}
💰 Pᴏɪɴᴛs sᴘᴇɴᴛ: {total_points}

🚀 Sʏsᴛᴇᴍ Oᴘᴇʀᴀᴛɪᴏɴᴀʟ
"""
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(WELCOME_IMAGE, caption=text),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(call.message.chat.id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

# Admin Commands
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """Admin panel"""
    if message.chat.id not in ADMIN_IDS:
        return
    
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    total_deposits = sum(user.get('total_deposits_points', 0) for user in users_collection.find()) / 100
    
    text = f"""
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

👥 Usᴇʀs: {total_users}
🛒 Oʀᴅᴇʀs: {total_orders}
💰 Tᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛs: ₹{total_deposits:.2f}

Cᴏᴍᴍᴀɴᴅs:
/addbalance <user_id> <amount> - Aᴅᴅ ʙᴀʟᴀɴᴄᴇ
/broadcast <message> - Sᴇɴᴅ ᴛᴏ ᴀʟʟ ᴜsᴇʀs
"""
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    """Add balance to user"""
    if message.chat.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, "❌ Usᴇ: /addbalance <user_id> <amount>")
            return
        
        user_id = int(parts[1])
        amount = float(parts[2])
        
        # Convert ₹ to points if amount > 100 (assuming large amounts are in ₹)
        if amount > 100:
            points = int(amount * 100)
            amount_str = f"₹{amount} ({points} ᴘᴏɪɴᴛs)"
        else:
            points = int(amount)
            amount_str = f"{points} ᴘᴏɪɴᴛs"
        
        new_balance = update_user_balance(user_id, points, is_deposit=True)
        
        bot.send_message(message.chat.id, f"✅ Aᴅᴅᴇᴅ {amount_str} ᴛᴏ {user_id}\nNᴇᴡ ʙᴀʟᴀɴᴄᴇ: {new_balance}")
        bot.send_message(user_id, f"🎁 Aᴅᴍɪɴ ᴀᴅᴅᴇᴅ {amount_str} ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ!")
        
        log_admin_action(message.chat.id, "add_balance", f"User: {user_id}, Amount: {amount_str}")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Eʀʀᴏʀ: {str(e)}")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    """Broadcast message to all users"""
    if message.chat.id not in ADMIN_IDS:
        return
    
    broadcast_text = message.text.replace('/broadcast', '').strip()
    if not broadcast_text:
        bot.send_message(message.chat.id, "❌ Usᴇ: /broadcast <message>")
        return
    
    users = users_collection.find({})
    success = 0
    
    for user in users:
        try:
            bot.send_message(user['user_id'], f"📢 Aɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ:\n\n{broadcast_text}")
            success += 1
            time.sleep(0.1)  # Rate limiting
        except:
            continue
    
    bot.send_message(message.chat.id, f"✅ Bʀᴏᴀᴅᴄᴀsᴛ sᴇɴᴛ ᴛᴏ {success} ᴜsᴇʀs")
    log_admin_action(message.chat.id, "broadcast", f"Message: {broadcast_text[:50]}...")

# Auto-Check Refund Worker (Simplified without schedule)
def auto_check_orders():
    """Background worker to check order status and process refunds"""
    while True:
        try:
            # Find orders that need checking
            check_time = datetime.now() - timedelta(minutes=30)
            orders = orders_collection.find({
                "status": {"$in": ["Pending", "In Progress"]},
                "last_check": {"$lt": check_time}
            })
            
            for order in orders:
                # Check if already processed for refund
                if processed_refunds_collection.find_one({"order_id": order["order_id"]}):
                    continue
                
                # Simulate API call to check status
                status = check_order_status(order)
                
                if status in ["Cancelled", "Partial"]:
                    # Process refund
                    refund_points = calculate_refund(order, status)
                    if refund_points > 0:
                        update_user_balance(order["user_id"], refund_points)
                        
                        # Update order status
                        orders_collection.update_one(
                            {"_id": order["_id"]},
                            {"$set": {
                                "status": "Refunded",
                                "refunded_at": datetime.now(),
                                "refunded_points": refund_points
                            }}
                        )
                        
                        # Mark as processed
                        processed_refunds_collection.insert_one({
                            "order_id": order["order_id"],
                            "processed_at": datetime.now()
                        })
                        
                        # Notify user
                        try:
                            bot.send_message(
                                order["user_id"],
                                f"💸 Oʀᴅᴇʀ {order['order_id']} ʀᴇғᴜɴᴅᴇᴅ!\n"
                                f"Rᴇғᴜɴᴅᴇᴅ: {refund_points} ᴘᴏɪɴᴛs\n"
                                f"Rᴇᴀsᴏɴ: {status}"
                            )
                        except:
                            pass
                
                # Update last check time
                orders_collection.update_one(
                    {"_id": order["_id"]},
                    {"$set": {"last_check": datetime.now()}}
                )
            
            time.sleep(1800)  # Sleep for 30 minutes
            
        except Exception as e:
            print(f"Auto-check error: {e}")
            time.sleep(300)  # Sleep 5 minutes on error

def check_order_status(order):
    """Check order status with SMM provider"""
    # Placeholder - implement actual API call
    statuses = ["Completed", "In Progress", "Pending", "Cancelled"]
    return random.choice(statuses)

def calculate_refund(order, status):
    """Calculate refund amount based on status"""
    if status == "Cancelled":
        return order["cost_points"]  # Full refund
    elif status == "Partial":
        return order["cost_points"] // 2  # 50% refund for demo
    return 0

# Text Message Handler
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Handle text messages"""
    text = message.text.lower()
    
    if text in ['/start', 'start', 'menu', 'restart']:
        send_welcome(message)
    elif text in ['/deposit', 'deposit']:
        class MockCall:
            def __init__(self): 
                self.message = message
                self.id = "mock"
        start_deposit(MockCall())
    else:
        bot.send_photo(message.chat.id, WELCOME_IMAGE, 
                      "❓ Uɴᴋɴᴏᴡɴ ᴄᴏᴍᴍᴀɴᴅ\n\nUsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴏʀ /start",
                      reply_markup=main_menu_keyboard())

# Initialize Sample Services
def initialize_sample_services():
    """Insert sample services if none exist"""
    if services_collection.count_documents({}) == 0:
        sample_services = [
            {
                "category": "instagram",
                "name": "Instagram Followers",
                "description": "⚡ Hɪɢʜ-Qᴜᴀʟɪᴛʏ Rᴇᴀʟ Fᴏʟʟᴏᴡᴇʀs ⚡",
                "service_id": "4679",
                "unit": 100,
                "price_per_unit": 10,
                "min": 100,
                "max": 300000,
                "active": True
            },
            {
                "category": "instagram",
                "name": "Instagram Likes", 
                "description": "✨ Fᴀsᴛ Lɪᴋᴇs Dᴇʟɪᴠᴇʀʏ ✨",
                "service_id": "4961",
                "unit": 100,
                "price_per_unit": 5,
                "min": 100,
                "max": 100000,
                "active": True
            },
            {
                "category": "youtube",
                "name": "YouTube Subscribers",
                "description": "🎥 Hɪɢʜ-Qᴜᴀʟɪᴛʏ Sᴜʙsᴄʀɪʙᴇʀs 🎥",
                "service_id": "5678", 
                "unit": 100,
                "price_per_unit": 15,
                "min": 100,
                "max": 50000,
                "active": True
            }
        ]
        
        services_collection.insert_many(sample_services)
        print("✅ Sample services inserted")

# Start Background Workers
def start_workers():
    """Start background workers"""
    worker_thread = threading.Thread(target=auto_check_orders, daemon=True)
    worker_thread.start()
    print("✅ Background workers started")

# Main Execution
if __name__ == "__main__":
    print("🚀 Bot starting...")
    
    # Initialize sample data
    initialize_sample_services()
    
    # Start background workers
    start_workers()
    
    # Start bot polling
    print(f"🔗 Bot URL: t.me/{bot.get_me().username}")
    
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(10)
