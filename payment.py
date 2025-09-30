import requests
import random
import string
from datetime import datetime
from database import deposits_collection
from utils import style_text

def generate_transaction_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def create_payment(amount, user_id):
    """Create payment record"""
    transaction_id = generate_transaction_id()
    
    # UPI Details (you should replace with your actual UPI ID)
    upi_id = "smmservices@okaxis"  # Change this to your actual UPI ID
    
    # Calculate points (1₹ = 100 points)
    points = int(amount * 100)
    
    # Save deposit record
    deposit_data = {
        "deposit_id": transaction_id,
        "user_id": user_id,
        "amount": amount,
        "points": points,
        "status": "pending",
        "upi_id": upi_id,
        "created_at": datetime.now()
    }
    deposits_collection.insert_one(deposit_data)
    
    return {
        "transaction_id": transaction_id,
        "upi_id": upi_id,
        "amount": amount,
        "points": points
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

def get_upi_payment_text(amount, upi_id):
    """Generate UPI payment instructions"""
    return style_text(f"""
💵 UPI Payment Instructions

💰 Amount: ₹{amount}
📱 UPI ID: {upi_id}

📋 How to Pay:
1. Open your UPI app (Google Pay, PhonePe, Paytm, etc.)
2. Enter UPI ID: {upi_id}
3. Enter amount: ₹{amount}
4. Add note: "SMM Services"
5. Complete payment

🔍 After payment, click "I Have Paid" below.

📞 Contact support if you face any issues.
    """)
