import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import random
from datetime import datetime

# Bot Configuration
BOT_TOKEN = "8052955693:AAFyR1xAz08jM664fJ4wUCsxpzg0WVS3Sw0"
SMM_API_URL = "https://mysmmapi.com/api/v2?"
SMM_API_KEY = "a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Simple services
SERVICES = [
    {
        "name": "📸 Insta Views",
        "service_id": "4901",
        "price": 40,
        "unit": 1000,
        "min": 100,
        "max": 50000,
        "description": "High-quality Instagram Views"
    }
]

# User data storage
users_data = {}
orders_data = {}

def place_smm_order(service_id, link, quantity):
    """Place order via SMM API"""
    try:
        params = {
            'key': SMM_API_KEY,
            'action': 'add',
            'service': service_id,
            'link': link,
            'quantity': quantity
        }
        
        response = requests.get(SMM_API_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Response: {data}")  # Debug log
            
            if isinstance(data, dict):
                if data.get('error'):
                    return None, data.get('error')
                
                # Try different possible order ID fields
                for key in ['order', 'order_id', 'id']:
                    if key in data and data[key]:
                        return str(data[key]), None
                
                # Check nested data
                if 'data' in data and isinstance(data['data'], dict):
                    for key in ['order', 'order_id', 'id']:
                        if key in data['data'] and data['data'][key]:
                            return str(data['data'][key]), None
            
            return None, "No order ID in response"
        else:
            return None, f"API Error: {response.status_code}"
            
    except Exception as e:
        return None, f"Request failed: {str(e)}"

def get_user_balance(user_id):
    if user_id not in users_data:
        users_data[user_id] = {"balance": 1000.0}  # Start with ₹1000 for testing
    return users_data[user_id]["balance"]

def update_user_balance(user_id, amount):
    if user_id not in users_data:
        users_data[user_id] = {"balance": 1000.0}
    users_data[user_id]["balance"] += amount
    return users_data[user_id]["balance"]

def generate_order_id():
    return f"TEST{random.randint(1000, 9999)}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_name = message.chat.first_name
    
    text = f"""
👋 Welcome {user_name}!

🤖 *SMM Bot Testing*
Testing Order Placement System

💰 *Your Balance:* ₹{get_user_balance(user_id):.2f}

Click below to test order placement:
"""
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 Test Insta Views Order", callback_data="test_order"))
    markup.add(InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    
    if call.data == "test_order":
        start_test_order(call)
    elif call.data == "check_balance":
        check_balance(call)
    elif call.data == "confirm_order":
        confirm_test_order(call)

def start_test_order(call):
    user_id = call.message.chat.id
    
    text = """
🛒 *Test Order - Insta Views*

💰 Price: ₹40 per 1000 views
🔢 Min: 100 | Max: 50,000

Please send the Instagram post URL:
"""
    
    bot.send_message(user_id, text, parse_mode='Markdown')
    bot.register_next_step_handler(call.message, process_test_link)

def process_test_link(message):
    user_id = message.chat.id
    link = message.text.strip()
    
    # Store the link
    if 'user_states' not in globals():
        globals()['user_states'] = {}
    user_states[user_id] = {"link": link, "step": "quantity"}
    
    bot.send_message(user_id, "🔢 Now send the quantity (100-50000):")
    bot.register_next_step_handler(message, process_test_quantity)

def process_test_quantity(message):
    user_id = message.chat.id
    
    try:
        quantity = int(message.text.strip())
        
        if quantity < 100 or quantity > 50000:
            bot.send_message(user_id, "❌ Quantity must be between 100-50000")
            return
        
        service = SERVICES[0]
        cost = (quantity / service["unit"]) * service["price"]
        
        # Store order data
        user_states[user_id]["quantity"] = quantity
        user_states[user_id]["cost"] = cost
        user_states[user_id]["service"] = service
        
        text = f"""
✅ *Order Ready!*

📝 Service: {service['name']}
🔗 Link: {user_states[user_id]['link']}
🔢 Quantity: {quantity}
💰 Cost: ₹{cost:.2f}

Click CONFIRM to place order:
"""
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ CONFIRM ORDER", callback_data="confirm_order"))
        
        bot.send_message(user_id, text, reply_markup=markup, parse_mode='Markdown')
        
    except ValueError:
        bot.send_message(user_id, "❌ Please enter a valid number")

def confirm_test_order(call):
    user_id = call.message.chat.id
    
    if user_id not in user_states:
        bot.send_message(user_id, "❌ No order data found. Please start over.")
        return
    
    order_data = user_states[user_id]
    service = order_data["service"]
    
    processing_msg = bot.send_message(user_id, "🔄 *Placing order via API...*", parse_mode='Markdown')
    
    # Place order via API
    api_order_id, error = place_smm_order(service["service_id"], order_data["link"], order_data["quantity"])
    
    if api_order_id:
        # Deduct balance
        new_balance = update_user_balance(user_id, -order_data["cost"])
        
        # Create order record
        order_id = generate_order_id()
        orders_data[order_id] = {
            "order_id": order_id,
            "api_order_id": api_order_id,
            "user_id": user_id,
            "service": service["name"],
            "link": order_data["link"],
            "quantity": order_data["quantity"],
            "cost": order_data["cost"],
            "status": "Pending",
            "created_at": datetime.now()
        }
        
        success_text = f"""
🎉 *ORDER PLACED SUCCESSFULLY!*

🆔 Your Order ID: `{order_id}`
🆔 API Order ID: `{api_order_id}`
📝 Service: {service['name']}
🔗 Link: {order_data['link']}
🔢 Quantity: {order_data['quantity']}
💰 Cost: ₹{order_data['cost']:.2f}
💳 New Balance: ₹{new_balance:.2f}

✅ Order sent to SMM API successfully!
📊 Status: Processing
"""
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=processing_msg.message_id,
            text=success_text,
            parse_mode='Markdown'
        )
        
        # Send to proof channel (optional)
        try:
            proof_text = f"""
🆕 TEST ORDER PLACED!

📝 Service: {service['name']}
👤 User: {user_id}
🆔 Order: {order_id}
🆔 API Order: {api_order_id}
🔗 Link: {order_data['link']}
🔢 Quantity: {order_data['quantity']}
"""
            bot.send_message("@prooflelo1", proof_text)
        except:
            pass
            
    else:
        error_text = f"""
❌ *ORDER FAILED!*

🚫 Error: {error}

💡 What to do:
• Check if API credentials are correct
• Verify service ID is valid
• Try different link/quantity
"""
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=processing_msg.message_id,
            text=error_text,
            parse_mode='Markdown'
        )
    
    # Clean up
    if user_id in user_states:
        del user_states[user_id]

def check_balance(call):
    user_id = call.message.chat.id
    balance = get_user_balance(user_id)
    
    text = f"""
💰 *Your Balance*

💳 Available: ₹{balance:.2f}
📊 Total Orders: {len([o for o in orders_data.values() if o['user_id'] == user_id])}
"""
    
    bot.send_message(user_id, text, parse_mode='Markdown')

@bot.message_handler(commands=['debug'])
def debug_info(message):
    user_id = message.chat.id
    
    text = f"""
🔧 *Debug Information*

🤖 Bot: Working
🔑 API Key: {SMM_API_KEY[:10]}...
🌐 API URL: {SMM_API_URL}
📊 Total Users: {len(users_data)}
🛒 Total Orders: {len(orders_data)}
"""
    
    bot.send_message(user_id, text, parse_mode='Markdown')

print("🤖 Testing Bot Started!")
print("🔑 API Key:", SMM_API_KEY)
print("🌐 API URL:", SMM_API_URL)

if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Bot error: {e}")
