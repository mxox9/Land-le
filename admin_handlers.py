import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (
    users_collection, orders_collection, deposits_collection,
    update_user_balance, get_user, log_admin_action,
    set_bot_accepting_orders, is_bot_accepting_orders
)
from services import services_list, add_service, update_service, delete_service, get_all_services
from utils import style_text, is_admin
from keyboards import (
    admin_main_keyboard, admin_services_keyboard, admin_balance_keyboard,
    admin_user_keyboard, admin_bot_control_keyboard, services_list_keyboard,
    confirm_delete_keyboard, broadcast_confirmation_keyboard
)

# Admin states for conversation flow
admin_states = {}

def setup_admin_handlers(bot):
    """Setup all admin handlers"""
    
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        user_id = message.chat.id
        admin_ids = [int(x) for x in os.getenv('ADMIN_IDS', '6052975324').split(',')]
        
        if not is_admin(user_id, admin_ids):
            bot.reply_to(message, style_text("❌ Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ."))
            return
        
        total_users = users_collection.count_documents({})
        total_orders = orders_collection.count_documents({})
        total_deposits = deposits_collection.aggregate([
            {"$match": {"status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        total_deposit = list(total_deposits)[0]['total'] if total_deposits else 0
        bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
        
        text = style_text(f"""
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

👤 Usᴇʀs: {total_users}
🛒 Oʀᴅᴇʀs: {total_orders}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposit:.2f}
📱 Aᴄᴛɪᴠᴇ Sᴇʀᴠɪᴄᴇs: {len(get_all_services())}
⚙️ Bᴏᴛ Sᴛᴀᴛᴜs: {bot_status}

Cʜᴏᴏsᴇ ᴀɴ ᴀᴄᴛɪᴏɴ:
        """)
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def handle_admin_callbacks(call):
        user_id = call.message.chat.id
        admin_ids = [int(x) for x in os.getenv('ADMIN_IDS', '6052975324').split(',')]
        
        if not is_admin(user_id, admin_ids):
            bot.answer_callback_query(call.id, style_text("❌ Nᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!"), show_alert=True)
            return
        
        try:
            if call.data == "admin_menu":
                show_admin_menu(bot, call)
            
            elif call.data == "admin_manage_services":
                show_admin_services_menu(bot, call)
            
            elif call.data == "admin_balance_control":
                show_admin_balance_menu(bot, call)
            
            elif call.data == "admin_user_control":
                show_admin_user_menu(bot, call)
            
            elif call.data == "admin_broadcast":
                start_admin_broadcast(bot, call)
            
            elif call.data == "admin_bot_control":
                show_admin_bot_control(bot, call)
            
            elif call.data == "admin_stats":
                show_admin_stats(bot, call)
            
            elif call.data == "admin_add_service":
                start_add_service(bot, call)
            
            elif call.data == "admin_edit_service":
                show_services_for_edit(bot, call)
            
            elif call.data == "admin_delete_service":
                show_services_for_delete(bot, call)
            
            elif call.data.startswith("admin_edit_"):
                service_id = call.data.replace("admin_edit_", "")
                start_edit_service(bot, call, service_id)
            
            elif call.data.startswith("admin_delete_"):
                service_id = call.data.replace("admin_delete_", "")
                confirm_delete_service(bot, call, service_id)
            
            elif call.data.startswith("admin_confirm_delete_"):
                service_id = call.data.replace("admin_confirm_delete_", "")
                delete_service_handler(bot, call, service_id)
            
            elif call.data == "admin_add_balance":
                start_add_balance(bot, call)
            
            elif call.data == "admin_deduct_balance":
                start_deduct_balance(bot, call)
            
            elif call.data == "admin_ban_user":
                start_ban_user(bot, call)
            
            elif call.data == "admin_unban_user":
                start_unban_user(bot, call)
            
            elif call.data == "admin_bot_on":
                set_bot_status(bot, call, True)
            
            elif call.data == "admin_bot_off":
                set_bot_status(bot, call, False)
            
            elif call.data == "admin_bot_status":
                show_bot_status(bot, call)
            
            elif call.data == "admin_confirm_broadcast":
                confirm_broadcast(bot, call)
                
        except Exception as e:
            print(f"Admin callback error: {e}")
            bot.answer_callback_query(call.id, style_text("❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!"))

    # Admin menu functions
    def show_admin_menu(bot, call):
        admin_panel(call.message)

    def show_admin_services_menu(bot, call):
        user_id = call.message.chat.id
        text = style_text("📱 Sᴇʀᴠɪᴄᴇs Mᴀɴᴀɢᴇᴍᴇɴᴛ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ:")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=admin_services_keyboard()
            )
        except:
            bot.send_message(user_id, text, reply_markup=admin_services_keyboard())

    def show_admin_balance_menu(bot, call):
        user_id = call.message.chat.id
        text = style_text("💰 Bᴀʟᴀɴᴄᴇ Cᴏɴᴛʀᴏʟ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ:")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=admin_balance_keyboard()
            )
        except:
            bot.send_message(user_id, text, reply_markup=admin_balance_keyboard())

    def show_admin_user_menu(bot, call):
        user_id = call.message.chat.id
        text = style_text("👤 Usᴇʀ Cᴏɴᴛʀᴏʟ\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ:")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=admin_user_keyboard()
            )
        except:
            bot.send_message(user_id, text, reply_markup=admin_user_keyboard())

    def show_admin_bot_control(bot, call):
        user_id = call.message.chat.id
        bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
        text = style_text(f"⚙️ Bᴏᴛ Cᴏɴᴛʀᴏʟ\n\nCᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: {bot_status}\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ:")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=admin_bot_control_keyboard()
            )
        except:
            bot.send_message(user_id, text, reply_markup=admin_bot_control_keyboard())

    def show_admin_stats(bot, call):
        user_id = call.message.chat.id
        total_users = users_collection.count_documents({})
        total_orders = orders_collection.count_documents({})
        total_deposits = deposits_collection.aggregate([
            {"$match": {"status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        total_deposit = list(total_deposits)[0]['total'] if total_deposits else 0
        active_services = len(get_all_services())
        
        text = style_text(f"""
📊 Aᴅᴍɪɴ Sᴛᴀᴛɪsᴛɪᴄs

👤 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
📱 Aᴄᴛɪᴠᴇ Sᴇʀᴠɪᴄᴇs: {active_services}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposit:.2f}
        """)
        
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=admin_main_keyboard()
            )
        except:
            bot.send_message(user_id, text, reply_markup=admin_main_keyboard())

    # Service Management Functions
    def start_add_service(bot, call):
        user_id = call.message.chat.id
        admin_states[user_id] = {"action": "adding_service", "step": "category"}
        
        text = style_text("📱 Aᴅᴅ Nᴇᴡ Sᴇʀᴠɪᴄᴇ\n\nEɴᴛᴇʀ ᴄᴀᴛᴇɢᴏʀʏ ɴᴀᴍᴇ:")
        bot.send_message(user_id, text)
        bot.register_next_step_handler(call.message, process_add_service_category)

    def process_add_service_category(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
            return
        
        admin_states[user_id]["category"] = message.text.strip()
        admin_states[user_id]["step"] = "name"
        
        bot.send_message(user_id, style_text("📱 Eɴᴛᴇʀ sᴇʀᴠɪᴄᴇ ɴᴀᴍᴇ:"))

    def process_add_service_name(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
            return
        
        admin_states[user_id]["name"] = message.text.strip()
        admin_states[user_id]["step"] = "description"
        
        bot.send_message(user_id, style_text("📝 Eɴᴛᴇʀ sᴇʀᴠɪᴄᴇ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:"))

    def process_add_service_description(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
            return
        
        admin_states[user_id]["description"] = message.text.strip()
        admin_states[user_id]["step"] = "min_quantity"
        
        bot.send_message(user_id, style_text("🔢 Eɴᴛᴇʀ ᴍɪɴɪᴍᴜᴍ ǫᴜᴀɴᴛɪᴛʏ:"))

    # Continue with other process functions...

    def show_services_for_edit(bot, call):
        user_id = call.message.chat.id
        text = style_text("✏️ Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴇᴅɪᴛ:")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=services_list_keyboard("edit")
            )
        except:
            bot.send_message(user_id, text, reply_markup=services_list_keyboard("edit"))

    # Similar functions for other admin operations...

    return bot
