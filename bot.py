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
    settings_collection = db.settings
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

# Main Menu Keyboard Builders (existing)
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
    
    bot.send_message(user_id, f"✅ Sᴇʀᴠɪᴄᴇ ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!", reply_markup=admin_main_keyboard())
    log_admin_action(user_id, "edit_service", f"Service ID: {data['service_id']}, Field: {field}")

def confirm_delete_service(call, service_id):
    """Confirm service deletion"""
    user_id = call.message.chat.id
    service = services_collection.find_one({"_id": ObjectId(service_id)})
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    text = f"""
❌ Cᴏɴғɪʀᴍ Sᴇʀᴠɪᴄᴇ Dᴇʟᴇᴛɪᴏɴ

📦 Sᴇʀᴠɪᴄᴇ: {service['name']}
📝 Cᴀᴛᴇɢᴏʀʏ: {service['category']}
💰 Pʀɪᴄᴇ: {service['price_per_unit']} ᴘᴏɪɴᴛs

Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜɪs sᴇʀᴠɪᴄᴇ?
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
    """Delete service (mark as inactive)"""
    user_id = call.message.chat.id
    
    # Mark service as inactive instead of deleting
    services_collection.update_one(
        {"_id": ObjectId(service_id)},
        {"$set": {"active": False}}
    )
    
    service = services_collection.find_one({"_id": ObjectId(service_id)})
    
    text = f"""
✅ Sᴇʀᴠɪᴄᴇ Dᴇʟᴇᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

📦 Sᴇʀᴠɪᴄᴇ: {service['name']}
📝 Cᴀᴛᴇɢᴏʀʏ: {service['category']}

Tʜᴇ sᴇʀᴠɪᴄᴇ ʜᴀs ʙᴇᴇɴ ᴍᴀʀᴋᴇᴅ ᴀs ɪɴᴀᴄᴛɪᴠᴇ.
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
    
    log_admin_action(user_id, "delete_service", f"Service: {service['name']}")

# Admin Balance Control Functions
def start_add_balance(call):
    """Start add balance process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "adding_balance", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="💰 Aᴅᴅ Bᴀʟᴀɴᴄᴇ\n\nEɴᴛᴇʀ ᴜsᴇʀ ID:"
        )
    except:
        bot.send_message(user_id, "💰 Aᴅᴅ Bᴀʟᴀɴᴄᴇ\n\nEɴᴛᴇʀ ᴜsᴇʀ ID:")
    
    bot.register_next_step_handler(call.message, process_balance_user_id)

def start_deduct_balance(call):
    """Start deduct balance process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "deducting_balance", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="💰 Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ\n\nEɴᴛᴇʀ ᴜsᴇʀ ID:"
        )
    except:
        bot.send_message(user_id, "💰 Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ\n\nEɴᴛᴇʀ ᴜsᴇʀ ID:")
    
    bot.register_next_step_handler(call.message, process_balance_user_id)

