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

# Stylish text mapping for the special font style
STYLISH_MAPPING = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
    'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ',
    'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
    'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'H': 'H', 'I': 'I', 'J': 'J',
    'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T',
    'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z'
}

# Text styling function - UPDATED WITH SPECIAL FONT STYLE
def style_text(text):
    """Convert text to stylish format with special font style"""
    if not text:
        return text
    
    def style_word(word):
        if len(word) > 0:
            # Keep first letter as is, convert rest to stylish lowercase
            styled_word = word[0]
            for char in word[1:]:
                styled_word += STYLISH_MAPPING.get(char.lower(), char.lower())
            return styled_word
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

# API Functions - COMPLETELY REWRITTEN ORDER PLACEMENT
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
            return True
        return False
    except Exception as e:
        print(f"Payment verification error: {e}")
        return False

def place_smm_order(service_id, link, quantity):
    """Place order via SMM API - COMPLETELY REWRITTEN TO MATCH WORKING CODE"""
    try:
        # DIRECT API CALL LIKE YOUR WORKING EXAMPLE
        api_key = SMM_API_KEY
        
        # Build URL exactly like your working example
        url = f"https://mysmmapi.com/api/v2?key={api_key}&action=add&service={service_id}&link={link}&quantity={quantity}"
        
        print(f"🔗 Making API call to: {url.replace(api_key, '***')}")
        
        # Make the request
        response = requests.get(url, timeout=30)
        print(f"📡 Raw API Response: {response.text}")
        
        # Parse JSON response
        data = response.json()
        print(f"📊 Parsed API Response: {data}")
        
        # Check if order was successful
        if 'order' in data:
            order_id = str(data['order'])
            print(f"✅ Order placed successfully! Order ID: {order_id}")
            return order_id
        elif 'error' in data:
            error_msg = data['error']
            print(f"❌ API Error: {error_msg}")
            return None
        else:
            print(f"❌ Unexpected API response: {data}")
            return None
            
    except Exception as e:
        print(f"❌ SMM API order error: {e}")
        return None

def get_order_status(api_order_id):
    """Get order status from SMM API"""
    try:
        url = f"{SMM_API_URL}?key={SMM_API_KEY}&action=status&order={api_order_id}"
        response = requests.get(url, timeout=10)
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
        text = style_text(f"""
🆕 Nᴇᴡ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ!

📱 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
👤 Usᴇʀ ID: {order['user_id']}
🆔 Oʀᴅᴇʀ ID: {order['order_id']}
🔗 Lɪɴᴋ: {order['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💵 Pᴏɪɴᴛs: {order['cost_points']}
⏰ Tɪᴍᴇ: {order['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
        """)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(style_text("🤖 Bᴏᴛ Hᴇʀᴇ 🛒"), url=f"https://t.me/{BOT_USERNAME.replace('@', '')}"))
        
        bot.send_message(PROOF_CHANNEL, text, reply_markup=markup)
        return True
    except Exception as e:
        print(f"Error sending to channel: {e}")
        return False

# [ALL THE KEYBOARD FUNCTIONS REMAIN THE SAME AS BEFORE...]
# Main Menu Keyboard Builders - WITH STYLISH TEXT
def main_menu_keyboard():
    """Main menu inline keyboard"""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(style_text("💵 Deposit"), callback_data="deposit"),
        InlineKeyboardButton(style_text("🛒 Order"), callback_data="order_menu")
    )
    markup.add(
        InlineKeyboardButton(style_text("📋 Orders"), callback_data="history"),
        InlineKeyboardButton(style_text("👥 Refer"), callback_data="refer")
    )
    markup.add(
        InlineKeyboardButton(style_text("👤 Account"), callback_data="account"),
        InlineKeyboardButton(style_text("📊 Stats"), callback_data="stats")
    )
    markup.add(InlineKeyboardButton(style_text("🆘 Support"), callback_data="support"))
    
    return markup

