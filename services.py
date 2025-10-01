from config import SERVICE_IMAGE
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Service data structure - Replace service_id here with real ID from SMM panel
SERVICES = {
    "Iɴsᴛᴀɢʀᴀᴍ": [
        {
            "id": "insta_likes_temp_1",  # Replace with real SMM panel service ID
            "category": "Iɴsᴛᴀɢʀᴀᴍ",
            "name": "❤️ Iɴsᴛᴀ Lɪᴋᴇs",
            "description": "Hɪɢʜ-ǫᴜᴀʟɪᴛʏ Iɴsᴛᴀɢʀᴀᴍ ʟɪᴋᴇs ғʀᴏᴍ ʀᴇᴀʟ ᴜsᴇʀs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 25.0,
            "active": True
        },
        {
            "id": "insta_follows_temp_2",  # Replace with real SMM panel service ID
            "category": "Iɴsᴛᴀɢʀᴀᴍ",
            "name": "👥 Iɴsᴛᴀ Fᴏʟʟᴏᴡs",
            "description": "Rᴇᴀʟ Iɴsᴛᴀɢʀᴀᴍ ғᴏʟʟᴏᴡᴇʀs ɢᴜᴀʀᴀɴᴛᴇᴇᴅ",
            "min": 50,
            "max": 5000,
            "unit": "followers",
            "price": 120.0,
            "active": True
        },
        {
            "id": "insta_views_temp_3",  # Replace with real SMM panel service ID
            "category": "Iɴsᴛᴀɢʀᴀᴍ",
            "name": "👁 Iɴsᴛᴀ Vɪᴇᴡs",
            "description": "Iɴsᴛᴀɢʀᴀᴍ ʀᴇᴇʟs ᴀɴᴅ ᴠɪᴅᴇᴏ ᴠɪᴇᴡs",
            "min": 500,
            "max": 50000,
            "unit": "views",
            "price": 15.0,
            "active": True
        }
    ],
    "Fᴀᴄᴇʙᴏᴏᴋ": [
        {
            "id": "fb_likes_temp_4",  # Replace with real SMM panel service ID
            "category": "Fᴀᴄᴇʙᴏᴏᴋ",
            "name": "👍 Fʙ Lɪᴋᴇs",
            "description": "Fᴀᴄᴇʙᴏᴏᴋ ᴘᴀɢᴇ ᴀɴᴅ ᴘᴏsᴛ ʟɪᴋᴇs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 30.0,
            "active": True
        },
        {
            "id": "fb_views_temp_5",  # Replace with real SMM panel service ID
            "category": "Fᴀᴄᴇʙᴏᴏᴋ",
            "name": "👁 Fʙ Vɪᴇᴡs",
            "description": "Fᴀᴄᴇʙᴏᴏᴋ ᴠɪᴅᴇᴏ ᴠɪᴇᴡs",
            "min": 500,
            "max": 50000,
            "unit": "views",
            "price": 20.0,
            "active": True
        },
        {
            "id": "fb_follows_temp_6",  # Replace with real SMM panel service ID
            "category": "Fᴀᴄᴇʙᴏᴏᴋ",
            "name": "👥 Fʙ Fᴏʟʟᴏᴡs",
            "description": "Fᴀᴄᴇʙᴏᴏᴋ ᴘᴀɢᴇ ғᴏʟʟᴏᴡᴇʀs",
            "min": 50,
            "max": 5000,
            "unit": "followers",
            "price": 150.0,
            "active": True
        }
    ],
    "Tᴇʟᴇɢʀᴀᴍ": [
        {
            "id": "tg_members_temp_7",  # Replace with real SMM panel service ID
            "category": "Tᴇʟᴇɢʀᴀᴍ",
            "name": "👥 Tɢ Mᴇᴍʙᴇʀs",
            "description": "Tᴇʟᴇɢʀᴀᴍ ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs",
            "min": 100,
            "max": 10000,
            "unit": "members",
            "price": 80.0,
            "active": True
        },
        {
            "id": "tg_views_temp_8",  # Replace with real SMM panel service ID
            "category": "Tᴇʟᴇɢʀᴀᴍ",
            "name": "👁 Tɢ Vɪᴇᴡs",
            "description": "Tᴇʟᴇɢʀᴀᴍ ᴘᴏsᴛ ᴠɪᴇᴡs",
            "min": 1000,
            "max": 100000,
            "unit": "views",
            "price": 10.0,
            "active": True
        },
        {
            "id": "tg_reactions_temp_9",  # Replace with real SMM panel service ID
            "category": "Tᴇʟᴇɢʀᴀᴍ",
            "name": "💬 Tɢ Rᴇᴀᴄᴛɪᴏɴs",
            "description": "Tᴇʟᴇɢʀᴀᴍ ᴘᴏsᴛ ʀᴇᴀᴄᴛɪᴏɴs",
            "min": 100,
            "max": 5000,
            "unit": "reactions",
            "price": 25.0,
            "active": True
        }
    ],
    "YᴏᴜTᴜʙᴇ": [
        {
            "id": "yt_likes_temp_10",  # Replace with real SMM panel service ID
            "category": "YᴏᴜTᴜʙᴇ",
            "name": "👍 Yᴛ Lɪᴋᴇs",
            "description": "YᴏᴜTᴜʙᴇ ᴠɪᴅᴇᴏ ʟɪᴋᴇs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 40.0,
            "active": True
        },
        {
            "id": "yt_views_temp_11",  # Replace with real SMM panel service ID
            "category": "YᴏᴜTᴜʙᴇ",
            "name": "👁 Yᴛ Vɪᴇᴡs",
            "description": "YᴏᴜTᴜʙᴇ ᴠɪᴅᴇᴏ ᴠɪᴇᴡs",
            "min": 1000,
            "max": 100000,
            "unit": "views",
            "price": 12.0,
            "active": True
        },
        {
            "id": "yt_subs_temp_12",  # Replace with real SMM panel service ID
            "category": "YᴏᴜTᴜʙᴇ",
            "name": "🔔 Yᴛ Sᴜʙsᴄʀɪʙᴇs",
            "description": "YᴏᴜTᴜʙᴇ ᴄʜᴀɴɴᴇʟ sᴜʙsᴄʀɪʙᴇʀs",
            "min": 50,
            "max": 5000,
            "unit": "subscribers",
            "price": 200.0,
            "active": True
        }
    ],
    "Tᴡɪᴛᴛᴇʀ": [
        {
            "id": "twt_likes_temp_13",  # Replace with real SMM panel service ID
            "category": "Tᴡɪᴛᴛᴇʀ",
            "name": "❤️ Tᴡᴛ Lɪᴋᴇs",
            "description": "Tᴡɪᴛᴛᴇʀ ᴛᴡᴇᴇᴛ ʟɪᴋᴇs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 35.0,
            "active": True
        },
        {
            "id": "twt_retweets_temp_14",  # Replace with real SMM panel service ID
            "category": "Tᴡɪᴛᴛᴇʀ",
            "name": "🔁 Tᴡᴛ Rᴇᴛᴡᴇᴇᴛs",
            "description": "Tᴡɪᴛᴛᴇʀ ʀᴇᴛᴡᴇᴇᴛs",
            "min": 100,
            "max": 5000,
            "unit": "retweets",
            "price": 45.0,
            "active": True
        },
        {
            "id": "twt_follows_temp_15",  # Replace with real SMM panel service ID
            "category": "Tᴡɪᴛᴛᴇʀ",
            "name": "👥 Tᴡᴛ Fᴏʟʟᴏᴡs",
            "description": "Tᴡɪᴛᴛᴇʀ ғᴏʟʟᴏᴡᴇʀs",
            "min": 50,
            "max": 5000,
            "unit": "followers",
            "price": 180.0,
            "active": True
        }
    ],
    "TɪᴋTᴏᴋ": [
        {
            "id": "tik_likes_temp_16",  # Replace with real SMM panel service ID
            "category": "TɪᴋTᴏᴋ",
            "name": "❤️ Tɪᴋ Lɪᴋᴇs",
            "description": "TɪᴋTᴏᴋ ᴠɪᴅᴇᴏ ʟɪᴋᴇs",
            "min": 100,
            "max": 10000,
            "unit": "likes",
            "price": 28.0,
            "active": True
        },
        {
            "id": "tik_views_temp_17",  # Replace with real SMM panel service ID
            "category": "TɪᴋTᴏᴋ",
            "name": "👁 Tɪᴋ Vɪᴇᴡs",
            "description": "TɪᴋTᴏᴋ ᴠɪᴅᴇᴏ ᴠɪᴇᴡs",
            "min": 1000,
            "max": 100000,
            "unit": "views",
            "price": 18.0,
            "active": True
        },
        {
            "id": "tik_follows_temp_18",  # Replace with real SMM panel service ID
            "category": "TɪᴋTᴏᴋ",
            "name": "👥 Tɪᴋ Fᴏʟʟᴏᴡs",
            "description": "TɪᴋTᴏᴋ ᴘʀᴏғɪʟᴇ ғᴏʟʟᴏᴡᴇʀs",
            "min": 50,
            "max": 5000,
            "unit": "followers",
            "price": 160.0,
            "active": True
        }
    ]
}

