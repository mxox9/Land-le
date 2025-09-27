# bot.py
# Single-file Telegram SMM bot (stylish English texts + /adminox password login)
# - Uses pyTelegramBotAPI, MongoDB, APScheduler
# - Admin login via /adminox with password "SmOx9679"
# - All user-facing text stylized (first char uppercase normal, rest small-cap style)
# Configure env vars: BOT_TOKEN, MONGO_URI, ADMIN_IDS (comma separated)
# Run: python bot.py

import os
import time
import threading
import traceback
import random
import string
from datetime import datetime, timedelta
from functools import wraps

import requests
from pymongo import MongoClient, ReturnDocument
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, InputMediaPhoto

load_dotenv()

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")  # e.g. "6052975324,1234567"
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]
QR_IMAGE_URL = os.getenv("QR_IMAGE_URL", "https://t.me/prooflelo1/27")
AUTO_REFUND_INTERVAL = int(os.getenv("AUTO_REFUND_INTERVAL", "300"))  # seconds
ADMIN_PASSWORD = "SmOx9679"  # as requested

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN env var required")
    exit(1)

# === INIT ===
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
client = MongoClient(MONGO_URI)
db = client.get_database("smm_bot_db_v2")

services_col = db.services
users_col = db.users
orders_col = db.orders
temp_col = db.temp_orders
config_col = db.config
admin_sessions = db.admin_sessions  # stores admin login sessions

# Ensure default config
def get_config():
    cfg = config_col.find_one({})
    if not cfg:
        cfg = {"maintenance": False, "qr_image": QR_IMAGE_URL}
        config_col.insert_one(cfg)
    return cfg

get_config()

# Lock for atomic balance operations
balance_lock = threading.Lock()

# === Stylish small-cap mapping ===
SMALL_CAPS_MAP = {
    "a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ꜰ","g":"ɢ","h":"ʜ","i":"ɪ","j":"ᴊ",
    "k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ","o":"ᴏ","p":"ᴘ","q":"ǫ","r":"ʀ","s":"s","t":"ᴛ",
    "u":"ᴜ","v":"ᴠ","w":"ᴡ","x":"x","y":"ʏ","z":"ᴢ"
}

def stylize_word(word: str) -> str:
    """
    Make first character normal uppercase, rest mapped to small-cap-like characters where possible.
    Example: "Instagram Like" -> "Iɴsᴛᴀɢʀᴀᴍ Lɪᴋᴇ"
    We'll apply per word and preserve spaces/punctuation.
    """
    def stylize_token(token):
        if not token:
            return token
        first = token[0].upper()
        rest = ""
        for ch in token[1:]:
            lower = ch.lower()
            rest += SMALL_CAPS_MAP.get(lower, ch)
        return first + rest
    # apply token-by-token (split by spaces)
    tokens = word.split(" ")
    return " ".join(stylize_token(t) for t in tokens)

def S(text):
    """Stylize helper for messages. You can include emoji normally."""
    return stylize_word(text)

# === Utilities ===
def is_admin_id(uid):
    return uid in ADMIN_IDS

def gen_utr():
    return ''.join(random.choice(string.digits) for _ in range(12))

def send_admin_log(text):
    for aid in ADMIN_IDS:
        try:
            bot.send_message(aid, text)
        except:
            pass

