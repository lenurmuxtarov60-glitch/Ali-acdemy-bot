from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from bot.config import ROLE_TEACHER, ROLE_SUPER_ADMIN
from bot.keyboards.menus import (
    teacher_menu_keyboard,
    back_keyboard,
    groups_keyboard,
    teachers_keyboard,
    main_menu_keyboard,
)
from bot.models import User, TeacherGroup, Group, get_session
from bot.utils.helpers import get_user_by_telegram_id, is_admin

(T_NAME, T_PHONE, T_TG_ID, T_ASSIGN, A_NAME, A_TG_ID) = range(6)


async def teachers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Faqat adminlar uchun.")
        return
    await update.message.reply_text(
        "👨‍🏫 <b>O'qituvchilar boshqaruvi</b>",
        parse_mode="HTML",
        reply_markup=teacher_menu_keyboard(),
    )


async def add_teacher_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text(
        "➕ <b>Yangi o'qituvchi</b>\n\nF.I.O kiriting:",
        parse_mode="HTML",
        reply_markup=back_keyboard(),
    )
    return T_NAME


async def receive_teacher_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel_admin(update, context)
    context.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text("📱 Telefon raqamini kiriting:")
    return T_PHONE


async def receive_teacher_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel_admin(update, context)
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text("🆔 Telegram ID sini kiriting:")
    return T_TG_ID


async def receive_teacher_tg_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel_admin(update, context)

    tg_id = update.message.text.strip()
    if not tg_id.isdigit():
        await update.message.reply_text("❌ Noto'g'ri ID. Qayta kiriting:")
        return T_TG_ID

    data = context.user_data
    with get_session() as session:
        existing = session.query(User).filter_by(telegram_id=int(tg_id)).first()
        if existing:
            existing.role = ROLE_TEACHER
            existing.full_name = data["full_name"]
            existing.phone = data["phone"]
            name = existing.full_name
        else:
            teacher = User(
                telegram_id=int(tg_id),
                full_name=data["full_name"],
                phone=data["phone"],
                role=ROLE_TEACHER,
            )
            session.add(teacher)
            name = data["full_name"]

    await update.message.reply_text(
        f"✅ <b>{name}</b> o'qituvchi sifatida qo'shildi!",
        parse_mode="HTML",
        reply_markup=teacher_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def list_teachers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    with get_session() as session:
        teachers = session.query(User).filter_by(role=ROLE_TEACHER, is_active=True).all()
        if not teachers:
            await update.message.reply_text("📋 O'qituvchilar ro'yxati bo'sh.")
            return

        lines = ["👨‍🏫 <b>O'qituvchilar ro'yxati</b>\n"]
        for i, t in enumerate(teachers, 1):
            group_count = session.query(TeacherGroup).filter_by(teacher_id=t.id).count()
            lines.append(
                f"{i}. <b>{t.full_name}</b>\n"
                f"   🆔 {t.telegram_id} | 📱 {t.phone or '-'}\n"
                f"   📚 {group_count} guruh\n"
            )
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def assign_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    with get_session() as session:
        teachers = session.query(User).filter_by(role=ROLE_TEACHER, is_active=True).all()
        if not teachers:
            await update.message.reply_text("❌ O'qituvchilar yo'q.")
            return

    await update.message.reply_text(
        "O'qituvchini tanlang:",
        reply_markup=teachers_keyboard(teachers),
    )


async def assign_teacher_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("teacher_"):
        return

    teacher_id = int(query.data.split("_")[-1])
    context.user_data["assign_teacher_id"] = teacher_id

    with get_session() as session:
        groups = session.query(Group).filter_by(is_active=True).all()

    if not groups:
        await query.edit_message_text("❌ Guruhlar yo'q.")
        return

    await query.edit_message_text("Guruhni tanlang:")
    await query.message.reply_text(
        "Guruhni tanlang:",
        reply_markup=groups_keyboard(groups, "assign_"),
    )


async def assign_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("_")[-1])
    teacher_id = context.user_data.get("assign_teacher_id")

    if not teacher_id:
        await query.edit_message_text("❌ Xatolik. Qayta urinib ko'ring.")
        return

    with get_session() as session:
        existing = session.query(TeacherGroup).filter_by(
            teacher_id=teacher_id, group_id=group_id
        ).first()
        if existing:
            await query.edit_message_text("ℹ️ Bu guruh allaqachon biriktirilgan.")
            return

        teacher = session.query(User).filter_by(id=teacher_id).first()
        group = session.query(Group).filter_by(id=group_id).first()
        session.add(TeacherGroup(teacher_id=teacher_id, group_id=group_id))

    await query.edit_message_text(
        f"✅ <b>{teacher.full_name}</b> → <b>{group.name}</b> guruhi biriktirildi!",
        parse_mode="HTML",
    )


