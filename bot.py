import telebot
import requests
import json
import random
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from urllib.parse import quote

# Bot Configuration
BOT_TOKEN = "8052955693:AAGf3qd5VXfq1I7d0_lM0eE3YwKFuBXLxvw"
ADMIN_ID = 6052975324
CHANNEL_ID = -1002587  # Replace with your channel ID
PROOF_CHANNEL = "@your_proof_channel"  # Replace with your proof channel
SUPPORT_LINK = "https://t.me/your_support"  # Replace with your support

# API Keys
AUTODEP_API_KEY = "LY81vEV7"
AUTODEP_MERCHANT_KEY = "WYcmQI71591891985230"
SMM_API_KEY = "YOUR_SMM_API_KEY"  # Replace with your SMM API key

# Image URLs
WELCOME_IMAGE = "https://t.me/prooflelo1/135?single"
SERVICE_IMAGE = "https://t.me/prooflelo1/138?single"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/136?single"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/137?single"
HISTORY_IMAGE = "https://t.me/prooflelo1/139?single"
REFER_IMAGE = "https://t.me/prooflelo1/17"
ADMIN_IMAGE = "https://t.me/prooflelo1/140?single"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Storage (in production, use database)
user_data = {}
orders = {}
user_balances = {}
user_deposits = {}
user_spent = {}
user_states = {}
banned_users = set()
bot_enabled = True

# Services and Categories
services = {
    "instagram": {
        "name": "📸 Instagram",
        "services": {
            1: {"name": "📸 Instagram Likes", "rate": 50, "min": 100, "max": 100000, "unit": 1000},
            2: {"name": "👁 Instagram Views", "rate": 50, "min": 100, "max": 100000, "unit": 1000},
            3: {"name": "👤 Instagram Followers", "rate": 100, "min": 50, "max": 50000, "unit": 1000}
        }
    },
    "facebook": {
        "name": "📘 Facebook", 
        "services": {
            4: {"name": "👍 Facebook Likes", "rate": 40, "min": 100, "max": 100000, "unit": 1000},
            5: {"name": "👁 Facebook Views", "rate": 35, "min": 100, "max": 100000, "unit": 1000},
            6: {"name": "👥 Facebook Followers", "rate": 80, "min": 50, "max": 50000, "unit": 1000}
        }
    },
    "youtube": {
        "name": "📺 YouTube",
        "services": {
            7: {"name": "👍 YouTube Likes", "rate": 60, "min": 100, "max": 100000, "unit": 1000},
            8: {"name": "👁 YouTube Views", "rate": 45, "min": 100, "max": 100000, "unit": 1000},
            9: {"name": "🔔 YouTube Subscribers", "rate": 150, "min": 50, "max": 25000, "unit": 1000}
        }
    },
    "telegram": {
        "name": "📱 Telegram",
        "services": {
            10: {"name": "👥 Telegram Members", "rate": 200, "min": 50, "max": 10000, "unit": 1000},
            11: {"name": "👍 Telegram Post Likes", "rate": 80, "min": 100, "max": 50000, "unit": 1000},
            12: {"name": "👁 Telegram Post Views", "rate": 50, "min": 100, "max": 50000, "unit": 1000}
        }
    }
}

# Initialize user data
def init_user(user_id):
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
    if user_id not in user_deposits:
        user_deposits[user_id] = 0.0
    if user_id not in user_spent:
        user_spent[user_id] = 0.0
    if user_id not in orders:
        orders[user_id] = []

# Main Menu Keyboard
def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton("💰 Dᴇᴘᴏsɪᴛ", callback_data="deposit"),
        InlineKeyboardButton("🛒 Oʀᴅᴇʀ", callback_data="order"),
        InlineKeyboardButton("📋 Oʀᴅᴇʀs", callback_data="orders"),
        InlineKeyboardButton("👥 Rᴇғᴇʀ", callback_data="refer"),
        InlineKeyboardButton("👤 Aᴄᴄᴏᴜɴᴛ", callback_data="account"),
        InlineKeyboardButton("📊 Sᴛᴀᴛs", callback_data="stats"),
        InlineKeyboardButton("ℹ️ Sᴜᴘᴘᴏʀᴛ", callback_data="support")
    ]
    # Add buttons in rows of 3
    for i in range(0, len(buttons), 3):
        keyboard.add(*buttons[i:i+3])
    return keyboard

