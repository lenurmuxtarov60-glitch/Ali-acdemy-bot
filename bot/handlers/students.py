from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from bot.config import ROLE_SUPER_ADMIN
from bot.keyboards.menus import (
    admin_menu_keyboard,
    back_keyboard,
    student_actions_keyboard,
    main_menu_keyboard,
)
from bot.models import Student, Group, get_session
from bot.utils.helpers import get_user_by_telegram_id, is_admin, is_teacher

(S_FULL_NAME, S_GROUP, S_SEARCH, E_FULL_NAME) = range(4)


def _save_student(full_name: str, group_id: int = None) -> tuple[str, int | None]:
    with get_session() as session:
        student = Student(
            full_name=full_name,
            group_id=group_id,
            phone="",
            parent_name="",
            parent_phone="",
        )
        session.add(student)
        session.flush()
        return student.full_name, student.id


async def students_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bu bo'lim faqat adminlar uchun.")
        return
    await update.message.reply_text(
        "👨‍🎓 <b>O'quvchilar boshqaruvi</b>\n\nKerakli amalni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(),
    )


async def add_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text(
        "➕ <b>Yangi o'quvchi qo'shish</b>\n\n"
        "O'quvchi <b>ism-familiyasini</b> kiriting:",
        parse_mode="HTML",
        reply_markup=back_keyboard(),
    )
    return S_FULL_NAME


async def receive_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel(update, context)

    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Ism-familiya juda qisqa. Qayta kiriting:")
        return S_FULL_NAME

    context.user_data["student_name"] = name
    with get_session() as session:
        groups = session.query(Group).filter_by(is_active=True).all()
    if not groups:
        saved_name, _ = _save_student(name)
        await update.message.reply_text(
            f"✅ <b>{saved_name}</b> o'quvchilar ro'yxatiga qo'shildi!",
            parse_mode="HTML",
            reply_markup=admin_menu_keyboard(),
        )
        context.user_data.clear()
        return ConversationHandler.END

    from bot.keyboards.menus import groups_keyboard
    await update.message.reply_text(
        f"👤 <b>{name}</b>\n\nGuruhni tanlang:",
        parse_mode="HTML",
        reply_markup=groups_keyboard(groups, "addgrp_"),
    )
    return S_GROUP


async def receive_group_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    name = context.user_data.get("student_name", "")
    if query.data.startswith("addgrp_group_"):
        group_id = int(query.data.split("_")[-1])
        saved_name, _ = _save_student(name, group_id)
        with get_session() as session:
            group = session.query(Group).filter_by(id=group_id).first()
            group_name = group.name if group else ""
    else:
        saved_name, _ = _save_student(name)
        group_name = ""

    parts = [f"✅ <b>{saved_name}</b> o'quvchilar ro'yxatiga qo'shildi!"]
    if group_name:
        parts.append(f"📚 Guruh: <b>{group_name}</b>")
    await query.message.edit_text(
        "\n".join(parts),
        parse_mode="HTML",
    )
    await query.message.reply_text(
        "👨‍🎓 <b>O'quvchilar boshqaruvi</b>",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def list_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    with get_session() as session:
        students = session.query(Student).filter_by(is_active=True).order_by(Student.full_name).all()
        if not students:
            await update.message.reply_text("📋 O'quvchilar ro'yxati bo'sh.")
            return

        lines = ["📋 <b>O'quvchilar ro'yxati</b>\n"]
        for i, s in enumerate(students, 1):
            lines.append(f"{i}. <b>{s.full_name}</b>")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def search_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data.pop("search_mode", None)
    await update.message.reply_text(
        "🔍 O'quvchi ismini kiriting:",
        reply_markup=back_keyboard(),
    )
    return S_SEARCH


async def delete_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data["search_mode"] = "delete"
    await update.message.reply_text(
        "🗑 O'chirmoqchi bo'lgan o'quvchi ismini kiriting:",
        reply_markup=back_keyboard(),
    )
    return S_SEARCH


async def stats_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_teacher(update.effective_user.id):
        return ConversationHandler.END
    context.user_data["search_mode"] = "stats"
    await update.message.reply_text(
        "📊 Statistika uchun o'quvchi ismini kiriting:",
        reply_markup=back_keyboard(),
    )
    return S_SEARCH


async def search_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel(update, context)

    query_text = update.message.text.strip()
    mode = context.user_data.pop("search_mode", None)

    with get_session() as session:
        students = (
            session.query(Student)
            .filter(Student.full_name.ilike(f"%{query_text}%"), Student.is_active == True)
            .limit(10)
            .all()
        )

    if not students:
        await update.message.reply_text("❌ O'quvchi topilmadi.", reply_markup=admin_menu_keyboard())
        return ConversationHandler.END

    if mode == "stats":
        from bot.services.reports import ReportService
        for s in students[:3]:
            await update.message.reply_text(ReportService.student_stats(s.id), parse_mode="HTML")
        return ConversationHandler.END

    for s in students:
        text = (
            f"👨‍🎓 <b>{s.full_name}</b>\n"
            f"📅 {s.registered_at.strftime('%d.%m.%Y')}"
        )
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=student_actions_keyboard(s.id),
        )
    return ConversationHandler.END


