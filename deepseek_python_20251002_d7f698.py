import telebot
from telebot import types
import requests
import json
import random
import time
import sqlite3
import threading
from urllib.parse import quote

# Bot configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_IDS = [123456789]  # Replace with your admin ID
PROOF_CHANNEL = "@your_proof_channel"  # Replace with your channel
SUPPORT_LINK = "https://t.me/your_support"  # Replace with your support
BOT_LINK = "https://t.me/your_bot"  # Replace with your bot link

# API Keys
AUTODEP_API_KEY = "YOUR_AUTODEP_API_KEY"
AUTODEP_MERCHANT_KEY = "YOUR_MERCHANT_KEY"
SMM_API_KEY = "YOUR_SMM_API_KEY"
SMM_API_URL = "https://example.com/api/v2"  # Replace with actual SMM API

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Database setup
def init_db():
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0, 
                     total_deposits REAL DEFAULT 0, total_spent REAL DEFAULT 0, 
                     banned INTEGER DEFAULT 0, joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Orders table
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders
                     (order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
                     service_name TEXT, link TEXT, quantity INTEGER, cost REAL,
                     status TEXT DEFAULT 'Pending', order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     api_order_id TEXT)''')
    
    # Deposits table
    cursor.execute('''CREATE TABLE IF NOT EXISTS deposits
                     (deposit_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                     amount REAL, utr TEXT, status TEXT DEFAULT 'Pending',
                     deposit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Settings table
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                     (key TEXT PRIMARY KEY, value TEXT)''')
    
    # Insert default settings
    cursor.execute('''INSERT OR IGNORE INTO settings (key, value) VALUES 
                     ('bot_status', 'on'), ('referral_bonus', '10')''')
    
    conn.commit()
    conn.close()

init_db()

# Image URLs
WELCOME_IMAGE = "https://t.me/prooflelo1/135?single"
SERVICE_IMAGE = "https://t.me/prooflelo1/138?single"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/136?single"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/137?single"
HISTORY_IMAGE = "https://t.me/prooflelo1/139?single"
REFER_IMAGE = "https://t.me/prooflelo1/17"
ADMIN_IMAGE = "https://t.me/prooflelo1/140?single"

# Services data (categories and services)
SERVICES = {
    "Instagram": {
        "📸 Instagram Likes": {"id": 101, "price": 30, "min": 100, "max": 10000, "unit": 1000},
        "👁 Instagram Views": {"id": 102, "price": 50, "min": 100, "max": 50000, "unit": 1000},
        "👤 Instagram Followers": {"id": 103, "price": 80, "min": 100, "max": 10000, "unit": 1000}
    },
    "Facebook": {
        "👍 Facebook Likes": {"id": 201, "price": 40, "min": 100, "max": 20000, "unit": 1000},
        "👁 Facebook Views": {"id": 202, "price": 60, "min": 100, "max": 50000, "unit": 1000},
        "👥 Facebook Followers": {"id": 203, "price": 90, "min": 100, "max": 15000, "unit": 1000}
    },
    "YouTube": {
        "👍 YouTube Likes": {"id": 301, "price": 35, "min": 100, "max": 50000, "unit": 1000},
        "👁 YouTube Views": {"id": 302, "price": 45, "min": 100, "max": 100000, "unit": 1000},
        "🔔 YouTube Subscribers": {"id": 303, "price": 120, "min": 100, "max": 10000, "unit": 1000}
    },
    "Telegram": {
        "👥 Telegram Members": {"id": 401, "price": 25, "min": 100, "max": 50000, "unit": 1000},
        "👍 Telegram Post Likes": {"id": 402, "price": 20, "min": 100, "max": 100000, "unit": 1000},
        "👁 Telegram Post Views": {"id": 403, "price": 15, "min": 100, "max": 100000, "unit": 1000}
    }
}

# User session data
user_sessions = {}

# Database helper functions
def get_user(user_id):
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(user_id, username):
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    if amount > 0:
        cursor.execute("UPDATE users SET total_deposits = total_deposits + ? WHERE user_id = ?", (amount, user_id))
    else:
        cursor.execute("UPDATE users SET total_spent = total_spent + ? WHERE user_id = ?", (abs(amount), user_id))
    conn.commit()
    conn.close()

def get_balance(user_id):
    user = get_user(user_id)
    return user[2] if user else 0

def add_order(user_id, service_name, link, quantity, cost, api_order_id):
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO orders (user_id, service_name, link, quantity, cost, api_order_id)
                     VALUES (?, ?, ?, ?, ?, ?)''', (user_id, service_name, link, quantity, cost, api_order_id))
    conn.commit()
    conn.close()

