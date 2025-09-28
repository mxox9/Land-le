import logging
import os
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Database setup
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            balance REAL DEFAULT 0.0,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Services table
    c.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Orders table
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_id INTEGER,
            quantity INTEGER DEFAULT 1,
            total_price REAL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (service_id) REFERENCES services (id)
        )
    ''')
    
    # Transactions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Insert sample services
    services = [
        ('Instagram Followers', 'High quality Instagram followers', 2.50, 'social'),
        ('Instagram Likes', 'Real Instagram likes', 1.50, 'social'),
        ('YouTube Views', 'Organic YouTube views', 5.00, 'video'),
        ('YouTube Likes', 'YouTube likes', 3.00, 'video'),
        ('Twitter Followers', 'Active Twitter followers', 3.00, 'social'),
        ('Facebook Likes', 'Facebook page likes', 2.00, 'social'),
        ('TikTok Views', 'TikTok video views', 4.00, 'video'),
        ('Telegram Members', 'Telegram group members', 6.00, 'messaging')
    ]
    
    c.executemany('''
        INSERT OR IGNORE INTO services (name, description, price, category)
        VALUES (?, ?, ?, ?)
    ''', services)
    
    conn.commit()
    conn.close()

# User management functions
def get_user(user_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def register_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# Service management functions
def get_services(category=None):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    if category:
        c.execute('SELECT * FROM services WHERE category = ? AND is_active = 1', (category,))
    else:
        c.execute('SELECT * FROM services WHERE is_active = 1')
    services = c.fetchall()
    conn.close()
    return services

def get_service(service_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM services WHERE id = ?', (service_id,))
    service = c.fetchone()
    conn.close()
    return service

# Order management functions
def create_order(user_id, service_id, quantity):
    service = get_service(service_id)
    if not service:
        return None
    
    total_price = service[3] * quantity
    
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders (user_id, service_id, quantity, total_price)
        VALUES (?, ?, ?, ?)
    ''', (user_id, service_id, quantity, total_price))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_user_orders(user_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''
        SELECT o.*, s.name 
        FROM orders o 
        JOIN services s ON o.service_id = s.id 
        WHERE o.user_id = ? 
        ORDER BY o.created_at DESC
    ''', (user_id,))
    orders = c.fetchall()
    conn.close()
    return orders

# Transaction management
def add_transaction(user_id, amount, transaction_type, description):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO transactions (user_id, amount, type, description)
        VALUES (?, ?, ?, ?)
    ''', (user_id, amount, transaction_type, description))
    conn.commit()
    conn.close()

