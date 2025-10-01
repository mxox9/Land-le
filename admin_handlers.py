import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from database import (
    users_collection, orders_collection, deposits_collection,
    update_user_balance, get_user, log_admin_action,
    set_bot_accepting_orders, is_bot_accepting_orders,
    get_total_users, get_total_orders, get_total_deposits
)
import services
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
        
        total_users = get_total_users()
        total_orders = get_total_orders()
        total_deposit = get_total_deposits()
        bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
        
        text = style_text(f"""
👑 Aᴅᴍɪɴ Pᴀɴᴇʟ

👤 Usᴇʀs: {total_users}
🛒 Oʀᴅᴇʀs: {total_orders}
💰 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛs: ₹{total_deposit:.2f}
📱 Aᴄᴛɪᴠᴇ Sᴇʀᴠɪᴄᴇs: {len(services.get_all_services())}
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
        total_users = get_total_users()
        total_orders = get_total_orders()
        total_deposit = get_total_deposits()
        active_services = len(services.get_all_services())
        
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

    def process_add_service_min_quantity(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
            return
        
        try:
            min_quantity = int(message.text.strip())
            admin_states[user_id]["min_quantity"] = min_quantity
            admin_states[user_id]["step"] = "max_quantity"
            
            bot.send_message(user_id, style_text("🔢 Eɴᴛᴇʀ ᴍᴀxɪᴍᴜᴍ ǫᴜᴀɴᴛɪᴛʏ:"))
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def process_add_service_max_quantity(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
            return
        
        try:
            max_quantity = int(message.text.strip())
            admin_states[user_id]["max_quantity"] = max_quantity
            admin_states[user_id]["step"] = "unit"
            
            bot.send_message(user_id, style_text("📦 Eɴᴛᴇʀ ᴜɴɪᴛ (100 ᴏʀ 1000):"))
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def process_add_service_unit(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
            return
        
        try:
            unit = int(message.text.strip())
            if unit not in [100, 1000]:
                bot.send_message(user_id, style_text("❌ Uɴɪᴛ ᴍᴜsᴛ ʙᴇ 100 ᴏʀ 1000!"))
                return
            
            admin_states[user_id]["unit"] = unit
            admin_states[user_id]["step"] = "price"
            
            bot.send_message(user_id, style_text("💰 Eɴᴛᴇʀ ᴘʀɪᴄᴇ ᴘᴇʀ ᴜɴɪᴛ (ɪɴ ᴘᴏɪɴᴛs):"))
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴑ ᴜɴɪᴛ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def process_add_service_price(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
            return
        
        try:
            price = int(message.text.strip())
            admin_states[user_id]["price"] = price
            admin_states[user_id]["step"] = "service_id"
            
            bot.send_message(user_id, style_text("🆔 Eɴᴛᴇʀ sᴇʀᴠɪᴄᴇ ID (API sᴇʀᴠɪᴄᴇ ID):"))
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ᴘʀɪᴄᴇ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def process_add_service_id(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_service":
            return
        
        service_id = message.text.strip()
        admin_states[user_id]["service_id"] = service_id
        
        # Save the service
        data = admin_states[user_id]
        service_data = {
            "category": data["category"],
            "name": data["name"],
            "description": data.get("description", ""),
            "min": data.get("min_quantity", 100),
            "max": data.get("max_quantity", 1000),
            "unit": data.get("unit", 100),
            "price_per_unit": data.get("price", 10),
            "service_id": service_id,
            "active": True
        }
        
        # Add service to memory
        new_id = services.add_service(service_data)
        
        # Clear state
        del admin_states[user_id]
        
        text = style_text(f"""
✅ Sᴇʀᴠɪᴄᴇ Aᴅᴅᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

📱 Cᴀᴛᴇɢᴏʀʏ: {service_data['category']}
📱 Nᴀᴍᴇ: {service_data['name']}
📝 Dᴇsᴄʀɪᴘᴛɪᴏɴ: {service_data['description']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {service_data['min']}-{service_data['max']}
📦 Uɴɪᴛ: {service_data['unit']}
💰 Pʀɪᴄᴇ: {service_data['price_per_unit']} ᴘᴏɪɴᴛs/ᴜɴɪᴛ
🆔 Sᴇʀᴠɪᴄᴇ ID: {service_data['service_id']}
        """)
        
        bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        log_admin_action(user_id, "add_service", f"Service: {service_data['name']}")

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

    def show_services_for_delete(bot, call):
        user_id = call.message.chat.id
        text = style_text("❌ Sᴇʟᴇᴄᴛ sᴇʀᴠɪᴄᴇ ᴛᴏ ᴅᴇʟᴇᴛᴇ:")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=services_list_keyboard("delete")
            )
        except:
            bot.send_message(user_id, text, reply_markup=services_list_keyboard("delete"))

    def start_edit_service(bot, call, service_id):
        user_id = call.message.chat.id
        service = services.get_service_by_id(service_id)
        
        if not service:
            bot.answer_callback_query(call.id, style_text("❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!"))
            return
        
        admin_states[user_id] = {
            "action": "editing_service",
            "service_id": service_id,
            "service": service
        }
        
        text = style_text(f"""
✏️ Eᴅɪᴛ Sᴇʀᴠɪᴄᴇ: {service['name']}

Rᴇᴘʟʏ ᴡɪᴛʜ ᴛʜᴇ ғɪᴇʟᴅ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴇᴅɪᴛ:
1. Nᴀᴍᴇ
2. Dᴇsᴄʀɪᴘᴛɪᴏɴ
3. Mɪɴ Qᴜᴀɴᴛɪᴛʏ
4. Mᴀx Qᴜᴀɴᴛɪᴛʏ
5. Uɴɪᴛ
6. Pʀɪᴄᴇ
7. Sᴇʀᴠɪᴄᴇ ID

Rᴇᴘʟʏ ᴡɪᴛʜ ɴᴜᴍʙᴇʀ (1-7):
        """)
        
        bot.send_message(user_id, text)
        bot.register_next_step_handler(call.message, process_edit_service_field)

    def process_edit_service_field(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "editing_service":
            return
        
        try:
            field_num = int(message.text.strip())
            field_map = {
                1: "name", 2: "description", 3: "min", 
                4: "max", 5: "unit", 6: "price_per_unit", 7: "service_id"
            }
            
            if field_num not in field_map:
                bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ғɪᴇʟᴅ ɴᴜᴍʙᴇʀ! Usᴇ 1-7."))
                return
            
            admin_states[user_id]["edit_field"] = field_map[field_num]
            
            field_names = {
                "name": "name", "description": "description", 
                "min": "minimum quantity", "max": "maximum quantity",
                "unit": "unit", "price_per_unit": "price per unit", 
                "service_id": "service ID"
            }
            
            bot.send_message(user_id, style_text(f"📱 Eɴᴛᴇʀ ɴᴇᴡ {field_names[field_map[field_num]]}:"))
            bot.register_next_step_handler(message, process_edit_service_value)
            
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ! Usᴇ ɴᴜᴍʙᴇʀs 1-7."))

    def process_edit_service_value(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "editing_service":
            return
        
        data = admin_states[user_id]
        new_value = message.text.strip()
        field = data["edit_field"]
        service_id = data["service_id"]
        
        # Validate numeric fields
        if field in ["min", "max", "unit", "price_per_unit"]:
            try:
                new_value = int(new_value)
            except ValueError:
                bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ғᴏʀᴍᴀᴛ!"))
                return
        
        # Update service
        updates = {field: new_value}
        if services.update_service(service_id, updates):
            # Clear state
            del admin_states[user_id]
            
            bot.send_message(user_id, style_text(f"✅ Sᴇʀᴠɪᴄᴇ {field} ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!"), 
                            reply_markup=admin_main_keyboard())
            
            log_admin_action(user_id, "edit_service", f"Service ID: {service_id}, Field: {field}")
        else:
            bot.send_message(user_id, style_text("❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴜᴘᴅᴀᴛᴇ sᴇʀᴠɪᴄᴇ!"))

    def confirm_delete_service(bot, call, service_id):
        user_id = call.message.chat.id
        service = services.get_service_by_id(service_id)
        
        if not service:
            bot.answer_callback_query(call.id, style_text("❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!"))
            return
        
        text = style_text(f"""
❌ Cᴏɴғɪʀᴍ Dᴇʟᴇᴛɪᴏɴ

Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜɪs sᴇʀᴠɪᴄᴇ?

📱 Sᴇʀᴠɪᴄᴇ: {service['name']}
📂 Cᴀᴛᴇɢᴏʀʏ: {service['category']}
💰 Pʀɪᴄᴇ: {service['price_per_unit']} ᴘᴏɪɴᴛs

Tʜɪs ᴀᴄᴛɪᴏɴ ᴄᴀɴɴᴏᴛ ʙᴇ ᴜɴᴅᴏɴᴇ!
        """)
        
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=confirm_delete_keyboard(service_id)
            )
        except:
            bot.send_message(user_id, text, reply_markup=confirm_delete_keyboard(service_id))

    def delete_service_handler(bot, call, service_id):
        user_id = call.message.chat.id
        service = services.get_service_by_id(service_id)
        
        if not service:
            bot.answer_callback_query(call.id, style_text("❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!"))
            return
        
        service_name = service['name']
        if services.delete_service(service_id):
            text = style_text(f"✅ Sᴇʀᴠɪᴄᴇ '{service_name}' ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
            
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    text=text,
                    reply_markup=admin_main_keyboard()
                )
            except:
                bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
            
            log_admin_action(user_id, "delete_service", f"Service: {service_name}")
        else:
            bot.answer_callback_query(call.id, style_text("❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ sᴇʀᴠɪᴄᴇ!"), show_alert=True)

    def start_admin_broadcast(bot, call):
        user_id = call.message.chat.id
        admin_states[user_id] = {"action": "broadcasting", "step": "message"}
        
        text = style_text("📢 Bʀᴏᴀᴅᴄᴀsᴛ\n\nSᴇɴᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs:")
        bot.send_message(user_id, text)

    def process_broadcast_message(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "broadcasting":
            return
        
        broadcast_message = message.text
        admin_states[user_id]["broadcast_message"] = broadcast_message
        
        text = style_text(f"""
📢 Bʀᴏᴀᴅᴄᴀsᴛ Cᴏɴғɪʀᴍᴀᴛɪᴏɴ

Mᴇssᴀɢᴇ:
{broadcast_message}

Tʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ sᴇɴᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs. Cᴏɴғɪʀᴍ?
        """)
        
        bot.send_message(user_id, text, reply_markup=broadcast_confirmation_keyboard())

    def confirm_broadcast(bot, call):
        user_id = call.message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "broadcasting":
            return
        
        message_text = admin_states[user_id].get("broadcast_message")
        if not message_text:
            bot.answer_callback_query(call.id, style_text("❌ Nᴏ ᴍᴇssᴀɢᴇ ғᴏᴜɴᴅ!"), show_alert=True)
            return
        
        # Send broadcast
        if users_collection:
            users = users_collection.find({})
            success_count = 0
            fail_count = 0
            
            for user in users:
                try:
                    bot.send_message(user["user_id"], style_text(f"📢 Aɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ:\n\n{message_text}"))
                    success_count += 1
                    time.sleep(0.1)  # Rate limiting
                except Exception as e:
                    fail_count += 1
            
            report = style_text(f"""
📢 Bʀᴏᴀᴅᴄᴀsᴛ Rᴇᴘᴏʀᴛ

✅ Sᴜᴄᴄᴇss: {success_count}
❌ Fᴀɪʟᴇᴅ: {fail_count}
📊 Tᴏᴛᴀʟ: {success_count + fail_count}
            """)
        else:
            report = style_text("❌ Dᴀᴛᴀʙᴀsᴇ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ʙʀᴏᴀᴅᴄᴀsᴛ")
        
        bot.send_message(user_id, report, reply_markup=admin_main_keyboard())
        del admin_states[user_id]
        log_admin_action(user_id, "broadcast", f"Message: {message_text[:50]}...")

    def start_add_balance(bot, call):
        user_id = call.message.chat.id
        admin_states[user_id] = {"action": "adding_balance", "step": "user_id"}
        
        text = style_text("💰 Aᴅᴅ Bᴀʟᴀɴᴄᴇ\n\nSᴇɴᴅ Usᴇʀ ID:")
        bot.send_message(user_id, text)

    def process_add_balance_user_id(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_balance":
            return
        
        try:
            target_user_id = int(message.text.strip())
            admin_states[user_id]["target_user_id"] = target_user_id
            admin_states[user_id]["step"] = "amount"
            
            bot.send_message(user_id, style_text("💰 Eɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴀᴅᴅ (ɪɴ ᴘᴏɪɴᴛs):"))
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def process_add_balance_amount(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "adding_balance":
            return
        
        try:
            amount = int(message.text.strip())
            target_user_id = admin_states[user_id]["target_user_id"]
            
            # Add balance
            new_balance = update_user_balance(target_user_id, amount, is_deposit=True)
            
            # Clear state
            del admin_states[user_id]
            
            text = style_text(f"""
✅ Bᴀʟᴀɴᴄᴇ Aᴅᴅᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
💰 Aᴍᴏᴜɴᴛ Aᴅᴅᴇᴅ: {amount} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs
            """)
            
            bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
            log_admin_action(user_id, "add_balance", f"User: {target_user_id}, Amount: {amount}")
            
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def start_deduct_balance(bot, call):
        user_id = call.message.chat.id
        admin_states[user_id] = {"action": "deducting_balance", "step": "user_id"}
        
        text = style_text("💰 Dᴇᴅᴜᴄᴛ Bᴀʟᴀɴᴄᴇ\n\nSᴇɴᴅ Usᴇʀ ID:")
        bot.send_message(user_id, text)

    def process_deduct_balance_user_id(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "deducting_balance":
            return
        
        try:
            target_user_id = int(message.text.strip())
            admin_states[user_id]["target_user_id"] = target_user_id
            admin_states[user_id]["step"] = "amount"
            
            bot.send_message(user_id, style_text("💰 Eɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴅᴇᴅᴜᴄᴛ (ɪɴ ᴘᴏɪɴᴛs):"))
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def process_deduct_balance_amount(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "deducting_balance":
            return
        
        try:
            amount = int(message.text.strip())
            target_user_id = admin_states[user_id]["target_user_id"]
            
            # Check if user has sufficient balance
            current_balance = get_user(target_user_id)["balance_points"]
            if current_balance < amount:
                bot.send_message(user_id, style_text(f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ! Usᴇʀ ʜᴀs ᴏɴʟʏ {current_balance} ᴘᴏɪɴᴛs."))
                return
            
            # Deduct balance
            new_balance = update_user_balance(target_user_id, -amount, is_spent=True)
            
            # Clear state
            del admin_states[user_id]
            
            text = style_text(f"""
✅ Bᴀʟᴀɴᴄᴇ Dᴇᴅᴜᴄᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
💰 Aᴍᴏᴜɴᴛ Dᴇᴅᴜᴄᴛᴇᴅ: {amount} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs
            """)
            
            bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
            log_admin_action(user_id, "deduct_balance", f"User: {target_user_id}, Amount: {amount}")
            
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def start_ban_user(bot, call):
        user_id = call.message.chat.id
        admin_states[user_id] = {"action": "banning_user", "step": "user_id"}
        
        text = style_text("🔨 Bᴀɴ Usᴇʀ\n\nSᴇɴᴅ Usᴇʀ ID ᴛᴏ ʙᴀɴ:")
        bot.send_message(user_id, text)

    def process_ban_user(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "banning_user":
            return
        
        try:
            target_user_id = int(message.text.strip())
            
            # Ban user
            if users_collection:
                users_collection.update_one(
                    {"user_id": target_user_id},
                    {"$set": {"banned": True}},
                    upsert=True
                )
            
            # Clear state
            del admin_states[user_id]
            
            text = style_text(f"""
✅ Usᴇʀ Bᴀɴɴᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
🔨 Sᴛᴀᴛᴜs: Bᴀɴɴᴇᴅ
            """)
            
            bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
            log_admin_action(user_id, "ban_user", f"User: {target_user_id}")
            
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def start_unban_user(bot, call):
        user_id = call.message.chat.id
        admin_states[user_id] = {"action": "unbanning_user", "step": "user_id"}
        
        text = style_text("✅ Uɴʙᴀɴ Usᴇʀ\n\nSᴇɴᴅ Usᴇʀ ID ᴛᴏ ᴜɴʙᴀɴ:")
        bot.send_message(user_id, text)

    def process_unban_user(message):
        user_id = message.chat.id
        if user_id not in admin_states or admin_states[user_id].get("action") != "unbanning_user":
            return
        
        try:
            target_user_id = int(message.text.strip())
            
            # Unban user
            if users_collection:
                users_collection.update_one(
                    {"user_id": target_user_id},
                    {"$set": {"banned": False}}
                )
            
            # Clear state
            del admin_states[user_id]
            
            text = style_text(f"""
✅ Usᴇʀ Uɴʙᴀɴɴᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

👤 Usᴇʀ ID: {target_user_id}
✅ Sᴛᴀᴛᴜs: Aᴄᴛɪᴠᴇ
            """)
            
            bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
            log_admin_action(user_id, "unban_user", f"User: {target_user_id}")
            
        except ValueError:
            bot.send_message(user_id, style_text("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID! Usᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ."))

    def set_bot_status(bot, call, status):
        user_id = call.message.chat.id
        set_bot_accepting_orders(status)
        
        status_text = "🟢 ON" if status else "🔴 OFF"
        text = style_text(f"✅ Bᴏᴛ sᴛᴀᴛᴜs sᴇᴛ ᴛᴏ: {status_text}")
        
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=admin_main_keyboard()
            )
        except:
            bot.send_message(user_id, text, reply_markup=admin_main_keyboard())
        
        log_admin_action(user_id, "set_bot_status", f"Status: {status_text}")

    def show_bot_status(bot, call):
        user_id = call.message.chat.id
        bot_status = "🟢 ON" if is_bot_accepting_orders() else "🔴 OFF"
        
        text = style_text(f"⚙️ Cᴜʀʀᴇɴᴛ Bᴏᴛ Sᴛᴀᴛᴜs: {bot_status}")
        
        bot.answer_callback_query(call.id, text, show_alert=True)

    return bot
