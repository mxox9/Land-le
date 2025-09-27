import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
from datetime import datetime
import random
import logging

# ✅ APNA BOT TOKEN YAHAN DALO
BOT_TOKEN = "8052955693:AAGoXnNg90jqvcC1X1fVo_qKV8Y0eHjDAZg"

# ✅ BOT INITIALIZE WITH THREADED=FALSE
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ✅ SIMPLE IN-MEMORY DATABASE (MongoDB ki zaroorat nahi)
users_data = {}
orders_data = []
services_data = []

# ✅ ADMIN CONFIG
ADMIN_ID = 6052975324
ADMIN_PASSWORD = "SmOx9679"
SMM_API_KEY = "a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d"

# ✅ DEFAULT SERVICES
default_services = [
    {
        "category": "instagram",
        "name": "Instagram Followers",
        "service_id": "4679",
        "price_per_100": 1000,
        "min": 100,
        "max": 300000,
        "description": "✨ Hɪɢʜ-Qᴜᴀʟɪᴛʏ Fᴏʟʟᴏᴡᴇʀs ✨"
    },
    {
        "category": "instagram", 
        "name": "Instagram Likes",
        "service_id": "4961",
        "price_per_100": 250,
        "min": 100,
        "max": 100000,
        "description": "❤️ Fᴀsᴛ Lɪᴋᴇs Dᴇʟɪᴠᴇʀʏ ❤️"
    },
    {
        "category": "instagram",
        "name": "Instagram Reel Views", 
        "service_id": "3411",
        "price_per_1000": 250,
        "min": 5000,
        "max": 1000000,
        "description": "🚀 Uʟᴛʀᴀ Fᴀsᴛ Rᴇᴇʟ Vɪᴇᴡs 🚀"
    },
    {
        "category": "facebook",
        "name": "Facebook Followers",
        "service_id": "1234",
        "price_per_100": 800,
        "min": 100,
        "max": 50000,
        "description": "📘 Fᴀᴄᴇʙᴏᴏᴋ Fᴏʟʟᴏᴡᴇʀs ✨"
    },
    {
        "category": "youtube",
        "name": "YouTube Subscribers", 
        "service_id": "5678",
        "price_per_100": 1200,
        "min": 100,
        "max": 100000,
        "description": "📺 Yᴏᴜᴛᴜʙᴇ Sᴜʙsᴄʀɪʙᴇʀs 🚀"
    }
]

# ✅ INITIALIZE SERVICES
services_data.extend(default_services)

# ✅ USER STATES FOR CONVERSATION
user_states = {}

