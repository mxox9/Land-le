import requests
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()

SMM_API_URL = os.getenv('SMM_API_URL', 'https://mysmmapi.com/api/v2')
SMM_API_KEY = os.getenv('SMM_API_KEY', 'a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d')

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def place_smm_order(service_id, link, quantity):
    """Place order via SMM API"""
    try:
        # Using direct API call like in your working example
        api_key = SMM_API_KEY
        url = f"{SMM_API_URL}?key={api_key}&action=add&service={service_id}&link={link}&quantity={quantity}"
        
        print(f"🔗 API URL: {url.replace(api_key, '***')}")
        
        response = requests.get(url, timeout=30)
        print(f"📡 API Response: {response.text}")
        
        data = response.json()
        
        # Check for order ID in response
        if 'order' in data:
            return str(data['order'])
        elif 'order_id' in data:
            return str(data['order_id'])
        elif 'id' in data:
            return str(data['id'])
        else:
            print(f"❌ No order ID in response: {data}")
            return None
            
    except Exception as e:
        print(f"❌ SMM API order error: {e}")
        return None

def check_smm_order(api_order_id):
    """Check order status from SMM API"""
    try:
        params = {
            "key": SMM_API_KEY,
            "action": "status",
            "order": api_order_id
        }
        
        response = requests.get(SMM_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('status', 'Pending')
        return "Pending"
    except Exception as e:
        print(f"Order status check error: {e}")
        return "Pending"
