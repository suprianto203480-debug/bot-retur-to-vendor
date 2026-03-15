import os
import psycopg2

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")


# ================= DATABASE =================

def get_connection():
    return psycopg2.connect(DATABASE_URL)


def cari_produk(upc):

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT item_desc, unit_retail, soh
        FROM produk_master
        WHERE TRIM(upc) = %s
        LIMIT 1
        """, (upc,))

        data = cur.fetchone()

        cur.close()
        conn.close()

        return data

    except Exception as e:
        print("ERROR DATABASE:", e)
        return None


# ================= TOMBOL SCAN =================

def tombol_scan():

    keyboard = [[
        InlineKeyboardButton(
            "📷 Scan Barcode",
            web_app=WebAppInfo(
                url="https://suprianto203480-debug.github.io/bot-retur-to-vendor/scanner.html"
            )
        )
    ]]

    return InlineKeyboardMarkup(keyboard)


# ================= FORMAT HASIL =================

def format_produk(barcode, produk):

    if produk:
        nama, harga, stok = produk

        return (
            f"📦 *Produk Ditemukan*\n\n"
            f"Nama  : {nama}\n"
            f"Harga : Rp {harga:,.0f}\n"
            f"Stok  : {stok}\n"
            f"UPC   : `{barcode}`"
        )

    else:
        return (
            f"❌ *Produk tidak ditemukan*\n\n"
            f"UPC : `{barcode}`"
        )


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Bot Retur Vendor Aktif\n\nKlik tombol untuk scan barcode:",
        reply_markup=tombol_scan()
    )


# ================= HANDLER WEBAPP =================

async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.effective_message

    if message.web_app_data is None:
        return

    barcode = message.web_app_data.data.strip()

    print("SCAN WEBAPP:", barcode)

    produk = cari_produk(barcode)

    pesan = format_produk(barcode, produk)

    await message.reply_text(
        pesan,
        parse_mode="Markdown",
        reply_markup=tombol_scan()
    )


# ================= HANDLER TEXT (CADANGAN) =================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    barcode = update.message.text.strip()

    if not barcode.isdigit():
        return

    print("SCAN TEXT:", barcode)

    produk = cari_produk(barcode)

    pesan = format_produk(barcode, produk)

    await update.message.reply_text(
        pesan,
        parse_mode="Markdown",
        reply_markup=tombol_scan()
    )


# ================= MAIN =================

def main():

    print("BOT RETUR VENDOR AKTIF")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # scanner webapp
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.WEB_APP_DATA,
            webapp_handler
        )
    )

    # input manual barcode
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
