import os
import random
import string
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= APNI DETAILS =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "7381283921:AAHkFmNcbk3w2yH8qVchG7w")
BOT_USERNAME = os.getenv("BOT_USERNAME", "AapkaBotUsername") # Bina @ ke
FIREBASE_DB_URL = "https://dora-dora-2e0e6-default-rtdb.asia-southeast1.firebasedatabase.app"

SHORTENER_API_KEY = os.getenv("SHORTENER_API_KEY", "APNA_SHORTENER_API_KEY")
SHORTENER_API_ENDPOINT = "https://gplinks.in/api"
# ================================================

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

    # Jab user shortener complete karke aayega
    if args and args[0].startswith("verify_"):
        session_id = args[0].replace("verify_", "")

        sess_check = requests.get(f"{FIREBASE_DB_URL}/pass_sessions/{session_id}.json").json()

        if not sess_check:
            await update.message.reply_text("❌ Invalid Session! App me jakar naya link lein.")
            return

        if sess_check.get("claimed") is True:
            await update.message.reply_text("⚠️ Ye session pehle hi use ho chuka hai.")
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
            f"📌 Ise Dora Dora app me video play karte waqt paste karein aur Unlock dabayein."
        )
        await update.message.reply_text(reply_text, parse_mode="Markdown")
        return

    # Normal /start request
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
        f"Videos unlock karne ke liye niche diye gaye button par tap karein.\n\n"
        f"👉 Shortener link par 10-15 seconds ke simple steps poore karein, aakhri page par **'Get Link'** dabate hi aapko yahan One-Time Token mil jayega."
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

if __name__ == '__main__':
    print("Bot live on Render...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.run_polling()
