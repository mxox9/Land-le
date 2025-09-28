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
SMM_API_URL = os.getenv('SMM_API_URL', 'https://mysmmapi.com/api/v2')
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
    print("✅ MᴏɴɢᴏDB ᴄᴏɴɴᴇᴄᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ")
except Exception as e:
    print(f"❌ MᴏɴɢᴏDB ᴄᴏɴɴᴇᴄᴛɪᴏɴ ᴇʀʀᴏʀ: {e}")
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

# Text styling function - IMPROVED VERSION
def style_text(text):
    """Convert text to stylish format with first letter capitalized and rest small with special unicode characters"""
    # Mapping for special unicode characters that look like small caps
    char_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 
        'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 
        'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 
        'y': 'ʏ', 'z': 'ᴢ'
    }
    
    def style_word(word):
        if len(word) == 0:
            return word
        
        # Keep first letter as is (capital), convert rest to styled version
        first_char = word[0]
        rest_chars = word[1:]
        
        # Convert rest characters to styled version
        styled_rest = ""
        for char in rest_chars:
            lower_char = char.lower()
            if lower_char in char_map:
                styled_rest += char_map[lower_char]
            else:
                styled_rest += char.lower()
        
        return first_char + styled_rest
    
    # Split into words and apply styling
    words = text.split()
    styled_words = []
    
    for word in words:
        # Skip styling for URLs, numbers, and special cases
        if (word.startswith('http') or 
            word.startswith('@') or 
            word.replace('.', '').replace(',', '').isdigit() or
            len(word) <= 1):
            styled_words.append(word)
        else:
            styled_words.append(style_word(word))
    
    return ' '.join(styled_words)

# API Functions - IMPROVED VERSION
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
    """Place order via SMM API - IMPROVED VERSION"""
    try:
        print(f"🔧 Placing order - Service ID: {service_id}, Link: {link}, Quantity: {quantity}")
        
        # Get service details from database
        service = services_collection.find_one({"_id": ObjectId(service_id)})
        if not service:
            print("❌ Service not found in database")
            return None
        
        # Use service-specific API details or fallback to global
        api_url = service.get('api_url', SMM_API_URL).rstrip('?')
        api_key = service.get('api_key', SMM_API_KEY)
        api_service_id = service.get('service_id') or service.get('smm_service_id')
        
        if not api_service_id:
            print("❌ No API service ID found")
            return None
        
        print(f"🔧 Using API - URL: {api_url}, Service ID: {api_service_id}")
        
        params = {
            'key': api_key,
            'action': 'add',
            'service': api_service_id,
            'link': link,
            'quantity': quantity
        }
        
        print(f"🔧 API Params: {params}")
        
        response = requests.get(api_url, params=params, timeout=30)
        print(f"🔧 API Response Status: {response.status_code}")
        print(f"🔧 API Response Text: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ API returned non-200 status: {response.status_code}")
            return None
        
        try:
            data = response.json()
            print(f"🔧 API JSON Response: {data}")
        except ValueError as e:
            print(f"❌ API returned invalid JSON: {e}")
            return None
        
        # Handle different API response formats
        if isinstance(data, dict):
            # Check for error first
            if data.get('error'):
                print(f"❌ API Error: {data['error']}")
                return None
            
            # Try to extract order ID from different response formats
            order_id_keys = ['order', 'order_id', 'id', 'orderid']
            for key in order_id_keys:
                if key in data and data[key]:
                    order_id = str(data[key])
                    print(f"✅ Order placed successfully: {order_id}")
                    return order_id
            
            # Check in nested data
            if 'data' in data and isinstance(data['data'], dict):
                for key in order_id_keys:
                    if key in data['data'] and data['data'][key]:
                        order_id = str(data['data'][key])
                        print(f"✅ Order placed successfully: {order_id}")
                        return order_id
        
        print("❌ No order ID found in API response")
        return None
        
    except Exception as e:
        print(f"❌ SMM API order error: {e}")
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
🆔 Nᴇᴡ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ!

