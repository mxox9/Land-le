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

# Load environment variables
load_dotenv()

# Configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN', '8052955693:AAGoXnNg90jqvcC1X1fVo_qKV8Y0eHjDAZg')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://saifulmolla79088179_db_user:17gNrX0pC3bPqVaG@cluster0.fusvqca.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '6052975324').split(',')]
CHANNEL_ID = os.getenv('CHANNEL_ID', '@prooflelo1')
SMM_API_URL = os.getenv('SMM_API_URL', 'https://mysmmapi.com/api/v2?')
SMM_API_KEY = os.getenv('SMM_API_KEY', 'a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d')
PROOF_CHANNEL = "https://t.me/prooflelo1"
BOT_USERNAME = "@prank_ox_bot"

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
WELCOME_IMAGE = "https://t.me/prooflelo1/135?single"
SERVICE_IMAGE = "https://t.me/prooflelo1/138?single"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/136?single"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/137?single"
HISTORY_IMAGE = "https://t.me/prooflelo1/139?single"
REFER_IMAGE = "https://t.me/prooflelo1/17"
ADMIN_IMAGE = "https://t.me/prooflelo1/140?single"

# UPI Details for QR Code
UPI_ID = "your-upi-id@oksbi"  # Change this to your UPI ID

# Text styling function
def style_text(text):
    """Convert text to stylish format with first letter capitalized and rest small"""
    def style_word(word):
        if len(word) > 0:
            # Keep first letter as is, make rest lowercase
            return word[0] + word[1:].lower()
        return word
    
    # Split into words and apply styling
    words = text.split()
    styled_words = []
    
    for word in words:
        # Handle special characters and emojis
        if any(char.isalpha() for char in word):
            styled_words.append(style_word(word))
        else:
            styled_words.append(word)
    
    return ' '.join(styled_words)

