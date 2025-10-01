import random
import time
import requests
from config import users, orders, SMM_API_KEY, SMM_API_URL, ADMIN_IDS, CHANNEL_ID
from services import get_service_by_id

def generate_order_id():
    """Generate unique order ID"""
    return f"ORD{random.randint(100000, 999999)}"

def validate_order(user_id, service_id, quantity, link):
    """Validate order parameters"""
    service = get_service_by_id(service_id)
    if not service:
        return False, "Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ"
    
    if not service["active"]:
        return False, "Sᴇʀᴠɪᴄᴇ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ"
    
    if quantity < service["min"] or quantity > service["max"]:
        return False, f"Qᴜᴀɴᴛɪᴛʏ ᴍᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ {service['min']:,} ᴀɴᴅ {service['max']:,}"
    
    # Validate link format (basic validation)
    if not link.startswith(('http://', 'https://')):
        return False, "Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ URL"
    
    # Check balance
    cost = (quantity / 1000) * service["price"]
    user_balance = users.get(user_id, {}).get('balance', 0)
    
    if user_balance < cost:
        return False, f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ. Nᴇᴇᴅᴇᴅ: ₹{cost:.2f}, Aᴠᴀɪʟᴀʙʟᴇ: ₹{user_balance:.2f}"
    
    return True, {"service": service, "cost": cost}

def place_smm_order(order_id, service_id, quantity, link):
    """Place order with SMM API (simulated)"""
    # This is where you'd integrate with real SMM panel API
    try:
        # Simulate API call
        # payload = {
        #     'key': SMM_API_KEY,
        #     'action': 'add',
        #     'service': service_id,  # Use real service ID here
        #     'link': link,
        #     'quantity': quantity
        # }
        # response = requests.post(SMM_API_URL, data=payload)
        
        # For demo, simulate API response
        time.sleep(2)
        
        # Simulate different statuses
        statuses = ['Pending', 'In progress', 'Completed', 'Partial', 'Cancelled']
        weights = [0.2, 0.5, 0.2, 0.05, 0.05]
        status = random.choices(statuses, weights=weights)[0]
        
        # Store order
        orders[order_id] = {
            'status': status,
            'service_id': service_id,
            'quantity': quantity,
            'link': link,
            'placed_at': time.time(),
            'api_response': f"Simulated {status}"
        }
        
        return True, "Oʀᴅᴇʀ ᴘʟᴀᴄᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ"
        
    except Exception as e:
        return False, f"Eʀʀᴏʀ ᴘʟᴀᴄɪɴɢ ᴏʀᴅᴇʀ: {str(e)}"

def handle_new_order(bot, message, service_id, link):
    """Handle new order creation"""
    user_id = message.from_user.id
    
    try:
        quantity = int(message.text)
        
        # Validate order
        is_valid, result = validate_order(user_id, service_id, quantity, link)
        
        if not is_valid:
            bot.send_message(message.chat.id, result)
            return
        
        service = result["service"]
        cost = result["cost"]
        
        # Generate order ID
        order_id = generate_order_id()
        
        # Deduct balance
        users[user_id]['balance'] -= cost
        users[user_id]['spent'] += cost
        
        # Place order with SMM API
        success, message_text = place_smm_order(order_id, service_id, quantity, link)
        
        if success:
            # Notify user
            bot.send_message(
                message.chat.id,
                f"""
✅ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!

📦 Oʀᴅᴇʀ ID: {order_id}
🏷 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {link[:50]}...
📊 Qᴜᴀɴᴛɪᴛʏ: {quantity:,} {service['unit']}
💰 Cᴏsᴛ: ₹{cost:.2f}
📝 Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ

Usᴇ /track ᴛᴏ ᴄʜᴇᴄᴋ sᴛᴀᴛᴜs.
                """.strip()
            )
            
            # Notify admin
            for admin_id in ADMIN_IDS:
                bot.send_message(
                    admin_id,
                    f"""
🆕 Nᴇᴡ Oʀᴅᴇʀ!
👤 Usᴇʀ: {user_id}
📦 Oʀᴅᴇʀ ID: {order_id}
🏷 Sᴇʀᴠɪᴄᴇ: {service['name']}
💰 Aᴍᴏᴜɴᴛ: ₹{cost:.2f}
                    """.strip()
                )
            
            # Notify channel
            if CHANNEL_ID:
                bot.send_message(
                    CHANNEL_ID,
                    f"🆕 Nᴇᴡ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ! Oʀᴅᴇʀ ID: {order_id}"
                )
        else:
            # Refund if order failed
            users[user_id]['balance'] += cost
            users[user_id]['spent'] -= cost
            bot.send_message(message.chat.id, f"❌ {message_text}")
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ")

def track_order(bot, message):
    """Track order status"""
    order_id = message.text.upper().strip()
    
    if order_id in orders:
        order = orders[order_id]
        service = get_service_by_id(order['service_id'])
        
        status_emoji = {
            'Pending': '⏳',
            'In progress': '🔄', 
            'Completed': '✅',
            'Partial': '⚠️',
            'Cancelled': '❌'
        }
        
        emoji = status_emoji.get(order['status'], '📦')
        
        bot.send_message(
            message.chat.id,
            f"""
📦 Oʀᴅᴇʀ Tʀᴀᴄᴋɪɴɢ

🆔 Oʀᴅᴇʀ ID: {order_id}
{emoji} Sᴛᴀᴛᴜs: {order['status']}
🏷 Sᴇʀᴠɪᴄᴇ: {service['name'] if service else 'Unknown'}
🔗 Lɪɴᴋ: {order['link'][:50]}...
📊 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']:,}
📝 Rᴇsᴘᴏɴsᴇ: {order['api_response']}
            """.strip()
        )
    else:
        bot.send_message(message.chat.id, "❌ Oʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ. Pʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ Oʀᴅᴇʀ ID.")

def process_refunds():
    """Process refunds for cancelled/partial orders"""
    # This would run as a background task
    for order_id, order in orders.items():
        if order['status'] in ['Cancelled', 'Partial'] and not order.get('refund_processed'):
            # Process refund logic here
            order['refund_processed'] = True
            # In real implementation, refund amount based on completion status