def process_balance_user_id(message):
    """Process user ID for balance operations"""
    user_id = message.chat.id
    
    if user_id not in admin_states or "balance" not in admin_states[user_id].get("action", ""):
        return
    
    try:
        target_user_id = int(message.text.strip())
        admin_states[user_id]["target_user_id"] = target_user_id
        admin_states[user_id]["step"] = "amount"
        
        action = "ᴀᴅᴅ" if "adding" in admin_states[user_id]["action"] else "ᴅᴇᴅᴜᴄᴛ"
        bot.send_message(user_id, f"💰 Eɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ ᴛᴏ {action} (₹ ᴏʀ ᴘᴏɪɴᴛs):")
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def process_balance_amount(message):
    """Process balance amount"""
    user_id = message.chat.id
    
    if user_id not in admin_states or "balance" not in admin_states[user_id].get("action", ""):
        return
    
    try:
        amount_text = message.text.strip().lower()
        
        # Check if amount is in rupees or points
        if '₹' in amount_text or 'rs' in amount_text or 'inr' in amount_text:
            # Convert rupees to points (1₹ = 100 points)
            amount_rupees = float(''.join(filter(str.isdigit, amount_text)))
            points = int(amount_rupees * 100)
            amount_type = "₹"
        else:
            # Assume points
            points = int(''.join(filter(str.isdigit, amount_text)))
            amount_type = "ᴘᴏɪɴᴛs"
        
        admin_states[user_id]["points"] = points
        admin_states[user_id]["amount_type"] = amount_type
        admin_states[user_id]["step"] = "confirm"
        
        target_user_id = admin_states[user_id]["target_user_id"]
        action = "ᴀᴅᴅ" if "adding" in admin_states[user_id]["action"] else "ᴅᴇᴅᴜᴄᴛ"
        
        # Get target user info
        target_user = users_collection.find_one({"user_id": target_user_id})
        username = target_user.get("username", "N/A") if target_user else "N/A"
        current_balance = get_user_balance(target_user_id)
        
        text = f"""
💰 Cᴏɴғɪʀᴍ Bᴀʟᴀɴᴄᴇ {action.title()}

👤 Usᴇʀ ID: {target_user_id}
👤 Usᴇʀɴᴀᴍᴇ: @{username}
💳 Cᴜʀʀᴇɴᴛ Bᴀʟᴀɴᴄᴇ: {current_balance} ᴘᴏɪɴᴛs
💰 Aᴍᴏᴜɴᴛ ᴛᴏ {action}: {points} ᴘᴏɪɴᴛs ({points/100:.2f}₹)

Cᴏɴғɪʀᴍ ᴛʜɪs ᴀᴄᴛɪᴏɴ?
        """
        
        markup = InlineKeyboardMarkup()
        if "adding" in admin_states[user_id]["action"]:
            markup.add(InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ Aᴅᴅ", callback_data="admin_confirm_add_balance"))
        else:
            markup.add(InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ Dᴇᴅᴜᴄᴛ", callback_data="admin_confirm_deduct_balance"))
        markup.add(InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="admin_balance_control"))
        
        bot.send_message(user_id, text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def execute_balance_adjustment(call, is_addition=True):
    """Execute balance addition or deduction"""
    user_id = call.message.chat.id
    
    if user_id not in admin_states or "balance" not in admin_states[user_id].get("action", ""):
        return
    
    data = admin_states[user_id]
    target_user_id = data["target_user_id"]
    points = data["points"]
    
    # Get target user
    target_user = users_collection.find_one({"user_id": target_user_id})
    if not target_user:
        bot.answer_callback_query(call.id, "❌ Usᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    current_balance = get_user_balance(target_user_id)
    
    if is_addition:
        # Add balance
        new_balance = update_user_balance(target_user_id, points, is_deposit=True)
        action_text = "ᴀᴅᴅᴇᴅ"
        log_action = "add_balance"
    else:
        # Check if enough balance
        if current_balance < points:
            bot.answer_callback_query(call.id, "❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!")
            return
        
        # Deduct balance
        new_balance = update_user_balance(target_user_id, -points, is_spent=True)
        action_text = "ᴅᴇᴅᴜᴄᴛᴇᴅ"
        log_action = "deduct_balance"
    
    # Notify admin
    admin_text = f"""
✅ Bᴀʟᴀɴᴄᴇ {action_text.title()} Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
💰 Aᴍᴏᴜɴᴛ {action_text}: {points} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=admin_text,
            reply_markup=admin_main_keyboard()
        )
    except:
        bot.send_message(user_id, admin_text, reply_markup=admin_main_keyboard())
    
    # Notify user (if possible)
    try:
        user_text = f"""
💰 Bᴀʟᴀɴᴄᴇ Uᴘᴅᴀᴛᴇ

Aᴅᴍɪɴ ʜᴀs {action_text} {points} ᴘᴏɪɴᴛs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.

💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs
        """
        bot.send_message(target_user_id, user_text)
    except:
        pass  # User might have blocked the bot
    
    # Clear state and log action
    del admin_states[user_id]
    log_admin_action(user_id, log_action, f"User: {target_user_id}, Points: {points}")

# Admin User Control Functions
def start_ban_user(call):
    """Start ban user process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "banning_user", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="🚫 Bᴀɴ Usᴇʀ\n\nEɴᴛᴇʀ ᴜsᴇʀ ID ᴛᴏ ʙᴀɴ:"
        )
    except:
        bot.send_message(user_id, "🚫 Bᴀɴ Usᴇʀ\n\nEɴᴛᴇʀ ᴜsᴇʀ ID ᴛᴏ ʙᴀɴ:")
    
    bot.register_next_step_handler(call.message, process_ban_user_id)

def start_unban_user(call):
    """Start unban user process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "unbanning_user", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="✅ Uɴʙᴀɴ Usᴇʀ\n\nEɴᴛᴇʀ ᴜsᴇʀ ID ᴛᴏ ᴜɴʙᴀɴ:"
        )
    except:
        bot.send_message(user_id, "✅ Uɴʙᴀɴ Usᴇʀ\n\nEɴᴛᴇʀ ᴜsᴇʀ ID ᴛᴏ ᴜɴʙᴀɴ:")
    
    bot.register_next_step_handler(call.message, process_unban_user_id)

def process_ban_user_id(message):
    """Process user ID for banning"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "banning_user":
        return
    
    try:
        target_user_id = int(message.text.strip())
        admin_states[user_id]["target_user_id"] = target_user_id
        
        # Check if user exists
        target_user = users_collection.find_one({"user_id": target_user_id})
        if not target_user:
            bot.send_message(user_id, "❌ Usᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!")
            return
        
        username = target_user.get("username", "N/A")
        is_banned = target_user.get("banned", False)
        
        if is_banned:
            bot.send_message(user_id, "⚠️ Usᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ʙᴀɴɴᴇᴅ!")
            return
        
        # Confirm ban
        text = f"""
🚫 Cᴏɴғɪʀᴍ Bᴀɴ Usᴇʀ

👤 Usᴇʀ ID: {target_user_id}
👤 Usᴇʀɴᴀᴍᴇ: @{username}

Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙᴀɴ ᴛʜɪs ᴜsᴇʀ?
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ Bᴀɴ", callback_data="admin_confirm_ban"))
        markup.add(InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="admin_user_control"))
        
        bot.send_message(user_id, text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def process_unban_user_id(message):
    """Process user ID for unbanning"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "unbanning_user":
        return
    
    try:
        target_user_id = int(message.text.strip())
        admin_states[user_id]["target_user_id"] = target_user_id
        
        # Check if user exists
        target_user = users_collection.find_one({"user_id": target_user_id})
        if not target_user:
            bot.send_message(user_id, "❌ Usᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!")
            return
        
        username = target_user.get("username", "N/A")
        is_banned = target_user.get("banned", False)
        
        if not is_banned:
            bot.send_message(user_id, "⚠️ Usᴇʀ ɪs ɴᴏᴛ ʙᴀɴɴᴇᴅ!")
            return
        
        # Confirm unban
        text = f"""
✅ Cᴏɴғɪʀᴍ Uɴʙᴀɴ Usᴇʀ

👤 Usᴇʀ ID: {target_user_id}
👤 Usᴇʀɴᴀᴍᴇ: @{username}

Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜɴʙᴀɴ ᴛʜɪs ᴜsᴇʀ?
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ Uɴʙᴀɴ", callback_data="admin_confirm_unban"))
        markup.add(InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="admin_user_control"))
        
        bot.send_message(user_id, text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def execute_ban_user(call, ban=True):
    """Execute user ban/unban"""
    user_id = call.message.chat.id
    
    if user_id not in admin_states or "user" not in admin_states[user_id].get("action", ""):
        return
    
    data = admin_states[user_id]
    target_user_id = data["target_user_id"]
    
    # Update user ban status
    users_collection.update_one(
        {"user_id": target_user_id},
        {"$set": {"banned": ban}}
    )
    
    action_text = "ʙᴀɴɴᴇᴅ" if ban else "ᴜɴʙᴀɴɴᴇᴅ"
    
    # Notify admin
    admin_text = f"""
✅ Usᴇʀ {action_text.title()} Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
🔄 Sᴛᴀᴛᴜs: {action_text.title()}
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=admin_text,
            reply_markup=admin_main_keyboard()
        )
    except:
        bot.send_message(user_id, admin_text, reply_markup=admin_main_keyboard())
    
    # Notify user (if not banning or if user wants to notify)
    if not ban:  # Only notify when unbanning
        try:
            user_text = f"""
🔓 Aᴄᴄᴏᴜɴᴛ Uɴʙᴀɴɴᴇᴅ

Yᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ʜᴀs ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ ʙʏ ᴀɴ ᴀᴅᴍɪɴ.

Yᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ ɴᴏʀᴍᴀʟʟʏ.
            """
            bot.send_message(target_user_id, user_text)
        except:
            pass  # User might have blocked the bot
    
    # Clear state and log action
    del admin_states[user_id]
    log_action = "ban_user" if ban else "unban_user"
    log_admin_action(user_id, log_action, f"User: {target_user_id}")

# Admin Broadcast Functions
def start_admin_broadcast(call):
    """Start broadcast process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "broadcasting", "step": "message"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="📢 Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ\n\nSᴇɴᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ (ᴛᴇxᴛ, ᴘʜᴏᴛᴏ+ᴄᴀᴘᴛɪᴏɴ, ᴏʀ ᴠɪᴅᴇᴏ+ᴄᴀᴘᴛɪᴏɴ):"
        )
    except:
        bot.send_message(user_id, "📢 Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ\n\nSᴇɴᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ (ᴛᴇxᴛ, ᴘʜᴏᴛᴏ+ᴄᴀᴘᴛɪᴏɴ, ᴏʀ ᴠɪᴅᴇᴏ+ᴄᴀᴘᴛɪᴏɴ):")

@bot.message_handler(content_types=['text', 'photo', 'video'])
def process_broadcast_message(message):
    """Process broadcast message from admin"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "broadcasting":
        return
    
    # Store the message content for broadcasting
    admin_states[user_id]["broadcast_message"] = {
        "content_type": message.content_type,
        "message_id": message.message_id,
        "chat_id": user_id
    }
    admin_states[user_id]["step"] = "confirm"
    
    # Ask for confirmation
    text = """
📢 Bʀᴏᴀᴅᴄᴀsᴛ Rᴇᴀᴅʏ

Mᴇssᴀɢᴇ ʀᴇᴄᴇɪᴠᴇᴅ! Tʜɪs ᴡɪʟʟ ʙᴇ sᴇɴᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs.

Cᴏɴғɪʀᴍ ʙʀᴏᴀᴅᴄᴀsᴛ?
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Sᴛᴀʀᴛ Bʀᴏᴀᴅᴄᴀsᴛ", callback_data="admin_confirm_broadcast"))
    markup.add(InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="admin_menu"))
    
    bot.send_message(user_id, text, reply_markup=markup)

def execute_broadcast(call):
    """Execute broadcast to all users"""
    user_id = call.message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "broadcasting":
        return
    
    data = admin_states[user_id]
    broadcast_data = data["broadcast_message"]
    
    # Get all users
    all_users = list(users_collection.find({}, {"user_id": 1}))
    total_users = len(all_users)
    successful = 0
    failed = 0
    
    # Update admin
    progress_msg = bot.send_message(user_id, f"📢 Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ...\n\nProgress: 0/{total_users}")
    
    # Broadcast to each user
    for i, user in enumerate(all_users):
        try:
            target_user_id = user["user_id"]
            
            # Forward the message based on content type
            if broadcast_data["content_type"] == "text":
                bot.send_message(target_user_id, broadcast_data.get("text", ""))
            elif broadcast_data["content_type"] == "photo":
                caption = broadcast_data.get("caption", "")
                bot.send_photo(target_user_id, broadcast_data.get("photo", ""), caption=caption)
            elif broadcast_data["content_type"] == "video":
                caption = broadcast_data.get("caption", "")
                bot.send_video(target_user_id, broadcast_data.get("video", ""), caption=caption)
            
            successful += 1
            
            # Update progress every 10 users
            if i % 10 == 0:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=progress_msg.message_id,
                        text=f"📢 Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ...\n\nProgress: {i+1}/{total_users}\n✅ Successful: {successful}\n❌ Failed: {failed}"
                    )
                except:
                    pass
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            failed += 1
            continue
    
    # Send final report
    final_text = f"""
✅ Bʀᴏᴀᴅᴄᴀsᴛ Cᴏᴍᴘʟᴇᴛᴇᴅ!

👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
✅ Sᴜᴄᴄᴇssғᴜʟ: {successful}
❌ Fᴀɪʟᴇᴅ: {failed}

Sᴜᴄᴄᴇss ʀᴀᴛᴇ: {(successful/total_users)*100:.1f}%
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=progress_msg.message_id,
            text=final_text
        )
    except:
        bot.send_message(user_id, final_text)
    
    # Clear state and log action
    del admin_states[user_id]
    log_admin_action(user_id, "broadcast", f"Users: {total_users}, Successful: {successful}")