# Categories Keyboard
def categories_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📸 Instagram", callback_data="category_instagram"))
    keyboard.add(InlineKeyboardButton("📘 Facebook", callback_data="category_facebook"))
    keyboard.add(InlineKeyboardButton("📺 YouTube", callback_data="category_youtube"))
    keyboard.add(InlineKeyboardButton("📱 Telegram", callback_data="category_telegram"))
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="land"))
    return keyboard

# Admin Keyboard
def admin_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💰 Balance Control", callback_data="admin_balance"))
    keyboard.add(InlineKeyboardButton("✏️ Manage Prices", callback_data="admin_prices"))
    keyboard.add(InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"))
    keyboard.add(InlineKeyboardButton("👤 User Control", callback_data="admin_users"))
    keyboard.add(InlineKeyboardButton("⚙️ Bot Control", callback_data="admin_control"))
    keyboard.add(InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
    keyboard.add(InlineKeyboardButton("🔙 Main Menu", callback_data="land"))
    return keyboard

# Start Command
@bot.message_handler(commands=['start'])
def start_command(message):
    if not bot_enabled and message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Bot is currently under maintenance. Please try again later.")
        return
        
    if message.from_user.id in banned_users:
        bot.send_message(message.chat.id, "❌ You are banned from using this bot.")
        return
        
    init_user(message.from_user.id)
    
    caption = """
🛡️ 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗠𝗠 𝗕𝗢𝗧  🛡️

🌟 𝗬𝗼𝘂𝗿 𝗧𝗿𝘂𝘀𝘁𝗲𝗱 𝗦𝗠𝗠 𝗣𝗮𝗻𝗲𝗹 🌟

🔰 𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀:
✅ 𝗜𝗻𝘀𝘁𝗮𝗻𝘁 𝗦𝘁𝗮𝗿𝘁
✅ 𝗛𝗶𝗴𝗵 𝗤𝘂𝗮𝗹𝗶𝘁𝘆 𝗦𝗲𝗿𝘃𝗶𝗰𝗲𝘀
✅ 𝟮𝟰/𝟳 𝗦𝘂𝗽𝗽𝗼𝗿𝘁

💎 𝗦𝘁𝗮𝗿𝘁 𝗚𝗿𝗼𝘄𝗶𝗻𝗴 𝗬𝗼𝘂𝗿 𝗦𝗼𝗰𝗶𝗮𝗹 𝗠𝗲𝗱𝗶𝗮 𝗡𝗼𝘄! 💎
    """
    
    bot.send_photo(
        chat_id=message.chat.id,
        photo=WELCOME_IMAGE,
        caption=caption,
        reply_markup=main_menu_keyboard(),
        parse_mode='HTML'
    )

# Admin Command
@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Access denied.")
        return
        
    caption = """
👑 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 👑

⚡ 𝗙𝘂𝗹𝗹 𝗖𝗼𝗻𝘁𝗿𝗼𝗹 𝗢𝘃𝗲𝗿 𝗕𝗼𝘁 ⚡

📊 𝗠𝗮𝗻𝗮𝗴𝗲 𝗮𝗹𝗹 𝗯𝗼𝘁 𝗼𝗽𝗲𝗿𝗮𝘁𝗶𝗼𝗻𝘀 𝗳𝗿𝗼𝗺 𝗵𝗲𝗿𝗲
    """
    
    bot.send_photo(
        chat_id=message.chat.id,
        photo=ADMIN_IMAGE,
        caption=caption,
        reply_markup=admin_keyboard(),
        parse_mode='HTML'
    )

# Callback Query Handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if not bot_enabled and user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Bot is currently under maintenance.")
        return
        
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "❌ You are banned from using this bot.")
        return
        
    init_user(user_id)
    
    if call.data == "land":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_command(call.message)
        
    elif call.data == "deposit":
        show_deposit(call)
        
    elif call.data == "order":
        show_categories(call)
        
    elif call.data == "orders":
        show_orders(call)
        
    elif call.data == "refer":
        show_refer(call)
        
    elif call.data == "account":
        show_account(call)
        
    elif call.data == "stats":
        show_stats(call)
        
    elif call.data == "support":
        show_support(call)
        
    elif call.data.startswith("category_"):
        category = call.data.split("_")[1]
        show_services(call, category)
        
    elif call.data.startswith("service_"):
        service_id = int(call.data.split("_")[1])
        start_order(call, service_id)
        
    elif call.data == "check_txn":
        check_transaction(call)
        
    elif call.data == "admin_balance":
        admin_balance_control(call)
        
    elif call.data == "admin_prices":
        admin_manage_prices(call)
        
    elif call.data == "admin_broadcast":
        admin_broadcast(call)
        
    elif call.data == "admin_users":
        admin_user_control(call)
        
    elif call.data == "admin_control":
        admin_bot_control(call)
        
    elif call.data == "admin_stats":
        admin_stats(call)

# Deposit Flow
def show_deposit(call):
    caption = """
💰 𝗗𝗲𝗽𝗼𝘀𝗶𝘁 𝗙𝘂𝗻𝗱𝘀 💰

𝗘𝗻𝘁𝗲𝗿 𝗧𝗵𝗲 𝗔𝗺𝗼𝘂𝗻𝘁 𝗬𝗼𝘂 𝗪𝗮𝗻𝘁 𝗧𝗼 𝗗𝗲𝗽𝗼𝘀𝗶𝘁 💰

💡 𝗠𝗶𝗻𝗶𝗺𝘂𝗺 𝗗𝗲𝗽𝗼𝘀𝗶𝘁: ₹10
    """
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            media=DEPOSIT_IMAGE,
            caption=caption,
            parse_mode='HTML'
        ),
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="land")
        )
    )
    
    # Set user state to wait for deposit amount
    user_states[user_id] = "waiting_deposit_amount"

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_deposit_amount")
def handle_deposit_amount(message):
    user_id = message.from_user.id
    
    try:
        amount = float(message.text)
        
        if amount < 10:
            bot.send_message(user_id, "❌ Minimum deposit amount is ₹10")
            return
            
        # Generate random 12-digit UTR
        utr = str(random.randint(100000000000, 999999999999))
        
        # Save deposit data
        user_data[user_id] = {
            "deposit_utr": utr,
            "deposit_amount": amount
        }
        
        # Create UPI payment link
        upi_link = f"upi://pay?pa=paytm.s1m11be@pty&pn=Paytm&am={amount}&tn=Deposit&tr={utr}"
        
        # Generate QR code
        qr_url = f"https://quickchart.io/qr?text={quote(upi_link)}&size=300"
        
        caption = f"""
💳 𝗗𝗲𝗽𝗼𝘀𝗶𝘁 𝗥𝗲𝗾𝘂𝗲𝘀𝘁

💰 𝗔𝗺𝗼𝘂𝗻𝘁: ₹{amount}
🔢 𝗨𝗧𝗥: {utr}

📱 𝗦𝗰𝗮𝗻 𝘁𝗵𝗲 𝗤𝗥 𝗰𝗼𝗱𝗲 𝘁𝗼 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲 𝘆𝗼𝘂𝗿 𝗱𝗲𝗽𝗼𝘀𝗶𝘁
        """
        
        # Send QR code
        bot.send_photo(
            chat_id=user_id,
            photo=qr_url,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("𝗣𝗮𝗶𝗱 ✅", callback_data="check_txn")],
                [InlineKeyboardButton("Back 🔙", callback_data="land")]
            ]),
            parse_mode='HTML'
        )
        
        # Clear user state
        user_states[user_id] = None
        
    except ValueError:
        bot.send_message(user_id, "❌ Please enter a valid amount (numbers only)")

