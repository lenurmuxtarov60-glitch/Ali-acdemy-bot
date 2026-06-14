from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.config import CENTER_NAME, MAIN_TEACHER
from bot.keyboards.menus import settings_menu_keyboard, main_menu_keyboard
from bot.utils.helpers import get_user_by_telegram_id, is_teacher


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        await update.message.reply_text(
            "❌ Bu bo'lim faqat admin va o'qituvchilar uchun.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await update.message.reply_text(
        "⚙️ <b>Sozlamalar</b>",
        parse_mode="HTML",
        reply_markup=settings_menu_keyboard(),
    )


async def about_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return

    text = (
        f"ℹ️ <b>{CENTER_NAME}</b>\n\n"
        f"📋 Davomat Bot — Ota-onalar uchun davomat tizimi\n"
        f"👨‍🏫 Asosiy o'qituvchi: <b>{MAIN_TEACHER}</b>\n\n"
        f"👨‍👩‍👧 Ota-onalar farzand ismini yozib davomatni tekshiradi.\n"
        f"✅ Admin darsda keldi/kelmadi va qatnashish darajasini belgilaydi.\n\n"
        f"🤖 Bot versiyasi: 2.0.0"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return

    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)

    role_names = {
        "super_admin": "Super Admin",
        "teacher": "O'qituvchi",
    }
    role = role_names.get(db_user.role if db_user else "", "Noma'lum")

    text = (
        f"👤 <b>Mening profilim</b>\n\n"
        f"📛 Ism: {user.full_name}\n"
        f"🆔 Telegram ID: <code>{user.id}</code>\n"
        f"🔑 Rol: {role}\n"
        f"📱 Telefon: {db_user.phone if db_user and db_user.phone else 'Kiritilmagan'}"
    )
    await update.message.reply_text(text, parse_mode="HTML")


def register_settings_handlers(application):
    application.add_handler(MessageHandler(filters.Regex("^⚙️ Sozlamalar$"), settings_menu))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ Markaz haqida$"), about_center))
    application.add_handler(MessageHandler(filters.Regex("^👤 Mening profilim$"), my_profile))
