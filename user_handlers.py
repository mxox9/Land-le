import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import services
from database import (
    get_user, update_user_balance, create_order, get_user_orders,
    get_order_by_id, is_bot_accepting_orders, users_collection, orders_collection
)
from utils import style_text, validate_amount, validate_quantity
from keyboards import (
    main_menu_keyboard, service_category_keyboard, services_keyboard,
    order_confirmation_keyboard, back_button_only, support_keyboard,
    deposit_confirmation_keyboard
)
from payment import create_payment, verify_payment, get_upi_payment_text
from smm_api import place_smm_order

# User states for conversation flow
user_states = {}

def setup_user_handlers(bot):
    """Setup all user handlers"""
    
    def check_channel_membership(user_id, channel_id):
        """Check if user is member of channel"""
        try:
            if channel_id.startswith('@'):
                channel_id = channel_id[1:]
            member = bot.get_chat_member(f"@{channel_id}", user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            print(f"Channel check error: {e}")
            return False

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.chat.id
        user_name = message.chat.first_name
        
        # Check if user is banned
        user = get_user(user_id)
        if user.get("banned"):
            bot.reply_to(message, style_text("❌ Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ."))
            return
        
        # Check channel membership
        channel_id = os.getenv('CHANNEL_ID', 'prooflelo1')
        if not check_channel_membership(user_id, channel_id):
            text = style_text(f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

📢 Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ:

@{channel_id}

Aғᴛᴇʀ ᴊᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴛʜᴇ ᴄʜᴇᴄᴋ ʙᴜᴛᴛᴏɴ.
            """)
            from keyboards import channel_join_keyboard
            bot.send_message(user_id, text, reply_markup=channel_join_keyboard())
            return
        
        # Show main menu
        text = style_text(f"""
👋 Wᴇʟᴄᴏᴍᴇ {user_name}!

🤖 I'ᴍ Mᴏsᴛ Aғғᴏʀᴅᴀʙʟᴇ Sᴏᴄɪᴀʟ Sᴇʀᴠɪᴄᴇs Bᴏᴛ. 
I ᴘʀᴏᴠɪᴅᴇ ᴄʜᴇᴀᴘ sᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ sᴇʀᴠɪᴄᴇs ᴀᴛ ᴛʜᴇ ʙᴇsᴛ ᴘʀɪᴄᴇs.

💰 Gᴇᴛ sᴛᴀʀᴛᴇᴅ ʙʏ ᴀᴅᴅɪɴɢ ғᴜɴᴅs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.
        """)
        
        bot.send_message(user_id, text, reply_markup=main_menu_keyboard())

    @bot.callback_query_handler(func=lambda call: not call.data.startswith('admin_'))
    def handle_user_callbacks(call):
        user_id = call.message.chat.id
        
        # Check if user is banned
        user = get_user(user_id)
        if user.get("banned"):
            bot.answer_callback_query(call.id, style_text("❌ Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ!"), show_alert=True)
            return
        
        try:
            if call.data == "main_menu":
                show_main_menu(bot, call)
            
            elif call.data == "deposit":
                start_deposit_process(bot, call)
            
            elif call.data == "order_menu":
                show_service_categories(bot, call)
            
            elif call.data == "history":
                show_order_history(bot, call)
            
            elif call.data == "refer":
                show_referral_info(bot, call)
            
            elif call.data == "account":
                show_account_info(bot, call)
            
            elif call.data == "stats":
                show_stats(bot, call)
            
            elif call.data == "support":
                show_support(bot, call)
            
            elif call.data == "how_to_use":
                show_how_to_use(bot, call)
            
            elif call.data == "restart":
                send_welcome(call.message)
            
            elif call.data.startswith("category_"):
                category = call.data.replace("category_", "")
                show_services(bot, call, category)
            
            elif call.data.startswith("service_"):
                service_id = call.data.replace("service_", "")
                start_order_process(bot, call, service_id)
            
            elif call.data == "confirm_order":
                confirm_order(bot, call)
            
            elif call.data == "confirm_deposit":
                process_deposit_confirmation(bot, call)
            
            elif call.data == "check_join":
                check_channel_join(bot, call)
                
        except Exception as e:
            print(f"User callback error: {e}")
            bot.answer_callback_query(call.id, style_text("❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!"))

    # User menu functions
    def show_main_menu(bot, call):
        user_id = call.message.chat.id
        user_name = call.from_user.first_name
        text = style_text(f"👋 Hᴇʟʟᴏ {user_name}!\n\nSᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ:")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=main_menu_keyboard()
            )
        except:
            bot.send_message(user_id, text, reply_markup=main_menu_keyboard())

    def start_deposit_process(bot, call):
        user_id = call.message.chat.id
        user_states[user_id] = {"action": "depositing", "step": "amount"}
        
        text = style_text("""
💵 Dᴇᴘᴏsɪᴛ Fᴜɴᴅs

💸 100 ᴘᴏɪɴᴛs = ₹1

Eɴᴛᴇʀ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇᴘᴏsɪᴛ (ɪɴ ʀᴜᴘᴇᴇs):
        """)
        
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text
            )
        except:
            bot.send_message(user_id, text)
        bot.register_next_step_handler(call.message, process_deposit_amount)

    def process_deposit_amount(message):
        user_id = message.chat.id
        if user_id not in user_states or user_states[user_id].get("action") != "depositing":
            return
        
        is_valid, result = validate_amount(message.text)
        if not is_valid:
            bot.send_message(user_id, style_text(result))
            return
        
        amount = result
        points = int(amount * 100)
        user_states[user_id]["amount"] = amount
        user_states[user_id]["points"] = points
        
        # Create payment
        payment_data = create_payment(amount, user_id)
        
        # Send payment instructions
        payment_text = get_upi_payment_text(amount, payment_data["upi_id"])
        
        bot.send_message(user_id, payment_text, reply_markup=deposit_confirmation_keyboard())

    def process_deposit_confirmation(bot, call):
        user_id = call.message.chat.id
        if user_id not in user_states or user_states[user_id].get("action") != "depositing":
            return
        
        data = user_states[user_id]
        amount = data["amount"]
        points = data["points"]
        
        # Verify payment
        verifying_msg = bot.send_message(user_id, "🔍 Vᴇʀɪғʏɪɴɢ ᴘᴀʏᴍᴇɴᴛ...")
        
        # For demo, we'll assume payment is verified
        # In real implementation, use actual verification
        payment_verified = True
        
        if payment_verified:
            # Add points to user balance
            new_balance = update_user_balance(user_id, points, is_deposit=True)
            
            text = style_text(f"""
✅ Dᴇᴘᴏsɪᴛ Sᴜᴄᴄᴇssғᴜʟ!

💵 Aᴍᴏᴜɴᴛ: ₹{amount}
💸 Pᴏɪɴᴛs Aᴅᴅᴇᴅ: {points} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs
            """)
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=verifying_msg.message_id,
                text=text,
                reply_markup=back_button_only()
            )
        else:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=verifying_msg.message_id,
                text=style_text("❌ Pᴀʏᴍᴇɴᴛ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ! Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ."),
                reply_markup=back_button_only()
            )
        
        del user_states[user_id]

    def show_service_categories(bot, call):
        user_id = call.message.chat.id
        
        if not is_bot_accepting_orders():
            bot.answer_callback_query(call.id, style_text("❌ Bᴏᴛ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ɴᴏᴛ ᴀᴄᴄᴇᴘᴛɪɴɢ ᴏʀᴅᴇʀs!"), show_alert=True)
            return
        
        text = style_text("🛒 Sᴇʟᴇᴄᴛ Cᴀᴛᴇɢᴏʀʏ:")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=service_category_keyboard()
            )
        except:
            bot.send_message(user_id, text, reply_markup=service_category_keyboard())

    def show_services(bot, call, category):
        user_id = call.message.chat.id
        text = style_text(f"📱 {category} Sᴇʀᴠɪᴄᴇs\n\nSᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ:")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=services_keyboard(category)
            )
        except:
            bot.send_message(user_id, text, reply_markup=services_keyboard(category))

    def start_order_process(bot, call, service_id):
        user_id = call.message.chat.id
        service = services.get_service_by_id(service_id)
        
        if not service:
            bot.answer_callback_query(call.id, style_text("❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!"))
            return
        
        user_states[user_id] = {
            "action": "ordering",
            "service_id": service_id,
            "service": service,
            "step": "link"
        }
        
        text = style_text(f"""
🛒 Oʀᴅᴇʀ: {service['name']}

📝 {service['description']}
💰 Pʀɪᴄᴇ: {service['price_per_unit']} ᴘᴏɪɴᴛs ᴘᴇʀ {service['unit']}
🔢 Rᴀɴɢᴇ: {service['min']} - {service['max']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ:
        """)
        
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text
            )
        except:
            bot.send_message(user_id, text)
        bot.register_next_step_handler(call.message, process_order_link)

    def process_order_link(message):
        user_id = message.chat.id
        if user_id not in user_states or user_states[user_id].get("action") != "ordering":
            return
        
        link = message.text.strip()
        user_states[user_id]["link"] = link
        user_states[user_id]["step"] = "quantity"
        
        service = user_states[user_id]["service"]
        bot.send_message(user_id, style_text(f"🔢 Eɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ ({service['min']} - {service['max']}):"))

    def process_order_quantity(message):
        user_id = message.chat.id
        if user_id not in user_states or user_states[user_id].get("action") != "ordering":
            return
        
        service = user_states[user_id]["service"]
        is_valid, result = validate_quantity(message.text, service["min"], service["max"])
        if not is_valid:
            bot.send_message(user_id, style_text(result))
            return
        
        quantity = result
        cost_points = (quantity / service["unit"]) * service["price_per_unit"]
        
        # Check balance
        user_balance = get_user(user_id)["balance_points"]
        if user_balance < cost_points:
            bot.send_message(user_id, style_text(f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ! Yᴏᴜ ɴᴇᴇᴅ {cost_points} ᴘᴏɪɴᴛs."))
            del user_states[user_id]
            return
        
        user_states[user_id]["quantity"] = quantity
        user_states[user_id]["cost_points"] = cost_points
        
        text = style_text(f"""
🛒 Oʀᴅᴇʀ Cᴏɴғɪʀᴍᴀᴛɪᴏɴ

📱 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {user_states[user_id]['link']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: {cost_points} ᴘᴏɪɴᴛs

Cᴏɴғɪʀᴍ ᴏʀᴅᴇʀ?
        """)
        
        bot.send_message(user_id, text, reply_markup=order_confirmation_keyboard())

    def confirm_order(bot, call):
        user_id = call.message.chat.id
        if user_id not in user_states or user_states[user_id].get("action") != "ordering":
            return
        
        data = user_states[user_id]
        service = data["service"]
        
        processing_msg = bot.send_message(user_id, "🔄 Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ᴏʀᴅᴇʀ...")
        
        # Place order via SMM API
        api_order_id = place_smm_order(service["service_id"], data["link"], data["quantity"])
        
        if api_order_id:
            # Deduct balance and create order
            new_balance = update_user_balance(user_id, -int(data["cost_points"]), is_spent=True)
            order = create_order(user_id, service, data["link"], data["quantity"], int(data["cost_points"]), api_order_id)
            
            text = style_text(f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

🆔 Oʀᴅᴇʀ ID: {order['order_id']}
📱 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {data['quantity']}
💰 Cᴏsᴛ: {data['cost_points']} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs

📊 Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ
            """)
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=text,
                reply_markup=back_button_only()
            )
            
            # Send to proof channel
            send_order_to_channel(bot, order)
        else:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=style_text("❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴘʟᴀᴄᴇ ᴏʀᴅᴇʀ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."),
                reply_markup=back_button_only()
            )
        
        del user_states[user_id]

    def show_order_history(bot, call):
        user_id = call.message.chat.id
        orders = get_user_orders(user_id)
        
        if not orders:
            text = style_text("📋 Yᴏᴜ ʜᴀᴠᴇ ɴᴏ ᴏʀᴅᴇʀs ʏᴇᴛ.")
        else:
            text = style_text("📋 Yᴏᴜʀ Rᴇᴄᴇɴᴛ Oʀᴅᴇʀs:\n\n")
            for order in orders:
                status_emoji = "✅" if order["status"] == "Completed" else "⏳" if order["status"] == "Processing" else "❌"
                text += style_text(f"""
{status_emoji} Oʀᴅᴇʀ ID: {order['order_id']}
📱 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💰 Cᴏsᴛ: {order['cost_points']} ᴘᴏɪɴᴛs
📊 Sᴛᴀᴛᴜs: {order['status']}
────────────────
                """)
        
        bot.send_message(user_id, text, reply_markup=back_button_only())

    def show_account_info(bot, call):
        user_id = call.message.chat.id
        user = get_user(user_id)
        balance = user["balance_points"]
        total_orders = len(get_user_orders(user_id))
        
        text = style_text(f"""
👤 Aᴄᴄᴏᴜɴᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ

🆔 Usᴇʀ ID: {user_id}
💰 Bᴀʟᴀɴᴄᴇ: {balance} ᴘᴏɪɴᴛs (₹{balance/100:.2f})
📥 Tᴏᴛᴀʟ Dᴇᴘᴏsɪᴛᴇᴅ: {user.get('total_deposits_points', 0)} ᴘᴏɪɴᴛs
📤 Tᴏᴛᴀʟ Sᴘᴇɴᴛ: {user.get('total_spent_points', 0)} ᴘᴏɪɴᴛs
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
📅 Jᴏɪɴᴇᴅ: {user['joined_at'].strftime('%Y-%m-%d')}

💸 100 ᴘᴏɪɴᴛs = ₹1
        """)
        
        bot.send_message(user_id, text, reply_markup=back_button_only())

    def show_stats(bot, call):
        user_id = call.message.chat.id
        total_users = users_collection.count_documents({})
        total_orders = orders_collection.count_documents({})
        
        text = style_text(f"""
📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs

👤 Tᴏᴛᴀʟ Usᴇʀs: {total_users}
🛒 Tᴏᴛᴀʟ Oʀᴅᴇʀs: {total_orders}
📱 Aᴄᴛɪᴠᴇ Sᴇʀᴠɪᴄᴇs: {len(services.get_all_services())}
        """)
        
        bot.send_message(user_id, text, reply_markup=back_button_only())

    def show_support(bot, call):
        user_id = call.message.chat.id
        text = style_text("""
🆘 Sᴜᴘᴘᴏʀᴛ

📞 Cᴏɴᴛᴀᴄᴛ ᴜs ғᴏʀ:
• Aᴄᴄᴏᴜɴᴛ ɪssᴜᴇs
• Dᴇᴘᴏsɪᴛ ʜᴇʟᴘ
• Oʀᴅᴇʀ ᴘʀᴏʙʟᴇᴍs
• Gᴇɴᴇʀᴀʟ ǫᴜᴇsᴛɪᴏɴs

⏰ Sᴜᴘᴘᴏʀᴛ ʜᴏᴜʀs: 24/7
        """)
        
        bot.send_message(user_id, text, reply_markup=support_keyboard())

    def show_how_to_use(bot, call):
        user_id = call.message.chat.id
        text = style_text("""
📖 Hᴏᴡ Tᴏ Usᴇ

1. 💰 Dᴇᴘᴏsɪᴛ - Aᴅᴅ ғᴜɴᴅs ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ
2. 🛒 Nᴇᴡ Oʀᴅᴇʀ - Pʟᴀᴄᴇ ɴᴇᴡ SMM ᴏʀᴅᴇʀs
3. 📋 Oʀᴅᴇʀs - Vɪᴇᴡ ʏᴏᴜʀ ᴏʀᴅᴇʀ ʜɪsᴛᴏʀʏ
4. 👤 Aᴄᴄᴏᴜɴᴛ - Cʜᴇᴄᴋ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ & sᴛᴀᴛs
5. 👥 Rᴇғᴇʀ - Eᴀʀɴ ʙʏ ʀᴇғᴇʀʀɪɴɢ ғʀɪᴇɴᴅs
6. 📊 Sᴛᴀᴛs - Vɪᴇᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs
7. ℹ️ Sᴜᴘᴘᴏʀᴛ - Gᴇᴛ ʜᴇʟᴘ

💸 100 ᴘᴏɪɴᴛs = ₹1
        """)
        
        bot.send_message(user_id, text, reply_markup=back_button_only())

    def check_channel_join(bot, call):
        user_id = call.message.chat.id
        channel_id = os.getenv('CHANNEL_ID', 'prooflelo1')
        
        if check_channel_membership(user_id, channel_id):
            send_welcome(call.message)
            bot.answer_callback_query(call.id, style_text("✅ Jᴏɪɴᴇᴅ! Wᴇʟᴄᴏᴍᴇ!"))
        else:
            bot.answer_callback_query(call.id, style_text("❌ Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ғɪʀsᴛ!"), show_alert=True)

    def send_order_to_channel(bot, order):
        """Send order to proof channel"""
        try:
            channel_id = os.getenv('PROOF_CHANNEL', 'prooflelo1')
            text = style_text(f"""
🆕 Nᴇᴡ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ!

📱 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
👤 Usᴇʀ ID: {order['user_id']}
🆔 Oʀᴅᴇʀ ID: {order['order_id']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💵 Pᴏɪɴᴛs: {order['cost_points']}
            """)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(style_text("🤖 Bᴏᴛ Hᴇʀᴇ 🛒"), url=f"https://t.me/{bot.get_me().username}"))
            
            bot.send_message(f"@{channel_id}", text, reply_markup=markup)
        except Exception as e:
            print(f"Error sending to channel: {e}")

    return bot
