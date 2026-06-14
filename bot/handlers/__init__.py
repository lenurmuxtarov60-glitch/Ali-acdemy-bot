from bot.handlers.start import register_admin_start_handlers, register_parent_start_handlers
from bot.handlers.students import register_student_handlers
from bot.handlers.groups import register_group_handlers
from bot.handlers.attendance import register_attendance_handlers
from bot.handlers.reports import register_report_handlers
from bot.handlers.settings import register_settings_handlers
from bot.handlers.admin import register_admin_handlers
from bot.handlers.parent import register_parent_handlers

__all__ = [
    "register_admin_start_handlers",
    "register_parent_start_handlers",
    "register_student_handlers",
    "register_group_handlers",
    "register_attendance_handlers",
    "register_report_handlers",
    "register_settings_handlers",
    "register_admin_handlers",
    "register_parent_handlers",
]

# Eski nom — admin start
register_start_handlers = register_admin_start_handlers
