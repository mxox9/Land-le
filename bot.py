import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import threading
import time
from datetime import datetime

from config import Config
from database import db
from utils import style_text, get_categories, get_services_by_category, validate_quantity
from payments import PaymentSystem, create_deposit_message
from orders import OrderSystem, calculate_order_cost, create_order_summary

# Initialize bot
bot = telebot.TeleBot(Config.BOT_TOKEN)

# Store temporary user data
user_states = {}
payment_sessions = {}

class UserState:
    WAITING_DEPOSIT_AMOUNT = "waiting_deposit_amount"
    WAITING_ORDER_LINK = "waiting_order_link"
    WAITING_ORDER_QUANTITY = "waiting_order_quantity"
    WAITING_TRACK_ORDER = "waiting_track_order"

def is_user_joined_channel(user_id):
    """Cʜᴇᴄᴋ ɪғ ᴜsᴇʀ ʜᴀs ᴊᴏɪɴᴇᴅ ᴄʜᴀɴɴᴇʟ"""
    try:
        member = bot.get_chat_member(f"@{Config.CHANNEL_ID}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return True  # If check fails, assume joined

def is_admin(user_id):
    """Cʜᴇᴄᴋ ɪғ ᴜsᴇʀ ɪs ᴀᴅᴍɪɴ"""
    return user_id in Config.ADMIN_IDS

def main_menu():
    """Mᴀɪɴ ᴍᴇɴᴜ ɪɴʟɪɴᴇ ᴋᴇʏʙᴏᴀʀᴅ"""
    keyboard = InlineKeyboardMarkup()
    
    keyboard.row(
        InlineKeyboardButton(style_text("💰 Dᴇᴘᴏsɪᴛ"), callback_data="deposit"),
        InlineKeyboardButton(style_text("🛒 Nᴇᴡ Oʀᴅᴇʀ"), callback_data="new_order")
    )
    
    keyboard.row(
        InlineKeyboardButton(style_text("📋 Tʀᴀᴄᴋ Oʀᴅᴇʀ"), callback_data="track_order"),
        InlineKeyboardButton(style_text("👤 Aᴄᴄᴏᴜɴᴛ"), callback_data="account")
    )
    
    keyboard.row(
        InlineKeyboardButton(style_text("👥 Rᴇғᴇʀ"), callback_data="refer"),
        InlineKeyboardButton(style_text("📊 Sᴛᴀᴛs"), callback_data="stats")
    )
    
    keyboard.row(
        InlineKeyboardButton(style_text("ℹ️ Sᴜᴘᴘᴏʀᴛ"), callback_data="support")
    )
    
    keyboard.row(
        InlineKeyboardButton(style_text("Hᴏᴡ Tᴏ Usᴇ"), callback_data="how_to_use"),
        InlineKeyboardButton(style_text("Rᴇsᴛᴀʀᴛ"), callback_data="restart")
    )
    
    return keyboard

def channel_join_keyboard():
    """Cʜᴀɴɴᴇʟ ᴊᴏɪɴ ᴋᴇʏʙᴏᴀʀᴅ"""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(style_text("✅ Jᴏɪɴ Cʜᴀɴɴᴇʟ"), url=f"https://t.me/{Config.CHANNEL_ID}"),
        InlineKeyboardButton(style_text("🔃 Cʜᴇᴄᴋ"), callback_data="check_join")
    )
    return keyboard

def back_button():
    """Bᴀᴄᴋ ʙᴜᴛᴛᴏɴ"""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton(style_text("Bᴀᴄᴋ 🔙"), callback_data="main_menu"))
    return keyboard

def paid_button(utr):
    """Pᴀɪᴅ ʙᴜᴛᴛᴏɴ ᴡɪᴛʜ UTR"""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(style_text("𝗣𝗮𝗶𝗱 ✅"), callback_data=f"paid_{utr}"),
        InlineKeyboardButton(style_text("Bᴀᴄᴋ 🔙"), callback_data="main_menu")
    )
    return keyboard