# Seed minimal services if empty (keeps example images from your code)
def seed_services():
    if services_col.count_documents({}) == 0:
        sample = [
            {"category":"instagram","name":"IG Followers (Non Drop)","service_id":"4618","api_key":"a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d","api_url":"https://mysmmapi.com/api/v2","price_per_100":350,"min_qty":100,"max_qty":1000000,"description":"⚡ Instant IG Non-Drop Followers. Make sure profile is public.","image_url":"https://t.me/prooflelo1/19","active":True},
            {"category":"instagram","name":"IG Likes","service_id":"4961","api_key":"a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d","api_url":"https://mysmmapi.com/api/v2","price_per_100":250,"min_qty":100,"max_qty":1000000,"description":"❤️ IG Post Likes. Fast start.","image_url":"https://t.me/prooflelo1/27","active":True},
            {"category":"youtube","name":"YT Subscribe","service_id":"3942","api_key":"6a37fe62a9cf761f5d53b82f5156894558e06043","api_url":"https://mysmmapi.com/api/v2","price_per_1000":3500,"min_qty":1000,"max_qty":10000000,"description":"📺 YouTube Subscribers. Minimum 1000.","image_url":"https://t.me/prooflelo1/28","active":True},
            {"category":"telegram","name":"TG Subscribe","service_id":"4956","api_key":"a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d","api_url":"https://mysmmapi.com/api/v2","price_per_100":750,"min_qty":100,"max_qty":10000000,"description":"📡 Telegram Subscribers. Public channel required.","image_url":"https://t.me/prooflelo1/27","active":True},
            {"category":"facebook","name":"FB Followers","service_id":"4618","api_key":"a9bbe2f7d1a748b62cf5d1e195d06a165e3cc36d","api_url":"https://mysmmapi.com/api/v2","price_per_1000":3500,"min_qty":100,"max_qty":10000000,"description":"📘 Facebook Followers. Public profile required.","image_url":"https://t.me/prooflelo1/19","active":True}
        ]
        services_col.insert_many(sample)

seed_services()

# === Keyboards builders ===
def start_buttons():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(S("💳 Deposit"), callback_data="deposit"))
    kb.add(InlineKeyboardButton(S("🛒 Order"), callback_data="order"))
    kb.add(InlineKeyboardButton(S("📜 History"), callback_data="history"))
    kb.add(InlineKeyboardButton(S("🎁 Refer"), callback_data="refer"))
    return kb

def category_buttons():
    kb = InlineKeyboardMarkup()
    cats = services_col.distinct("category", {"active": True})
    pref = ["instagram","facebook","telegram","youtube"]
    ordered = [c for c in pref if c in cats] + [c for c in cats if c not in pref]
    for c in ordered:
        emoji = {"instagram":"📸","facebook":"📘","telegram":"📡","youtube":"📺"}.get(c,"⭐")
        kb.add(InlineKeyboardButton(S(f"{emoji} {c.title()}"), callback_data=f"cat:{c}"))
    kb.add(InlineKeyboardButton(S("◀️ Back"), callback_data="back_start"))
    return kb

def services_buttons_for_category(category):
    kb = InlineKeyboardMarkup()
    docs = list(services_col.find({"category":category, "active":True}))
    for s in docs:
        kb.add(InlineKeyboardButton(S(s.get("name")), callback_data=f"svc:{str(s['_id'])}"))
    kb.add(InlineKeyboardButton(S("◀️ Back"), callback_data="cat_back"))
    return kb

def service_action_kb(sid):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(S("ℹ️ Info"), callback_data=f"info:{sid}"), InlineKeyboardButton(S("✅ Order"), callback_data=f"order_svc:{sid}"))
    kb.add(InlineKeyboardButton(S("◀️ Back"), callback_data="svc_back"))
    return kb

# === /start handler ===
@bot.message_handler(commands=["start","help"])
def cmd_start(msg):
    uid = msg.from_user.id
    # ensure user record
    users_col.update_one({"tg_id": uid}, {"$setOnInsert": {"tg_id": uid, "balance_points": 0, "created_at": datetime.utcnow()}}, upsert=True)
    cfg = get_config()
    try:
        bot.send_photo(uid, cfg.get("qr_image", QR_IMAGE_URL), caption=S("👋 Welcome! Use buttons below to continue."), reply_markup=start_buttons())
    except Exception:
        bot.send_message(uid, S("👋 Welcome! Use buttons below to continue."), reply_markup=start_buttons())

