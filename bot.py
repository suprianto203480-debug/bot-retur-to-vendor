import os
import psycopg2

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# ================= DATABASE =================

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def cari_produk_database(keyword):

    try:
        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT upc, item_desc, unit_retail, soh
        FROM produk_master
        WHERE
            upc ILIKE %s
            OR item_desc ILIKE %s
        LIMIT 10
        """

        param = (f"%{keyword}%", f"%{keyword}%")

        cur.execute(query, param)

        data = cur.fetchall()

        cur.close()
        conn.close()

        return data

    except Exception as e:

        print("ERROR DATABASE:", e)
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

    text = (
        "🤖 *Bot Retur Vendor Aktif*\n\n"
        "Menu:\n"
        "/scan - Scan Barcode\n"
        "/cari - Cari Produk\n\n"
        "Atau kirim UPC / nama produk langsung."
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=tombol_scan()
    )


# ================= SCAN =================

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📷 Klik tombol untuk scan barcode:",
        reply_markup=tombol_scan()
    )


# ================= CARI =================

async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🔎 Kirim UPC atau nama produk yang ingin dicari."
    )


# ================= TERIMA DATA SCANNER =================

async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.effective_message

    if not message.web_app_data:
        return

    barcode = message.web_app_data.data.strip()

    print("BARCODE MASUK:", barcode)

    hasil = cari_produk_database(barcode)

    await kirim_hasil(update, hasil)


# ================= TERIMA TEXT =================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyword = update.message.text.strip()

    hasil = cari_produk_database(keyword)

    await kirim_hasil(update, hasil)


# ================= FORMAT HASIL =================

async def kirim_hasil(update, hasil):

    if not hasil:

        await update.message.reply_text(
            "❌ Produk tidak ditemukan."
        )

        return

    pesan = "📦 *Hasil Pencarian*\n\n"

    for upc, nama, harga, stok in hasil:

        try:
            harga_format = f"Rp {harga:,.0f}"
        except:
            harga_format = str(harga)

        pesan += (
            f"*{nama}*\n"
            f"UPC : `{upc}`\n"
            f"Harga : {harga_format}\n"
            f"Stok : {stok}\n\n"
        )

    await update.message.reply_text(
        pesan,
        parse_mode="Markdown",
        reply_markup=tombol_scan()
    )


# ================= MAIN =================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("cari", cari))

    app.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_handler)
    )

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    print("✅ BOT RETUR VENDOR AKTIF")

    app.run_polling()


if __name__ == "__main__":
    main()