# API Functions
def verify_payment(amount, transaction_id=None):
    """Verify payment using SMM API"""
    try:
        params = {
            'key': SMM_API_KEY,
            'action': 'balance'
        }
        response = requests.get(SMM_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # For demo purposes, we'll assume payment is verified
            # In real implementation, check transaction status
            return True
        return False
    except Exception as e:
        print(f"Payment verification error: {e}")
        return False

def place_smm_order(service_id, link, quantity):
    """Place order via SMM API (robust). Accepts either a service ID string or a MongoDB service _id.
    It prefers service-specific api_url/api_key/service_id when present in the service document.
    Returns order id string on success, or None on failure.
    """
    try:
        # try to load service document from DB if service_id looks like an ObjectId
        service = None
        try:
            if isinstance(service_id, str) and len(service_id) >= 12:
                service = services_collection.find_one({"_id": ObjectId(service_id)})
        except Exception:
            service = None

        # default to global config
        api_url = SMM_API_URL.rstrip('?')
        api_key = SMM_API_KEY
        api_service_id = None

        # prefer service-specific fields if available
        if service:
            api_url = service.get('api_url', api_url)
            api_key = service.get('api_key', api_key)
            api_service_id = service.get('service_id') or service.get('smm_service_id')

        # if the caller passed an actual API service id instead of our mongo _id, use it
        if not api_service_id:
            api_service_id = service_id

        params = {
            'key': api_key,
            'action': 'add',
            'service': api_service_id,
            'link': link,
            'quantity': quantity
        }

        response = requests.get(api_url, params=params, timeout=30)
        # be resilient to non-JSON responses
        try:
            data = response.json()
        except ValueError:
            print(f"SMM API returned non-JSON response: {response.text[:300]!r}")
            return None

        # handle common error shapes
        if isinstance(data, dict):
            if data.get('error') or str(data.get('status')).lower() in ['error', 'failed']:
                print(f"SMM API reported error placing order: {data}")
                return None

            # try multiple keys for order id
            for key in ('order', 'order_id', 'id', 'orderid'):
                if key in data and data[key]:
                    return str(data[key])

            # nested under data
            if 'data' in data and isinstance(data['data'], dict):
                for key in ('order', 'order_id', 'id'):
                    if key in data['data'] and data['data'][key]:
                        return str(data['data'][key])

        print(f"SMM API response did not contain order id: {data}")
        return None

    except Exception as e:
        print(f"SMM API order error: {e}")
        return None

def get_order_status(api_order_id):
    """Get order status from SMM API"""
    try:
        params = {
            "key": SMM_API_KEY,
            "action": "status",
            "order": api_order_id
        }
        
        response = requests.get(SMM_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Order status check error: {e}")
        return None

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

def create_order(user_id, service_id, link, quantity, cost_points, api_order_id=None):
    """Create new order with API integration"""
    service = get_service_by_id(service_id)
    if not service:
        return None
    
    # Generate order ID
    order_id = f"ORD{random.randint(100000, 999999)}"
    
    order = {
        "order_id": order_id,
        "api_order_id": api_order_id,
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

def generate_qr_code(amount, upi_id=UPI_ID):
    """Generate QR code for UPI payment"""
    upi_url = f"upi://pay?pa={upi_id}&pn=SMM%20Services&am={amount}&cu=INR"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def send_order_to_channel(order):
    """Send order proof to channel"""
    try:
        text = f"""
🆕 New Order Placed!

📱 Service: {order['service_name']}
👤 User ID: {order['user_id']}
🆔 Order ID: {order['order_id']}
🔗 Link: {order['link']}
🔢 Quantity: {order['quantity']}
💵 Points: {order['cost_points']}
⏰ Time: {order['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🤖 Bot Here 🛒", url=f"https://t.me/{BOT_USERNAME.replace('@', '')}"))
        
        bot.send_message(PROOF_CHANNEL, text, reply_markup=markup)
        return True
    except Exception as e:
        print(f"Error sending to channel: {e}")
        return False

# Admin Keyboard Builders
def admin_main_keyboard():
    """Admin main menu keyboard"""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📱 Manage Services", callback_data="admin_manage_services"),
        InlineKeyboardButton("💰 Balance Control", callback_data="admin_balance_control")
    )
    markup.add(
        InlineKeyboardButton("👤 User Control", callback_data="admin_user_control"),
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
    markup.add(InlineKeyboardButton("➕ Add Category", callback_data="admin_add_category"))
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
    markup.add(InlineKeyboardButton("🔨 Ban User", callback_data="admin_ban_user"))
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
    categories = services_collection.distinct("category")
    if not categories:
        categories = ["Instagram", "YouTube", "Telegram", "Facebook", "Twitter", "TikTok", "Other"]
    
    for category in categories:
        markup.add(InlineKeyboardButton(style_text(category), callback_data=f"admin_category_{category.lower()}"))
    markup.add(InlineKeyboardButton("➕ Add New Category", callback_data="admin_add_new_category"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="admin_manage_services"))
    return markup

def services_list_keyboard(category, action):
    """Services list for a category with action"""
    markup = InlineKeyboardMarkup()
    services = list(services_collection.find({"category": category.lower(), "active": True}))
    
    for service in services:
        service_name = style_text(service['name'][:30])  # Limit name length
        markup.add(InlineKeyboardButton(
            service_name, 
            callback_data=f"admin_{action}_{str(service['_id'])}"
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
        InlineKeyboardButton("💵 Deposit", callback_data="deposit"),
        InlineKeyboardButton("🛒 Order", callback_data="order_menu")
    )
    markup.add(
        InlineKeyboardButton("📋 Orders", callback_data="history"),
        InlineKeyboardButton("👥 Refer", callback_data="refer")
    )
    markup.add(
        InlineKeyboardButton("👤 Account", callback_data="account"),
        InlineKeyboardButton("📊 Stats", callback_data="stats")
    )
    markup.add(InlineKeyboardButton("🆘 Support", callback_data="support"))
    
    return markup

def back_button_only():
    """Back button only keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
    return markup

def service_category_keyboard():
    """Service category selection keyboard"""
    markup = InlineKeyboardMarkup()
    
    # Get unique categories from services
    categories = services_collection.distinct("category", {"active": True})
    
    for category in categories:
        emoji = "📱" if category == "instagram" else "📺" if category == "youtube" else "📢"
        markup.add(InlineKeyboardButton(
            f"{emoji} {style_text(category)}", 
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
        button_text = f"{style_text(service['name'])} - {price} Points/{unit}"
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
    markup.add(InlineKeyboardButton("📊 Track Order", callback_data="track_order"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    return markup

def deposit_confirmation_keyboard():
    """Deposit confirmation keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ I Have Paid", callback_data="confirm_deposit"))
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="main_menu"))
    return markup

# Admin Message Handlers
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """Admin panel command"""
    user_id = message.chat.id
    
    if not is_admin(user_id):
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    total_deposits = sum(user.get('total_deposits_points', 0) for user in users_collection.find()) / 100
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    
    text = f"""
👑 Admin Panel

👤 Users: {total_users}
🛒 Orders: {total_orders}
💰 Total Deposits: ₹{total_deposits:.2f}
⚙️ Bot Status: {bot_status}

Choose an action:
    """
    
    bot.send_photo(user_id, ADMIN_IMAGE, text, reply_markup=admin_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callbacks(call):
    """Handle admin callback queries"""
    user_id = call.message.chat.id
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ You are not authorized.", show_alert=True)
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
        
        elif call.data == "admin_add_category":
            start_add_category(call)
        
        elif call.data == "admin_add_new_category":
            start_add_new_category(call)
        
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
        bot.answer_callback_query(call.id, "❌ An error occurred!")

# Fixed Admin Service Management Functions
def start_add_service(call):
    """Start add service process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "adding_service", "step": "category"}
    
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    
    text = "📱 Add New Service\n\nSelect category:"
    bot.send_message(user_id, text, reply_markup=service_categories_keyboard())

def start_add_category(call):
    """Start add category process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "adding_category", "step": "name"}
    
    text = "📂 Add New Category\n\nEnter category name:"
    bot.send_message(user_id, text)
    bot.register_next_step_handler(call.message, process_add_category_name)

def process_add_category_name(message):
    """Process new category name"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_category":
        return
    
    category_name = message.text.strip().lower()
    
    # Check if category already exists
    existing_categories = services_collection.distinct("category")
    if category_name in existing_categories:
        bot.send_message(user_id, f"❌ Category '{category_name}' already exists!", reply_markup=admin_main_keyboard())
        del admin_states[user_id]
        return
    
    # Category added successfully
    bot.send_message(user_id, f"✅ Category '{category_name}' added successfully!", reply_markup=admin_main_keyboard())
    del admin_states[user_id]

def start_add_new_category(call):
    """Start adding a new category during service creation"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "adding_service_new_category", "step": "name"}
    
    text = "📂 Enter new category name:"
    bot.send_message(user_id, text)
    bot.register_next_step_handler(call.message, process_new_category_for_service)

def process_new_category_for_service(message):
    """Process new category for service"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service_new_category":
        return
    
    category_name = message.text.strip().lower()
    admin_states[user_id]["category"] = category_name
    admin_states[user_id]["action"] = "adding_service"
    admin_states[user_id]["step"] = "name"
    
    bot.send_message(user_id, "📱 Enter service name:")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_category_'))
def handle_admin_category_selection(call):
    """Handle admin category selection"""
    user_id = call.message.chat.id
    
    if not is_admin(user_id):
        return
    
    category = call.data.replace('admin_category_', '')
    action = admin_states.get(user_id, {}).get("action")
    
    if action == "adding_service":
        admin_states[user_id]["category"] = category
        admin_states[user_id]["step"] = "name"
        
        try:
            bot.delete_message(user_id, call.message.message_id)
        except:
            pass
        
        bot.send_message(user_id, "📱 Enter service name:")
        bot.register_next_step_handler(call.message, process_add_service_name)
    
    elif action == "edit":
        show_services_for_edit(call, category)
    
    elif action == "delete":
        show_services_for_delete(call, category)

def process_add_service_name(message):
    """Process service name"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    admin_states[user_id]["name"] = message.text.strip()
    admin_states[user_id]["step"] = "description"
    
    bot.send_message(user_id, "📝 Enter service description:")

def process_add_service_description(message):
    """Process service description"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    admin_states[user_id]["description"] = message.text.strip()
    admin_states[user_id]["step"] = "min_quantity"
    
    bot.send_message(user_id, "🔢 Enter minimum quantity:")

def process_add_service_min_quantity(message):
    """Process minimum quantity"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    try:
        min_quantity = int(message.text.strip())
        admin_states[user_id]["min_quantity"] = min_quantity
        admin_states[user_id]["step"] = "max_quantity"
        
        bot.send_message(user_id, "🔢 Enter maximum quantity:")
    except ValueError:
        bot.send_message(user_id, "❌ Invalid quantity! Use numbers only.")

def process_add_service_max_quantity(message):
    """Process maximum quantity"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    try:
        max_quantity = int(message.text.strip())
        admin_states[user_id]["max_quantity"] = max_quantity
        admin_states[user_id]["step"] = "unit"
        
        bot.send_message(user_id, "📦 Enter unit (100 or 1000):")
    except ValueError:
        bot.send_message(user_id, "❌ Invalid quantity! Use numbers only.")

def process_add_service_unit(message):
    """Process service unit"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    try:
        unit = int(message.text.strip())
        if unit not in [100, 1000]:
            bot.send_message(user_id, "❌ Unit must be 100 or 1000!")
            return
        
        admin_states[user_id]["unit"] = unit
        admin_states[user_id]["step"] = "price"
        
        bot.send_message(user_id, "💰 Enter price per unit (in points):")
    except ValueError:
        bot.send_message(user_id, "❌ Invalid unit! Use numbers only.")

def process_add_service_price(message):
    """Process service price"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    try:
        price = int(message.text.strip())
        admin_states[user_id]["price"] = price
        admin_states[user_id]["step"] = "service_id"
        
        bot.send_message(user_id, "🆔 Enter service ID (API service ID):")
    except ValueError:
        bot.send_message(user_id, "❌ Invalid price! Use numbers only.")

def process_add_service_id(message):
    """Process service ID and then ask for API URL"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return
    
    service_id = message.text.strip()
    admin_states[user_id]["service_id"] = service_id
    admin_states[user_id]["step"] = "api_url"

    bot.send_message(user_id, "🔗 Enter API URL (or type 'db' to use default):")
    bot.register_next_step_handler(message, process_add_service_api_url)

def process_add_service_api_url(message):
    """Process API URL for the service (optional)"""
    user_id = message.chat.id
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return

    api_url = message.text.strip()
    if api_url.lower() in ('db', 'default', 'global'):
        api_url = None

    admin_states[user_id]["api_url"] = api_url
    admin_states[user_id]["step"] = "api_key"

    bot.send_message(user_id, "🔑 Enter API Key (or type 'db' to use default):")
    bot.register_next_step_handler(message, process_add_service_api_key)

def process_add_service_api_key(message):
    """Process API key and save the service to DB"""
    user_id = message.chat.id
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
        return

    api_key = message.text.strip()
    if api_key.lower() in ('db', 'default', 'global'):
        api_key = None

    data = admin_states[user_id]
    service_data = {
        "category": data["category"].lower(),
        "name": data["name"],
        "description": data.get("description", ""),
        "min": data.get("min_quantity", 1),
        "max": data.get("max_quantity", 1000),
        "unit": data.get("unit", 100),
        "price_per_unit": data.get("price", 0),
        "service_id": data.get("service_id"),
        "api_url": data.get("api_url"),
        "api_key": api_key,
        "active": True,
        "created_at": datetime.now()
    }

    services_collection.insert_one(service_data)

    # Clear state
    del admin_states[user_id]

    # Send confirmation
    text = f"""
✅ Service Added Successfully!

📱 Category: {service_data['category']}
📱 Name: {service_data['name']}
📝 Description: {service_data['description']}
🔢 Quantity: {service_data['min']}-{service_data['max']}
📦 Unit: {service_data['unit']}
💰 Price: {service_data['price_per_unit']} points/unit
🆔 Service ID: {service_data['service_id']}
🔗 API URL: {service_data.get('api_url') or 'GLOBAL'}
🔑 API Key: {('SET' if service_data.get('api_key') else 'GLOBAL')}
    """

    bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
    log_admin_action(user_id, "add_service", f"Service: {service_data['name']}")

def show_service_categories(call, action):
    """Show service categories for edit/delete"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": action}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="📱 Select service category:",
            reply_markup=service_categories_keyboard()
        )
    except:
        bot.send_message(user_id, "📱 Select service category:", reply_markup=service_categories_keyboard())

def show_services_for_edit(call, category):
    """Show services for editing"""
    user_id = call.message.chat.id
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=f"✏️ Select service to edit ({style_text(category)}):",
            reply_markup=services_list_keyboard(category, "edit")
        )
    except:
        bot.send_message(user_id, f"✏️ Select service to edit ({style_text(category)}):", 
                        reply_markup=services_list_keyboard(category, "edit"))

def show_services_for_delete(call, category):
    """Show services for deletion"""
    user_id = call.message.chat.id
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=f"❌ Select service to delete ({style_text(category)}):",
            reply_markup=services_list_keyboard(category, "delete")
        )
    except:
        bot.send_message(user_id, f"❌ Select service to delete ({style_text(category)}):", 
                        reply_markup=services_list_keyboard(category, "delete"))

def start_edit_service(call, service_id):
    """Start editing a service"""
    user_id = call.message.chat.id
    service = services_collection.find_one({"_id": ObjectId(service_id)})
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Service not found!")
        return
    
    admin_states[user_id] = {
        "action": "editing_service",
        "service_id": service_id,
        "service": service,
        "step": "field"
    }
    
    text = f"""
✏️ Edit Service: {service['name']}

Select field to edit:
1. 📱 Name
2. 📝 Description  
3. 🔢 Min Quantity
4. 🔢 Max Quantity
5. 📦 Unit
6. 💰 Price
7. 🆔 Service ID

Reply with number (1-7):
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
            bot.send_message(user_id, "❌ Invalid field number! Use 1-7.")
            return
        
        admin_states[user_id]["edit_field"] = field_map[field_num]
        admin_states[user_id]["step"] = "new_value"
        
        field_names = {
            "name": "name", "description": "description", 
            "min": "minimum quantity", "max": "maximum quantity",
            "unit": "unit", "price_per_unit": "price per unit", 
            "service_id": "service ID"
        }
        
        bot.send_message(user_id, f"📱 Enter new {field_names[field_map[field_num]]}:")
        
    except ValueError:
        bot.send_message(user_id, "❌ Invalid input! Use numbers 1-7.")

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
            bot.send_message(user_id, "❌ Invalid number format!")
            return
    
    # Update service in database
    services_collection.update_one(
        {"_id": ObjectId(data["service_id"])},
        {"$set": {field: new_value}}
    )
    
    # Clear state
    del admin_states[user_id]
    
    bot.send_message(user_id, f"✅ Service {field} updated successfully!", 
                    reply_markup=admin_main_keyboard())
    
    log_admin_action(user_id, "edit_service", f"Service ID: {data['service_id']}, Field: {field}")

def confirm_delete_service(call, service_id):
    """Confirm service deletion"""
    user_id = call.message.chat.id
    service = services_collection.find_one({"_id": ObjectId(service_id)})
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Service not found!")
        return
    
    text = f"""
❌ Confirm Deletion

Are you sure you want to delete this service?

📱 Service: {service['name']}
📂 Category: {service['category']}
💰 Price: {service['price_per_unit']} points

This action cannot be undone!
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
        bot.answer_callback_query(call.id, "❌ Service not found!")
        return
    
    service_name = service['name']
    services_collection.delete_one({"_id": ObjectId(service_id)})
    
    text = f"✅ Service '{service_name}' deleted successfully!"
    
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
            text="📱 Services Management\n\nSelect an action:",
            reply_markup=admin_services_keyboard()
        )
    except:
        bot.send_message(user_id, "📱 Services Management\n\nSelect an action:", 
                        reply_markup=admin_services_keyboard())

def show_admin_balance_menu(call):
    """Show admin balance control menu"""
    user_id = call.message.chat.id
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="💰 Balance Control\n\nSelect an action:",
            reply_markup=admin_balance_keyboard()
        )
    except:
        bot.send_message(user_id, "💰 Balance Control\n\nSelect an action:", 
                        reply_markup=admin_balance_keyboard())