# ✅ USER MANAGEMENT FUNCTIONS
def get_user_balance(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "user_id": user_id,
            "balance": 0,
            "total_orders": 0,
            "total_deposits": 0,
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    return users_data[user_id]["balance"]

def update_user_balance(user_id, amount):
    if user_id not in users_data:
        users_data[user_id] = {
            "user_id": user_id,
            "balance": 0,
            "total_orders": 0,
            "total_deposits": 0,
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    
    users_data[user_id]["balance"] += amount
    if amount > 0:
        users_data[user_id]["total_deposits"] += amount
    return users_data[user_id]["balance"]

def create_order(user_id, service_name, link, quantity, cost, order_id):
    order = {
        "user_id": user_id,
        "service_name": service_name,
        "link": link,
        "quantity": quantity,
        "cost": cost,
        "order_id": order_id,
        "status": "In Progress",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    orders_data.append(order)
    
    # Update user's total orders
    if user_id in users_data:
        users_data[user_id]["total_orders"] += cost
    
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

# ✅ KEYBOARD FUNCTIONS
def main_menu_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("💰 Dᴇᴘᴏsɪᴛ", callback_data="deposit"),
        InlineKeyboardButton("🛒 Oʀᴅᴇʀ", callback_data="order_menu")
    )
    markup.add(
        InlineKeyboardButton("📋 Hɪsᴛᴏʀʏ", callback_data="history"),
        InlineKeyboardButton("👥 Rᴇғᴇʀ", callback_data="refer")
    )
    markup.add(InlineKeyboardButton("👤 Mʏ Aᴄᴄᴏᴜɴᴛ", callback_data="account"))
    return markup

def service_category_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📷 Iɴsᴛᴀɢʀᴀᴍ", callback_data="service_instagram"),
        InlineKeyboardButton("📘 Fᴀᴄᴇʙᴏᴏᴋ", callback_data="service_facebook")
    )
    markup.add(
        InlineKeyboardButton("📺 Yᴏᴜᴛᴜʙᴇ", callback_data="service_youtube"),
        InlineKeyboardButton("✈️ Tᴇʟᴇɢʀᴀᴍ", callback_data="service_telegram")
    )
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    return markup

def instagram_services_keyboard():
    markup = InlineKeyboardMarkup()
    instagram_services = get_services_by_category("instagram")
    
    for service in instagram_services:
        markup.add(InlineKeyboardButton(
            f"✨ {service['name']}", 
            callback_data=f"order_{service['name'].replace(' ', '_')}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order_menu"))
    return markup

def facebook_services_keyboard():
    markup = InlineKeyboardMarkup()
    facebook_services = get_services_by_category("facebook")
    
    for service in facebook_services:
        markup.add(InlineKeyboardButton(
            f"📘 {service['name']}", 
            callback_data=f"order_{service['name'].replace(' ', '_')}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order_menu"))
    return markup

def youtube_services_keyboard():
    markup = InlineKeyboardMarkup()
    youtube_services = get_services_by_category("youtube")
    
    for service in youtube_services:
        markup.add(InlineKeyboardButton(
            f"📺 {service['name']}", 
            callback_data=f"order_{service['name'].replace(' ', '_')}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order_menu"))
    return markup

# ✅ START COMMAND - FIXED
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_id = message.chat.id
        user_name = message.from_user.first_name
        
        welcome_text = f"""
✨ Wᴇʟᴄᴏᴍᴇ {user_name}! ✨

Tʜɪs Is Tʜᴇ Mᴏsᴛ Aᴅᴠᴀɴᴄᴇᴅ SMM Bᴏᴛ Oɴ Tᴇʟᴇɢʀᴀᴍ! 🚀

Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ Fʀᴏᴍ Tʜᴇ Mᴇɴᴜ Bᴇʟᴏᴡ:
        """
        
        # Initialize user if not exists
        get_user_balance(user_id)
        
        bot.send_message(
            chat_id=user_id,
            text=welcome_text,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"Error in start command: {e}")
        bot.send_message(message.chat.id, "❌ Error occurred. Please try again.")

# ✅ CALLBACK QUERY HANDLER - FIXED
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        user_id = call.message.chat.id
        
        if call.data == "main_menu":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="🏠 Mᴀɪɴ Mᴇɴᴜ - Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ:",
                reply_markup=main_menu_keyboard(),
                parse_mode="HTML"
            )
        
        elif call.data == "deposit":
            handle_deposit(call)
        
        elif call.data == "order_menu":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="🛒 Sᴇʟᴇᴄᴛ A Sᴇʀᴠɪᴄᴇ Cᴀᴛᴇɢᴏʀʏ:",
                reply_markup=service_category_keyboard(),
                parse_mode="HTML"
            )
        
        elif call.data == "history":
            handle_history(call)
        
        elif call.data == "refer":
            handle_refer(call)
        
        elif call.data == "account":
            handle_account(call)
        
        elif call.data == "service_instagram":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📷 Iɴsᴛᴀɢʀᴀᴍ Sᴇʀᴠɪᴄᴇs - Cʜᴏᴏsᴇ Oɴᴇ:",
                reply_markup=instagram_services_keyboard(),
                parse_mode="HTML"
            )
        
        elif call.data == "service_facebook":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📘 Fᴀᴄᴇʙᴏᴏᴋ Sᴇʀᴠɪᴄᴇs - Cʜᴏᴏsᴇ Oɴᴇ:",
                reply_markup=facebook_services_keyboard(),
                parse_mode="HTML"
            )
        
        elif call.data == "service_youtube":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📺 Yᴏᴜᴛᴜʙᴇ Sᴇʀᴠɪᴄᴇs - Cʜᴏᴏsᴇ Oɴᴇ:",
                reply_markup=youtube_services_keyboard(),
                parse_mode="HTML"
            )
        
        elif call.data.startswith("order_"):
            service_name = call.data.replace("order_", "").replace("_", " ")
            user_states[user_id] = {"action": "ordering", "service_name": service_name}
            
            service = get_service_by_name(service_name)
            if service:
                price_info = ""
                if 'price_per_100' in service:
                    price_info = f"💸 Pʀɪᴄᴇ: {service['price_per_100']} Pᴏɪɴᴛs Pᴇʀ 100"
                elif 'price_per_1000' in service:
                    price_info = f"💸 Pʀɪᴄᴇ: {service['price_per_1000']} Pᴏɪɴᴛs Pᴇʀ 1000"
                
                service_text = f"""
✨ {service['name']} ✨

{service['description']}

{price_info}
🔰 Mɪɴ: {service['min']} | Mᴀx: {service['max']}

Pʟᴇᴀsᴇ Sᴇɴᴅ Tʜᴇ Lɪɴᴋ:
                """
                
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    text=service_text,
                    parse_mode="HTML"
                )
                
                bot.send_message(user_id, "🔗 Pʟᴇᴀsᴇ Sᴇɴᴅ Tʜᴇ Lɪɴᴋ:")
                bot.register_next_step_handler(call.message, process_order_link)
        
        elif call.data == "check_deposit":
            handle_deposit_check(call)
            
    except Exception as e:
        print(f"Callback error: {e}")
        bot.send_message(user_id, "❌ Error occurred. Please try /start")

