import os
import telebot
import random
import time
import threading
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []
CHANNEL_ID = os.getenv('CHANNEL_ID')
BOT_USERNAME = os.getenv('BOT_USERNAME')
SUPPORT_WHATSAPP = os.getenv('SUPPORT_WHATSAPP')

# Images
WELCOME_IMAGE = os.getenv('WELCOME_IMAGE', 'https://via.placeholder.com/400x200/4A90E2/FFFFFF?text=Welcome+Image')
SERVICE_IMAGE = os.getenv('SERVICE_IMAGE', 'https://via.placeholder.com/400x200/50C878/FFFFFF?text=Service+Image')
DEPOSIT_IMAGE = os.getenv('DEPOSIT_IMAGE', 'https://via.placeholder.com/400x200/F39C12/FFFFFF?text=Deposit+Image')
ACCOUNT_IMAGE = os.getenv('ACCOUNT_IMAGE', 'https://via.placeholder.com/400x200/9B59B6/FFFFFF?text=Account+Image')
HISTORY_IMAGE = os.getenv('HISTORY_IMAGE', 'https://via.placeholder.com/400x200/E74C3C/FFFFFF?text=History+Image')
REFER_IMAGE = os.getenv('REFER_IMAGE', 'https://via.placeholder.com/400x200/3498DB/FFFFFF?text=Refer+Image')
ADMIN_IMAGE = os.getenv('ADMIN_IMAGE', 'https://via.placeholder.com/400x200/2C3E50/FFFFFF?text=Admin+Image')

# In-memory storage
users = {}
orders = {}
deposits = {}
user_states = {}

# Initialize bot

# Safety checks for environment variables
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is not set. Please set BOT_TOKEN in your environment or .env file and redeploy.")
    raise SystemExit("Missing BOT_TOKEN")

# Initialize bot inside try/except
try:
    bot = telebot.TeleBot(BOT_TOKEN)
except Exception as e:
    print(f"ERROR: Failed to initialize TeleBot. Details: {e}")
    raise


