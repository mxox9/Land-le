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

# Initialize bot with better error handling
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# MongoDB connection with improved error handling
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.smm_bot
    users_collection = db.users
    services_collection = db.services
    orders_collection = db.orders
    deposits_collection = db.deposits
    admin_logs_collection = db.admin_logs
    processed_refunds_collection = db.processed_refunds
    config_collection = db.config
    settings_collection = db.settings
    # Test connection
    client.admin.command('ismaster')
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

# Initialize settings
if not settings_collection.find_one({"_id": "bot_settings"}):
    settings_collection.insert_one({
        "_id": "bot_settings",
        "accepting_orders": True
    })

# User states for conversation flow
user_states = {}
admin_states = {}

# Image URLs
WELCOME_IMAGE = "https://t.me/prooflelo1/16"
SERVICE_IMAGE = "https://t.me/prooflelo1/16"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/16"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/16"
HISTORY_IMAGE = "https://t.me/prooflelo1/16"
REFER_IMAGE = "https://t.me/prooflelo1/16"
ADMIN_IMAGE = "https://t.me/prooflelo1/16"

# Helper Functions
def log_admin_action(admin_id, action, details):
    """Log admin actions to database"""
    admin_logs_collection.insert_one({
        "admin_id": admin_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now()
    })

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

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

def is_bot_accepting_orders():
    """Check if bot is accepting orders"""
    settings = settings_collection.find_one({"_id": "bot_settings"})
    return settings.get("accepting_orders", True) if settings else True

def set_bot_accepting_orders(status):
    """Set bot accepting orders status"""
    settings_collection.update_one(
        {"_id": "bot_settings"},
        {"$set": {"accepting_orders": status}},
        upsert=True
    )

# Admin Keyboard Builders
def admin_main_keyboard():
    """Admin main menu keyboard"""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📦 Manage Services", callback_data="admin_manage_services"),
        InlineKeyboardButton("💰 Balance Control", callback_data="admin_balance_control")
    )
    markup.add(
        InlineKeyboardButton("👥 User Control", callback_data="admin_user_control"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )
    markup.add(
        InlineKeyboardButton("⚙️ Bot Control", callback_data="admin_bot_control"),
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats")
    )
    markup.add(InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu"))
    return markup

def admin_services_keyboard():
    """Admin services management keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Add Service", callback_data="admin_add_service"))
    markup.add(InlineKeyboardButton("✏️ Edit Service", callback_data="admin_edit_service"))
    markup.add(InlineKeyboardButton("❌ Delete Service", callback_data="admin_delete_service"))
    markup.add(InlineKeyboardButton("🔙 Admin Menu", callback_data="admin_menu"))
    return markup

def admin_balance_keyboard():
    """Admin balance control keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Add Balance", callback_data="admin_add_balance"))
    markup.add(InlineKeyboardButton("➖ Deduct Balance", callback_data="admin_deduct_balance"))
    markup.add(InlineKeyboardButton("🔙 Admin Menu", callback_data="admin_menu"))
    return markup

def admin_user_keyboard():
    """Admin user control keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user"))
    markup.add(InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_user"))
    markup.add(InlineKeyboardButton("🔙 Admin Menu", callback_data="admin_menu"))
    return markup

def admin_bot_control_keyboard():
    """Admin bot control keyboard"""
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🟢 Turn Bot ON", callback_data="admin_bot_on"))
    markup.add(InlineKeyboardButton("🔴 Turn Bot OFF", callback_data="admin_bot_off"))
    markup.add(InlineKeyboardButton(f"📊 Current Status: {bot_status}", callback_data="admin_bot_status"))
    markup.add(InlineKeyboardButton("🔙 Admin Menu", callback_data="admin_menu"))
    return markup

def service_categories_keyboard():
    """Service categories selection keyboard for admin"""
    markup = InlineKeyboardMarkup()
    categories = ["Instagram", "YouTube", "Telegram", "Facebook", "Other"]
    for category in categories:
        markup.add(InlineKeyboardButton(category, callback_data=f"admin_category_{category.lower()}"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="admin_manage_services"))
    return markup

def services_list_keyboard(category, action):
    """Services list for a category with action"""
    markup = InlineKeyboardMarkup()
    services = list(services_collection.find({"category": category.lower(), "active": True}))
    
    for service in services:
        service_name = service['name'][:30]  # Limit name length
        markup.add(InlineKeyboardButton(
            service_name, 
            callback_data=f"admin_{action}_{service['_id']}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Back", callback_data=f"admin_{action}_back"))
    return markup

def confirm_delete_keyboard(service_id):
    """Confirmation keyboard for service deletion"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Yes, Delete", callback_data=f"admin_confirm_delete_{service_id}"))
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="admin_manage_services"))
    return markup

# Main Menu Keyboard Builders
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

