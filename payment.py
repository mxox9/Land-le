import requests
import random
import string
import qrcode
import io
from datetime import datetime
from database import deposits_collection
from utils import style_text

def generate_transaction_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def create_payment(amount, user_id):
    """Create payment record and generate QR code"""
    transaction_id = generate_transaction_id()
    
    # UPI Details (you should replace with your actual UPI ID)
    upi_id = "your-upi@oksbi"  # Change this
    upi_url = f"upi://pay?pa={upi_id}&pn=SMM%20Services&am={amount}&cu=INR"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    qr_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Save deposit record
    deposit_data = {
        "deposit_id": transaction_id,
        "user_id": user_id,
        "amount": amount,
        "points": int(amount * 100),  # 1₹ = 100 points
        "status": "pending",
        "created_at": datetime.now()
    }
    deposits_collection.insert_one(deposit_data)
    
    return {
        "transaction_id": transaction_id,
        "qr_code": img_bytes,
        "upi_id": upi_id,
        "amount": amount,
        "points": int(amount * 100)
    }

def verify_payment(transaction_id):
    """Verify payment - in real implementation, integrate with payment gateway"""
    # For demo purposes, we'll assume payment is verified
    # In real implementation, check with payment API
    deposit = deposits_collection.find_one({"deposit_id": transaction_id})
    if deposit:
        deposits_collection.update_one(
            {"deposit_id": transaction_id},
            {"$set": {"status": "completed"}}
        )
        return True
    return False
