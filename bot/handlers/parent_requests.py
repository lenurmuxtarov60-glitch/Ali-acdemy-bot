from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from bot.config import PARTICIPATION_LEVELS
from bot.models import Student, User, get_session
from bot.services.attendance import AttendanceService
from bot.services.notifications import NotificationService
from bot.services.parent_requests import ParentRequestService
from bot.utils.helpers import is_teacher


def _participation_keyboard(request_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for key, info in PARTICIPATION_LEVELS.items():
        buttons.append([
            InlineKeyboardButton(
                f"{info['emoji']} {info['label']}",
                callback_data=f"preqpart_{request_id}_{key}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


async def handle_parent_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_teacher(query.from_user.id):
        await query.edit_message_text("❌ Ruxsat yo'q.")
        return

    parts = query.data.split("_")
    request_id = int(parts[1])
    action = parts[2]

    req = ParentRequestService.get_request(request_id)
    if not req or req.status != "pending":
        await query.edit_message_text("ℹ️ Bu so'rov allaqachon ko'rib chiqilgan.")
        return

    with get_session() as session:
        student = session.query(Student).filter_by(id=req.student_id).first()

    if not student:
        await query.edit_message_text("❌ O'quvchi topilmadi.")
        return

    if action == "present":
        await query.edit_message_text(
            f"👨‍🎓 <b>{student.full_name}</b>\n\n"
            f"🟢 Keldi — qatnashish darajasini tanlang:",
            parse_mode="HTML",
            reply_markup=_participation_keyboard(request_id),
        )
        return

    if action == "absent":
        await _finalize_request(query, request_id, student, "absent", None)


async def handle_parent_request_participation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_teacher(query.from_user.id):
        await query.edit_message_text("❌ Ruxsat yo'q.")
        return

    parts = query.data.split("_")
    request_id = int(parts[1])
    participation = parts[2]

    req = ParentRequestService.get_request(request_id)
    if not req or req.status != "pending":
        await query.edit_message_text("ℹ️ Bu so'rov allaqachon ko'rib chiqilgan.")
        return

    with get_session() as session:
        student = session.query(Student).filter_by(id=req.student_id).first()

    if not student:
        await query.edit_message_text("❌ O'quvchi topilmadi.")
        return

    await _finalize_request(query, request_id, student, "present", participation)


async def _finalize_request(query, request_id: int, student, status: str, participation: str | None):
    req = ParentRequestService.get_request(request_id)
    if not req:
        return

    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=query.from_user.id).first()

    record = AttendanceService.mark_attendance(
        student_id=student.id,
        group_id=student.group_id,
        status=status,
        marked_by=user.id if user else None,
        participation=participation,
    )

    ParentRequestService.complete_request(request_id, "approved" if status == "present" else "rejected")

    part_label = ""
    if participation:
        part_label = f" ({PARTICIPATION_LEVELS[participation]['label']})"

    status_label = "Keldi" if status == "present" else "Kelmadi"
    await query.edit_message_text(
        f"✅ <b>{student.full_name}</b> — {status_label}{part_label}\n"
        f"Ota-onaga xabar yuborildi.",
        parse_mode="HTML",
    )

    await NotificationService.notify_after_attendance(
        student.id,
        status,
        record.id,
        participation,
        parent_chat_id=req.parent_telegram_id,
    )


def register_parent_request_handlers(application):
    application.add_handler(
        CallbackQueryHandler(handle_parent_request, pattern=r"^preq_\d+_(present|absent)$")
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_parent_request_participation,
            pattern=r"^preqpart_\d+_(good|average|bad)$",
        )
    )