# Services Data - Replace service_id here with real ID from SMM panel
SERVICES = {
    "Iɴsᴛᴀɢʀᴀᴍ": [
        {
            "id": "insta_likes_temp_1",  # Replace with real SMM panel service ID
            "category": "Iɴsᴛᴀɢʀᴀᴍ",
            "name": "❤️ Iɴsᴛᴀ Lɪᴋᴇs",
            "description": "Hɪɢʜ-ǫᴜᴀʟɪᴛʏ Iɴsᴛᴀɢʀᴀᴍ ʟɪᴋᴇs ғʀᴏᴍ ʀᴇᴀʟ ᴜsᴇʀs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 25.0,
            "active": True
        },
        {
            "id": "insta_follows_temp_2",  # Replace with real SMM panel service ID
            "category": "Iɴsᴛᴀɢʀᴀᴍ",
            "name": "👥 Iɴsᴛᴀ Fᴏʟʟᴏᴡs",
            "description": "Rᴇᴀʟ Iɴsᴛᴀɢʀᴀᴍ ғᴏʟʟᴏᴡᴇʀs ɢᴜᴀʀᴀɴᴛᴇᴇᴅ",
            "min": 50,
            "max": 5000,
            "unit": "followers",
            "price": 120.0,
            "active": True
        },
        {
            "id": "insta_views_temp_3",  # Replace with real SMM panel service ID
            "category": "Iɴsᴛᴀɢʀᴀᴍ",
            "name": "👁 Iɴsᴛᴀ Vɪᴇᴡs",
            "description": "Iɴsᴛᴀɢʀᴀᴍ ʀᴇᴇʟs ᴀɴᴅ ᴠɪᴅᴇᴏ ᴠɪᴇᴡs",
            "min": 500,
            "max": 50000,
            "unit": "views",
            "price": 15.0,
            "active": True
        }
    ],
    "Fᴀᴄᴇʙᴏᴏᴋ": [
        {
            "id": "fb_likes_temp_4",  # Replace with real SMM panel service ID
            "category": "Fᴀᴄᴇʙᴏᴏᴋ",
            "name": "👍 Fʙ Lɪᴋᴇs",
            "description": "Fᴀᴄᴇʙᴏᴏᴋ ᴘᴀɢᴇ ᴀɴᴅ ᴘᴏsᴛ ʟɪᴋᴇs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 30.0,
            "active": True
        },
        {
            "id": "fb_views_temp_5",  # Replace with real SMM panel service ID
            "category": "Fᴀᴄᴇʙᴏᴏᴋ",
            "name": "👁 Fʙ Vɪᴇᴡs",
            "description": "Fᴀᴄᴇʙᴏᴏᴋ ᴠɪᴅᴇᴏ ᴠɪᴇᴡs",
            "min": 500,
            "max": 50000,
            "unit": "views",
            "price": 20.0,
            "active": True
        },
        {
            "id": "fb_follows_temp_6",  # Replace with real SMM panel service ID
            "category": "Fᴀᴄᴇʙᴏᴏᴋ",
            "name": "👥 Fʙ Fᴏʟʟᴏᴡs",
            "description": "Fᴀᴄᴇʙᴏᴏᴋ ᴘᴀɢᴇ ғᴏʟʟᴏᴡᴇʀs",
            "min": 50,
            "max": 5000,
            "unit": "followers",
            "price": 150.0,
            "active": True
        }
    ],
    "Tᴇʟᴇɢʀᴀᴍ": [
        {
            "id": "tg_members_temp_7",  # Replace with real SMM panel service ID
            "category": "Tᴇʟᴇɢʀᴀᴍ",
            "name": "👥 Tɢ Mᴇᴍʙᴇʀs",
            "description": "Tᴇʟᴇɢʀᴀᴍ ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs",
            "min": 100,
            "max": 10000,
            "unit": "members",
            "price": 80.0,
            "active": True
        },
        {
            "id": "tg_views_temp_8",  # Replace with real SMM panel service ID
            "category": "Tᴇʟᴇɢʀᴀᴍ",
            "name": "👁 Tɢ Vɪᴇᴡs",
            "description": "Tᴇʟᴇɢʀᴀᴍ ᴘᴏsᴛ ᴠɪᴇᴡs",
            "min": 1000,
            "max": 100000,
            "unit": "views",
            "price": 10.0,
            "active": True
        },
        {
            "id": "tg_reactions_temp_9",  # Replace with real SMM panel service ID
            "category": "Tᴇʟᴇɢʀᴀᴍ",
            "name": "💬 Tɢ Rᴇᴀᴄᴛɪᴏɴs",
            "description": "Tᴇʟᴇɢʀᴀᴍ ᴘᴏsᴛ ʀᴇᴀᴄᴛɪᴏɴs",
            "min": 100,
            "max": 5000,
            "unit": "reactions",
            "price": 25.0,
            "active": True
        }
    ],
    "YᴏᴜTᴜʙᴇ": [
        {
            "id": "yt_likes_temp_10",  # Replace with real SMM panel service ID
            "category": "YᴏᴜTᴜʙᴇ",
            "name": "👍 Yᴛ Lɪᴋᴇs",
            "description": "YᴏᴜTᴜʙᴇ ᴠɪᴅᴇᴏ ʟɪᴋᴇs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 40.0,
            "active": True
        },
        {
            "id": "yt_views_temp_11",  # Replace with real SMM panel service ID
            "category": "YᴏᴜTᴜʙᴇ",
            "name": "👁 Yᴛ Vɪᴇᴡs",
            "description": "YᴏᴜTᴜʙᴇ ᴠɪᴇᴡs",
            "min": 1000,
            "max": 100000,
            "unit": "views",
            "price": 12.0,
            "active": True
        },
        {
            "id": "yt_subs_temp_12",  # Replace with real SMM panel service ID
            "category": "YᴏᴜTᴜʙᴇ",
            "name": "🔔 Yᴛ Sᴜʙsᴄʀɪʙᴇs",
            "description": "YᴏᴜTᴜʙᴇ sᴜʙsᴄʀɪʙᴇʀs",
            "min": 50,
            "max": 5000,
            "unit": "subscribers",
            "price": 200.0,
            "active": True
        }
    ],
    "Tᴡɪᴛᴛᴇʀ": [
        {
            "id": "twt_likes_temp_13",  # Replace with real SMM panel service ID
            "category": "Tᴡɪᴛᴛᴇʀ",
            "name": "❤️ Tᴡᴛ Lɪᴋᴇs",
            "description": "Tᴡɪᴛᴛᴇʀ ʟɪᴋᴇs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 35.0,
            "active": True
        },
        {
            "id": "twt_retweets_temp_14",  # Replace with real SMM panel service ID
            "category": "Tᴡɪᴛᴛᴇʀ",
            "name": "🔁 Tᴡᴛ Rᴇᴛᴡᴇᴇᴛs",
            "description": "Tᴡɪᴛᴛᴇʀ ʀᴇᴛᴡᴇᴇᴛs",
            "min": 100,
            "max": 5000,
            "unit": "retweets",
            "price": 45.0,
            "active": True
        },
        {
            "id": "twt_follows_temp_15",  # Replace with real SMM panel service ID
            "category": "Tᴡɪᴛᴛᴇʀ",
            "name": "👥 Tᴡᴛ Fᴏʟʟᴏᴡs",
            "description": "Tᴡɪᴛᴛᴇʀ ғᴏʟʟᴏᴡᴇʀs",
            "min": 50,
            "max": 5000,
            "unit": "followers",
            "price": 180.0,
            "active": True
        }
    ],
    "TɪᴋTᴏᴋ": [
        {
            "id": "tik_likes_temp_16",  # Replace with real SMM panel service ID
            "category": "TɪᴋTᴏᴋ",
            "name": "❤️ Tɪᴋ Lɪᴋᴇs",
            "description": "TɪᴋTᴏᴋ ʟɪᴋᴇs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 28.0,
            "active": True
        },
        {
            "id": "tik_views_temp_17",  # Replace with real SMM panel service ID
            "category": "TɪᴋTᴏᴋ",
            "name": "👁 Tɪᴋ Vɪᴇᴡs",
            "description": "TɪᴋTᴏᴋ ᴠɪᴇᴡs",
            "min": 1000,
            "max": 100000,
            "unit": "views",
            "price": 18.0,
            "active": True
        },
        {
            "id": "tik_follows_temp_18",  # Replace with real SMM panel service ID
            "category": "TɪᴋTᴏᴋ",
            "name": "👥 Tɪᴋ Fᴏʟʟᴏᴡs",
            "description": "TɪᴋTᴏᴋ ғᴏʟʟᴏᴡᴇʀs",
            "min": 50,
            "max": 5000,
            "unit": "followers",
            "price": 160.0,
            "active": True
        }
    ]
}

