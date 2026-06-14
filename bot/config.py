import os
from dotenv import load_dotenv

load_dotenv()

# Admin panel boti (super admin / o'qituvchilar)
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN") or os.getenv("BOT_TOKEN", "")
# Ota-onalar uchun alohida bot
PARENT_BOT_TOKEN = os.getenv("PARENT_BOT_TOKEN", "")
# Ota-onalarga ko'rsatish uchun (@username, ixtiyoriy)
PARENT_BOT_USERNAME = os.getenv("PARENT_BOT_USERNAME", "").lstrip("@")

SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///davomat.db")
MAIN_TEACHER = os.getenv("MAIN_TEACHER", "Nodirbek")
CENTER_NAME = os.getenv("CENTER_NAME", "ALI ACADEMY")

ATTENDANCE_STATUS = {
    "present": {"emoji": "🟢", "label": "Keldi", "key": "present"},
    "absent": {"emoji": "🔴", "label": "Kelmadi", "key": "absent"},
}

PARTICIPATION_LEVELS = {
    "good": {"emoji": "⭐", "label": "Yaxshi"},
    "average": {"emoji": "➖", "label": "O'rtacha"},
    "bad": {"emoji": "👎", "label": "Yomon"},
}

def build_parent_message(status: str, student_name: str, participation: str | None = None) -> str:
    if status == "absent":
        return f"Assalomu alaykum. Farzandingiz <b>{student_name}</b> bugungi darsga kelmadi."
    if status == "present" and participation:
        level = PARTICIPATION_LEVELS.get(participation, {})
        label = level.get("label", participation)
        return (
            f"Assalomu alaykum. Farzandingiz <b>{student_name}</b> bugungi darsga keldi. "
            f"Darsda <b>{label.lower()}</b> qatnashdi."
        )
    return f"Assalomu alaykum. Farzandingiz <b>{student_name}</b> bugungi darsga keldi."

ROLE_SUPER_ADMIN = "super_admin"
ROLE_TEACHER = "teacher"
ROLE_PARENT = "parent"