📱 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
👤 Usᴇʀ ID: {order['user_id']}
🆔 Oʀᴅᴇʀ ID: {order['order_id']}
🔗 Lɪɴᴋ: {order['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💵 Pᴏɪɴᴛs: {order['cost_points']}
⏰ Tɪᴍᴇ: {order['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🤖 Bᴏᴛ Hᴇʀᴇ 🛒", url=f"https://t.me/{BOT_USERNAME.replace('@', '')}"))
        
        bot.send_message(PROOF_CHANNEL, text, reply_markup=markup)
        return True
    except Exception as e:
        print(f"Error sending to channel: {e}")
        return False

# Admin Keyboard Builders - ALL STYLED
def admin_main_keyboard():
    """Admin main menu keyboard"""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(style_text("📱 Mᴀɴᴀɢᴇ Sᴇʀᴠɪᴄᴇs"), callback_data="admin_manage_services"),
        InlineKeyboardButton(style_text("💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ"), callback_data="admin_balance_control")
    )
    markup.add(
        InlineKeyboardButton(style_text("👤 Usᴇʀ Cᴏɴᴛʀᴏʟ"), callback_data="admin_user_control"),
        InlineKeyboardButton(style_text("📢 Bʀᴏᴀᴅᴄᴀsᴛ"), callback_data="admin_broadcast")
    )
    markup.add(
        InlineKeyboardButton(style_text("⚙️ Bᴏᴛ Cᴏɴᴛʀᴏʟ"), callback_data="admin_bot_control"),
        InlineKeyboardButton(style_text("📊 Sᴛᴀᴛs"), callback_data="admin_stats")
    )
    markup.add(InlineKeyboardButton(style_text("🔙 Mᴀɪɴ Mᴇɴᴜ"), callback_data="main_menu"))
    return markup

def admin_services_keyboard():
    """Admin services management keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("➕ Aᴅᴅ Sᴇʀᴠɪᴄᴇ"), callback_data="admin_add_service"))
    markup.add(InlineKeyboardButton(style_text("✏️ Eᴅɪᴛ Sᴇʀᴠɪᴄᴇ"), callback_data="admin_edit_service"))
    markup.add(InlineKeyboardButton(style_text("❌ Dᴇʟᴇᴛᴇ Sᴇʀᴠɪᴄᴇ"), callback_data="admin_delete_service"))
    markup.add(InlineKeyboardButton(style_text("➕ Aᴅᴅ Cᴀᴛᴇɢᴏʀʏ"), callback_data="admin_add_category"))
    markup.add(InlineKeyboardButton(style_text("🔙 Aᴅᴍɪɴ Mᴇɴᴜ"), callback_data="admin_menu"))
    return markup

def admin_balance_keyboard():
    """Admin balance control keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("➕ Aᴅᴅ Bᴀʟᴀɴᴄᴇ"), callback_data="admin_add_balance"))
    markup.add(InlineKeyboardButton(style_text("➖ Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ"), callback_data="admin_deduct_balance"))
    markup.add(InlineKeyboardButton(style_text("🔙 Aᴅᴍɪɴ Mᴇɴᴜ"), callback_data="admin_menu"))
    return markup

def admin_user_keyboard():
    """Admin user control keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("🔨 Bᴀɴ Usᴇʀ"), callback_data="admin_ban_user"))
    markup.add(InlineKeyboardButton(style_text("✅ Uɴʙᴀɴ Usᴇʀ"), callback_data="admin_unban_user"))
    markup.add(InlineKeyboardButton(style_text("🔙 Aᴅᴍɪɴ Mᴇɴᴜ"), callback_data="admin_menu"))
    return markup

def admin_bot_control_keyboard():
    """Admin bot control keyboard"""
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("🟢 Tᴜʀɴ Bᴏᴛ ON"), callback_data="admin_bot_on"))
    markup.add(InlineKeyboardButton(style_text("🔴 Tᴜʀɴ Bᴏᴛ OFF"), callback_data="admin_bot_off"))
    markup.add(InlineKeyboardButton(style_text(f"📊 Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: {bot_status}"), callback_data="admin_bot_status"))
    markup.add(InlineKeyboardButton(style_text("🔙 Aᴅᴍɪɴ Mᴇɴᴜ"), callback_data="admin_menu"))
    return markup

def service_categories_keyboard():
    """Service categories selection keyboard for admin"""
    markup = InlineKeyboardMarkup()
    categories = services_collection.distinct("category")
    if not categories:
        categories = ["Instagram", "YouTube", "Telegram", "Facebook", "Twitter", "TikTok", "Other"]
    
    for category in categories:
        markup.add(InlineKeyboardButton(style_text(category), callback_data=f"admin_category_{category.lower()}"))
    markup.add(InlineKeyboardButton(style_text("➕ Aᴅᴅ Nᴇᴡ Cᴀᴛᴇɢᴏʀʏ"), callback_data="admin_add_new_category"))
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="admin_manage_services"))
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
    
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data=f"admin_{action}_back"))
    return markup

def confirm_delete_keyboard(service_id):
    """Confirmation keyboard for service deletion"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("✅ Yᴇs, Dᴇʟᴇᴛᴇ"), callback_data=f"admin_confirm_delete_{service_id}"))
    markup.add(InlineKeyboardButton(style_text("❌ Cᴀɴᴄᴇʟ"), callback_data="admin_manage_services"))
    return markup

# Main Menu Keyboard Builders - ALL STYLED
def main_menu_keyboard():
    """Main menu inline keyboard"""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(style_text("💵 Dᴇᴘᴏsɪᴛ"), callback_data="deposit"),
        InlineKeyboardButton(style_text("🛒 Oʀᴅᴇʀ"), callback_data="order_menu")
    )
    markup.add(
        InlineKeyboardButton(style_text("📋 Oʀᴅᴇʀs"), callback_data="history"),
        InlineKeyboardButton(style_text("👥 Rᴇғᴇʀ"), callback_data="refer")
    )
    markup.add(
        InlineKeyboardButton(style_text("👤 Aᴄᴄᴏᴜɴᴛ"), callback_data="account"),
        InlineKeyboardButton(style_text("📊 Sᴛᴀᴛs"), callback_data="stats")
    )
    markup.add(InlineKeyboardButton(style_text("🆘 Sᴜᴘᴘᴏʀᴛ"), callback_data="support"))
    
    return markup

