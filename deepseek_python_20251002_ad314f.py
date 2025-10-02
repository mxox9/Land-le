import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import random
import time
import threading
from datetime import datetime

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8052955693:AAGoXnNg90jqvcC1X1fVo_qKV8Y0eHjDAZg')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '6052975324').split(',')]
CHANNEL_ID = os.getenv('CHANNEL_ID', '@prooflelo1')
SMM_API_URL = os.getenv('SMM_API_URL', 'https://mysmmapi.com/api/v2?')
SMM_API_KEY = os.getenv('SMM_API_KEY', 'a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d')
PROOF_CHANNEL = "@prooflelo1"
BOT_USERNAME = "@prank_ox_bot"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# Image URLs (Same as original)
WELCOME_IMAGE = "https://t.me/prooflelo1/135?single"
SERVICE_IMAGE = "https://t.me/prooflelo1/138?single"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/136?single"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/137?single"
HISTORY_IMAGE = "https://t.me/prooflelo1/139?single"
REFER_IMAGE = "https://t.me/prooflelo1/17"
ADMIN_IMAGE = "https://t.me/prooflelo1/140?single"

# All Services
SERVICES = [
    # Instagram Services
    {
        "category": "instagram",
        "name": "Insta Likes",
        "service_id": "101",
        "price_per_unit": 50,
        "unit": 1000,
        "min": 100,
        "max": 10000,
        "description": "High-quality Instagram Likes"
    },
    {
        "category": "instagram", 
        "name": "Insta Views",
        "service_id": "102",
        "price_per_unit": 40,
        "unit": 1000,
        "min": 500,
        "max": 50000,
        "description": "Real Instagram Views"
    },
    {
        "category": "instagram",
        "name": "Insta Followers",
        "service_id": "103", 
        "price_per_unit": 100,
        "unit": 1000,
        "min": 100,
        "max": 10000,
        "description": "Premium Instagram Followers"
    },
    
    # Facebook Services
    {
        "category": "facebook",
        "name": "FB Likes",
        "service_id": "201",
        "price_per_unit": 60,
        "unit": 1000,
        "min": 100,
        "max": 20000,
        "description": "Facebook Page/Post Likes"
    },
    {
        "category": "facebook",
        "name": "FB Views", 
        "service_id": "202",
        "price_per_unit": 45,
        "unit": 1000,
        "min": 500,
        "max": 50000,
        "description": "Facebook Video Views"
    },
    {
        "category": "facebook",
        "name": "FB Followers",
        "service_id": "203",
        "price_per_unit": 120,
        "unit": 1000, 
        "min": 100,
        "max": 15000,
        "description": "Facebook Page Followers"
    },
    
    # YouTube Services
    {
        "category": "youtube",
        "name": "YT Likes",
        "service_id": "301",
        "price_per_unit": 70,
        "unit": 1000,
        "min": 100,
        "max": 25000,
        "description": "YouTube Video Likes"
    },
    {
        "category": "youtube",
        "name": "YT Views",
        "service_id": "302",
        "price_per_unit": 55,
        "unit": 1000,
        "min": 1000,
        "max": 100000,
        "description": "YouTube Video Views"
    },
    {
        "category": "youtube", 
        "name": "YT Subscribers",
        "service_id": "303",
        "price_per_unit": 150,
        "unit": 1000,
        "min": 100,
        "max": 10000,
        "description": "YouTube Channel Subscribers"
    },
    
    # Telegram Services
    {
        "category": "telegram",
        "name": "TG Members",
        "service_id": "401",
        "price_per_unit": 80,
        "unit": 1000,
        "min": 100,
        "max": 50000,
        "description": "Telegram Channel Members"
    },
    {
        "category": "telegram",
        "name": "TG Post Likes",
        "service_id": "402",
        "price_per_unit": 35,
        "unit": 1000,
        "min": 100,
        "max": 50000,
        "description": "Telegram Post Reactions"
    },
    {
        "category": "telegram",
        "name": "TG Post Views",
        "service_id": "403",
        "price_per_unit": 25,
        "unit": 1000,
        "min": 1000,
        "max": 100000,
        "description": "Telegram Post Views"
    }
]

