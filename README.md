# QURESHIxOTP — Premium OTP Panel Bot

Ek premium, single-owner Telegram OTP panel bot. Ye file `shownXpannel.py` ko
server par host karne ke liye sab kuch ready hai.

---

## 1. Owner (sirf ek hi owner)

| Field | Value |
|---|---|
| **Bot** | `@QxP_Pannel_bot` |
| **Owner ID** | `8984851474` |
| Owner username | `@WhoIsShown` |
| Admin count | **1 (sirf owner)** |

- `OWNER_IDS == ADMIN_IDS == {8984851474}` — code me hard-locked hai.
- Koi "first user admin" nahi banta.
- Username se kisi ko admin nahi banaya jata (sirf ID `8984851474`).
- `load_data()` ke baad bhi owner force re-set hota hai.

## 2. Access gates (default OFF — koi error nahi)

| Gate | Value |
|---|---|
| `GRANT_ACCESS_REQUIRED` | **ON (locked)** |
| `REFERRAL_ENABLED` | **ON** |
| `REQUIRED_REFERRALS` | **2** |
| `FORCE_JOIN_ENABLED` | OFF |

**Unlock ke 2 raste:**
1. User **2 valid referrals** complete kare (referral link se aaye users join karein), YA
2. User **Request Owner Access** dabaye → owner ko Grant/Reject buttons aate hain → Grant par turant access.

Owner khud `/grant <user_id>` se bhi access de sakta hai.

## 3. Tap-to-Copy (premium clipboard)

Telegram ke native `copy_text` button use hote hain (PTB 22.5):

- Device terminal me: **Copy OTP** + **Copy Number**
- Device terminal ke quick buttons: **🔄 Refresh OTP**, **⚡ Last 5 OTPs**, **📋 Recent OTPs**, **📨 View Last 10 SMS**, **📱 Device Info**, **✉️ Send SMS**, **📞 Call Forward**, **‹ Back**, **📡 All Panels**
- Last 10 SMS view me: har OTP ka **Copy OTP** button
- Last 5 OTPs view me: har OTP ka **Copy OTP** + **Copy All**
- Recent OTPs view me: per-number latest OTP ka **Copy** button
- **Copy All OTPs** (ek click me saare OTP)
- Auto-forward OTP message me: **Copy OTP** + **Copy Number**
- `/id` aur **My ID** card me: **Copy My ID**

## 4. Commands

| Command | Kya karta hai |
|---|---|
| `/start` | Main menu |
| `/help` | Command list |
| `/id` / `/myid` | Aapki ID + copy button |
| `/ping` | Latency / uptime / panels / users |
| `/menu` | Reply keyboard dobara kholna |
| `/panel` / `/admin` | Admin panel (owner only) |
| `/status` | Bot status (admin) |
| `/grant` `/revoke` | Access dena/lena (admin) |
| `/setadminpanel` `/unsetadminpanel` `/adminpanels` | Panel visibility (admin) |
| `/autodb` | Auto-DB sender settings (admin) |
| `/cancel` | Pending input cancel |

## 5. Server par host karna

### Option A — systemd (recommended, VPS)

```bash
sudo mkdir -p /opt/qureshixotp
sudo cp shownXpannel.py requirements.txt start.sh qureshixotp-bot.service /opt/qureshixotp/
cd /opt/qureshixotp
sudo python3 -m pip install -r requirements.txt

sudo cp qureshixotp-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now qureshixotp-bot
sudo systemctl status qureshixotp-bot
journalctl -u qureshixotp-bot -f
```

### Option B — simple / one command

```bash
chmod +x start.sh
./start.sh
```

### Option C — Railway / Render / Heroku

- `Procfile` already included: `worker: python shownXpannel.py`
- Build command: `pip install -r requirements.txt`
- Start command: `python shownXpannel.py`

### Webhook mode (optional)

```bash
export WEBHOOK_URL="https://your-domain.com"
export PORT=8443
python3 shownXpannel.py
```

Webhook `https://your-domain.com/webhook` par set ho jayega.

## 6. ⚠️ IMPORTANT — sirf EK instance chalao

Agar bot token (`9102355745`) kisi aur jagah bhi chal raha hai to log me
aayega:

```
⛔ CONFLICT: Bot ka koi AUR instance bhi chal raha hai!
```

**Fix:** purana instance band karo, phir naya chalao. Ek token = ek process.

```bash
# purane process dhoondo aur band karo
ps aux | grep shownXpannel
pkill -f shownXpannel.py
```

## 7. Env variables (optional branding)

| Variable | Default |
|---|---|
| `BOT_TOKEN` | built-in token |
| `BOT_USERNAME` | `@QxP_Pannel_bot` |
| `BOT_BRAND_NAME` | `QURESHIxOTP` |
| `OWNER_DISPLAY_NAME` | `Shown` |
| `OWNER_CONTACT` | `@WhoIsShown` |
| `WEBHOOK_URL` | *(empty → polling)* |
| `PORT` | `8080` |

## 8. Data / persistence