# === Callback central ===
@bot.callback_query_handler(func=lambda c: True)
def cb_router(c):
    try:
        data = c.data
        uid = c.from_user.id
        cfg = get_config()
        if data == "deposit":
            return handle_deposit_start(c)
        if data == "order":
            bot.answer_callback_query(c.id)
            try:
                bot.edit_message_caption(S("🔰 Choose a category:"), c.message.chat.id, c.message.message_id, reply_markup=category_buttons())
            except:
                bot.edit_message_text(S("🔰 Choose a category:"), c.message.chat.id, c.message.message_id, reply_markup=category_buttons())
            return
        if data == "history":
            return handle_history_start(c)
        if data == "refer":
            return handle_refer(c)
        if data == "back_start":
            bot.answer_callback_query(c.id)
            try:
                bot.edit_message_caption(S("🏠 Main Menu"), c.message.chat.id, c.message.message_id, reply_markup=start_buttons())
            except:
                bot.edit_message_text(S("🏠 Main Menu"), c.message.chat.id, c.message.message_id, reply_markup=start_buttons())
            return
        if data.startswith("cat:"):
            cat = data.split(":",1)[1]
            return handle_category(c, cat)
        if data == "cat_back":
            bot.answer_callback_query(c.id)
            try:
                bot.edit_message_caption(S("🔰 Choose a category:"), c.message.chat.id, c.message.message_id, reply_markup=category_buttons())
            except:
                bot.edit_message_text(S("🔰 Choose a category:"), c.message.chat.id, c.message.message_id, reply_markup=category_buttons())
            return
        if data.startswith("svc:"):
            sid = data.split(":",1)[1]
            return handle_service_view(c, sid)
        if data == "svc_back":
            bot.answer_callback_query(c.id)
            try:
                bot.edit_message_caption(S("🔰 Choose a category:"), c.message.chat.id, c.message.message_id, reply_markup=category_buttons())
            except:
                bot.edit_message_text(S("🔰 Choose a category:"), c.message.chat.id, c.message.message_id, reply_markup=category_buttons())
            return
        if data.startswith("info:"):
            sid = data.split(":",1)[1]
            return handle_service_info(c, sid)
        if data.startswith("order_svc:"):
            if cfg.get("maintenance", False):
                bot.answer_callback_query(c.id, S("⚠️ Maintenance mode active. Try later."), show_alert=True)
                return
            sid = data.split(":",1)[1]
            return start_order_flow(c, sid)
        if data.startswith("confirm_order:"):
            tempid = data.split(":",1)[1]
            return confirm_temp_order(c, tempid)
        if data.startswith("cancel_temp:"):
            tempid = data.split(":",1)[1]
            temp_col.delete_one({"_id": tempid})
            bot.answer_callback_query(c.id, S("❌ Order cancelled."))
            return
        # history paging
        if data.startswith("history:page:"):
            page = int(data.split(":")[-1])
            return show_history_page(c, page)
        # admin callbacks (only active after admin login)
        if data.startswith("admin:"):
            return admin_callback_router(c)
        bot.answer_callback_query(c.id, S("❗ Unknown action"))
    except Exception as e:
        traceback.print_exc()
        try:
            bot.answer_callback_query(c.id, S("❌ Error occurred"))
        except:
            pass

# === Deposit flows ===
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("deposit"))
def handle_deposit_start(c):
    uid = c.from_user.id
    cfg = get_config()
    qr = cfg.get("qr_image", QR_IMAGE_URL)
    bot.answer_callback_query(c.id)
    msg = (
        S("💳 Deposit") + "\n\n" +
        S("Scan the QR or use the UPI link. After payment, send UTR (12 digits) and screenshot for verification.")
    )
    try:
        bot.send_photo(uid, qr, caption=msg)
    except:
        bot.send_message(uid, msg)

# Simple manual deposit via text (fallback)
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("deposit"))
def deposit_manual(m):
    uid = m.from_user.id
    bot.send_message(uid, S("💳 Send deposit amount in INR (example: 100)"), reply_markup=ForceReply(selective=True))

