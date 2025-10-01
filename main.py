import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time

from config import *
from services import *
from payments import *
from orders import *
from admin import *

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# User states for conversation flow
user_states = {}

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command"""
    user_id = message.from_user.id
    
    # Initialize user data if not exists
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
    
    bot.send_photo(
        message.chat.id,
        WELCOME_IMAGE,
        caption=welcome_text,
        reply_markup=keyboard
    )

@bot.message_handler(commands=['admin'])
def admin_command(message):
    """Handle /admin command"""
    show_admin_panel(bot, message)

@bot.message_handler(commands=['track'])
def track_command(message):
    """Handle /track command"""
    bot.send_message(message.chat.id, "📦 Eɴᴛᴇʀ ʏᴏᴜʀ Oʀᴅᴇʀ ID:")
    bot.register_next_step_handler(message, track_order)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    """Handle all callback queries"""
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
            show_admin_panel(bot, call.message)
        elif call.data == "back_to_main":
            edit_to_main_menu(call)
        elif call.data.startswith("category_"):
            category = call.data.replace("category_", "")
            show_services(call, category)
        elif call.data.startswith("service_"):
            service_id = call.data.replace("service_", "")
            service = get_service_by_id(service_id)
            if service:
                show_service_details(bot, call, service)
                user_states[user_id] = {'waiting_for_link': service_id}
        elif call.data == "back_to_categories":
            show_categories(call)
        elif call.data.startswith("paid_"):
            utr = call.data.replace("paid_", "")
            check_payment_status(bot, call, utr)
        elif call.data.startswith("admin_"):
            handle_admin_callbacks(call)
            
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ")
        print(f"Callback error: {e}")

def show_categories(call):
    """Show service categories"""
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
    """Show services for a category"""
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

def ask_deposit_amount(call):
    """Ask user for deposit amount"""
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

def show_orders_menu(call):
    """Show orders menu"""
    user_orders = {k: v for k, v in orders.items() if v.get('user_id') == call.from_user.id}
    
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
    """Show user account"""
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
    """Show support information"""
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
            SERVICE_IMAGE,  # Using service image as placeholder
            caption=caption
        ),
        reply_markup=keyboard
    )

def show_refer(call):
    """Show referral information"""
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

def edit_to_main_menu(call):
    """Edit message to show main menu"""
    start_command(call.message)

def handle_admin_callbacks(call):
    """Handle admin panel callbacks"""
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ")
        return
    
    if call.data == "admin_broadcast":
        handle_broadcast(bot, call)
    elif call.data == "admin_add_balance":
        handle_add_balance(bot, call)
    elif call.data == "admin_deduct_balance":
        handle_deduct_balance(bot, call)
    elif call.data == "admin_service_price":
        handle_service_price(bot, call)
    elif call.data.startswith("admin_service_"):
        service_id = call.data.replace("admin_service_", "")
        handle_service_selection(bot, call, service_id)
    elif call.data == "admin_back":
        show_admin_panel(bot, call.message)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Handle all text messages"""
    user_id = message.from_user.id
    
    # Check if user is waiting for link input
    if user_id in user_states and 'waiting_for_link' in user_states[user_id]:
        service_id = user_states[user_id]['waiting_for_link']
        link = message.text
        
        # Store link and ask for quantity
        user_states[user_id] = {'waiting_for_quantity': service_id, 'link': link}
        
        service = get_service_by_id(service_id)
        if service:
            bot.send_message(
                message.chat.id,
                f"🔗 Lɪɴᴋ sᴀᴠᴇᴅ: {link[:50]}...\n\n"
                f"📊 Nᴏᴡ ᴇɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ ({service['min']:,} - {service['max']:,} {service['unit']}):"
            )
        return
    
    # Check if user is waiting for quantity input
    elif user_id in user_states and 'waiting_for_quantity' in user_states[user_id]:
        service_id = user_states[user_id]['waiting_for_quantity']
        link = user_states[user_id]['link']
        
        handle_new_order(bot, message, service_id, link)
        
        # Clear user state
        if user_id in user_states:
            del user_states[user_id]
        return
    
    # Default response for unknown messages
    bot.send_message(
        message.chat.id,
        "🤖 Usᴇ ᴛʜᴇ ᴍᴇɴᴜ ʙᴜᴛᴛᴏɴs ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ. Oʀ ᴛʏᴘᴇ /start ᴛᴏ sᴇᴇ ᴛʜᴇ ᴍᴀɪɴ ᴍᴇɴᴜ."
    )

def refund_background_task():
    """Background task to process refunds"""
    while True:
        try:
            process_refunds()
            time.sleep(1800)  # Run every 30 minutes
        except Exception as e:
            print(f"Refund task error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    print("🤖 Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ...")
    
    # Start background tasks
    refund_thread = threading.Thread(target=refund_background_task, daemon=True)
    refund_thread.start()
    
    # Start bot polling
    bot.polling(none_stop=True)
