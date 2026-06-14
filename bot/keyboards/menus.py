from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import ATTENDANCE_STATUS, PARTICIPATION_LEVELS


def main_menu_keyboard(role: str) -> ReplyKeyboardMarkup:
    if role == "super_admin":
        buttons = [
            ["🏠 Bosh sahifa", "👨‍🎓 O'quvchilar"],
            ["📚 Guruhlar", "✅ Davomat"],
            ["📊 Hisobotlar", "⚙️ Sozlamalar"],
            ["👨‍🏫 O'qituvchilar", "🔍 Qidiruv"],
        ]
    else:
        buttons = [
            ["🏠 Bosh sahifa", "📚 Mening guruhlarim"],
            ["✅ Davomat", "📊 Hisobotlar"],
        ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ["➕ O'quvchi qo'shish", "✏️ O'quvchini tahrirlash"],
        ["🗑 O'quvchini o'chirish", "🔍 O'quvchi qidirish"],
        ["📋 Barcha o'quvchilar"],
        ["🔙 Orqaga"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def teacher_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ["🔐 Admin qo'shish", "📋 Adminlar ro'yxati"],
        ["➕ O'qituvchi qo'shish", "📋 O'qituvchilar ro'yxati"],
        ["🔗 Guruh biriktirish"],
        ["🔙 Orqaga"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def parent_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ["📅 Bugungi davomat", "📊 Oylik statistika"],
        ["🔙 Orqaga"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def groups_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ["➕ Guruh yaratish", "✏️ Guruhni tahrirlash"],
        ["🗑 Guruhni o'chirish", "👥 Guruh o'quvchilari"],
        ["📋 Barcha guruhlar"],
        ["🔙 Orqaga"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def attendance_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ["✅ Davomat belgilash", "📋 Bugungi davomat"],
        ["🔙 Orqaga"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def reports_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ["📅 Kunlik davomat", "📆 Haftalik davomat"],
        ["🗓 Oylik davomat", "👨‍🎓 O'quvchi statistikasi"],
        ["📈 Davomat foizi"],
        ["📥 Excel eksport", "📄 PDF hisobot"],
        ["🔙 Orqaga"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def settings_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ["ℹ️ Markaz haqida", "👤 Mening profilim"],
        ["🔙 Orqaga"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([["🔙 Orqaga"]], resize_keyboard=True)


def groups_keyboard(groups: list, prefix: str = "") -> InlineKeyboardMarkup:
    buttons = []
    for g in groups:
        buttons.append([InlineKeyboardButton(g.name, callback_data=f"{prefix}group_{g.id}")])
    return InlineKeyboardMarkup(buttons)


def students_keyboard(students: list, prefix: str = "") -> InlineKeyboardMarkup:
    buttons = []
    for s in students:
        buttons.append([InlineKeyboardButton(s.full_name, callback_data=f"{prefix}student_{s.id}")])
    return InlineKeyboardMarkup(buttons)


def attendance_status_keyboard(student_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for key, info in ATTENDANCE_STATUS.items():
        buttons.append([
            InlineKeyboardButton(
                f"{info['emoji']} {info['label']}",
                callback_data=f"att_{student_id}_{key}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


def participation_keyboard(student_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for key, info in PARTICIPATION_LEVELS.items():
        buttons.append([
            InlineKeyboardButton(
                f"{info['emoji']} {info['label']}",
                callback_data=f"part_{student_id}_{key}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


def yes_no_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ha", callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton("❌ Yo'q", callback_data=f"cancel_{action}"),
        ]
    ])


def report_period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 Kunlik", callback_data="report_daily"),
            InlineKeyboardButton("📆 Haftalik", callback_data="report_weekly"),
        ],
        [InlineKeyboardButton("🗓 Oylik", callback_data="report_monthly")],
    ])


def settings_keyboard() -> ReplyKeyboardMarkup:
    return settings_menu_keyboard()


def teachers_keyboard(teachers: list) -> InlineKeyboardMarkup:
    buttons = []
    for t in teachers:
        buttons.append([InlineKeyboardButton(t.full_name, callback_data=f"teacher_{t.id}")])
    return InlineKeyboardMarkup(buttons)


def student_actions_keyboard(student_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_student_{student_id}"),
            InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_student_{student_id}"),
        ],
        [InlineKeyboardButton("📊 Statistika", callback_data=f"stats_student_{student_id}")],
    ])