# Paid flow simplified: admin will verify via admin menu
# We'll accept messages containing "UTR" and store as pending deposit
@bot.message_handler(func=lambda m: True, content_types=['text','photo'])
def generic_message_handler(m):
    """
    This generic handler will:
    - accept deposit messages that include a 12-digit UTR and save to user.pending_deposit
    - otherwise ignore (or used in order flow via ForceReply handlers registered inline)
    """
    try:
        text = (m.text or "").strip()
        uid = m.from_user.id
        # detect UTR 12 digits
        import re
        match = re.search(r"\b(\d{12})\b", text)
        if match:
            utr = match.group(1)
            # if photo included, get file_id
            photo_id = None
            if m.content_type == 'photo':
                photo_id = m.photo[-1].file_id
            users_col.update_one({"tg_id": uid}, {"$set": {"pending_deposit": {"amount_text": text, "utr": utr, "screenshot": photo_id, "created_at": datetime.utcnow()}}}, upsert=True)
            bot.send_message(uid, S("✅ Deposit request saved. Admin will verify soon."))
            # notify admins
            send_admin_log(S(f"📥 New deposit request from {uid} • UTR: {utr}"))
            return
    except Exception:
        traceback.print_exc()
    # otherwise, we may ignore here (order flow uses ForceReply handlers separately)

# === Category & Service view ===
def handle_category(c, cat):
    uid = c.from_user.id
    docs = list(services_col.find({"category":cat, "active":True}))
    if not docs:
        bot.answer_callback_query(c.id, S("No services available in this category."))
        return
    text = S(f"🔰 {cat.title()} Services")
    try:
        bot.edit_message_caption(text, c.message.chat.id, c.message.message_id, reply_markup=services_buttons_for_category(cat))
    except:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=services_buttons_for_category(cat))
    bot.answer_callback_query(c.id)

def handle_service_view(c, sid):
    uid = c.from_user.id
    # sid stored as string id
    from bson import ObjectId
    svc = services_col.find_one({"_id": ObjectId(sid)})
    if not svc:
        bot.answer_callback_query(c.id, S("Service not found"))
        return
    img = svc.get("image_url", QR_IMAGE_URL)
    caption = f"<b>{stylize_word(svc.get('name'))}</b>\n\n{svc.get('description')}\n\n<b>{stylize_word('Min')}:</b> {svc.get('min_qty')}  <b>{stylize_word('Max')}:</b> {svc.get('max_qty')}"
    try:
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id, media=InputMediaPhoto(img, caption=caption), reply_markup=service_action_kb(sid))
    except Exception:
        bot.send_message(uid, caption, reply_markup=service_action_kb(sid))
    bot.answer_callback_query(c.id)

def handle_service_info(c, sid):
    from bson import ObjectId
    svc = services_col.find_one({"_id": ObjectId(sid)})
    if not svc:
        bot.answer_callback_query(c.id, S("Service not found"))
        return
    text = (
        f"<b>{stylize_word(svc.get('name'))}</b>\n\n"
        f"{svc.get('description')}\n\n"
        f"<b>Service ID:</b> {svc.get('service_id')}\n"
        f"<b>API URL:</b> {svc.get('api_url')}\n"
        f"<b>Min:</b> {svc.get('min_qty')}  <b>Max:</b> {svc.get('max_qty')}"
    )
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, text)