async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text(
        "🔐 <b>Yangi admin qo'shish</b>\n\nAdmin ism-familiyasini kiriting:",
        parse_mode="HTML",
        reply_markup=back_keyboard(),
    )
    return A_NAME


async def receive_admin_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel_admin(update, context)
    context.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text("🆔 Telegram ID sini kiriting:")
    return A_TG_ID


async def receive_admin_tg_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Orqaga":
        return await _cancel_admin(update, context)
    tg_id = update.message.text.strip()
    if not tg_id.isdigit():
        await update.message.reply_text("❌ Noto'g'ri ID. Qayta kiriting:")
        return A_TG_ID
    data = context.user_data
    with get_session() as session:
        existing = session.query(User).filter_by(telegram_id=int(tg_id)).first()
        if existing:
            existing.role = ROLE_SUPER_ADMIN
            existing.full_name = data["full_name"]
            name = existing.full_name
        else:
            admin = User(
                telegram_id=int(tg_id),
                full_name=data["full_name"],
                role=ROLE_SUPER_ADMIN,
            )
            session.add(admin)
            name = data["full_name"]
    await update.message.reply_text(
        f"✅ <b>{name}</b> admin sifatida qo'shildi!\n"
        f"🆔 ID: <code>{tg_id}</code>\n\n"
        f"Endi u /start bosib admin panelga kira oladi.",
        parse_mode="HTML",
        reply_markup=teacher_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    with get_session() as session:
        admins = session.query(User).filter_by(role=ROLE_SUPER_ADMIN, is_active=True).all()
        if not admins:
            await update.message.reply_text("📋 Adminlar ro'yxati bo'sh.")
            return
        lines = ["🔐 <b>Adminlar ro'yxati</b>\n"]
        for i, a in enumerate(admins, 1):
            lines.append(f"{i}. <b>{a.full_name}</b>\n   🆔 {a.telegram_id}\n")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def _cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=teacher_menu_keyboard())
    return ConversationHandler.END


def register_admin_handlers(application):
    add_admin_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔐 Admin qo'shish$"), add_admin_start)],
        states={
            A_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_name)],
            A_TG_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_tg_id)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Orqaga$"), _cancel_admin)],
    )
    application.add_handler(add_admin_conv)
    application.add_handler(MessageHandler(filters.Regex("^📋 Adminlar ro'yxati$"), list_admins))
    add_teacher_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ O'qituvchi qo'shish$"), add_teacher_start)],
        states={
            T_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_teacher_name)],
            T_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_teacher_phone)],
            T_TG_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_teacher_tg_id)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Orqaga$"), _cancel_admin)],
    )

    application.add_handler(add_teacher_conv)
    application.add_handler(MessageHandler(filters.Regex("^👨‍🏫 O'qituvchilar$"), teachers_menu))
    application.add_handler(MessageHandler(filters.Regex("^📋 O'qituvchilar ro'yxati$"), list_teachers))
    application.add_handler(MessageHandler(filters.Regex("^🔗 Guruh biriktirish$"), assign_group_start))
    application.add_handler(CallbackQueryHandler(assign_teacher_callback, pattern=r"^teacher_\d+$"))
    application.add_handler(CallbackQueryHandler(assign_group_callback, pattern=r"^assign_group_\d+$"))