# Check Transaction
def check_transaction(call):
    user_id = call.from_user.id
    
    if user_id not in user_data or "deposit_utr" not in user_data[user_id]:
        bot.answer_callback_query(call.id, "❌ No pending deposit found.", show_alert=True)
        return
        
    utr = user_data[user_id]["deposit_utr"]
    amount = user_data[user_id]["deposit_amount"]
    
    try:
        # Check transaction via Autodep API
        url = f"https://erox-autodep-api.onrender.com/api?key={AUTODEP_API_KEY}&merchantkey={AUTODEP_MERCHANT_KEY}&transactionid={utr}"
        response = requests.get(url)
        data = response.json()
        
        if data.get("result", {}).get("STATUS") == "TXN_SUCCESS":
            # Update user balance
            user_balances[user_id] += amount
            user_deposits[user_id] += amount
            
            # Clear deposit data
            user_data[user_id].pop("deposit_utr", None)
            user_data[user_id].pop("deposit_amount", None)
            
            # Notify user
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=f"✅ 𝗧𝗿𝗮𝗻𝘀𝗮𝗰𝘁𝗶𝗼𝗻 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹!\n\n💰 ₹{amount} added to your balance\n💳 New Balance: ₹{user_balances[user_id]}",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 Main Menu", callback_data="land")
                )
            )
            
            # Notify admin
            bot.send_message(
                ADMIN_ID,
                f"✅ 𝗡𝗲𝘄 𝗗𝗲𝗽𝗼𝘀𝗶𝘁\n\n👤 User: {user_id}\n💰 Amount: ₹{amount}\n💳 Balance: ₹{user_balances[user_id]}"
            )
            
            # Notify channel if configured
            if CHANNEL_ID:
                bot.send_message(
                    CHANNEL_ID,
                    f"📢 𝗡𝗲𝘄 𝗗𝗲𝗽𝗼𝘀𝗶𝘁!\n\n👤 User {user_id} deposited ₹{amount} successfully!"
                )
                
        else:
            bot.answer_callback_query(
                call.id,
                "❌ You have not deposited yet. Please pay first.",
                show_alert=True
            )
            
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}", show_alert=True)

