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
SMM_API_KEY = "c33fb3166621856879b2e486b99a30f0c442ac92"
SMM_API_URL = "https://smm-jupiter.com/api/v2"

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

# Font style conversion function
def style_text(text):
    conversion_map = {
        'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'H': 'H', 'I': 'I', 
        'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R',
        'S': 'S', 'T': 'T', 'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z',
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ',
        'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ',
        's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
    }
    
    styled_text = ""
    for char in text:
        if char in conversion_map:
            styled_text += conversion_map[char]
        else:
            styled_text += char
    return styled_text

# Services and Categories (with styled text)
services = {
    "instagram": {
        "name": style_text("Instagram"),
        "services": {
            1: {"name": style_text("Instagram Likes"), "rate": 50, "min": 100, "max": 100000, "unit": 1000, "api_id": 1},
            2: {"name": style_text("Instagram Views"), "rate": 1, "min": 100, "max": 100000, "unit": 1000, "api_id": 13685},
            3: {"name": style_text("Instagram Followers"), "rate": 100, "min": 50, "max": 50000, "unit": 1000, "api_id": 3}
        }
    },
    "facebook": {
        "name": style_text("Facebook"), 
        "services": {
            4: {"name": style_text("Facebook Likes"), "rate": 40, "min": 100, "max": 100000, "unit": 1000, "api_id": 4},
            5: {"name": style_text("Facebook Views"), "rate": 35, "min": 100, "max": 100000, "unit": 1000, "api_id": 13685},
            6: {"name": style_text("Facebook Followers"), "rate": 80, "min": 50, "max": 50000, "unit": 1000, "api_id": 6}
        }
    },
    "youtube": {
        "name": style_text("YouTube"),
        "services": {
            7: {"name": style_text("YouTube Likes"), "rate": 60, "min": 100, "max": 100000, "unit": 1000, "api_id": 7},
            8: {"name": style_text("YouTube Views"), "rate": 45, "min": 100, "max": 100000, "unit": 1000, "api_id": 8},
            9: {"name": style_text("YouTube Subscribers"), "rate": 150, "min": 50, "max": 25000, "unit": 1000, "api_id": 9}
        }
    },
    "telegram": {
        "name": style_text("Telegram"),
        "services": {
            10: {"name": style_text("Telegram Members"), "rate": 200, "min": 50, "max": 10000, "unit": 1000, "api_id": 10},
            11: {"name": style_text("Telegram Post Likes"), "rate": 80, "min": 100, "max": 50000, "unit": 1000, "api_id": 11},
            12: {"name": style_text("Telegram Post Views"), "rate": 50, "min": 100, "max": 50000, "unit": 1000, "api_id": 12}
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
        InlineKeyboardButton(style_text("Deposit"), callback_data="deposit"),
        InlineKeyboardButton(style_text("Order"), callback_data="order"),
        InlineKeyboardButton(style_text("Orders"), callback_data="orders"),
        InlineKeyboardButton(style_text("Refer"), callback_data="refer"),
        InlineKeyboardButton(style_text("Account"), callback_data="account"),
        InlineKeyboardButton(style_text("Stats"), callback_data="stats"),
        InlineKeyboardButton(style_text("Support"), callback_data="support")
    ]
    # Add buttons in rows of 3
    for i in range(0, len(buttons), 3):
        keyboard.add(*buttons[i:i+3])
    return keyboard

# Categories Keyboard
def categories_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(style_text("Instagram"), callback_data="category_instagram"))
    keyboard.add(InlineKeyboardButton(style_text("Facebook"), callback_data="category_facebook"))
    keyboard.add(InlineKeyboardButton(style_text("YouTube"), callback_data="category_youtube"))
    keyboard.add(InlineKeyboardButton(style_text("Telegram"), callback_data="category_telegram"))
    keyboard.add(InlineKeyboardButton(style_text("Back"), callback_data="land"))
    return keyboard

# Admin Keyboard
def admin_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(style_text("Balance Control"), callback_data="admin_balance"))
    keyboard.add(InlineKeyboardButton(style_text("Manage Prices"), callback_data="admin_prices"))
    keyboard.add(InlineKeyboardButton(style_text("Broadcast"), callback_data="admin_broadcast"))
    keyboard.add(InlineKeyboardButton(style_text("User Control"), callback_data="admin_users"))
    keyboard.add(InlineKeyboardButton(style_text("Bot Control"), callback_data="admin_control"))
    keyboard.add(InlineKeyboardButton(style_text("Stats"), callback_data="admin_stats"))
    keyboard.add(InlineKeyboardButton(style_text("Main Menu"), callback_data="land"))
    return keyboard

