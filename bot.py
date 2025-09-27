import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import requests
import time
from datetime import datetime
import threading
from pymongo import MongoClient
import os

# Bot Token
BOT_TOKEN = "8052955693:AAGoXnNg90jqvcC1X1fVo_qKV8Y0eHjDAZg"
bot = telebot.TeleBot(BOT_TOKEN)

# MongoDB Setup
MONGO_URI = "mongodb+srv://saifulmolla79088179_db_user:17gNrX0pC3bPqVaG@cluster0.fusvqca.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0"  # Change to your MongoDB URI
client = MongoClient(MONGO_URI)
db = client.telegram_bot
users_collection = db.users
orders_collection = db.orders
services_collection = db.services
admin_collection = db.admin

# Admin Configuration
ADMIN_ID = 6052975324  # Your Telegram ID
ADMIN_PASSWORD = "SmOx9679"

# SMM Panel API
SMM_API_KEY = "a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d"

# Initialize default services if not exists
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
    }
]

if services_collection.count_documents({}) == 0:
    services_collection.insert_many(default_services)

# User states for conversation handling
user_states = {}

def get_user_balance(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        return user.get('balance', 0)
    else:
        users_collection.insert_one({
            "user_id": user_id,
            "balance": 0,
            "total_orders": 0,
            "total_deposits": 0,
            "joined_date": datetime.now()
        })
        return 0

def update_user_balance(user_id, amount):
    current_balance = get_user_balance(user_id)
    new_balance = current_balance + amount
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"balance": new_balance}}
    )
    return new_balance

def create_order(user_id, service_name, link, quantity, cost, order_id):
    order_data = {
        "user_id": user_id,
        "service_name": service_name,
        "link": link,
        "quantity": quantity,
        "cost": cost,
        "order_id": order_id,
        "status": "In Progress",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    orders_collection.insert_one(order_data)
    
    # Update user's total orders
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"total_orders": cost}}
    )

def get_user_orders(user_id):
    return list(orders_collection.find({"user_id": user_id}).sort("created_at", -1))

def get_service_by_name(service_name):
    return services_collection.find_one({"name": service_name})

# Auto-refund system
def check_orders_status():
    while True:
        try:
            # Get orders that are in progress
            in_progress_orders = orders_collection.find({"status": "In Progress"})
            
            for order in in_progress_orders:
                # Check order status from SMM API (simplified)
                # In real implementation, you'd call your SMM panel API
                time.sleep(2)  # Prevent API rate limiting
                
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            print(f"Error in auto-refund system: {e}")
            time.sleep(60)

# Start auto-refund thread
refund_thread = threading.Thread(target=check_orders_status, daemon=True)
refund_thread.start()

# Text styling function
def style_text(text):
    words = text.split()
    styled_words = []
    for word in words:
        if word:
            styled_words.append(word[0].upper() + word[1:].lower())
        else:
            styled_words.append(word)
    return ' '.join(styled_words)

# Main menu inline keyboard
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
    return markup

# Service category keyboard
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

# Instagram services keyboard
def instagram_services_keyboard():
    markup = InlineKeyboardMarkup()
    instagram_services = services_collection.find({"category": "instagram"})
    
    for service in instagram_services:
        markup.add(InlineKeyboardButton(
            f"✨ {service['name']}", 
            callback_data=f"order_{service['name']}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order_menu"))
    return markup

# Admin keyboard
def admin_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("👥 Mᴀɴᴀɢᴇ Usᴇʀs", callback_data="admin_users"),
        InlineKeyboardButton("🛠 Mᴀɴᴀɢᴇ Sᴇʀᴠɪᴄᴇs", callback_data="admin_services")
    )
    markup.add(
        InlineKeyboardButton("📊 Bᴏᴛ Sᴛᴀᴛs", callback_data="admin_stats"),
        InlineKeyboardButton("📢 Bʀᴏᴀᴅᴄᴀsᴛ", callback_data="admin_broadcast")
    )
    markup.add(InlineKeyboardButton("⚙️ Bᴏᴛ Sᴇᴛᴛɪɴɢs", callback_data="admin_settings"))
    return markup

# Start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name
    
    welcome_text = f"""
✨ Wᴇʟᴄᴏᴍᴇ {user_name}! ✨

Tʜɪs Is Tʜᴇ Mᴏsᴛ Aᴅᴠᴀɴᴄᴇᴅ SMM Bᴏᴛ Oɴ Tᴇʟᴇɢʀᴀᴍ! 🚀

Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ Fʀᴏᴍ Tʜᴇ Mᴇɴᴜ Bᴇʟᴏᴡ:
    """
    
    bot.send_photo(
        chat_id=user_id,
        photo="https://via.placeholder.com/400x200/0088cc/ffffff?text=Welcome+To+SMM+Bot",
        caption=welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "main_menu":
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                "https://via.placeholder.com/400x200/0088cc/ffffff?text=Main+Menu",
                caption="🏠 Mᴀɪɴ Mᴇɴᴜ - Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ:"
            ),
            reply_markup=main_menu_keyboard()
        )
    
    elif call.data == "deposit":
        handle_deposit(call)
    
    elif call.data == "order_menu":
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                "https://via.placeholder.com/400x200/28a745/ffffff?text=Order+Services",
                caption="🛒 Sᴇʟᴇᴄᴛ A Sᴇʀᴠɪᴄᴇ Cᴀᴛᴇɢᴏʀʏ:"
            ),
            reply_markup=service_category_keyboard()
        )
    
    elif call.data == "history":
        handle_history(call)
    
    elif call.data == "refer":
        handle_refer(call)
    
    elif call.data == "service_instagram":
        bot.edit_message_media(
            chat_id=user_id,
            message_id=message_id,
            media=telebot.types.InputMediaPhoto(
                "https://via.placeholder.com/400x200/E4405F/ffffff?text=Instagram+Services",
                caption="📷 Iɴsᴛᴀɢʀᴀᴍ Sᴇʀᴠɪᴄᴇs - Cʜᴏᴏsᴇ Oɴᴇ:"
            ),
            reply_markup=instagram_services_keyboard()
        )
    
    elif call.data.startswith("order_"):
        service_name = call.data.replace("order_", "")
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
            
            bot.edit_message_media(
                chat_id=user_id,
                message_id=message_id,
                media=telebot.types.InputMediaPhoto(
                    "https://via.placeholder.com/400x200/17a2b8/ffffff?text=Enter+Link",
                    caption=service_text
                )
            )
            
            bot.register_next_step_handler(call.message, process_order_link)
    
    elif call.data == "check_deposit":
        handle_deposit_check(call)

# Deposit handler
def handle_deposit(call):
    user_id = call.message.chat.id
    amount = 100  # Default amount
    
    # Generate UTR
    import random
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
    
    bot.edit_message_media(
        chat_id=user_id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            "https://via.placeholder.com/400x200/28a745/ffffff?text=Deposit+Instructions",
            caption=deposit_text
        ),
        reply_markup=markup
    )

# Deposit check handler
def handle_deposit_check(call):
    user_id = call.message.chat.id
    user_state = user_states.get(user_id, {})
    
    if user_state.get("action") == "deposit":
        amount = user_state.get("amount", 0)
        points_to_add = amount * 100  # 1 INR = 100 points
        
        # In real implementation, you'd verify payment here
        # For now, we'll simulate successful payment
        new_balance = update_user_balance(user_id, points_to_add)
        
        success_text = f"""
✅ Pᴀʏᴍᴇɴᴛ Sᴜᴄᴄᴇssғᴜʟ! ✅

💰 Aᴍᴏᴜɴᴛ Dᴇᴘᴏsɪᴛᴇᴅ: ₹{amount}
🎯 Pᴏɪɴᴛs Aᴅᴅᴇᴅ: {points_to_add}
🏦 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} Pᴏɪɴᴛs

Tʜᴀɴᴋ Yᴏᴜ Fᴏʀ Yᴏᴜʀ Dᴇᴘᴏsɪᴛ! 🎉
        """
        
        # Update user's total deposits
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"total_deposits": points_to_add}}
        )
        
        bot.edit_message_media(
            chat_id=user_id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                "https://via.placeholder.com/400x200/28a745/ffffff?text=Payment+Success",
                caption=success_text
            ),
            reply_markup=main_menu_keyboard()
        )
        
        # Notify admin
        try:
            bot.send_message(
                ADMIN_ID,
                f"💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ!\n\nUsᴇʀ: {user_id}\nAᴍᴏᴜɴᴛ: ₹{amount}\nPᴏɪɴᴛs: {points_to_add}"
            )
        except:
            pass

