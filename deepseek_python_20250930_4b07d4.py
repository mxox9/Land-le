import os
import re
from datetime import datetime

# Stylish text mapping for the special font style
STYLISH_MAPPING = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
    'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ',
    'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
    'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'H': 'H', 'I': 'I', 'J': 'J',
    'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T',
    'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z'
}

def style_text(text):
    """Convert text to stylish format with special font style"""
    if not text:
        return text
    
    def style_word(word):
        if len(word) > 0:
            # Keep first letter as is, convert rest to stylish lowercase
            styled_word = word[0]
            for char in word[1:]:
                styled_word += STYLISH_MAPPING.get(char.lower(), char.lower())
            return styled_word
        return word
    
    # Split into words and apply styling
    words = text.split()
    styled_words = []
    
    for word in words:
        # Handle special characters and emojis
        if any(char.isalpha() for char in word):
            styled_words.append(style_word(word))
        else:
            styled_words.append(word)
    
    return ' '.join(styled_words)

def is_admin(user_id, admin_ids):
    """Check if user is admin"""
    return user_id in admin_ids

def validate_amount(amount_text):
    """Validate amount input"""
    try:
        amount = float(amount_text)
        if amount < 10:
            return False, "Mɪɴɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ ᴀᴍᴏᴜɴᴛ ɪs ₹10"
        return True, amount
    except ValueError:
        return False, "Iɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ! Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ"

def validate_quantity(quantity_text, min_qty, max_qty):
    """Validate quantity input"""
    try:
        quantity = int(quantity_text)
        if quantity < min_qty or quantity > max_qty:
            return False, f"Qᴜᴀɴᴛɪᴛʏ ᴍᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ {min_qty} ᴀɴᴅ {max_qty}"
        return True, quantity
    except ValueError:
        return False, "Iɴᴠᴀʟɪᴅ ǫᴜᴀɴᴛɪᴛʏ! Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ"