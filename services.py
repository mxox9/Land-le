services_list = [
    {
        "id": 1,
        "category": "Instagram",
        "name": "Instagram Likes",
        "description": "High quality Instagram likes",
        "min": 100,
        "max": 10000,
        "unit": "like",
        "price_per_unit": 0.50,
        "active": True
    },
    {
        "id": 2,
        "category": "Instagram",
        "name": "Instagram Followers",
        "description": "Real Instagram followers",
        "min": 50,
        "max": 5000,
        "unit": "follower",
        "price_per_unit": 1.20,
        "active": True
    },
    {
        "id": 3,
        "category": "YouTube",
        "name": "YouTube Views",
        "description": "High retention YouTube views",
        "min": 1000,
        "max": 100000,
        "unit": "view",
        "price_per_unit": 0.80,
        "active": True
    },
    {
        "id": 4,
        "category": "YouTube",
        "name": "YouTube Likes",
        "description": "Real YouTube likes",
        "min": 100,
        "max": 10000,
        "unit": "like",
        "price_per_unit": 1.50,
        "active": True
    },
    {
        "id": 5,
        "category": "Telegram",
        "name": "Telegram Members",
        "description": "Real Telegram channel members",
        "min": 100,
        "max": 10000,
        "unit": "member",
        "price_per_unit": 2.00,
        "active": True
    }
]

def add_service(service_data):
    new_id = max([s['id'] for s in services_list]) + 1
    service_data['id'] = new_id
    services_list.append(service_data)
    return new_id

def edit_service(service_id, field, value):
    for service in services_list:
        if service['id'] == service_id:
            service[field] = value
            return True
    return False

def delete_service(service_id):
    global services_list
    services_list = [s for s in services_list if s['id'] != service_id]
    return True