# History handler
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
📅 Dᴀᴛᴇ: {order['created_at'].strftime('%Y-%m-%d %H:%M')}
📊 Sᴛᴀᴛᴜs: {order['status']}
────────────────
            """
    
    bot.edit_message_media(
        chat_id=user_id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            "https://via.placeholder.com/400x200/6f42c1/ffffff?text=Order+History",
            caption=history_text
        ),
        reply_markup=main_menu_keyboard()
    )

# Refer handler
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
    markup.add(InlineKeyboardButton("📤 Sʜᴀʀᴇ Lɪɴᴋ", url=f"tg://msg_url?text={referral_link}"))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    
    bot.edit_message_media(
        chat_id=user_id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            "https://via.placeholder.com/400x200/ffc107/ffffff?text=Refer+Friends",
            caption=refer_text
        ),
        reply_markup=markup
    )

# Order processing
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
            
            # Place order via SMM API
            order_id = place_smm_order(service['service_id'], user_state["link"], quantity)
            
            if order_id:
                # Deduct balance
                new_balance = update_user_balance(user_id, -cost)
                
                # Save order to database
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
                
                bot.send_photo(
                    user_id,
                    photo="https://via.placeholder.com/400x200/28a745/ffffff?text=Order+Success",
                    caption=success_text,
                    reply_markup=main_menu_keyboard()
                )
                
                # Notify admin
                try:
                    bot.send_message(
                        ADMIN_ID,
                        f"🛒 Nᴇᴡ Oʀᴅᴇʀ!\n\nUsᴇʀ: {user_id}\nSᴇʀᴠɪᴄᴇ: {service['name']}\nQᴜᴀɴᴛɪᴛʏ: {quantity}\nOʀᴅᴇʀ ID: {order_id}"
                    )
                except:
                    pass
            else:
                bot.send_message(user_id, "❌ Fᴀɪʟᴇᴅ Tᴏ Pʟᴀᴄᴇ Oʀᴅᴇʀ! Pʟᴇᴀsᴇ Tʀʏ Aɢᴀɪɴ Lᴀᴛᴇʀ.")
        
        except ValueError:
            bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Qᴜᴀɴᴛɪᴛʏ! Pʟᴇᴀsᴇ Eɴᴛᴇʀ A Nᴜᴍʙᴇʀ.")

def place_smm_order(service_id, link, quantity):
    try:
        # Simulate API call - replace with actual SMM panel API
        import random
        order_id = f"ORD{random.randint(100000, 999999)}"
        return order_id
        
        # Actual API implementation would look like:
        # url = f"https://your-smm-panel.com/api/v2?key={SMM_API_KEY}&action=add&service={service_id}&link={link}&quantity={quantity}"
        # response = requests.get(url)
        # data = response.json()
        # return data.get('order')
    except:
        return None

# Admin commands
@bot.message_handler(commands=['adminox'])
def admin_login(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ!")
        return
    
    bot.send_message(
        message.chat.id,
        "🔐 Aᴅᴍɪɴ Lᴏɢɪɴ\n\nPʟᴇᴀsᴇ Eɴᴛᴇʀ Tʜᴇ Aᴅᴍɪɴ Pᴀssᴡᴏʀᴅ:"
    )
    bot.register_next_step_handler(message, process_admin_password)

def process_admin_password(message):
    if message.text == ADMIN_PASSWORD:
        admin_text = """
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ 👑

Wᴇʟᴄᴏᴍᴇ Bᴀᴄᴋ, Aᴅᴍɪɴ! 🎉

Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ Fʀᴏᴍ Tʜᴇ Mᴇɴᴜ Bᴇʟᴏᴡ:
        """
        
        bot.send_photo(
            message.chat.id,
            photo="https://via.placeholder.com/400x200/dc3545/ffffff?text=Admin+Panel",
            caption=admin_text,
            reply_markup=admin_keyboard()
        )
    else:
        bot.send_message(message.chat.id, "❌ Iɴᴄᴏʀʀᴇᴄᴛ Pᴀssᴡᴏʀᴅ!")

# My Account command
@bot.message_handler(commands=['account'])
def my_account(message):
    user_id = message.chat.id
    user = users_collection.find_one({"user_id": user_id})
    
    if not user:
        user = {
            "user_id": user_id,
            "balance": 0,
            "total_orders": 0,
            "total_deposits": 0
        }
        users_collection.insert_one(user)
    
    account_text = f"""