# === Order flow (temp storage approach) ===
def start_order_flow(c, sid):
    uid = c.from_user.id
    from bson import ObjectId
    svc = services_col.find_one({"_id": ObjectId(sid)})
    if not svc:
        bot.answer_callback_query(c.id, S("Service not found"))
        return
    # create temp doc
    temp_id = ''.join(random.choice("0123456789abcdef") for _ in range(16))
    temp_col.insert_one({"_id": temp_id, "user_id": uid, "svc_id": sid, "created_at": datetime.utcnow()})
    bot.answer_callback_query(c.id)
    msg = bot.send_message(uid, S("🔗 Please send the PUBLIC link (example: https://...)"), reply_markup=ForceReply(selective=True))
    # register inline handler by checking reply_to_message id using a small closure
    @bot.message_handler(func=lambda m: m.reply_to_message and m.reply_to_message.message_id == msg.message_id and m.from_user.id == uid)
    def receive_link(m):
        try:
            link = m.text.strip()
            temp_col.update_one({"_id": temp_id, "user_id": uid}, {"$set": {"link": link}})
            bot.send_message(uid, S(f"🔢 Now send quantity (Minimum {svc.get('min_qty')})"), reply_markup=ForceReply(selective=True))
            @bot.message_handler(func=lambda mm: mm.reply_to_message and mm.reply_to_message.message_id == m.message_id and mm.from_user.id == uid)
            def receive_qty(mm):
                try:
                    qty = int(mm.text.strip())
                except:
                    bot.send_message(uid, S("❌ Invalid number. Please send numeric quantity."))
                    return
                if svc.get('min_qty') and qty < svc.get('min_qty'):
                    bot.send_message(uid, S(f"❌ Minimum order is {svc.get('min_qty')}"))
                    return
                if svc.get('max_qty') and svc.get('max_qty')>0 and qty > svc.get('max_qty'):
                    bot.send_message(uid, S(f"❌ Maximum order is {svc.get('max_qty')}"))
                    return
                # compute cost in points
                points = 0
                if svc.get('price_per_100'):
                    points = int((qty/100.0) * svc.get('price_per_100'))
                elif svc.get('price_per_1000'):
                    points = int((qty/1000.0) * svc.get('price_per_1000'))
                else:
                    points = int((qty/100.0)*100)  # fallback
                user = users_col.find_one({"tg_id": uid}) or {"balance_points":0}
                if user.get("balance_points",0) < points:
                    bot.send_message(uid, S(f"❌ Insufficient balance. Need {points} Points (₹{points/100:.2f}). Your balance: {user.get('balance_points',0)} Points."))
                    return
                # save qty & cost in temp
                temp_col.update_one({"_id": temp_id}, {"$set": {"quantity": qty, "points_cost": points}})
                # show confirm inline
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton(S("✅ Confirm Order"), callback_data=f"confirm_order:{temp_id}"), InlineKeyboardButton(S("❌ Cancel"), callback_data=f"cancel_temp:{temp_id}"))
                bot.send_message(uid, S("🧾 Confirm Order") + f"\nService: {stylize_word(svc.get('name'))}\nLink: {link}\nQuantity: {qty}\nPoints: {points}", reply_markup=kb)
        except Exception:
            traceback.print_exc()
    return

