from config import ADMIN_IDS, users, orders, ADMIN_IMAGE
from services import SERVICES, get_service_by_id
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def get_admin_keyboard():
    """Get admin panel inline keyboard"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📢 Bʀᴏᴀᴅᴄᴀsᴛ", callback_data="admin_broadcast"),
        InlineKeyboardButton("💰 Aᴅᴅ Bᴀʟᴀɴᴄᴇ", callback_data="admin_add_balance"),
        InlineKeyboardButton("💸 Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ", callback_data="admin_deduct_balance"),
        InlineKeyboardButton("👥 Bᴀɴ/Uɴʙᴀɴ", callback_data="admin_ban_user"),
        InlineKeyboardButton("📦 Sᴇʀᴠɪᴄᴇ Pʀɪᴄᴇ", callback_data="admin_service_price")
    )
    return keyboard

def show_admin_panel(bot, message):
    """Show admin panel"""
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

def handle_broadcast(bot, call):
    """Handle broadcast message"""
    bot.send_message(call.message.chat.id, "📢 Sᴇɴᴅ ᴛʜᴇ ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ:")
    bot.register_next_step_handler(call.message, process_broadcast)

def process_broadcast(bot, message):
    """Process and send broadcast message"""
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

def handle_add_balance(bot, call):
    """Handle add balance request"""
    bot.send_message(call.message.chat.id, "👤 Eɴᴛᴇʀ ᴜsᴇʀ ID:")
    bot.register_next_step_handler(call.message, process_user_id_for_balance, "add")

def handle_deduct_balance(bot, call):
    """Handle deduct balance request"""
    bot.send_message(call.message.chat.id, "👤 Eɴᴛᴇʀ ᴜsᴇʀ ID:")
    bot.register_next_step_handler(call.message, process_user_id_for_balance, "deduct")

def process_user_id_for_balance(bot, message, action):
    """Process user ID for balance operation"""
    try:
        user_id = int(message.text)
        bot.send_message(message.chat.id, f"💰 Eɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ ᴛᴏ {action}:")
        bot.register_next_step_handler(message, process_balance_amount, user_id, action)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID")

def process_balance_amount(bot, message, user_id, action):
    """Process balance amount"""
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

def get_service_selection_keyboard():
    """Get keyboard for service selection in admin panel"""
    keyboard = InlineKeyboardMarkup()
    for category, service_list in SERVICES.items():
        for service in service_list:
            keyboard.add(InlineKeyboardButton(
                f"{service['name']} - ₹{service['price']}", 
                callback_data=f"admin_service_{service['id']}"
            ))
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="admin_back"))
    return keyboard

def handle_service_price(bot, call):
    """Handle service price update"""
    bot.send_message(
        call.message.chat.id,
        "📦 Sᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ᴘʀɪᴄᴇ:",
        reply_markup=get_service_selection_keyboard()
    )

def handle_service_selection(bot, call, service_id):
    """Handle service selection for price update"""
    service = get_service_by_id(service_id)
    if service:
        bot.send_message(
            call.message.chat.id,
            f"🏷 Sᴇʀᴠɪᴄᴇ: {service['name']}\n💰 Cᴜʀʀᴇɴᴛ Pʀɪᴄᴇ: ₹{service['price']}\n\nEɴᴛᴇʀ ɴᴇᴡ ᴘʀɪᴄᴇ:"
        )
        bot.register_next_step_handler(call.message, process_new_price, service_id)
    else:
        bot.send_message(call.message.chat.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ")

def process_new_price(bot, message, service_id):
    """Process new price for service"""
    try:
        new_price = float(message.text)
        service = get_service_by_id(service_id)
        
        if service:
            service['price'] = new_price
            bot.send_message(
                message.chat.id,
                f"✅ Pʀɪᴄᴇ ᴜᴘᴅᴀᴛᴇᴅ!\n{service['name']} - ₹{new_price:.2f}"
            )
        else:
            bot.send_message(message.chat.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ")
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ Iɴᴠᴀʟɪᴅ ᴘʀɪᴄᴇ")
