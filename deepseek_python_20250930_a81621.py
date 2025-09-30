from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGO_URI'))
db = client.smm_bot

users_collection = db.users
deposits_collection = db.deposits
orders_collection = db.orders

def init_db():
    # Create indexes
    users_collection.create_index("user_id", unique=True)
    deposits_collection.create_index("transaction_id", unique=True)
    orders_collection.create_index("order_id", unique=True)