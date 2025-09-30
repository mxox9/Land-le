import requests
import random
import string
from datetime import datetime
from database import deposits_collection

def generate_transaction_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def create_bharatpe_payment(amount, user_id):
    # Simulate BharatPe payment creation
    transaction_id = generate_transaction_id()
    
    payment_data = {
        "transaction_id": transaction_id,
        "amount": amount,
        "user_id": user_id,
        "status": "pending",
        "created_at": datetime.now(),
        "upi_id": "merchant@bharatpe",  # From env in real implementation
        "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=UPI://pay?pa=merchant@bharatpe&pn=Merchant&am={amount}&tn={transaction_id}"
    }
    
    deposits_collection.insert_one(payment_data)
    return payment_data

def verify_bharatpe_payment(transaction_id):
    # Simulate payment verification
    # In real implementation, integrate with BharatPe API
    deposit = deposits_collection.find_one({"transaction_id": transaction_id})
    if deposit:
        deposits_collection.update_one(
            {"transaction_id": transaction_id},
            {"$set": {"status": "completed"}}
        )
        return True
    return False
