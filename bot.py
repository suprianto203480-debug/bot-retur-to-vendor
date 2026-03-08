import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📷 Scan Barcode",
                web_app=WebAppInfo(
                    url="https://suprianto203480-debug.github.io/bot-retur-to-vendor/scanner.html"
                )
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Bot Retur Vendor Aktif\n\nKlik tombol untuk scan barcode:",
        reply_markup=reply_markup
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