# Helper functions
def style_text(text):
    """Convert text to stylish format"""
    def style_word(word):
        if len(word) > 0:
            return word[0] + word[1:].lower()
        return word
    
    words = text.split()
    styled_words = []
    
    for word in words:
        if any(char.isalpha() for char in word):
            styled_words.append(style_word(word))
        else:
            styled_words.append(word)
    
    return ' '.join(styled_words)

def get_services_by_category(category):
    return [service for service in SERVICES if service["category"] == category]

def get_all_categories():
    categories = set(service["category"] for service in SERVICES)
    return list(categories)

def get_service_by_id(service_id):
    for service in SERVICES:
        if service["service_id"] == service_id:
            return service
    return None

# In-memory storage
users_data = {}
orders_data = {}
user_states = {}
bot_settings = {"accepting_orders": True}

def get_user_balance(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 0.0,
            "total_deposits": 0.0,
            "total_spent": 0.0,
            "joined_at": datetime.now()
        }
    return users_data[user_id]["balance"]

def update_user_balance(user_id, amount, is_deposit=False, is_spent=False):
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": amount,
            "total_deposits": amount if is_deposit else 0.0,
            "total_spent": amount if is_spent else 0.0,
            "joined_at": datetime.now()
        }
    else:
        users_data[user_id]["balance"] += amount
        if is_deposit:
            users_data[user_id]["total_deposits"] += amount
        elif is_spent:
            users_data[user_id]["total_spent"] += amount
    
    return users_data[user_id]["balance"]

def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def place_smm_order(service_id, link, quantity):
    """Place order via SMM API - Test Bot Style"""
    try:
        params = {
            'key': SMM_API_KEY,
            'action': 'add',
            'service': service_id,
            'link': link,
            'quantity': quantity
        }
        
        response = requests.get(SMM_API_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Response: {data}")  # Debug log
            
            if isinstance(data, dict):
                if data.get('error'):
                    return None, data.get('error')
                
                # Try different possible order ID fields
                for key in ['order', 'order_id', 'id']:
                    if key in data and data[key]:
                        return str(data[key]), None
                
                # Check nested data
                if 'data' in data and isinstance(data['data'], dict):
                    for key in ['order', 'order_id', 'id']:
                        if key in data['data'] and data['data'][key]:
                            return str(data['data'][key]), None
            
            return None, "No order ID in response"
        else:
            return None, f"API Error: {response.status_code}"
            
    except Exception as e:
        return None, f"Request failed: {str(e)}"

def generate_order_id():
    return f"ORD{random.randint(100000, 999999)}"

def send_order_to_channel(order):
    try:
        text = f"""
🆕 Nᴇᴡ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ!

📝 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
👤 Usᴇʀ ID: {order['user_id']}
🆔 Oʀᴅᴇʀ ID: {order['order_id']}
🔗 Lɪɴᴋ: {order['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💰 Aᴍᴏᴜɴᴛ: ₹{order['cost']:.2f}
⏰ Tɪᴍᴇ: {order['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🤖 Bᴏᴛ Hᴇʀᴇ 🈴", url=f"https://t.me/{BOT_USERNAME.replace('@', '')}"))
        
        bot.send_message(PROOF_CHANNEL, text, reply_markup=markup)
        return True
    except Exception as e:
        return False

# Keyboard Builders (Original Style)
def main_menu_keyboard():
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
    return markup

def service_category_keyboard():
    markup = InlineKeyboardMarkup()
    categories = get_all_categories()
    
    category_emojis = {
        "instagram": "📸",
        "facebook": "👍", 
        "youtube": "📺",
        "telegram": "📢"
    }
    
    for category in categories:
        emoji = category_emojis.get(category, "📱")
        markup.add(InlineKeyboardButton(
            f"{emoji} {style_text(category)}", 
            callback_data=f"category_{category}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    return markup

def services_keyboard(category):
    markup = InlineKeyboardMarkup()
    services = get_services_by_category(category)
    
    for service in services:
        price = service["price_per_unit"]
        unit = service["unit"]
        button_text = f"{style_text(service['name'])} - ₹{price}/{unit}"
        markup.add(InlineKeyboardButton(
            button_text, 
            callback_data=f"service_{service['service_id']}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order_menu"))
    return markup

def channel_join_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Jᴏɪɴ Cʜᴀɴɴᴇʟ", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    markup.add(InlineKeyboardButton("🔄 Cʜᴇᴄᴋ Jᴏɪɴ", callback_data="check_join"))
    return markup

def back_button_only():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ ᴛᴏ Mᴀɪɴ Mᴇɴᴜ", callback_data="main_menu"))
    return markup

# User Message Handlers (Original Style)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_name = message.chat.first_name
    
    if not check_channel_membership(user_id):
        text = f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

📢 Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ:

{CHANNEL_ID}

Aғᴛᴇʀ ᴊᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴛʜᴇ ᴄʜᴇᴄᴋ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.
        """
        bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=channel_join_keyboard())
        return
    
    text = f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