# Admin states for conversation handling
admin_states = {}

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Register user if not exists
    if not get_user(user_id):
        register_user(user_id, user.username, user.first_name, user.last_name)
        # Add welcome bonus
        update_balance(user_id, 5.00)
        add_transaction(user_id, 5.00, 'bonus', 'Welcome bonus')
    
    keyboard = [
        [InlineKeyboardButton("🛍️ Services", callback_data="services")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), 
         InlineKeyboardButton("📦 Orders", callback_data="orders")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile"),
         InlineKeyboardButton("📞 Support", callback_data="support")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
👋 Welcome {user.first_name} to Social Media Services Bot!

🤖 **Bot Features:**
• 📊 Social Media Services
• 💰 Easy Balance System  
• 🚀 Fast Delivery
• 📞 24/7 Support

💎 **Welcome Bonus: $5.00 has been added to your account!**

Use the buttons below to navigate:
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "services":
        await show_categories(query)
    elif data == "balance":
        await show_balance(query)
    elif data == "orders":
        await show_orders(query)
    elif data == "profile":
        await show_profile(query)
    elif data == "support":
        await show_support(query)
    elif data == "admin_panel":
        await admin_panel(query)
    elif data.startswith("category_"):
        category = data.split("_")[1]
        await show_services(query, category)
    elif data.startswith("service_"):
        service_id = int(data.split("_")[1])
        await service_details(query, service_id)
    elif data.startswith("buy_"):
        service_id = int(data.split("_")[1])
        await start_buy_process(query, service_id)
    elif data == "back_to_main":
        await start_callback(query, context)
    elif data == "back_to_categories":
        await show_categories(query)
    elif data.startswith("admin_"):
        await handle_admin_commands(query, data)
    elif data == "add_balance":
        await add_balance_handler(query)

async def start_callback(query, context):
    user = query.from_user
    user_id = user.id
    
    keyboard = [
        [InlineKeyboardButton("🛍️ Services", callback_data="services")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), 
         InlineKeyboardButton("📦 Orders", callback_data="orders")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile"),
         InlineKeyboardButton("📞 Support", callback_data="support")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
👋 Welcome {user.first_name} to Social Media Services Bot!

🤖 **Bot Features:**
• 📊 Social Media Services
• 💰 Easy Balance System  
• 🚀 Fast Delivery
• 📞 24/7 Support

Use the buttons below to navigate:
    """
    
    await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_categories(query):
    categories = [
        ("📱 Social Media", "social"),
        ("🎥 Video Services", "video"), 
        ("💬 Messaging Apps", "messaging")
    ]
    
    keyboard = []
    for name, category in categories:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"category_{category}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📊 **Select a Category:**\n\nChoose the type of service you're looking for:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_services(query, category):
    services = get_services(category)
    
    if not services:
        await query.edit_message_text("❌ No services available in this category.")
        return
    
    keyboard = []
    for service in services:
        keyboard.append([
            InlineKeyboardButton(
                f"{service[1]} - ${service[3]:.2f}", 
                callback_data=f"service_{service[0]}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_categories")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    category_names = {
        'social': '📱 Social Media',
        'video': '🎥 Video Services', 
        'messaging': '💬 Messaging Apps'
    }
    
    await query.edit_message_text(
        f"{category_names.get(category, 'Services')}:\n\nSelect a service:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def service_details(query, service_id):
    service = get_service(service_id)
    if not service:
        await query.edit_message_text("❌ Service not found.")
        return
    
    text = f"""
📦 **{service[1]}**

📝 **Description:** {service[2]}
💰 **Price:** ${service[3]:.2f}
🏷️ **Category:** {service[4]}

Ready to order?
    """
    
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Now", callback_data=f"buy_{service_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"category_{service[4]}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def start_buy_process(query, service_id):
    service = get_service(service_id)
    if not service:
        await query.edit_message_text("❌ Service not found.")
        return
    
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if user[4] < service[3]:
        text = f"""
❌ **Insufficient Balance**

💰 Your Balance: ${user[4]:.2f}
📦 Service Price: ${service[3]:.2f}
💵 Needed: ${service[3] - user[4]:.2f}

Please top up your balance to continue.
        """
        keyboard = [
            [InlineKeyboardButton("💳 Add Balance", callback_data="add_balance")],
            [InlineKeyboardButton("⬅️ Back", callback_data=f"service_{service_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        text = f"""
🛒 **Order Summary**

📦 Service: {service[1]}
💰 Price per item: ${service[3]:.2f}
💼 Your Balance: ${user[4]:.2f}

Please send the quantity you want to order (1-1000):
        """
        # Store service ID in context for quantity input
        if 'pending_orders' not in context.bot_data:
            context.bot_data['pending_orders'] = {}
        context.bot_data['pending_orders'][user_id] = service_id
        
        await query.edit_message_text(text, parse_mode='Markdown')

async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    message_text = update.message.text
    
    # Check if user has a pending order
    if 'pending_orders' not in context.bot_data or user_id not in context.bot_data['pending_orders']:
        await update.message.reply_text("Please start the order process from the menu.")
        return
    
    try:
        quantity = int(message_text)
        if quantity < 1 or quantity > 1000:
            await update.message.reply_text("Please enter a quantity between 1 and 1000.")
            return
        
        service_id = context.bot_data['pending_orders'][user_id]
        service = get_service(service_id)
        user = get_user(user_id)
        
        total_price = service[3] * quantity
        
        if user[4] < total_price:
            await update.message.reply_text(
                f"❌ Insufficient balance. Total: ${total_price:.2f}, Your balance: ${user[4]:.2f}"
            )
            return
        
        # Create order and deduct balance
        order_id = create_order(user_id, service_id, quantity)
        update_balance(user_id, -total_price)
        add_transaction(user_id, -total_price, 'purchase', f'Order #{order_id} - {service[1]}')
        
        # Clear pending order
        del context.bot_data['pending_orders'][user_id]
        
        success_text = f"""
✅ **Order Placed Successfully!**

📦 Order ID: #{order_id}
🛍️ Service: {service[1]}
🔢 Quantity: {quantity}
💰 Total Paid: ${total_price:.2f}
💳 Remaining Balance: ${user[4] - total_price:.2f}

We'll start processing your order shortly!
        """
        
        await update.message.reply_text(success_text, parse_mode='Markdown')
        
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")

async def show_balance(query):
    user_id = query.from_user.id
    user = get_user(user_id)
    
    text = f"""
💰 **Balance Information**

💳 Current Balance: **${user[4]:.2f}**

💎 Add balance to start ordering services!
    """
    
    keyboard = [
        [InlineKeyboardButton("💳 Add Balance", callback_data="add_balance")],
        [InlineKeyboardButton("📊 Services", callback_data="services")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def add_balance_handler(query):
    text = """
💳 **Add Balance**

To add balance to your account, please contact our support team:

📞 @YourSupportHandle

We accept various payment methods including:
• 💰 Cryptocurrency
• 💳 Credit/Debit Cards
• 📱 Mobile Payments

Our support team will guide you through the process!
    """
    
    keyboard = [
        [InlineKeyboardButton("📞 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅️ Back", callback_data="balance")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_orders(query):
    user_id = query.from_user.id
    orders = get_user_orders(user_id)
    
    if not orders:
        text = "📦 You haven't placed any orders yet."
    else:
        text = "📦 **Your Orders:**\n\n"
        for order in orders[:10]:  # Show last 10 orders
            status_emoji = "✅" if order[5] == 'completed' else "⏳" if order[5] == 'processing' else "❌"
            text += f"{status_emoji} **Order #{order[0]}**\n"
            text += f"🛍️ {order[8]}\n"
            text += f"🔢 Quantity: {order[3]}\n"
            text += f"💰 Amount: ${order[4]:.2f}\n"
            text += f"📅 Date: {order[6][:16]}\n"
            text += f"📊 Status: {order[5].title()}\n\n"
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_profile(query):
    user_id = query.from_user.id
    user = get_user(user_id)
    
    text = f"""
👤 **Profile Information**

🆔 User ID: `{user[0]}`
👤 Name: {user[2]} {user[3] or ''}
📧 Username: @{user[1] or 'N/A'}
💰 Balance: ${user[4]:.2f}
📅 Member Since: {user[5][:10]}
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_support(query):
    text = """
📞 **Support**

If you need help, have questions, or want to report an issue:

💬 Contact our support team: @YourSupportHandle
📧 Email: support@yourdomain.com
🌐 Website: https://yourwebsite.com

We're here to help you 24/7!
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Admin functions
async def admin_panel(query):
    user_id = query.from_user.id
    # In a real bot, you should check if user is admin
    # For demo, we'll allow anyone to access
    
    text = """
👑 **Admin Panel**

Welcome to the admin dashboard!
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [InlineKeyboardButton("🛍️ Services", callback_data="admin_services")],
        [InlineKeyboardButton("📦 Orders", callback_data="admin_orders")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_commands(query, command):
    if command == "admin_stats":
        conn = sqlite3.connect('bot.db')
        c = conn.cursor()
        
        # Get stats
        c.execute('SELECT COUNT(*) FROM users')
        total_users = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM orders')
        total_orders = c.fetchone()[0]
        
        c.execute('SELECT SUM(total_price) FROM orders WHERE status = "completed"')
        total_revenue = c.fetchone()[0] or 0
        
        c.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
        pending_orders = c.fetchone()[0]
        
        conn.close()
        
        text = f"""
📊 **Bot Statistics**

👥 Total Users: {total_users}
📦 Total Orders: {total_orders}
💰 Total Revenue: ${total_revenue:.2f}
⏳ Pending Orders: {pending_orders}
        """
        
    elif command == "admin_users":
        text = "👥 User management features coming soon..."
    elif command == "admin_services":
        text = "🛍️ Service management features coming soon..."
    elif command == "admin_orders":
        text = "📦 Order management features coming soon..."
    else:
        text = "❌ Unknown command"
    
    keyboard = [[InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **Bot Help Guide**

**Available Commands:**
/start - Start the bot and show main menu
/help - Show this help message

**How to Use:**
1. Use the menu buttons to navigate
2. Select a service category
3. Choose your desired service
4. Check your balance and order

**Need Help?**
Contact support through the main menu!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception occurred:", exc_info=context.error)

def main():
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()