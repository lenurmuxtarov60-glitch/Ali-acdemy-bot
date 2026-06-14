import logging

from telegram.ext import Application

from bot.config import ADMIN_BOT_TOKEN
from bot.handlers import (
    register_admin_handlers,
    register_attendance_handlers,
    register_group_handlers,
    register_report_handlers,
    register_settings_handlers,
    register_student_handlers,
)
from bot.handlers.start import register_admin_start_handlers
from bot.handlers.parent_requests import register_parent_request_handlers

logger = logging.getLogger(__name__)


def create_admin_application() -> Application:
    if not ADMIN_BOT_TOKEN:
        raise ValueError("ADMIN_BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan!")

    application = Application.builder().token(ADMIN_BOT_TOKEN).build()

    register_admin_start_handlers(application)
    register_student_handlers(application)
    register_group_handlers(application)
    register_attendance_handlers(application)
    register_report_handlers(application)
    register_settings_handlers(application)
    register_admin_handlers(application)
    register_parent_request_handlers(application)

    logger.info("Admin bot tayyor!")
    return application