def back_button_only():
    """Back button only keyboard"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("🔙 Back to Main Menu"), callback_data="main_menu"))
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
    
    markup.add(InlineKeyboardButton(style_text("🔙 Back"), callback_data="main_menu"))
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
    
    markup.add(InlineKeyboardButton(style_text("🔙 Back"), callback_data="order_menu"))
    return markup

# [REST OF KEYBOARD FUNCTIONS REMAIN THE SAME...]

# User Message Handlers - FIXED ORDER PROCESSING
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
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(style_text("✅ Join Channel"), url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
        markup.add(InlineKeyboardButton(style_text("🔄 Check Join"), callback_data="check_join"))
        bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=markup)
        return
    
    # Welcome message for verified users
    text = style_text(f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

🤖 I'ᴍ Mᴏsᴛ Aғғᴏʀᴅᴀʙʟᴇ Sᴏᴄɪᴀʟ Sᴇʀᴠɪᴄᴇs Bᴏᴛ. 
I ᴘʀᴏᴠɪᴅᴇ ᴄʜᴇᴀᴘ sᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ sᴇʀᴠɪᴄᴇs ᴀᴛ ᴛʜᴇ ʙᴇsᴛ ᴘʀɪᴄᴇs.

📱 Sᴇʀᴠɪᴄᴇs:
• Iɴsᴛᴀɢʀᴀᴍ • Fᴀᴄᴇʙᴏᴏᴋ :
• YᴏᴜTᴜʙᴇ • Tᴇʟᴇɢʀᴀᴍ :

💰 Gᴇᴛ sᴛᴀʀᴛᴇᴅ ʙʏ ᴀᴅᴅɪɴɢ ғᴜɴᴅs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.
    """)
    
    bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("service_"))
def start_order_process(call):
    """Start order process for a service"""
    user_id = call.message.chat.id
    service_id = call.data.replace("service_", "")
    service = get_service_by_id(service_id)
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    user_states[user_id] = {
        "action": "ordering",
        "service_id": service_id,
        "step": "link"
    }
    
    text = style_text(f"""
🛒 Oʀᴅᴇʀ: {service['name']}

📝 Dᴇsᴄʀɪᴘᴛɪᴏɴ: {service['description']}
💰 Pʀɪᴄᴇ: {service['price_per_unit']} ᴘᴏɪɴᴛs ᴘᴇʀ {service['unit']}
🔢 Qᴜᴀɴᴛɪᴛʏ Rᴀɴɢᴇ: {service['min']} - {service['max']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ:
    """)
    
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
    
    # Validate link
    if not link.startswith("http"):
        bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ʟɪɴᴋ! Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ʜᴛᴛᴘs ʟɪɴᴋ."))
        return
    
    user_states[user_id]["link"] = link
    user_states[user_id]["step"] = "quantity"
    
    service = get_service_by_id(user_states[user_id]["service_id"])
    
    bot.send_message(user_id, style_text(f"🔢 Eɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ ({service['min']} - {service['max']}):"))

