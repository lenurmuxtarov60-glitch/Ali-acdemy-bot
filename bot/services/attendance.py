from datetime import date

from bot.models import Attendance, Student, Group, get_session


class AttendanceService:

    @staticmethod
    def mark_attendance(
        student_id: int,
        group_id: int | None,
        status: str,
        marked_by: int | None,
        participation: str | None = None,
    ) -> Attendance:
        today = date.today()
        with get_session() as session:
            existing = (
                session.query(Attendance)
                .filter_by(student_id=student_id, date=today)
                .first()
            )
            if existing:
                existing.status = status
                existing.participation = participation if status == "present" else None
                existing.marked_by = marked_by
                existing.notified = False
                session.flush()
                session.refresh(existing)
                return existing

            record = Attendance(
                student_id=student_id,
                group_id=group_id,
                date=today,
                status=status,
                participation=participation if status == "present" else None,
                marked_by=marked_by,
            )
            session.add(record)
            session.flush()
            session.refresh(record)
            return record

    @staticmethod
    def get_today_attendance(group_id: int) -> list:
        today = date.today()
        with get_session() as session:
            students = (
                session.query(Student)
                .filter_by(group_id=group_id, is_active=True)
                .order_by(Student.full_name)
                .all()
            )
            records = (
                session.query(Attendance)
                .filter_by(group_id=group_id, date=today)
                .all()
            )
            record_map = {r.student_id: r for r in records}
            result = []
            for s in students:
                rec = record_map.get(s.id)
                result.append({
                    "student": s,
                    "status": rec.status if rec else "unmarked",
                    "participation": rec.participation if rec else None,
                })
            return result

    @staticmethod
    def get_today_for_student(student_id: int) -> Attendance | None:
        today = date.today()
        with get_session() as session:
            return (
                session.query(Attendance)
                .filter_by(student_id=student_id, date=today)
                .first()
            )

    @staticmethod
    def get_student_attendance(student_id: int, start: date, end: date) -> list:
        with get_session() as session:
            return (
                session.query(Attendance)
                .filter(
                    Attendance.student_id == student_id,
                    Attendance.date >= start,
                    Attendance.date <= end,
                )
                .order_by(Attendance.date.desc())
                .all()
            )

    @staticmethod
    def calculate_percentage(student_id: int, start: date, end: date) -> dict:
        records = AttendanceService.get_student_attendance(student_id, start, end)
        total = len(records)
        if total == 0:
            return {"total": 0, "present": 0, "absent": 0, "late": 0, "percentage": 0.0}

        present = sum(1 for r in records if r.status == "present")
        absent = sum(1 for r in records if r.status == "absent")
        late = sum(1 for r in records if r.status == "late")
        attended = present + late
        percentage = (attended / total) * 100

        return {
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "percentage": percentage,
        }

    @staticmethod
    def get_all_students_report(start: date, end: date) -> list:
        with get_session() as session:
            students = (
                session.query(Student)
                .filter_by(is_active=True)
                .order_by(Student.full_name)
                .all()
            )
            report = []
            for student in students:
                stats = AttendanceService.calculate_percentage(student.id, start, end)
                report.append({
                    "student": student,
                    "total": stats["total"],
                    "present": stats["present"],
                    "absent": stats["absent"],
                    "percentage": stats["percentage"],
                })
            return report

    @staticmethod
    def get_group_attendance_report(group_id: int, start: date, end: date) -> list:
        with get_session() as session:
            students = (
                session.query(Student)
                .filter_by(group_id=group_id, is_active=True)
                .order_by(Student.full_name)
                .all()
            )
            records = (
                session.query(Attendance)
                .filter(
                    Attendance.group_id == group_id,
                    Attendance.date >= start,
                    Attendance.date <= end,
                )
                .all()
            )

            report = []
            for student in students:
                student_records = [r for r in records if r.student_id == student.id]
                total = len(student_records)
                present = sum(1 for r in student_records if r.status == "present")
                absent = sum(1 for r in student_records if r.status == "absent")
                late = sum(1 for r in student_records if r.status == "late")
                pct = ((present + late) / total * 100) if total > 0 else 0

                report.append({
                    "student": student,
                    "total": total,
                    "present": present,
                    "absent": absent,
                    "late": late,
                    "percentage": pct,
                })
            return report