# Admin Message Handlers
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """Admin panel command"""
    user_id = message.chat.id
    
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.")
        return
    
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    total_deposits = sum(user.get('total_deposits_points', 0) for user in users_collection.find()) / 100
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    
    text = f"""
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

👥 Usᴇʀs: {total_users}
🛒 Oʀᴅᴇʀs: {total_orders}
💰 Tᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛs: ₹{total_deposits:.2f}
⚙️ Bᴏᴛ Sᴛᴀᴛᴜs: {bot_status}

Cʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:
    """
    
    bot.send_photo(user_id, ADMIN_IMAGE, text, reply_markup=admin_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callbacks(call):
    """Handle admin callback queries"""
    user_id = call.message.chat.id
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "🚫 Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.", show_alert=True)
        return
    
    try:
        if call.data == "admin_menu":
            show_admin_menu(call)
        
        elif call.data == "admin_manage_services":
            show_admin_services_menu(call)
        
        elif call.data == "admin_balance_control":
            show_admin_balance_menu(call)
        
        elif call.data == "admin_user_control":
            show_admin_user_menu(call)
        
        elif call.data == "admin_broadcast":
            start_admin_broadcast(call)
        
        elif call.data == "admin_bot_control":
            show_admin_bot_control(call)
        
        elif call.data == "admin_stats":
            show_admin_stats(call)
        
        elif call.data == "admin_add_service":
            start_add_service(call)
        
        elif call.data == "admin_edit_service":
            show_service_categories(call, "edit")
        
        elif call.data == "admin_delete_service":
            show_service_categories(call, "delete")
        
        elif call.data.startswith("admin_category_"):
            category = call.data.replace("admin_category_", "")
            action = admin_states.get(user_id, {}).get("action")
            if action == "edit":
                show_services_for_edit(call, category)
            elif action == "delete":
                show_services_for_delete(call, category)
        
        elif call.data.startswith("admin_edit_"):
            service_id = call.data.replace("admin_edit_", "")
            start_edit_service(call, service_id)
        
        elif call.data.startswith("admin_delete_"):
            service_id = call.data.replace("admin_delete_", "")
            confirm_delete_service(call, service_id)
        
        elif call.data.startswith("admin_confirm_delete_"):
            service_id = call.data.replace("admin_confirm_delete_", "")
            delete_service(call, service_id)
        
        elif call.data == "admin_add_balance":
            start_add_balance(call)
        
        elif call.data == "admin_deduct_balance":
            start_deduct_balance(call)
        
        elif call.data == "admin_ban_user":
            start_ban_user(call)
        
        elif call.data == "admin_unban_user":
            start_unban_user(call)
        
        elif call.data == "admin_bot_on":
            set_bot_status(call, True)
        
        elif call.data == "admin_bot_off":
            set_bot_status(call, False)
        
        elif call.data == "admin_bot_status":
            show_bot_status(call)
        
        elif call.data.endswith("_back"):
            handle_admin_back(call)
        
        elif call.data.startswith('admin_confirm_'):
            handle_admin_confirmations(call)
            
    except Exception as e:
        print(f"Admin callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!")

# Admin Service Management Functions
def start_add_service(call):
    """Start add service process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "adding_service", "step": "category"}
    
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    
    text = "📦 Aᴅᴅ Nᴇᴡ Sᴇʀᴠɪᴄᴇ\n\nSᴇʟᴇᴄᴛ ᴄᴀᴛᴇɢᴏʀʏ:"
    bot.send_message(user_id, text, reply_markup=service_categories_keyboard())

def process_add_service_category(message):
    """Process service category selection"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    category = message.text.strip()
    admin_states[user_id]["category"] = category
    admin_states[user_id]["step"] = "name"
    
    bot.send_message(user_id, "📝 Eɴᴛᴇʀ sᴇʀᴠɪᴄᴇ ɴᴀᴍᴇ:")

def process_add_service_name(message):
    """Process service name"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    admin_states[user_id]["name"] = message.text.strip()
    admin_states[user_id]["step"] = "description"
    
    bot.send_message(user_id, "📄 Eɴᴛᴇʀ sᴇʀᴠɪᴄᴇ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:")

def process_add_service_description(message):
    """Process service description"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    admin_states[user_id]["description"] = message.text.strip()
    admin_states[user_id]["step"] = "min_quantity"
    
    bot.send_message(user_id, "🔢 Eɴᴛᴇʀ ᴍɪɴɪᴍᴜᴍ ǫᴜᴀɴᴛɪᴛʏ:")

def process_add_service_min_quantity(message):
    """Process minimum quantity"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    try:
        min_quantity = int(message.text.strip())
        admin_states[user_id]["min_quantity"] = min_quantity
        admin_states[user_id]["step"] = "max_quantity"
        
        bot.send_message(user_id, "🔢 Eɴᴛᴇʀ ᴍᴀxɪᴍᴜᴍ ǫᴜᴀɴᴛɪᴛʏ:")
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def process_add_service_max_quantity(message):
    """Process maximum quantity"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    try:
        max_quantity = int(message.text.strip())
        admin_states[user_id]["max_quantity"] = max_quantity
        admin_states[user_id]["step"] = "unit"
        
        bot.send_message(user_id, "📏 Eɴᴛᴇʀ ᴜɴɪᴛ (100 ᴏʀ 1000):")
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def process_add_service_unit(message):
    """Process service unit"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    try:
        unit = int(message.text.strip())
        if unit not in [100, 1000]:
            bot.send_message(user_id, "❌ Uɴɪᴛ ᴍᴜsᴛ ʙᴇ 100 ᴏʀ 1000!")
            return
        
        admin_states[user_id]["unit"] = unit
        admin_states[user_id]["step"] = "price"
        
        bot.send_message(user_id, "💰 Eɴᴛᴇʀ ᴘʀɪᴄᴇ ᴘᴇʀ ᴜɴɪᴛ (ᴘᴏɪɴᴛs):")
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴜɴɪᴛ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def process_add_service_price(message):
    """Process service price"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    try:
        price = int(message.text.strip())
        admin_states[user_id]["price"] = price
        admin_states[user_id]["step"] = "service_id"
        
        bot.send_message(user_id, "🆔 Eɴᴛᴇʀ sᴇʀᴠɪᴄᴇ ID (API sᴇʀᴠɪᴄᴇ ɪᴅ):")
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴘʀɪᴄᴇ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def process_add_service_id(message):
    """Process service ID and save service"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    service_id = message.text.strip()
    data = admin_states[user_id]
    
    # Save service to database
    service_data = {
        "category": data["category"].lower(),
        "name": data["name"],
        "description": data["description"],
        "min": data["min_quantity"],
        "max": data["max_quantity"],
        "unit": data["unit"],
        "price_per_unit": data["price"],
        "service_id": service_id,
        "active": True,
        "created_at": datetime.now()
    }
    
    services_collection.insert_one(service_data)
    
    # Clear state
    del admin_states[user_id]
    
    # Send confirmation
    text = f"""
✅ Sᴇʀᴠɪᴄᴇ Aᴅᴅᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

📦 Cᴀᴛᴇɢᴏʀʏ: {data['category']}
📝 Nᴀᴍᴇ: {data['name']}
📄 Dᴇsᴄʀɪᴘᴛɪᴏɴ: {data['description']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {data['min_quantity']}-{data['max_quantity']}
📏 Uɴɪᴛ: {data['unit']}
💰 Pʀɪᴄᴇ: {data['price']} ᴘᴏɪɴᴛs/ᴜɴɪᴛ
🆔 Sᴇʀᴠɪᴄᴇ ID: {service_id}
    """
    
    bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
    log_admin_action(user_id, "add_service", f"Service: {data['name']}")

def show_service_categories(call, action):
    """Show service categories for edit/delete"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": action}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="📦 Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴄᴀᴛᴇɢᴏʀʏ:",
            reply_markup=service_categories_keyboard()
        )
    except:
        bot.send_message(user_id, "📦 Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴄᴀᴛᴇɢᴏʀʏ:", reply_markup=service_categories_keyboard())