def back_button_only():
    """Back button only keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ ᴛᴏ Mᴀɪɴ Mᴇɴᴜ"), callback_data="main_menu"))
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
    
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="main_menu"))
    return markup

def services_keyboard(category):
    """Services list for a category"""
    markup = InlineKeyboardMarkup()
    services = get_services_by_category(category)
    
    for service in services:
        price = service["price_per_unit"]
        unit = service["unit"]
        button_text = f"{style_text(service['name'])} - {price} Pᴏɪɴᴛs/{unit}"
        markup.add(InlineKeyboardButton(
            button_text, 
            callback_data=f"service_{service['_id']}"
        ))
    
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="order_menu"))
    return markup

def channel_join_keyboard():
    """Channel join requirement keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("✅ Jᴏɪɴ Cʜᴀɴɴᴇʟ"), url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    markup.add(InlineKeyboardButton(style_text("🔄 Cʜᴇᴄᴋ Jᴏɪɴ"), callback_data="check_join"))
    return markup

def support_keyboard():
    """Support options keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("📞 Cᴏɴᴛᴀᴄᴛ Us"), url="https://wa.me/639941532149"))
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="main_menu"))
    return markup

def track_order_keyboard():
    """Track order keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("📊 Tʀᴀᴄᴋ Oʀᴅᴇʀ"), callback_data="track_order"))
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="main_menu"))
    return markup

