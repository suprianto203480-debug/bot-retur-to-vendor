import os
import psycopg2
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# ================= DATABASE =================

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def cari_produk(upc):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT item_desc, unit_retail, soh
        FROM produk_master
        WHERE upc = %s
        LIMIT 1
    """, (upc,))

    data = cur.fetchone()

    cur.close()
    conn.close()

    return data


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [[
        InlineKeyboardButton(
            "📷 Scan Barcode",
            web_app=WebAppInfo(
                url="https://suprianto203480-debug.github.io/bot-retur-to-vendor/scanner.html"
            )
        )
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Bot Retur Vendor Aktif\n\nKlik tombol untuk scan barcode:",
        reply_markup=reply_markup
    )


# ================= TERIMA DATA SCANNER =================

async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.effective_message.web_app_data:
        return

    data = json.loads(update.effective_message.web_app_data.data)

    barcode = data["barcode"]

    produk = cari_produk(barcode)

    if produk:

        nama, harga, stok = produk

        pesan = (
            f"📦 Produk : {nama}\n"
            f"💰 Harga  : Rp {harga}\n"
            f"📊 Stok   : {stok}\n"
            f"🔎 UPC    : {barcode}"
        )

    else:

        pesan = f"❌ Produk tidak ditemukan\nUPC: {barcode}"

    await update.message.reply_text(pesan)


# ================= MAIN =================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.WEB_APP_DATA,
            webapp_handler
        )
    )

    print("✅ BOT SCANNER AKTIF")

    app.run_polling()


if __name__ == "__main__":
    main()