def show_services_for_edit(call, category):
    """Show services for editing"""
    user_id = call.message.chat.id
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=f"✏️ Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴇᴅɪᴛ ({category.title()}):",
            reply_markup=services_list_keyboard(category, "edit")
        )
    except:
        bot.send_message(user_id, f"✏️ Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴇᴅɪᴛ ({category.title()}):", 
                        reply_markup=services_list_keyboard(category, "edit"))

def show_services_for_delete(call, category):
    """Show services for deletion"""
    user_id = call.message.chat.id
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=f"❌ Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴅᴇʟᴇᴛᴇ ({category.title()}):",
            reply_markup=services_list_keyboard(category, "delete")
        )
    except:
        bot.send_message(user_id, f"❌ Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴅᴇʟᴇᴛᴇ ({category.title()}):", 
                        reply_markup=services_list_keyboard(category, "delete"))

def start_edit_service(call, service_id):
    """Start editing a service"""
    user_id = call.message.chat.id
    service = services_collection.find_one({"_id": ObjectId(service_id)})
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    admin_states[user_id] = {
        "action": "editing_service",
        "service_id": service_id,
        "service": service,
        "step": "field"
    }
    
    text = f"""
✏️ Eᴅɪᴛ Sᴇʀᴠɪᴄᴇ: {service['name']}

Sᴇʟᴇᴄᴛ ғɪᴇʟᴅ ᴛᴏ ᴇᴅɪᴛ:
1. 📝 Nᴀᴍᴇ
2. 📄 Dᴇsᴄʀɪᴘᴛɪᴏɴ  
3. 🔢 Mɪɴ Qᴜᴀɴᴛɪᴛʏ
4. 🔢 Mᴀx Qᴜᴀɴᴛɪᴛʏ
5. 📏 Uɴɪᴛ
6. 💰 Pʀɪᴄᴇ
7. 🆔 Sᴇʀᴠɪᴄᴇ ID

Rᴇᴘʟʏ ᴡɪᴛʜ ᴛʜᴇ ɴᴜᴍʙᴇʀ (1-7):
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text
        )
    except:
        bot.send_message(user_id, text)
    
    bot.register_next_step_handler(call.message, process_edit_service_field)

def process_edit_service_field(message):
    """Process which field to edit"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "editing_service":
        return
    
    try:
        field_num = int(message.text.strip())
        field_map = {
            1: "name", 2: "description", 3: "min", 
            4: "max", 5: "unit", 6: "price_per_unit", 7: "service_id"
        }
        
        if field_num not in field_map:
            bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ғɪᴇʟᴅ ɴᴜᴍʙᴇʀ! Usᴇ 1-7.")
            return
        
        admin_states[user_id]["edit_field"] = field_map[field_num]
        admin_states[user_id]["step"] = "new_value"
        
        field_names = {
            "name": "ɴᴀᴍᴇ", "description": "ᴅᴇsᴄʀɪᴘᴛɪᴏɴ", 
            "min": "ᴍɪɴɪᴍᴜᴍ ǫᴜᴀɴᴛɪᴛʏ", "max": "ᴍᴀxɪᴍᴜᴍ ǫᴜᴀɴᴛɪᴛʏ",
            "unit": "ᴜɴɪᴛ", "price_per_unit": "ᴘʀɪᴄᴇ ᴘᴇʀ ᴜɴɪᴛ", 
            "service_id": "sᴇʀᴠɪᴄᴇ ID"
        }
        
        bot.send_message(user_id, f"📝 Eɴᴛᴇʀ ɴᴇᴡ {field_names[field_map[field_num]]}:")
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ! Usᴇ ɴᴜᴍʙᴇʀs 1-7.")

def process_edit_service_value(message):
    """Process new value for service field"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "editing_service":
        return
    
    data = admin_states[user_id]
    new_value = message.text.strip()
    field = data["edit_field"]
    
    # Validate numeric fields
    if field in ["min", "max", "unit", "price_per_unit"]:
        try:
            new_value = int(new_value)
        except ValueError:
            bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴠᴀʟᴜᴇ!")
            return
    
    # Update service in database
    services_collection.update_one(
        {"_id": ObjectId(data["service_id"])},
        {"$set": {field: new_value}}
    )
    
    # Clear state
    del admin_states[user_id]
    
    bot.send_message(user_id, f"✅ Sᴇʀᴠɪᴄᴇ {field} ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!", 
                    reply_markup=admin_main_keyboard())
    
    log_admin_action(user_id, "edit_service", f"Service ID: {data['service_id']}, Field: {field}")

def confirm_delete_service(call, service_id):
    """Confirm service deletion"""
    user_id = call.message.chat.id
    service = services_collection.find_one({"_id": ObjectId(service_id)})
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    text = f"""
❌ Cᴏɴғɪʀᴍ Dᴇʟᴇᴛɪᴏɴ

Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜɪs sᴇʀᴠɪᴄᴇ?

📦 Sᴇʀᴠɪᴄᴇ: {service['name']}
📝 Cᴀᴛᴇɢᴏʀʏ: {service['category']}
💰 Pʀɪᴄᴇ: {service['price_per_unit']} ᴘᴏɪɴᴛs

Tʜɪs ᴀᴄᴛɪᴏɴ ᴄᴀɴɴᴏᴛ ʙᴇ ᴜɴᴅᴏɴᴇ!
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=confirm_delete_keyboard(service_id)
        )
    except:
        bot.send_message(user_id, text, reply_markup=confirm_delete_keyboard(service_id))

def delete_service(call, service_id):
    """Delete service from database"""
    user_id = call.message.chat.id
    service = services_collection.find_one({"_id": ObjectId(service_id)})
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    service_name = service['name']
    services_collection.delete_one({"_id": ObjectId(service_id)})
    
    text = f"✅ Sᴇʀᴠɪᴄᴇ '{service_name}' ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!"
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=admin_main_keyboard()
        )
    except:
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
    
    log_admin_action(user_id, "delete_service", f"Service: {service_name}")

