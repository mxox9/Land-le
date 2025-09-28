import requests
import random
from datetime import datetime
from bson import ObjectId
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv

load_dotenv()

class OrderSystem:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.services_collection = db.services
        self.orders_collection = db.orders
        self.users_collection = db.users
        
        # SMM API Configuration
        self.SMM_API_URL = "https://mysmmapi.com/api/v2"
        self.SMM_API_KEY = os.getenv('SMM_API_KEY', 'a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d')
        self.PROOF_CHANNEL = "https://t.me/prooflelo1"
        
        self.user_states = {}
        
        # Initialize default services if none exist
        self.initialize_default_services()

    def initialize_default_services(self):
        """Initialize default services if database is empty"""
        if self.services_collection.count_documents({}) == 0:
            default_services = [
                {
                    "name": "Instagram Likes",
                    "category": "instagram",
                    "description": "High quality Instagram likes with fast delivery",
                    "min": 100,
                    "max": 10000,
                    "unit": 100,
                    "price_per_unit": 250,  # 250 points per 100 likes
                    "service_id": "4952",  # Actual SMM panel service ID
                    "active": True,
                    "created_at": datetime.now()
                },
                {
                    "name": "Instagram Followers", 
                    "category": "instagram",
                    "description": "Real Instagram followers with guaranteed delivery",
                    "min": 100,
                    "max": 5000,
                    "unit": 100,
                    "price_per_unit": 300,  # 300 points per 100 followers
                    "service_id": "4953",  # Actual SMM panel service ID
                    "active": True,
                    "created_at": datetime.now()
                },
                {
                    "name": "YouTube Views",
                    "category": "youtube", 
                    "description": "High retention YouTube views",
                    "min": 1000,
                    "max": 50000,
                    "unit": 1000,
                    "price_per_unit": 200,  # 200 points per 1000 views
                    "service_id": "4954",  # Actual SMM panel service ID
                    "active": True,
                    "created_at": datetime.now()
                }
            ]
            
            self.services_collection.insert_many(default_services)
            print("✅ Default services initialized")

    def style_text(self, text):
        """Stylish text formatting"""
        stylish_mapping = {
            'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
            'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ',
            'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
        }
        
        if not text:
            return text
        
        def style_word(word):
            if len(word) > 0:
                styled_word = word[0]
                for char in word[1:]:
                    styled_word += stylish_mapping.get(char.lower(), char.lower())
                return styled_word
            return word
        
        words = text.split()
        styled_words = []
        
        for word in words:
            if any(char.isalpha() for char in word):
                styled_words.append(style_word(word))
            else:
                styled_words.append(word)
        
        return ' '.join(styled_words)

    def get_user_balance(self, user_id):
        """Get user balance"""
        user = self.users_collection.find_one({"user_id": user_id})
        if not user:
            self.users_collection.insert_one({
                "user_id": user_id,
                "balance_points": 0,
                "joined_at": datetime.now()
            })
            return 0
        return user.get("balance_points", 0)

    def update_user_balance(self, user_id, points_change):
        """Update user balance"""
        user = self.users_collection.find_one({"user_id": user_id})
        if not user:
            return 0
        
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance_points": points_change}}
        )
        return self.get_user_balance(user_id)

    def get_services_by_category(self, category):
        """Get services by category"""
        return list(self.services_collection.find({
            "category": category,
            "active": True
        }))

    def get_service_by_id(self, service_id):
        """Get service by ID"""
        return self.services_collection.find_one({
            "_id": ObjectId(service_id)
        })

    def place_smm_order(self, service_id, link, quantity):
        """Place order via SMM API - SIMPLE AND DIRECT"""
        try:
            # Direct API call - EXACTLY like your working code
            url = f"{self.SMM_API_URL}?key={self.SMM_API_KEY}&action=add&service={service_id}&link={link}&quantity={quantity}"
            
            print(f"🔗 API Call: {url}")
            
            response = requests.get(url, timeout=30)
            print(f"📡 API Response: {response.text}")
            
            data = response.json()
            
            # Check for order ID in response
            if 'order' in data:
                return str(data['order'])
            else:
                print(f"❌ API Error: {data}")
                return None
                
        except Exception as e:
            print(f"❌ Order placement error: {e}")
            return None

    def create_order(self, user_id, service_id, link, quantity, cost_points, api_order_id):
        """Create order record in database"""
        service = self.get_service_by_id(service_id)
        if not service:
            return None
        
        order_id = f"ORD{random.randint(100000, 999999)}"
        
        order = {
            "order_id": order_id,
            "api_order_id": api_order_id,
            "user_id": user_id,
            "service_id": service_id,
            "service_name": service["name"],
            "link": link,
            "quantity": quantity,
            "cost_points": cost_points,
            "status": "Pending",
            "created_at": datetime.now()
        }
        
        self.orders_collection.insert_one(order)
        return order

    def send_order_to_channel(self, order):
        """Send order proof to channel"""
        try:
            text = self.style_text(f"""
🆕 Nᴇᴡ Oʀᴅᴇʀ Pʟᴀᴄᴇᴅ!

📱 Sᴇʀᴠɪᴄᴇ: {order['service_name']}
👤 Usᴇʀ ID: {order['user_id']}
🆔 Oʀᴅᴇʀ ID: {order['order_id']}
🔗 Lɪɴᴋ: {order['link'][:50]}...
🔢 Qᴜᴀɴᴛɪᴛʏ: {order['quantity']}
💵 Pᴏɪɴᴛs: {order['cost_points']}
            """)
            
            self.bot.send_message(self.PROOF_CHANNEL, text)
            return True
        except Exception as e:
            print(f"Error sending to channel: {e}")
            return False

    # Keyboard functions for order system
    def service_category_keyboard(self):
        markup = InlineKeyboardMarkup()
        categories = self.services_collection.distinct("category", {"active": True})
        
        for category in categories:
            emoji = "📱" if category == "instagram" else "📺" if category == "youtube" else "📢"
            markup.add(InlineKeyboardButton(
                f"{emoji} {self.style_text(category)}", 
                callback_data=f"category_{category}"
            ))
        
        markup.add(InlineKeyboardButton(self.style_text("🔙 Back"), callback_data="main_menu"))
        return markup

    def services_keyboard(self, category):
        markup = InlineKeyboardMarkup()
        services = self.get_services_by_category(category)
        
        for service in services:
            price = service["price_per_unit"]
            unit = service["unit"]
            button_text = f"{self.style_text(service['name'])} - {price} Points/{unit}"
            markup.add(InlineKeyboardButton(
                button_text, 
                callback_data=f"service_{service['_id']}"
            ))
        
        markup.add(InlineKeyboardButton(self.style_text("🔙 Back"), callback_data="order_menu"))
        return markup

    # Order flow methods
    def show_service_categories(self, call):
        """Show service categories"""
        user_id = call.message.chat.id
        
        text = self.style_text("""
🛒 Sᴇʀᴠɪᴄᴇ Cᴀᴛᴇɢᴏʀɪᴇs

Sᴇʟᴇᴄᴛ ᴀ ᴄᴀᴛᴇɢᴏʀʏ:
        """)
        
        try:
            self.bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=self.service_category_keyboard()
            )
        except:
            self.bot.send_message(user_id, text, reply_markup=self.service_category_keyboard())

    def show_services(self, call, category):
        """Show services for a category"""
        user_id = call.message.chat.id
        
        text = self.style_text(f"""
📱 {category.upper()} Sᴇʀᴠɪᴄᴇs

Sᴇʟᴇᴄᴛ ᴀ sᴇʀᴠɪᴄᴇ:
        """)
        
        try:
            self.bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=self.services_keyboard(category)
            )
        except:
            self.bot.send_message(user_id, text, reply_markup=self.services_keyboard(category))

    def start_order_process(self, call, service_id):
        """Start order process"""
        user_id = call.message.chat.id
        service = self.get_service_by_id(service_id)
        
        if not service:
            self.bot.answer_callback_query(call.id, "❌ Sᴇʀᴠɪᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")
            return
        
        self.user_states[user_id] = {
            "action": "ordering",
            "service_id": service_id,
            "step": "link"
        }
        
        text = self.style_text(f"""
🛒 Oʀᴅᴇʀ: {service['name']}

📝 {service['description']}
💰 Pʀɪᴄᴇ: {service['price_per_unit']} ᴘᴏɪɴᴛs ᴘᴇʀ {service['unit']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {service['min']} - {service['max']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ:
        """)
        
        try:
            self.bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text
            )
        except:
            self.bot.send_message(user_id, text)

    def handle_order_messages(self, message):
        """Handle order flow messages"""
        user_id = message.chat.id
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        
        if state.get("action") == "ordering" and state.get("step") == "link":
            self.process_order_link(message)
        
        elif state.get("action") == "ordering" and state.get("step") == "quantity":
            self.process_order_quantity(message)

    def process_order_link(self, message):
        """Process order link"""
        user_id = message.chat.id
        link = message.text.strip()
        
        if not link.startswith("http"):
            self.bot.send_message(user_id, self.style_text("❌ Iɴᴠᴀʟɪᴅ ʟɪɴᴋ! Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ʜᴛᴛᴘs ʟɪɴᴋ."))
            return
        
        self.user_states[user_id]["link"] = link
        self.user_states[user_id]["step"] = "quantity"
        
        service = self.get_service_by_id(self.user_states[user_id]["service_id"])
        self.bot.send_message(user_id, self.style_text(f"🔢 Eɴᴛᴇʀ ǫᴜᴀɴᴛɪᴛʏ ({service['min']} - {service['max']}):"))

    def process_order_quantity(self, message):
        """Process order quantity"""
        user_id = message.chat.id
        
        try:
            quantity = int(message.text.strip())
            service = self.get_service_by_id(self.user_states[user_id]["service_id"])
            
            if quantity < service["min"] or quantity > service["max"]:
                self.bot.send_message(user_id, self.style_text(f"❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Mᴜsᴛ ʙᴇ {service['min']}-{service['max']}."))
                return
            
            self.user_states[user_id]["quantity"] = quantity
            
            # Calculate cost
            cost_points = (quantity / service["unit"]) * service["price_per_unit"]
            self.user_states[user_id]["cost_points"] = cost_points
            
            # Check balance
            user_balance = self.get_user_balance(user_id)
            if user_balance < cost_points:
                self.bot.send_message(user_id, self.style_text(f"❌ Iɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ! Nᴇᴇᴅ: {cost_points}, Hᴀᴠᴇ: {user_balance}"))
                del self.user_states[user_id]
                return
            
            # Show confirmation
            text = self.style_text(f"""
🛒 Oʀᴅᴇʀ Cᴏɴғɪʀᴍᴀᴛɪᴏɴ

📱 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔗 Lɪɴᴋ: {self.user_states[user_id]['link'][:50]}...
🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
💰 Cᴏsᴛ: {cost_points} ᴘᴏɪɴᴛs

Cᴏɴғɪʀᴍ ᴏʀᴅᴇʀ?
            """)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(self.style_text("✅ Confirm"), callback_data="confirm_order"))
            markup.add(InlineKeyboardButton(self.style_text("❌ Cancel"), callback_data="order_menu"))
            
            self.bot.send_message(user_id, text, reply_markup=markup)
            
        except ValueError:
            self.bot.send_message(user_id, self.style_text("❌ Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Usᴇ ɴᴜᴍʙᴇʀs."))

    def confirm_order(self, call):
        """Confirm and place order"""
        user_id = call.message.chat.id
        
        if user_id not in self.user_states or self.user_states[user_id].get("action") != "ordering":
            self.bot.answer_callback_query(call.id, "❌ Nᴏ ᴏʀᴅᴇʀ ᴅᴀᴛᴀ!")
            return
        
        data = self.user_states[user_id]
        service = self.get_service_by_id(data["service_id"])
        
        # Show processing
        processing_msg = self.bot.send_message(user_id, "🔄 Pʀᴏᴄᴇssɪɴɢ ᴏʀᴅᴇʀ...")
        
        # Get SMM service ID
        smm_service_id = service.get("service_id")
        
        if not smm_service_id:
            self.bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=self.style_text("❌ Sᴇʀᴠɪᴄᴇ ᴇʀʀᴏʀ! Cᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.")
            )
            del self.user_states[user_id]
            return
        
        # Place order via SMM API
        api_order_id = self.place_smm_order(smm_service_id, data["link"], data["quantity"])
        
        if not api_order_id:
            # Order failed
            self.bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=self.style_text("""
❌ Oʀᴅᴇʀ Fᴀɪʟᴇᴅ!

Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.
Cᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ ɪғ ɪssᴜᴇ ᴘᴇʀsɪsᴛs.
                """)
            )
            return
        
        # SUCCESS: Order placed
        # Deduct balance
        new_balance = self.update_user_balance(user_id, -int(data["cost_points"]))
        
        # Create order record
        order = self.create_order(user_id, data["service_id"], data["link"], data["quantity"], int(data["cost_points"]), api_order_id)
        
        if order:
            # Send to channel
            self.send_order_to_channel(order)
            
            # Success message
            success_text = self.style_text(f"""
✅ Oʀᴅᴇʀ Sᴜᴄᴄᴇssғᴜʟ!

🆔 Oʀᴅᴇʀ ID: {order['order_id']}
📱 Sᴇʀᴠɪᴄᴇ: {service['name']}
🔢 Qᴜᴀɴᴛɪᴛʏ: {data['quantity']}
💰 Cᴏsᴛ: {data['cost_points']} ᴘᴏɪɴᴛs
💳 Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance} ᴘᴏɪɴᴛs

Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ
            """)
            
            self.bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=success_text
            )
            
            # Clear state
            del self.user_states[user_id]
        else:
            # Refund if order creation failed
            self.update_user_balance(user_id, int(data["cost_points"]))
            self.bot.edit_message_text(
                chat_id=user_id,
                message_id=processing_msg.message_id,
                text=self.style_text("❌ Oʀᴅᴇʀ ᴇʀʀᴏʀ! Pᴏɪɴᴛs ʀᴇғᴜɴᴅᴇᴅ.")
            )

    def show_order_history(self, call):
        """Show user order history"""
        user_id = call.message.chat.id
        orders = list(self.orders_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(5))
        
        if not orders:
            text = self.style_text("📋 Nᴏ ᴏʀᴅᴇʀs ʏᴇᴛ.")
        else:
            text = self.style_text("📋 Yᴏᴜʀ Oʀᴅᴇʀs:\n\n")
            for order in orders:
                status_emoji = "✅" if order["status"] == "Completed" else "⏳"
                text += self.style_text(f"""
{status_emoji} {order['order_id']}
📱 {order['service_name']}
🔢 {order['quantity']} | 💰 {order['cost_points']}
📊 {order['status']}
────────────────
                """)
        
        try:
            self.bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text
            )
        except:
            self.bot.send_message(user_id, text)
