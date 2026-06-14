from datetime import date

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters

from bot.config import ATTENDANCE_STATUS, PARTICIPATION_LEVELS
from bot.keyboards.menus import (
    attendance_menu_keyboard,
    groups_keyboard,
    attendance_status_keyboard,
    participation_keyboard,
)
from bot.models import Group, Student, User, TeacherGroup, get_session
from bot.services.attendance import AttendanceService
from bot.services.notifications import NotificationService
from bot.services.parent_requests import ParentRequestService
from bot.utils.helpers import get_user_by_telegram_id, is_admin, is_teacher


async def attendance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        await update.message.reply_text("❌ Bu bo'lim faqat o'qituvchilar uchun.")
        return
    await update.message.reply_text(
        "✅ <b>Davomat boshqaruvi</b>",
        parse_mode="HTML",
        reply_markup=attendance_menu_keyboard(),
    )


def _get_teacher_groups(telegram_id: int) -> list:
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return []
        if is_admin(telegram_id):
            return session.query(Group).filter_by(is_active=True).all()
        tg_ids = session.query(TeacherGroup.group_id).filter_by(teacher_id=user.id).all()
        group_ids = [g[0] for g in tg_ids]
        return session.query(Group).filter(Group.id.in_(group_ids), Group.is_active == True).all()