# Start Command
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        if not bot_enabled and message.from_user.id != ADMIN_ID:
            bot.send_message(message.chat.id, style_text("Bot is currently under maintenance. Please try again later."))
            return
            
        if message.from_user.id in banned_users:
            bot.send_message(message.chat.id, style_text("You are banned from using this bot."))
            return
            
        init_user(message.from_user.id)
        
        caption = style_text("""
Welcome to SMM Bot

Your Trusted SMM Panel

Features:
Instant Start
High Quality Services
24/7 Support

Start Growing Your Social Media Now!
        """)
        
        bot.send_photo(
            chat_id=message.chat.id,
            photo=WELCOME_IMAGE,
            caption=caption,
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Start command error: {e}")
        bot.send_message(message.chat.id, style_text("An error occurred. Please try again."))

# Admin Command
@bot.message_handler(commands=['admin'])
def admin_command(message):
    try:
        if message.from_user.id != ADMIN_ID:
            bot.send_message(message.chat.id, style_text("Access denied."))
            return
            
        caption = style_text("""
Admin Panel

Full Control Over Bot

Manage all bot operations from here
        """)
        
        bot.send_photo(
            chat_id=message.chat.id,
            photo=ADMIN_IMAGE,
            caption=caption,
            reply_markup=admin_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin command error: {e}")
        bot.send_message(message.chat.id, style_text("An error occurred. Please try again."))

# Callback Query Handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        user_id = call.from_user.id
        
        if not bot_enabled and user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, style_text("Bot is currently under maintenance."))
            return
            
        if user_id in banned_users:
            bot.answer_callback_query(call.id, style_text("You are banned from using this bot."))
            return
            
        init_user(user_id)
        
        if call.data == "land":
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
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
            
    except Exception as e:
        print(f"Callback handler error: {e}")
        try:
            bot.answer_callback_query(call.id, style_text("An error occurred. Please try again."))
        except:
            pass

# Deposit Flow - FIXED
def show_deposit(call):
    try:
        user_id = call.from_user.id  # FIXED: Define user_id here
        
        caption = style_text("""
Deposit Funds

Enter The Amount You Want To Deposit

Minimum Deposit: ₹10
        """)
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=DEPOSIT_IMAGE,
                caption=caption,
                parse_mode='HTML'
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="land")
            )
        )
        
        # Set user state to wait for deposit amount
        user_states[user_id] = "waiting_deposit_amount"
        
    except Exception as e:
        print(f"Show deposit error: {e}")
        bot.answer_callback_query(call.id, style_text("Error showing deposit. Please try again."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_deposit_amount")
def handle_deposit_amount(message):
    user_id = message.from_user.id
    
    try:
        amount = float(message.text)
        
        if amount < 10:
            bot.send_message(user_id, style_text("Minimum deposit amount is ₹10"))
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
        
        caption = style_text(f"""
Deposit Request

Amount: ₹{amount}
UTR: {utr}

Scan the QR code to complete your deposit
        """)
        
        # Send QR code
        bot.send_photo(
            chat_id=user_id,
            photo=qr_url,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(style_text("Paid"), callback_data="check_txn")],
                [InlineKeyboardButton(style_text("Back"), callback_data="land")]
            ]),
            parse_mode='HTML'
        )
        
        # Clear user state
        user_states[user_id] = None
        
    except ValueError:
        bot.send_message(user_id, style_text("Please enter a valid amount (numbers only)"))
    except Exception as e:
        print(f"Deposit amount error: {e}")
        bot.send_message(user_id, style_text("An error occurred. Please try again."))

