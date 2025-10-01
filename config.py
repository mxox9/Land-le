import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
    CHANNEL_ID = os.getenv('CHANNEL_ID', '').replace('@', '')
    BOT_USERNAME = os.getenv('BOT_USERNAME', '').replace('@', '')
    
    # SMM API
    SMM_API_KEY = os.getenv('SMM_API_KEY')
    SMM_API_URL = os.getenv('SMM_API_URL')
    
    # Payment API
    AUTODEP_API_KEY = os.getenv('AUTODEP_API_KEY')
    AUTODEP_MERCHANT_KEY = os.getenv('AUTODEP_MERCHANT_KEY')
    
    # Support
    SUPPORT_WHATSAPP = os.getenv('SUPPORT_WHATSAPP')
    
    # Referral bonus
    REFERRAL_BONUS = 500  # points
    
    # Services (Hardcoded as required)
    SERVICES = [
        {
            "id": 1001,
            "category": "Iɴsᴛᴀɢʀᴀᴍ",
            "name": "Iɴsᴛᴀɢʀᴀᴍ Lɪᴋᴇs",
            "description": "Gᴇᴛ ʜɪɢʜ-ǫᴜᴀʟɪᴛʏ ʟɪᴋᴇs",
            "min": 100,
            "max": 10000,
            "unit": 100,
            "price": 1500  # price per unit in points
        },
        {
            "id": 1002,
            "category": "Iɴsᴛᴀɢʀᴀᴍ", 
            "name": "Iɴsᴛᴀɢʀᴀᴍ Fᴏʟʟᴏᴡᴇʀs",
            "description": "Gᴇᴛ ʀᴇᴀʟ ғᴏʟʟᴏᴡᴇʀs",
            "min": 100,
            "max": 5000,
            "unit": 100,
            "price": 2000
        },
        {
            "id": 2001,
            "category": "YᴏᴜTᴜʙᴇ",
            "name": "YᴏᴜTᴜʙᴇ Vɪᴇᴡs", 
            "description": "Gᴇᴛ ʜɪɢʜ-ʀᴇᴛᴇɴᴛɪᴏɴ ᴠɪᴇᴡs",
            "min": 1000,
            "max": 100000,
            "unit": 1000,
            "price": 1000
        },
        {
            "id": 3001,
            "category": "Tᴇʟᴇɢʀᴀᴍ",
            "name": "Tᴇʟᴇɢʀᴀᴍ Mᴇᴍʙᴇʀs",
            "description": "Gᴇᴛ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs",
            "min": 100,
            "max": 50000,
            "unit": 100,
            "price": 1200
        }
    ]
