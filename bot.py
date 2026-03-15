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
        SELECT 
        sku,
        item_desc,
        upc,
        vendor_dc,
        supplier_dc,
        vendor_lokal,
        supplier_lokal,
        inner_pack
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
        SELECT
        sku,
        item_desc,
        upc,
        vendor_dc,
        supplier_dc,
        vendor_lokal,
        supplier_lokal,
        inner_pack
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
            "Scan Barcode",
            web_app=WebAppInfo(
                url="https://suprianto203480-debug.github.io/bot-retur-to-vendor/scanner.html"
            )
        )
    ]]

    return InlineKeyboardMarkup(keyboard)


# ================= COMMAND =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    teks = (
        "BOT RETUR VENDOR\n\n"
        "/scan - scan barcode\n"
        "/cari <sku/upc/nama>\n"
        "/help - bantuan"
    )

    await update.message.reply_text(
        teks,
        reply_markup=tombol_scan()
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Scan barcode produk",
        reply_markup=tombol_scan()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    teks = (
        "Menu Bot\n\n"
        "/scan - scan barcode\n"
        "/cari <sku/upc/nama>\n\n"
        "Contoh:\n"
        "/cari 8994448860567\n"
        "/cari sarung\n"
        "/cari 91774219"
    )

    await update.message.reply_text(
        teks,
        reply_markup=tombol_scan()
    )


# ================= FITUR CARI =================

async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "Gunakan: /cari <UPC / SKU / Nama Produk>",
            reply_markup=tombol_scan()
        )
        return

    keyword = " ".join(context.args)

    hasil = cari_produk_by_keyword(keyword)

    if hasil is None:

        pesan = f"Produk tidak ditemukan\n\nKeyword : {keyword}"

    elif isinstance(hasil, tuple):

        sku, desc, upc, vendor_dc, supplier_dc, vendor_lokal, supplier_lokal, inner = hasil

        pesan = (
            f"SKU : {sku}\n"
            f"DESC : {desc}\n"
            f"UPC : {upc}\n\n"
            f"VENDOR DC : {vendor_dc}\n"
            f"SUPPLIER DC : {supplier_dc}\n\n"
            f"VENDOR LOKAL : {vendor_lokal}\n"
            f"SUPPLIER LOKAL : {supplier_lokal}\n\n"
            f"INNER : {inner}"
        )

    else:

        pesan = "Beberapa produk ditemukan\n\n"

        for i, row in enumerate(hasil, start=1):

            sku, desc, upc, vendor_dc, supplier_dc, vendor_lokal, supplier_lokal, inner = row

            pesan += (
                f"{i}. {desc}\n"
                f"SKU : {sku}\n"
                f"UPC : {upc}\n\n"
            )

        if len(hasil) >= 10:
            pesan += "Maksimal 10 hasil"

    await update.message.reply_text(
        pesan,
        reply_markup=tombol_scan()
    )


# ================= SCAN BARCODE =================

async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        message = update.effective_message

        if message is None:
            print("DEBUG: message None")
            return

        if not message.web_app_data:
            print("DEBUG: web_app_data kosong")
            return

        barcode = message.web_app_data.data.strip()

        print("SCAN DATA:", barcode)

        produk = cari_produk_by_upc(barcode)

        if produk:

            sku, desc, upc, vendor_dc, supplier_dc, vendor_lokal, supplier_lokal, inner = produk

            pesan = (
                f"SKU : {sku}\n"
                f"DESC : {desc}\n"
                f"UPC : {upc}\n\n"
                f"VENDOR DC : {vendor_dc}\n"
                f"SUPPLIER DC : {supplier_dc}\n\n"
                f"VENDOR LOKAL : {vendor_lokal}\n"
                f"SUPPLIER LOKAL : {supplier_lokal}\n\n"
                f"INNER : {inner}"
            )

        else:

            pesan = f"Produk tidak ditemukan\n\nUPC : {barcode}"

        await message.reply_text(
            pesan,
            reply_markup=tombol_scan()
        )

    except Exception as e:

        print("ERROR WEBAPP HANDLER:", e)

# ================= PENCARIAN OTOMATIS =================

async def cari_otomatis(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyword = update.message.text.strip()

    hasil = cari_produk_by_keyword(keyword)

    if hasil is None:
        return

    if isinstance(hasil, tuple):

        sku, desc, upc, vendor_dc, supplier_dc, vendor_lokal, supplier_lokal, inner = hasil

        pesan = (
            f"SKU : {sku}\n"
            f"DESC : {desc}\n"
            f"UPC : {upc}\n\n"
            f"VENDOR DC : {vendor_dc}\n"
            f"SUPPLIER DC : {supplier_dc}\n\n"
            f"VENDOR LOKAL : {vendor_lokal}\n"
            f"SUPPLIER LOKAL : {supplier_lokal}\n\n"
            f"INNER : {inner}"
        )

    else:

        hasil_list = []

        for i, row in enumerate(hasil, start=1):

            sku, desc, upc, vendor_dc, supplier_dc, vendor_lokal, supplier_lokal, inner = row

            hasil_list.append(
                f"HASIL {i}\n\n"
                f"SKU : {sku}\n"
                f"DESC : {desc}\n"
                f"UPC : {upc}\n\n"
                f"VENDOR DC : {vendor_dc}\n"
                f"SUPPLIER DC : {supplier_dc}\n\n"
                f"VENDOR LOKAL : {vendor_lokal}\n"
                f"SUPPLIER LOKAL : {supplier_lokal}\n\n"
                f"INNER : {inner}"
            )

        pesan = "\n-----------------------------\n\n".join(hasil_list)

    await update.message.reply_text(pesan)
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

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            cari_otomatis
        )
    )

    print("BOT RETUR VENDOR AKTIF")

    app.run_polling()


if __name__ == "__main__":
    main()