def show_admin_services_menu(call):
    """Show admin services management menu"""
    user_id = call.message.chat.id
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="📦 Sᴇʀᴠɪᴄᴇs Mᴀɴᴀɢᴇᴍᴇɴᴛ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:",
            reply_markup=admin_services_keyboard()
        )
    except:
        bot.send_message(user_id, "📦 Sᴇʀᴠɪᴄᴇs Mᴀɴᴀɢᴇᴍᴇɴᴛ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:", 
                        reply_markup=admin_services_keyboard())

def show_admin_balance_menu(call):
    """Show admin balance control menu"""
    user_id = call.message.chat.id
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:",
            reply_markup=admin_balance_keyboard()
        )
    except:
        bot.send_message(user_id, "💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:", 
                        reply_markup=admin_balance_keyboard())

def show_admin_user_menu(call):
    """Show admin user control menu"""
    user_id = call.message.chat.id
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="👥 Usᴇʀ Cᴏɴᴛʀᴏʟ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:",
            reply_markup=admin_user_keyboard()
        )
    except:
        bot.send_message(user_id, "👥 Usᴇʀ Cᴏɴᴛʀᴏʟ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:", 
                        reply_markup=admin_user_keyboard())

def show_admin_bot_control(call):
    """Show admin bot control menu"""
    user_id = call.message.chat.id
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    
    text = f"""
⚙️ Bᴏᴛ Cᴏɴᴛʀᴏʟ

Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: {bot_status}

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=admin_bot_control_keyboard()
        )
    except:
        bot.send_message(user_id, text, reply_markup=admin_bot_control_keyboard())

def show_admin_stats(call):
    """Show admin statistics"""
    user_id = call.message.chat.id
    
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    total_deposits = sum(user.get('total_deposits_points', 0) for user in users_collection.find()) / 100
    total_spent = sum(user.get('total_spent_points', 0) for user in users_collection.find()) / 100
    active_services = services_collection.count_documents({"active": True})
    
    text = f"""
📊 Aᴅᴍɪɴ Sᴛᴀᴛɪsᴛɪᴄs

👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
📦 Aᴄᴛɪᴠᴇ Sᴇʀᴠɪᴄᴇs: {active_services}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposits:.2f}
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{total_spent:.2f}
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=admin_main_keyboard()
        )
    except:
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())

def start_admin_broadcast(call):
    """Start broadcast process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "broadcasting", "step": "message"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="📢 Bʀᴏᴀᴅᴄᴀsᴛ\n\nSᴇɴᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs:"
        )
    except:
        bot.send_message(user_id, "📢 Bʀᴏᴀᴅᴄᴀsᴛ\n\nSᴇɴᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs:")

def process_broadcast_message(message):
    """Process broadcast message"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "broadcasting":
        return
    
    broadcast_message = message.text
    admin_states[user_id]["broadcast_message"] = broadcast_message
    admin_states[user_id]["step"] = "confirm"
    
    text = f"""
📢 Bʀᴏᴀᴅᴄᴀsᴛ Cᴏɴғɪʀᴍᴀᴛɪᴏɴ

Mᴇssᴀɢᴇ:
{broadcast_message}

Tʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ sᴇɴᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs. Cᴏɴᴛɪɴᴜᴇ?
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Yes, Send", callback_data="admin_confirm_broadcast"))
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="admin_menu"))
    
    bot.send_message(user_id, text, reply_markup=markup)

def send_broadcast(admin_id, message_text):
    """Send broadcast to all users"""
    users = users_collection.find({})
    success_count = 0
    fail_count = 0
    
    for user in users:
        try:
            bot.send_message(user["user_id"], f"📢 Aɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ:\n\n{message_text}")
            success_count += 1
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Broadcast failed for {user['user_id']}: {e}")
            fail_count += 1
    
    # Send report to admin
    report = f"""
📢 Bʀᴏᴀᴅᴄᴀsᴛ Rᴇᴘᴏʀᴛ

✅ Sᴜᴄᴄᴇssғᴜʟ: {success_count}
❌ Fᴀɪʟᴇᴅ: {fail_count}
📊 Tᴏᴛᴀʟ: {success_count + fail_count}
    """
    
    bot.send_message(admin_id, report)
    log_admin_action(admin_id, "broadcast", f"Sent to {success_count} users")

def start_add_balance(call):
    """Start add balance process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "adding_balance", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="💰 Aᴅᴅ Bᴀʟᴀɴᴄᴇ\n\nSᴇɴᴅ ᴛʜᴇ Usᴇʀ ID:"
        )
    except:
        bot.send_message(user_id, "💰 Aᴅᴅ Bᴀʟᴀɴᴄᴇ\n\nSᴇɴᴅ ᴛʜᴇ Usᴇʀ ID:")

def process_add_balance_user_id(message):
    """Process user ID for adding balance"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_balance":
        return
    
    try:
        target_user_id = int(message.text.strip())
        admin_states[user_id]["target_user_id"] = target_user_id
        admin_states[user_id]["step"] = "amount"
        
        bot.send_message(user_id, "💰 Eɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴀᴅᴅ (ɪɴ ᴘᴏɪɴᴛs):")
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def process_add_balance_amount(message):
    """Process amount to add"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_balance":
        return
    
    try:
        amount = int(message.text.strip())
        target_user_id = admin_states[user_id]["target_user_id"]
        
        # Add balance
        new_balance = update_user_balance(target_user_id, amount, is_deposit=True)
        
        # Clear state
        del admin_states[user_id]
        
        text = f"""
✅ Bᴀʟᴀɴᴄᴇ Aᴅᴅᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
💰 Aᴅᴅᴇᴅ: {amount} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs
        """
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        log_admin_action(user_id, "add_balance", f"User: {target_user_id}, Amount: {amount}")
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def start_deduct_balance(call):
    """Start deduct balance process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "deducting_balance", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="💰 Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ\n\nSᴇɴᴅ ᴛʜᴇ Usᴇʀ ID:"
        )
    except:
        bot.send_message(user_id, "💰 Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ\n\nSᴇɴᴅ ᴛʜᴇ Usᴇʀ ID:")

def process_deduct_balance_user_id(message):
    """Process user ID for deducting balance"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "deducting_balance":
        return
    
    try:
        target_user_id = int(message.text.strip())
        admin_states[user_id]["target_user_id"] = target_user_id
        admin_states[user_id]["step"] = "amount"
        
        bot.send_message(user_id, "💰 Eɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴅᴇᴅᴜᴄᴛ (ɪɴ ᴘᴏɪɴᴛs):")
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def process_deduct_balance_amount(message):
    """Process amount to deduct"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "deducting_balance":
        return
    
    try:
        amount = int(message.text.strip())
        target_user_id = admin_states[user_id]["target_user_id"]
        
        # Check if user has sufficient balance
        current_balance = get_user_balance(target_user_id)
        if current_balance < amount:
            bot.send_message(user_id, f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ! Usᴇʀ ʜᴀs ᴏɴʟʏ {current_balance} ᴘᴏɪɴᴛs.")
            return
        
        # Deduct balance
        new_balance = update_user_balance(target_user_id, -amount, is_spent=True)
        
        # Clear state
        del admin_states[user_id]
        
        text = f"""