def confirm_temp_order(c, tempid):
    uid = c.from_user.id
    tmp = temp_col.find_one({"_id": tempid})
    if not tmp or tmp.get("user_id") != uid:
        bot.answer_callback_query(c.id, S("Order expired/invalid"))
        return
    sid = tmp.get("svc_id")
    from bson import ObjectId
    svc = services_col.find_one({"_id": ObjectId(sid)})
    if not svc:
        bot.answer_callback_query(c.id, S("Service not found"))
        return
    points = tmp.get("points_cost",0)
    # deduct atomically
    with balance_lock:
        udoc = users_col.find_one({"tg_id": uid}) or {"balance_points":0}
        if udoc.get("balance_points",0) < points:
            bot.answer_callback_query(c.id, S("Insufficient balance at confirm time"))
            return
        users_col.update_one({"tg_id": uid}, {"$inc": {"balance_points": -points}})
    # call provider API
    api_key = svc.get("api_key")
    api_url = svc.get("api_url")
    provider_service_id = svc.get("service_id")
    link = tmp.get("link")
    qty = tmp.get("quantity")
    try:
        resp = requests.get(f"{api_url}?key={api_key}&action=add&service={provider_service_id}&link={requests.utils.requote_uri(link)}&quantity={qty}", timeout=30).json()
    except Exception as e:
        # rollback
        users_col.update_one({"tg_id": uid}, {"$inc": {"balance_points": points}})
        bot.answer_callback_query(c.id, S("API request failed. Your balance refunded."))
        bot.send_message(uid, S("❌ API error. Try later."))
        return
    api_order_id = resp.get("order") or resp.get("order_id") or None
    order_doc = {
        "tg_id": uid,
        "service_name": svc.get("name"),
        "provider_service_id": provider_service_id,
        "api_order_id": api_order_id,
        "api_raw": resp,
        "link": link,
        "quantity": qty,
        "points_charged": points,
        "status": "in_progress" if api_order_id else "placed",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    orders_col.insert_one(order_doc)
    temp_col.delete_one({"_id": tempid})
    bot.answer_callback_query(c.id, S("✅ Order placed"))
    bot.send_message(uid, S("✅ Order placed!") + f"\nOrder API ID: {api_order_id}\nPoints deducted: {points}")
    send_admin_log(S(f"🆕 New Order • User: {uid} • Service: {svc.get('name')} • Qty: {qty} • Points: {points}"))

# === History (paginated) ===
PAGE_SIZE = 5

def handle_history_start(c):
    return show_history_page(c, 0)

def show_history_page(c, page):
    uid = c.from_user.id
    skip = page * PAGE_SIZE
    total = orders_col.count_documents({"tg_id": uid})
    docs = list(orders_col.find({"tg_id": uid}).sort("created_at", -1).skip(skip).limit(PAGE_SIZE))
    if not docs:
        bot.answer_callback_query(c.id, S("No history found"))
        return
    text = S(f"📜 Order History — Page {page+1}\n\n")
    for d in docs:
        status = d.get("status","-")
        api_id = d.get("api_order_id","-")
        created = d.get("created_at")
        created_str = created.strftime("%Y-%m-%d %H:%M") if created else "-"
        text += f"🆔 <code>{str(d.get('_id'))[:8]}</code> • <b>{stylize_word(d.get('service_name'))}</b>\nQty: {d.get('quantity')} • Points: {d.get('points_charged')}\nStatus: {status}\nAPI ID: {api_id}\nCreated: {created_str}\n\n"
    kb = InlineKeyboardMarkup()
    if skip > 0:
        kb.add(InlineKeyboardButton(S("⬅️ Prev"), callback_data=f"history:page:{page-1}"))
    if (skip + PAGE_SIZE) < total:
        kb.add(InlineKeyboardButton(S("Next ➡️"), callback_data=f"history:page:{page+1}"))
    kb.add(InlineKeyboardButton(S("◀️ Back"), callback_data="back_start"))
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, text, reply_markup=kb)
    # === Refer ===