async def edit_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text(
        "✏️ Tahrirlash uchun o'quvchi ismini kiriting:",
        reply_markup=back_keyboard(),
    )
    return S_SEARCH


async def edit_student_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    student_id = int(query.data.split("_")[-1])
    context.user_data["edit_student_id"] = student_id

    with get_session() as session:
        student = session.query(Student).filter_by(id=student_id).first()

    if not student:
        await query.edit_message_text("❌ O'quvchi topilmadi.")
        return ConversationHandler.END

    await query.message.reply_text(
        f"✏️ <b>{student.full_name}</b> tahrirlanmoqda.\n\n"
        f"Yangi F.I.O kiriting yoki 🔙 Orqaga bosing:",
        parse_mode="HTML",
        reply_markup=back_keyboard(),
    )
    return E_FULL_NAME


async def edit_receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel(update, context)

    student_id = context.user_data.get("edit_student_id")
    with get_session() as session:
        student = session.query(Student).filter_by(id=student_id).first()
        if student:
            student.full_name = update.message.text.strip()

    await update.message.reply_text(
        "✅ O'quvchi ma'lumotlari yangilandi!",
        reply_markup=admin_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def delete_student_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    student_id = int(query.data.split("_")[-1])

    with get_session() as session:
        student = session.query(Student).filter_by(id=student_id).first()
        if student:
            student.is_active = False
            await query.edit_message_text(f"✅ {student.full_name} o'chirildi (deaktiv).")
        else:
            await query.edit_message_text("❌ O'quvchi topilmadi.")


async def stats_student_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.services.reports import ReportService

    query = update.callback_query
    await query.answer()
    student_id = int(query.data.split("_")[-1])
    text = ReportService.student_stats(student_id)
    await query.message.reply_text(text, parse_mode="HTML")


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = get_user_by_telegram_id(update.effective_user.id)
    role = user.role if user else ROLE_SUPER_ADMIN
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_menu_keyboard(role))
    return ConversationHandler.END


def register_student_handlers(application):
    add_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ O'quvchi qo'shish$"), add_student_start)],
        states={
            S_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_full_name)],
            S_GROUP: [CallbackQueryHandler(receive_group_selection, pattern=r"^addgrp_(group_\d+|skip)$")],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Orqaga$"), _cancel)],
    )

    search_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🔍 O'quvchi qidirish$"), search_student_start),
            MessageHandler(filters.Regex("^🗑 O'quvchini o'chirish$"), delete_student_start),
            MessageHandler(filters.Regex("^🔍 Qidiruv$"), search_student_start),
            MessageHandler(filters.Regex("^👨‍🎓 O'quvchi statistikasi$"), stats_search_start),
        ],
        states={
            S_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_student)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Orqaga$"), _cancel)],
    )

    edit_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^✏️ O'quvchini tahrirlash$"), edit_student_start),
            CallbackQueryHandler(edit_student_callback, pattern=r"^edit_student_\d+$"),
        ],
        states={
            S_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_student)],
            E_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_receive_name)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Orqaga$"), _cancel)],
    )

    application.add_handler(add_conv)
    application.add_handler(search_conv)
    application.add_handler(edit_conv)
    application.add_handler(MessageHandler(filters.Regex("^👨‍🎓 O'quvchilar$"), students_menu))
    application.add_handler(MessageHandler(filters.Regex("^📋 Barcha o'quvchilar$"), list_students))
    application.add_handler(CallbackQueryHandler(delete_student_callback, pattern=r"^delete_student_\d+$"))
    application.add_handler(CallbackQueryHandler(stats_student_callback, pattern=r"^stats_student_\d+$"))
