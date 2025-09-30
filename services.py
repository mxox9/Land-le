# In-memory services storage (not in MongoDB)
services_list = [
    {
        "id": 1,
        "category": "Instagram",
        "name": "Instagram Followers",
        "description": "High quality real Instagram followers",
        "min": 100,
        "max": 10000,
        "unit": 100,
        "price_per_unit": 15,  # points per 100 followers
        "active": True,
        "service_id": "101"  # SMM API service ID
    },
    {
        "id": 2,
        "category": "Instagram",
        "name": "Instagram Likes",
        "description": "Premium Instagram likes",
        "min": 100,
        "max": 5000,
        "unit": 100,
        "price_per_unit": 8,  # points per 100 likes
        "active": True,
        "service_id": "102"
    },
    {
        "id": 3,
        "category": "YouTube",
        "name": "YouTube Views",
        "description": "High retention YouTube views",
        "min": 1000,
        "max": 50000,
        "unit": 1000,
        "price_per_unit": 20,  # points per 1000 views
        "active": True,
        "service_id": "201"
    },
    {
        "id": 4,
        "category": "YouTube",
        "name": "YouTube Likes",
        "description": "Real YouTube likes",
        "min": 100,
        "max": 10000,
        "unit": 100,
        "price_per_unit": 12,  # points per 100 likes
        "active": True,
        "service_id": "202"
    },
    {
        "id": 5,
        "category": "Telegram",
        "name": "Telegram Members",
        "description": "Real Telegram channel members",
        "min": 100,
        "max": 10000,
        "unit": 100,
        "price_per_unit": 25,  # points per 100 members
        "active": True,
        "service_id": "301"
    },
    {
        "id": 6,
        "category": "Facebook",
        "name": "Facebook Likes",
        "description": "Real Facebook page likes",
        "min": 100,
        "max": 10000,
        "unit": 100,
        "price_per_unit": 10,  # points per 100 likes
        "active": True,
        "service_id": "401"
    }
]

def get_categories():
    """Get all active categories"""
    categories = set()
    for service in services_list:
        if service['active']:
            categories.add(service['category'])
    return sorted(list(categories))

def get_services_by_category(category):
    """Get services by category"""
    return [service for service in services_list if service['category'] == category and service['active']]

def get_service_by_id(service_id):
    """Get service by ID"""
    try:
        service_id = int(service_id)
        for service in services_list:
            if service['id'] == service_id:
                return service
    except:
        pass
    return None

def add_service(service_data):
    """Add new service to memory"""
    new_id = max([s['id'] for s in services_list]) + 1 if services_list else 1
    service_data['id'] = new_id
    service_data['active'] = True
    services_list.append(service_data)
    return new_id

def update_service(service_id, updates):
    """Update existing service"""
    for i, service in enumerate(services_list):
        if service['id'] == service_id:
            services_list[i].update(updates)
            return True
    return False

def delete_service(service_id):
    """Delete service (set inactive)"""
    for service in services_list:
        if service['id'] == service_id:
            service['active'] = False
            return True
    return False

def get_all_services():
    """Get all active services"""
    return [service for service in services_list if service['active']]
