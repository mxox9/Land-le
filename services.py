# services.py - Predefined services for SMM Bot

SERVICES = [
    # Instagram Services
    {
        "category": "instagram",
        "name": "Insta Likes",
        "service_id": "101",
        "price_per_unit": 50,
        "unit": 1000,
        "min": 100,
        "max": 10000,
        "description": "High-quality Instagram Likes"
    },
    {
        "category": "instagram", 
        "name": "Insta Views",
        "service_id": "4901",
        "price_per_unit": 40,
        "unit": 1000,
        "min": 500,
        "max": 50000,
        "description": "Real Instagram Views"
    },
    {
        "category": "instagram",
        "name": "Insta Followers",
        "service_id": "103", 
        "price_per_unit": 100,
        "unit": 1000,
        "min": 100,
        "max": 10000,
        "description": "Premium Instagram Followers"
    },
    
    # Facebook Services
    {
        "category": "facebook",
        "name": "FB Likes",
        "service_id": "201",
        "price_per_unit": 60,
        "unit": 1000,
        "min": 100,
        "max": 20000,
        "description": "Facebook Page/Post Likes"
    },
    {
        "category": "facebook",
        "name": "FB Views", 
        "service_id": "202",
        "price_per_unit": 45,
        "unit": 1000,
        "min": 500,
        "max": 50000,
        "description": "Facebook Video Views"
    },
    {
        "category": "facebook",
        "name": "FB Followers",
        "service_id": "203",
        "price_per_unit": 120,
        "unit": 1000, 
        "min": 100,
        "max": 15000,
        "description": "Facebook Page Followers"
    },
    
    # YouTube Services
    {
        "category": "youtube",
        "name": "YT Likes",
        "service_id": "301",
        "price_per_unit": 70,
        "unit": 1000,
        "min": 100,
        "max": 25000,
        "description": "YouTube Video Likes"
    },
    {
        "category": "youtube",
        "name": "YT Views",
        "service_id": "302",
        "price_per_unit": 55,
        "unit": 1000,
        "min": 1000,
        "max": 100000,
        "description": "YouTube Video Views"
    },
    {
        "category": "youtube", 
        "name": "YT Subscribers",
        "service_id": "303",
        "price_per_unit": 150,
        "unit": 1000,
        "min": 100,
        "max": 10000,
        "description": "YouTube Channel Subscribers"
    },
    
    # Telegram Services
    {
        "category": "telegram",
        "name": "TG Members",
        "service_id": "401",
        "price_per_unit": 80,
        "unit": 1000,
        "min": 100,
        "max": 50000,
        "description": "Telegram Channel Members"
    },
    {
        "category": "telegram",
        "name": "TG Post Likes",
        "service_id": "402",
        "price_per_unit": 35,
        "unit": 1000,
        "min": 100,
        "max": 50000,
        "description": "Telegram Post Reactions"
    },
    {
        "category": "telegram",
        "name": "TG Post Views",
        "service_id": "403",
        "price_per_unit": 25,
        "unit": 1000,
        "min": 1000,
        "max": 100000,
        "description": "Telegram Post Views"
    }
]

def get_services_by_category(category):
    """Get services by category"""
    return [service for service in SERVICES if service["category"] == category]

def get_all_categories():
    """Get all unique categories"""
    categories = set(service["category"] for service in SERVICES)
    return list(categories)

def get_service_by_id(service_id):
    """Get service by service_id"""
    for service in SERVICES:
        if service["service_id"] == service_id:
            return service
    return None

def update_service_price(service_id, new_price):
    """Update service price"""
    for service in SERVICES:
        if service["service_id"] == service_id:
            service["price_per_unit"] = new_price
            return True
    return False