# Order Flow
def show_categories(call):
    caption = """
🛒 𝗦𝗲𝗿𝘃𝗶𝗰𝗲𝘀 𝗠𝗲𝗻𝘂

📊 𝗖𝗵𝗼𝗼𝘀𝗲 𝗮 𝗰𝗮𝘁𝗲𝗴𝗼𝗿𝘆 𝘁𝗼 𝘀𝘁𝗮𝗿𝘁 𝗼𝗿𝗱𝗲𝗿𝗶𝗻𝗴:
    """
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            media=SERVICE_IMAGE,
            caption=caption,
            parse_mode='HTML'
        ),
        reply_markup=categories_keyboard()
    )

def show_services(call, category):
    if category not in services:
        bot.answer_callback_query(call.id, "❌ Category not found")
        return
        
    category_data = services[category]
    keyboard = InlineKeyboardMarkup()
    
    for service_id, service in category_data["services"].items():
        keyboard.add(InlineKeyboardButton(
            f"{service['name']} - ₹{service['rate']}/{service['unit']}",
            callback_data=f"service_{service_id}"
        ))
    
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="order"))
    
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=f"📊 𝗦𝗲𝗿𝘃𝗶𝗰𝗲𝘀 - {category_data['name']}\n\nSelect a service to order:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