# Utility Functions
def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_service_by_id(service_id):
    for category_services in SERVICES.values():
        for service in category_services:
            if service["id"] == service_id:
                return service
    return None

def generate_utr():
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])

def generate_qr_code(amount, utr):
    upi_link = f"upi://pay?pa=merchant@upi&pn=Merchant&am={amount}&tn=Deposit-{utr}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={upi_link}"
    return qr_url

def generate_order_id():
    return f"ORD{random.randint(100000, 999999)}"

# Keyboard Functions
def get_main_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🛍 Sᴇʀᴠɪᴄᴇs", callback_data="services"),
        InlineKeyboardButton("💰 Dᴇᴘᴏsɪᴛ", callback_data="deposit"),
        InlineKeyboardButton("📦 Oʀᴅᴇʀs", callback_data="orders"),
        InlineKeyboardButton("👤 Aᴄᴄᴏᴜɴᴛ", callback_data="account"),
        InlineKeyboardButton("📞 Sᴜᴘᴘᴏʀᴛ", callback_data="support"),
        InlineKeyboardButton("👥 Rᴇғᴇʀ", callback_data="refer")
    )
    if is_admin(user_id):
        keyboard.add(InlineKeyboardButton("👑 Aᴅᴍɪɴ", callback_data="admin"))
    return keyboard

def get_categories_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for category in SERVICES.keys():
        buttons.append(InlineKeyboardButton(category, callback_data=f"category_{category}"))
    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        keyboard.add(*row)
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_main"))
    return keyboard

def get_services_keyboard(category):
    keyboard = InlineKeyboardMarkup()
    for service in SERVICES[category]:
        if service["active"]:
            keyboard.add(InlineKeyboardButton(
                service["name"], 
                callback_data=f"service_{service['id']}"
            ))
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_categories"))
    return keyboard

def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📢 Bʀᴏᴀᴅᴄᴀsᴛ", callback_data="admin_broadcast"),
        InlineKeyboardButton("💰 Aᴅᴅ Bᴀʟᴀɴᴄᴇ", callback_data="admin_add_balance"),
        InlineKeyboardButton("💸 Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ", callback_data="admin_deduct_balance"),
        InlineKeyboardButton("👥 Bᴀɴ/Uɴʙᴀɴ", callback_data="admin_ban_user"),
        InlineKeyboardButton("📦 Sᴇʀᴠɪᴄᴇ Pʀɪᴄᴇ", callback_data="admin_service_price")
    )
    return keyboard

