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
        print("ERROR DB:", e)
        return None


# ================= FORMAT HASIL =================

def format_produk(barcode, produk):

    if produk:

        nama, harga, stok = produk

        return (
            f"📦 Produk Ditemukan\n\n"
            f"Nama  : {nama}\n"
            f"Harga : Rp {harga:,.0f}\n"
            f"Stok  : {stok}\n"
            f"UPC   : {barcode}"
        )

    else:

        return (
            f"❌ Produk tidak ditemukan\n\n"
            f"UPC : {barcode}"
        )


# ================= TOMBOL =================

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


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Bot Retur Vendor Aktif\n\n"
        "Kirim UPC barcode atau gunakan tombol scan.",
        reply_markup=tombol_scan()
    )


# ================= CARI COMMAND =================

async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:

        await update.message.reply_text(
            "Gunakan:\n/cari 8995077600135"
        )
        return

    barcode = context.args[0]

    produk = cari_produk(barcode)

    pesan = format_produk(barcode, produk)

    await update.message.reply_text(pesan)


# ================= HANDLE TEXT =================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    if not text.isdigit():
        return

    produk = cari_produk(text)

    pesan = format_produk(text, produk)

    await update.message.reply_text(
        pesan,
        reply_markup=tombol_scan()
    )


# ================= MAIN =================

def main():

    print("BOT RETUR VENDOR AKTIF")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cari", cari))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
