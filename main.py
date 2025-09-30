import os
import telebot
import threading
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
from database import init_database
from admin_handlers import setup_admin_handlers
from user_handlers import setup_user_handlers
from utils import style_text

# Initialize bot
BOT_TOKEN = os.getenv('BOT_TOKEN', '8052955693:AAGoXnNg90jqvcC1X1fVo_qKV8Y0eHjDAZg')
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize database
init_database()

# Setup handlers
bot = setup_admin_handlers(bot)
bot = setup_user_handlers(bot)

# Background task for order status updates
def update_order_statuses():
    """Background task to update order statuses"""
    from database import orders_collection
    from smm_api import check_smm_order
    
    while True:
        try:
            # Get pending orders
            pending_orders = orders_collection.find({
                "status": {"$in": ["Pending", "Processing"]}
            })
            
            for order in pending_orders:
                if order.get("api_order_id"):
                    # Check status from API
                    new_status = check_smm_order(order["api_order_id"])
                    if new_status and new_status != order["status"]:
                        orders_collection.update_one(
                            {"_id": order["_id"]},
                            {
                                "$set": {
                                    "status": new_status,
                                    "last_check": datetime.now()
                                }
                            }
                        )
                        print(f"Updated order {order['order_id']} status to {new_status}")
            
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            print(f"Order status update error: {e}")
            time.sleep(60)

# Start background tasks
def start_background_tasks():
    """Start all background tasks"""
    threading.Thread(target=update_order_statuses, daemon=True).start()

if __name__ == "__main__":
    print("🤖 Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
    start_background_tasks()
    
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Bot error: {e}")
        time.sleep(10)
