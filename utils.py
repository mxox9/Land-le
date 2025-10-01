# utils.py - Helper functions
import qrcode
import io
import random
from datetime import datetime

def style_text(text):
    """Convert text to stylish format with first letter capitalized and rest small"""
    def style_word(word):
        if len(word) > 0:
            return word[0] + word[1:].lower()
        return word
    
    words = text.split()
    styled_words = []
    
    for word in words:
        if any(char.isalpha() for char in word):
            styled_words.append(style_word(word))
        else:
            styled_words.append(word)
    
    return ' '.join(styled_words)

def generate_qr_code(amount, upi_id="your-upi@oksbi"):
    """Generate QR code for UPI payment"""
    upi_url = f"upi://pay?pa={upi_id}&pn=SMM%20Services&am={amount}&cu=INR"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def generate_order_id():
    """Generate unique order ID"""
    return f"ORD{random.randint(100000, 999999)}"

def format_currency(amount):
    """Format amount as Indian Rupees"""
    return f"₹{amount:.2f}"
