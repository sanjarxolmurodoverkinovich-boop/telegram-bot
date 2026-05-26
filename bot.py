"""
Groq AI Telegram Bot
"""

import logging
from groq import Groq
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ===================== SOZLAMALAR =====================
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = """Sen professional va do'stona AI yordamchisan.
Foydalanuvchilarga o'zbek tilida, aniq va tushunarli javob ber.
Kerak bo'lsa rus yoki ingliz tilida ham javob bera olasan."""
# ======================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)

user_histories: dict[int, list[dict]] = {}


def get_history(user_id: int) -> list[dict]:
    return user_histories.get(user_id, [])


def add_to_history(user_id: int, role: str, content: str):
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": role, "content": content})
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]


def clear_history(user_id: int):
    user_histories[user_id] = []


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    clear_history(user.id)
    welcome = (
        f"Salom, {user.first_name}! 👋\n\n"
        "Men Groq AI asosidagi professional yordamchiman.\n"
        "Menga istalgan savolingizni bering!\n\n"
        "📌 Buyruqlar:\n"
        "/start - Suhbatni qayta boshlash\n"
        "/clear - Tarixni tozalash\n"
        "/help - Yordam"
    )
    await update.message.reply_text(welcome)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_history(update.effective_user.id)
    await update.message.reply_text("✅ Suhbat tarixi tozalandi!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Groq AI Bot - Yordam*\n\n"
        "Menga istalgan savolingizni yozing!\n\n"
        "*Buyruqlar:*\n"
        "/start - Suhbatni qayta boshlash\n"
        "/clear - Suhbat tarixini tozalash\n"
        "/help - Ushbu yordam xabari\n\n"
        "*Imkoniyatlar:*\n"
        "✅ O'zbek, Rus, Ingliz tillarida muloqot\n"
        "✅ Suhbat tarixini eslab qoladi\n"
        "✅ Har qanday savollarga javob beradi"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    add_to_history(user_id, "user", user_message)

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(user_id)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024,
        )

        reply = response.choices[0].message.content
        add_to_history(user_id, "assistant", reply)

        if len(reply) > 4096:
            for i in range(0, len(reply), 4096):
                await update.message.reply_text(reply[i:i+4096])
        else:
            await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Xato: {e}")
        await update.message.reply_text(
            f"❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.\nXato: {str(e)}"
        )


def main():
    print("🤖 Groq AI Telegram Bot ishga tushmoqda...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot muvaffaqiyatli ishga tushdi!")
    print("Toxtatish uchun: Ctrl+C")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