def handle_refer(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    bot.send_message(uid, S("🎁 Refer & Earn") + f"\nShare your link:\nhttps://t.me/{bot.get_me().username}?start={uid}")

# === Auto-refund background job ===
def check_provider_status(order):
    # try provider status endpoint pattern
    try:
        svc = services_col.find_one({"service_id": order.get("provider_service_id")})
        if not svc:
            return None
        api_key = svc.get("api_key"); api_url = svc.get("api_url"); api_ord = order.get("api_order_id")
        if not (api_key and api_url and api_ord):
            return None
        resp = requests.get(f"{api_url}?key={api_key}&action=status&order={api_ord}", timeout=20).json()
        status = resp.get("status") or (resp.get("data") or {}).get("status")
        return {"status": status, "raw": resp}
    except Exception as e:
        return None

def auto_refund_job():
    print("[scheduler] running auto refund:", datetime.utcnow())
    pending = list(orders_col.find({"status":{"$in":["in_progress","placed","processing"]}}))
    for ord in pending:
        try:
            res = check_provider_status(ord)
            if not res:
                continue
            st = (res.get("status") or "").lower()
            if st in ["cancelled","canceled","failed","refunded","declined"]:
                if ord.get("status") == "refunded":
                    continue
                points = ord.get("points_charged",0)
                if points > 0:
                    users_col.update_one({"tg_id": ord.get("tg_id")}, {"$inc": {"balance_points": points}})
                orders_col.update_one({"_id": ord.get("_id")}, {"$set":{"status":"refunded","provider_raw":res.get("raw"),"updated_at":datetime.utcnow()}})
                try:
                    bot.send_message(ord.get("tg_id"), S("🔁 Your order was cancelled/refunded. Points returned."))
                except:
                    pass
                send_admin_log(S(f"🔁 Auto-refund executed • Order: {str(ord.get('_id'))[:8]} • User: {ord.get('tg_id')} • Points: {points}"))
            elif st in ["completed","delivered","success"]:
                if ord.get("status") != "completed":
                    orders_col.update_one({"_id": ord.get("_id")}, {"$set":{"status":"completed","provider_raw":res.get("raw"),"updated_at":datetime.utcnow()}})
        except Exception:
            traceback.print_exc()

scheduler = BackgroundScheduler()
scheduler.add_job(auto_refund_job, 'interval', seconds=AUTO_REFUND_INTERVAL, id='auto_refund', replace_existing=True)
scheduler.start()

# === Admin login & menu (/adminox) ===
ADMIN_SESSION_TTL = 60*30  # 30 minutes session

@bot.message_handler(commands=["adminox"])
def adminox_cmd(m):
    uid = m.from_user.id
    if not is_admin_id(uid):
        bot.reply_to(m, S("❌ You are not allowed to use this command."))
        return
    # ask for password via ForceReply
    msg = bot.send_message(uid, S("🔐 Admin login — Enter password:"), reply_markup=ForceReply(selective=True))
    @bot.message_handler(func=lambda mm: mm.reply_to_message and mm.reply_to_message.message_id==msg.message_id and mm.from_user.id==uid)
    def receive_admin_password(mm):
        pwd = mm.text.strip()
        if pwd == ADMIN_PASSWORD:
            # create session
            expires = datetime.utcnow() + timedelta(seconds=ADMIN_SESSION_TTL)
            admin_sessions.update_one({"tg_id": uid}, {"$set": {"tg_id": uid, "expires_at": expires}}, upsert=True)
            bot.send_message(uid, S("✅ Login successful. Opening admin menu..."))
            send_admin_menu(uid)
        else:
            bot.send_message(uid, S("❌ Wrong password. Access denied."))

def is_admin_logged_in(uid):
    s = admin_sessions.find_one({"tg_id": uid})
    if not s:
        return False
    if s.get("expires_at") and s.get("expires_at") < datetime.utcnow():
        admin_sessions.delete_one({"tg_id": uid})
        return False
    return True

def send_admin_menu(uid):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(S("➕ Add Service"), callback_data="admin:add_service"))
    kb.add(InlineKeyboardButton(S("📝 Edit Service"), callback_data="admin:edit_service"))
    kb.add(InlineKeyboardButton(S("🗑️ Delete Service"), callback_data="admin:delete_service"))
    kb.add(InlineKeyboardButton(S("💰 Add Balance"), callback_data="admin:add_balance"))
    kb.add(InlineKeyboardButton(S("📢 Broadcast"), callback_data="admin:broadcast"))
    kb.add(InlineKeyboardButton(S("⚙️ Toggle Maintenance"), callback_data="admin:toggle_maint"))
    bot.send_message(uid, S("🔐 Admin Menu"), reply_markup=kb)

