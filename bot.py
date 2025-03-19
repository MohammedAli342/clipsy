import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# إعدادات البوت
TOKEN = "7801778015:AAHxZMN1LW3vXjeT5N2h860RV4mixTM2ork"
CHANNEL_USERNAME = "@hormon1"
CHANNEL_LINK = "https://t.me/hormon1"
COOKIES_FILE = "cookies.txt"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ========== إصلاح 1: إضافة async للدالة start_command ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "✨ *مرحبًا بك في بوت التحميل!* ✨\n\n"
        "📥 أرسل رابط الفيديو من:\n"
        "- تيك توك\n- يوتيوب\n- إنستجرام\n- فيسبوك\n- +1000 منصة أخرى!\n\n"
        "⚠️ *ملاحظة:* يجب الاشتراك في قناتنا أولاً: @hormon1"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# ========== إصلاح 2: تعديل دالة فحص الاشتراك ==========
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"خطأ في فحص الاشتراك: {str(e)}")
        return False

# ========== إصلاح 3: تحسين معالجة ملفات التيك توك ==========
async def handle_media_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    url = update.message.text.strip()

    if not await check_subscription(user.id, context):
        keyboard = [
            [InlineKeyboardButton("قناة المطور 📢", url=CHANNEL_LINK)],
            [InlineKeyboardButton("تأكيد الاشتراك ✅", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "🔒 يجب الاشتراك في القناة أولاً",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text("⏳ جاري التحميل...")

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            'user_agent': 'com.ss.android.ugc.trill/2613 (Linux; U; Android 12; en_US; Pixel 6 Pro; Build/SP2A.220405.004;tt-ok/3.12.13.1)',
            'referer': 'https://www.tiktok.com/',
            'extractor_args': {
                'instagram': {'story': ['yes']},
                'facebook': {'story': ['yes']},
                'tiktok': {'app_version': '25.1.3', 'manifest_app_version': '2023103101'}
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

            # ========== إصلاح 4: إغلاق الملف بشكل صحيح بعد الإرسال ==========
            with open(filepath, 'rb') as file:
                if info.get('ext') == 'mp4':
                    await update.message.reply_video(
                        video=file,
                        caption=f"🎬 {info.get('title', '')}"
                    )
                else:
                    await update.message.reply_document(
                        document=file,
                        caption=f"📁 {info.get('title', '')}"
                    )

    except yt_dlp.utils.DownloadError as e:
        error_msg = "⚠️ خطأ في التحميل:"
        if "Private" in str(e):
            error_msg += "\n- المحتوى خاص أو يحتاج تسجيل دخول"
        elif "unavailable" in str(e):
            error_msg += "\n- الرابط غير صالح"
        await update.message.reply_text(error_msg)
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ غير متوقع: {str(e)}")
    finally:
        # ========== إصلاح 5: حذف الملف بعد الإرسال ==========
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_sub":
        if await check_subscription(query.from_user.id, context):
            await query.edit_message_text("✅ تم التحقق! يمكنك استخدام البوت الآن")
        else:
            await query.edit_message_text("❌ لم تشترك بعد!")

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    app = Application.builder().token(TOKEN).build()
    
    # ========== إصلاح 6: تصحيح تسجيل المعالجات ==========
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media_request))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    app.run_polling()