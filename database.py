import time
from datetime import datetime
from typing import Dict, List, Optional

class MemoryDatabase:
    def __init__(self):
        self.users = {}
        self.orders = []
        self.deposits = []
        self.bot_enabled = True
        
    def get_user(self, user_id: int) -> Dict:
        if user_id not in self.users:
            self.users[user_id] = {
                'user_id': user_id,
                'balance': 0,  # in points (1₹ = 100 points)
                'total_deposits': 0,  # in ₹
                'total_spent': 0,  # in points
                'join_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'referred_by': None,
                'referral_bonus_claimed': False
            }
        return self.users[user_id]
    
    def update_user(self, user_id: int, updates: Dict):
        user = self.get_user(user_id)
        user.update(updates)
        self.users[user_id] = user
    
    def add_order(self, order_data: Dict) -> str:
        order_id = f"ORD{int(time.time())}{len(self.orders)}"
        order_data['order_id'] = order_id
        order_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_data['status'] = 'Pᴇɴᴅɪɴɢ'
        self.orders.append(order_data)
        return order_id
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        for order in self.orders:
            if order['order_id'] == order_id:
                return order
        return None
    
    def update_order(self, order_id: str, updates: Dict):
        for i, order in enumerate(self.orders):
            if order['order_id'] == order_id:
                self.orders[i].update(updates)
                break
    
    def add_deposit(self, deposit_data: Dict):
        deposit_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.deposits.append(deposit_data)
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        return [order for order in self.orders if order['user_id'] == user_id]
    
    def get_stats(self) -> Dict:
        total_users = len(self.users)
        total_orders = len(self.orders)
        total_deposits = sum(deposit['amount'] for deposit in self.deposits if deposit.get('status') == 'Cᴏᴍᴘʟᴇᴛᴇᴅ')
        
        return {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_deposits': total_deposits
        }

# Global database instance
db = MemoryDatabase()