🤖 I'ᴍ Aɴ Aᴅᴠᴀɴᴄᴇᴅ Sᴏᴄɪᴀʟ Sᴇʀᴠɪᴄᴇs Bᴏᴛ. 
I ᴡɪʟʟ ʜᴇʟᴘ ʏᴏᴜ ɢᴇᴛ ǫᴜᴀʟɪᴛʏ sᴏᴄɪᴀʟ ᴇɴɢᴀɢᴇᴍᴇɴᴛ ᴀᴛ ᴛʜᴇ ʙᴇsᴛ ᴘʀɪᴄᴇs.

⭐ Sᴇʀᴠɪᴄᴇs:
• Iɴsᴛᴀɢʀᴀᴍ • Fᴀᴄᴇʙᴏᴏᴋ
• YᴏᴜTᴜʙᴇ • Tᴇʟᴇɢʀᴀᴍ

💰 Gᴇᴛ sᴛᴀʀᴛᴇᴅ ʙʏ ᴀᴅᴅɪɴɢ ғᴜɴᴅs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.
    """
    
    bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=main_menu_keyboard())

# Callback Handler
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_queries(call):
    user_id = call.message.chat.id
    
    try:
        if call.data == "main_menu":
            show_main_menu(call)
        elif call.data == "order_menu":
            show_service_categories_user(call)
        elif call.data == "history":
            show_order_history(call)
        elif call.data == "account":
            show_account_info(call)
        elif call.data == "stats":
            show_stats(call)
        elif call.data == "support":
            show_support(call)
        elif call.data == "check_join":
            check_channel_join(call)
        elif call.data.startswith("category_"):
            category = call.data.replace("category_", "")
            show_services(call, category)
        elif call.data.startswith("service_"):
            service_id = call.data.replace("service_", "")
            start_order_process(call, service_id)
        elif call.data == "confirm_order":
            confirm_order(call)
            
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!")

# Order Flow (Test Bot Style)
def start_order_process(call, service_id):
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
🛒 Oʀᴅᴇʀ: {service['name']}

📖 Dᴇsᴄʀɪᴘᴛɪᴏɴ: {service['description']}
💰 Pʀɪᴄᴇ: ₹{service['price_per_unit']} ᴘᴇʀ {service['unit']}
🔢 Qᴜᴀɴᴛɪᴛʏ Rᴀɴɢᴇ: {service['min']} - {service['max']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ:
"""
    
    bot.send_message(user_id, text)
    bot.register_next_step_handler(call.message, process_order_link)

def process_order_link(message):
    user_id = message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        return
    
    link = message.text.strip()
    user_states[user_id]["link"] = link
    user_states[user_id]["step"] = "quantity"
    
    service = get_service_by_id(user_states[user_id]["service_id"])
    bot.send_message(user_id, f"🔢 Eɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ ({service['min']} - {service['max']}):")
    bot.register_next_step_handler(message, process_order_quantity)