# Bot Control Functions
def set_bot_status(call, status):
    """Set bot accepting orders status"""
    user_id = call.message.chat.id
    
    set_bot_accepting_orders(status)
    status_text = "🟢 ON" if status else "🔴 OFF"
    action_text = "ᴇɴᴀʙʟᴇᴅ" if status else "ᴅɪsᴀʙʟᴇᴅ"
    
    text = f"""
✅ Bᴏᴛ Sᴛᴀᴛᴜs Uᴘᴅᴀᴛᴇᴅ

Bᴏᴛ ʜᴀs ʙᴇᴇɴ {action_text}.

⚙️ Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: {status_text}
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
    
    log_admin_action(user_id, "bot_status_change", f"Status: {status_text}")

def show_bot_status(call):
    """Show current bot status"""
    user_id = call.message.chat.id
    status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    
    text = f"""
⚙️ Bᴏᴛ Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs

🔄 Oʀᴅᴇʀs: {status}
📊 Mᴀɪɴᴛᴇɴᴀɴᴄᴇ: {'🔴 OFF' if is_bot_accepting_orders() else '🟢 ON'}
    """
    
    bot.answer_callback_query(call.id, text, show_alert=True)

# Admin Menu Navigation Functions
def show_admin_menu(call):
    """Show admin main menu"""
    user_id = call.message.chat.id
    
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
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=admin_main_keyboard()
        )
    except:
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())

def show_admin_services_menu(call):
    """Show admin services menu"""
    user_id = call.message.chat.id
    total_services = services_collection.count_documents({"active": True})
    
    text = f"""
📦 Mᴀɴᴀɢᴇ Sᴇʀᴠɪᴄᴇs

Tᴏᴛᴀʟ ᴀᴄᴛɪᴠᴇ sᴇʀᴠɪᴄᴇs: {total_services}

Cʜᴏᴏsᴇ ᴀɴ ᴀᴄᴛɪᴏɴ:
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=admin_services_keyboard()
        )
    except:
        bot.send_message(user_id, text, reply_markup=admin_services_keyboard())

def show_admin_balance_menu(call):
    """Show admin balance control menu"""
    user_id = call.message.chat.id
    
    text = """
💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ

Mᴀɴᴀɢᴇ ᴜsᴇʀ ʙᴀʟᴀɴᴄᴇs:

• ➕ Aᴅᴅ Bᴀʟᴀɴᴄᴇ - Aᴅᴅ ᴘᴏɪɴᴛs ᴛᴏ ᴜsᴇʀ ᴀᴄᴄᴏᴜɴᴛ
• ➖ Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ - Rᴇᴍᴏᴠᴇ ᴘᴏɪɴᴛs ғʀᴏᴍ ᴜsᴇʀ ᴀᴄᴄᴏᴜɴᴛ

Cʜᴏᴏsᴇ ᴀɴ ᴀᴄᴛɪᴏɴ:
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=admin_balance_keyboard()
        )
    except:
        bot.send_message(user_id, text, reply_markup=admin_balance_keyboard())

def show_admin_user_menu(call):
    """Show admin user control menu"""
    user_id = call.message.chat.id
    banned_users = users_collection.count_documents({"banned": True})
    
    text = f"""
