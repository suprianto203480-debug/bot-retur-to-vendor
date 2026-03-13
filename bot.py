import os
import logging
import psycopg2
from psycopg2 import sql
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= KONFIGURASI LOGGING =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= AMBIL TOKEN & DATABASE URL =================
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TOKEN:
    logger.error("BOT_TOKEN tidak ditemukan di environment variable!")
    exit(1)

if not DATABASE_URL:
    logger.error("DATABASE_URL tidak ditemukan di environment variable!")
    exit(1)

# ================= FUNGSI DATABASE =================
def get_connection():
    """Membuat koneksi ke database PostgreSQL."""
    return psycopg2.connect(DATABASE_URL)

def cari_produk(upc: str):
    """Mencari produk berdasarkan UPC di tabel produk_master."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = sql.SQL("""
            SELECT item_desc, unit_retail, soh
            FROM produk_master
            WHERE upc = %s
            LIMIT 1
        """)
        cur.execute(query, (upc,))
        data = cur.fetchone()
        cur.close()
        conn.close()
        logger.info(f"Hasil query UPC {upc}: {data}")
        return data
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None

# ================= HANDLER START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim pesan dengan tombol untuk membuka scanner."""
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
    logger.info(f"Perintah /start dari user {update.effective_user.id}")

# ================= HANDLER DATA DARI WEB APP =================
async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menerima data barcode dari web app dan merespon."""
    logger.info("=== webapp_handler DIPANGGIL ===")
    try:
        message = update.message
        if not message or not message.web_app_data:
            logger.warning("Tidak ada web_app_data dalam pesan.")
            return

        barcode = message.web_app_data.data.strip()
        logger.info(f"BARCODE DITERIMA: {barcode}")

        produk = cari_produk(barcode)

        if produk:
            nama, harga, stok = produk
            # Format harga dengan pemisah ribuan
            harga_str = f"Rp {harga:,.0f}".replace(',', '.')
            pesan = (
                f"📦 *Produk* : {nama}\n"
                f"💰 *Harga*  : {harga_str}\n"
                f"📊 *Stok*   : {stok}\n"
                f"🔎 *UPC*    : `{barcode}`"
            )
        else:
            pesan = f"❌ *Produk tidak ditemukan*\n\n🔎 UPC: `{barcode}`"

        await message.reply_text(pesan, parse_mode='Markdown')
        logger.info("✅ Balasan terkirim ke user.")

    except Exception as e:
        logger.exception(f"❌ ERROR di webapp_handler: {e}")
        # Coba kirim pesan error ke user jika masih bisa
        try:
            await update.message.reply_text("Terjadi kesalahan internal. Silakan coba lagi.")
        except:
            pass

# ================= HANDLER UNTUK PESAN TEKS BIASA (OPSIONAL) =================
async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pesan teks biasa (misal untuk debugging)."""
    logger.info(f"Pesan teks diterima: {update.message.text}")
    await update.message.reply_text("Gunakan tombol Scan Barcode.")

# ================= MAIN =================
def main():
    """Memulai bot."""
    # Buat aplikasi
    app = ApplicationBuilder().token(TOKEN).build()

    # Tambahkan handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.WEB_APP_DATA,
            webapp_handler
        )
    )
    # Handler tambahan untuk pesan teks (opsional, bisa dihapus)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))

    logger.info("✅ BOT SCANNER AKTIF, mulai polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
