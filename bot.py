import os
import random
import string
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= AAPKI DETAILS (FULLY FILLED) =================
BOT_TOKEN = "8974372919:AAFS5_nvskKwhT31BkXY15j3V9H51ZJ32RUk"
BOT_USERNAME = "DoraDorakeybot"
FIREBASE_DB_URL = "https://dora-dora-2e0e6-default-rtdb.asia-southeast1.firebasedatabase.app"

# AroLinks Shortener API Configuration
SHORTENER_API_KEY = "5cb7c078128873314bab5f26dfd12c8546f25f10"
SHORTENER_API_ENDPOINT = "https://arolinks.com/api"
# ================================================================

def generate_random_token(prefix="DORA", length=6):
    chars = string.ascii_uppercase + string.digits
    rand_str = ''.join(random.choice(chars) for _ in range(length))
    return f"{prefix}-{rand_str}"

def get_short_link(target_url):
    try:
        req_url = f"{SHORTENER_API_ENDPOINT}?api={SHORTENER_API_KEY}&url={target_url}"
        res = requests.get(req_url, timeout=10).json()
        if res.get("status") == "success" or "shortenedUrl" in res:
            return res.get("shortenedUrl")
    except Exception as e:
        print("Shortener error:", e)
    return target_url

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    # Jab user shortener link complete karke redirect hokar aayega
    if args and args[0].startswith("verify_"):
        session_id = args[0].replace("verify_", "")

        # Session validity check in Firebase
        sess_check = requests.get(f"{FIREBASE_DB_URL}/pass_sessions/{session_id}.json").json()

        if not sess_check:
            await update.message.reply_text("❌ Invalid Session! App me jakar naya link generate karein.")
            return

        if sess_check.get("claimed") is True:
            await update.message.reply_text("⚠️️ Ye session pehle hi claim kiya ja chuka hai.")
            return

        token_code = generate_random_token()

        token_payload = {
            "status": "unused",
            "createdAt": {".sv": "timestamp"},
            "userId": user_id
        }
        requests.put(f"{FIREBASE_DB_URL}/access_tokens/{token_code}.json", json=token_payload)
        requests.patch(f"{FIREBASE_DB_URL}/pass_sessions/{session_id}.json", json={"claimed": True})

        reply_text = (
            f"🎉 **Verification Successful!**\n\n"
            f"Aapka Access Token:\n"
            f"`{token_code}`\n\n"
            f"📌 Is token code ko tap karke copy karein aur Dora Dora app me video play karte waqt paste karke Unlock dabayein."
        )
        await update.message.reply_text(reply_text, parse_mode="Markdown")
        return

    # Normal /start request (Session start)
    new_session = generate_random_token(prefix="SESS", length=8)

    requests.put(f"{FIREBASE_DB_URL}/pass_sessions/{new_session}.json", json={
        "userId": user_id,
        "claimed": False,
        "createdAt": {".sv": "timestamp"}
    })

    destination_target = f"https://t.me/{BOT_USERNAME}?start=verify_{new_session}"
    shortened_url = get_short_link(destination_target)

    keyboard = [
        [InlineKeyboardButton("🔗 Complete Step & Get Token", url=shortened_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 **Namaste {update.effective_user.first_name}!**\n\n"
        f"App me videos unlock karne ke liye niche diye gaye button par click karein.\n\n"
        f"👉 Shortener link par simple steps complete karein, aakhri page par **'Get Link'** dabate hi aapko yahan One-Time Token mil jayega."
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

if __name__ == '__main__':
    print("Bot live ho raha hai...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.run_polling()
