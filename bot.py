import os
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# ================= DATABASE =================

def get_connection():
    return psycopg2.connect(DATABASE_URL)


def cari_produk_by_upc(upc):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT sku, item_desc, unit_retail, soh, upc
            FROM produk_master
            WHERE upc::text = %s
            LIMIT 1
        """, (upc,))

        data = cur.fetchone()

        cur.close()
        conn.close()

        return data

    except Exception as e:
        print("ERROR DATABASE UPC:", e)
        return None


def cari_produk_by_keyword(keyword):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT sku, item_desc, unit_retail, soh, upc
            FROM produk_master
            WHERE
                upc::text = %s
                OR sku::text = %s
                OR item_desc ILIKE %s
                OR sku::text ILIKE %s
                OR upc::text ILIKE %s
            LIMIT 10
        """, (
            keyword,
            keyword,
            f"%{keyword}%",
            f"%{keyword}%",
            f"%{keyword}%"
        ))

        results = cur.fetchall()

        cur.close()
        conn.close()

        if len(results) == 1:
            return results[0]

        if len(results) > 1:
            return results

        return None

    except Exception as e:
        print("ERROR DATABASE SEARCH:", e)
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


# ================= COMMAND =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    teks = (
        "🤖 *BOT SCANNER PRODUK*\n\n"
        "Gunakan:\n"
        "/scan → Scan barcode\n"
        "/cari <nama / sku / upc>\n"
        "/help → bantuan"
    )

    await update.message.reply_text(
        teks,
        parse_mode="Markdown",
        reply_markup=tombol_scan()
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📷 Silakan scan barcode produk",
        reply_markup=tombol_scan()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    teks = (
        "*Menu Bot*\n\n"
        "/scan → Scan barcode\n"
        "/cari <keyword> → cari produk\n"
        "/help → bantuan\n\n"
        "Contoh:\n"
        "`/cari 8994448860567`\n"
        "`/cari sarung`\n"
        "`/cari 91774219`"
    )

    await update.message.reply_text(
        teks,
        parse_mode="Markdown",
        reply_markup=tombol_scan()
    )


# ================= FITUR CARI =================

async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "Gunakan:\n/cari <UPC / SKU / Nama Produk>",
            reply_markup=tombol_scan()
        )
        return

    keyword = " ".join(context.args)

    hasil = cari_produk_by_keyword(keyword)

    if hasil is None:

        pesan = f"❌ Produk tidak ditemukan\n\nKeyword : {keyword}"

    elif isinstance(hasil, tuple):

        sku, nama, harga, stok, upc = hasil

        pesan = (
            f"📦 *Produk Ditemukan*\n\n"
            f"SKU   : {sku}\n"
            f"Nama  : {nama}\n"
            f"Harga : Rp {harga:,.0f}\n"
            f"Stok  : {stok}\n"
            f"UPC   : `{upc}`"
        )

    else:

        pesan = "🔎 *Beberapa produk ditemukan:*\n\n"

        for i, row in enumerate(hasil, start=1):

            sku, nama, harga, stok, upc = row

            pesan += (
                f"{i}. {nama}\n"
                f"   SKU : {sku}\n"
                f"   UPC : `{upc}`\n"
                f"   Stok: {stok}\n\n"
            )

        if len(hasil) >= 10:
            pesan += "_Menampilkan maksimal 10 produk_"

    await update.message.reply_text(
        pesan,
        parse_mode="Markdown",
        reply_markup=tombol_scan()
    )


# ================= WEBAPP BARCODE =================

async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.effective_message

    if not message.web_app_data:
        return

    barcode = message.web_app_data.data.strip()

    print("BARCODE:", barcode)

    produk = cari_produk_by_upc(barcode)

    if produk:

        sku, nama, harga, stok, upc = produk

        pesan = (
            f"📦 *Produk Ditemukan*\n\n"
            f"SKU   : {sku}\n"
            f"Nama  : {nama}\n"
            f"Harga : Rp {harga:,.0f}\n"
            f"Stok  : {stok}\n"
            f"UPC   : `{upc}`"
        )

    else:

        pesan = f"❌ Produk tidak ditemukan\n\nUPC : `{barcode}`"

    await message.reply_text(
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
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.WEB_APP_DATA,
            webapp_handler
        )
    )

    print("✅ BOT SCANNER PRODUK AKTIF")

    app.run_polling()


if __name__ == "__main__":
    main()