def start_order(call, service_id):
    user_id = call.from_user.id
    
    # Find service
    service = None
    category_name = None
    for cat_name, cat_data in services.items():
        if service_id in cat_data["services"]:
            service = cat_data["services"][service_id]
            category_name = cat_data["name"]
            break
    
    if not service:
        bot.answer_callback_query(call.id, "❌ Service not found")
        return
        
    # Save service selection
    user_data[user_id] = {
        "selected_service": service_id,
        "service_details": service
    }
    
    caption = f"""
🛒 𝗢𝗿𝗱𝗲𝗿 𝗗𝗲𝘁𝗮𝗶𝗹𝘀

📦 𝗦𝗲𝗿𝘃𝗶𝗰𝗲: {service['name']}
💰 𝗣𝗿𝗶𝗰𝗲: ₹{service['rate']}/{service['unit']}
📏 𝗠𝗶𝗻: {service['min']}
📏 𝗠𝗮𝘅: {service['max']}

🔗 𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗻𝗱 𝘁𝗵𝗲 𝗹𝗶𝗻𝗸:
    """
    
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data=f"category_{list(services.keys())[list(services.values()).index(next(c for c in services.values() if service_id in c['services']))]}")
        ),
        parse_mode='HTML'
    )
    
    user_states[user_id] = "waiting_order_link"

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_order_link")
def handle_order_link(message):
    user_id = message.from_user.id
    
    if user_id not in user_data or "selected_service" not in user_data[user_id]:
        bot.send_message(user_id, "❌ No service selected. Please start over.")
        user_states[user_id] = None
        return
        
    link = message.text
    user_data[user_id]["order_link"] = link
    
    service = user_data[user_id]["service_details"]
    
    bot.send_message(
        user_id,
        f"🔗 𝗟𝗶𝗻𝗸 𝗦𝗮𝘃𝗲𝗱: {link}\n\n📦 𝗡𝗼𝘄 𝗽𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗾𝘂𝗮𝗻𝘁𝗶𝘁𝘆:\n(Min: {service['min']}, Max: {service['max']})"
    )
    
    user_states[user_id] = "waiting_order_quantity"

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_order_quantity")
def handle_order_quantity(message):
    user_id = message.from_user.id
    
    if user_id not in user_data or "selected_service" not in user_data[user_id]:
        bot.send_message(user_id, "❌ No service selected. Please start over.")
        user_states[user_id] = None
        return
        
    try:
        quantity = int(message.text)
        service = user_data[user_id]["service_details"]
        link = user_data[user_id]["order_link"]
        
        # Validate quantity
        if quantity < service["min"] or quantity > service["max"]:
            bot.send_message(
                user_id,
                f"❌ Quantity must be between {service['min']} and {service['max']}"
            )
            return
            
        # Calculate cost
        cost = (quantity / service["unit"]) * service["rate"]
        
        # Check balance
        if user_balances[user_id] < cost:
            bot.send_message(
                user_id,
                f"❌ 𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗕𝗮𝗹𝗮𝗻𝗰𝗲\n\n💰 Required: ₹{cost:.2f}\n💳 Available: ₹{user_balances[user_id]:.2f}\n\nPlease deposit first."
            )
            user_states[user_id] = None
            return
            
        # Place order via SMM API
        order_result = place_smm_order(
            service_id=user_data[user_id]["selected_service"],
            link=link,
            quantity=quantity
        )
        
        if order_result["success"]:
            # Deduct balance
            user_balances[user_id] -= cost
            user_spent[user_id] += cost
            
            # Save order
            order_id = order_result["order_id"]
            orders[user_id].append({
                "order_id": order_id,
                "service": service["name"],
                "link": link,
                "quantity": quantity,
                "cost": cost,
                "status": "Pending",
                "timestamp": time.time()
            })
            
            # Confirm to user
            bot.send_message(
                user_id,
                f"✅ 𝗢𝗿𝗱𝗲𝗿 𝗣𝗹𝗮𝗰𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!\n\n"
                f"📦 𝗢𝗿𝗱𝗲𝗿 𝗜𝗗: {order_id}\n"
                f"💰 𝗔𝗺𝗼𝘂𝗻𝘁: ₹{cost:.2f}\n"
                f"💳 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: ₹{user_balances[user_id]:.2f}"
            )
            
            # Send to proof channel
            send_proof_message(user_id, service["name"], quantity, cost, order_id)
            
        else:
            bot.send_message(
                user_id,
                f"❌ 𝗢𝗿𝗱𝗲𝗿 𝗙𝗮𝗶𝗹𝗲𝗱\n\nError: {order_result['error']}"
            )
            
    except ValueError:
        bot.send_message(user_id, "❌ Please enter a valid number for quantity")
        return
        
    user_states[user_id] = None