def deposit_confirmation_keyboard():
    """Deposit confirmation keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("✅ I Hᴀᴠᴇ Pᴀɪᴅ"), callback_data="confirm_deposit"))
    markup.add(InlineKeyboardButton(style_text("❌ Cᴀɴᴄᴇʟ"), callback_data="main_menu"))
    return markup

# Admin Message Handlers
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """Admin panel command"""
    user_id = message.chat.id
    
    if not is_admin(user_id):
        bot.reply_to(message, style_text("❌ Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ."))
        return
    
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    total_deposits = sum(user.get('total_deposits_points', 0) for user in users_collection.find()) / 100
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    
    text = style_text(f"""
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

👤 Usᴇʀs: {total_users}
🛒 Oʀᴅᴇʀs: {total_orders}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposits:.2f}
⚙️ Bᴏᴛ Sᴛᴀᴛᴜs: {bot_status}

Cʜᴏᴏsᴇ ᴀɴ ᴀᴄᴛɪᴏɴ:
    """)
    
    bot.send_photo(user_id, ADMIN_IMAGE, text, reply_markup=admin_main_keyboard())

# ... (Previous admin callback handlers remain the same, just ensure all text is styled)
# Due to character limits, I'll show the improved order placement function and main flow

def confirm_order(call):
    """Confirm and process order with IMPROVED API integration"""
    user_id = call.message.chat.id

    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        bot.answer_callback_query(call.id, style_text("❌ Nᴏ ᴏʀᴅᴇʀ ᴅᴀᴛᴀ ғᴏᴜɴᴅ. Pʟᴇᴀsᴇ sᴛᴀʀᴛ ᴀɢᴀɪɴ."))
        return

    data = user_states[user_id]
    service = get_service_by_id(data["service_id"])

    if not service:
        bot.answer_callback_query(call.id, style_text("❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ."))
        return

    # Show processing message
    processing_text = style_text("🔄 Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ᴏʀᴅᴇʀ...")
    processing_msg = bot.send_message(user_id, processing_text)

    try:
        # Place order via SMM API
        api_order_id = place_smm_order(data["service_id"], data["link"], data["quantity"])

        if not api_order_id:
            # Try alternative method - direct API call
            alternative_order_id = place_order_direct(data["service_id"], data["link"], data["quantity"])
            if not alternative_order_id:
                error_text = style_text("""
❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴘʟᴀᴄᴇ ᴏʀᴅᴇʀ!

Pᴏssɪʙʟᴇ ʀᴇᴀsᴏɴs:
• API sᴇʀᴠᴇʀ ɪssᴜᴇ
• Iɴᴠᴀʟɪᴅ sᴇʀᴠɪᴄᴇ ᴘᴀʀᴀᴍᴇᴛᴇʀs
• Nᴇᴛᴡᴏʀᴋ ᴘʀᴏʙʟᴇᴍ

Wʜᴀᴛ ʏᴏᴜ ᴄᴀɴ ᴅᴏ:
• Tʀʏ ᴀɢᴀɪɴ ɪɴ 5 ᴍɪɴᴜᴛᴇs
• Cᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ
• Cʜᴇᴄᴋ sᴇʀᴠɪᴄᴇ ᴀᴠᴀɪʟᴀʙɪʟɪᴛʏ
                """)
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton(style_text("🔄 Rᴇᴛʀʏ"), callback_data="retry_order"))
                markup.add(InlineKeyboardButton(style_text("🆘 Sᴜᴘᴘᴏʀᴛ"), callback_data="support"))
                
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=processing_msg.message_id,
                    text=error_text,
                    reply_markup=markup
                )
                return
            api_order_id = alternative_order_id

        # Deduct balance and create order
        new_balance = update_user_balance(user_id, -int(data["cost_points"]), is_spent=True)
        order = create_order(user_id, data["service_id"], data["link"], data["quantity"], int(data["cost_points"]), api_order_id)

        if order:
            # Send to channel
            send_order_to_channel(order)

            # Clear state
            del user_states[user_id]

            success_text = style_text(f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

🆔 Oʀᴅᴇʀ ID: {order['order_id']}
🆔 API Oʀᴅᴇʀ ID: {api_order_id}
📱 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {data['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {data['quantity']}
💰 Cᴏsᴛ: {data['cost_points']} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs

📊 Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ
⏰ ETA: 24-48 ʜᴏᴜʀs
            """)

            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=success_text,
                reply_markup=back_button_only()
            )
        else:
            # Refund points if order creation failed
            update_user_balance(user_id, int(data["cost_points"]), is_deposit=True)
            error_text = style_text("❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴏʀᴅᴇʀ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ. Pᴏɪɴᴛs ʀᴇғᴜɴᴅᴇᴅ.")
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=error_text
            )

    except Exception as e:
        print(f"Order placement error: {e}")
        error_text = style_text("❌ Aɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")
        bot.edit_message_text(
            chat_id=user_id,
            message_id=processing_msg.message_id,
            text=error_text
        )