✅ Bᴀʟᴀɴᴄᴇ Dᴇᴅᴜᴄᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
💰 Dᴇᴅᴜᴄᴛᴇᴅ: {amount} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs
        """
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        log_admin_action(user_id, "deduct_balance", f"User: {target_user_id}, Amount: {amount}")
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def start_ban_user(call):
    """Start ban user process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "banning_user", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="🚫 Bᴀɴ Usᴇʀ\n\nSᴇɴᴅ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ʙᴀɴ:"
        )
    except:
        bot.send_message(user_id, "🚫 Bᴀɴ Usᴇʀ\n\nSᴇɴᴅ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ʙᴀɴ:")

def process_ban_user(message):
    """Process user ban"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "banning_user":
        return
    
    try:
        target_user_id = int(message.text.strip())
        
        # Ban user
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"banned": True}},
            upsert=True
        )
        
        # Clear state
        del admin_states[user_id]
        
        text = f"""
✅ Usᴇʀ Bᴀɴɴᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
🚫 Sᴛᴀᴛᴜs: Bᴀɴɴᴇᴅ
        """
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        log_admin_action(user_id, "ban_user", f"User: {target_user_id}")
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def start_unban_user(call):
    """Start unban user process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "unbanning_user", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="✅ Uɴʙᴀɴ Usᴇʀ\n\nSᴇɴᴅ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ᴜɴʙᴀɴ:"
        )
    except:
        bot.send_message(user_id, "✅ Uɴʙᴀɴ Usᴇʀ\n\nSᴇɴᴅ ᴛʜᴇ Usᴇʀ ID ᴛᴏ ᴜɴʙᴀɴ:")

def process_unban_user(message):
    """Process user unban"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "unbanning_user":
        return
    
    try:
        target_user_id = int(message.text.strip())
        
        # Unban user
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"banned": False}}
        )
        
        # Clear state
        del admin_states[user_id]
        
        text = f"""
✅ Usᴇʀ Uɴʙᴀɴɴᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
✅ Sᴛᴀᴛᴜs: Aᴄᴛɪᴠᴇ
        """
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        log_admin_action(user_id, "unban_user", f"User: {target_user_id}")
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def set_bot_status(call, status):
    """Set bot accepting orders status"""
    user_id = call.message.chat.id
    set_bot_accepting_orders(status)
    
    status_text = "🟢 ON" if status else "🔴 OFF"
    text = f"✅ Bᴏᴛ sᴛᴀᴛᴜs sᴇᴛ ᴛᴏ: {status_text}"
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=admin_main_keyboard()
        )
    except:
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
    
    log_admin_action(user_id, "set_bot_status", f"Status: {status_text}")

def show_bot_status(call):
    """Show current bot status"""
    user_id = call.message.chat.id
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    
    text = f"⚙️ Cᴜʀʀᴇɴᴛ Bᴏᴛ Sᴛᴀᴛᴜs: {bot_status}"
    
    bot.answer_callback_query(call.id, text, show_alert=True)

def handle_admin_back(call):
    """Handle admin back navigation"""
    user_id = call.message.chat.id
    
    if call.data == "admin_manage_services_back":
        show_admin_services_menu(call)
    elif call.data == "admin_edit_back" or call.data == "admin_delete_back":
        show_service_categories(call, "edit" if "edit" in call.data else "delete")
    else:
        show_admin_menu(call)

def handle_admin_confirmations(call):
    """Handle admin confirmations"""
    user_id = call.message.chat.id
    
    if call.data == "admin_confirm_broadcast":
        message_text = admin_states[user_id].get("broadcast_message")
        if message_text:
            send_broadcast(user_id, message_text)
            del admin_states[user_id]
            
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    text="📢 Bʀᴏᴀᴅᴄᴀsᴛ sᴇɴᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!",
                    reply_markup=admin_main_keyboard()
                )
            except:
                bot.send_message(user_id, "📢 Bʀᴏᴀᴅᴄᴀsᴛ sᴇɴᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!", 
                               reply_markup=admin_main_keyboard())

def show_admin_menu(call):
    """Show admin main menu"""
    user_id = call.message.chat.id
    admin_panel(call.message)

# User Message Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    user_id = message.chat.id
    user_name = message.chat.first_name
    
    # Check if user is banned
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("banned"):
        bot.reply_to(message, "🚫 Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ.")
        return
    
    # Check channel membership
    if not check_channel_membership(user_id):
        text = f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

📢 Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ:

{CHANNEL_ID}

Aғᴛᴇʀ ᴊᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴄʜᴇᴄᴋ.
        """
        bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=channel_join_keyboard())
        return
    
    # Welcome message for verified users
    text = f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

🤖 I'ᴍ ᴀɴ SMM sᴇʀᴠɪᴄᴇs ʙᴏᴛ. I ᴄᴀɴ ʜᴇʟᴘ ʏᴏᴜ ɢʀᴏᴡ ʏᴏᴜʀ sᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ ᴀᴄᴄᴏᴜɴᴛs.

💡 Fᴇᴀᴛᴜʀᴇs:
• Instagram Followers/Likes
• YouTube Views/Subscribers  
• Telegram Members/Reactions
• Facebook Likes/Followers
• And many more!

