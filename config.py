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
WELCOME_IMAGE = os.getenv('WELCOME_IMAGE', 'https://t.me/prooflelo1/138?single')
SERVICE_IMAGE = os.getenv('SERVICE_IMAGE', 'https://t.me/prooflelo1/138?single')
DEPOSIT_IMAGE = os.getenv('DEPOSIT_IMAGE', 'https://t.me/prooflelo1/138?single')
ACCOUNT_IMAGE = os.getenv('ACCOUNT_IMAGE', 'https://t.me/prooflelo1/138?single')
HISTORY_IMAGE = os.getenv('HISTORY_IMAGE', 'https://t.me/prooflelo1/138?single')
REFER_IMAGE = os.getenv('REFER_IMAGE', 'https://t.me/prooflelo1/138?single')
ADMIN_IMAGE = os.getenv('ADMIN_IMAGE', 'https://t.me/prooflelo1/138?single')

# In-memory storage
users = {}
orders = {}
deposits = {}
