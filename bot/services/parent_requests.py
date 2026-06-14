from datetime import date

from sqlalchemy.orm import joinedload
from bot.models import ParentRequest, Student, User, Group, get_session
from bot.config import ROLE_SUPER_ADMIN, ROLE_TEACHER, SUPER_ADMIN_ID


class ParentRequestService:

    @staticmethod
    def find_student_by_name(query: str) -> list[Student]:
        from bot.utils.helpers import normalize_name
        cleaned = normalize_name(query)
        if len(cleaned) < 2:
            return []
        with get_session() as session:
            return (
                session.query(Student)
                .options(joinedload(Student.group))
                .filter(Student.full_name.ilike(f"%{cleaned}%"), Student.is_active == True)
                .order_by(Student.full_name)
                .limit(5)
                .all()
            )

    @staticmethod
    def get_pending_today(student_id: int, parent_telegram_id: int) -> ParentRequest | None:
        today = date.today()
        with get_session() as session:
            return (
                session.query(ParentRequest)
                .filter_by(
                    student_id=student_id,
                    parent_telegram_id=parent_telegram_id,
                    date=today,
                    status="pending",
                )
                .first()
            )

    @staticmethod
    def create_request(student_id: int, parent_telegram_id: int, parent_name: str) -> ParentRequest:
        today = date.today()
        with get_session() as session:
            existing = (
                session.query(ParentRequest)
                .filter_by(
                    student_id=student_id,
                    parent_telegram_id=parent_telegram_id,
                    date=today,
                    status="pending",
                )
                .first()
            )
            if existing:
                return existing

            req = ParentRequest(
                student_id=student_id,
                parent_telegram_id=parent_telegram_id,
                parent_name=parent_name,
                date=today,
                status="pending",
            )
            session.add(req)
            session.flush()
            session.refresh(req)
            return req

    @staticmethod
    def get_request(request_id: int) -> ParentRequest | None:
        with get_session() as session:
            return session.query(ParentRequest).filter_by(id=request_id).first()

    @staticmethod
    def complete_request(request_id: int, result: str):
        with get_session() as session:
            req = session.query(ParentRequest).filter_by(id=request_id).first()
            if req:
                req.status = result

    @staticmethod
    def get_parent_chat_for_student_today(student_id: int) -> int | None:
        today = date.today()
        with get_session() as session:
            req = (
                session.query(ParentRequest)
                .filter_by(student_id=student_id, date=today)
                .order_by(ParentRequest.created_at.desc())
                .first()
            )
            return req.parent_telegram_id if req else None

    @staticmethod
    def has_approved(student_id: int, parent_telegram_id: int) -> bool:
        with get_session() as session:
            return session.query(ParentRequest).filter_by(
                student_id=student_id,
                parent_telegram_id=parent_telegram_id,
                status="approved",
            ).first() is not None

    @staticmethod
    def get_staff_telegram_ids() -> list[int]:
        ids = set()
        if SUPER_ADMIN_ID:
            ids.add(SUPER_ADMIN_ID)
        with get_session() as session:
            staff = (
                session.query(User)
                .filter(User.role.in_([ROLE_SUPER_ADMIN, ROLE_TEACHER]), User.is_active == True)
                .all()
            )
            for u in staff:
                ids.add(u.telegram_id)
        return list(ids)
