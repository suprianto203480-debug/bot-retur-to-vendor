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
    return psycopg2.connect(DATABASE_URL)


# ================= CARI UPC =================

def cari_upc(upc):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT sku,item_desc,unit_retail,soh
    FROM produk_master
    WHERE TRIM(upc)=%s
    LIMIT 1
    """,(upc,))

    data = cur.fetchone()

    cur.close()
    conn.close()

    return data


# ================= CARI SKU =================

def cari_sku(sku):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT item_desc,unit_retail,soh,upc
    FROM produk_master
    WHERE sku=%s
    LIMIT 1
    """,(sku,))

    data = cur.fetchone()

    cur.close()
    conn.close()

    return data


# ================= CARI NAMA =================

def cari_nama(keyword):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT sku,item_desc,unit_retail,soh,upc
    FROM produk_master
    WHERE item_desc ILIKE %s
    LIMIT 10
    """,(f"%{keyword}%",))

    data = cur.fetchall()

    cur.close()
    conn.close()

    return data


# ================= TOMBOL SCAN =================

def tombol_scan():

    keyboard=[[InlineKeyboardButton(
        "📷 Scan Barcode",
        web_app=WebAppInfo(
            url="https://USERNAME.github.io/scanner.html"
        )
    )]]

    return InlineKeyboardMarkup(keyboard)


# ================= START =================

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Bot Retur Vendor Aktif\n\n"
        "Kirim UPC barcode\n"
        "atau gunakan tombol scan",
        reply_markup=tombol_scan()
    )


# ================= CARI UPC =================

async def handle_barcode(update:Update,context:ContextTypes.DEFAULT_TYPE):

    barcode=update.message.text.strip()

    if not barcode.isdigit():
        return

    produk=cari_upc(barcode)

    if produk:

        sku,nama,harga,stok=produk

        text=(
        f"📦 Produk Ditemukan\n\n"
        f"Nama : {nama}\n"
        f"SKU : {sku}\n"
        f"Harga : Rp {harga:,.0f}\n"
        f"Stok : {stok}\n"
        f"UPC : {barcode}"
        )

    else:

        text=(
        f"❌ Produk tidak ditemukan\n\n"
        f"UPC : {barcode}"
        )

    await update.message.reply_text(text,reply_markup=tombol_scan())


# ================= COMMAND SKU =================

async def sku(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if len(context.args)==0:

        await update.message.reply_text(
        "Gunakan:\n/sku 91774219"
        )
        return

    kode=context.args[0]

    produk=cari_sku(kode)

    if produk:

        nama,harga,stok,upc=produk

        text=(
        f"📦 Produk Ditemukan\n\n"
        f"Nama : {nama}\n"
        f"SKU : {kode}\n"
        f"Harga : Rp {harga:,.0f}\n"
        f"Stok : {stok}\n"
        f"UPC : {upc}"
        )

    else:

        text="Produk tidak ditemukan"

    await update.message.reply_text(text)


# ================= COMMAND NAMA =================

async def nama(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if len(context.args)==0:

        await update.message.reply_text(
        "Gunakan:\n/nama kacang"
        )
        return

    keyword=" ".join(context.args)

    hasil=cari_nama(keyword)

    if not hasil:

        await update.message.reply_text(
        "Produk tidak ditemukan"
        )
        return

    text="🔎 Hasil pencarian:\n\n"

    for sku,nama,harga,stok,upc in hasil:

        text+=(
        f"{nama}\n"
        f"SKU : {sku}\n"
        f"Harga : Rp {harga:,.0f}\n"
        f"UPC : {upc}\n\n"
        )

    await update.message.reply_text(text)


# ================= MAIN =================

def main():

    print("BOT RETUR VENDOR AKTIF")

    app=ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("sku",sku))
    app.add_handler(CommandHandler("nama",nama))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_barcode
        )
    )

    app.run_polling()


if __name__=="__main__":
    main()
