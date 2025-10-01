import random
import string
from typing import List, Dict

def style_text(text: str) -> str:
    """Cᴏɴᴠᴇʀᴛ ᴛᴇxᴛ ᴛᴏ sᴛʏʟɪᴢᴇᴅ ғᴏɴᴛ"""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    styled = "AʙᴄᴅEғɢʜIᴊᴋʟMɴᴏᴘQʀsᴛUᴠᴡxYᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    
    translation_table = str.maketrans(normal, styled)
    return text.translate(translation_table)

def generate_utr() -> str:
    """Gᴇɴᴇʀᴀᴛᴇ ʀᴀɴᴅᴏᴍ 12-ᴅɪɢɪᴛ UTR"""
    return ''.join(random.choices(string.digits, k=12))

def get_categories(services: List[Dict]) -> List[str]:
    """Gᴇᴛ ᴜɴɪǫᴜᴇ ᴄᴀᴛᴇɢᴏʀɪᴇs ғʀᴏᴍ sᴇʀᴠɪᴄᴇs"""
    return list(set(service['category'] for service in services))

def get_services_by_category(category: str, services: List[Dict]) -> List[Dict]:
    """Gᴇᴛ sᴇʀᴠɪᴄᴇs ʙʏ ᴄᴀᴛᴇɢᴏʀʏ"""
    return [service for service in services if service['category'] == category]

def points_to_rupees(points: int) -> float:
    """Cᴏɴᴠᴇʀᴛ ᴘᴏɪɴᴛs ᴛᴏ ʀᴜᴘᴇᴇs"""
    return points / 100

def rupees_to_points(rupees: float) -> int:
    """Cᴏɴᴠᴇʀᴛ ʀᴜᴘᴇᴇs ᴛᴏ ᴘᴏɪɴᴛs"""
    return int(rupees * 100)

def validate_quantity(quantity: int, service: Dict) -> tuple:
    """Vᴀʟɪᴅᴀᴛᴇ ǫᴜᴀɴᴛɪᴛʏ ᴀɢᴀɪɴsᴛ sᴇʀᴠɪᴄᴇ ʟɪᴍɪᴛs"""
    if quantity < service['min']:
        return False, style_text(f"Mɪɴɪᴍᴜᴍ ǫᴜᴀɴᴛɪᴛʏ ɪs {service['min']}")
    
    if quantity > service['max']:
        return False, style_text(f"Mᴀxɪᴍᴜᴍ ǫᴜᴀɴᴛɪᴛʏ ɪs {service['max']}")
    
    if quantity % service['unit'] != 0:
        return False, style_text(f"Qᴜᴀɴᴛɪᴛʏ ᴍᴜsᴛ ʙᴇ ɪɴ ᴍᴜʟᴛɪᴘʟᴇs ᴏғ {service['unit']}")
    
    return True, ""
