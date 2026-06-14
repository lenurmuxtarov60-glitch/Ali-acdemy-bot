from datetime import date

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.services.attendance import AttendanceService
from bot.services.notifications import NotificationService
from bot.services.parent_requests import ParentRequestService


async def parent_name_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if text.startswith("/"):
        return

    user = update.effective_user
    students = ParentRequestService.find_student_by_name(text)

    if not students:
        await update.message.reply_text(
            f"❌ <b>{text}</b> ismli o'quvchi topilmadi.\n\n"
            f"Farzandingiz <b>ism-familiyasini</b> to'g'ri yozing.",
            parse_mode="HTML",
        )
        return

    if len(students) > 1:
        lines = [f"🔍 <b>{len(students)} ta o'quvchi topildi:</b>\n"]
        for s in students:
            lines.append(f"• {s.full_name}")
        lines.append("\nAniqroq ism yozing.")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return

    student = students[0]
    record = AttendanceService.get_today_for_student(student.id)

    course_name = (student.group.course if student.group else "") or student.course or ""
    if record:
        text = NotificationService.format_attendance_for_parent(
            student.full_name, record.status, record.participation, course_name
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    if ParentRequestService.has_approved(student.id, user.id):
        if record is None:
            await update.message.reply_text(
                f"📋 <b>{student.full_name}</b> ({course_name})\n\n"
                f"❌ Bugun uchun davomat hali qayd etilmagan.\n"
                f"Keyinroq tekshiring.",
                parse_mode="HTML",
            )
        return

    pending = ParentRequestService.get_pending_today(student.id, user.id)
    if pending:
        await update.message.reply_text(
            f"⏳ <b>{student.full_name}</b> bo'yicha so'rovingiz admin ko'rib chiqmoqda.\n"
            f"Iltimos, javobni kuting.",
            parse_mode="HTML",
        )
        return

    req = ParentRequestService.create_request(student.id, user.id, user.full_name or "")
    await NotificationService.notify_staff_parent_request(
        req.id, student.full_name, user.full_name or "", user.id, course_name
    )

    await update.message.reply_text(
        f"✅ <b>{student.full_name}</b> bo'yicha so'rovingiz qabul qilindi.\n\n"
        f"Admin tekshirgach, javob shu yerga yuboriladi.",
        parse_mode="HTML",
    )


def register_parent_handlers(application):
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, parent_name_query),
        group=10,
    )