async def mark_attendance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    user_id = update.effective_user.id
    groups = _get_teacher_groups(user_id)
    buttons = []

    if is_admin(user_id):
        buttons.append([InlineKeyboardButton("👥 Barcha o'quvchilar", callback_data="attgrp_all")])
    for g in groups:
        buttons.append([InlineKeyboardButton(g.name, callback_data=f"attgrp_group_{g.id}")])

    if not buttons:
        await update.message.reply_text("❌ Sizga biriktirilgan guruhlar yo'q.")
        return

    await update.message.reply_text(
        "Davomat belgilash — o'quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _show_student_list_for_attendance(query, students: list, title: str, result_callback: str | None = None):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.models import Attendance

    today = date.today()
    with get_session() as session:
        student_ids = [s.id for s in students]
        records = (
            session.query(Attendance)
            .filter(Attendance.student_id.in_(student_ids), Attendance.date == today)
            .all()
        ) if student_ids else []
    status_map = {r.student_id: r.status for r in records}

    lines = [f"✅ <b>{title}</b> — Bugungi davomat", f"📅 {today.strftime('%d.%m.%Y')}\n"]
    await query.edit_message_text("\n".join(lines), parse_mode="HTML")

    buttons = []
    for s in students:
        status = status_map.get(s.id, "unmarked")
        if status == "present":
            icon = "🟢"
        elif status == "absent":
            icon = "🔴"
        else:
            icon = "⚪"
        buttons.append([
            InlineKeyboardButton(f"{icon} {s.full_name}", callback_data=f"attselect_{s.id}")
        ])
    if result_callback:
        buttons.append([InlineKeyboardButton("📋 Jami natija", callback_data=result_callback)])
    await query.message.reply_text(
        "O'quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def select_group_for_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "attgrp_all":
        with get_session() as session:
            students = (
                session.query(Student)
                .filter_by(is_active=True)
                .order_by(Student.full_name)
                .all()
            )
        if not students:
            await query.edit_message_text("❌ O'quvchilar yo'q.")
            return
        context.user_data["attendance_group_id"] = None
        await _show_student_list_for_attendance(query, students, "Barcha o'quvchilar", "attresult_all")
        return

    if not query.data.startswith("attgrp_group_"):
        return

    group_id = int(query.data.split("_")[-1])
    context.user_data["attendance_group_id"] = group_id

    with get_session() as session:
        students = (
            session.query(Student)
            .filter_by(group_id=group_id, is_active=True)
            .order_by(Student.full_name)
            .all()
        )
        group = session.query(Group).filter_by(id=group_id).first()

    if not students:
        await query.edit_message_text(f"❌ {group.name} guruhida o'quvchilar yo'q.")
        return

    await _show_student_list_for_attendance(
        query, students, group.name, f"attresult_{group_id}"
    )


async def select_student_for_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "attresult_all":
        return await show_all_today_results(query)
    if query.data.startswith("attresult_"):
        group_id = int(query.data.split("_")[-1])
        return await show_today_results(query, group_id)

    student_id = int(query.data.split("_")[-1])
    with get_session() as session:
        student = session.query(Student).filter_by(id=student_id).first()

    await query.edit_message_text(
        f"👨‍🎓 <b>{student.full_name}</b>\n\nDavomat holatini tanlang:",
        parse_mode="HTML",
        reply_markup=attendance_status_keyboard(student_id),
    )


async def mark_attendance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    student_id = int(parts[1])
    status = parts[2]

    with get_session() as session:
        student = session.query(Student).filter_by(id=student_id).first()

    if not student:
        await query.edit_message_text("❌ O'quvchi topilmadi.")
        return

    if status == "present":
        await query.edit_message_text(
            f"👨‍🎓 <b>{student.full_name}</b>\n\n"
            f"🟢 Keldi — qatnashish darajasini tanlang:",
            parse_mode="HTML",
            reply_markup=participation_keyboard(student_id),
        )
        return

    await _save_attendance(query, context, student, status)


async def mark_participation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    student_id = int(parts[1])
    participation = parts[2]

    with get_session() as session:
        student = session.query(Student).filter_by(id=student_id).first()

    if not student:
        await query.edit_message_text("❌ O'quvchi topilmadi.")
        return

    await _save_attendance(query, context, student, "present", participation)


async def _save_attendance(query, context, student, status: str, participation: str | None = None):
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=query.from_user.id).first()

    record = AttendanceService.mark_attendance(
        student_id=student.id,
        group_id=student.group_id,
        status=status,
        marked_by=user.id if user else None,
        participation=participation,
    )

    status_info = ATTENDANCE_STATUS.get(status, {})
    lines = [
        f"✅ <b>{student.full_name}</b>",
        f"{status_info.get('emoji', '')} {status_info.get('label', status)} — saqlandi!",
    ]
    if participation:
        part = PARTICIPATION_LEVELS.get(participation, {})
        lines.append(f"{part.get('emoji', '')} Qatnashish: {part.get('label', participation)}")

    await query.edit_message_text("\n".join(lines), parse_mode="HTML")

    parent_chat = ParentRequestService.get_parent_chat_for_student_today(student.id)
    if parent_chat:
        await NotificationService.notify_after_attendance(
            student.id, status, record.id, participation, parent_chat_id=parent_chat
        )


async def show_all_today_results(query):
    from bot.models import Attendance

    today = date.today()
    with get_session() as session:
        students = session.query(Student).filter_by(is_active=True).order_by(Student.full_name).all()
        records = session.query(Attendance).filter_by(date=today).all()
    record_map = {r.student_id: r for r in records}

    lines = [f"📋 <b>Barcha o'quvchilar</b> — Bugungi natija", f"📅 {today.strftime('%d.%m.%Y')}\n"]
    present = absent = unmarked = 0
    for s in students:
        rec = record_map.get(s.id)
        st = rec.status if rec else "unmarked"
        if st == "present":
            icon, present = "🟢", present + 1
            part_label = ""
            if rec and rec.participation:
                pinfo = PARTICIPATION_LEVELS.get(rec.participation, {})
                part_label = f" ({pinfo.get('label', rec.participation)})"
            lines.append(f"{icon} {s.full_name}{part_label}")
        elif st == "absent":
            icon, absent = "🔴", absent + 1
            lines.append(f"{icon} {s.full_name}")
        else:
            icon, unmarked = "⚪", unmarked + 1
            lines.append(f"{icon} {s.full_name}")
    lines.append(f"\n📊 Jami: 🟢{present} 🔴{absent} ⚪{unmarked}")
    await query.edit_message_text("\n".join(lines), parse_mode="HTML")


async def show_today_results(query, group_id: int):
    records = AttendanceService.get_today_attendance(group_id)
    with get_session() as session:
        group = session.query(Group).filter_by(id=group_id).first()

    lines = [f"📋 <b>{group.name}</b> — Bugungi natija\n"]
    lines.append(f"📅 {date.today().strftime('%d.%m.%Y')}\n")

    present = absent = unmarked = 0
    for item in records:
        s = item["student"]
        st = item["status"]
        part = item.get("participation")
        if st == "present":
            icon, present = "🟢", present + 1
            part_label = ""
            if part:
                pinfo = PARTICIPATION_LEVELS.get(part, {})
                part_label = f" ({pinfo.get('label', part)})"
            lines.append(f"{icon} {s.full_name}{part_label}")
        elif st == "absent":
            icon, absent = "🔴", absent + 1
            lines.append(f"{icon} {s.full_name}")
        else:
            icon, unmarked = "⚪", unmarked + 1
            lines.append(f"{icon} {s.full_name}")

    lines.append(f"\n📊 Jami: 🟢{present} 🔴{absent} ⚪{unmarked}")
    await query.edit_message_text("\n".join(lines), parse_mode="HTML")


async def today_attendance_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return

    groups = _get_teacher_groups(update.effective_user.id)
    if not groups:
        await update.message.reply_text("❌ Guruhlar yo'q.")
        return

    await update.message.reply_text(
        "Guruhni tanlang:",
        reply_markup=groups_keyboard(groups, "today_"),
    )


async def today_attendance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group_id = int(query.data.split("_")[-1])
    await show_today_results(query, group_id)


def register_attendance_handlers(application):
    application.add_handler(MessageHandler(filters.Regex("^✅ Davomat$"), attendance_menu))
    application.add_handler(MessageHandler(filters.Regex("^✅ Davomat belgilash$"), mark_attendance_start))
    application.add_handler(MessageHandler(filters.Regex("^📋 Bugungi davomat$"), today_attendance_view))
    application.add_handler(CallbackQueryHandler(select_group_for_attendance, pattern=r"^attgrp_(all|group_\d+)$"))
    application.add_handler(CallbackQueryHandler(select_student_for_attendance, pattern=r"^attselect_\d+$"))
    application.add_handler(CallbackQueryHandler(select_student_for_attendance, pattern=r"^attresult_(all|\d+)$"))
    application.add_handler(CallbackQueryHandler(mark_attendance_callback, pattern=r"^att_\d+_(present|absent)$"))
    application.add_handler(CallbackQueryHandler(mark_participation_callback, pattern=r"^part_\d+_(good|average|bad)$"))
    application.add_handler(CallbackQueryHandler(today_attendance_callback, pattern=r"^today_group_\d+$"))