💰 Gᴇᴛ sᴛᴀʀᴛᴇᴅ ʙʏ ᴀᴅᴅɪɴɢ ғᴜɴᴅs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.
    """
    
    bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['balance'])
def check_balance(message):
    """Check user balance"""
    user_id = message.chat.id
    balance = get_user_balance(user_id)
    
    text = f"""
💳 Yᴏᴜʀ Aᴄᴄᴏᴜɴᴛ Bᴀʟᴀɴᴄᴇ

💰 Aᴠᴀɪʟᴀʙʟᴇ Bᴀʟᴀɴᴄᴇ: {balance} ᴘᴏɪɴᴛs
💵 Aᴘᴘʀᴏx. ɪɴ ʀᴜᴘᴇᴇs: ₹{balance/100:.2f}

💡 100 ᴘᴏɪɴᴛs = ₹1
    """
    
    bot.send_photo(user_id, ACCOUNT_IMAGE, text, reply_markup=main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_queries(call):
    """Handle all callback queries"""
    user_id = call.message.chat.id
    
    # Check if user is banned
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("banned"):
        bot.answer_callback_query(call.id, "🚫 Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ.", show_alert=True)
        return
    
    try:
        if call.data == "main_menu":
            show_main_menu(call)
        
        elif call.data == "deposit":
            show_deposit_options(call)
        
        elif call.data == "order_menu":
            show_service_categories_user(call)
        
        elif call.data == "history":
            show_order_history(call)
        
        elif call.data == "refer":
            show_referral_info(call)
        
        elif call.data == "account":
            show_account_info(call)
        
        elif call.data == "stats":
            show_stats(call)
        
        elif call.data == "support":
            show_support(call)
        
        elif call.data == "restart":
            restart_bot(call)
        
        elif call.data == "check_join":
            check_channel_join(call)
        
        elif call.data.startswith("category_"):
            category = call.data.replace("category_", "")
            show_services(call, category)
        
        elif call.data.startswith("service_"):
            service_id = call.data.replace("service_", "")
            start_order_process(call, service_id)
        
        elif call.data == "track_order":
            start_track_order(call)
        
        # Handle admin callbacks
        elif call.data.startswith("admin_"):
            handle_admin_callbacks(call)
            
    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!")

def show_main_menu(call):
    """Show main menu"""
    user_id = call.message.chat.id
    user_name = call.message.chat.first_name
    
    text = f"""
👋 Hᴇʟʟᴏ {user_name}!

🤖 Wᴇʟᴄᴏᴍᴇ ᴛᴏ SMM Bᴏᴛ Mᴀɪɴ Mᴇɴᴜ

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ʙᴇʟᴏᴡ:
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(WELCOME_IMAGE, text),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

def show_deposit_options(call):
    """Show deposit options"""
    user_id = call.message.chat.id
    balance = get_user_balance(user_id)
    
    text = f"""
💰 Dᴇᴘᴏsɪᴛ Fᴜɴᴅs

💳 Cᴜʀʀᴇɴᴛ Bᴀʟᴀɴᴄᴇ: {balance} ᴘᴏɪɴᴛs
💵 Aᴘᴘʀᴏx. ɪɴ ʀᴜᴘᴇᴇs: ₹{balance/100:.2f}

💡 100 ᴘᴏɪɴᴛs = ₹1

Pʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ғᴏʀ ᴅᴇᴘᴏsɪᴛs:

📞 Cᴏɴᴛᴀᴄᴛ: @SMMSupportBot
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(DEPOSIT_IMAGE, text),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(user_id, DEPOSIT_IMAGE, text, reply_markup=main_menu_keyboard())

def show_service_categories_user(call):
    """Show service categories for users"""
    user_id = call.message.chat.id
    
    if not is_bot_accepting_orders():
        bot.answer_callback_query(call.id, "❌ Bᴏᴛ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ɴᴏᴛ ᴀᴄᴄᴇᴘᴛɪɴɢ ᴏʀᴅᴇʀs!", show_alert=True)
        return
    
    text = """
🛒 Sᴇʟᴇᴄᴛ Sᴇʀᴠɪᴄᴇ Cᴀᴛᴇɢᴏʀʏ

Cʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ғʀᴏᴍ ʙᴇʟᴏᴡ:
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(SERVICE_IMAGE, text),
            reply_markup=service_category_keyboard()
        )
    except:
        bot.send_photo(user_id, SERVICE_IMAGE, text, reply_markup=service_category_keyboard())

def show_services(call, category):
    """Show services for a category"""
    user_id = call.message.chat.id
    
    text = f"""
📦 {category.title()} Sᴇʀᴠɪᴄᴇs

Sᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ ғʀᴏᴍ ʙᴇʟᴏᴡ:
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(SERVICE_IMAGE, text),
            reply_markup=services_keyboard(category)
        )
    except:
        bot.send_photo(user_id, SERVICE_IMAGE, text, reply_markup=services_keyboard(category))

def start_order_process(call, service_id):
    """Start order process for a service"""
    user_id = call.message.chat.id
    service = get_service_by_id(service_id)
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    user_states[user_id] = {
        "action": "ordering",
        "service_id": service_id,
        "step": "link"
    }
    
    text = f"""
📦 Oʀᴅᴇʀ: {service['name']}

📝 Dᴇsᴄʀɪᴘᴛɪᴏɴ: {service['description']}
💰 Pʀɪᴄᴇ: {service['price_per_unit']} ᴘᴏɪɴᴛs ᴘᴇʀ {service['unit']}
🔢 Qᴜᴀɴᴛɪᴛʏ ʀᴀɴɢᴇ: {service['min']} - {service['max']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ:
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text
        )
    except:
        bot.send_message(user_id, text)
    
    bot.register_next_step_handler(call.message, process_order_link)

def process_order_link(message):
    """Process order link"""
    user_id = message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        return
    
    link = message.text.strip()
    user_states[user_id]["link"] = link
    user_states[user_id]["step"] = "quantity"
    
    service = get_service_by_id(user_states[user_id]["service_id"])
    
    bot.send_message(user_id, f"🔢 Eɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ ({service['min']} - {service['max']}):")