def admin_callback_router(c):
    uid = c.from_user.id
    if not is_admin_id(uid):
        bot.answer_callback_query(c.id, S("❌ Not authorized"))
        return
    if not is_admin_logged_in(uid):
        bot.answer_callback_query(c.id, S("❌ Admin session expired. Use /adminox"))
        return
    data = c.data
    bot.answer_callback_query(c.id)
    if data == "admin:add_service":
        bot.send_message(uid, S("➕ Send service in format (pipe separated):\ncategory|name|service_id|api_key|api_url|min|max|image_url|description"))
        @bot.message_handler(func=lambda m: m.from_user.id==uid)
        def admin_add(m):
            try:
                parts = m.text.strip().split("|")
                if len(parts) < 9:
                    bot.send_message(uid, S("❌ Invalid format"))
                    return
                category,name,service_id,api_key,api_url,min_q,max_q,image_url,description = parts[:9]
                doc = {"category": category.strip().lower(), "name": name.strip(), "service_id": service_id.strip(), "api_key": api_key.strip(), "api_url": api_url.strip(), "min_qty": int(min_q), "max_qty": int(max_q), "image_url": image_url.strip(), "description": description.strip(), "active": True}
                services_col.insert_one(doc)
                bot.send_message(uid, S("✅ Service added"))
            except Exception as e:
                bot.send_message(uid, S("❌ Error adding service"))
    elif data == "admin:edit_service":
        bot.send_message(uid, S("📝 Send service _id on first line, then field|value lines. Example:\n<id>\nname|New Name\nmin_qty|100"))
        @bot.message_handler(func=lambda m: m.from_user.id==uid)
        def admin_edit(m):
            try:
                lines = m.text.strip().splitlines()
                _id = lines[0].strip()
                updates = {}
                for ln in lines[1:]:
                    if "|" in ln:
                        k,v = ln.split("|",1)
                        kv = v.strip()
                        if kv.lower() in ("true","false"):
                            kv = kv.lower()=="true"
                        else:
                            try:
                                if "." in kv:
                                    kv = float(kv)
                                else:
                                    kv = int(kv)
                            except:
                                pass
                        updates[k.strip()] = kv
                from bson import ObjectId
                services_col.update_one({"_id": ObjectId(_id)}, {"$set": updates})
                bot.send_message(uid, S("✅ Service updated"))
            except Exception as e:
                bot.send_message(uid, S("❌ Error updating service"))
    elif data == "admin:delete_service":
        bot.send_message(uid, S("🗑️ Send service _id to soft-delete (active=false)"))
        @bot.message_handler(func=lambda m: m.from_user.id==uid)
        def admin_delete(m):
            try:
                _id = m.text.strip()
                from bson import ObjectId
                services_col.update_one({"_id": ObjectId(_id)}, {"$set":{"active":False}})
                bot.send_message(uid, S("✅ Service deactivated"))
            except:
                bot.send_message(uid, S("❌ Error"))
    elif data == "admin:add_balance":
        bot.send_message(uid, S("💰 Send in format: tg_id|amount_in_points (example: 6052975324|1000)"))
        @bot.message_handler(func=lambda m: m.from_user.id==uid)
        def admin_add_bal(m):
            try:
                tg,amt = m.text.strip().split("|")
                users_col.update_one({"tg_id": int(tg)}, {"$inc":{"balance_points": int(amt)}}, upsert=True)
                bot.send_message(uid, S("✅ Balance added"))
            except:
                bot.send_message(uid, S("❌ Error"))
    elif data == "admin:broadcast":
        bot.send_message(uid, S("📢 Send broadcast message (text). It will be sent to all users."))
        @bot.message_handler(func=lambda m: m.from_user.id==uid)
        def admin_broadcast(m):
            try:
                msg = m.text
                sent = 0
                for u in users_col.find({}):
                    try:
                        bot.send_message(u["tg_id"], S("📣 Broadcast") + "\n\n" + msg)
                        sent += 1
                    except:
                        pass
                bot.send_message(uid, S(f"✅ Broadcast sent to {sent} users."))
            except:
                bot.send_message(uid, S("❌ Broadcast failed"))
    elif data == "admin:toggle_maint":
        cfg = get_config()
        new = not cfg.get("maintenance", False)
        config_col.update_one({}, {"$set":{"maintenance": new}}, upsert=True)
        bot.send_message(uid, S(f"⚙️ Maintenance set to {new}"))
    else:
        bot.send_message(uid, S("❌ Unknown admin action"))

# === Graceful shutdown ===
import atexit
def shutdown():
    try:
        scheduler.shutdown(wait=False)
    except:
        pass
    try:
        bot.stop_polling()
    except:
        pass

atexit.register(shutdown)

# === Run polling ===
if __name__ == "__main__":
    print("Bot starting...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except KeyboardInterrupt:
        print("Stopping.")
    except Exception as e:
        print("Crash:", e)