def get_user_orders(user_id, limit=5):
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM orders WHERE user_id = ? ORDER BY order_date DESC LIMIT ?''', (user_id, limit))
    orders = cursor.fetchall()
    conn.close()
    return orders

def add_deposit(user_id, amount, utr):
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO deposits (user_id, amount, utr) VALUES (?, ?, ?)''', (user_id, amount, utr))
    conn.commit()
    conn.close()

def update_deposit_status(utr, status):
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE deposits SET status = ? WHERE utr = ?", (status, utr))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_orders():
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_deposits():
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM deposits WHERE status = 'Completed'")
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_total_spent():
    conn = sqlite3.connect('smm_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(cost) FROM orders")
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

# Keyboard helpers
def main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("💰 Dᴇᴘᴏsɪᴛ", callback_data="deposit"),
        types.InlineKeyboardButton("🛒 Oʀᴅᴇʀ", callback_data="order"),
        types.InlineKeyboardButton("📋 Oʀᴅᴇʀs", callback_data="orders"),
        types.InlineKeyboardButton("👥 Rᴇғᴇʀ", callback_data="refer"),
        types.InlineKeyboardButton("👤 Aᴄᴄᴏᴜɴᴛ", callback_data="account"),
        types.InlineKeyboardButton("📊 Sᴛᴀᴛs", callback_data="stats"),
        types.InlineKeyboardButton("ℹ️ Sᴜᴘᴘᴏʀᴛ", callback_data="support")
    ]
    keyboard.add(*buttons)
    return keyboard

