import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
from datetime import datetime
import random
import logging
import urllib.parse

# ✅ BOT TOKEN
BOT_TOKEN = "8052955693:AAGoXnNg90jqvcC1X1fVo_qKV8Y0eHjDAZg"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ✅ DATABASE
users_data = {}
orders_data = []
services_data = []
user_deposit_data = {}

# ✅ CONFIG
ADMIN_ID = 6052975324
CHANNEL_ID = "@prooflelo1"

# ✅ IMAGES
WELCOME_IMAGE = "https://t.me/prooflelo1/16"
SERVICE_IMAGE = "https://t.me/prooflelo1/16" 
DEPOSIT_IMAGE = "https://t.me/prooflelo1/16"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/16"
HISTORY_IMAGE = "https://t.me/prooflelo1/16"
REFER_IMAGE = "https://t.me/prooflelo1/16"

# ✅ SERVICES (FIXED)
services_data = [
    {
        "category": "instagram",
        "name": "Instagram Followers",
        "service_id": "4679",
        "price_per_100": 10,
        "min": 100,
        "max": 300000,
        "description": "✨ Hɪɢʜ-Qᴜᴀʟɪᴛʏ Fᴏʟʟᴏᴡᴇʀs ✨"
    },
    {
        "category": "instagram", 
        "name": "Instagram Likes",
        "service_id": "4961", 
        "price_per_100": 5,
        "min": 100,
        "max": 100000,
        "description": "❤️ Fᴀsᴛ Lɪᴋᴇs Dᴇʟɪᴠᴇʀʏ ❤️"
    },
    {
        "category": "instagram",
        "name": "Instagram Reel Views", 
        "service_id": "3411",
        "price_per_1000": 5,
        "min": 1000,
        "max": 1000000,
        "description": "🚀 Uʟᴛʀᴀ Fᴀsᴛ Rᴇᴇʟ Vɪᴇᴡs 🚀"
    },
    {
        "category": "youtube",
        "name": "YouTube Subscribers", 
        "service_id": "5678",
        "price_per_100": 15,
        "min": 100,
        "max": 50000,
        "description": "📺 Hɪɢʜ-Qᴜᴀʟɪᴛʏ Sᴜʙsᴄʀɪʙᴇʀs 🚀"
    },
    {
        "category": "youtube",
        "name": "YouTube Views",
        "service_id": "8910", 
        "price_per_1000": 8,
        "min": 1000,
        "max": 500000,
        "description": "📺 Rᴇᴀʟ Yᴏᴜᴛᴜʙᴇ Vɪᴇᴡs ⚡"
    }
]

# ✅ USER STATES
user_states = {}

