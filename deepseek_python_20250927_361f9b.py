import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
from datetime import datetime
import random
import logging
import urllib.parse

# ✅ APNA BOT TOKEN YAHAN DALO
BOT_TOKEN = "8052955693:AAGoXnNg90jqvcC1X1fVo_qKV8Y0eHjDAZg"

# ✅ BOT INITIALIZE WITH THREADED=FALSE
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ✅ SIMPLE IN-MEMORY DATABASE
users_data = {}
orders_data = []
services_data = []
user_deposit_data = {}  # Store deposit info

# ✅ ADMIN CONFIG
ADMIN_ID = 6052975324
CHANNEL_ID = "@prooflelo1"

# ✅ IMAGE URLS
WELCOME_IMAGE = "https://t.me/prooflelo1/16"
SERVICE_IMAGE = "https://t.me/prooflelo1/16"
DEPOSIT_IMAGE = "https://t.me/prooflelo1/16"
ACCOUNT_IMAGE = "https://t.me/prooflelo1/16"
HISTORY_IMAGE = "https://t.me/prooflelo1/16"
REFER_IMAGE = "https://t.me/prooflelo1/16"

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
    }
]

services_data.extend(default_services)

# ✅ USER STATES FOR CONVERSATION
user_states = {}

# ✅ CHANNEL MEMBERSHIP CHECK
def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

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
    markup.add(InlineKeyboardButton("📞 Sᴜᴘᴘᴏʀᴛ", callback_data="support"))
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

def channel_join_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Jᴏɪɴ Cʜᴀɴɴᴇʟ", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    markup.add(InlineKeyboardButton("✅ I'ᴠᴇ Jᴏɪɴᴇᴅ", callback_data="check_join"))
    return markup

# ✅ START COMMAND - WITH CHANNEL CHECK
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_id = message.chat.id
        user_name = message.from_user.first_name
        
        # Check channel membership
        if not check_channel_membership(user_id):
            channel_text = f"""
📢 Jᴏɪɴ Oᴜʀ Cʜᴀɴɴᴇʟ Fɪʀsᴛ! 📢

Hᴇʏ {user_name}! 👋

Tᴏ Usᴇ Tʜɪs Bᴏᴛ, Yᴏᴜ Nᴇᴇᴅ Tᴏ Jᴏɪɴ Oᴜʀ Oғғɪᴄɪᴀʟ Cʜᴀɴɴᴇʟ Fɪʀsᴛ.

Cʟɪᴄᴋ Tʜᴇ Bᴜᴛᴛᴏɴ Bᴇʟᴏᴡ Tᴏ Jᴏɪɴ Aɴᴅ Tʜᴇɴ Cʟɪᴄᴋ "I'ᴠᴇ Jᴏɪɴᴇᴅ" ✅
            """
            
            bot.send_photo(
                chat_id=user_id,
                photo=WELCOME_IMAGE,
                caption=channel_text,
                reply_markup=channel_join_keyboard(),
                parse_mode="HTML"
            )
            return
        
        # User is in channel, show main menu
        welcome_text = f"""
✨ Wᴇʟᴄᴏᴍᴇ {user_name}! ✨

Tʜɪs Is Tʜᴇ Mᴏsᴛ Aᴅᴠᴀɴᴄᴇᴅ SMM Bᴏᴛ Oɴ Tᴇʟᴇɢʀᴀᴍ! 🚀

Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ Fʀᴏᴍ Tʜᴇ Mᴇɴᴜ Bᴇʟᴏᴡ:
        """
        
        # Initialize user if not exists
        get_user_balance(user_id)
        
        bot.send_photo(
            chat_id=user_id,
            photo=WELCOME_IMAGE,
            caption=welcome_text,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"Error in start command: {e}")

# ✅ CALLBACK QUERY HANDLER
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        user_id = call.message.chat.id
        
        if call.data == "check_join":
            if check_channel_membership(user_id):
                bot.delete_message(user_id, call.message.message_id)
                send_welcome(call.message)
            else:
                bot.answer_callback_query(call.id, "❌ Pʟᴇᴀsᴇ Jᴏɪɴ Tʜᴇ Cʜᴀɴɴᴇʟ Fɪʀsᴛ!", show_alert=True)
        
        elif call.data == "main_menu":
            show_main_menu(call)
        
        elif call.data == "deposit":
            handle_deposit_start(call)
        
        elif call.data == "order_menu":
            show_service_categories(call)
        
        elif call.data == "history":
            handle_history(call)
        
        elif call.data == "refer":
            handle_refer(call)
        
        elif call.data == "account":
            handle_account(call)
        
        elif call.data == "support":
            handle_support(call)
        
        elif call.data == "check_deposit":
            handle_deposit_verification(call)
            
    except Exception as e:
        print(f"Callback error: {e}")

