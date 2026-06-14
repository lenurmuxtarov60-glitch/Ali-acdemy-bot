import logging

from telegram.ext import Application

from bot.config import PARENT_BOT_TOKEN
from bot.handlers.parent import register_parent_handlers
from bot.handlers.start import register_parent_start_handlers

logger = logging.getLogger(__name__)


def create_parent_application() -> Application:
    if not PARENT_BOT_TOKEN:
        raise ValueError("PARENT_BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan!")

    application = Application.builder().token(PARENT_BOT_TOKEN).build()

    register_parent_start_handlers(application)
    register_parent_handlers(application)

    logger.info("Ota-ona bot tayyor!")
    return application