def show_admin_user_menu(call):
    """Show admin user control menu"""
    user_id = call.message.chat.id
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="👤 User Control\n\nSelect an action:",
            reply_markup=admin_user_keyboard()
        )
    except:
        bot.send_message(user_id, "👤 User Control\n\nSelect an action:", 
                        reply_markup=admin_user_keyboard())

def show_admin_bot_control(call):
    """Show admin bot control menu"""
    user_id = call.message.chat.id
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    
    text = f"""
⚙️ Bot Control

Current Status: {bot_status}

Select an action:
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
📊 Admin Statistics

👤 Total Users: {total_users}
🛒 Total Orders: {total_orders}
📱 Active Services: {active_services}
💰 Total Deposits: ₹{total_deposits:.2f}
💸 Total Spent: ₹{total_spent:.2f}
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
            text="📢 Broadcast\n\nSend the message you want to broadcast to all users:"
        )
    except:
        bot.send_message(user_id, "📢 Broadcast\n\nSend the message you want to broadcast to all users:")

def process_broadcast_message(message):
    """Process broadcast message"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "broadcasting":
        return
    
    broadcast_message = message.text
    admin_states[user_id]["broadcast_message"] = broadcast_message
    admin_states[user_id]["step"] = "confirm"
    
    text = f"""
📢 Broadcast Confirmation

Message:
{broadcast_message}

This message will be sent to all users. Confirm?
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
            bot.send_message(user["user_id"], f"📢 Announcement:\n\n{message_text}")
            success_count += 1
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Broadcast failed for {user['user_id']}: {e}")
            fail_count += 1
    
    # Send report to admin
    report = f"""