# ✅ DEPOSIT SYSTEM - TUMHARA SYSTEM
def handle_deposit_start(call):
    user_id = call.message.chat.id
    
    # Delete previous message if exists
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    
    # Ask for amount
    deposit_text = """
💰 Dᴇᴘᴏsɪᴛ Sʏsᴛᴇᴍ 💰

Eɴᴛᴇʀ Tʜᴇ Aᴍᴏᴜɴᴛ Yᴏᴜ Wᴀɴᴛ Tᴏ Dᴇᴘᴏsɪᴛ:

💸 Exᴀᴍᴘʟᴇ: 10, 50, 100, 500

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ɪɴ ɴᴜᴍʙᴇʀs:
    """
    
    bot.send_photo(
        chat_id=user_id,
        photo=DEPOSIT_IMAGE,
        caption=deposit_text,
        parse_mode="HTML"
    )
    
    # Set state for next message
    user_states[user_id] = {"action": "awaiting_deposit_amount"}
    bot.register_next_step_handler(call.message, process_deposit_amount)

def process_deposit_amount(message):
    user_id = message.chat.id
    
    try:
        amount = float(message.text)
        
        if amount < 10:
            bot.send_message(user_id, "❌ Mɪɴɪᴍᴜᴍ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ Is ₹10!")
            return
        
        # Generate random 12-digit UTR
        utr = str(random.randint(100000000000, 999999999999))
        
        # Save deposit data
        user_deposit_data[user_id] = {
            "utr": utr,
            "amount": amount,
            "timestamp": datetime.now()
        }
        
        # Create UPI payment link
        upi_link = f"upi://pay?pa=paytm.s1m11be@pty&pn=Paytm&am={amount}&tn=Deposit&tr={utr}"
        
        # Generate QR code using QuickChart API
        encoded_upi_link = urllib.parse.quote(upi_link)
        qr_url = f"https://quickchart.io/qr?text={encoded_upi_link}&size=300"
        
        deposit_details = f"""
💰 Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ 💰

Aᴍᴏᴜɴᴛ: ₹{amount}
UTR: {utr}

UPI ID: paytm.s1m11be@pty
Nᴏᴛᴇ: {utr}

Sᴄᴀɴ Tʜᴇ QR Cᴏᴅᴇ Tᴏ Cᴏᴍᴘʟᴇᴛᴇ Pᴀʏᴍᴇɴᴛ.
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💰 Pᴀɪᴅ ✅", callback_data="check_deposit"))
        markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
        
        # Send QR code with details
        bot.send_photo(
            chat_id=user_id,
            photo=qr_url,
            caption=deposit_details,
            reply_markup=markup,
            parse_mode="HTML"
        )
        
    except ValueError:
        bot.send_message(user_id, "❌ Iɴᴠᴀʟɪᴅ Aᴍᴏᴜɴᴛ! Pʟᴇᴀsᴇ Eɴᴛᴇʀ A Vᴀʟɪᴅ Nᴜᴍʙᴇʀ.")

def handle_deposit_verification(call):
    user_id = call.message.chat.id
    
    if user_id not in user_deposit_data:
        bot.answer_callback_query(call.id, "❌ Nᴏ Pᴇɴᴅɪɴɢ Dᴇᴘᴏsɪᴛ Fᴏᴜɴᴅ!", show_alert=True)
        return
    
    deposit_info = user_deposit_data[user_id]
    utr = deposit_info["utr"]
    amount = deposit_info["amount"]
    
    try:
        # ✅ Autodep API call for payment verification
        api_url = f"https://erox-autodep-api.onrender.com/api?key=LY81vEV7&merchantkey=WYcmQI71591891985230&transactionid={utr}"
        response = requests.get(api_url).json()
        
        if response.get("result", {}).get("STATUS") == "TXN_SUCCESS":
            # Convert ₹ to Points (1 ₹ = 100 Points)
            points_to_add = int(amount * 100)
            
            # Update user balance
            new_balance = update_user_balance(user_id, points_to_add)
            
            # Delete QR message
            try:
                bot.delete_message(user_id, call.message.message_id)
            except:
                pass
            
            # Clear deposit data
            del user_deposit_data[user_id]
            
            success_text = f"""
✅ Pᴀʏᴍᴇɴᴛ Vᴇʀɪғɪᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ! ✅

💰 Aᴍᴏᴜɴᴛ Dᴇᴘᴏsɪᴛᴇᴅ: ₹{amount}
🎯 Pᴏɪɴᴛs Aᴅᴅᴇᴅ: {points_to_add}
🏦 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} Pᴏɪɴᴛs