def place_smm_order(service_id, link, quantity):
    try:
        # Mock SMM API call - replace with actual API
        params = {
            "key": SMM_API_KEY,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        
        # response = requests.get("YOUR_SMM_API_URL", params=params)
        # data = response.json()
        
        # Mock response for demonstration
        return {
            "success": True,
            "order_id": f"ORD{random.randint(100000, 999999)}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def send_proof_message(user_id, service_name, quantity, cost, order_id):
    proof_text = f"""
📦 𝗡𝗘𝗪 𝗢𝗥𝗗𝗘𝗥 𝗣𝗟𝗔𝗖𝗘𝗗! 📦

👤 𝗨𝘀𝗲𝗿: {user_id}
🛒 𝗦𝗲𝗿𝘃𝗶𝗰𝗲: {service_name}
🔢 𝗤𝘂𝗮𝗻𝘁𝗶𝘁𝘆: {quantity}
💰 𝗔𝗺𝗼𝘂𝗻𝘁: ₹{cost:.2f}
🆔 𝗢𝗿𝗱𝗲𝗿 𝗜𝗗: {order_id}

⏰ 𝗧𝗶𝗺𝗲: {time.strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    try:
        bot.send_message(
            PROOF_CHANNEL,
            proof_text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🤖 Bᴏᴛ Hᴇʀᴇ 🈴", url=f"https://t.me/{(bot.get_me()).username}")
            )
        )
    except:
        pass  # Ignore if proof channel not set up

# Other Menu Functions
def show_orders(call):
    user_id = call.from_user.id
    user_orders = orders.get(user_id, [])[-5:]  # Last 5 orders
    
    if not user_orders:
        caption = "📋 𝗡𝗼 𝗼𝗿𝗱𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱"
    else:
        caption = "📋 𝗟𝗮𝘀𝘁 𝟱 𝗢𝗿𝗱𝗲𝗿𝘀:\n\n"
        for order in reversed(user_orders):
            caption += f"🆔 {order['order_id']}\n"
            caption += f"📦 {order['service']}\n"
            caption += f"🔢 {order['quantity']}\n"
            caption += f"💰 ₹{order['cost']:.2f}\n"
            caption += f"📊 {order['status']}\n"
            caption += "─" * 20 + "\n"
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            media=HISTORY_IMAGE,
            caption=caption,
            parse_mode='HTML'
        ),
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="land")
        )
    )

def show_refer(call):
    user_id = call.from_user.id
    bot_username = (bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    caption = f"""
👥 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗦𝘆𝘀𝘁𝗲𝗺

🔗 𝗬𝗼𝘂𝗿 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗟𝗶𝗻𝗸:
{referral_link}

💰 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗕𝗼𝗻𝘂𝘀:
• 10% of your friend's first deposit
• Unlimited earnings

📢 𝗦𝗵𝗮𝗿𝗲 𝘁𝗵𝗶𝘀 𝗹𝗶𝗻𝗸 𝗮𝗻𝗱 𝗲𝗮𝗿𝗻 𝗺𝗼𝗿𝗲!
    """
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            media=REFER_IMAGE,
            caption=caption,
            parse_mode='HTML'
        ),
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="land")
        )
    )

def show_account(call):
    user_id = call.from_user.id
    init_user(user_id)
    
    caption = f"""
👤 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗜𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻

🆔 𝗨𝘀𝗲𝗿 𝗜𝗗: {user_id}
💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: ₹{user_balances[user_id]:.2f}
💳 𝗧𝗼𝘁𝗮𝗹 𝗗𝗲𝗽𝗼𝘀𝗶𝘁𝘀: ₹{user_deposits[user_id]:.2f}
📊 𝗧𝗼𝘁𝗮𝗹 𝗦𝗽𝗲𝗻𝘁: ₹{user_spent[user_id]:.2f}
🛒 𝗧𝗼𝘁𝗮𝗹 𝗢𝗿𝗱𝗲𝗿𝘀: {len(orders.get(user_id, []))}
    """
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(
            media=ACCOUNT_IMAGE,
            caption=caption,
            parse_mode='HTML'
        ),
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="land")
        )
    )

def show_stats(call):
    user_id = call.from_user.id
    
    total_users = len(user_balances)
    total_orders = sum(len(user_orders) for user_orders in orders.values())
    total_deposits = sum(user_deposits.values())
    total_spent = sum(user_spent.values())
    
    caption = f"""
📊 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗰𝘀

👥 𝗧𝗼𝘁𝗮𝗹 𝗨𝘀𝗲𝗿𝘀: {total_users}
🛒 𝗧𝗼𝘁𝗮𝗹 𝗢𝗿𝗱𝗲𝗿𝘀: {total_orders}
💰 𝗧𝗼𝘁𝗮𝗹 𝗗𝗲𝗽𝗼𝘀𝗶𝘁𝘀: ₹{total_deposits:.2f}
📊 𝗧𝗼𝘁𝗮𝗹 𝗦𝗽𝗲𝗻𝘁: ₹{total_spent:.2f}

⚡ 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘂𝘀: {'🟢 Online' if bot_enabled else '🔴 Offline'}
    """
    
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="land")
        ),
        parse_mode='HTML'
    )

def show_support(call):
    caption = """
ℹ️ 𝗦𝘂𝗽𝗽𝗼𝗿𝘁

📞 𝗡𝗲𝗲𝗱 𝗵𝗲𝗹𝗽? 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗼𝘂𝗿 𝘀𝘂𝗽𝗽𝗼𝗿𝘁 𝘁𝗲𝗮𝗺:

🕒 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝟮𝟰/𝟳
📧 𝗤𝘂𝗶𝗰𝗸 𝗿𝗲𝘀𝗽𝗼𝗻𝘀𝗲𝘀
🔧 𝗧𝗲𝗰𝗵𝗻𝗶𝗰𝗮𝗹 𝘀𝘂𝗽𝗽𝗼𝗿𝘁
    """
    
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Contact Support", url=SUPPORT_LINK)],
            [InlineKeyboardButton("🔙 Back", callback_data="land")]
        ]),
        parse_mode='HTML'
    )

# Admin Functions
def admin_balance_control(call):
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption="💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 𝗖𝗼𝗻𝘁𝗿𝗼𝗹\n\nUse commands:\n/addbalance user_id amount\n/deductbalance user_id amount",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="admin")
        ),
        parse_mode='HTML'
    )

def admin_manage_prices(call):
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption="✏️ 𝗠𝗮𝗻𝗮𝗴𝗲 𝗣𝗿𝗶𝗰𝗲𝘀\n\nPrice management interface coming soon...",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="admin")
        ),
        parse_mode='HTML'
    )

def admin_broadcast(call):
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption="📢 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁\n\nUse command:\n/broadcast your_message_here",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="admin")
        ),
        parse_mode='HTML'
    )

def admin_user_control(call):
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption="👤 𝗨𝘀𝗲𝗿 𝗖𝗼𝗻𝘁𝗿𝗼𝗹\n\nUse commands:\n/ban user_id\n/unban user_id",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="admin")
        ),
        parse_mode='HTML'
    )

def admin_bot_control(call):
    status = "🟢 ENABLED" if bot_enabled else "🔴 DISABLED"
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=f"⚙️ 𝗕𝗼𝘁 𝗖𝗼𝗻𝘁𝗿𝗼𝗹\n\nCurrent Status: {status}\n\nUse commands:\n/enablebot\n/disablebot",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="admin")
        ),
        parse_mode='HTML'
    )

def admin_stats(call):
    total_users = len(user_balances)
    total_orders = sum(len(user_orders) for user_orders in orders.values())
    total_deposits = sum(user_deposits.values())
    total_spent = sum(user_spent.values())
    
    caption = f"""
📊 𝗔𝗱𝗺𝗶𝗻 𝗦𝘁𝗮𝘁𝘀

👥 𝗧𝗼𝘁𝗮𝗹 𝗨𝘀𝗲𝗿𝘀: {total_users}
🛒 𝗧𝗼𝘁𝗮𝗹 𝗢𝗿𝗱𝗲𝗿𝘀: {total_orders}
💰 𝗧𝗼𝘁𝗮𝗹 𝗗𝗲𝗽𝗼𝘀𝗶𝘁𝘀: ₹{total_deposits:.2f}
📊 𝗧𝗼𝘁𝗮𝗹 𝗦𝗽𝗲𝗻𝘁: ₹{total_spent:.2f}
🔨 𝗕𝗮𝗻𝗻𝗲𝗱 𝗨𝘀𝗲𝗿𝘀: {len(banned_users)}
⚡ 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘂𝘀: {'🟢 Online' if bot_enabled else '🔴 Offline'}
    """
    
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Back", callback_data="admin")
        ),
        parse_mode='HTML'
    )

# Admin Commands
@bot.message_handler(commands=['addbalance'])
def add_balance_command(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        _, user_id, amount = message.text.split()
        user_id = int(user_id)
        amount = float(amount)
        
        init_user(user_id)
        user_balances[user_id] += amount
        
        bot.send_message(
            message.chat.id,
            f"✅ Balance added!\nUser: {user_id}\nAmount: ₹{amount}\nNew Balance: ₹{user_balances[user_id]}"
        )
        
    except:
        bot.send_message(message.chat.id, "❌ Usage: /addbalance user_id amount")

@bot.message_handler(commands=['deductbalance'])
def deduct_balance_command(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        _, user_id, amount = message.text.split()
        user_id = int(user_id)
        amount = float(amount)
        
        init_user(user_id)
        user_balances[user_id] -= amount
        
        bot.send_message(
            message.chat.id,
            f"✅ Balance deducted!\nUser: {user_id}\nAmount: ₹{amount}\nNew Balance: ₹{user_balances[user_id]}"
        )
        
    except:
        bot.send_message(message.chat.id, "❌ Usage: /deductbalance user_id amount")

@bot.message_handler(commands=['ban'])
def ban_user_command(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        _, user_id = message.text.split()
        user_id = int(user_id)
        
        banned_users.add(user_id)
        bot.send_message(message.chat.id, f"✅ User {user_id} banned")
        
    except:
        bot.send_message(message.chat.id, "❌ Usage: /ban user_id")

@bot.message_handler(commands=['unban'])
def unban_user_command(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        _, user_id = message.text.split()
        user_id = int(user_id)
        
        banned_users.discard(user_id)
        bot.send_message(message.chat.id, f"✅ User {user_id} unbanned")
        
    except:
        bot.send_message(message.chat.id, "❌ Usage: /unban user_id")

@bot.message_handler(commands=['enablebot'])
def enable_bot_command(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    global bot_enabled
    bot_enabled = True
    bot.send_message(message.chat.id, "✅ Bot enabled")

@bot.message_handler(commands=['disablebot'])
def disable_bot_command(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    global bot_enabled
    bot_enabled = False
    bot.send_message(message.chat.id, "✅ Bot disabled")

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        broadcast_text = message.text.split(' ', 1)[1]
        sent = 0
        failed = 0
        
        for user_id in user_balances:
            try:
                bot.send_message(user_id, f"📢 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁:\n\n{broadcast_text}")
                sent += 1
            except:
                failed += 1
                
        bot.send_message(
            message.chat.id,
            f"✅ Broadcast completed!\nSent: {sent}\nFailed: {failed}"
        )
        
    except:
        bot.send_message(message.chat.id, "❌ Usage: /broadcast your_message")

# Start polling
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.polling(none_stop=True)
