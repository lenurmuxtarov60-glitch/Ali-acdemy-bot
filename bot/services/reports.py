from datetime import date

from bot.models import Student, Group, Attendance, get_session
from bot.services.attendance import AttendanceService
from bot.utils.helpers import date_range


class ReportService:

    @staticmethod
    def daily_report(group_id: int | None = None) -> str:
        start, end = date_range("daily")
        return ReportService._build_report("Kunlik davomat", start, end, group_id)

    @staticmethod
    def weekly_report(group_id: int | None = None) -> str:
        start, end = date_range("weekly")
        return ReportService._build_report("Haftalik davomat", start, end, group_id)

    @staticmethod
    def monthly_report(group_id: int | None = None) -> str:
        start, end = date_range("monthly")
        return ReportService._build_report("Oylik davomat", start, end, group_id)

    @staticmethod
    def attendance_percentage_report() -> str:
        start, end = date_range("monthly")
        items = AttendanceService.get_all_students_report(start, end)
        lines = [
            "📈 <b>Davomat foizi (Oylik)</b>",
            f"📅 {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}",
            "",
        ]
        if not items:
            lines.append("📋 O'quvchilar yo'q.")
            return "\n".join(lines)

        for item in items:
            s = item["student"]
            pct = item["percentage"]
            icon = "🟢" if pct >= 80 else "🟡" if pct >= 50 else "🔴"
            lines.append(f"{icon} <b>{s.full_name}</b>: {pct:.0f}%")
        return "\n".join(lines)

    @staticmethod
    def _build_report(title: str, start: date, end: date, group_id: int | None) -> str:
        lines = [f"📊 <b>{title}</b>", f"📅 {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}", ""]

        if group_id:
            with get_session() as session:
                group = session.query(Group).filter_by(id=group_id).first()
            if group:
                report = AttendanceService.get_group_attendance_report(group.id, start, end)
                lines.extend(ReportService._format_student_rows(report))
                return "\n".join(lines)

        report = AttendanceService.get_all_students_report(start, end)
        if not report:
            lines.append("📋 O'quvchilar yo'q.")
            return "\n".join(lines)

        lines.extend(ReportService._format_student_rows(report))
        return "\n".join(lines)

    @staticmethod
    def _format_student_rows(report: list) -> list[str]:
        rows = []
        for item in report:
            s = item["student"]
            pct = item.get("percentage", 0)
            icon = "🟢" if pct >= 80 else "🟡" if pct >= 50 else "🔴"
            if item["total"] == 0:
                rows.append(f"⚪ {s.full_name}: belgilanmagan")
            else:
                rows.append(
                    f"{icon} {s.full_name}: "
                    f"✅{item['present']} 🔴{item['absent']} ({pct:.0f}%)"
                )
        return rows

    @staticmethod
    def student_stats(student_id: int) -> str:
        start, end = date_range("monthly")
        with get_session() as session:
            student = session.query(Student).filter_by(id=student_id).first()
            if not student:
                return "❌ O'quvchi topilmadi."

            stats = AttendanceService.calculate_percentage(student_id, start, end)
            group = session.query(Group).filter_by(id=student.group_id).first()

            return (
                f"👨‍🎓 <b>{student.full_name}</b>\n"
                f"📚 Guruh: {group.name if group else '—'}\n"
                f"📅 Davr: {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}\n\n"
                f"📊 Jami darslar: {stats['total']}\n"
                f"🟢 Keldi: {stats['present']}\n"
                f"🔴 Kelmadi: {stats['absent']}\n"
                f"📈 Davomat foizi: <b>{stats['percentage']:.1f}%</b>"
            )
