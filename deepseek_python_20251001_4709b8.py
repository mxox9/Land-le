import requests
from config import Config
from utils import style_text, points_to_rupees

class OrderSystem:
    @staticmethod
    def place_smm_order(service_id: int, link: str, quantity: int) -> dict:
        """Pʟᴀᴄᴇ ᴏʀᴅᴇʀ ᴡɪᴛʑ SMM API"""
        try:
            # Mock API call - replace with actual SMM API
            headers = {
                'Authorization': f'Bearer {Config.SMM_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'service': service_id,
                'link': link,
                'quantity': quantity
            }
            
            # response = requests.post(f'{Config.SMM_API_URL}/order', headers=headers, json=data)
            # return response.json()
            
            # For demo purposes, return mock response
            return {
                'status': 'success',
                'order': f'API{service_id}{quantity}',
                'charge': quantity / 100 * 10  # mock charge
            }
            
        except Exception as e:
            print(f"SMM API error: {e}")
            return {'status': 'error', 'message': 'API error'}
    
    @staticmethod
    def get_order_status(api_order_id: str) -> dict:
        """Gᴇᴛ ᴏʀᴅᴇʀ sᴛᴀᴛᴜs ғʀᴏᴍ SMM API"""
        try:
            # Mock API call
            headers = {
                'Authorization': f'Bearer {Config.SMM_API_KEY}'
            }
            
            # response = requests.get(f'{Config.SMM_API_URL}/status/{api_order_id}', headers=headers)
            # return response.json()
            
            # For demo purposes, return mock status
            statuses = ['Pᴇɴᴅɪɴɢ', 'Iɴ Pʀᴏɢʀᴇss', 'Cᴏᴍᴘʟᴇᴛᴇᴅ', 'Pᴀʀᴛɪᴀʟ', 'Cᴀɴᴄᴇʟʟᴇᴅ']
            import random
            return {
                'status': random.choice(statuses),
                'start_count': 0,
                'remains': '0'
            }
            
        except Exception as e:
            print(f"SMM status error: {e}")
            return {'status': 'error'}

def calculate_order_cost(quantity: int, service: dict) -> int:
    """Cᴀʟᴄᴜʟᴀᴛᴇ ᴏʀᴅᴇʀ ᴄᴏsᴛ ɪɴ ᴘᴏɪɴᴛs"""
    units = quantity / service['unit']
    return int(units * service['price'])

def create_order_summary(order_data: dict, service: dict, cost: int) -> str:
    """Cʀᴇᴀᴛᴇ ᴏʀᴅᴇʀ sᴜᴍᴍᴀʀʏ ᴛᴇxᴛ"""
    return style_text(f"""
🛒 Nᴇᴡ Oʀᴅᴇʀ Cʀᴇᴀᴛᴇᴅ

Sᴇʀᴠɪᴄᴇ: {service['name']}
Oʀᴅᴇʀ ID: {order_data['order_id']}
Lɪɴᴋ: {order_data['link']}
Qᴜᴀɴᴛɪᴛʏ: {order_data['quantity']}
Cᴏsᴛ: {cost} ᴘᴏɪɴᴛs (₹{points_to_rupees(cost)})

Sᴛᴀᴛᴜs: Pᴇɴᴅɪɴɢ
""")