# ✅ CHANNEL CHECK
def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ✅ USER MANAGEMENT
def get_user_balance(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 0, "total_orders": 0, "total_deposits": 0,
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    return users_data[user_id]["balance"]

def update_user_balance(user_id, amount):
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 0, "total_orders": 0, "total_deposits": 0,
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    
    users_data[user_id]["balance"] += amount
    if amount > 0:
        users_data[user_id]["total_deposits"] += amount
    return users_data[user_id]["balance"]

def create_order(user_id, service_name, link, quantity, cost, order_id):
    order = {
        "user_id": user_id, "service_name": service_name, "link": link,
        "quantity": quantity, "cost": cost, "order_id": order_id,
        "status": "Pending", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    orders_data.append(order)
    return order

def get_user_orders(user_id):
    return [order for order in orders_data if order["user_id"] == user_id]

def get_service_by_name(service_name):
    for service in services_data:
        if service["name"] == service_name:
            return service
    return None

def get_services_by_category(category):
    return [service for service in services_data if service["category"] == category]

# ✅ KEYBOARDS
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
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📷 Iɴsᴛᴀɢʀᴀᴍ", callback_data="category_instagram"),
        InlineKeyboardButton("📺 Yᴏᴜᴛᴜʙᴇ", callback_data="category_youtube")
    )
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    return markup

def instagram_services_keyboard():
    markup = InlineKeyboardMarkup()
    services = get_services_by_category("instagram")
    for service in services:
        price = service.get('price_per_100', service.get('price_per_1000', 0))
        unit = "100" if 'price_per_100' in service else "1000"
        markup.add(InlineKeyboardButton(
            f"{service['name']} - {price} Points/{unit}", 
            callback_data=f"service_{service['name'].replace(' ', '_')}"
        ))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order_menu"))
    return markup

def youtube_services_keyboard():
    markup = InlineKeyboardMarkup()
    services = get_services_by_category("youtube")
    for service in services:
        price = service.get('price_per_100', service.get('price_per_1000', 0))
        unit = "100" if 'price_per_100' in service else "1000"
        markup.add(InlineKeyboardButton(
            f"{service['name']} - {price} Points/{unit}", 
            callback_data=f"service_{service['name'].replace(' ', '_')}"
        ))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order_menu"))
    return markup

def channel_join_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Jᴏɪɴ Cʜᴀɴɴᴇʟ", url=f"https://t.me/prooflelo1"))
    markup.add(InlineKeyboardButton("🔃 Cʜᴇᴄᴋ Jᴏɪɴ", callback_data="check_join"))
    return markup

def back_to_menu_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Mᴀɪɴ Mᴇɴᴜ", callback_data="main_menu"))
    return markup

# ✅ START COMMAND
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_id = message.chat.id
        user_name = message.from_user.first_name
        
        if not check_channel_membership(user_id):
            welcome_text = f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

📢 Pʟᴇᴀsᴇ Jᴏɪɴ Oᴜʀ Cʜᴀɴɴᴇʟ Tᴏ Usᴇ Tʜɪs Bᴏᴛ!

Jᴏɪɴ Tʜᴇ Cʜᴀɴɴᴇʟ Bᴇʟᴏᴡ Aɴᴅ Tʜᴇɴ Cʟɪᴄᴋ "Cʜᴇᴄᴋ Jᴏɪɴ" ✅
            """
            bot.send_photo(user_id, WELCOME_IMAGE, welcome_text, reply_markup=channel_join_keyboard())
            return
        
        # User is member, show main menu
        get_user_balance(user_id)  # Initialize user
        
        welcome_text = f"""
✨ Wᴇʟᴄᴏᴍᴇ {user_name}! ✨

🚀 Aᴅᴠᴀɴᴄᴇᴅ SMM Pᴀɴᴇʟ Bᴏᴛ

💎 Fᴀsᴛ Dᴇʟɪᴠᴇʀʏ | 🔐 Sᴇᴄᴜʀᴇ | 💰 Cʜᴇᴀᴘ

Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ Fʀᴏᴍ Bᴇʟᴏᴡ:
        """
        bot.send_photo(user_id, WELCOME_IMAGE, welcome_text, reply_markup=main_menu_keyboard())
        
    except Exception as e:
        print(f"Start error: {e}")

# ✅ CALLBACK HANDLER
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
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
        
        elif call.data == "category_instagram":
            show_instagram_services(call)
        
        elif call.data == "category_youtube":
            show_youtube_services(call)
        
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
        
        elif call.data.startswith("service_"):
            service_name = call.data.replace("service_", "").replace("_", " ")
            start_order(call, service_name)
        
        elif call.data == "check_deposit":
            verify_deposit(call)
            
    except Exception as e:
        print(f"Callback error: {e}")

# ✅ DEPOSIT SYSTEM (YOUR SYSTEM)
def start_deposit(call):
    user_id = call.message.chat.id
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    
    bot.send_photo(user_id, DEPOSIT_IMAGE, 
                  "💰 Eɴᴛᴇʀ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ (ɪɴ ₹):\n\nExᴀᴍᴘʟᴇ: 10, 50, 100")
    
    user_states[user_id] = {"action": "awaiting_deposit_amount"}
    bot.register_next_step_handler(call.message, process_deposit_amount)

def process_deposit_amount(message):
    user_id = message.chat.id
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(user_id, "❌ Mɪɴɪᴍᴜᴍ ₹10 Rᴇǫᴜɪʀᴇᴅ!")
            return
        
        # Generate UTR
        utr = str(random.randint(100000000000, 999999999999))
        user_deposit_data[user_id] = {"utr": utr, "amount": amount}
        
        # Create UPI link and QR
        upi_link = f"upi://pay?pa=paytm.s1m11be@pty&pn=Paytm&am={amount}&tn=Deposit&tr={utr}"
        qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(upi_link)}&size=200"
        
        deposit_text = f"""
💰 Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ 💰

💳 UPI ID: `paytm.s1m11be@pty`
💰 Aᴍᴏᴜɴᴛ: ₹{amount}
🔢 UTR: `{utr}`

Sᴄᴀɴ QR ᴏʀ ᴜsᴇ UPI ID ᴛᴏ ᴘᴀʏ.
Aғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ, ᴄʟɪᴄᴋ 'Pᴀɪᴅ ✅'
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💰 Pᴀɪᴅ ✅", callback_data="check_deposit"))
        markup.add(InlineKeyboardButton("🔙 Mᴀɪɴ Mᴇɴᴜ", callback_data="main_menu"))
        
        bot.send_photo(user_id, qr_url, deposit_text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")

def verify_deposit(call):
    user_id = call.message.chat.id
    if user_id not in user_deposit_data:
        bot.answer_callback_query(call.id, "❌ Nᴏ ᴘᴇɴᴅɪɴɢ ᴅᴇᴘᴏsɪᴛ!", show_alert=True)
        return
    
    deposit = user_deposit_data[user_id]
    utr = deposit["utr"]
    amount = deposit["amount"]
    
    try:
        # Your AutoDep API
        api_url = f"https://erox-autodep-api.onrender.com/api?key=LY81vEV7&merchantkey=WYcmQI71591891985230&transactionid={utr}"
        response = requests.get(api_url, timeout=10).json()
        
        if response.get("result", {}).get("STATUS") == "TXN_SUCCESS":
            points = int(amount * 100)  # 1₹ = 100 points
            new_balance = update_user_balance(user_id, points)
            
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
            try:
                bot.send_message(ADMIN_ID, f"💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ!\nUsᴇʀ: {user_id}\nAᴍᴏᴜɴᴛ: ₹{amount}")
            except:
                pass
            
            del user_deposit_data[user_id]
        else:
            bot.answer_callback_query(call.id, 
                "❌ Pᴀʏᴍᴇɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! Pʟᴇᴀsᴇ ᴘᴀʏ ғɪʀsᴛ.", show_alert=True)
            
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ API ᴇʀʀᴏʀ: {str(e)}", show_alert=True)

# ✅ ORDER SYSTEM (FIXED)
def start_order(call, service_name):
    user_id = call.message.chat.id
    service = get_service_by_name(service_name)
    if not service:
        bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")
        return
    
    user_states[user_id] = {
        "action": "ordering", 
        "service_name": service_name,
        "service": service
    }
    
    price_info = f"💰 {service.get('price_per_100', service.get('price_per_1000', 0))} Points"
    price_info += "/100" if 'price_per_100' in service else "/1000"
    
    service_text = f"""
🛒 {service['name']}

{service['description']}

{price_info}
📊 Mɪɴ: {service['min']} | Mᴀx: {service['max']}

🔗 Sᴇɴᴅ ʏᴏᴜʀ ʟɪɴᴋ:
    """
    
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    
    bot.send_photo(user_id, SERVICE_IMAGE, service_text)
    bot.send_message(user_id, "📩 Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ:")
    bot.register_next_step_handler(call.message, process_order_link)

def process_order_link(message):
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
        if 'price_per_100' in service:
            cost = (quantity // 100) * service['price_per_100']
        else:
            cost = (quantity // 1000) * service['price_per_1000']
        
        balance = get_user_balance(user_id)
        if balance < cost:
            bot.send_message(user_id, f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!\nNᴇᴇᴅ: {cost} | Hᴀᴠᴇ: {balance}")
            return
        
        # Create order
        order_id = f"ORD{random.randint(100000, 999999)}"
        update_user_balance(user_id, -cost)
        create_order(user_id, service['name'], state["link"], quantity, cost, order_id)
        
        success_text = f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ!

🛒 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: {cost} ᴘᴏɪɴᴛs
🆔 ID: {order_id}

Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ ⏳
        """
        bot.send_photo(user_id, SERVICE_IMAGE, success_text, reply_markup=main_menu_keyboard())
        
        # Notify admin
        try:
            bot.send_message(ADMIN_ID, f"🛒 Nᴇᴡ Oʀᴅᴇʀ!\nUsᴇʀ: {user_id}\nSᴇʀᴠɪᴄᴇ: {service['name']}\nQᴛʏ: {quantity}")
        except:
            pass
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Usᴇ ɴᴜᴍʙᴇʀs.")

# ✅ MENU HANDLERS
def show_main_menu(call):
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
    text = "📦 Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴄᴀᴛᴇɢᴏʀʏ:"
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(SERVICE_IMAGE, caption=text),
            reply_markup=service_category_keyboard()
        )
    except:
        bot.send_photo(call.message.chat.id, SERVICE_IMAGE, text, reply_markup=service_category_keyboard())

def show_instagram_services(call):
    text = "📷 Iɴsᴛᴀɢʀᴀᴍ Sᴇʀᴠɪᴄᴇs:"
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(SERVICE_IMAGE, caption=text),
            reply_markup=instagram_services_keyboard()
        )
    except:
        bot.send_photo(call.message.chat.id, SERVICE_IMAGE, text, reply_markup=instagram_services_keyboard())

def show_youtube_services(call):
    text = "📺 Yᴏᴜᴛᴜʙᴇ Sᴇʀᴠɪᴄᴇs:"
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(SERVICE_IMAGE, caption=text),
            reply_markup=youtube_services_keyboard()
        )
    except:
        bot.send_photo(call.message.chat.id, SERVICE_IMAGE, text, reply_markup=youtube_services_keyboard())

def show_history(call):
    user_id = call.message.chat.id
    orders = get_user_orders(user_id)
    
    if not orders:
        text = "📭 Nᴏ ᴏʀᴅᴇʀ ʜɪsᴛᴏʀʏ ғᴏᴜɴᴅ."
    else:
        text = "📋 Lᴀsᴛ 5 Oʀᴅᴇʀs:\n\n"
        for order in orders[-5:]:
            text += f"""🛒 {order['service_name']}
🔢 {order['quantity']} | 💰 {order['cost']}ᴘ
🆔 {order['order_id']}
📅 {order['created_at']}
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
    user_id = call.message.chat.id
    user = users_data.get(user_id, {})
    
    text = f"""👤 Aᴄᴄᴏᴜɴᴛ Iɴғᴏ

🏦 Bᴀʟᴀɴᴄᴇ: {user.get('balance', 0)} ᴘᴏɪɴᴛs
🛒 Tᴏᴛᴀʟ sᴘᴇɴᴛ: {user.get('total_orders', 0)} ᴘᴏɪɴᴛs
💰 Tᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛ: {user.get('total_deposits', 0)} ᴘᴏɪɴᴛs
📅 Jᴏɪɴᴇᴅ: {user.get('joined_date', 'N/A')}

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
    user_id = call.message.chat.id
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    text = f"""👥 Rᴇғᴇʀ & Eᴀʀɴ

🔗 Rᴇғᴇʀʀᴀʟ ʟɪɴᴋ:
{ref_link}

🎯 Yᴏᴜ ɢᴇᴛ: 100 ᴘᴏɪɴᴛs ᴘᴇʀ ʀᴇғᴇʀʀᴀʟ
🎁 Fʀɪᴇɴᴅ ɢᴇᴛs: 50 ᴘᴏɪɴᴛs ʙᴏɴᴜs
"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📤 Sʜᴀʀᴇ Lɪɴᴋ", url=f"tg://msg_url?text=Join%20this%20SMM%20bot:%20{ref_link}"))
    markup.add(InlineKeyboardButton("🔙 Mᴀɪɴ Mᴇɴᴜ", callback_data="main_menu"))
    
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
    text = """📞 Sᴜᴘᴘᴏʀᴛ

🤵 Cᴜsᴛᴏᴍᴇʀ sᴜᴘᴘᴏʀᴛ: @YourSupport
📧 Email: support@example.com

Wᴇ'ʀᴇ ʜᴇʀᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ! ⏰
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

def show_stats(call):
    total_points = sum(order['cost'] for order in orders_data)
    text = f"""📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs

👥 Tᴏᴛᴀʟ ᴜsᴇʀs: {len(users_data)}
🛒 Tᴏᴛᴀʟ ᴏʀᴅᴇʀs: {len(orders_data)}
💰 Pᴏɪɴᴛs sᴘᴇɴᴛ: {total_points}

🚀 Sʏsᴛᴇᴍ ᴏᴘᴇʀᴀᴛɪᴏɴᴀʟ
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

# ✅ ADMIN COMMANDS
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return
    
    text = f"""👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

👥 Usᴇʀs: {len(users_data)}
🛒 Oʀᴅᴇʀs: {len(orders_data)}
💰 Tᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛs: {sum(user.get('total_deposits', 0) for user in users_data.values())}

Cᴏᴍᴍᴀɴᴅs:
/addpoints <user_id> <amount> - Aᴅᴅ ᴘᴏɪɴᴛs
/broadcast <message> - Sᴇɴᴅ ᴛᴏ ᴀʟʟ ᴜsᴇʀs
"""
    bot.send_message(ADMIN_ID, text)

@bot.message_handler(commands=['addpoints'])
def add_points(message):
    if message.chat.id != ADMIN_ID:
        return
    
    try:
        _, user_id, amount = message.text.split()
        user_id = int(user_id)
        amount = int(amount)
        
        new_balance = update_user_balance(user_id, amount)
        bot.send_message(ADMIN_ID, f"✅ Aᴅᴅᴇᴅ {amount} ᴘᴏɪɴᴛs ᴛᴏ {user_id}\nNᴇᴡ ʙᴀʟᴀɴᴄᴇ: {new_balance}")
        bot.send_message(user_id, f"🎁 Aᴅᴍɪɴ ᴀᴅᴅᴇᴅ {amount} ᴘᴏɪɴᴛs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ!")
        
    except:
        bot.send_message(ADMIN_ID, "❌ Usᴀɢᴇ: /addpoints <user_id> <amount>")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id != ADMIN_ID:
        return
    
    broadcast_text = message.text.replace('/broadcast', '').strip()
    if not broadcast_text:
        bot.send_message(ADMIN_ID, "❌ Usᴀɢᴇ: /broadcast <message>")
        return
    
    success = 0
    for user_id in users_data.keys():
        try:
            bot.send_message(user_id, f"📢 Aɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ:\n\n{broadcast_text}")
            success += 1
            time.sleep(0.1)
        except:
            continue
    
    bot.send_message(ADMIN_ID, f"✅ Bʀᴏᴀᴅᴄᴀsᴛ sᴇɴᴛ ᴛᴏ {success} ᴜsᴇʀs")

# ✅ TEXT COMMANDS
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.lower()
    
    if text in ['/start', 'start', 'menu']:
        send_welcome(message)
    elif text in ['/deposit', 'deposit']:
        # Simulate deposit callback
        class MockCall:
            def __init__(self): 
                self.message = message
                self.id = "mock"
        start_deposit(MockCall())
    elif text in ['/balance', 'balance', 'account']:
        show_account(MockCall())
    elif text in ['/orders', 'orders', 'history']:
        show_history(MockCall())
    elif text in ['/support', 'support', 'help']:
        show_support(MockCall())
    else:
        bot.send_photo(message.chat.id, WELCOME_IMAGE, 
                      "❓ Uɴᴋɴᴏᴡɴ ᴄᴏᴍᴍᴀɴᴅ\n\nUsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴏʀ /start",
                      reply_markup=main_menu_keyboard())

class MockCall:
    def __init__(self):
        self.message = type('Message', (), {'chat': type('Chat', (), {'id': None})})()
        self.message.chat.id = None

# ✅ START BOT
if __name__ == "__main__":
    print("🤖 Bᴏᴛ sᴛᴀʀᴛᴇᴅ...")
    print(f"🔗 Lɪɴᴋ: t.me/{bot.get_me().username}")
    
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"❌ Eʀʀᴏʀ: {e}")
            time.sleep(10)