# ✅ DEPOSIT HANDLER
def handle_deposit(call):
    user_id = call.message.chat.id
    amount = 100  # Default amount
    
    # Generate UTR
    utr = str(random.randint(100000000000, 999999999999))
    
    # Save deposit info
    user_states[user_id] = {
        "action": "deposit",
        "utr": utr,
        "amount": amount
    }
    
    deposit_text = f"""
💰 Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ 💰

Aᴍᴏᴜɴᴛ: ₹{amount}
UTR: {utr}

Pʟᴇᴀsᴇ Usᴇ Tʜᴇ Fᴏʟʟᴏᴡɪɴɢ Dᴇᴛᴀɪʟs Fᴏʀ Pᴀʏᴍᴇɴᴛ:

UPI ID: paytm.s1m11be@pty
Aᴍᴏᴜɴᴛ: ₹{amount}
Nᴏᴛᴇ: {utr}

Aғᴛᴇʀ Pᴀʏᴍᴇɴᴛ, Cʟɪᴄᴋ 'Pᴀɪᴅ ✅' Bᴇʟᴏᴡ.
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💰 Pᴀɪᴅ ✅", callback_data="check_deposit"))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text=deposit_text,
        reply_markup=markup,
        parse_mode="HTML"
    )

# ✅ DEPOSIT CHECK HANDLER
def handle_deposit_check(call):
    user_id = call.message.chat.id
    user_state = user_states.get(user_id, {})
    
    if user_state.get("action") == "deposit":
        amount = user_state.get("amount", 0)
        points_to_add = amount * 100  # 1 INR = 100 points
        
        # Simulate payment verification
        new_balance = update_user_balance(user_id, points_to_add)
        
        success_text = f"""
✅ Pᴀʏᴍᴇɴᴛ Sᴜᴄᴄᴇssғᴜʟ! ✅

💰 Aᴍᴏᴜɴᴛ Dᴇᴘᴏsɪᴛᴇᴅ: ₹{amount}
🎯 Pᴏɪɴᴛs Aᴅᴅᴇᴅ: {points_to_add}
🏦 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} Pᴏɪɴᴛs

