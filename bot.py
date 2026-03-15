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

        query = """
        SELECT item_desc, unit_retail, soh
        FROM produk_master
        WHERE TRIM(upc) = %s
        LIMIT 1
        """

        cur.execute(query, (upc,))
        data = cur.fetchone()

        cur.close()
        conn.close()

        return data

    except Exception as e:

        print("ERROR DATABASE :", e)
        return None


# ================= TOMBOL SCAN =================

def tombol_scan():

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

    return InlineKeyboardMarkup(keyboard)


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Bot Retur Vendor Aktif\n\nKlik tombol untuk scan barcode:",
        reply_markup=tombol_scan()
    )


# ================= TERIMA DATA SCANNER =================

async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.effective_message

    if message.web_app_data is None:
        print("Tidak ada data WebApp")
        return

    barcode = message.web_app_data.data.strip()

    print("BARCODE MASUK :", barcode)

    produk = cari_produk(barcode)

    if produk:

        nama, harga, stok = produk

        pesan = (
            f"📦 *Produk Ditemukan*\n\n"
            f"Nama  : {nama}\n"
            f"Harga : Rp {harga:,.0f}\n"
            f"Stok  : {stok}\n"
            f"UPC   : `{barcode}`"
        )

    else:

        pesan = (
            f"❌ *Produk tidak ditemukan*\n\n"
            f"UPC : `{barcode}`"
        )

    await message.reply_text(
        pesan,
        parse_mode="Markdown",
        reply_markup=tombol_scan()
    )


# ================= MAIN =================

def main():

    print("✅ BOT SCANNER AKTIF")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # handler khusus data dari scanner
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.WEB_APP_DATA,
            webapp_handler
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