Tʜᴀɴᴋ Yᴏᴜ Fᴏʀ Yᴏᴜʀ Dᴇᴘᴏsɪᴛ! 🎉
            """
            
            bot.send_photo(
                chat_id=user_id,
                photo=DEPOSIT_IMAGE,
                caption=success_text,
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
            
        else:
            bot.answer_callback_query(
                call.id,
                "❌ Pʟᴇᴀsᴇ Pᴀʏ Fɪʀsᴛ Bᴇғᴏʀᴇ Cʟɪᴄᴋɪɴɢ Pᴀɪᴅ!\n\nYᴏᴜ Hᴀᴠᴇ Nᴏᴛ Dᴇᴘᴏsɪᴛᴇᴅ Yᴇᴛ.",
                show_alert=True
            )
            
    except Exception as e:
        bot.answer_callback_query(
            call.id,
            f"❌ Eʀʀᴏʀ: {str(e)}",
            show_alert=True
        )

# ✅ OTHER HANDLERS WITH IMAGES
def show_main_menu(call):
    main_text = "🏠 Mᴀɪɴ Mᴇɴᴜ - Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ:"
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(WELCOME_IMAGE, caption=main_text),
        reply_markup=main_menu_keyboard()
    )

def show_service_categories(call):
    service_text = "🛒 Sᴇʟᴇᴄᴛ A Sᴇʀᴠɪᴄᴇ Cᴀᴛᴇɢᴏʀʏ:"
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(SERVICE_IMAGE, caption=service_text),
        reply_markup=service_category_keyboard()
    )

def handle_history(call):
    user_id = call.message.chat.id
    user = users_data.get(user_id, {})
    
    history_text = f"📋 Oʀᴅᴇʀ Hɪsᴛᴏʀʏ\n\nTᴏᴛᴀʟ Oʀᴅᴇʀs: {user.get('total_orders', 0)} Pᴏɪɴᴛs"
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(HISTORY_IMAGE, caption=history_text),
        reply_markup=main_menu_keyboard()
    )

def handle_account(call):
    user_id = call.message.chat.id
    user = users_data.get(user_id, {})
    
    account_text = f"""
👤 Mʏ Aᴄᴄᴏᴜɴᴛ 👤

🏦 Bᴀʟᴀɴᴄᴇ: {user.get('balance', 0)} Pᴏɪɴᴛs
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {user.get('total_orders', 0)} Pᴏɪɴᴛs
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: {user.get('total_deposits', 0)} Pᴏɪɴᴛs
📅 Jᴏɪɴᴇᴅ: {user.get('joined_date', 'N/A')}
    """
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(ACCOUNT_IMAGE, caption=account_text),
        reply_markup=main_menu_keyboard()
    )

def handle_refer(call):
    user_id = call.message.chat.id
    bot_username = bot.get_me().username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    refer_text = f"""
👥 Rᴇғᴇʀ & Eᴀʀɴ 👥

Rᴇғᴇʀʀᴀʟ Lɪɴᴋ: {referral_link}

🔹 Yᴏᴜ Gᴇᴛ: 100 Pᴏɪɴᴛs Pᴇʀ Rᴇғᴇʀʀᴀʟ
🔹 Fʀɪᴇɴᴅ Gᴇᴛs: 50 Pᴏɪɴᴛs Bᴏɴᴜs
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📤 Sʜᴀʀᴇ Lɪɴᴋ", url=f"tg://msg_url?text=Join%20this%20awesome%20bot%3A%20{referral_link}"))
    markup.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="main_menu"))
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(REFER_IMAGE, caption=refer_text),
        reply_markup=markup
    )

def handle_support(call):
    support_text = """
📞 Sᴜᴘᴘᴏʀᴛ & Hᴇʟᴘ 📞

Cᴏɴᴛᴀᴄᴛ Sᴜᴘᴘᴏʀᴛ: @YourSupport
Eᴍᴀɪʟ: support@example.com

Wᴇ'ʀᴇ Hᴇʀᴇ Tᴏ Hᴇʟᴘ Yᴏᴜ! ⏰
    """
    
    bot.edit_message_media(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        media=telebot.types.InputMediaPhoto(WELCOME_IMAGE, caption=support_text),
        reply_markup=main_menu_keyboard()
    )

# ✅ TEXT MESSAGE HANDLER
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.lower()
    
    if text in ['/start', 'start', 'menu', 'home']:
        send_welcome(message)
    elif text in ['/deposit', 'deposit']:
        # Simulate deposit callback
        class MockCall:
            def __init__(self, message):
                self.message = message
                self.id = "mock"
        handle_deposit_start(MockCall(message))
    elif text in ['/balance', 'balance', 'account']:
        # Simulate account callback
        class MockCall:
            def __init__(self, message):
                self.message = message
                self.id = "mock"
        handle_account(MockCall(message))
    elif text in ['/support', 'support', 'help']:
        # Simulate support callback
        class MockCall:
            def __init__(self, message):
                self.message = message
                self.id = "mock"
        handle_support(MockCall(message))
    else:
        # Send main menu for unknown commands
        bot.send_photo(
            chat_id=message.chat.id,
            photo=WELCOME_IMAGE,
            caption="❓ Uɴᴋɴᴏᴡɴ Cᴏᴍᴍᴀɴᴅ\n\nUsᴇ Tʜᴇ Bᴜᴛᴛᴏɴs Bᴇʟᴏᴡ:",
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