# Command Handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if user_id not in users:
        users[user_id] = {
            'balance': 0.0,
            'deposits': 0.0,
            'spent': 0.0,
            'joined_at': message.date,
            'referral': None
        }
    
    welcome_text = """
🤖 Wᴇʟᴄᴏᴍᴇ ᴛᴏ Sᴏᴄɪᴀʟ Mᴇᴅɪᴀ Bᴏᴏsᴛᴇʀ!

🚀 Bᴏᴏsᴛ ʏᴏᴜʀ sᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ ᴘʀᴇsᴇɴᴄᴇ ᴡɪᴛʜ ʜɪɢʜ-ǫᴜᴀʟɪᴛʏ sᴇʀᴠɪᴄᴇs.

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:
    """.strip()
    
    bot.send_photo(
        message.chat.id,
        WELCOME_IMAGE,
        caption=welcome_text,
        reply_markup=get_main_keyboard(user_id)
    )

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ")
        return
    
    total_users = len(users)
    total_orders = len(orders)
    total_balance = sum(user.get('balance', 0) for user in users.values())
    
    caption = f"""
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

📊 Sᴛᴀᴛɪsᴛɪᴄs:
├─ 👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
├─ 📦 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
└─ 💰 Tᴏᴛᴀʟ Bᴀʟᴀɴᴄᴇ: ₹{total_balance:,.2f}

Sᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ:
    """.strip()
    
    bot.send_photo(
        message.chat.id,
        ADMIN_IMAGE,
        caption=caption,
        reply_markup=get_admin_keyboard()
    )

@bot.message_handler(commands=['track'])
def track_command(message):
    bot.send_message(message.chat.id, "📦 Eɴᴛᴇʀ ʏᴏᴜʀ Oʀᴅᴇʀ ID:")
    bot.register_next_step_handler(message, track_order)

def track_order(message):
    order_id = message.text.upper().strip()
    
    if order_id in orders:
        order = orders[order_id]
        service = get_service_by_id(order['service_id'])
        
        status_emoji = {
            'Pending': '⏳',
            'In progress': '🔄', 
            'Completed': '✅',
            'Partial': '⚠️',
            'Cancelled': '❌'
        }
        
        emoji = status_emoji.get(order['status'], '📦')
        
        bot.send_message(
            message.chat.id,
            f"""
📦 Oʀᴅᴇʀ Tʀᴀᴄᴋɪɴɢ

🆔 Oʀᴅᴇʀ ID: {order_id}
{emoji} Sᴛᴀᴛᴜs: {order['status']}
🏷 Sᴇʀᴠɪᴄᴇ: {service['name'] if service else 'Unknown'}
🔗 Lɪɴᴋ: {order['link'][:50]}...
📊 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']:,}
📝 Rᴇsᴘᴏɴsᴇ: {order['api_response']}
            """.strip()
        )
    else:
        bot.send_message(message.chat.id, "❌ Oʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ. Pʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ Oʀᴅᴇʀ ID.")

# Callback Handlers
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    
    try:
        if call.data == "services":
            show_categories(call)
        elif call.data == "deposit":
            ask_deposit_amount(call)
        elif call.data == "orders":
            show_orders_menu(call)
        elif call.data == "account":
            show_account(call)
        elif call.data == "support":
            show_support(call)
        elif call.data == "refer":
            show_refer(call)
        elif call.data == "admin":
            show_admin_panel(call)
        elif call.data == "back_to_main":
            edit_to_main_menu(call)
        elif call.data.startswith("category_"):
            category = call.data.replace("category_", "")
            show_services(call, category)
        elif call.data.startswith("service_"):
            service_id = call.data.replace("service_", "")
            service = get_service_by_id(service_id)
            if service:
                show_service_details(call, service)
                user_states[user_id] = {'waiting_for_link': service_id}
        elif call.data == "back_to_categories":
            show_categories(call)
        elif call.data.startswith("paid_"):
            utr = call.data.replace("paid_", "")
            check_payment_status(call, utr)
        elif call.data.startswith("admin_"):
            handle_admin_callbacks(call)
            
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ")
        print(f"Callback error: {e}")

# Menu Functions
def show_categories(call):
    caption = """
🛍 Sᴇʀᴠɪᴄᴇs

Sᴇʟᴇᴄᴛ ᴀ ᴄᴀᴛᴇɢᴏʀʏ:
    """.strip()
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            SERVICE_IMAGE,
            caption=caption
        ),
        reply_markup=get_categories_keyboard()
    )

def show_services(call, category):
    if category in SERVICES:
        caption = f"""
🛍 {category} Sᴇʀᴠɪᴄᴇs

Sᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ:
        """.strip()
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                SERVICE_IMAGE,
                caption=caption
            ),
            reply_markup=get_services_keyboard(category)
        )

