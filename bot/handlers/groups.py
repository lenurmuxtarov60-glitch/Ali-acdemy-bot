from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from bot.keyboards.menus import (
    groups_menu_keyboard,
    back_keyboard,
    main_menu_keyboard,
)
from bot.models import Group, Student, TeacherGroup, get_session
from bot.utils.helpers import get_user_by_telegram_id, is_admin, is_teacher

(G_NAME, G_SCHEDULE, G_EDIT) = range(3)


async def groups_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id) and not is_teacher(user_id):
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return

    if is_teacher(user_id) and not is_admin(user_id):
        await my_groups_handler(update, context)
        return

    await update.message.reply_text(
        "📚 <b>Guruhlar boshqaruvi</b>",
        parse_mode="HTML",
        reply_markup=groups_menu_keyboard(),
    )


async def my_groups_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_session() as session:
        from bot.models import User
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ Foydalanuvchi topilmadi.")
            return

        if is_admin(user_id):
            groups = session.query(Group).filter_by(is_active=True).all()
        else:
            tg_ids = session.query(TeacherGroup.group_id).filter_by(teacher_id=user.id).all()
            group_ids = [g[0] for g in tg_ids]
            groups = session.query(Group).filter(Group.id.in_(group_ids), Group.is_active == True).all()

        if not groups:
            await update.message.reply_text("📚 Sizga biriktirilgan guruhlar yo'q.")
            return

        lines = ["📚 <b>Mening guruhlarim</b>\n"]
        for g in groups:
            count = session.query(Student).filter_by(group_id=g.id, is_active=True).count()
            lines.append(f"• <b>{g.name}</b> ({count} o'quvchi)")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def create_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text(
        "➕ <b>Yangi guruh yaratish</b>\n\nGuruh nomini kiriting:",
        parse_mode="HTML",
        reply_markup=back_keyboard(),
    )
    return G_NAME


async def receive_group_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel_groups(update, context)
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        "🕐 Dars jadvalini kiriting:\n(Masalan: Dush-Chor-Jum 14:00)\n"
        "Yoki o'tkazib yuborish uchun — belgilanmagan"
    )
    return G_SCHEDULE