def process_order_quantity(message):
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
        
        cost = (quantity / service["unit"]) * service["price_per_unit"]
        user_states[user_id]["cost"] = cost
        
        user_balance = get_user_balance(user_id)
        if user_balance < cost:
            bot.send_message(user_id, f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ! Yᴏᴜ ɴᴇᴇᴅ ₹{cost:.2f}, ʙᴜᴛ ʏᴏᴜ ʜᴀᴠᴇ ₹{user_balance:.2f}.")
            del user_states[user_id]
            return
        
        text = f"""
🛒 Oʀᴅᴇʀ Cᴏɴғɪʀᴍᴀᴛɪᴏɴ

📝 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {user_states[user_id]['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: ₹{cost:.2f}

Cʟɪᴄᴋ CONFIRM ᴛᴏ ᴘʟᴀᴄᴇ ᴏʀᴅᴇʀ:
"""
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ Oʀᴅᴇʀ", callback_data="confirm_order"))
        
        bot.send_message(user_id, text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")

def confirm_order(call):
    user_id = call.message.chat.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        return
    
    data = user_states[user_id]
    service = get_service_by_id(data["service_id"])

    processing_msg = bot.send_message(user_id, "🔄 Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ᴏʀᴅᴇʀ...")

    # Place order via API (Test Bot Style)
    api_order_id, error = place_smm_order(service["service_id"], data["link"], data["quantity"])

    if api_order_id:
        # Deduct balance
        new_balance = update_user_balance(user_id, -data["cost"], is_spent=True)
        
        # Create order record
        order_id = generate_order_id()
        order = {
            "order_id": order_id,
            "api_order_id": api_order_id,
            "user_id": user_id,
            "service_name": service["name"],
            "link": data["link"],
            "quantity": data["quantity"],
            "cost": data["cost"],
            "status": "Pending",
            "created_at": datetime.now()
        }
        orders_data[order_id] = order
        
        # Send to proof channel
        send_order_to_channel(order)
        
        success_text = f"""
🎉 Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

🆔 Oʀᴅᴇʀ ID: {order_id}
🆔 API Oʀᴅᴇʀ ID: {api_order_id}
📝 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {data['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {data['quantity']}
💰 Cᴏsᴛ: ₹{data['cost']:.2f}
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: ₹{new_balance:.2f}

✅ Oʀᴅᴇʀ sᴇɴᴛ ᴛᴏ SMM API sᴜᴄᴄᴇssғᴜʟʟʏ!
📊 Sᴛᴀᴛᴜs: Pʀᴏᴄᴇssɪɴɢ
⏰ ETA: 24-48 ʜᴏᴜʀs
"""
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=processing_msg.message_id,
            text=success_text
        )
        
    else:
        error_text = f"""
❌ Oʀᴅᴇʀ Fᴀɪʟᴇᴅ!

🚫 Eʀʀᴏʀ: {error}

💡 Wʜᴀᴛ ᴛᴏ ᴅᴏ:
• Cʜᴇᴄᴋ ɪғ API ᴄʀᴇᴅᴇɴᴛɪᴀʟs ᴀʀᴇ ᴄᴏʀʀᴇᴄᴛ
• Vᴇʀɪғʏ sᴇʀᴠɪᴄᴇ ID ɪs ᴠᴀʟɪᴅ
• Tʀʏ ᴅɪғғᴇʀᴇɴᴛ ʟɪɴᴋ/ǫᴜᴀɴᴛɪᴛʏ
"""
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=processing_msg.message_id,
            text=error_text
        )
    
    # Clean up
    if user_id in user_states:
        del user_states[user_id]

# Other functions (Original Style)
def show_main_menu(call):
    user_id = call.message.chat.id
    user_name = call.message.chat.first_name
    
    text = f"""
👋 Hᴇʟʟᴏ {user_name}!

🤖 Wᴇʟᴄᴏᴍᴇ ᴛᴏ Oᴜʀ Bᴏᴛ Mᴀɪɴ Mᴇɴᴜ

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:
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
    user_id = call.message.chat.id
    
    text = """
🛒 Sᴇʀᴠɪᴄᴇ Cᴀᴛᴇɢᴏʀɪᴇs