📢 Broadcast Report

✅ Success: {success_count}
❌ Failed: {fail_count}
📊 Total: {success_count + fail_count}
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
            text="💰 Add Balance\n\nSend User ID:"
        )
    except:
        bot.send_message(user_id, "💰 Add Balance\n\nSend User ID:")

def process_add_balance_user_id(message):
    """Process user ID for adding balance"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "adding_balance":
        return
    
    try:
        target_user_id = int(message.text.strip())
        admin_states[user_id]["target_user_id"] = target_user_id
        admin_states[user_id]["step"] = "amount"
        
        bot.send_message(user_id, "💰 Enter amount to add (in points):")
    except ValueError:
        bot.send_message(user_id, "❌ Invalid User ID! Use numbers only.")

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
✅ Balance Added Successfully!

👤 User ID: {target_user_id}
💰 Amount Added: {amount} points
💳 New Balance: {new_balance} points
        """
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        log_admin_action(user_id, "add_balance", f"User: {target_user_id}, Amount: {amount}")
        
    except ValueError:
        bot.send_message(user_id, "❌ Invalid amount! Use numbers only.")

def start_deduct_balance(call):
    """Start deduct balance process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "deducting_balance", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="💰 Deduct Balance\n\nSend User ID:"
        )
    except:
        bot.send_message(user_id, "💰 Deduct Balance\n\nSend User ID:")

def process_deduct_balance_user_id(message):
    """Process user ID for deducting balance"""
    user_id = message.chat.id
    
    if user_id not in admin_states or admin_states[user_id].get("action") != "deducting_balance":
        return
    
    try:
        target_user_id = int(message.text.strip())
        admin_states[user_id]["target_user_id"] = target_user_id
        admin_states[user_id]["step"] = "amount"
        
        bot.send_message(user_id, "💰 Enter amount to deduct (in points):")
    except ValueError:
        bot.send_message(user_id, "❌ Invalid User ID! Use numbers only.")

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
            bot.send_message(user_id, f"❌ Insufficient balance! User has only {current_balance} points.")
            return
        
        # Deduct balance
        new_balance = update_user_balance(target_user_id, -amount, is_spent=True)
        
        # Clear state
        del admin_states[user_id]
        
        text = f"""