# Check Transaction - FIXED
def check_transaction(call):
    user_id = call.from_user.id
    
    try:
        if user_id not in user_data or "deposit_utr" not in user_data[user_id]:
            bot.answer_callback_query(call.id, style_text("No pending deposit found."), show_alert=True)
            return
            
        utr = user_data[user_id]["deposit_utr"]
        amount = user_data[user_id]["deposit_amount"]
        
        # Check transaction via Autodep API
        url = f"https://erox-autodep-api.onrender.com/api?key={AUTODEP_API_KEY}&merchantkey={AUTODEP_MERCHANT_KEY}&transactionid={utr}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("result", {}).get("STATUS") == "TXN_SUCCESS":
            # Update user balance
            user_balances[user_id] += amount
            user_deposits[user_id] += amount
            
            # Clear deposit data
            if user_id in user_data:
                user_data[user_id].pop("deposit_utr", None)
                user_data[user_id].pop("deposit_amount", None)
            
            # Notify user
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=style_text(f"Transaction Successful!\n\n₹{amount} added to your balance\nNew Balance: ₹{user_balances[user_id]}"),
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(style_text("Main Menu"), callback_data="land")
                )
            )
            
            # Notify admin
            try:
                bot.send_message(
                    ADMIN_ID,
                    style_text(f"New Deposit\n\nUser: {user_id}\nAmount: ₹{amount}\nBalance: ₹{user_balances[user_id]}")
                )
            except:
                pass
            
        else:
            bot.answer_callback_query(
                call.id,
                style_text("You have not deposited yet. Please pay first."),
                show_alert=True
            )
            
    except Exception as e:
        print(f"Check transaction error: {e}")
        bot.answer_callback_query(call.id, style_text("Error checking transaction. Please try again."), show_alert=True)

# Order Flow
def show_categories(call):
    try:
        caption = style_text("""
Services Menu

Choose a category to start ordering:
        """)
        
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
    except Exception as e:
        print(f"Show categories error: {e}")
        bot.answer_callback_query(call.id, style_text("Error showing categories. Please try again."))