👤 Mʏ Aᴄᴄᴏᴜɴᴛ 👤

🏦 Aᴠᴀɪʟᴀʙʟᴇ Bᴀʟᴀɴᴄᴇ: {user.get('balance', 0)} Pᴏɪɴᴛs
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {user.get('total_orders', 0)} Pᴏɪɴᴛs
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: {user.get('total_deposits', 0)} Pᴏɪɴᴛs
📅 Mᴇᴍʙᴇʀ Sɪɴᴄᴇ: {user.get('joined_date', datetime.now()).strftime('%Y-%m-%d')}

Usᴇʀ ID: {user_id}
    """
    
    bot.send_photo(
        user_id,
        photo="https://via.placeholder.com/400x200/17a2b8/ffffff?text=My+Account",
        caption=account_text,
        reply_markup=main_menu_keyboard()
    )

# Statistics command
@bot.message_handler(commands=['stats'])
def bot_stats(message):
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    
    # Calculate total points in orders
    pipeline = [{"$group": {"_id": None, "total_points": {"$sum": "$cost"}}}]
    result = list(orders_collection.aggregate(pipeline))
    total_points = result[0]['total_points'] if result else 0
    
    stats_text = f"""
📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs 📊

👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
💰 Tᴏᴛᴀʟ Pᴏɪɴᴛs Sᴘᴇɴᴛ: {total_points}

🚀 Bᴏᴛ Is Rᴜɴɴɪɴɢ Sᴍᴏᴏᴛʜʟʏ!
    """
    
    bot.send_photo(
        message.chat.id,
        photo="https://via.placeholder.com/400x200/6f42c1/ffffff?text=Bot+Statistics",
        caption=stats_text
    )

# Support command
@bot.message_handler(commands=['support'])
def support(message):
    support_text = """
📞 Sᴜᴘᴘᴏʀᴛ & Hᴇʟᴘ 📞

Iғ Yᴏᴜ Hᴀᴠᴇ Aɴʏ Issᴜᴇs Oʀ Qᴜᴇsᴛɪᴏɴs, Cᴏɴᴛᴀᴄᴛ Oᴜʀ Sᴜᴘᴘᴏʀᴛ Tᴇᴀᴍ:

👤 Cᴜsᴛᴏᴍᴇʀ Sᴜᴘᴘᴏʀᴛ: @Username
📧 Eᴍᴀɪʟ: support@example.com
🌐 Wᴇʙsɪᴛᴇ: example.com

Wᴇ'ʀᴇ Hᴇʀᴇ Tᴏ Hᴇʟᴘ Yᴏᴜ 24/7! ⏰
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👤 Cᴏɴᴛᴀᴄᴛ Sᴜᴘᴘᴏʀᴛ", url="https://t.me/username"))
    
    bot.send_photo(
        message.chat.id,
        photo="https://via.placeholder.com/400x200/ffc107/ffffff?text=Support",
        caption=support_text,
        reply_markup=markup
    )

# Handle text messages
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.lower()
    
    if text in ['menu', 'start', 'home']:
        send_welcome(message)
    elif text in ['balance', 'account']:
        my_account(message)
    elif text in ['stats', 'statistics']:
        bot_stats(message)
    elif text in ['support', 'help']:
        support(message)
    else:
        bot.send_message(
            message.chat.id,
            "❓ I Dᴏɴ'ᴛ Uɴᴅᴇʀsᴛᴀɴᴅ Tʜᴀᴛ Cᴏᴍᴍᴀɴᴅ.\n\nUsᴇ /start Tᴏ Sᴇᴇ Tʜᴇ Mᴀɪɴ Mᴇɴᴜ."
        )

# Start the bot
if __name__ == "__main__":
    print("🤖 Bᴏᴛ Is Rᴜɴɴɪɴɢ...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ Eʀʀᴏʀ: {e}")
        time.sleep(15)