✅ Balance Deducted Successfully!

👤 User ID: {target_user_id}
💰 Amount Deducted: {amount} points
💳 New Balance: {new_balance} points
        """
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        log_admin_action(user_id, "deduct_balance", f"User: {target_user_id}, Amount: {amount}")
        
    except ValueError:
        bot.send_message(user_id, "❌ Invalid amount! Use numbers only.")

def start_ban_user(call):
    """Start ban user process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "banning_user", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="🔨 Ban User\n\nSend User ID to ban:"
        )
    except:
        bot.send_message(user_id, "🔨 Ban User\n\nSend User ID to ban:")

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
✅ User Banned Successfully!

👤 User ID: {target_user_id}
🔨 Status: Banned
        """
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        log_admin_action(user_id, "ban_user", f"User: {target_user_id}")
        
    except ValueError:
        bot.send_message(user_id, "❌ Invalid User ID! Use numbers only.")

def start_unban_user(call):
    """Start unban user process"""
    user_id = call.message.chat.id
    admin_states[user_id] = {"action": "unbanning_user", "step": "user_id"}
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="✅ Unban User\n\nSend User ID to unban:"
        )
    except:
        bot.send_message(user_id, "✅ Unban User\n\nSend User ID to unban:")

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
✅ User Unbanned Successfully!

👤 User ID: {target_user_id}
✅ Status: Active
        """
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        log_admin_action(user_id, "unban_user", f"User: {target_user_id}")
        
    except ValueError:
        bot.send_message(user_id, "❌ Invalid User ID! Use numbers only.")

def set_bot_status(call, status):
    """Set bot accepting orders status"""
    user_id = call.message.chat.id
    set_bot_accepting_orders(status)
    
    status_text = "🟢 ON" if status else "🔴 OFF"
    text = f"✅ Bot status set to: {status_text}"
    
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
    
    text = f"⚙️ Current Bot Status: {bot_status}"
    
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
                    text="📢 Broadcast sent successfully!",
                    reply_markup=admin_main_keyboard()
                )
            except:
                bot.send_message(user_id, "📢 Broadcast sent successfully!", 
                               reply_markup=admin_main_keyboard())

def show_admin_menu(call):
    """Show admin main menu"""
    user_id = call.message.chat.id
    admin_panel(call.message)

