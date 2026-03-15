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
    """Cari produk berdasarkan UPC (eksak)"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT sku, item_desc, unit_retail, soh, upc
            FROM produk_master
            WHERE upc = %s
            LIMIT 1
        """, (upc,))
        data = cur.fetchone()
        cur.close()
        conn.close()
        return data
    except Exception as e:
        print("ERROR DATABASE (UPC):", e)
        return None

def cari_produk_by_keyword(keyword):
    """
    Cari produk:
    1. Exact match di UPC
    2. Exact match di SKU
    3. Partial match (ILIKE) di item_desc (bisa juga di SKU/UPC jika perlu, tapi kita batasi di desc)
    Mengembalikan tuple jika exact, list of tuples jika banyak, None jika tidak ada.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1. Exact UPC
        cur.execute("""
            SELECT sku, item_desc, unit_retail, soh, upc
            FROM produk_master
            WHERE upc = %s
            LIMIT 1
        """, (keyword,))
        data = cur.fetchone()
        if data:
            return data  # tuple

        # 2. Exact SKU
        cur.execute("""
            SELECT sku, item_desc, unit_retail, soh, upc
            FROM produk_master
            WHERE sku = %s
            LIMIT 1
        """, (keyword,))
        data = cur.fetchone()
        if data:
            return data

        # 3. Partial di deskripsi (dan mungkin juga di SKU/UPC? Tapi biasanya deskripsi)
        # Kita cari di item_desc, bisa juga ditambahkan sku dan upc jika ingin
        cur.execute("""
            SELECT sku, item_desc, unit_retail, soh, upc
            FROM produk_master
            WHERE item_desc ILIKE %s
            LIMIT 10
        """, (f'%{keyword}%',))
        results = cur.fetchall()
        if results:
            return results  # list of tuples

        return None
    except Exception as e:
        print("ERROR DATABASE (keyword):", e)
        return None
    finally:
        cur.close()
        conn.close()

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

# ================= HANDLER PERINTAH =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot Retur Vendor Aktif\n\nKlik tombol untuk scan barcode:",
        reply_markup=tombol_scan()
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Scan Barcode",
        reply_markup=tombol_scan()
    )

async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Gunakan: /cari <UPC atau nama produk>",
            reply_markup=tombol_scan()
        )
        return

    keyword = ' '.join(args)
    hasil = cari_produk_by_keyword(keyword)

    if hasil is None:
        pesan = f"❌ Produk tidak ditemukan untuk: {keyword}"
    elif isinstance(hasil, tuple):
        # Satu hasil exact
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
        # Banyak hasil dari pencarian deskripsi
        pesan = "🔍 *Beberapa produk ditemukan:*\n"
        for idx, (sku, nama, harga, stok, upc) in enumerate(hasil, 1):
            pesan += f"{idx}. SKU: {sku} - {nama} (UPC: `{upc}`) Stok: {stok}\n"
        if len(hasil) >= 10:
            pesan += "\n*Tampilkan maksimal 10 hasil. Perjelas kata kunci.*"

    await update.message.reply_text(
        pesan,
        parse_mode="Markdown",
        reply_markup=tombol_scan()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = (
        "/start - Mulai bot dan tampilkan tombol scan\n"
        "/scan - Scan barcode produk\n"
        "/cari <UPC/SKU/deskripsi> - Cari produk berdasarkan SKU/DESC/UPC\n"
        "/help - Bantuan penggunaan bot"
    )
    await update.message.reply_text(teks, reply_markup=tombol_scan())

# ================= TERIMA DATA DARI WEB APP =================

async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message.web_app_data:
        return

    barcode = message.web_app_data.data.strip()
    print("BARCODE MASUK:", barcode)

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

    print("✅ BOT SCANNER AKTIF (dengan menu lengkap dan pencarian SKU)")
    app.run_polling()

if __name__ == "__main__":
    main()