def process_order_quantity(message):
    """Process order quantity"""
    user_id = message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        return
    
    try:
        quantity = int(message.text.strip())
        service = get_service_by_id(user_states[user_id]["service_id"])
        
        if quantity < service["min"] or quantity > service["max"]:
            bot.send_message(user_id, f"❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Mᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ {service['min']} ᴀɴᴅ {service['max']}.")
            return
        
        user_states[user_id]["quantity"] = quantity
        
        # Calculate cost
        cost_points = (quantity / service["unit"]) * service["price_per_unit"]
        user_states[user_id]["cost_points"] = cost_points
        
        # Check balance
        user_balance = get_user_balance(user_id)
        if user_balance < cost_points:
            bot.send_message(user_id, f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ! Yᴏᴜ ɴᴇᴇᴅ {cost_points} ᴘᴏɪɴᴛs, ʙᴜᴛ ʏᴏᴜ ʜᴀᴠᴇ ᴏɴʟʏ {user_balance} ᴘᴏɪɴᴛs.")
            del user_states[user_id]
            return
        
        # Confirm order
        text = f"""
📦 Oʀᴅᴇʀ Cᴏɴғɪʀᴍᴀᴛɪᴏɴ

📝 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {user_states[user_id]['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: {cost_points} ᴘᴏɪɴᴛs

Cᴏɴғɪʀᴍ ᴏʀᴅᴇʀ?
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Confirm", callback_data="confirm_order"))
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data="order_menu"))
        
        bot.send_message(user_id, text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def confirm_order(call):
    """Confirm and process order"""
    user_id = call.message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        return
    
    data = user_states[user_id]
    service = get_service_by_id(data["service_id"])
    
    # Deduct balance
    new_balance = update_user_balance(user_id, -data["cost_points"], is_spent=True)
    
    # Create order
    order = create_order(user_id, data["service_id"], data["link"], data["quantity"], data["cost_points"])
    
    if order:
        # Clear state
        del user_states[user_id]
        
        text = f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

🆔 Oʀᴅᴇʀ ID: {order['order_id']}
📝 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {data['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {data['quantity']}
💰 Cᴏsᴛ: {data['cost_points']} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs

📊 Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ
⏰ Eᴛᴀ: 24-48 ʜᴏᴜʀs
        """
        
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=main_menu_keyboard()
            )
        except:
            bot.send_message(user_id, text, reply_markup=main_menu_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴏʀᴅᴇʀ!", show_alert=True)

def show_order_history(call):
    """Show user's order history"""
    user_id = call.message.chat.id
    orders = get_user_orders(user_id)
    
    if not orders:
        text = "📋 Yᴏᴜ ʜᴀᴠᴇ ɴᴏ ᴏʀᴅᴇʀs ʏᴇᴛ."
    else:
        text = "📋 Yᴏᴜʀ Rᴇᴄᴇɴᴛ Oʀᴅᴇʀs:\n\n"
        for order in orders:
            status_emoji = "🟢" if order["status"] == "Completed" else "🟡" if order["status"] == "Processing" else "🔴"
            text += f"""
{status_emoji} Oʀᴅᴇʀ ID: {order['order_id']}
📦 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💰 Cᴏsᴛ: {order['cost_points']} ᴘᴏɪɴᴛs
📊 Sᴛᴀᴛᴜs: {order['status']}
⏰ Dᴀᴛᴇ: {order['created_at'].strftime('%Y-%m-%d %H:%M')}
────────────────────
            """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(HISTORY_IMAGE, text),
            reply_markup=track_order_keyboard()
        )
    except:
        bot.send_photo(user_id, HISTORY_IMAGE, text, reply_markup=track_order_keyboard())

def show_referral_info(call):
    """Show referral information"""
    user_id = call.message.chat.id
    referral_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    
    text = f"""
👥 Rᴇғᴇʀ & Eᴀʀɴ

🔗 Yᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ:
{referral_link}

💡 Hᴏᴡ ɪᴛ ᴡᴏʀᴋs:
• Sʜᴀʀᴇ ʏᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ
• Gᴇᴛ 10% ᴏғ ᴇᴠᴇʀʏ ᴅᴇᴘᴏsɪᴛ ᴛʜᴇʏ ᴍᴀᴋᴇ
• Eᴀʀɴ ᴜɴʟɪᴍɪᴛᴇᴅ ᴄᴏᴍᴍɪssɪᴏɴs!

💰 Rᴇғᴇʀʀᴀʟ ᴄᴏᴍᴍɪssɪᴏɴ: 10%
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(REFER_IMAGE, text),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(user_id, REFER_IMAGE, text, reply_markup=main_menu_keyboard())

def show_account_info(call):
    """Show user account information"""
    user_id = call.message.chat.id
    user = users_collection.find_one({"user_id": user_id})
    balance = get_user_balance(user_id)
    total_orders = orders_collection.count_documents({"user_id": user_id})
    
    if not user:
        users_collection.insert_one({
            "user_id": user_id,
            "balance_points": 0,
            "total_deposits_points": 0,
            "total_spent_points": 0,
            "joined_at": datetime.now(),
            "banned": False
        })
        user = users_collection.find_one({"user_id": user_id})
    
    text = f"""
👤 Aᴄᴄᴏᴜɴᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ

🆔 Usᴇʀ ID: {user_id}
👋 Nᴀᴍᴇ: {call.message.chat.first_name}
📅 Jᴏɪɴᴇᴅ: {user['joined_at'].strftime('%Y-%m-%d')}

💳 Bᴀʟᴀɴᴄᴇ: {balance} ᴘᴏɪɴᴛs
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛᴇᴅ: {user.get('total_deposits_points', 0)} ᴘᴏɪɴᴛs
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: {user.get('total_spent_points', 0)} ᴘᴏɪɴᴛs
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}

💡 100 ᴘᴏɪɴᴛs = ₹1
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(ACCOUNT_IMAGE, text),
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_photo(user_id, ACCOUNT_IMAGE, text, reply_markup=main_menu_keyboard())

def show_stats(call):
    """Show bot statistics"""
    user_id = call.message.chat.id
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    
    text = f"""
📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs

👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
📦 Aᴄᴛɪᴠᴇ Sᴇʀᴠɪᴄᴇs: {services_collection.count_documents({'active': True})}

⚡ Bᴏᴛ Sᴛᴀᴛᴜs: {'🟢 Online' if is_bot_accepting_orders() else '🔴 Maintenance'}
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=main_menu_keyboard()
        )
    except:
        bot.send_message(user_id, text, reply_markup=main_menu_keyboard())

def show_support(call):
    """Show support information"""
    user_id = call.message.chat.id
    
    text = """