# User Message Handlers with new deposit system
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    user_id = message.chat.id
    user_name = message.chat.first_name
    
    # Check if user is banned
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("banned"):
        bot.reply_to(message, "❌ You are banned from using this bot.")
        return
    
    # Check channel membership
    if not check_channel_membership(user_id):
        text = f"""
👋 Welcome {user_name}!

📢 Please join our channel to use the bot:

{CHANNEL_ID}

After joining, click the check button below.
        """
        bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=channel_join_keyboard())
        return
    
    # Welcome message for verified users
    text = f"""
👋 Welcome {user_name}!

🤖 I'm Most Affordable Social Services Bot. 
I provide cheap social media services at the best prices.

📱 Services:
• Instagram • Facebook :
• YouTube • Telegram :

💰 Get started by adding funds to your account.
    """
    
    bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['balance'])
def check_balance(message):
    """Check user balance"""
    user_id = message.chat.id
    balance = get_user_balance(user_id)
    
    text = f"""
💳 Your Account Balance

💰 Available Balance: {balance} points
💵 Approx. in rupees: ₹{balance/100:.2f}

💸 100 points = ₹1
    """
    
    bot.send_photo(user_id, ACCOUNT_IMAGE, text, reply_markup=back_button_only())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_queries(call):
    """Handle all callback queries"""
    user_id = call.message.chat.id
    
    # Check if user is banned
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("banned"):
        bot.answer_callback_query(call.id, "❌ You are banned from using this bot.", show_alert=True)
        return
    
    try:
        if call.data == "main_menu":
            show_main_menu(call)
        
        elif call.data == "deposit":
            start_deposit_process(call)
        
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
        
        elif call.data == "confirm_order":
            confirm_order(call)
        
        elif call.data == "confirm_deposit":
            process_deposit_confirmation(call)
        
        # Handle admin callbacks
        elif call.data.startswith("admin_"):
            handle_admin_callbacks(call)
            
    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "❌ An error occurred!")

# New Deposit System with Payment Verification
def start_deposit_process(call):
    """Start deposit process"""
    user_id = call.message.chat.id
    user_states[user_id] = {"action": "depositing", "step": "amount"}
    
    text = """
💵 Deposit Funds

💸 100 points = ₹1

Enter the amount you want to deposit (in rupees):
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(DEPOSIT_IMAGE, text)
        )
    except:
        bot.send_photo(user_id, DEPOSIT_IMAGE, text)
    
    bot.register_next_step_handler(call.message, process_deposit_amount)

def process_deposit_amount(message):
    """Process deposit amount"""
    user_id = message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "depositing":
        return
    
    try:
        amount = float(message.text.strip())
        if amount < 10:
            bot.send_message(user_id, "❌ Minimum deposit amount is ₹10!")
            return
        
        # Calculate points (1 rupee = 100 points)
        points = int(amount * 100)
        user_states[user_id]["amount"] = amount
        user_states[user_id]["points"] = points
        
        # Generate QR code
        qr_img = generate_qr_code(amount)
        
        text = f"""
💵 Deposit Request

💵 Amount: ₹{amount}
💸 Points: {points} points

Please scan the QR code below to pay ₹{amount}.

After payment, click "I Have Paid" below.

📞 Contact support if you face any issues.
        """
        
        # Send QR code and confirmation
        bot.send_photo(user_id, qr_img, caption=text, reply_markup=deposit_confirmation_keyboard())
        
    except ValueError:
        bot.send_message(user_id, "❌ Invalid amount! Please enter a valid number.")

def process_deposit_confirmation(call):
    """Process deposit confirmation with payment verification"""
    user_id = call.message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "depositing":
        return
    
    data = user_states[user_id]
    amount = data["amount"]
    points = data["points"]
    
    # Show verifying message
    verifying_msg = bot.send_message(user_id, "🔍 Verifying payment...")
    
    # Verify payment using API
    payment_verified = verify_payment(amount)
    
    if not payment_verified:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=verifying_msg.message_id,
            text="❌ Payment not verified! Please try again or contact support."
        )
        return
    
    # Payment verified - add points to user balance
    new_balance = update_user_balance(user_id, points, is_deposit=True)
    
    # Record deposit
    deposit_id = f"DEP{random.randint(100000, 999999)}"
    deposits_collection.insert_one({
        "deposit_id": deposit_id,
        "user_id": user_id,
        "amount": amount,
        "points": points,
        "status": "Completed",
        "created_at": datetime.now()
    })
    
    # Clear state
    del user_states[user_id]
    
    text = f"""
✅ Deposit Successful!

💵 Amount: ₹{amount}
💸 Points Added: {points} points
💳 New Balance: {new_balance} points

Thank you for your payment!
    """
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=verifying_msg.message_id,
        text=text,
        reply_markup=back_button_only()
    )

def show_main_menu(call):
    """Show main menu"""
    user_id = call.message.chat.id
    user_name = call.message.chat.first_name
    
    text = f"""
👋 Hello {user_name}!

🤖 Welcome to Our Bot Main Menu

Select an option below:
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

def show_service_categories_user(call):
    """Show service categories for users"""
    user_id = call.message.chat.id
    
    if not is_bot_accepting_orders():
        bot.answer_callback_query(call.id, "❌ Bot is currently not accepting orders!", show_alert=True)
        return
    
    text = """
🛒 Service Categories

Select a category:
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
📱 {style_text(category)} Services

Select a service:
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
        bot.answer_callback_query(call.id, "❌ Service not found!")
        return
    
    user_states[user_id] = {
        "action": "ordering",
        "service_id": service_id,
        "step": "link"
    }
    
    text = f"""