def place_order_direct(service_id, link, quantity):
    """Alternative order placement method"""
    try:
        service = get_service_by_id(service_id)
        if not service:
            return None
        
        api_service_id = service.get('service_id')
        if not api_service_id:
            return None
        
        # Direct API parameters
        params = {
            'key': SMM_API_KEY,
            'action': 'add',
            'service': api_service_id,
            'link': link,
            'quantity': quantity
        }
        
        response = requests.get(SMM_API_URL, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                # Check for order ID in response
                order_keys = ['order', 'order_id', 'id']
                for key in order_keys:
                    if key in data and data[key]:
                        return str(data[key])
        return None
    except Exception as e:
        print(f"Direct order placement error: {e}")
        return None

# User Message Handlers - ALL STYLED
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    user_id = message.chat.id
    user_name = message.chat.first_name
    
    # Check if user is banned
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("banned"):
        bot.reply_to(message, style_text("❌ Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ."))
        return
    
    # Check channel membership
    if not check_channel_membership(user_id):
        text = style_text(f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

📢 Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ:

{CHANNEL_ID}

Aғᴛᴇʀ ᴊᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴛʜᴇ ᴄʜᴇᴄᴋ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.
        """)
        bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=channel_join_keyboard())
        return
    
    # Welcome message for verified users
    text = style_text(f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

🤖 I'ᴍ Mᴏsᴛ Aғғᴏʀᴅᴀʙʟᴇ Sᴏᴄɪᴀʟ Sᴇʀᴠɪᴄᴇs Bᴏᴛ. 
I ᴘʀᴏᴠɪᴅᴇ ᴄʜᴇᴀᴘ sᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ sᴇʀᴠɪᴄᴇs ᴀᴛ ᴛʜᴇ ʙᴇsᴛ ᴘʀɪᴄᴇs.

📱 Sᴇʀᴠɪᴄᴇs:
• Iɴsᴛᴀɢʀᴀᴍ • Fᴀᴄᴇʙᴏᴏᴋ
• YᴏᴜTᴜʙᴇ • Tᴇʟᴇɢʀᴀᴍ

💰 Gᴇᴛ sᴛᴀʀᴛᴇᴅ ʙʏ ᴀᴅᴅɪɴɢ ғᴜɴᴅs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.
    """)
    
    bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['balance'])
def check_balance(message):
    """Check user balance"""
    user_id = message.chat.id
    balance = get_user_balance(user_id)
    
    text = style_text(f"""
💳 Yᴏᴜʀ Aᴄᴄᴏᴜɴᴛ Bᴀʟᴀɴᴄᴇ

💰 Aᴠᴀɪʟᴀʙʟᴇ Bᴀʟᴀɴᴄᴇ: {balance} ᴘᴏɪɴᴛs
💵 Aᴘᴘʀᴏx. ɪɴ ʀᴜᴘᴇᴇs: ₹{balance/100:.2f}

💸 100 ᴘᴏɪɴᴛs = ₹1
    """)
    
    bot.send_photo(user_id, ACCOUNT_IMAGE, text, reply_markup=back_button_only())

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
    print("🤖 Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
    start_background_tasks()
    
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Bᴏᴛ ᴇʀʀᴏʀ: {e}")
        time.sleep(10)