Sᴇʟᴇᴄᴛ ᴀ ᴄᴀᴛᴇɢᴏʀʏ:
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
    user_id = call.message.chat.id
    
    text = f"""
📱 {style_text(category)} Sᴇʀᴠɪᴄᴇs

Sᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ:
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

def show_order_history(call):
    user_id = call.message.chat.id
    user_orders = [order for order in orders_data.values() if order["user_id"] == user_id]
    user_orders = sorted(user_orders, key=lambda x: x["created_at"], reverse=True)[:5]
    
    if not user_orders:
        text = "📋 Yᴏᴜ ʜᴀᴠᴇ ɴᴏ ᴏʀᴅᴇʀs ʏᴇᴛ."
    else:
        text = "📋 Yᴏᴜʀ Rᴇᴄᴇɴᴛ Oʀᴅᴇʀs:\n\n"
        for order in user_orders:
            status_emoji = "✅" if order["status"] == "Completed" else "🔄" if order["status"] == "Processing" else "❌"
            text += f"""
{status_emoji} Oʀᴅᴇʀ ID: {order['order_id']}
📝 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💰 Cᴏsᴛ: ₹{order['cost']:.2f}
📊 Sᴛᴀᴛᴜs: {order['status']}
📅 Dᴀᴛᴇ: {order['created_at'].strftime('%Y-%m-%d %H:%M')}
────────────────
"""
    
    bot.send_photo(user_id, HISTORY_IMAGE, text, reply_markup=back_button_only())

def show_account_info(call):
    user_id = call.message.chat.id
    user = users_data.get(user_id)
    balance = get_user_balance(user_id)
    total_orders = len([order for order in orders_data.values() if order["user_id"] == user_id])
    
    if not user:
        users_data[user_id] = {
            "balance": 0.0,
            "total_deposits": 0.0,
            "total_spent": 0.0,
            "joined_at": datetime.now()
        }
        user = users_data[user_id]
    
    text = f"""
👤 Aᴄᴄᴏᴜɴᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ

🆔 Usᴇʀ ID: {user_id}
👤 Nᴀᴍᴇ: {call.message.chat.first_name}
📅 Jᴏɪɴᴇᴅ: {user['joined_at'].strftime('%Y-%m-%d')}

💳 Bᴀʟᴀɴᴄᴇ: ₹{balance:.2f}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{user.get('total_deposits', 0):.2f}
💸 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{user.get('total_spent', 0):.2f}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
"""
    
    bot.send_photo(user_id, ACCOUNT_IMAGE, text, reply_markup=back_button_only())

def show_stats(call):
    user_id = call.message.chat.id
    total_users = len(users_data)
    total_orders = len(orders_data)
    
    text = f"""
📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs

👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
📱 Aᴄᴛɪᴠᴇ Sᴇʀᴠɪᴄᴇs: {len(SERVICES)}
"""
    
    bot.send_message(user_id, text, reply_markup=back_button_only())

def show_support(call):
    user_id = call.message.chat.id
    
    text = """
ℹ️ Sᴜᴘᴘᴏʀᴛ

📞 Cᴏɴᴛᴀᴄᴛ ᴜs ғᴏʀ:
• Aᴄᴄᴏᴜɴᴛ ɪssᴜᴇs
• Dᴇᴘᴏsɪᴛ ʜᴇʟᴘ
• Oʀᴅᴇʀ ᴘʀᴏʙʟᴇᴍs
• Gᴇɴᴇʀᴀʟ ǫᴜᴇsᴛɪᴏɴs

⏰ Sᴜᴘᴘᴏʀᴛ ʜᴏᴜʀs: 24/7
"""
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📞 Cᴏɴᴛᴀᴄᴛ Us", url="https://wa.me/639941532149"))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    
    bot.send_photo(user_id, WELCOME_IMAGE, text, reply_markup=markup)

def check_channel_join(call):
    user_id = call.message.chat.id
    
    if check_channel_membership(user_id):
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ʏᴇᴛ!", show_alert=True)

print("🤖 Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
print("🔑 API Key:", SMM_API_KEY)
print("🌐 API URL:", SMM_API_URL)

if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Bot error: {e}")