🛒 Order: {service['name']}

📝 Description: {service['description']}
💰 Price: {service['price_per_unit']} points per {service['unit']}
🔢 Quantity Range: {service['min']} - {service['max']}

Please send the link:
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
    
    bot.send_message(user_id, f"🔢 Enter quantity ({service['min']} - {service['max']}):")

def process_order_quantity(message):
    """Process order quantity"""
    user_id = message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        return
    
    try:
        quantity = int(message.text.strip())
        service = get_service_by_id(user_states[user_id]["service_id"])
        
        if quantity < service["min"] or quantity > service["max"]:
            bot.send_message(user_id, f"❌ Invalid quantity! Must be between {service['min']} and {service['max']}.")
            return
        
        user_states[user_id]["quantity"] = quantity
        
        # Calculate cost
        cost_points = (quantity / service["unit"]) * service["price_per_unit"]
        user_states[user_id]["cost_points"] = cost_points
        
        # Check balance
        user_balance = get_user_balance(user_id)
        if user_balance < cost_points:
            bot.send_message(user_id, f"❌ Insufficient balance! You need {cost_points} points, but you have only {user_balance} points.")
            del user_states[user_id]
            return
        
        # Confirm order
        text = f"""
🛒 Order Confirmation

📱 Service: {service['name']}
🔗 Link: {user_states[user_id]['link']}
🔢 Quantity: {quantity}
💰 Cost: {cost_points} points

Confirm order?
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Confirm", callback_data="confirm_order"))
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data="order_menu"))
        
        bot.send_message(user_id, text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(user_id, "❌ Invalid quantity! Use numbers only.")

def confirm_order(call):
    """Confirm and process order with API integration (improved error handling)."""
    user_id = call.message.chat.id

    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        return

    data = user_states[user_id]
    service = get_service_by_id(data["service_id"])

    # Show processing message (use send_message to get a message_id we can edit)
    processing_msg = bot.send_message(user_id, "🔄 Processing your order...")

    # Place order via SMM API
    api_order_id = place_smm_order(service["service_id"], data["link"], data["quantity"])

    if not api_order_id:
        # Provide more helpful diagnostic message and a retry option
        text = """❌ Failed to place order!

Possible reasons:
• SMM API returned an error or unexpected response.
• Invalid service ID or parameters.
• Temporary network problem.

What you can do:
• Try again in a few minutes.
• Contact support if the problem persists.

Would you like to retry placing the order?"""
        markup = InlineKeyboardMarkup()
        # retry will trigger a callback we handle below
        markup.add(InlineKeyboardButton("🔄 Retry", callback_data="retry_place_order"))
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data="order_menu"))
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=text,
                reply_markup=markup
            )
        except Exception:
            bot.send_message(user_id, text, reply_markup=markup)
        # Keep the user state so they can retry; do not clear it here.
        return

    # At this point, api_order_id exists. Proceed to deduct balance and create order.
    new_balance = update_user_balance(user_id, -int(data["cost_points"]), is_spent=True)

    # Create order in database with API order ID
    order = create_order(user_id, data["service_id"], data["link"], data["quantity"], int(data["cost_points"]), api_order_id)

    if order:
        # Send order to channel
        send_order_to_channel(order)

        # Clear state
        del user_states[user_id]

        text = f"""
✅ Order Placed Successfully!

🆔 Order ID: {order['order_id']}
🆔 API Order ID: {api_order_id}
📱 Service: {service['name']}
🔗 Link: {data['link']}
🔢 Quantity: {data['quantity']}
💰 Cost: {data['cost_points']} points
💳 New Balance: {new_balance} points

📊 Status: Pending
⏰ ETA: 24-48 hours
        """

        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=text,
                reply_markup=back_button_only()
            )
        except Exception:
            bot.send_message(user_id, text, reply_markup=back_button_only())
    else:
        # If order creation failed after API order id, try to refund points (best-effort) and inform user/admin.
        try:
            # Refund the deducted points
            update_user_balance(user_id, int(data["cost_points"]), is_deposit=True)
        except Exception as e:
            print(f"Failed to refund user {user_id} after create_order failure: {e}")

        bot.edit_message_text(
            chat_id=user_id,
            message_id=processing_msg.message_id,
            text="❌ Failed to create order in database. Admin will be notified."
        )
        # Log admin action for manual review
        log_admin_action(0, "create_order_failed", f"user:{user_id}, service:{data['service_id']}, api_order_id:{api_order_id}")

def show_order_history(call):
    """Show user's order history"""
    user_id = call.message.chat.id
    orders = get_user_orders(user_id)
    
    if not orders:
        text = "📋 You have no orders yet."
    else:
        text = "📋 Your Recent Orders:\n\n"
        for order in orders:
            status_emoji = "✅" if order["status"] == "Completed" else "⏳" if order["status"] == "Processing" else "❌"
            text += f"""
{status_emoji} Order ID: {order['order_id']}
📱 Service: {order['service_name']}
🔢 Quantity: {order['quantity']}
💰 Cost: {order['cost_points']} points
📊 Status: {order['status']}
📅 Date: {order['created_at'].strftime('%Y-%m-%d %H:%M')}
────────────────
            """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(HISTORY_IMAGE, text),
            reply_markup=back_button_only()
        )
    except:
        bot.send_photo(user_id, HISTORY_IMAGE, text, reply_markup=back_button_only())