def show_service_details(call, service):
    caption = f"""
📦 {service['name']}

📝 {service['description']}

📊 Qᴜᴀɴᴛɪᴛʏ Rᴀɴɢᴇ: {service['min']:,} - {service['max']:,} {service['unit']}
💰 Pʀɪᴄᴇ: ₹{service['price']:.2f} ᴘᴇʀ 1,000 {service['unit']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ:
    """.strip()
    
    bot.send_photo(
        call.message.chat.id,
        SERVICE_IMAGE,
        caption=caption
    )
    
    user_id = call.from_user.id
    if user_id not in users:
        users[user_id] = {}
    users[user_id]['selected_service'] = service['id']

def ask_deposit_amount(call):
    caption = """
💰 Dᴇᴘᴏsɪᴛ

Eɴᴛᴇʀ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇᴘᴏsɪᴛ (ɪɴ ₹):
Mɪɴɪᴍᴜᴍ: ₹10
    """.strip()
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            DEPOSIT_IMAGE,
            caption=caption
        )
    )
    
    bot.register_next_step_handler(call.message, handle_deposit)

def handle_deposit(message):
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, "❌ Mɪɴɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ ɪs ₹10")
            return
        
        utr = generate_utr()
        qr_url = generate_qr_code(amount, utr)
        
        user_id = message.from_user.id
        deposits[utr] = {
            'user_id': user_id,
            'amount': amount,
            'status': 'pending',
            'timestamp': message.date
        }
        
        caption = f"""
💰 Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ

💳 Aᴍᴏᴜɴᴛ: ₹{amount:,.2f}
🔢 UTR: {utr}

Sᴄᴀɴ ᴛʜᴇ QR ᴄᴏᴅᴇ ᴏʀ ᴜsᴇ UPI ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ ᴘᴀʏᴍᴇɴᴛ.
        """.strip()
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Pᴀɪᴅ", callback_data=f"paid_{utr}"),
            InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_main")
        )
        
        bot.send_photo(
            message.chat.id,
            qr_url,
            caption=caption,
            reply_markup=keyboard
        )
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ")

def check_payment_status(call, utr):
    try:
        time.sleep(2)
        
        if random.random() < 0.8:
            deposit = deposits.get(utr)
            if deposit and deposit['status'] == 'pending':
                user_id = deposit['user_id']
                amount = deposit['amount']
                
                if user_id not in users:
                    users[user_id] = {'balance': 0, 'deposits': 0, 'spent': 0}
                
                users[user_id]['balance'] += amount
                users[user_id]['deposits'] += amount
                deposits[utr]['status'] = 'completed'
                
                bot.send_message(
                    user_id,
                    f"✅ Pᴀʏᴍᴇɴᴛ Cᴏɴғɪʀᴍᴇᴅ!\n💰 ₹{amount:,.2f} ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ."
                )
                
                for admin_id in ADMIN_IDS:
                    bot.send_message(
                        admin_id,
                        f"💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ\n👤 Usᴇʀ: {user_id}\n💳 Aᴍᴏᴜɴᴛ: ₹{amount:,.2f}\n🔢 UTR: {utr}"
                    )
                
                if CHANNEL_ID:
                    bot.send_message(
                        CHANNEL_ID,
                        f"💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ Rᴇᴄᴇɪᴠᴇᴅ!\n💳 Aᴍᴏᴜɴᴛ: ₹{amount:,.2f}"
                    )
                
            else:
                bot.answer_callback_query(call.id, "❌ Pᴀʏᴍᴇɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ ᴏʀ ᴀʟʀᴇᴀᴅʏ ᴘʀᴏᴄᴇssᴇᴅ")
        else:
            bot.answer_callback_query(call.id, "❌ Pᴀʏᴍᴇɴᴛ ɴᴏᴛ ʏᴇᴛ ᴠᴇʀɪғɪᴇᴅ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ɪɴ 2 ᴍɪɴᴜᴛᴇs.")
            
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴄʜᴇᴄᴋɪɴɢ ᴘᴀʏᴍᴇɴᴛ sᴛᴀᴛᴜs")

def show_orders_menu(call):
    user_orders = {k: v for k, v in orders.items()}
    
    caption = f"""
📦 Mʏ Oʀᴅᴇʀs

Tᴏᴛᴀʟ Oʀᴅᴇʀs: {len(user_orders)}

Usᴇ /track ᴛᴏ ᴄʜᴇᴄᴋ ᴏʀᴅᴇʀ sᴛᴀᴛᴜs
    """.strip()
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_main"))
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            HISTORY_IMAGE,
            caption=caption
        ),
        reply_markup=keyboard
    )

