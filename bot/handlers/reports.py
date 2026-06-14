from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.keyboards.menus import reports_menu_keyboard, main_menu_keyboard
from bot.services.reports import ReportService
from bot.services.export import ExportService
from bot.utils.helpers import get_user_by_telegram_id, is_teacher


async def reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        await update.message.reply_text(
            "❌ Bu bo'lim faqat admin va o'qituvchilar uchun.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await update.message.reply_text(
        "📊 <b>Hisobotlar</b>\n\nKerakli hisobotni tanlang:",
        parse_mode="HTML",
        reply_markup=reports_menu_keyboard(),
    )


async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return
    text = ReportService.daily_report()
    await update.message.reply_text(text, parse_mode="HTML")


async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return
    text = ReportService.weekly_report()
    await update.message.reply_text(text, parse_mode="HTML")


async def monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return
    text = ReportService.monthly_report()
    await update.message.reply_text(text, parse_mode="HTML")


async def attendance_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return
    text = ReportService.attendance_percentage_report()
    await update.message.reply_text(text, parse_mode="HTML")


async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return
    buffer = ExportService.export_excel("monthly")
    await update.message.reply_document(
        document=buffer,
        filename="davomat_oylik.xlsx",
        caption="📥 Oylik davomat hisoboti (Excel)",
    )


async def export_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return
    buffer = ExportService.export_pdf("monthly")
    await update.message.reply_document(
        document=buffer,
        filename="davomat_oylik.pdf",
        caption="📄 Oylik davomat hisoboti (PDF)",
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_telegram_id(update.effective_user.id)
    if not user or not is_teacher(update.effective_user.id):
        await update.message.reply_text(
            "❌ Ruxsat yo'q.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    await update.message.reply_text(
        "🏠 Bosh sahifa",
        reply_markup=main_menu_keyboard(user.role),
    )


def register_report_handlers(application):
    application.add_handler(MessageHandler(filters.Regex("^📊 Hisobotlar$"), reports_menu))
    application.add_handler(MessageHandler(filters.Regex("^📅 Kunlik davomat$"), daily_report))
    application.add_handler(MessageHandler(filters.Regex("^📆 Haftalik davomat$"), weekly_report))
    application.add_handler(MessageHandler(filters.Regex("^🗓 Oylik davomat$"), monthly_report))
    application.add_handler(MessageHandler(filters.Regex("^📈 Davomat foizi$"), attendance_percentage))
    application.add_handler(MessageHandler(filters.Regex("^📥 Excel eksport$"), export_excel))
    application.add_handler(MessageHandler(filters.Regex("^📄 PDF hisobot$"), export_pdf))
    application.add_handler(MessageHandler(filters.Regex("^🔙 Orqaga$"), back_to_main), group=1)