def categories_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for category in SERVICES.keys():
        emoji = "📸" if category == "Instagram" else "👍" if category == "Facebook" else "📺" if category == "YouTube" else "📱"
        buttons.append(types.InlineKeyboardButton(f"{emoji} {category}", callback_data=f"cat_{category}"))
    
    keyboard.add(*buttons)
    keyboard.add(types.InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land"))
    return keyboard

def services_keyboard(category):
    keyboard = types.InlineKeyboardMarkup()
    for service_name in SERVICES[category].keys():
        keyboard.add(types.InlineKeyboardButton(service_name, callback_data=f"serv_{category}_{service_name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="order"))
    return keyboard

def admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("💰 Balance Control", callback_data="admin_balance"),
        types.InlineKeyboardButton("✏️ Manage Prices", callback_data="admin_prices"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("👤 User Control", callback_data="admin_users"),
        types.InlineKeyboardButton("⚙️ Bot Control", callback_data="admin_control"),
        types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("🔙 Main Menu", callback_data="land")
    ]
    keyboard.add(*buttons)
    return keyboard

# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    
    create_user(user_id, username)
    
    welcome_text = f"""
✨ 𝕎𝔼𝕃ℂ𝕆𝕄𝔼 𝕋𝕆 𝕊𝕄𝕄 𝔹𝕆𝕋 ✨

🚀 𝔹𝕦𝕪 𝕊𝕠𝕔𝕚𝕒𝕝 𝕄𝕖𝕕𝕚𝕒 𝕊𝕖𝕣𝕧𝕚𝕔𝕖𝕤 𝕒𝕥 ℂ𝕙𝕖𝕒𝕡𝕖𝕤𝕥 ℝ𝕒𝕥𝕖𝕤!

📊 𝕀𝕟𝕤𝕥𝕒𝕘𝕣𝕒𝕞, 𝔽𝕒𝕔𝕖𝕓𝕠𝕠𝕜, 𝕐𝕠𝕦𝕋𝕦𝕓𝕖 & 𝕋𝕖𝕝𝕖𝕘𝕣𝕒𝕞 𝕊𝕖𝕣𝕧𝕚𝕔𝕖𝕤
💎 ℍ𝕚𝕘𝕙 ℚ𝕦𝕒𝕝𝕚𝕥𝕪 & 𝔽𝕒𝕤𝕥 𝔻𝕖𝕝𝕚𝕧𝕖𝕣𝕪
🔒 𝕊𝕖𝕔𝕦𝕣𝕖 ℙ𝕒𝕪𝕞𝕖𝕟𝕥𝕤 & 𝟚𝟜/𝟟 𝕊𝕦𝕡𝕡𝕠𝕣𝕥

💫 𝕊𝕥𝕒𝕣𝕥 𝕓𝕪 𝕕𝕖𝕡𝕠𝕤𝕚𝕥𝕚𝕟𝕘 𝕗𝕦𝕟𝕕𝕤 𝕠𝕣 𝕡𝕝𝕒𝕔𝕚𝕟𝕘 𝕒𝕟 𝕠𝕣𝕕𝕖𝕣!
    """
    
    bot.send_photo(
        chat_id=user_id,
        photo=WELCOME_IMAGE,
        caption=welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='HTML'
    )

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    if call.data == "land":
        bot.delete_message(user_id, message_id)
        start_command(call.message)
    
    elif call.data == "deposit":
        show_deposit_menu(user_id, message_id)
    
    elif call.data == "order":
        show_categories(user_id, message_id)
    
    elif call.data == "orders":
        show_orders(user_id, message_id)
    
    elif call.data == "refer":
        show_refer(user_id, message_id)
    
    elif call.data == "account":
        show_account(user_id, message_id)
    
    elif call.data == "stats":
        show_stats(user_id, message_id)
    
    elif call.data == "support":
        show_support(user_id, message_id)
    
    elif call.data.startswith("cat_"):
        category = call.data[4:]
        show_services(user_id, message_id, category)
    
    elif call.data.startswith("serv_"):
        parts = call.data.split("_")
        category = parts[1]
        service_name = "_".join(parts[2:])
        start_order_flow(user_id, message_id, category, service_name)
    
    elif call.data == "check_txn":
        check_transaction(user_id, message_id)
    
    elif call.data == "admin":
        if user_id in ADMIN_IDS:
            show_admin_panel(user_id, message_id)
    
    elif call.data.startswith("admin_"):
        if user_id in ADMIN_IDS:
            handle_admin_commands(call)

# Deposit flow
def show_deposit_menu(user_id, message_id):
    deposit_text = "𝗘𝗻𝘁𝗲𝗿 𝗧𝗵𝗲 𝗔𝗺𝗼𝘂𝗻𝘁 𝗬𝗼𝘂 𝗪𝗮𝗻𝘁 𝗧𝗼 𝗗𝗲𝗽𝗼𝘀𝗶𝘁 💰"
    
    bot.edit_message_media(
        chat_id=user_id,
        message_id=message_id,
        media=types.InputMediaPhoto(
            media=DEPOSIT_IMAGE,
            caption=deposit_text
        ),
        reply_markup=None
    )
    
    bot.send_message(user_id, "💳 Please enter the amount you want to deposit (in ₹):")
    bot.register_next_step_handler_by_chat_id(user_id, process_deposit_amount)

def process_deposit_amount(message):
    user_id = message.from_user.id
    
    try:
        amount = float(message.text)
        if amount <= 0:
            bot.send_message(user_id, "❌ Please enter a valid amount greater than 0.")
            return
        
        # Generate random 12-digit UTR
        utr = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        
        # Create UPI link
        upi_link = f"upi://pay?pa=paytm.s1m11be@pty&pn=Paytm&am={amount}&tn=Deposit&tr={utr}"
        
        # Generate QR code
        qr_url = f"https://quickchart.io/qr?text={quote(upi_link)}&size=300"
        
        # Store deposit info
        add_deposit(user_id, amount, utr)
        user_sessions[user_id] = {"utr": utr, "amount": amount}
        
        # Create payment keyboard
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("𝗣𝗮𝗶𝗱 ✅", callback_data="check_txn"),
            types.InlineKeyboardButton("Back 🔙", callback_data="land")
        )
        
        payment_text = f"""
💰 *Payment Details*

💵 Amount: ₹{amount}
🔢 UTR: `{utr}`
        
📲 Scan the QR code or use the UPI ID below:

💳 UPI ID: `paytm.s1m11be@pty`

⏰ Please complete payment within 30 minutes.
        """
        
        bot.send_photo(
            chat_id=user_id,
            photo=qr_url,
            caption=payment_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except ValueError:
        bot.send_message(user_id, "❌ Please enter a valid number.")
        show_deposit_menu(user_id, message.message_id)

def check_transaction(user_id, message_id):
    if user_id not in user_sessions:
        bot.answer_callback_query(message_id, "❌ No pending transaction found.", show_alert=True)
        return
    
    utr = user_sessions[user_id]["utr"]
    amount = user_sessions[user_id]["amount"]
    
    # Simulate API check (replace with actual Autodep API)
    try:
        # This is a simulation - replace with actual API call
        # response = requests.get(f"https://erox-autodep-api.onrender.com/api?key={AUTODEP_API_KEY}&merchantkey={AUTODEP_MERCHANT_KEY}&transactionid={utr}")
        # api_response = response.json()
        
        # Simulate successful transaction for demo
        api_response = {"STATUS": "TXN_SUCCESS"}
        
        if api_response.get("STATUS") == "TXN_SUCCESS":
            # Update balance
            update_balance(user_id, amount)
            update_deposit_status(utr, "Completed")
            
            balance = get_balance(user_id)
            
            # Notify user
            success_text = f"✅ Transaction successful! ₹{amount} added. New Balance: ₹{balance}"
            bot.send_message(user_id, success_text)
            
            # Notify admin
            admin_text = f"💰 User {user_id} deposited ₹{amount}. Balance: ₹{balance}"
            for admin_id in ADMIN_IDS:
                bot.send_message(admin_id, admin_text)
            
            # Notify channel
            channel_text = f"📢 User {user_id} deposited ₹{amount} successfully!"
            try:
                bot.send_message(PROOF_CHANNEL, channel_text)
            except:
                pass
            
            # Clear session
            del user_sessions[user_id]
            
            # Show main menu
            start_command(bot.send_message(user_id, "🎉 Deposit successful!"))
            
        else:
            bot.answer_callback_query(message_id, "❌ You have not deposited yet. Please pay first.", show_alert=True)
            
    except Exception as e:
        bot.answer_callback_query(message_id, f"❌ Error checking transaction: {str(e)}", show_alert=True)

# Order flow
def show_categories(user_id, message_id):
    bot.edit_message_media(
        chat_id=user_id,
        message_id=message_id,
        media=types.InputMediaPhoto(
            media=SERVICE_IMAGE,
            caption="🎯 *Select a Category*"
        ),
        reply_markup=categories_keyboard(),
        parse_mode='Markdown'
    )

def show_services(user_id, message_id, category):
    bot.edit_message_media(
        chat_id=user_id,
        message_id=message_id,
        media=types.InputMediaPhoto(
            media=SERVICE_IMAGE,
            caption=f"🛍️ *{category} Services*\n\nSelect a service to continue:"
        ),
        reply_markup=services_keyboard(category),
        parse_mode='Markdown'
    )

def start_order_flow(user_id, message_id, category, service_name):
    service = SERVICES[category][service_name]
    
    service_info = f"""
{service_name}

💰 Price: ₹{service['price']}/1000
📦 Min: {service['min']}
📈 Max: {service['max']}

🔗 Please send the link for your order:
    """
    
    bot.edit_message_caption(
        chat_id=user_id,
        message_id=message_id,
        caption=service_info,
        reply_markup=None
    )
    
    # Store service info in session
    user_sessions[user_id] = {
        "category": category,
        "service_name": service_name,
        "service_data": service
    }
    
    bot.send_message(user_id, "🔗 Please enter the link:")
    bot.register_next_step_handler_by_chat_id(user_id, process_order_link)

def process_order_link(message):
    user_id = message.from_user.id
    link = message.text.strip()
    
    if user_id not in user_sessions:
        bot.send_message(user_id, "❌ Session expired. Please start over.")
        return
    
    user_sessions[user_id]["link"] = link
    
    service = user_sessions[user_id]["service_data"]
    service_name = user_sessions[user_id]["service_name"]
    
    bot.send_message(
        user_id,
        f"🔢 *Enter Quantity*\n\nService: {service_name}\nLink: {link}\n\nMin: {service['min']}\nMax: {service['max']}\n\nPlease enter quantity:",
        parse_mode='Markdown'
    )
    
    bot.register_next_step_handler_by_chat_id(user_id, process_order_quantity)

def process_order_quantity(message):
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        bot.send_message(user_id, "❌ Session expired. Please start over.")
        return
    
    try:
        quantity = int(message.text)
        service = user_sessions[user_id]["service_data"]
        service_name = user_sessions[user_id]["service_name"]
        link = user_sessions[user_id]["link"]
        
        # Validate quantity
        if quantity < service['min'] or quantity > service['max']:
            bot.send_message(
                user_id,
                f"❌ Quantity must be between {service['min']} and {service['max']}. Please try again."
            )
            return
        
        # Calculate cost
        cost = (quantity / service['unit']) * service['price']
        
        # Check balance
        balance = get_balance(user_id)
        if balance < cost:
            bot.send_message(
                user_id,
                f"❌ Insufficient Balance\n\nRequired: ₹{cost:.2f}\nYour Balance: ₹{balance:.2f}\n\nPlease deposit first."
            )
            return
        
        # Place order via SMM API
        try:
            # This is a simulation - replace with actual API call
            # params = {
            #     "key": SMM_API_KEY,
            #     "action": "add",
            #     "service": service['id'],
            #     "link": link,
            #     "quantity": quantity
            # }
            # response = requests.get(SMM_API_URL, params=params)
            # api_response = response.json()
            
            # Simulate API response
            api_response = {"order": "123456"}
            api_order_id = api_response.get("order", "SIMULATED_ORDER")
            
            # Deduct balance and save order
            update_balance(user_id, -cost)
            add_order(user_id, service_name, link, quantity, cost, api_order_id)
            
            # Get updated balance
            new_balance = get_balance(user_id)
            
            # Confirm to user
            confirmation_text = f"""
✅ *Order Placed Successfully!*

📦 Service: {service_name}
🔗 Link: {link}
🔢 Quantity: {quantity}
💰 Cost: ₹{cost:.2f}
🆔 Order ID: {api_order_id}
💳 Balance: ₹{new_balance:.2f}

📊 You can check order status in Orders menu.
            """
            
            bot.send_message(user_id, confirmation_text, parse_mode='Markdown')
            
            # Send to proof channel
            proof_text = f"""
🎉 *New Order Placed!*

👤 User: @{message.from_user.username or user_id}
📦 Service: {service_name}
🔢 Quantity: {quantity}
💰 Amount: ₹{cost:.2f}
🆔 Order ID: {api_order_id}

🤖 [Bᴏᴛ Hᴇʀᴇ 🈴]({BOT_LINK})
            """
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("🤖 Bᴏᴛ Hᴇʀᴇ 🈴", url=BOT_LINK))
            
            try:
                bot.send_message(
                    PROOF_CHANNEL,
                    proof_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            except:
                pass
            
            # Clear session
            del user_sessions[user_id]
            
        except Exception as e:
            bot.send_message(user_id, f"❌ Error placing order: {str(e)}")
            
    except ValueError:
        bot.send_message(user_id, "❌ Please enter a valid number.")

# Other user menus
def show_orders(user_id, message_id):
    orders = get_user_orders(user_id)
    
    if not orders:
        orders_text = "📭 No orders found."
    else:
        orders_text = "📋 *Your Last 5 Orders*\n\n"
        for order in orders[:5]:
            status_emoji = {
                'Pending': '⏳',
                'In Progress': '🔄', 
                'Completed': '✅',
                'Cancelled': '❌'
            }.get(order[6], '⏳')
            
            orders_text += f"""
{status_emoji} *Order #{order[0]}*
📦 {order[2]}
🔗 {order[3][:30]}...
🔢 Qty: {order[4]}
💰 ₹{order[5]:.2f}
🕒 {order[7]}
Status: {order[6]}

"""
    
    bot.edit_message_media(
        chat_id=user_id,
        message_id=message_id,
        media=types.InputMediaPhoto(
            media=HISTORY_IMAGE,
            caption=orders_text
        ),
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land")
        ),
        parse_mode='Markdown'
    )

def show_refer(user_id, message_id):
    refer_link = f"https://t.me/share/url?url={BOT_LINK}&text=Join%20this%20awesome%20SMM%20bot!"
    bonus = 10  # Get from settings
    
    refer_text = f"""
👥 *Referral Program*

🔗 Your Referral Link:
`{refer_link}`

💰 Referral Bonus: ₹{bonus} per successful referral

📊 How it works:
1. Share your referral link
2. When someone joins using your link
3. You get ₹{bonus} bonus when they deposit

🎁 Start referring and earn more!
    """
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📤 Share Link", url=f"tg://msg_url?url={quote(refer_link)}&text=Check%20this%20bot!"))
    keyboard.add(types.InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land"))
    
    bot.edit_message_media(
        chat_id=user_id,
        message_id=message_id,
        media=types.InputMediaPhoto(
            media=REFER_IMAGE,
            caption=refer_text
        ),
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

def show_account(user_id, message_id):
    user = get_user(user_id)
    if not user:
        create_user(user_id, f"User_{user_id}")
        user = get_user(user_id)
    
    account_text = f"""
👤 *Account Information*

🆔 User ID: `{user[0]}`
👤 Username: @{user[1] or 'N/A'}
💰 Balance: ₹{user[2]:.2f}
📥 Total Deposits: ₹{user[3]:.2f}
📤 Total Spent: ₹{user[4]:.2f}
📅 Member Since: {user[6]}
    """
    
    bot.edit_message_media(
        chat_id=user_id,
        message_id=message_id,
        media=types.InputMediaPhoto(
            media=ACCOUNT_IMAGE,
            caption=account_text
        ),
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land")
        ),
        parse_mode='Markdown'
    )

def show_stats(user_id, message_id):
    total_users = get_all_users()
    total_orders = get_total_orders()
    total_deposits = get_total_deposits()
    total_spent = get_total_spent()
    
    stats_text = f"""
📊 *Bot Statistics*

👥 Total Users: {total_users}
📦 Total Orders: {total_orders}
💰 Total Deposits: ₹{total_deposits:.2f}
💸 Total Spent: ₹{total_spent:.2f}

🚀 Growing strong every day!
    """
    
    bot.edit_message_media(
        chat_id=user_id,
        message_id=message_id,
        media=types.InputMediaPhoto(
            media=HISTORY_IMAGE,  # Using history image for stats
            caption=stats_text
        ),
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land")
        ),
        parse_mode='Markdown'
    )

def show_support(user_id, message_id):
    support_text = f"""
ℹ️ *Support*

📞 Need help? Contact our support team:

{SUPPORT_LINK}

🕒 Available 24/7
🔒 Quick response guaranteed
💬 We're here to help you!

⚠️ Only contact support for genuine issues.
    """
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📞 Contact Support", url=SUPPORT_LINK))
    keyboard.add(types.InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="land"))
    
    bot.edit_message_media(
        chat_id=user_id,
        message_id=message_id,
        media=types.InputMediaPhoto(
            media=HISTORY_IMAGE,  # Using history image for support
            caption=support_text
        ),
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# Admin functions
@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        show_admin_panel(user_id, message.message_id)
    else:
        bot.send_message(user_id, "❌ Access denied.")

def show_admin_panel(user_id, message_id):
    admin_text = """
👑 *Admin Panel*

💼 Manage your SMM bot with powerful admin tools.

Select an option below:
    """
    
    bot.send_photo(
        chat_id=user_id,
        photo=ADMIN_IMAGE,
        caption=admin_text,
        reply_markup=admin_keyboard(),
        parse_mode='Markdown'
    )

def handle_admin_commands(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    if call.data == "admin_stats":
        show_admin_stats(user_id, message_id)
    elif call.data == "admin_balance":
        # Implement balance control
        bot.send_message(user_id, "💰 Balance control feature coming soon!")
    elif call.data == "admin_prices":
        # Implement price management
        bot.send_message(user_id, "✏️ Price management feature coming soon!")
    elif call.data == "admin_broadcast":
        # Implement broadcast
        bot.send_message(user_id, "📢 Broadcast feature coming soon!")
    elif call.data == "admin_users":
        # Implement user control
        bot.send_message(user_id, "👤 User control feature coming soon!")
    elif call.data == "admin_control":
        # Implement bot control
        bot.send_message(user_id, "⚙️ Bot control feature coming soon!")

def show_admin_stats(user_id, message_id):
    total_users = get_all_users()
    total_orders = get_total_orders()
    total_deposits = get_total_deposits()
    total_spent = get_total_spent()
    
    admin_stats_text = f"""
📊 *Admin Statistics*

👥 Total Users: {total_users}
📦 Total Orders: {total_orders}
💰 Total Deposits: ₹{total_deposits:.2f}
💸 Total Spent: ₹{total_spent:.2f}
💎 Revenue: ₹{total_deposits - total_spent:.2f}

📈 Detailed analytics coming soon!
    """
    
    bot.edit_message_caption(
        chat_id=user_id,
        message_id=message_id,
        caption=admin_stats_text,
        reply_markup=admin_keyboard(),
        parse_mode='Markdown'
    )

# Error handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "❓ Unknown command. Use /start to begin.")

# Start the bot
if __name__ == "__main__":
    print("🤖 SMM Bot is running...")
    bot.infinity_polling()