def show_account(call):
    user_id = call.from_user.id
    user_data = users.get(user_id, {})
    
    caption = f"""
👤 Aᴄᴄᴏᴜɴᴛ Iɴғᴏ

🆔 Usᴇʀ ID: {user_id}
💰 Bᴀʟᴀɴᴄᴇ: ₹{user_data.get('balance', 0):,.2f}
📥 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{user_data.get('deposits', 0):,.2f}
📤 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: ₹{user_data.get('spent', 0):,.2f}
📅 Jᴏɪɴᴇᴅ: {time.strftime('%Y-%m-%d', time.gmtime(user_data.get('joined_at', 0)))}
    """.strip()
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_main"))
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            ACCOUNT_IMAGE,
            caption=caption
        ),
        reply_markup=keyboard
    )

def show_support(call):
    caption = f"""
📞 Sᴜᴘᴘᴏʀᴛ

Wᴇ'ʀᴇ ʜᴇʀᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ!

Cᴏɴᴛᴀᴄᴛ ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ᴛᴇᴀᴍ ғᴏʀ ᴀɴʏ ǫᴜᴇsᴛɪᴏɴs ᴏʀ ɪssᴜᴇs.
    """.strip()
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📞 Cᴏɴᴛᴀᴄᴛ Us", url=f"https://wa.me/{SUPPORT_WHATSAPP}"),
        InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_main")
    )
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            SERVICE_IMAGE,
            caption=caption
        ),
        reply_markup=keyboard
    )

def show_refer(call):
    user_id = call.from_user.id
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    
    caption = f"""
👥 Rᴇғᴇʀ & Eᴀʀɴ

Iɴᴠɪᴛᴇ ғʀɪᴇɴᴅs ᴀɴᴅ ᴇᴀʀɴ 10% ᴄᴏᴍᴍɪssɪᴏɴ ᴏɴ ᴛʜᴇɪʀ ᴅᴇᴘᴏsɪᴛs!

🔗 Yᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ:
{referral_link}

✨ Fᴇᴀᴛᴜʀᴇs:
• 10% ᴄᴏᴍᴍɪssɪᴏɴ ᴏɴ ᴇᴠᴇʀʏ ᴅᴇᴘᴏsɪᴛ
• Fʀɪᴇɴᴅ ɢᴇᴛs ₹10 ʙᴏɴᴜs ᴏɴ ғɪʀsᴛ ᴅᴇᴘᴏsɪᴛ
• Nᴏ ʟɪᴍɪᴛ ᴏɴ ᴇᴀʀɴɪɴɢs
    """.strip()
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_main"))
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            REFER_IMAGE,
            caption=caption
        ),
        reply_markup=keyboard
    )

def show_admin_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ")
        return
    
    total_users = len(users)
    total_orders = len(orders)
    total_balance = sum(user.get('balance', 0) for user in users.values())
    
    caption = f"""
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

📊 Sᴛᴀᴛɪsᴛɪᴄs:
├─ 👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
├─ 📦 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
└─ 💰 Tᴏᴛᴀʟ Bᴀʟᴀɴᴄᴇ: ₹{total_balance:,.2f}

Sᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ:
    """.strip()
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            ADMIN_IMAGE,
            caption=caption
        ),
        reply_markup=get_admin_keyboard()
    )

def edit_to_main_menu(call):
    user_id = call.from_user.id
    welcome_text = """
🤖 Wᴇʟᴄᴏᴍᴇ ᴛᴏ Sᴏᴄɪᴀʟ Mᴇᴅɪᴀ Bᴏᴏsᴛᴇʀ!

🚀 Bᴏᴏsᴛ ʏᴏᴜʀ sᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ ᴘʀᴇsᴇɴᴄᴇ ᴡɪᴛʜ ʜɪɢʜ-ǫᴜᴀʟɪᴛʏ sᴇʀᴠɪᴄᴇs.

Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:
    """.strip()
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            WELCOME_IMAGE,
            caption=welcome_text
        ),
        reply_markup=get_main_keyboard(user_id)
    )

