import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []
CHANNEL_ID = os.getenv('CHANNEL_ID')
BOT_USERNAME = os.getenv('BOT_USERNAME')

# API Keys
SMM_API_KEY = os.getenv('SMM_API_KEY')
SMM_API_URL = os.getenv('SMM_API_URL')
AUTODEP_API_KEY = os.getenv('AUTODEP_API_KEY')
AUTODEP_MERCHANT_KEY = os.getenv('AUTODEP_MERCHANT_KEY')

# Support
SUPPORT_WHATSAPP = os.getenv('SUPPORT_WHATSAPP')

# Images
WELCOME_IMAGE = os.getenv('WELCOME_IMAGE', 'https://via.placeholder.com/400x200/4A90E2/FFFFFF?text=Welcome+Image')
SERVICE_IMAGE = os.getenv('SERVICE_IMAGE', 'https://via.placeholder.com/400x200/50C878/FFFFFF?text=Service+Image')
DEPOSIT_IMAGE = os.getenv('DEPOSIT_IMAGE', 'https://via.placeholder.com/400x200/F39C12/FFFFFF?text=Deposit+Image')
ACCOUNT_IMAGE = os.getenv('ACCOUNT_IMAGE', 'https://via.placeholder.com/400x200/9B59B6/FFFFFF?text=Account+Image')
HISTORY_IMAGE = os.getenv('HISTORY_IMAGE', 'https://via.placeholder.com/400x200/E74C3C/FFFFFF?text=History+Image')
REFER_IMAGE = os.getenv('REFER_IMAGE', 'https://via.placeholder.com/400x200/3498DB/FFFFFF?text=Refer+Image')
ADMIN_IMAGE = os.getenv('ADMIN_IMAGE', 'https://via.placeholder.com/400x200/2C3E50/FFFFFF?text=Admin+Image')

# In-memory storage
users = {}
orders = {}
deposits = {}