async def receive_group_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel_groups(update, context)

    data = context.user_data
    with get_session() as session:
        schedule = update.message.text.strip()
        if schedule.lower() in ("belgilanmagan", "-", "yo'q"):
            schedule = None
        group = Group(
            name=data["name"],
            course="",
            schedule=schedule,
        )
        session.add(group)

    await update.message.reply_text(
        f"✅ <b>{data['name']}</b> guruhi yaratildi!",
        parse_mode="HTML",
        reply_markup=groups_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_session() as session:
        groups = session.query(Group).filter_by(is_active=True).all()
        if not groups:
            await update.message.reply_text("📚 Guruhlar mavjud emas.")
            return

        lines = ["📚 <b>Barcha guruhlar</b>\n"]
        for g in groups:
            count = session.query(Student).filter_by(group_id=g.id, is_active=True).count()
            lines.append(
                f"• <b>{g.name}</b>\n"
                f"  🕐 {g.schedule or 'Belgilanmagan'}\n"
                f"  👥 {count} o'quvchi\n"
            )
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def group_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    with get_session() as session:
        groups = session.query(Group).filter_by(is_active=True).all()
        if not groups:
            await update.message.reply_text("❌ Guruhlar yo'q.")
            return

        from bot.keyboards.menus import groups_keyboard
        await update.message.reply_text(
            "Guruhni tanlang:",
            reply_markup=groups_keyboard(groups, "view_"),
        )


async def view_group_students_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group_id = int(query.data.split("_")[-1])

    with get_session() as session:
        group = session.query(Group).filter_by(id=group_id).first()
        students = (
            session.query(Student)
            .filter_by(group_id=group_id, is_active=True)
            .order_by(Student.full_name)
            .all()
        )
        if not students:
            await query.edit_message_text(f"👥 <b>{group.name}</b> guruhida o'quvchilar yo'q.", parse_mode="HTML")
            return

        lines = [f"👥 <b>{group.name}</b> — O'quvchilar\n"]
        for i, s in enumerate(students, 1):
            lines.append(f"{i}. {s.full_name} ({s.phone})")
        await query.edit_message_text("\n".join(lines), parse_mode="HTML")


async def edit_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    with get_session() as session:
        groups = session.query(Group).filter_by(is_active=True).all()
        if not groups:
            await update.message.reply_text("❌ Guruhlar yo'q.")
            return
        from bot.keyboards.menus import groups_keyboard
        await update.message.reply_text(
            "Tahrirlash uchun guruhni tanlang:",
            reply_markup=groups_keyboard(groups, "edit_"),
        )


async def edit_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group_id = int(query.data.split("_")[-1])
    context.user_data["edit_group_id"] = group_id

    await query.message.reply_text(
        "Yangi guruh nomini kiriting:",
        reply_markup=back_keyboard(),
    )
    return G_EDIT


async def receive_edit_group_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel_groups(update, context)

    group_id = context.user_data.get("edit_group_id")
    with get_session() as session:
        group = session.query(Group).filter_by(id=group_id).first()
        if group:
            group.name = update.message.text.strip()
            name = group.name
        else:
            await update.message.reply_text("❌ Guruh topilmadi.")
            return ConversationHandler.END

    await update.message.reply_text(
        f"✅ <b>{name}</b> guruhi yangilandi!",
        parse_mode="HTML",
        reply_markup=groups_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def delete_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    with get_session() as session:
        groups = session.query(Group).filter_by(is_active=True).all()
        if not groups:
            await update.message.reply_text("❌ Guruhlar yo'q.")
            return
        from bot.keyboards.menus import groups_keyboard
        await update.message.reply_text(
            "O'chirmoqchi bo'lgan guruhni tanlang:",
            reply_markup=groups_keyboard(groups, "del_"),
        )


async def delete_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return

    group_id = int(query.data.split("_")[-1])
    with get_session() as session:
        group = session.query(Group).filter_by(id=group_id).first()
        if group:
            group.is_active = False
            await query.edit_message_text(f"✅ {group.name} guruhi o'chirildi.")
        else:
            await query.edit_message_text("❌ Guruh topilmadi.")


async def _cancel_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = get_user_by_telegram_id(update.effective_user.id)
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=groups_menu_keyboard())
    return ConversationHandler.END


def register_group_handlers(application):
    create_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Guruh yaratish$"), create_group_start)],
        states={
            G_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_group_name)],
            G_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_group_schedule)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Orqaga$"), _cancel_groups)],
    )

    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_group_callback, pattern=r"^edit_group_\d+$")],
        states={
            G_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_group_name)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Orqaga$"), _cancel_groups)],
    )

    application.add_handler(create_conv)
    application.add_handler(edit_conv)
    application.add_handler(MessageHandler(filters.Regex("^📚 Guruhlar$"), groups_menu_handler))
    application.add_handler(MessageHandler(filters.Regex("^📚 Mening guruhlarim$"), my_groups_handler))
    application.add_handler(MessageHandler(filters.Regex("^📋 Barcha guruhlar$"), list_groups))
    application.add_handler(MessageHandler(filters.Regex("^👥 Guruh o'quvchilari$"), group_students))
    application.add_handler(MessageHandler(filters.Regex("^✏️ Guruhni tahrirlash$"), edit_group_start))
    application.add_handler(MessageHandler(filters.Regex("^🗑 Guruhni o'chirish$"), delete_group_start))
    application.add_handler(CallbackQueryHandler(view_group_students_callback, pattern=r"^view_group_\d+$"))
    application.add_handler(CallbackQueryHandler(delete_group_callback, pattern=r"^del_group_\d+$"))