# Order Management
def validate_order(user_id, service_id, quantity, link):
    service = get_service_by_id(service_id)
    if not service:
        return False, "Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ"
    
    if not service["active"]:
        return False, "Sᴇʀᴠɪᴄᴇ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ"
    
    if quantity < service["min"] or quantity > service["max"]:
        return False, f"Qᴜᴀɴᴛɪᴛʏ ᴍᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ {service['min']:,} ᴀɴᴅ {service['max']:,}"
    
    if not link.startswith(('http://', 'https://')):
        return False, "Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ URL"
    
    cost = (quantity / 1000) * service["price"]
    user_balance = users.get(user_id, {}).get('balance', 0)
    
    if user_balance < cost:
        return False, f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ. Nᴇᴇᴅᴇᴅ: ₹{cost:.2f}, Aᴠᴀɪʟᴀʙʟᴇ: ₹{user_balance:.2f}"
    
    return True, {"service": service, "cost": cost}

def place_smm_order(order_id, service_id, quantity, link):
    try:
        time.sleep(2)
        
        statuses = ['Pending', 'In progress', 'Completed', 'Partial', 'Cancelled']
        weights = [0.2, 0.5, 0.2, 0.05, 0.05]
        status = random.choices(statuses, weights=weights)[0]
        
        orders[order_id] = {
            'status': status,
            'service_id': service_id,
            'quantity': quantity,
            'link': link,
            'placed_at': time.time(),
            'api_response': f"Simulated {status}",
            'user_id': None  # You can add user_id tracking here
        }
        
        return True, "Oʀᴅᴇʀ ᴘʟᴀᴄᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ"
        
    except Exception as e:
        return False, f"Eʀʀᴏʀ ᴘʟᴀᴄɪɴɢ ᴏʀᴅᴇʀ: {str(e)}"

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    if user_id in user_states and 'waiting_for_link' in user_states[user_id]:
        service_id = user_states[user_id]['waiting_for_link']
        link = message.text
        
        user_states[user_id] = {'waiting_for_quantity': service_id, 'link': link}
        
        service = get_service_by_id(service_id)
        if service:
            bot.send_message(
                message.chat.id,
                f"🔗 Lɪɴᴋ sᴀᴠᴇᴅ: {link[:50]}...\n\n"
                f"📊 Nᴏᴡ ᴇɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ ({service['min']:,} - {service['max']:,} {service['unit']}):"
            )
        return
    
    elif user_id in user_states and 'waiting_for_quantity' in user_states[user_id]:
        service_id = user_states[user_id]['waiting_for_quantity']
        link = user_states[user_id]['link']
        
        handle_new_order(message, service_id, link)
        
        if user_id in user_states:
            del user_states[user_id]
        return
    
    bot.send_message(
        message.chat.id,
        "🤖 Usᴇ ᴛʜᴇ ᴍᴇɴᴜ ʙᴜᴛᴛᴏɴs ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ. Oʀ ᴛʏᴘᴇ /start ᴛᴏ sᴇᴇ ᴛʜᴇ ᴍᴀɪɴ ᴍᴇɴᴜ."
    )

