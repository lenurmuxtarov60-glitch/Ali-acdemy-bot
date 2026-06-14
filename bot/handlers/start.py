from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from bot.config import CENTER_NAME, MAIN_TEACHER, PARENT_BOT_USERNAME, ROLE_SUPER_ADMIN, ROLE_TEACHER
from bot.keyboards.menus import main_menu_keyboard
from bot.utils.helpers import get_user_by_telegram_id, is_teacher


def get_staff_welcome_text(role: str, name: str) -> str:
    base = (
        f"🎓 <b>{CENTER_NAME}</b>\n"
        f"🔑 <b>Admin Panel</b>\n\n"
        f"Assalomu alaykum, <b>{name}</b>!\n"
        f"👨‍🏫 Asosiy o'qituvchi: <b>{MAIN_TEACHER}</b>\n\n"
    )
    if role == ROLE_SUPER_ADMIN:
        return base + "🔑 Siz <b>Super Admin</b> sifatida tizimga kirdingiz."
    return base + "👨‍🏫 Siz <b>O'qituvchi</b> sifatida tizimga kirdingiz."


def get_parent_welcome_text(name: str) -> str:
    return (
        f"Assalomu alaykum! <b>{CENTER_NAME}</b> botiga xush kelibsiz!\n\n"
        f"Farzandingizni <b>ism va familyasini</b> yozing.\n"
        f"Masalan: Ismoilov Ismoil"
    )


def get_admin_guest_text() -> str:
    parent_hint = ""
    if PARENT_BOT_USERNAME:
        parent_hint = f"\n\n👨‍👩‍👧 Ota-onalar uchun bot: @{PARENT_BOT_USERNAME}"
    return (
        f"🎓 <b>{CENTER_NAME}</b>\n"
        f"🔑 <b>Admin Panel Bot</b>\n\n"
        f"❌ Bu bot faqat <b>admin</b> va <b>o'qituvchilar</b> uchun.\n"
        f"Ota-ona so'rovlari shu yerga keladi — tasdiqlang yoki rad eting."
        f"{parent_hint}"
    )


async def admin_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.full_name or "Foydalanuvchi"
    db_user = get_user_by_telegram_id(user.id)

    if db_user and db_user.role in (ROLE_SUPER_ADMIN, ROLE_TEACHER):
        text = get_staff_welcome_text(db_user.role, name)
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(db_user.role),
        )
    else:
        await update.message.reply_text(
            get_admin_guest_text(),
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )


async def parent_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.full_name or "Foydalanuvchi"
    await update.message.reply_text(
        get_parent_welcome_text(name),
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


async def home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)

    if not db_user or not is_teacher(user.id):
        await update.message.reply_text(
            get_admin_guest_text(),
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    text = get_staff_welcome_text(db_user.role, user.full_name or db_user.full_name)
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(db_user.role),
    )


def register_admin_start_handlers(application):
    application.add_handler(CommandHandler("start", admin_start_command))
    application.add_handler(CommandHandler("help", admin_start_command))
    application.add_handler(MessageHandler(filters.Regex("^🏠 Bosh sahifa$"), home_handler))


def register_parent_start_handlers(application):
    application.add_handler(CommandHandler("start", parent_start_command))
    application.add_handler(CommandHandler("help", parent_start_command))