Tʜᴀɴᴋ Yᴏᴜ Fᴏʀ Yᴏᴜʀ Dᴇᴘᴏsɪᴛ! 🎉
        """
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=success_text,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
        
        # Notify admin
        try:
            bot.send_message(
                ADMIN_ID,
                f"💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ!\n\nUsᴇʀ: {user_id}\nAᴍᴏᴜɴᴛ: ₹{amount}\nPᴏɪɴᴛs: {points_to_add}"
            )
        except:
            pass

# ✅ HISTORY HANDLER
def handle_history(call):
    user_id = call.message.chat.id
    orders = get_user_orders(user_id)
    
    if not orders:
        history_text = "📭 Nᴏ Oʀᴅᴇʀ Hɪsᴛᴏʀʏ Fᴏᴜɴᴅ"
    else:
        history_text = "📋 Yᴏᴜʀ Oʀᴅᴇʀ Hɪsᴛᴏʀʏ:\n\n"
        for order in orders[:10]:  # Show last 10 orders
            status_emoji = "🟢" if order['status'] == 'Completed' else "🟡" if order['status'] == 'In Progress' else "🔴"
            history_text += f"""
{status_emoji} Sᴇʀᴠɪᴄᴇ: {order['service_name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💰 Cᴏsᴛ: {order['cost']} Pᴏɪɴᴛs
🆔 Oʀᴅᴇʀ ID: {order['order_id']}
📅 Dᴀᴛᴇ: {order['created_at']}
📊 Sᴛᴀᴛᴜs: {order['status']}
────────────────
            """
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text=history_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

# ✅ ACCOUNT HANDLER
def handle_account(call):
    user_id = call.message.chat.id
    user = users_data.get(user_id, {})
    
    account_text = f"""
👤 Mʏ Aᴄᴄᴏᴜɴᴛ 👤

🏦 Aᴠᴀɪʟᴀʙʟᴇ Bᴀʟᴀɴᴄᴇ: {user.get('balance', 0)} Pᴏɪɴᴛs
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {user.get('total_orders', 0)} Pᴏɪɴᴛs
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: {user.get('total_deposits', 0)} Pᴏɪɴᴛs
📅 Mᴇᴍʙᴇʀ Sɪɴᴄᴇ: {user.get('joined_date', 'N/A')}

Usᴇʀ ID: {user_id}
    """
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text=account_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

# ✅ REFER HANDLER
def handle_refer(call):
    user_id = call.message.chat.id
    bot_username = bot.get_me().username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    refer_text = f"""
👥 Rᴇғᴇʀ & Eᴀʀɴ 👥

Iɴᴠɪᴛᴇ Fʀɪᴇɴᴅs Aɴᴅ Eᴀʀɴ 100 Pᴏɪɴᴛs Pᴇʀ Rᴇғᴇʀʀᴀʟ!

Yᴏᴜʀ Rᴇғᴇʀʀᴀʟ Lɪɴᴋ:
{referral_link}

🔹 Yᴏᴜ Gᴇᴛ: 100 Pᴏɪɴᴛs Pᴇʀ Rᴇғᴇʀʀᴀʟ
🔹 Fʀɪᴇɴᴅ Gᴇᴛs: 50 Pᴏɪɴᴛs Wᴇʟᴄᴏᴍᴇ Bᴏɴᴜs

Sʜᴀʀᴇ Tʜɪs Lɪɴᴋ Wɪᴛʜ Yᴏᴜʀ Fʀɪᴇɴᴅs! 🎉
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📤 Sʜᴀʀᴇ Lɪɴᴋ", url=f"tg://msg_url?text=Join%20this%20awesome%20bot%3A%20{referral_link}"))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text=refer_text,
        reply_markup=markup,
        parse_mode="HTML"
    )

# ✅ ORDER PROCESSING
def process_order_link(message):
    user_id = message.chat.id
    user_state = user_states.get(user_id, {})
    
    if user_state.get("action") == "ordering":
        link = message.text
        if not link.startswith("http"):
            bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Lɪɴᴋ! Pʟᴇᴀsᴇ Sᴇɴᴅ A Vᴀʟɪᴅ HTTP/S Lɪɴᴋ.")
            return
        
        user_state["link"] = link
        user_states[user_id] = user_state
        
        service = get_service_by_name(user_state["service_name"])
        if service:
            bot.send_message(
                user_id,
                f"🔢 Nᴏᴡ Pʟᴇᴀsᴇ Eɴᴛᴇʀ Tʜᴇ Qᴜᴀɴᴛɪᴛʏ:\n\nMɪɴ: {service['min']} | Mᴀx: {service['max']}"
            )
            bot.register_next_step_handler(message, process_order_quantity)

def process_order_quantity(message):
    user_id = message.chat.id
    user_state = user_states.get(user_id, {})
    
    if user_state.get("action") == "ordering":
        try:
            quantity = int(message.text)
            service = get_service_by_name(user_state["service_name"])
            
            if not service:
                bot.send_message(user_id, "❌ Sᴇʀᴠɪᴄᴇ Nᴏᴛ Fᴏᴜɴᴅ!")
                return
            
            # Validate quantity
            if quantity < service['min']:
                bot.send_message(user_id, f"❌ Qᴜᴀɴᴛɪᴛʏ Tᴏᴏ Lᴏᴡ! Mɪɴɪᴍᴜᴍ: {service['min']}")
                return
            
            if quantity > service['max']:
                bot.send_message(user_id, f"❌ Qᴜᴀɴᴛɪᴛʏ Tᴏᴏ Hɪɢʜ! Mᴀxɪᴍᴜᴍ: {service['max']}")
                return
            
            # Calculate cost
            if 'price_per_100' in service:
                cost = (quantity // 100) * service['price_per_100']
            elif 'price_per_1000' in service:
                cost = (quantity // 1000) * service['price_per_1000']
            else:
                cost = quantity  # Fallback
            
            user_balance = get_user_balance(user_id)
            
            if user_balance < cost:
                bot.send_message(
                    user_id,
                    f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ!\n\nYᴏᴜʀ Bᴀʟᴀɴᴄᴇ: {user_balance} Pᴏɪɴᴛs\nRᴇǫᴜɪʀᴇᴅ: {cost} Pᴏɪɴᴛs"
                )
                return
            
            # Place order
            order_id = f"ORD{random.randint(100000, 999999)}"
            
            # Deduct balance
            new_balance = update_user_balance(user_id, -cost)
            
            # Save order
            create_order(user_id, service['name'], user_state["link"], quantity, cost, order_id)
            
            success_text = f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ! ✅

✨ Sᴇʀᴠɪᴄᴇ: {service['name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: {cost} Pᴏɪɴᴛs
🆔 Oʀᴅᴇʀ ID: {order_id}
🏦 Rᴇᴍᴀɪɴɪɴɢ Bᴀʟᴀɴᴄᴇ: {new_balance} Pᴏɪɴᴛs

Oʀᴅᴇʀ Wɪʟʟ Bᴇ Cᴏᴍᴘʟᴇᴛᴇᴅ Sʜᴏʀᴛʟʏ! ⏳
            """
            
            bot.send_message(
                user_id,
                text=success_text,
                reply_markup=main_menu_keyboard(),
                parse_mode="HTML"
            )
            
            # Notify admin
            try:
                bot.send_message(
                    ADMIN_ID,
                    f"🛒 Nᴇᴡ Oʀᴅᴇʀ!\n\nUsᴇʀ: {user_id}\nSᴇʀᴠɪᴄᴇ: {service['name']}\nQᴜᴀɴᴛɪᴛʏ: {quantity}\nOʀᴅᴇʀ ID: {order_id}"
                )
            except:
                pass
            
        except ValueError:
            bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Qᴜᴀɴᴛɪᴛʏ! Pʟᴇᴀsᴇ Eɴᴛᴇʀ A Nᴜᴍʙᴇʀ.")

# ✅ ADMIN COMMAND
@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.chat.id == ADMIN_ID:
        admin_text = """
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ 👑

Tᴏᴛᴀʟ Usᴇʀs: {}
Tᴏᴛᴀʟ Oʀᴅᴇʀs: {}

Usᴇ /stats ғᴏʀ ᴅᴇᴛᴀɪʟᴇᴅ sᴛᴀᴛɪsᴛɪᴄs
        """.format(len(users_data), len(orders_data))
        
        bot.send_message(message.chat.id, admin_text)

# ✅ STATS COMMAND
@bot.message_handler(commands=['stats'])
def stats_command(message):
    total_points = sum(order['cost'] for order in orders_data)
    
    stats_text = f"""
📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs 📊

👥 Tᴏᴛᴀʟ Usᴇʀs: {len(users_data)}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {len(orders_data)}
💰 Tᴏᴛᴀʟ Pᴏɪɴᴛs Sᴘᴇɴᴛ: {total_points}

🚀 Bᴏᴛ Is Rᴜɴɴɪɴɢ Sᴍᴏᴏᴛʜʟʏ!
    """
    
    bot.send_message(message.chat.id, stats_text)

# ✅ SUPPORT COMMAND
@bot.message_handler(commands=['support'])
def support_command(message):
    support_text = """
📞 Sᴜᴘᴘᴏʀᴛ & Hᴇʟᴘ 📞

Iғ Yᴏᴜ Hᴀᴠᴇ Aɴʏ Issᴜᴇs Oʀ Qᴜᴇsᴛɪᴏɴs, Cᴏɴᴛᴀᴄᴛ Oᴜʀ Sᴜᴘᴘᴏʀᴛ:

👤 Cᴜsᴛᴏᴍᴇʀ Sᴜᴘᴘᴏʀᴛ: @YourSupport
📧 Eᴍᴀɪʟ: support@example.com

Wᴇ'ʀᴇ Hᴇʀᴇ Tᴏ Hᴇʟᴘ Yᴏᴜ! ⏰
    """
    
    bot.send_message(message.chat.id, support_text)

# ✅ HANDLE TEXT MESSAGES
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.lower()
    
    if text in ['menu', 'start', 'home', '/start']:
        send_welcome(message)
    elif text in ['balance', 'account', '/account']:
        handle_account_from_text(message)
    elif text in ['stats', 'statistics', '/stats']:
        stats_command(message)
    elif text in ['support', 'help', '/support']:
        support_command(message)
    else:
        bot.send_message(
            message.chat.id,
            "❓ I Dᴏɴ'ᴛ Uɴᴅᴇʀsᴛᴀɴᴅ Tʜᴀᴛ Cᴏᴍᴍᴀɴᴅ.\n\nUsᴇ /start Tᴏ Sᴇᴇ Tʜᴇ Mᴀɪɴ Mᴇɴᴜ."
        )

def handle_account_from_text(message):
    user_id = message.chat.id
    user = users_data.get(user_id, {})
    
    account_text = f"""
👤 Mʏ Aᴄᴄᴏᴜɴᴛ 👤

🏦 Aᴠᴀɪʟᴀʙʟᴇ Bᴀʟᴀɴᴄᴇ: {user.get('balance', 0)} Pᴏɪɴᴛs
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {user.get('total_orders', 0)} Pᴏɪɴᴛs
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: {user.get('total_deposits', 0)} Pᴏɪɴᴛs

Usᴇʀ ID: {user_id}
    """
    
    bot.send_message(
        user_id,
        text=account_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

# ✅ START THE BOT
if __name__ == "__main__":
    print("🤖 Bᴏᴛ Is Rᴜɴɴɪɴɢ...")
    print(f"👤 Bᴏᴛ Usᴇʀɴᴀᴍᴇ: @{bot.get_me().username}")
    
    try:
        bot.polling(none_stop=True, interval=2, timeout=60)
    except Exception as e:
        print(f"❌ Eʀʀᴏʀ: {e}")
        print("🔄 Rᴇsᴛᴀʀᴛɪɴɢ ɪɴ 10 sᴇᴄᴏɴᴅs...")
        time.sleep(10)