from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import style_text
import services
from database import is_bot_accepting_orders

# Main Menu Keyboards
def main_menu_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(style_text("💰 Dᴇᴘᴏsɪᴛ"), callback_data="deposit"),
        InlineKeyboardButton(style_text("🛒 Nᴇᴡ Oʀᴅᴇʀ"), callback_data="order_menu")
    )
    markup.add(
        InlineKeyboardButton(style_text("📋 Oʀᴅᴇʀs"), callback_data="history"),
        InlineKeyboardButton(style_text("👥 Rᴇғᴇʀ"), callback_data="refer")
    )
    markup.add(
        InlineKeyboardButton(style_text("👤 Aᴄᴄᴏᴜɴᴛ"), callback_data="account"),
        InlineKeyboardButton(style_text("📊 Sᴛᴀᴛs"), callback_data="stats")
    )
    markup.add(InlineKeyboardButton(style_text("ℹ️ Sᴜᴘᴘᴏʀᴛ"), callback_data="support"))
    markup.row(
        InlineKeyboardButton(style_text("Hᴏᴡ Tᴏ Usᴇ"), callback_data="how_to_use"),
        InlineKeyboardButton(style_text("Rᴇsᴛᴀʀᴛ"), callback_data="restart")
    )
    return markup

def back_button_only():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="main_menu"))
    return markup

def service_category_keyboard():
    markup = InlineKeyboardMarkup()
    categories = services.get_categories()
    
    for category in categories:
        emoji = "📱" if "instagram" in category.lower() else "📺" if "youtube" in category.lower() else "📢"
        markup.add(InlineKeyboardButton(
            f"{emoji} {style_text(category)}", 
            callback_data=f"category_{category}"
        ))
    
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="main_menu"))
    return markup

def services_keyboard(category):
    markup = InlineKeyboardMarkup()
    services_list = services.get_services_by_category(category)
    
    for service in services_list:
        price = service["price_per_unit"]
        unit = service["unit"]
        button_text = f"{style_text(service['name'])} - {price}ᴘ/{unit}"
        markup.add(InlineKeyboardButton(
            button_text, 
            callback_data=f"service_{service['id']}"
        ))
    
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="order_menu"))
    return markup

def channel_join_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("✅ Jᴏɪɴ Cʜᴀɴɴᴇʟ"), url="https://t.me/prooflelo1"))
    markup.add(InlineKeyboardButton(style_text("🔃 Cʜᴇᴄᴋ"), callback_data="check_join"))
    return markup

def support_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("📞 Cᴏɴᴛᴀᴄᴛ Us"), url="https://wa.me/639941532149"))
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="main_menu"))
    return markup

def deposit_confirmation_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("✅ I Hᴀᴠᴇ Pᴀɪᴅ"), callback_data="confirm_deposit"))
    markup.add(InlineKeyboardButton(style_text("❌ Cᴀɴᴄᴇʟ"), callback_data="main_menu"))
    return markup

def order_confirmation_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("✅ Cᴏɴғɪʀᴍ"), callback_data="confirm_order"))
    markup.add(InlineKeyboardButton(style_text("❌ Cᴀɴᴄᴇʟ"), callback_data="order_menu"))
    return markup

# Admin Keyboards
def admin_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(style_text("📦 Mᴀɴᴀɢᴇ Sᴇʀᴠɪᴄᴇs"), callback_data="admin_manage_services"),
        InlineKeyboardButton(style_text("💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ"), callback_data="admin_balance_control")
    )
    markup.add(
        InlineKeyboardButton(style_text("👥 Usᴇʀ Cᴏɴᴛʀᴏʟ"), callback_data="admin_user_control"),
        InlineKeyboardButton(style_text("📢 Bʀᴏᴀᴅᴄᴀsᴛ"), callback_data="admin_broadcast")
    )
    markup.add(
        InlineKeyboardButton(style_text("⚙️ Bᴏᴛ Cᴏɴᴛʀᴏʟ"), callback_data="admin_bot_control"),
        InlineKeyboardButton(style_text("📊 Sᴛᴀᴛs"), callback_data="admin_stats")
    )
    markup.add(InlineKeyboardButton(style_text("🔙 Mᴀɪɴ Mᴇɴᴜ"), callback_data="main_menu"))
    return markup

def admin_services_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("➕ Aᴅᴅ Sᴇʀᴠɪᴄᴇ"), callback_data="admin_add_service"))
    markup.add(InlineKeyboardButton(style_text("✏️ Eᴅɪᴛ Sᴇʀᴠɪᴄᴇ"), callback_data="admin_edit_service"))
    markup.add(InlineKeyboardButton(style_text("❌ Dᴇʟᴇᴛᴇ Sᴇʀᴠɪᴄᴇ"), callback_data="admin_delete_service"))
    markup.add(InlineKeyboardButton(style_text("🔙 Aᴅᴍɪɴ Mᴇɴᴜ"), callback_data="admin_menu"))
    return markup

def admin_balance_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("➕ Aᴅᴅ Bᴀʟᴀɴᴄᴇ"), callback_data="admin_add_balance"))
    markup.add(InlineKeyboardButton(style_text("➖ Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ"), callback_data="admin_deduct_balance"))
    markup.add(InlineKeyboardButton(style_text("🔙 Aᴅᴍɪɴ Mᴇɴᴜ"), callback_data="admin_menu"))
    return markup

def admin_user_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("🔨 Bᴀɴ Usᴇʀ"), callback_data="admin_ban_user"))
    markup.add(InlineKeyboardButton(style_text("✅ Uɴʙᴀɴ Usᴇʀ"), callback_data="admin_unban_user"))
    markup.add(InlineKeyboardButton(style_text("🔙 Aᴅᴍɪɴ Mᴇɴᴜ"), callback_data="admin_menu"))
    return markup

def admin_bot_control_keyboard():
    bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("🟢 Tᴜʀɴ Bᴏᴛ ON"), callback_data="admin_bot_on"))
    markup.add(InlineKeyboardButton(style_text("🔴 Tᴜʀɴ Bᴏᴛ OFF"), callback_data="admin_bot_off"))
    markup.add(InlineKeyboardButton(style_text(f"📊 Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: {bot_status}"), callback_data="admin_bot_status"))
    markup.add(InlineKeyboardButton(style_text("🔙 Aᴅᴍɪɴ Mᴇɴᴜ"), callback_data="admin_menu"))
    return markup

def services_list_keyboard(action):
    """Services list for admin actions"""
    markup = InlineKeyboardMarkup()
    all_services = services.get_all_services()
    
    for service in all_services:
        service_name = style_text(service['name'][:30])
        markup.add(InlineKeyboardButton(
            service_name, 
            callback_data=f"admin_{action}_{service['id']}"
        ))
    
    markup.add(InlineKeyboardButton(style_text("🔙 Bᴀᴄᴋ"), callback_data="admin_manage_services"))
    return markup

def confirm_delete_keyboard(service_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("✅ Yᴇs, Dᴇʟᴇᴛᴇ"), callback_data=f"admin_confirm_delete_{service_id}"))
    markup.add(InlineKeyboardButton(style_text("❌ Cᴀɴᴄᴇʟ"), callback_data="admin_manage_services"))
    return markup

def broadcast_confirmation_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(style_text("✅ Yᴇs, Sᴇɴᴅ"), callback_data="admin_confirm_broadcast"))
    markup.add(InlineKeyboardButton(style_text("❌ Cᴀɴᴄᴇʟ"), callback_data="admin_menu"))
    return markup
