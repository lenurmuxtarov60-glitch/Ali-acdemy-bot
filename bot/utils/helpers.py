from datetime import date, datetime, timedelta

from bot.config import ROLE_SUPER_ADMIN, ROLE_TEACHER
from bot.models import User, Student, get_session


def format_date(d: date) -> str:
    return d.strftime("%d.%m.%Y")


def format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def parse_phone(phone: str) -> str:
    return phone.strip().replace(" ", "").replace("-", "")


def normalize_name(name: str) -> str:
    """Ism qidiruv uchun tozalash: sh. Ozodbek → Ozodbek"""
    import re
    cleaned = name.strip()
    cleaned = re.sub(r"^(sh\.?|s\.?|sh\s+)\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def get_user_by_telegram_id(telegram_id: int) -> User | None:
    with get_session() as session:
        return session.query(User).filter_by(telegram_id=telegram_id, is_active=True).first()


def is_registered_parent(telegram_id: int) -> bool:
    with get_session() as session:
        return (
            session.query(Student)
            .filter_by(parent_telegram_id=telegram_id, is_active=True)
            .first()
            is not None
        )


def get_user_role(telegram_id: int) -> str | None:
    user = get_user_by_telegram_id(telegram_id)
    if user:
        return user.role
    return None


def is_admin(telegram_id: int) -> bool:
    return get_user_role(telegram_id) == ROLE_SUPER_ADMIN


def is_teacher(telegram_id: int) -> bool:
    role = get_user_role(telegram_id)
    return role in (ROLE_SUPER_ADMIN, ROLE_TEACHER)


def is_parent(telegram_id: int) -> bool:
    return is_registered_parent(telegram_id)


def date_range(period: str) -> tuple[date, date]:
    today = date.today()
    if period == "daily":
        return today, today
    if period == "weekly":
        start = today - timedelta(days=today.weekday())
        return start, today
    if period == "monthly":
        start = today.replace(day=1)
        return start, today
    return today, today