def handle_new_order(message, service_id, link):
    user_id = message.from_user.id
    
    try:
        quantity = int(message.text)
        
        is_valid, result = validate_order(user_id, service_id, quantity, link)
        
        if not is_valid:
            bot.send_message(message.chat.id, result)
            return
        
        service = result["service"]
        cost = result["cost"]
        
        order_id = generate_order_id()
        
        users[user_id]['balance'] -= cost
        users[user_id]['spent'] += cost
        
        success, message_text = place_smm_order(order_id, service_id, quantity, link)
        
        if success:
            bot.send_message(
                message.chat.id,
                f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

📦 Oʀᴅᴇʀ ID: {order_id}
🏷 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {link[:50]}...
📊 Qᴜᴀɴᴛɪᴛʏ: {quantity:,} {service['unit']}
💰 Cᴏsᴛ: ₹{cost:.2f}
📝 Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ

Usᴇ /track ᴛᴏ ᴄʜᴇᴄᴋ sᴛᴀᴛᴜs.
                """.strip()
            )
            
            for admin_id in ADMIN_IDS:
                bot.send_message(
                    admin_id,
                    f"""
🆕 Nᴇᴡ Oʀᴅᴇʀ!
👤 Usᴇʀ: {user_id}
📦 Oʀᴅᴇʀ ID: {order_id}
🏷 Sᴇʀᴠɪᴄᴇ: {service['name']}
💰 Aᴍᴏᴜɴᴛ: ₹{cost:.2f}
                    """.strip()
                )
            
            if CHANNEL_ID:
                bot.send_message(
                    CHANNEL_ID,
                    f"🆕 Nᴇᴡ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ! Oʀᴅᴇʀ ID: {order_id}"
                )
        else:
            users[user_id]['balance'] += cost
            users[user_id]['spent'] -= cost
            bot.send_message(message.chat.id, f"❌ {message_text}")
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ")

# Admin Functions
def handle_admin_callbacks(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ")
        return
    
    if call.data == "admin_broadcast":
        handle_broadcast(call)
    elif call.data == "admin_add_balance":
        handle_add_balance(call)
    elif call.data == "admin_deduct_balance":
        handle_deduct_balance(call)
    elif call.data == "admin_service_price":
        handle_service_price(call)

def handle_broadcast(call):
    bot.send_message(call.message.chat.id, "📢 Sᴇɴᴅ ᴛʜᴇ ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ:")
    bot.register_next_step_handler(call.message, process_broadcast)

def process_broadcast(message):
    if not is_admin(message.from_user.id):
        return
    
    broadcast_text = message.text
    success_count = 0
    
    for user_id in users.keys():
        try:
            bot.send_message(user_id, f"📢 Aɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ:\n\n{broadcast_text}")
            success_count += 1
        except:
            continue
    
    bot.send_message(
        message.chat.id,
        f"✅ Bʀᴏᴀᴅᴄᴀsᴛ sᴇɴᴛ ᴛᴏ {success_count}/{len(users)} ᴜsᴇʀs"
    )

def handle_add_balance(call):
    bot.send_message(call.message.chat.id, "👤 Eɴᴛᴇʀ ᴜsᴇʀ ID:")
    bot.register_next_step_handler(call.message, process_user_id_for_balance, "add")

def handle_deduct_balance(call):
    bot.send_message(call.message.chat.id, "👤 Eɴᴛᴇʀ ᴜsᴇʀ ID:")
    bot.register_next_step_handler(call.message, process_user_id_for_balance, "deduct")

def process_user_id_for_balance(message, action):
    try:
        user_id = int(message.text)
        bot.send_message(message.chat.id, f"💰 Eɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ ᴛᴏ {action}:")
        bot.register_next_step_handler(message, process_balance_amount, user_id, action)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID")

def process_balance_amount(message, user_id, action):
    try:
        amount = float(message.text)
        
        if user_id not in users:
            users[user_id] = {'balance': 0, 'deposits': 0, 'spent': 0}
        
        if action == "add":
            users[user_id]['balance'] += amount
            users[user_id]['deposits'] += amount
            bot.send_message(message.chat.id, f"✅ Aᴅᴅᴇᴅ ₹{amount:,.2f} ᴛᴏ ᴜsᴇʀ {user_id}")
            bot.send_message(user_id, f"💰 Aᴅᴍɪɴ ᴀᴅᴅᴇᴅ ₹{amount:,.2f} ᴛᴏ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ")
        else:
            if users[user_id]['balance'] >= amount:
                users[user_id]['balance'] -= amount
                bot.send_message(message.chat.id, f"✅ Dᴇᴅᴜᴄᴛᴇᴅ ₹{amount:,.2f} ғʀᴏᴍ ᴜsᴇʀ {user_id}")
                bot.send_message(user_id, f"💰 Aᴅᴍɪɴ ᴅᴇᴅᴜᴄᴛᴇᴅ ₹{amount:,.2f} ғʀᴏᴍ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ")
            else:
                bot.send_message(message.chat.id, "❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ")
                
    except ValueError:
        bot.send_message(message.chat.id, "❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ")

def handle_service_price(call):
    keyboard = InlineKeyboardMarkup()
    for category, service_list in SERVICES.items():
        for service in service_list:
            keyboard.add(InlineKeyboardButton(
                f"{service['name']} - ₹{service['price']}", 
                callback_data=f"admin_service_{service['id']}"
            ))
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin_back"))
    
    bot.send_message(
        call.message.chat.id,
        "📦 Sᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ᴘʀɪᴄᴇ:",
        reply_markup=keyboard
    )

# Background Tasks
def refund_background_task():
    while True:
        try:
            # Refund logic here
            time.sleep(1800)
        except Exception as e:
            print(f"Refund task error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    print("🤖 Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ...")
    
    refund_thread = threading.Thread(target=refund_background_task, daemon=True)
    refund_thread.start()
    
    try:
    bot.polling(none_stop=True)
except KeyboardInterrupt:
    print("Bot stopped by user (KeyboardInterrupt).")
except Exception as e:
    print(f"Bot polling terminated with error: {e}")
    try:
        if '401' in str(e) or 'Unauthorized' in str(e):
            print("❌ ERROR: Invalid BOT_TOKEN. Please check your BOT_TOKEN in environment variables.")
    except:
        pass
    raise