- `bot_database.json` — users, access, settings (auto-save + `.bak` rolling backup).
- 144 Firebase panels built-in, polling engine (`POLL_INTERVAL=15s`).

## 9. Fixes (v2.1)

| Problem | Fix |
|---|---|
| `field "copy_text" must be of type object` | `premium_button()` ab `CopyTextButton(text)` object banata hai, plain string nahi |
| `Message is too long` (Panel Status) | 3800-char safe truncation + "… aur N lines chhupayi gayi" + All Panels hint |
| `Reply markup is too long` (All Panels) | 18-per-page pagination (Prev / Next / page counter) |
| `Reply markup is too long` (Set Admin Panel) | Wahi pagination (`setadmin:<page>`) |
| Number button dabane par kuch nahi hota | `_ts_num()` — Firebase string timestamp par `-d.timestamp` TypeError crash fix |
| Refresh / Recent OTPs / Last 5 OTPs gayab | `device_action_keyboard()` me poore buttons + naye `msgs5:` / `rec:` handlers |
| Chup-chaap fail hone wale buttons | `on_callback` bulletproof wrapper + global `on_error` handler |
| `Auto DB error: BadRequest: Chat not found` | `resolve_send_chat()` health-check + backup channel fallback + owner alert + **📍 Set This Chat** / **🧪 Test Group** buttons |

### Auto DB Sender — "Chat not found" kaise fix hua

`Chat not found` ka matlab: bot us group/channel me **member nahi hai** (ya group delete/kick ho gaya).

Ab bot:
1. Bhejne se pehle `get_chat()` se **validate** karta hai
2. Fail ho to **backup channel** par automatic fallback
3. Dono fail ho to owner ko **ek hi baar** saaf message (log spam nahi)
4. Auto DB panel me live health dikhta hai: `Last Good`, `Fail Count`, `Last Error`
5. **📍 Set This Chat** — jis chat me button dabaya wahi target ban jata hai (sabse aasan fix)
6. **🧪 Test Group** — dono chats reachable hain ya nahi, turant batata hai

## 10. Files

```
shownXpannel.py            # main bot (single file)
requirements.txt           # deps (python-telegram-bot[webhooks]==22.5)
start.sh                   # one-command starter
Procfile                   # Railway/Render/Heroku
qureshixotp-bot.service    # systemd unit
README.md                  # ye file
```

## 11. 🆔 Chat ID Finder (built-in — koi alag file nahi)

Pehle `chatid.py` alag file thi. Ab **poora Chat ID Finder `shownXpannel.py` ke andar** hai.
Kuch bhi install karne ki zaroorat nahi — sirf ek `.py` + ek `requirements.txt`.

**Kahan milega:** Admin Panel → **Auto DB Sender** → **🆔 Chat ID Finder**

**4 tareeke se chat ID nikal sakte hain:**

| Tareeka | Kaise |
|---|---|
| 1️⃣ **Forward** *(best)* | Private channel/group ka koi bhi message bot ko forward karo → ID + title + type + bot status turant |
| 2️⃣ **Numeric ID** | `-1001234567890` bhejo |
| 3️⃣ **Username** | `@mychannel` bhejo |
| 4️⃣ **Link** | `https://t.me/mychannel` bhejo |

**Bonus — Auto-Forward:** Admin jab bhi koi message forward karta hai (bina button dabaye),
bot khud Chat ID card bhej deta hai. Private channel ka ID nikalne ka sabse tez tareeka.

Card me dikhta hai: `Chat ID`, `Title`, `Type`, `Username`, `Bot Status`, `Posting permission` —
aur do one-tap buttons: **✅ Set as Auto DB Group** / **🗄 Set as Backup Channel**.

### ⚠️ Private channel ka sach (Telegram ka rule)

Bot **khud** private channel join **nahi** kar sakta. Invite link (`t.me/+...`) sirf insaan use kar sakta hai.
Isliye ye steps zaroori hain:

1. Channel → **Administrators** → **Add Admin**
2. Bot ka username daalo: `@QxP_Pannel_bot`
3. **Post Messages** right **ON** karo
4. Channel ka koi message bot ko **forward** karo → ID mil jayega
5. **✅ Set as Auto DB Group** dabao

Bas. Uske baad Auto DB Sender us channel me har 30s me database bhejta rahega.

## 12. Verification (is build par chalaya gaya)

| Test | Result |
|---|---|
| `py_compile shownXpannel.py` | ✅ OK |
| Keyboard limits (14 keyboards, ≤100 buttons, callback ≤64B) | ✅ ALL PASS |
| Callback dispatch (41 callbacks, real handlers) | ✅ 41 OK / 0 FAIL |
| Chat ID Finder (11 tests, **real Telegram API**) | ✅ ALL PASS |
| Panel Status text length (144 panels) | ✅ 3659 / 4096 chars |
| Recent OTPs text length | ✅ 237 chars |
| Live run — 144 DBs fetched | ✅ 2.6s |
| Live run — Auto DB Sender | ✅ `Auto DB sent → -1003924957801` har 30s |
| Live run — error/traceback count | ✅ 0 |
