import requests
import qrcode
import io
from config import Config
from utils import generate_utr, style_text

class PaymentSystem:
    @staticmethod
    def generate_upi_link(amount: float, utr: str) -> str:
        """Gᴇɴᴇʀᴀᴛᴇ UPI ᴘᴀʏᴍᴇɴᴛ ʟɪɴᴋ"""
        # This would be your actual UPI ID - using placeholder
        upi_id = "your-merchant@upi"
        return f"upi://pay?pa={upi_id}&pn=Merchant&am={amount}&cu=INR&tn=UTR{utr}"
    
    @staticmethod
    def generate_qr_code(upi_link: str) -> bytes:
        """Gᴇɴᴇʀᴀᴛᴇ QR ᴄᴏᴅᴇ ᴜsɪɴɢ ǫʀᴄᴏᴅᴇ ʟɪʙʀᴀʀʏ"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_link)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
    @staticmethod
    def verify_payment(utr: str, amount: float) -> bool:
        """Vᴇʀɪғʏ ᴘᴀʏᴍᴇɴᴛ ᴡɪᴛʜ Aᴜᴛᴏᴅᴇᴘ API"""
        try:
            # Mock API call - replace with actual Autodep API
            headers = {
                'Authorization': f'Bearer {Config.AUTODEP_API_KEY}',
                'X-Merchant-Key': Config.AUTODEP_MERCHANT_KEY
            }
            
            data = {
                'utr': utr,
                'amount': amount
            }
            
            # response = requests.post('https://api.autodep.com/verify', headers=headers, json=data)
            # return response.json().get('status') == 'success'
            
            # For demo purposes, assume payment is successful
            return True
            
        except Exception as e:
            print(f"Payment verification error: {e}")
            return False

def create_deposit_message(amount: float, utr: str, qr_image: bytes) -> tuple:
    """Cʀᴇᴀᴛᴇ ᴅᴇᴘᴏsɪᴛ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ QR ᴄᴏᴅᴇ"""
    caption = style_text(f"""
💰 Dᴇᴘᴏsɪᴛ Rᴇǫᴜᴇsᴛ

Aᴍᴏᴜɴᴛ: ₹{amount}
UTR: {utr}

Sᴄᴀɴ ᴛʜᴇ QR ᴄᴏᴅᴇ ᴏʀ ᴜsᴇ ᴜᴘɪ ʟɪɴᴋ ᴛᴏ ᴘᴀʏ.

Aғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ, ᴄʟɪᴄᴋ "Pᴀɪᴅ ✅" ʙᴜᴛᴛᴏɴ.
""")
    
    return qr_image, caption