def show_services(call, category):
    try:
        if category not in services:
            bot.answer_callback_query(call.id, style_text("Category not found"))
            return
            
        category_data = services[category]
        keyboard = InlineKeyboardMarkup()
        
        for service_id, service in category_data["services"].items():
            keyboard.add(InlineKeyboardButton(
                f"{service['name']} - ₹{service['rate']}/{service['unit']}",
                callback_data=f"service_{service_id}"
            ))
        
        keyboard.add(InlineKeyboardButton(style_text("Back"), callback_data="order"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=style_text(f"Services - {category_data['name']}\n\nSelect a service to order:"),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Show services error: {e}")
        bot.answer_callback_query(call.id, style_text("Error showing services. Please try again."))

def start_order(call, service_id):
    try:
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
            bot.answer_callback_query(call.id, style_text("Service not found"))
            return
            
        # Save service selection
        user_data[user_id] = {
            "selected_service": service_id,
            "service_details": service
        }
        
        caption = style_text(f"""
Order Details

Service: {service['name']}
Price: ₹{service['rate']}/{service['unit']}
Min: {service['min']}
Max: {service['max']}

Please send the link:
        """)
        
        # Find the category key for back button
        category_key = None
        for cat_key, cat_data in services.items():
            if service_id in cat_data["services"]:
                category_key = cat_key
                break
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data=f"category_{category_key}")
            ),
            parse_mode='HTML'
        )
        
        user_states[user_id] = "waiting_order_link"
        
    except Exception as e:
        print(f"Start order error: {e}")
        bot.answer_callback_query(call.id, style_text("Error starting order. Please try again."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_order_link")
def handle_order_link(message):
    user_id = message.from_user.id
    
    try:
        if user_id not in user_data or "selected_service" not in user_data[user_id]:
            bot.send_message(user_id, style_text("No service selected. Please start over."))
            user_states[user_id] = None
            return
            
        link = message.text
        user_data[user_id]["order_link"] = link
        
        service = user_data[user_id]["service_details"]
        
        bot.send_message(
            user_id,
            style_text(f"Link Saved: {link}\n\nNow please enter the quantity:\n(Min: {service['min']}, Max: {service['max']})")
        )
        
        user_states[user_id] = "waiting_order_quantity"
        
    except Exception as e:
        print(f"Order link error: {e}")
        bot.send_message(user_id, style_text("Error processing link. Please try again."))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_order_quantity")
def handle_order_quantity(message):
    user_id = message.from_user.id
    
    try:
        if user_id not in user_data or "selected_service" not in user_data[user_id]:
            bot.send_message(user_id, style_text("No service selected. Please start over."))
            user_states[user_id] = None
            return
            
        quantity = int(message.text)
        service = user_data[user_id]["service_details"]
        link = user_data[user_id]["order_link"]
        
        # Validate quantity
        if quantity < service["min"] or quantity > service["max"]:
            bot.send_message(
                user_id,
                style_text(f"Quantity must be between {service['min']} and {service['max']}")
            )
            return
            
        # Calculate cost
        cost = (quantity / service["unit"]) * service["rate"]
        
        # Check balance
        if user_balances[user_id] < cost:
            bot.send_message(
                user_id,
                style_text(f"Insufficient Balance\n\nRequired: ₹{cost:.2f}\nAvailable: ₹{user_balances[user_id]:.2f}\n\nPlease deposit first.")
            )
            user_states[user_id] = None
            return
            
        # Place order via SMM API
        order_result = place_smm_order(
            service_id=service["api_id"],  # Use API service ID
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
                style_text(f"Order Placed Successfully!\n\nOrder ID: {order_id}\nAmount: ₹{cost:.2f}\nBalance: ₹{user_balances[user_id]:.2f}")
            )
            
            # Send to proof channel
            send_proof_message(user_id, service["name"], quantity, cost, order_id)
            
        else:
            bot.send_message(
                user_id,
                style_text(f"Order Failed\n\nError: {order_result['error']}")
            )
            
    except ValueError:
        bot.send_message(user_id, style_text("Please enter a valid number for quantity"))
        return
    except Exception as e:
        print(f"Order quantity error: {e}")
        bot.send_message(user_id, style_text("Error processing order. Please try again."))
        
    user_states[user_id] = None

def place_smm_order(service_id, link, quantity):
    try:
        # Actual SMM API call
        params = {
            "key": SMM_API_KEY,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        
        response = requests.post(SMM_API_URL, data=params, timeout=30)
        data = response.json()
        
        if data.get("order"):
            return {
                "success": True,
                "order_id": data["order"]
            }
        else:
            return {
                "success": False,
                "error": data.get("error", "Unknown error from SMM API")
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def send_proof_message(user_id, service_name, quantity, cost, order_id):
    proof_text = style_text(f"""
New Order Placed!

User: {user_id}
Service: {service_name}
Quantity: {quantity}
Amount: ₹{cost:.2f}
Order ID: {order_id}

Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
    """)
    
    try:
        bot.send_message(
            PROOF_CHANNEL,
            proof_text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Bot Here"), url=f"https://t.me/{(bot.get_me()).username}")
            )
        )
    except Exception as e:
        print(f"Proof channel error: {e}")

# Other Menu Functions
def show_orders(call):
    try:
        user_id = call.from_user.id
        user_orders = orders.get(user_id, [])[-5:]  # Last 5 orders
        
        if not user_orders:
            caption = style_text("No orders found")
        else:
            caption = style_text("Last 5 Orders:\n\n")
            for order in reversed(user_orders):
                caption += f"ID {order['order_id']}\n"
                caption += f"{order['service']}\n"
                caption += f"{order['quantity']}\n"
                caption += f"₹{order['cost']:.2f}\n"
                caption += f"{order['status']}\n"
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
                InlineKeyboardButton(style_text("Back"), callback_data="land")
            )
        )
    except Exception as e:
        print(f"Show orders error: {e}")
        bot.answer_callback_query(call.id, style_text("Error showing orders. Please try again."))

def show_refer(call):
    try:
        user_id = call.from_user.id
        bot_username = (bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        
        caption = style_text(f"""
Referral System

Your Referral Link:
{referral_link}

Referral Bonus:
• 10% of your friend's first deposit
• Unlimited earnings

Share this link and earn more!
        """)
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=REFER_IMAGE,
                caption=caption,
                parse_mode='HTML'
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="land")
            )
        )
    except Exception as e:
        print(f"Show refer error: {e}")
        bot.answer_callback_query(call.id, style_text("Error showing referral. Please try again."))