def get_categories_keyboard():
    """Get inline keyboard for service categories"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for category in SERVICES.keys():
        buttons.append(InlineKeyboardButton(category, callback_data=f"category_{category}"))
    # Add two buttons per row
    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        keyboard.add(*row)
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_main"))
    return keyboard

def get_services_keyboard(category):
    """Get inline keyboard for services in a category"""
    keyboard = InlineKeyboardMarkup()
    for service in SERVICES[category]:
        if service["active"]:
            keyboard.add(InlineKeyboardButton(
                service["name"], 
                callback_data=f"service_{service['id']}"
            ))
    keyboard.add(InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back_to_categories"))
    return keyboard

def get_service_by_id(service_id):
    """Find service by ID"""
    for category_services in SERVICES.values():
        for service in category_services:
            if service["id"] == service_id:
                return service
    return None

def show_service_details(bot, call, service):
    """Show service details and ask for link"""
    caption = f"""
📦 {service['name']}

📝 {service['description']}

📊 Qᴜᴀɴᴛɪᴛʏ Rᴀɴɢᴇ: {service['min']:,} - {service['max']:,} {service['unit']}
💰 Pʀɪᴄᴇ: ₹{service['price']:.2f} ᴘᴇʀ 1,000 {service['unit']}

Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ:
    """.strip()
    
    bot.send_photo(
        call.message.chat.id,
        SERVICE_IMAGE,
        caption=caption
    )
    
    # Store service selection in user data
    from config import users
    user_id = call.from_user.id
    if user_id not in users:
        users[user_id] = {}
    users[user_id]['selected_service'] = service['id']