ℹ️ Sᴜᴘᴘᴏʀᴛ

📞 Cᴏɴᴛᴀᴄᴛ ᴜs ғᴏʀ:
• Aᴄᴄᴏᴜɴᴛ ɪssᴜᴇs
• Dᴇᴘᴏsɪᴛ ʜᴇʟᴘ
• Oʀᴅᴇʀ ᴘʀᴏʙʟᴇᴍs
• Gᴇɴᴇʀᴀʟ ǫᴜᴇsᴛɪᴏɴs

👨‍💻 Cᴏɴᴛᴀᴄᴛ: @SMMSupportBot
⏰ Sᴜᴘᴘᴏʀᴛ ʜᴏᴜʀs: 24/7
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(WELCOME_IMAGE, text),
            reply_markup=support_keyboard()
        )
    except:
        bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=support_keyboard())

def restart_bot(call):
    """Restart bot for user"""
    user_id = call.message.chat.id
    send_welcome(call.message)

def check_channel_join(call):
    """Check if user has joined the channel"""
    user_id = call.message.chat.id
    
    if check_channel_membership(user_id):
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ʏᴇᴛ!", show_alert=True)

def start_track_order(call):
    """Start track order process"""
    user_id = call.message.chat.id
    user_states[user_id] = {"action": "tracking_order", "step": "order_id"}
    
    bot.send_message(user_id, "🔍 Eɴᴛᴇʀ ʏᴏᴜʀ Oʀᴅᴇʀ ID:")

def process_track_order(message):
    """Process order tracking"""
    user_id = message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "tracking_order":
        return
    
    order_id = message.text.strip()
    order = get_order_by_id(order_id)
    
    if not order or order["user_id"] != user_id:
        bot.send_message(user_id, "❌ Oʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ ᴏʀ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴠɪᴇᴡ ɪᴛ!")
        del user_states[user_id]
        return
    
    status_emoji = "🟢" if order["status"] == "Completed" else "🟡" if order["status"] == "Processing" else "🔴"
    
    text = f"""
🔍 Oʀᴅᴇʀ Tʀᴀᴄᴋɪɴɢ

🆔 Oʀᴅᴇʀ ID: {order['order_id']}
📦 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
🔗 Lɪɴᴋ: {order['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💰 Cᴏsᴛ: {order['cost_points']} ᴘᴏɪɴᴛs
📊 Sᴛᴀᴛᴜs: {status_emoji} {order['status']}
⏰ Cʀᴇᴀᴛᴇᴅ: {order['created_at'].strftime('%Y-%m-%d %H:%M')}
⏰ Lᴀsᴛ ᴜᴘᴅᴀᴛᴇ: {order['last_check'].strftime('%Y-%m-%d %H:%M')}
    """
    
    bot.send_message(user_id, text, reply_markup=main_menu_keyboard())
    del user_states[user_id]

# Message handlers for conversation flows
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all messages for conversation flows"""
    user_id = message.chat.id
    
    # Check if user is banned
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("banned"):
        return
    
    # Handle admin conversation flows
    if user_id in admin_states:
        state = admin_states[user_id]
        
        if state.get("action") == "adding_service":
            if state.get("step") == "category":
                process_add_service_category(message)
            elif state.get("step") == "name":
                process_add_service_name(message)
            elif state.get("step") == "description":
                process_add_service_description(message)
            elif state.get("step") == "min_quantity":
                process_add_service_min_quantity(message)
            elif state.get("step") == "max_quantity":
                process_add_service_max_quantity(message)
            elif state.get("step") == "unit":
                process_add_service_unit(message)
            elif state.get("step") == "price":
                process_add_service_price(message)
            elif state.get("step") == "service_id":
                process_add_service_id(message)
        
        elif state.get("action") == "editing_service" and state.get("step") == "new_value":
            process_edit_service_value(message)
        
        elif state.get("action") == "broadcasting" and state.get("step") == "message":
            process_broadcast_message(message)
        
        elif state.get("action") == "adding_balance":
            if state.get("step") == "user_id":
                process_add_balance_user_id(message)
            elif state.get("step") == "amount":
                process_add_balance_amount(message)
        
        elif state.get("action") == "deducting_balance":
            if state.get("step") == "user_id":
                process_deduct_balance_user_id(message)
            elif state.get("step") == "amount":
                process_deduct_balance_amount(message)
        
        elif state.get("action") == "banning_user" and state.get("step") == "user_id":
            process_ban_user(message)
        
        elif state.get("action") == "unbanning_user" and state.get("step") == "user_id":
            process_unban_user(message)
    
    # Handle user conversation flows
    elif user_id in user_states:
        state = user_states[user_id]
        
        if state.get("action") == "ordering" and state.get("step") == "quantity":
            process_order_quantity(message)
        
        elif state.get("action") == "tracking_order" and state.get("step") == "order_id":
            process_track_order(message)

# Error handler
@bot.message_handler(func=lambda message: True, content_types=['audio', 'video', 'document', 'sticker', 'photo'])
def handle_non_text_messages(message):
    """Handle non-text messages"""
    bot.reply_to(message, "❌ I ᴏɴʟʏ ᴜɴᴅᴇʀsᴛᴀɴᴅ ᴛᴇxᴛ ᴍᴇssᴀɢᴇs. Pʟᴇᴀsᴇ ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ᴘʀᴏᴠɪᴅᴇᴅ.")

# Start the bot with proper error handling
def start_bot():
    """Start the bot with error handling and recovery"""
    print("🤖 Starting SMM Bot...")
    
    while True:
        try:
            print("🔄 Starting polling...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
            
        except Exception as e:
            print(f"❌ Bot error: {e}")
            print("🔄 Restarting bot in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    # Ensure only one instance runs
    print("🚀 SMM Bot Starting...")
    print("✅ MongoDB Connected")
    print("✅ Bot Initialized")
    print("✅ Services Loaded")
    
    # Start the bot
    start_bot()