def show_account(call):
    try:
        user_id = call.from_user.id
        init_user(user_id)
        
        caption = style_text(f"""
Account Information

User ID: {user_id}
Balance: ₹{user_balances[user_id]:.2f}
Total Deposits: ₹{user_deposits[user_id]:.2f}
Total Spent: ₹{user_spent[user_id]:.2f}
Total Orders: {len(orders.get(user_id, []))}
        """)
        
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=telebot.types.InputMediaPhoto(
                media=ACCOUNT_IMAGE,
                caption=caption,
                parse_mode='HTML'
            ),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="land")
            )
        )
    except Exception as e:
        print(f"Show account error: {e}")
        bot.answer_callback_query(call.id, style_text("Error showing account. Please try again."))

def show_stats(call):
    try:
        user_id = call.from_user.id
        
        total_users = len(user_balances)
        total_orders = sum(len(user_orders) for user_orders in orders.values())
        total_deposits = sum(user_deposits.values())
        total_spent = sum(user_spent.values())
        
        caption = style_text(f"""
Bot Statistics

Total Users: {total_users}
Total Orders: {total_orders}
Total Deposits: ₹{total_deposits:.2f}
Total Spent: ₹{total_spent:.2f}

Bot Status: {'Online' if bot_enabled else 'Offline'}
        """)
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="land")
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Show stats error: {e}")
        bot.answer_callback_query(call.id, style_text("Error showing stats. Please try again."))

def show_support(call):
    try:
        caption = style_text("""
Support

Need help? Contact our support team:

Available 24/7
Quick responses
Technical support
        """)
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(style_text("Contact Support"), url=SUPPORT_LINK)],
                [InlineKeyboardButton(style_text("Back"), callback_data="land")]
            ]),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Show support error: {e}")
        bot.answer_callback_query(call.id, style_text("Error showing support. Please try again."))

