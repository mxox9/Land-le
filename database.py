from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize collections as None initially
users_collection = None
orders_collection = None
deposits_collection = None
admin_logs_collection = None
config_collection = None
settings_collection = None

# MongoDB connection with error handling
try:
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb+srv://saifulmolla79088179_db_user:17gNrX0pC3bPqVaG@cluster0.fusvqca.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0'), serverSelectionTimeoutMS=5000)
    db = client.smm_bot
    
    # Test connection
    client.admin.command('ismaster')
    print("✅ MongoDB connected successfully")
    
    # Initialize collections
    users_collection = db.users
    orders_collection = db.orders
    deposits_collection = db.deposits
    admin_logs_collection = db.admin_logs
    config_collection = db.config
    settings_collection = db.settings
    
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    print("🔄 Running in limited mode without database")

def init_database():
    """Initialize database with default settings"""
    if users_collection is None:
        print("❌ Database not available - running in limited mode")
        return
    
    try:
        # Create indexes only if collections exist
        users_collection.create_index("user_id", unique=True)
        orders_collection.create_index("order_id", unique=True)
        deposits_collection.create_index("deposit_id", unique=True)
        
        # Initialize settings
        if not settings_collection.find_one({"_id": "bot_settings"}):
            settings_collection.insert_one({
                "_id": "bot_settings",
                "accepting_orders": True
            })
        
        if not config_collection.find_one({"_id": "bot_config"}):
            config_collection.insert_one({
                "_id": "bot_config",
                "maintenance_mode": False
            })
            
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

def get_user(user_id):
    """Get user by ID, create if not exists"""
    if users_collection is None:
        # Fallback for when database is not available
        return {
            "user_id": user_id,
            "balance_points": 0,
            "total_deposits_points": 0,
            "total_spent_points": 0,
            "joined_at": datetime.now(),
            "banned": False
        }
    
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        user_data = {
            "user_id": user_id,
            "balance_points": 0,
            "total_deposits_points": 0,
            "total_spent_points": 0,
            "joined_at": datetime.now(),
            "banned": False
        }
        users_collection.insert_one(user_data)
        return user_data
    return user

def update_user_balance(user_id, points_change, is_deposit=False, is_spent=False):
    """Update user balance"""
    if users_collection is None:
        return 0  # Return 0 balance if DB not available
    
    user = get_user(user_id)
    update_data = {"$inc": {"balance_points": points_change}}
    
    if is_deposit:
        update_data["$inc"]["total_deposits_points"] = points_change
    elif is_spent:
        update_data["$inc"]["total_spent_points"] = points_change
    
    users_collection.update_one({"user_id": user_id}, update_data)
    return users_collection.find_one({"user_id": user_id})["balance_points"]

def create_order(user_id, service_data, link, quantity, cost_points, api_order_id=None):
    """Create new order"""
    if orders_collection is None:
        return None  # Return None if DB not available
    
    import random
    from utils import style_text
    
    order_id = f"ORD{random.randint(100000, 999999)}"
    
    order = {
        "order_id": order_id,
        "api_order_id": api_order_id,
        "user_id": user_id,
        "service_name": service_data["name"],
        "service_category": service_data["category"],
        "link": link,
        "quantity": quantity,
        "cost_points": cost_points,
        "status": "Pending",
        "created_at": datetime.now(),
        "last_check": datetime.now()
    }
    
    orders_collection.insert_one(order)
    return order

def get_user_orders(user_id, limit=10):
    """Get user orders"""
    if orders_collection is None:
        return []  # Return empty list if DB not available
    
    return list(orders_collection.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit))

def get_order_by_id(order_id):
    """Get order by order ID"""
    if orders_collection is None:
        return None  # Return None if DB not available
    
    return orders_collection.find_one({"order_id": order_id})

def log_admin_action(admin_id, action, details):
    """Log admin actions"""
    if admin_logs_collection is None:
        return  # Skip logging if DB not available
    
    admin_logs_collection.insert_one({
        "admin_id": admin_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now()
    })

def get_bot_settings():
    """Get bot settings"""
    if settings_collection is None:
        return {"accepting_orders": True}  # Default settings if DB not available
    
    return settings_collection.find_one({"_id": "bot_settings"})

def set_bot_accepting_orders(status):
    """Set bot accepting orders status"""
    if settings_collection is None:
        return  # Skip if DB not available
    
    settings_collection.update_one(
        {"_id": "bot_settings"},
        {"$set": {"accepting_orders": status}},
        upsert=True
    )

def is_bot_accepting_orders():
    """Check if bot is accepting orders"""
    settings = get_bot_settings()
    return settings.get("accepting_orders", True) if settings else True

def get_total_users():
    """Get total users count"""
    if users_collection is None:
        return 0
    return users_collection.count_documents({})

def get_total_orders():
    """Get total orders count"""
    if orders_collection is None:
        return 0
    return orders_collection.count_documents({})

def get_total_deposits():
    """Get total deposits amount"""
    if deposits_collection is None:
        return 0
    
    result = deposits_collection.aggregate([
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    
    deposits_list = list(result)
    return deposits_list[0]['total'] if deposits_list else 0