👥 Usᴇʀ Cᴏɴᴛʀᴏʟ

Cᴜʀʀᴇɴᴛʟʏ ʙᴀɴɴᴇᴅ ᴜsᴇʀs: {banned_users}

• 🚫 Bᴀɴ Usᴇʀ - Rᴇsᴛʀɪᴄᴛ ᴜsᴇʀ ᴀᴄᴄᴇss
• ✅ Uɴʙᴀɴ Usᴇʀ - Rᴇsᴛᴏʀᴇ ᴜsᴇʀ ᴀᴄᴄᴇss

Cʜᴏᴏsᴇ ᴀɴ ᴀᴄᴛɪᴏɴ:
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=admin_user_keyboard()
        )
    except:
        bot.send_message(user_id, text, reply_markup=admin_user_keyboard())

def show_admin_bot_control(call):
    """Show admin bot control menu"""
    user_id = call.message.chat.id
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    
    text = f"""
⚙️ Bᴏᴛ Cᴏɴᴛʀᴏʟ

Cᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs: {bot_status}

• 🟢 Tᴜʀɴ Bᴏᴛ ON - Aʟʟᴏᴡ ɴᴇᴡ ᴏʀᴅᴇʀs
• 🔴 Tᴜʀɴ Bᴏᴛ OFF - Bʟᴏᴄᴋ ɴᴇᴡ ᴏʀᴅᴇʀs

Cʜᴏᴏsᴇ ᴀɴ ᴀᴄᴛɪᴏɴ:
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
    
    # Calculate stats
    total_users = users_collection.count_documents({})
    active_users = users_collection.count_documents({"last_activity": {"$gte": datetime.now() - timedelta(days=30)}})
    banned_users = users_collection.count_documents({"banned": True})
    total_orders = orders_collection.count_documents({})
    pending_orders = orders_collection.count_documents({"status": "Pending"})
    completed_orders = orders_collection.count_documents({"status": "Completed"})
    total_services = services_collection.count_documents({"active": True})
    total_deposits = sum(user.get('total_deposits_points', 0) for user in users_collection.find()) / 100
    total_spent = sum(user.get('total_spent_points', 0) for user in users_collection.find()) / 100
    
    text = f"""
📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs

👥 Usᴇʀs:
• Tᴏᴛᴀʟ: {total_users}
• Aᴄᴛɪᴠᴇ (30ᴅ): {active_users}
• Bᴀɴɴᴇᴅ: {banned_users}

🛒 Oʀᴅᴇʀs:
• Tᴏᴛᴀʟ: {total_orders}
• Pᴇɴᴅɪɴɢ: {pending_orders}
• Cᴏᴍᴘʟᴇᴛᴇᴅ: {completed_orders}

💰 Fɪɴᴀɴᴄᴇ:
• Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposits:.2f}
• Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{total_spent:.2f}
• Rᴇᴠᴇɴᴜᴇ: ₹{total_deposits - total_spent:.2f}

📦 Sᴇʀᴠɪᴄᴇs:
• Aᴄᴛɪᴠᴇ: {total_services}
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

def handle_admin_back(call):
    """Handle back navigation in admin panel"""
    user_id = call.message.chat.id
    
    if call.data == "admin_manage_services_back":
        show_admin_services_menu(call)
    elif call.data == "admin_edit_back" or call.data == "admin_delete_back":
        show_admin_services_menu(call)
    elif call.data.endswith("_back"):
        show_admin_menu(call)

# Additional Admin Callback Handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_confirm_'))
def handle_admin_confirmations(call):
    """Handle admin confirmation callbacks"""
    user_id = call.message.chat.id
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "🚫 Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.", show_alert=True)
        return
    
    if call.data == "admin_confirm_add_balance":
        execute_balance_adjustment(call, is_addition=True)
    elif call.data == "admin_confirm_deduct_balance":
        execute_balance_adjustment(call, is_addition=False)
    elif call.data == "admin_confirm_ban":
        execute_ban_user(call, ban=True)
    elif call.data == "admin_confirm_unban":
        execute_ban_user(call, ban=False)
    elif call.data == "admin_confirm_broadcast":
        execute_broadcast(call)

# Message Handlers for Admin Steps
@bot.message_handler(func=lambda message: message.chat.id in admin_states)
def handle_admin_steps(message):
    """Handle admin conversation steps"""
    user_id = message.chat.id
    
    if user_id not in admin_states:
        return
    
    state = admin_states[user_id]
    action = state.get("action")
    step = state.get("step")
    
    if action == "adding_service":
        if step == "category":
            process_add_service_category(message)
        elif step == "name":
            process_add_service_name(message)
        elif step == "description":
            process_add_service_description(message)
        elif step == "min_quantity":
            process_add_service_min_quantity(message)
        elif step == "max_quantity":
            process_add_service_max_quantity(message)
        elif step == "unit":
            process_add_service_unit(message)
        elif step == "price":
            process_add_service_price(message)
        elif step == "service_id":
            process_add_service_id(message)
    
    elif action == "editing_service" and step == "new_value":
        process_edit_service_value(message)
    
    elif "balance" in action and step == "user_id":
        process_balance_user_id(message)
    elif "balance" in action and step == "amount":
        process_balance_amount(message)
    
    elif "user" in action and step == "user_id":
        if "ban" in action:
            process_ban_user_id(message)
        else:
            process_unban_user_id(message)

# Existing bot handlers (keep your existing functionality)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Your existing start function
    pass

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    # Your existing callback handler
    pass

# Add other existing handlers here...

# Start the bot
if __name__ == "__main__":
    print("🤖 Bot starting...")
    bot.infinity_polling()