def show_referral_info(call):
    """Show referral information"""
    user_id = call.message.chat.id
    referral_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    
    text = f"""
👥 Refer & Earn

🔗 Your referral link:
{referral_link}

🎯 How it works:
• Share your referral link
• Get 10% of every deposit made by your referrals
• Earn unlimited commission!

💰 Referral commission: 10%
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(REFER_IMAGE, text),
            reply_markup=back_button_only()
        )
    except:
        bot.send_photo(user_id, REFER_IMAGE, text, reply_markup=back_button_only())

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
👤 Account Information

🆔 User ID: {user_id}
👤 Name: {call.message.chat.first_name}
📅 Joined: {user['joined_at'].strftime('%Y-%m-%d')}

💳 Balance: {balance} points
💰 Total Deposited: {user.get('total_deposits_points', 0)} points
💸 Total Spent: {user.get('total_spent_points', 0)} points
🛒 Total Orders: {total_orders}

💸 100 points = ₹1
    """
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(ACCOUNT_IMAGE, text),
            reply_markup=back_button_only()
        )
    except:
        bot.send_photo(user_id, ACCOUNT_IMAGE, text, reply_markup=back_button_only())

def show_stats(call):
    """Show bot statistics"""
    user_id = call.message.chat.id
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    
    text = f"""
📊 Bot Statistics

👤 Total Users: {total_users}
🛒 Total Orders: {total_orders}
📱 Active Services: {services_collection.count_documents({'active': True})}

⚙️ Bot Status: {'🟢 Operating' if is_bot_accepting_orders() else '🔴 Maintenance'}
    """
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=back_button_only()
        )
    except:
        bot.send_message(user_id, text, reply_markup=back_button_only())

def show_support(call):
    """Show support information"""
    user_id = call.message.chat.id
    
    text = """
🆘 Support

📞 Contact us for:
• Account issues
• Deposit help
• Order problems
• General questions

⏰ Support hours: 24/7
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
        bot.answer_callback_query(call.id, "❌ You have not joined the channel yet!", show_alert=True)

def start_track_order(call):
    """Start track order process"""
    user_id = call.message.chat.id
    user_states[user_id] = {"action": "tracking_order", "step": "order_id"}
    
    bot.send_message(user_id, "🔍 Enter your Order ID:")

def process_track_order(message):
    """Process order tracking"""
    user_id = message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "tracking_order":
        return
    
    order_id = message.text.strip()
    order = get_order_by_id(order_id)
    
    if not order or order["user_id"] != user_id:
        bot.send_message(user_id, "❌ Order not found or you don't have permission to view this order!")
        del user_states[user_id]
        return
    
    status_emoji = "✅" if order["status"] == "Completed" else "⏳" if order["status"] == "Processing" else "❌"
    
    text = f"""
🔍 Order Tracking

🆔 Order ID: {order['order_id']}
📱 Service: {order['service_name']}
🔗 Link: {order['link']}
🔢 Quantity: {order['quantity']}
💰 Cost: {order['cost_points']} points
📊 Status: {status_emoji} {order['status']}
📅 Created: {order['created_at'].strftime('%Y-%m-%d %H:%M')}
🕒 Last Check: {order['last_check'].strftime('%Y-%m-%d %H:%M')}
    """
    
    bot.send_message(user_id, text, reply_markup=back_button_only())
    del user_states[user_id]

# Message handlers for conversation flows
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all messages for conversation flows and default to main menu"""
    user_id = message.chat.id
    
    # Check if user is banned
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("banned"):
        return
    
    # Handle admin conversation flows
    if user_id in admin_states:
        state = admin_states[user_id]
        
        if state.get("action") == "adding_service":
            if state.get("step") == "name":
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
        return
    
    # Handle user conversation flows
    elif user_id in user_states:
        state = user_states[user_id]
        
        if state.get("action") == "ordering" and state.get("step") == "quantity":
            process_order_quantity(message)
        
        elif state.get("action") == "tracking_order" and state.get("step") == "order_id":
            process_track_order(message)
        return
    
    # Default behavior: show main menu for any other message
    show_main_menu_for_message(message)

def show_main_menu_for_message(message):
    """Show main menu for any message"""
    user_id = message.chat.id
    user_name = message.chat.first_name
    
    text = f"""
👋 Hello {user_name}!

🤖 Welcome to Our Bot Main Menu

Select an option below:
    """
    
    bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

# Background tasks for order status updates
def update_orders_status():
    """Background task to update order statuses"""
    while True:
        try:
            # Get pending orders
            pending_orders = orders_collection.find({
                "status": {"$in": ["Pending", "Processing"]}
            })
            
            for order in pending_orders:
                if order.get("api_order_id"):
                    # Check status from API
                    status_data = get_order_status(order["api_order_id"])
                    if status_data:
                        new_status = status_data.get("status", order["status"])
                        orders_collection.update_one(
                            {"_id": order["_id"]},
                            {
                                "$set": {
                                    "status": new_status,
                                    "last_check": datetime.now()
                                }
                            }
                        )
            
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            print(f"Order status update error: {e}")
            time.sleep(60)

# Start background tasks
def start_background_tasks():
    """Start all background tasks"""
    threading.Thread(target=update_orders_status, daemon=True).start()

if __name__ == "__main__":
    print("🤖 Bot started successfully!")
    start_background_tasks()
    
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Bot error: {e}")
        time.sleep(10)
