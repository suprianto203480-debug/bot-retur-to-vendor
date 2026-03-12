import os
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def cari_produk(upc):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT item_desc, unit_retail, soh
        FROM produk_master
        WHERE upc = %s
        LIMIT 1
    """, (upc,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [[
        InlineKeyboardButton(
            "📷 Scan Barcode",
            web_app=WebAppInfo(
                url="https://suprianto203480-debug.github.io/bot-retur-to-vendor/scanner.html"
            )
        )
    ]]

    await update.message.reply_text(
        "Bot Retur Vendor Aktif\nKlik tombol scan:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def scan_result(update: Update, context: ContextTypes.DEFAULT_TYPE):

    upc = update.message.text

    produk = cari_produk(upc)

    if produk:
        nama, harga, stok = produk
        pesan = f"📦 {nama}\n💰 Harga: Rp {harga}\n📊 Stok: {stok}"
    else:
        pesan = "❌ Produk tidak ditemukan"

    await update.message.reply_text(pesan)

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, scan_result))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
