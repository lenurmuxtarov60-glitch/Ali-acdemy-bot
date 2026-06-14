import logging

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import (
    ADMIN_BOT_TOKEN,
    CENTER_NAME,
    PARENT_BOT_TOKEN,
    ATTENDANCE_STATUS,
    PARTICIPATION_LEVELS,
    build_parent_message,
)
from bot.models import Attendance, get_session
from bot.services.parent_requests import ParentRequestService

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def _parent_bot() -> Bot | None:
        if not PARENT_BOT_TOKEN:
            logger.error("PARENT_BOT_TOKEN o'rnatilmagan")
            return None
        return Bot(PARENT_BOT_TOKEN)

    @staticmethod
    def _admin_bot() -> Bot | None:
        if not ADMIN_BOT_TOKEN:
            logger.error("ADMIN_BOT_TOKEN o'rnatilmagan")
            return None
        return Bot(ADMIN_BOT_TOKEN)

    @staticmethod
    def format_attendance_for_parent(student_name: str, status: str, participation: str | None = None, course_name: str = "") -> str:
        today_str = __import__("datetime").date.today().strftime("%d.%m.%Y")
        status_info = ATTENDANCE_STATUS.get(status, {})
        lines = [
            f"🎓 <b>{CENTER_NAME}</b>",
            "",
            f"👨‍🎓 <b>{student_name}</b>",
        ]
        if course_name:
            lines.append(f"📚 Kurs: <b>{course_name}</b>")
        lines += [
            f"📅 {today_str}",
            "",
            f"{status_info.get('emoji', '')} Darsga: <b>{status_info.get('label', status)}</b>",
        ]
        if status == "present" and participation:
            part = PARTICIPATION_LEVELS.get(participation, {})
            lines.append(
                f"{part.get('emoji', '')} Qatnashish: <b>{part.get('label', participation)}</b>"
            )
        elif status == "absent":
            lines.append("❌ Darsda qatnashmadi.")
        return "\n".join(lines)

    @staticmethod
    async def send_to_parent(chat_id: int, text: str) -> bool:
        bot = NotificationService._parent_bot()
        if not bot:
            return False
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            return True
        except Exception as e:
            logger.error(f"Ota-onaga xabar yuborilmadi: {e}")
            return False

    @staticmethod
    async def notify_parent_result(
        chat_id: int,
        student_name: str,
        status: str,
        participation: str | None = None,
        course_name: str = "",
    ) -> bool:
        text = NotificationService.format_attendance_for_parent(
            student_name, status, participation, course_name
        )
        return await NotificationService.send_to_parent(chat_id, text)

    @staticmethod
    async def notify_staff_parent_request(request_id: int, student_name: str, parent_name: str, parent_id: int, course_name: str = ""):
        bot = NotificationService._admin_bot()
        if not bot:
            return

        from datetime import date
        course_line = f"\n📚 Kurs: <b>{course_name}</b>" if course_name else ""
        text = (
            f"📩 <b>Yangi ota-ona so'rovi</b>\n\n"
            f"👨‍👩‍👧 Kimdan: <b>{parent_name or 'Nomalum'}</b>\n"
            f"🆔 ID: <code>{parent_id}</code>\n"
            f"👨‍🎓 O'quvchi: <b>{student_name}</b>{course_line}\n"
            f"📅 {date.today().strftime('%d.%m.%Y')}\n\n"
            f"Tasdiqlaysizmi?"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 Keldi", callback_data=f"preq_{request_id}_present"),
                InlineKeyboardButton("🔴 Kelmadi", callback_data=f"preq_{request_id}_absent"),
            ]
        ])

        for chat_id in ParentRequestService.get_staff_telegram_ids():
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception as e:
                logger.error(f"Adminga xabar yuborilmadi ({chat_id}): {e}")

    @staticmethod
    async def notify_after_attendance(
        student_id: int,
        status: str,
        attendance_id: int,
        participation: str | None = None,
        parent_chat_id: int | None = None,
    ):
        if not parent_chat_id:
            return

        from bot.models import Student, Group
        with get_session() as session:
            student = session.query(Student).filter_by(id=student_id).first()
            if not student:
                return
            name = student.full_name
            course_name = ""
            if student.group_id:
                group = session.query(Group).filter_by(id=student.group_id).first()
                if group:
                    course_name = group.name

        sent = await NotificationService.notify_parent_result(
            parent_chat_id, name, status, participation, course_name
        )
        if sent:
            with get_session() as session:
                record = session.query(Attendance).filter_by(id=attendance_id).first()
                if record:
                    record.notified = True