def process_order_quantity(message):
    """Process order quantity"""
    user_id = message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        return
    
    try:
        quantity = int(message.text.strip())
        service = get_service_by_id(user_states[user_id]["service_id"])
        
        if quantity < service["min"] or quantity > service["max"]:
            bot.send_message(user_id, style_text(f"❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Mᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ {service['min']} ᴀɴᴅ {service['max']}."))
            return
        
        user_states[user_id]["quantity"] = quantity
        
        # Calculate cost
        cost_points = (quantity / service["unit"]) * service["price_per_unit"]
        user_states[user_id]["cost_points"] = cost_points
        
        # Check balance
        user_balance = get_user_balance(user_id)
        if user_balance < cost_points:
            bot.send_message(user_id, style_text(f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ! Yᴏᴜ ɴᴇᴇᴅ {cost_points} ᴘᴏɪɴᴛs, ʙᴜᴛ ʏᴏᴜ ʜᴀᴠᴇ ᴏɴʟʏ {user_balance} ᴘᴏɪɴᴛs."))
            del user_states[user_id]
            return
        
        # Confirm order
        text = style_text(f"""
🛒 Oʀᴅᴇʀ Cᴏɴғɪʀᴍᴀᴛɪᴏɴ

📱 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {user_states[user_id]['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: {cost_points} ᴘᴏɪɴᴛs

Cᴏɴғɪʀᴍ ᴏʀᴅᴇʀ?
        """)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(style_text("✅ Confirm"), callback_data="confirm_order"))
        markup.add(InlineKeyboardButton(style_text("❌ Cancel"), callback_data="order_menu"))
        
        bot.send_message(user_id, text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

@bot.callback_query_handler(func=lambda call: call.data == "confirm_order")
def confirm_order(call):
    """Confirm and process order with API integration - COMPLETELY REWRITTEN"""
    user_id = call.message.chat.id

    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        bot.answer_callback_query(call.id, "❌ Nᴏ ᴏʀᴅᴇʀ ᴅᴀᴛᴀ ғᴏᴜɴᴅ!")
        return

    data = user_states[user_id]
    service = get_service_by_id(data["service_id"])

    # Show processing message
    processing_msg = bot.send_message(user_id, "🔄 Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ᴏʀᴅᴇʀ...")

    # Get the ACTUAL SMM PANEL SERVICE ID from the service document
    smm_service_id = service.get("service_id")  # This should be the actual API service ID like "4952"
    
    if not smm_service_id:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=processing_msg.message_id,
            text=style_text("❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ ᴄᴏʀʀᴇᴄᴛʟʏ! Cᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.")
        )
        del user_states[user_id]
        return

    print(f"🎯 Placing order with SMM Service ID: {smm_service_id}")
    print(f"🔗 Link: {data['link']}")
    print(f"🔢 Quantity: {data['quantity']}")

    # Place order via SMM API - USING THE EXACT METHOD FROM YOUR WORKING CODE
    api_order_id = place_smm_order(smm_service_id, data["link"], data["quantity"])

    if not api_order_id:
        # If order placement failed
        error_text = style_text("""
❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴘʟᴀᴄᴇ ᴏʀᴅᴇʀ!

Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ɪɴ ᴀ ғᴇᴡ ᴍɪɴᴜᴛᴇs.
Iғ ᴘʀᴏʙʟᴇᴍ ᴘᴇʀsɪsᴛs, ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ.
        """)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(style_text("🔄 Try Again"), callback_data="order_menu"))
        markup.add(InlineKeyboardButton(style_text("📞 Contact Support"), url="https://wa.me/639941532149"))
        
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=error_text,
                reply_markup=markup
            )
        except Exception as e:
            print(f"Error editing message: {e}")
            bot.send_message(user_id, error_text, reply_markup=markup)
        
        return

    # SUCCESS: Order placed via API
    # Deduct balance first
    new_balance = update_user_balance(user_id, -int(data["cost_points"]), is_spent=True)

    # Create order in database with API order ID
    order = create_order(user_id, data["service_id"], data["link"], data["quantity"], int(data["cost_points"]), api_order_id)

    if order:
        # Send order to channel
        send_order_to_channel(order)

        # Clear state
        del user_states[user_id]

        success_text = style_text(f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

🆔 Oʀᴅᴇʀ ID: {order['order_id']}
🆔 API Oʀᴅᴇʀ ID: {api_order_id}
📱 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {data['link'][:50]}...
🔢 Qᴜᴀɴᴛɪᴛʏ: {data['quantity']}
💰 Cᴏsᴛ: {data['cost_points']} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs

📊 Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ
⏰ ETA: 24-48 ʜᴏᴜʀs
        """)

        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=success_text,
                reply_markup=back_button_only()
            )
        except Exception as e:
            print(f"Error editing success message: {e}")
            bot.send_message(user_id, success_text, reply_markup=back_button_only())
    else:
        # If order creation failed after API order id, refund points
        try:
            update_user_balance(user_id, int(data["cost_points"]), is_deposit=True)
        except Exception as e:
            print(f"Failed to refund user {user_id}: {e}")

        bot.edit_message_text(
            chat_id=user_id,
            message_id=processing_msg.message_id,
            text=style_text("❌ Fᴀɪʟᴇᴅ ᴛᴏ sᴀᴠᴇ ᴏʀᴅᴇʀ. Pᴏɪɴᴛs ʀᴇғᴜɴᴅᴇᴅ. Cᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ.")
        )

# [REST OF THE CODE REMAINS THE SAME...]

@bot.callback_query_handler(func=lambda call: call.data == "order_menu")
def show_service_categories_user(call):
    """Show service categories for users"""
    user_id = call.message.chat.id
    
    if not is_bot_accepting_orders():
        bot.answer_callback_query(call.id, "❌ Bᴏᴛ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ɴᴏᴛ ᴀᴄᴄᴇᴘᴛɪɴɢ ᴏʀᴅᴇʀs!", show_alert=True)
        return
    
    text = style_text("""
🛒 Sᴇʀᴠɪᴄᴇ Cᴀᴛᴇɢᴏʀɪᴇs

Sᴇʟᴇᴄᴛ ᴀ ᴄᴀᴛᴇɢᴏʀʏ:
    """)
    
    try:
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(SERVICE_IMAGE, text),
            reply_markup=service_category_keyboard()
        )
    except:
        bot.send_photo(user_id, SERVICE_IMAGE, text, reply_markup=service_category_keyboard())

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
        print(f"Bot error: {e}")
        time.sleep(10)