# Admin Functions
def admin_balance_control(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=style_text("Balance Control\n\nUse commands:\n/addbalance user_id amount\n/deductbalance user_id amount"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="admin")
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin balance control error: {e}")
        bot.answer_callback_query(call.id, style_text("Error accessing balance control."))

def admin_manage_prices(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=style_text("Manage Prices\n\nPrice management interface coming soon..."),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="admin")
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin manage prices error: {e}")
        bot.answer_callback_query(call.id, style_text("Error accessing price management."))

def admin_broadcast(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=style_text("Broadcast\n\nUse command:\n/broadcast your_message_here"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="admin")
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin broadcast error: {e}")
        bot.answer_callback_query(call.id, style_text("Error accessing broadcast."))

def admin_user_control(call):
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=style_text("User Control\n\nUse commands:\n/ban user_id\n/unban user_id"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="admin")
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin user control error: {e}")
        bot.answer_callback_query(call.id, style_text("Error accessing user control."))

def admin_bot_control(call):
    try:
        status = "ENABLED" if bot_enabled else "DISABLED"
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=style_text(f"Bot Control\n\nCurrent Status: {status}\n\nUse commands:\n/enablebot\n/disablebot"),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="admin")
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin bot control error: {e}")
        bot.answer_callback_query(call.id, style_text("Error accessing bot control."))

def admin_stats(call):
    try:
        total_users = len(user_balances)
        total_orders = sum(len(user_orders) for user_orders in orders.values())
        total_deposits = sum(user_deposits.values())
        total_spent = sum(user_spent.values())
        
        caption = style_text(f"""
Admin Stats

Total Users: {total_users}
Total Orders: {total_orders}
Total Deposits: ₹{total_deposits:.2f}
Total Spent: ₹{total_spent:.2f}
Banned Users: {len(banned_users)}
Bot Status: {'Online' if bot_enabled else 'Offline'}
        """)
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(style_text("Back"), callback_data="admin")
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Admin stats error: {e}")
        bot.answer_callback_query(call.id, style_text("Error accessing admin stats."))

# Admin Commands
@bot.message_handler(commands=['addbalance'])
def add_balance_command(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return
            
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, style_text("Usage: /addbalance user_id amount"))
            return
            
        user_id = int(parts[1])
        amount = float(parts[2])
        
        init_user(user_id)
        user_balances[user_id] += amount
        
        bot.send_message(
            message.chat.id,
            style_text(f"Balance added!\nUser: {user_id}\nAmount: ₹{amount}\nNew Balance: ₹{user_balances[user_id]}")
        )
        
    except Exception as e:
        print(f"Add balance error: {e}")
        bot.send_message(message.chat.id, style_text("Error adding balance. Usage: /addbalance user_id amount"))

@bot.message_handler(commands=['deductbalance'])
def deduct_balance_command(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return
            
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, style_text("Usage: /deductbalance user_id amount"))
            return
            
        user_id = int(parts[1])
        amount = float(parts[2])
        
        init_user(user_id)
        user_balances[user_id] -= amount
        
        bot.send_message(
            message.chat.id,
            style_text(f"Balance deducted!\nUser: {user_id}\nAmount: ₹{amount}\nNew Balance: ₹{user_balances[user_id]}")
        )
        
    except Exception as e:
        print(f"Deduct balance error: {e}")
        bot.send_message(message.chat.id, style_text("Error deducting balance. Usage: /deductbalance user_id amount"))

@bot.message_handler(commands=['ban'])
def ban_user_command(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return
            
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, style_text("Usage: /ban user_id"))
            return
            
        user_id = int(parts[1])
        
        banned_users.add(user_id)
        bot.send_message(message.chat.id, style_text(f"User {user_id} banned"))
        
    except Exception as e:
        print(f"Ban user error: {e}")
        bot.send_message(message.chat.id, style_text("Error banning user. Usage: /ban user_id"))

@bot.message_handler(commands=['unban'])
def unban_user_command(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return
            
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, style_text("Usage: /unban user_id"))
            return
            
        user_id = int(parts[1])
        
        banned_users.discard(user_id)
        bot.send_message(message.chat.id, style_text(f"User {user_id} unbanned"))
        
    except Exception as e:
        print(f"Unban user error: {e}")
        bot.send_message(message.chat.id, style_text("Error unbanning user. Usage: /unban user_id"))

@bot.message_handler(commands=['enablebot'])
def enable_bot_command(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return
            
        global bot_enabled
        bot_enabled = True
        bot.send_message(message.chat.id, style_text("Bot enabled"))
        
    except Exception as e:
        print(f"Enable bot error: {e}")
        bot.send_message(message.chat.id, style_text("Error enabling bot"))

@bot.message_handler(commands=['disablebot'])
def disable_bot_command(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return
            
        global bot_enabled
        bot_enabled = False
        bot.send_message(message.chat.id, style_text("Bot disabled"))
        
    except Exception as e:
        print(f"Disable bot error: {e}")
        bot.send_message(message.chat.id, style_text("Error disabling bot"))

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return
            
        if len(message.text.split()) < 2:
            bot.send_message(message.chat.id, style_text("Usage: /broadcast your_message"))
            return
            
        broadcast_text = message.text.split(' ', 1)[1]
        sent = 0
        failed = 0
        
        for user_id in user_balances:
            try:
                bot.send_message(user_id, style_text(f"Broadcast:\n\n{broadcast_text}"))
                sent += 1
            except:
                failed += 1
                
        bot.send_message(
            message.chat.id,
            style_text(f"Broadcast completed!\nSent: {sent}\nFailed: {failed}")
        )
        
    except Exception as e:
        print(f"Broadcast error: {e}")
        bot.send_message(message.chat.id, style_text("Error broadcasting. Usage: /broadcast your_message"))

# Default handler for unknown commands/messages - FIXED
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    try:
        # If user is in a state, don't show main menu
        if message.from_user.id in user_states and user_states[message.from_user.id] is not None:
            return
            
        # Show main menu for unknown commands
        start_command(message)
    except Exception as e:
        print(f"Unknown message handler error: {e}")
        bot.send_message(message.chat.id, style_text("An error occurred. Please try /start"))

# Start polling with error handling
if __name__ == "__main__":
    print("🤖 Bot is running...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            print("Restarting bot in 10 seconds...")
            time.sleep(10)