def support_keyboard():
    """Sᴜᴘᴘᴏʀᴛ ᴋᴇʏʙᴏᴀʀᴅ"""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(style_text("Cᴏɴᴛᴀᴄᴛ Us"), url=Config.SUPPORT_WHATSAPP),
        InlineKeyboardButton(style_text("Bᴀᴄᴋ"), callback_data="main_menu")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    """Sᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ ᴡɪᴛʜ ᴄʜᴀɴɴᴇʟ ᴄʜᴇᴄᴋ"""
    user_id = message.from_user.id
    
    # Check for referral
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        if ref_code.startswith('ref_'):
            referrer_id = int(ref_code[4:])
            user = db.get_user(user_id)
            if user['referred_by'] is None and referrer_id != user_id:
                db.update_user(user_id, {'referred_by': referrer_id})
                
                # Add bonus to referrer if new user hasn't claimed yet
                referrer = db.get_user(referrer_id)
                if not user.get('referral_bonus_claimed', False):
                    db.update_user(referrer_id, {
                        'balance': referrer['balance'] + Config.REFERRAL_BONUS,
                        'referral_bonus_claimed': True
                    })
                    bot.send_message(referrer_id, style_text(f"""
🎉 Rᴇғᴇʀʀᴀʟ Bᴏɴᴜs!

Yᴏᴜ ʀᴇғᴇʀʀᴇᴅ ᴀ ɴᴇᴡ ᴜsᴇʀ! 
+{Config.REFERRAL_BONUS} ᴘᴏɪɴᴛs ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.
"""))
    
    if not is_user_joined_channel(user_id):
        bot.send_message(
            message.chat.id,
            style_text("Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ:"),
            reply_markup=channel_join_keyboard()
        )
        return
    
    welcome_text = style_text("""
🤖 Wᴇʟᴄᴏᴍᴇ ᴛᴏ Sᴏᴄɪᴀʟ Mᴇᴅɪᴀ Mᴀʀᴋᴇᴛɪɴɢ Bᴏᴛ!

Cʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ᴛʜᴇ ᴍᴇɴᴜ ʙᴇʟᴏᴡ:

💰 Dᴇᴘᴏsɪᴛ - Aᴅᴅ ғᴜɴᴅs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ
🛒 Nᴇᴡ Oʀᴅᴇʀ - Pʟᴀᴄᴇ ᴀ ɴᴇᴡ sᴇʀᴠɪᴄᴇ ᴏʀᴅᴇʀ
📋 Tʀᴀᴄᴋ Oʀᴅᴇʀ - Cʜᴇᴄᴋ ᴏʀᴅᴇʀ sᴛᴀᴛᴜs
👤 Aᴄᴄᴏᴜɴᴛ - Vɪᴇᴡ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ɪɴғᴏ
👥 Rᴇғᴇʀ - Rᴇғᴇʀ ғʀɪᴇɴᴅs & ᴇᴀʀɴ ʙᴏɴᴜsᴇs
📊 Sᴛᴀᴛs - Vɪᴇᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs
ℹ️ Sᴜᴘᴘᴏʀᴛ - Gᴇᴛ ʜᴇʟᴘ & sᴜᴘᴘᴏʀᴛ
""")
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Hᴀɴᴅʟᴇ ᴀʟʟ ɪɴʟɪɴᴇ ǫᴜᴇʀɪᴇs"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "check_join":
        if is_user_joined_channel(user_id):
            bot.edit_message_text(
                style_text("Tʜᴀɴᴋ ʏᴏᴜ! Nᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ."),
                chat_id, message_id,
                reply_markup=main_menu()
            )
        else:
            bot.answer_callback_query(call.id, style_text("Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ғɪʀsᴛ!"), show_alert=True)
    
    elif call.data == "main_menu":
        bot.edit_message_text(
            style_text("Mᴀɪɴ Mᴇɴᴜ:"),
            chat_id, message_id,
            reply_markup=main_menu()
        )
    
    elif call.data == "deposit":
        user_states[user_id] = UserState.WAITING_DEPOSIT_AMOUNT
        bot.edit_message_text(
            style_text("💰 Dᴇᴘᴏsɪᴛ\n\nEɴᴛᴇʀ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ɪɴ ʀᴜᴘᴇᴇs (₹):"),
            chat_id, message_id,
            reply_markup=back_button()
        )
    
    elif call.data == "new_order":
        if not db.bot_enabled:
            bot.answer_callback_query(call.id, style_text("Bᴏᴛ ɪs ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ᴅɪsᴀʙʟᴇᴅ ʙʏ ᴀᴅᴍɪɴ!"), show_alert=True)
            return
        
        categories = get_categories(Config.SERVICES)
        keyboard = InlineKeyboardMarkup()
        
        for category in categories:
            keyboard.row(InlineKeyboardButton(category, callback_data=f"category_{category}"))
        
        keyboard.row(InlineKeyboardButton(style_text("Bᴀᴄᴋ 🔙"), callback_data="main_menu"))
        
        bot.edit_message_text(
            style_text("🛒 Nᴇᴡ Oʀᴅᴇʀ\n\nSᴇʟᴇᴄᴛ ᴀ ᴄᴀᴛᴇɢᴏʀʏ:"),
            chat_id, message_id,
            reply_markup=keyboard
        )
    
    elif call.data.startswith("category_"):
        category = call.data.replace("category_", "")
        services = get_services_by_category(category, Config.SERVICES)
        
        keyboard = InlineKeyboardMarkup()
        for service in services:
            keyboard.row(InlineKeyboardButton(
                f"{service['name']} - ₹{service['price']/100:.2f}/{service['unit']}",
                callback_data=f"service_{service['id']}"
            ))
        
        keyboard.row(InlineKeyboardButton(style_text("Bᴀᴄᴋ 🔙"), callback_data="new_order"))
        
        bot.edit_message_text(
            style_text(f"🛒 {category}\n\nSᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ:"),
            chat_id, message_id,
            reply_markup=keyboard
        )
    
    elif call.data.startswith("service_"):
        service_id = int(call.data.replace("service_", ""))
        service = next((s for s in Config.SERVICES if s['id'] == service_id), None)
        
        if service:
            user_states[user_id] = {
                'state': UserState.WAITING_ORDER_LINK,
                'service': service
            }
            
            bot.edit_message_text(
                style_text(f"""
🛒 {service['name']}

{service['description']}

Mɪɴ: {service['min']}
Mᴀx: {service['max']}
Uɴɪᴛ: {service['unit']}
Pʀɪᴄᴇ: ₹{service['price']/100:.2f} ᴘᴇʀ {service['unit']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ:
"""),
                chat_id, message_id,
                reply_markup=back_button()
            )
    
    elif call.data == "track_order":
        user_states[user_id] = UserState.WAITING_TRACK_ORDER
        bot.edit_message_text(
            style_text("📋 Tʀᴀᴄᴋ Oʀᴅᴇʀ\n\nPʟᴇᴀsᴇ ᴇɴᴛᴇʀ ʏᴏᴜʀ Oʀᴅᴇʀ ID:"),
            chat_id, message_id,
            reply_markup=back_button()
        )
    
    elif call.data == "account":
        user = db.get_user(user_id)
        account_text = style_text(f"""
👤 Aᴄᴄᴏᴜɴᴛ Iɴғᴏ

🆔 Usᴇʀ ID: {user_id}
💰 Bᴀʟᴀɴᴄᴇ: {user['balance']} ᴘᴏɪɴᴛs (₹{user['balance']/100:.2f})
🏦 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{user['total_deposits']:.2f}
💳 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: {user['total_spent']} ᴘᴏɪɴᴛs
📅 Jᴏɪɴ Dᴀᴛᴇ: {user['join_date']}
""")
        bot.edit_message_text(account_text, chat_id, message_id, reply_markup=back_button())
    
    elif call.data == "refer":
        user = db.get_user(user_id)
        ref_link = f"https://t.me/{Config.BOT_USERNAME}?start=ref_{user_id}"
        
        ref_text = style_text(f"""
👥 Rᴇғᴇʀ & Eᴀʀɴ

Yᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ:
{ref_link}

🔹 Rᴇғᴇʀ ʏᴏᴜʀ ғʀɪᴇɴᴅs ᴀɴᴅ ɢᴇᴛ {Config.REFERRAL_BONUS} ᴘᴏɪɴᴛs ғᴏʀ ᴇᴀᴄʜ ɴᴇᴡ ᴜsᴇʀ!
🔹 Tʜᴇʏ ᴍᴜsᴛ ᴜsᴇ ʏᴏᴜʀ ʟɪɴᴋ ᴛᴏ ᴊᴏɪɴ
🔹 Bᴏɴᴜs ᴡɪʟʟ ʙᴇ ᴄʀᴇᴅɪᴛᴇᴅ ᴏɴᴄᴇ ᴛʜᴇʏ ᴊᴏɪɴ

Rᴇғᴇʀʀᴇᴅ ʙʏ: {user['referred_by'] or 'Nᴏᴏɴᴇ'}
""")
        bot.edit_message_text(ref_text, chat_id, message_id, reply_markup=back_button())
    
    elif call.data == "stats":
        stats = db.get_stats()
        user = db.get_user(user_id)
        
        stats_text = style_text(f"""
📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs

👥 Tᴏᴛᴀʟ Usᴇʀs: {stats['total_users']}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {stats['total_orders']}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{stats['total_deposits']:.2f}

👤 Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ: {user['balance']} ᴘᴏɪɴᴛs
👤 Yᴏᴜʀ Oʀᴅᴇʀs: {len(db.get_user_orders(user_id))}
""")
        bot.edit_message_text(stats_text, chat_id, message_id, reply_markup=back_button())
    
    elif call.data == "support":
        bot.delete_message(chat_id, message_id)
        bot.send_photo(
            chat_id,
            photo="https://via.placeholder.com/500x300/0088cc/ffffff?text=Support",  # Replace with actual support image
            caption=style_text("""
📞 Cᴏɴᴛᴀᴄᴛ Oᴜʀ Sᴜᴘᴘᴏʀᴛ Tᴇᴀᴍ

Wᴇ'ʀᴇ ʜᴇʀᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ! Cʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴᴛᴀᴄᴛ ᴜs ᴏɴ WʜᴀᴛsAᴘᴘ.

Oᴜʀ sᴜᴘᴘᴏʀᴛ ʜᴏᴜʀs:
• Mᴏɴ - Sᴜɴ: 24/7
• Rᴇsᴘᴏɴsᴇ ᴛɪᴍᴇ: Wɪᴛʜɪɴ 15 ᴍɪɴᴜᴛᴇs
"""),
            reply_markup=support_keyboard()
        )
    
    elif call.data == "how_to_use":
        how_to_text = style_text("""
📖 Hᴏᴡ Tᴏ Usᴇ

1️⃣ 💰 Dᴇᴘᴏsɪᴛ
   • Cʟɪᴄᴋ ᴏɴ Dᴇᴘᴏsɪᴛ
   • Eɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ ɪɴ ₹
   • Sᴄᴀɴ QR ᴄᴏᴅᴇ ᴏʀ ᴜsᴇ UPI ʟɪɴᴋ
   • Cʟɪᴄᴏᴋ "Pᴀɪᴅ ✅" ᴀғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ

2️⃣ 🛒 Nᴇᴡ Oʀᴅᴇʀ
   • Sᴇʟᴇᴄᴛ ᴄᴀᴛᴇɢᴏʀʏ
   • Cʜᴏᴏsᴇ sᴇʀᴠɪᴄᴇ
   • Sᴇɴᴅ ʟɪɴᴋ
   • Eɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ
   • Oʀᴅᴇʀ ᴡɪʟʟ ʙᴇ ᴘʟᴀᴄᴇᴅ

3️⃣ 📋 Tʀᴀᴄᴋ Oʀᴅᴇʀ
   • Eɴᴛᴇʀ ᴏʀᴅᴇʀ ID
   • Vɪᴇᴡ ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs

Nᴇᴇᴅ ʜᴇʟᴘ? Cᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ!
""")
        bot.edit_message_text(how_to_text, chat_id, message_id, reply_markup=back_button())
    
    elif call.data == "restart":
        bot.delete_message(chat_id, message_id)
        start_command(call.message)
    
    elif call.data.startswith("paid_"):
        utr = call.data.replace("paid_", "")
        
        if utr in payment_sessions:
            session = payment_sessions[utr]
            amount = session['amount']
            user_id = session['user_id']
            
            # Verify payment
            if PaymentSystem.verify_payment(utr, amount):
                # Payment successful
                points = amount * 100  # Convert ₹ to points
                user = db.get_user(user_id)
                
                # Update user balance
                db.update_user(user_id, {
                    'balance': user['balance'] + points,
                    'total_deposits': user['total_deposits'] + amount
                })
                
                # Record deposit
                db.add_deposit({
                    'user_id': user_id,
                    'amount': amount,
                    'utr': utr,
                    'points': points,
                    'status': 'Cᴏᴍᴘʟᴇᴛᴇᴅ'
                })
                
                # Notify user
                bot.edit_message_text(
                    style_text(f"""
✅ Pᴀʏᴍᴇɴᴛ Sᴜᴄᴄᴇssғᴜʟ!

Aᴍᴏᴜɴᴛ: ₹{amount}
Pᴏɪɴᴛs ᴀᴅᴅᴇᴅ: {points}
Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {user['balance'] + points} ᴘᴏɪɴᴛs

Tʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ʏᴏᴜʀ ᴅᴇᴘᴏsɪᴛ!
"""),
                    chat_id, message_id,
                    reply_markup=back_button()
                )
                
                # Notify admin
                for admin_id in Config.ADMIN_IDS:
                    try:
                        bot.send_message(
                            admin_id,
                            style_text(f"""
💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ!

Usᴇʀ: {user_id}
Aᴍᴏᴜɴᴛ: ₹{amount}
UTR: {utr}
Pᴏɪɴᴛs: {points}
""")
                        )
                    except:
                        pass
                
                # Cleanup session
                del payment_sessions[utr]
                
            else:
                bot.answer_callback_query(call.id, style_text("❌ Pʟᴇᴀsᴇ ᴘᴀʏ ғɪʀsᴛ!"), show_alert=True)
        else:
            bot.answer_callback_query(call.id, style_text("❌ Sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ!"), show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Hᴀɴᴅʟᴇ ᴀʟʟ ᴛᴇxᴛ ᴍᴇssᴀɢᴇs"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    
    if state == UserState.WAITING_DEPOSIT_AMOUNT:
        try:
            amount = float(message.text)
            if amount < 10:
                bot.send_message(chat_id, style_text("Mɪɴɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ ɪs ₹10!"), reply_markup=back_button())
                return
            
            # Generate UTR and payment details
            utr = generate_utr()
            upi_link = PaymentSystem.generate_upi_link(amount, utr)
            qr_image = PaymentSystem.generate_qr_code(upi_link)
            
            # Store payment session
            payment_sessions[utr] = {
                'user_id': user_id,
                'amount': amount,
                'created_at': datetime.now()
            }
            
            # Send QR code and payment details
            bot.send_photo(
                chat_id,
                photo=qr_image,
                caption=style_text(f"""
💰 Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ

Aᴍᴏᴜɴᴛ: ₹{amount}
UTR: {utr}

Sᴄᴀɴ ᴛʜᴇ QR ᴄᴏᴅᴇ ᴏʀ ᴜsᴇ ᴜᴘɪ ʟɪɴᴋ ᴛᴏ ᴘᴀʏ.

Aғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ, ᴄʟɪᴄᴋ "Pᴀɪᴅ ✅" ʙᴜᴛᴛᴏɴ.
"""),
                reply_markup=paid_button(utr)
            )
            
            del user_states[user_id]
            
        except ValueError:
            bot.send_message(chat_id, style_text("Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ!"), reply_markup=back_button())
    
    elif isinstance(state, dict) and state.get('state') == UserState.WAITING_ORDER_LINK:
        link = message.text.strip()
        service = state['service']
        
        user_states[user_id] = {
            'state': UserState.WAITING_ORDER_QUANTITY,
            'service': service,
            'link': link
        }
        
        bot.send_message(
            chat_id,
            style_text(f"""
🛒 {service['name']}

Lɪɴᴋ: {link}

Nᴏᴡ ᴇɴᴛᴇʀ ᴛʜᴇ ǫᴜᴀɴᴛɪᴛʏ:

Mɪɴ: {service['min']}
Mᴀx: {service['max']}
Uɴɪᴛ: {service['unit']}
"""),
            reply_markup=back_button()
        )
    
    elif isinstance(state, dict) and state.get('state') == UserState.WAITING_ORDER_QUANTITY:
        try:
            quantity = int(message.text)
            service = state['service']
            link = state['link']
            
            # Validate quantity
            is_valid, error_msg = validate_quantity(quantity, service)
            if not is_valid:
                bot.send_message(chat_id, error_msg, reply_markup=back_button())
                return
            
            # Calculate cost
            cost = calculate_order_cost(quantity, service)
            user = db.get_user(user_id)
            
            # Check balance
            if user['balance'] < cost:
                bot.send_message(
                    chat_id,
                    style_text(f"""
❌ Iɴsᴜғғɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ!

Rᴇǫᴜɪʀᴇᴅ: {cost} ᴘᴏɪɴᴛs
Yᴏᴜʀ ʙᴀʟᴀɴᴄᴇ: {user['balance']} ᴘᴏɪɴᴛs

Pʟᴇᴀsᴇ ᴅᴇᴘᴏsɪᴛ ғᴜɴᴅs ғɪʀsᴛ.
"""),
                    reply_markup=back_button()
                )
                del user_states[user_id]
                return
            
            # Place order with SMM API
            api_result = OrderSystem.place_smm_order(service['id'], link, quantity)
            
            if api_result.get('status') == 'success':
                # Deduct balance
                db.update_user(user_id, {
                    'balance': user['balance'] - cost,
                    'total_spent': user['total_spent'] + cost
                })
                
                # Save order
                order_data = {
                    'user_id': user_id,
                    'service_id': service['id'],
                    'service_name': service['name'],
                    'link': link,
                    'quantity': quantity,
                    'cost': cost,
                    'api_order_id': api_result.get('order', ''),
                    'status': 'Pᴇɴᴅɪɴɢ'
                }
                
                order_id = db.add_order(order_data)
                
                # Send order confirmation
                order_summary = create_order_summary(
                    {**order_data, 'order_id': order_id},
                    service,
                    cost
                )
                
                bot.send_message(chat_id, order_summary, reply_markup=main_menu())
                
                # Notify admin
                for admin_id in Config.ADMIN_IDS:
                    try:
                        keyboard = InlineKeyboardMarkup()
                        keyboard.row(InlineKeyboardButton(
                            style_text("Bᴏᴛ Hᴇʀᴇ 🈴"), 
                            url=f"https://t.me/{Config.BOT_USERNAME}"
                        ))
                        
                        bot.send_message(
                            admin_id,
                            style_text(f"""
🛒 Nᴇᴡ Oʀᴅᴇʀ!

Usᴇʀ: {user_id}
Sᴇʀᴠɪᴄᴇ: {service['name']}
Oʀᴅᴇʀ ID: {order_id}
Lɪɴᴋ: {link}
Qᴜᴀɴᴛɪᴛʏ: {quantity}
Cᴏsᴛ: {cost} ᴘᴏɪɴᴛs
"""),
                            reply_markup=keyboard
                        )
                    except:
                        pass
                
            else:
                bot.send_message(
                    chat_id,
                    style_text("❌ Eʀʀᴏʀ ᴘʟᴀᴄɪɴɢ ᴏʀᴅᴇʀ! Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."),
                    reply_markup=back_button()
                )
            
            del user_states[user_id]
            
        except ValueError:
            bot.send_message(chat_id, style_text("Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ!"), reply_markup=back_button())
    
    elif state == UserState.WAITING_TRACK_ORDER:
        order_id = message.text.strip()
        order = db.get_order(order_id)
        
        if not order:
            bot.send_message(
                chat_id,
                style_text("❌ Oʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ! Pʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ Oʀᴅᴇʀ ID."),
                reply_markup=back_button()
            )
            return
        
        # Get latest status from SMM API
        api_status = OrderSystem.get_order_status(order.get('api_order_id', ''))
        current_status = api_status.get('status', order['status'])
        
        # Update order status
        db.update_order(order_id, {'status': current_status})
        
        track_text = style_text(f"""
📋 Oʀᴅᴇʀ Tʀᴀᴄᴋɪɴɢ

Sᴇʀᴠɪᴄᴇ: {order['service_name']}
Oʀᴅᴇʀ ID: {order_id}
API Oʀᴅᴇʀ ID: {order.get('api_order_id', 'N/A')}
Lɪɴᴋ: {order['link']}
Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
Cᴏsᴛ: {order['cost']} ᴘᴏɪɴᴛs
Sᴛᴀᴛᴜs: {current_status}

Uᴘᴅᴀᴛᴇᴅ: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
""")
        
        bot.send_message(chat_id, track_text, reply_markup=main_menu())
        del user_states[user_id]

@bot.message_handler(commands=['admin'])
def admin_command(message):
    """Aᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅ"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.send_message(message.chat.id, style_text("❌ Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ!"))
        return
    
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(style_text("📢 Bʀᴏᴀᴅᴄᴀsᴛ"), callback_data="admin_broadcast"),
        InlineKeyboardButton(style_text("📊 Vɪᴇᴡ Sᴛᴀᴛs"), callback_data="admin_stats")
    )
    keyboard.row(
        InlineKeyboardButton(
            style_text("⚙️ Bᴏᴛ Cᴏɴᴛʀᴏʟ") + f" ({'ON' if db.bot_enabled else 'OFF'})",
            callback_data="admin_toggle_bot"
        )
    )
    
    bot.send_message(
        message.chat.id,
        style_text("👑 Aᴅᴍɪɴ Pᴀɴᴇʟ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:"),
        reply_markup=keyboard
    )

# Background refund system
def refund_system():
    """Bᴀᴄᴋɢʀᴏᴜɴᴅ ʀᴇғᴜɴᴅ sʏsᴛᴇᴍ"""
    while True:
        try:
            # Check orders every 30 minutes
            time.sleep(1800)  # 30 minutes
            
            for order in db.orders:
                if order['status'] in ['Pᴇɴᴅɪɴɢ', 'Iɴ Pʀᴏɢʀᴇss']:
                    # Get latest status from API
                    api_status = OrderSystem.get_order_status(order.get('api_order_id', ''))
                    current_status = api_status.get('status', order['status'])
                    
                    if current_status in ['Cᴀɴᴄᴇʟʟᴇᴅ', 'Pᴀʀᴛɪᴀʟ']:
                        # Calculate refund
                        user = db.get_user(order['user_id'])
                        refund_amount = order['cost']
                        
                        if current_status == 'Pᴀʀᴛɪᴀʟ':
                            # Partial refund logic (simplified)
                            remains = int(api_status.get('remains', 0))
                            if remains > 0:
                                service = next((s for s in Config.SERVICES if s['id'] == order['service_id']), None)
                                if service:
                                    refund_amount = calculate_order_cost(remains, service)
                        
                        # Process refund
                        db.update_user(order['user_id'], {
                            'balance': user['balance'] + refund_amount
                        })
                        
                        db.update_order(order['order_id'], {
                            'status': current_status,
                            'refund_amount': refund_amount
                        })
                        
                        # Notify user
                        try:
                            bot.send_message(
                                order['user_id'],
                                style_text(f"""
💰 Rᴇғᴜɴᴅ Pʀᴏᴄᴇssᴇᴅ!

Oʀᴅᴇʀ ID: {order['order_id']}
Sᴛᴀᴛᴜs: {current_status}
Rᴇғᴜɴᴅᴇᴅ: {refund_amount} ᴘᴏɪɴᴛs
Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {user['balance'] + refund_amount} ᴘᴏɪɴᴛs
""")
                            )
                        except:
                            pass
                        
                        # Notify admin
                        for admin_id in Config.ADMIN_IDS:
                            try:
                                bot.send_message(
                                    admin_id,
                                    style_text(f"""
💰 Rᴇғᴜɴᴅ Pʀᴏᴄᴇssᴇᴅ

Usᴇʀ: {order['user_id']}
Oʀᴅᴇʀ: {order['order_id']}
Sᴇʀᴠɪᴄᴇ: {order['service_name']}
Rᴇғᴜɴᴅ: {refund_amount} ᴘᴏɪɴᴛs
Sᴛᴀᴛᴜs: {current_status}
""")
                                )
                            except:
                                pass
        
        except Exception as e:
            print(f"Refund system error: {e}")

# Start refund system in background thread
refund_thread = threading.Thread(target=refund_system, daemon=True)
refund_thread.start()

if __name__ == "__main__":
    print(style_text("Bᴏᴛ sᴛᴀʀᴛᴇᴅ..."))
    bot.infinity_polling()
