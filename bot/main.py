import asyncio
import logging
import signal
import sys

from bot.admin_app import create_admin_application
from bot.models import init_db
from bot.parent_app import create_parent_application

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def _run_application(application, name: str, stop_event: asyncio.Event):
    async with application:
        await application.start()
        await application.updater.start_polling(allowed_updates=["message", "callback_query"])
        logger.info("%s ishga tushdi", name)
        await stop_event.wait()
        await application.updater.stop()
        await application.stop()


async def async_main():
    init_db()
    stop_event = asyncio.Event()

    def _request_stop(*_):
        logger.info("To'xtatish signali qabul qilindi...")
        stop_event.set()

    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, _request_stop)
    else:
        signal.signal(signal.SIGINT, _request_stop)

    admin_app = create_admin_application()
    parent_app = create_parent_application()

    await asyncio.gather(
        _run_application(admin_app, "Admin bot", stop_event),
        _run_application(parent_app, "Ota-ona bot", stop_event),
    )


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    main()
