# utils.py - Helper functions
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
    """Return a dummy QR code image (skip actual qrcode module)"""
    # Aap apna QR image Telegram ya Imgur pe upload karke link paste kar sakte ho
    return "https://t.me/prooflelo1/136?single"

def generate_order_id():
    """Generate unique order ID"""
    return f"ORD{random.randint(100000, 999999)}"

def format_currency(amount):
    """Format amount as Indian Rupees"""
    return f"₹{amount:.2f}"
