import random
import requests
from config import DEPOSIT_IMAGE, users, deposits, ADMIN_IDS, CHANNEL_ID
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def generate_utr():
    """Generate 12-digit UTR number"""
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])

def create_upi_link(amount, utr):
    """Create UPI payment link"""
    # This is a simplified version - in production, use real UPI parameters
    return f"upi://pay?pa=merchant@upi&pn=Merchant&am={amount}&tn=Deposit-{utr}"

def generate_qr_code(amount, utr):
    """Generate QR code for UPI payment using QuickChart"""
    upi_link = create_upi_link(amount, utr)
    qr_url = f"https://quickchart.io/qr?text={upi_link}&size=200"
    return qr_url

def handle_deposit(bot, message):
    """Handle deposit request"""
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, "❌ Mɪɴɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ ɪs ₹10")
            return
        
        utr = generate_utr()
        qr_url = generate_qr_code(amount, utr)
        
        # Store deposit info
        user_id = message.from_user.id
        deposits[utr] = {
            'user_id': user_id,
            'amount': amount,
            'status': 'pending',
            'timestamp': message.date
        }
        
        caption = f"""
💰 Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ

💳 Aᴍᴏᴜɴᴛ: ₹{amount:,.2f}
🔢 UTR: {utr}

Sᴄᴀɴ ᴛʜᴇ QR ᴄᴏᴅᴇ ᴏʀ ᴜsᴇ UPI ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ ᴘᴀʏᴍᴇɴᴛ.
        """.strip()
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Pᴀɪᴅ", callback_data=f"paid_{utr}"),
            InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_main")
        )
        
        bot.send_photo(
            message.chat.id,
            qr_url,
            caption=caption,
            reply_markup=keyboard
        )
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ")

def check_payment_status(bot, call, utr):
    """Check payment status using Autodep API (simulated)"""
    # Simulate API call - replace with real Autodep API integration
    try:
        # This is where you'd integrate with Autodep API
        # response = requests.get(f"https://api.autodep.com/check/{utr}", headers={"Authorization": AUTODEP_API_KEY})
        # For demo, we'll simulate success after 2 seconds
        import time
        time.sleep(2)
        
        # Simulate payment verification (80% success rate for demo)
        if random.random() < 0.8:
            deposit = deposits.get(utr)
            if deposit and deposit['status'] == 'pending':
                user_id = deposit['user_id']
                amount = deposit['amount']
                
                # Update user balance
                if user_id not in users:
                    users[user_id] = {'balance': 0, 'deposits': 0, 'spent': 0}
                
                users[user_id]['balance'] += amount
                users[user_id]['deposits'] += amount
                deposits[utr]['status'] = 'completed'
                
                # Notify user
                bot.send_message(
                    user_id,
                    f"✅ Pᴀʏᴍᴇɴᴛ Cᴏɴғɪʀᴍᴇᴅ!\n💰 ₹{amount:,.2f} ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ."
                )
                
                # Notify admin
                for admin_id in ADMIN_IDS:
                    bot.send_message(
                        admin_id,
                        f"💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ\n👤 Usᴇʀ: {user_id}\n💳 Aᴍᴏᴜɴᴛ: ₹{amount:,.2f}\n🔢 UTR: {utr}"
                    )
                
                # Notify channel
                if CHANNEL_ID:
                    bot.send_message(
                        CHANNEL_ID,
                        f"💰 Nᴇᴡ Dᴇᴘᴏsɪᴛ Rᴇᴄᴇɪᴠᴇᴅ!\n💳 Aᴍᴏᴜɴᴛ: ₹{amount:,.2f}"
                    )
                
            else:
                bot.answer_callback_query(call.id, "❌ Pᴀʏᴍᴇɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ ᴏʀ ᴀʟʀᴇᴀᴅʏ ᴘʀᴏᴄᴇssᴇᴅ")
        else:
            bot.answer_callback_query(call.id, "❌ Pᴀʏᴍᴇɴᴛ ɴᴏᴛ ʏᴇᴛ ᴠᴇʀɪғɪᴇᴅ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ɪɴ 2 ᴍɪɴᴜᴛᴇs.")
            
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Eʀʀᴏʀ ᴄʜᴇᴄᴋɪɴɢ ᴘᴀʏᴍᴇɴᴛ sᴛᴀᴛᴜs")
