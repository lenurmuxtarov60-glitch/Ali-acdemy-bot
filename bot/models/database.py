from datetime import datetime, date

from contextlib import contextmanager



from sqlalchemy import (

    create_engine,

    Column,

    Integer,

    String,

    DateTime,

    Date,

    ForeignKey,

    UniqueConstraint,

    Boolean,

    Text,

)

from sqlalchemy.orm import declarative_base, sessionmaker, relationship



from bot.config import DATABASE_URL, SUPER_ADMIN_ID, ROLE_SUPER_ADMIN



Base = declarative_base()



engine = create_engine(

    DATABASE_URL,

    echo=False,

    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},

)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)





class User(Base):

    __tablename__ = "users"



    id = Column(Integer, primary_key=True)

    telegram_id = Column(Integer, unique=True, nullable=False, index=True)

    full_name = Column(String(255), nullable=False)

    phone = Column(String(20), nullable=True)

    role = Column(String(20), nullable=False, default="parent")

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)



    teacher_groups = relationship("TeacherGroup", back_populates="teacher", cascade="all, delete-orphan")





class Group(Base):

    __tablename__ = "groups"



    id = Column(Integer, primary_key=True)

    name = Column(String(100), nullable=False)

    course = Column(String(100), nullable=False)

    schedule = Column(String(255), nullable=True)

    max_students = Column(Integer, default=20)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)



    students = relationship("Student", back_populates="group")

    teacher_groups = relationship("TeacherGroup", back_populates="group", cascade="all, delete-orphan")





class TeacherGroup(Base):

    __tablename__ = "teacher_groups"



    id = Column(Integer, primary_key=True)

    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)



    __table_args__ = (UniqueConstraint("teacher_id", "group_id", name="uq_teacher_group"),)



    teacher = relationship("User", back_populates="teacher_groups")

    group = relationship("Group", back_populates="teacher_groups")





class Student(Base):

    __tablename__ = "students"



    id = Column(Integer, primary_key=True)

    full_name = Column(String(255), nullable=False)

    phone = Column(String(20), nullable=True)

    parent_name = Column(String(255), nullable=True)

    parent_phone = Column(String(20), nullable=True)

    parent_telegram_id = Column(Integer, nullable=True, index=True)

    course = Column(String(100), nullable=True)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    registered_at = Column(Date, default=date.today)

    is_active = Column(Boolean, default=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)



    group = relationship("Group", back_populates="students")

    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")

    parent_requests = relationship("ParentRequest", back_populates="student", cascade="all, delete-orphan")





class ParentRequest(Base):

    """Ota-ona botdan kelgan so'rov — admin tasdiqlashi kerak."""

    __tablename__ = "parent_requests"



    id = Column(Integer, primary_key=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    parent_telegram_id = Column(Integer, nullable=False, index=True)

    parent_name = Column(String(255), nullable=True)

    date = Column(Date, nullable=False, default=date.today)

    status = Column(String(20), nullable=False, default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)



    student = relationship("Student", back_populates="parent_requests")





class Attendance(Base):

    __tablename__ = "attendances"



    id = Column(Integer, primary_key=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    date = Column(Date, nullable=False, default=date.today)

    status = Column(String(20), nullable=False)

    participation = Column(String(20), nullable=True)

    marked_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    notified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)



    __table_args__ = (UniqueConstraint("student_id", "date", name="uq_student_date"),)



    student = relationship("Student", back_populates="attendances")





def _migrate_schema():
    import sqlalchemy as sa

    with engine.connect() as conn:
        if not DATABASE_URL.startswith("sqlite"):
            return

        att_cols = {row[1] for row in conn.execute(sa.text("PRAGMA table_info(attendances)"))}
        if "participation" not in att_cols:
            conn.execute(sa.text("ALTER TABLE attendances ADD COLUMN participation VARCHAR(20)"))

        tables = {t[0] for t in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))}
        if "parent_requests" not in tables:
            Base.metadata.tables["parent_requests"].create(bind=conn)

        st_info = list(conn.execute(sa.text("PRAGMA table_info(students)")))
        if st_info:
            notnull = {row[1]: row[3] for row in st_info}
            if notnull.get("phone") == 1 or notnull.get("parent_name") == 1:
                conn.execute(sa.text("""
                    CREATE TABLE students_new (
                        id INTEGER PRIMARY KEY,
                        full_name VARCHAR(255) NOT NULL,
                        phone VARCHAR(20),
                        parent_name VARCHAR(255),
                        parent_phone VARCHAR(20),
                        parent_telegram_id INTEGER,
                        course VARCHAR(100),
                        group_id INTEGER,
                        registered_at DATE,
                        is_active BOOLEAN DEFAULT 1,
                        notes TEXT,
                        created_at DATETIME,
                        FOREIGN KEY(group_id) REFERENCES groups(id)
                    )
                """))
                conn.execute(sa.text("""
                    INSERT INTO students_new (
                        id, full_name, phone, parent_name, parent_phone,
                        parent_telegram_id, course, group_id, registered_at,
                        is_active, notes, created_at
                    )
                    SELECT
                        id, full_name, phone, parent_name, parent_phone,
                        parent_telegram_id, course, group_id, registered_at,
                        is_active, notes, created_at
                    FROM students
                """))
                conn.execute(sa.text("DROP TABLE students"))
                conn.execute(sa.text("ALTER TABLE students_new RENAME TO students"))

        conn.commit()





def init_db():

    Base.metadata.create_all(bind=engine)

    _migrate_schema()

    _seed_super_admin()
    _seed_default_groups()





def _seed_super_admin():

    if not SUPER_ADMIN_ID:

        return

    with get_session() as session:

        existing = session.query(User).filter_by(telegram_id=SUPER_ADMIN_ID).first()

        if not existing:

            session.add(

                User(

                    telegram_id=SUPER_ADMIN_ID,

                    full_name="Super Admin",

                    role=ROLE_SUPER_ADMIN,

                )

            )





def _seed_default_groups():
    with get_session() as session:
        default_courses = ["Frontend", "Kompyuter savodxonligi"]
        existing = {g.name for g in session.query(Group).filter_by(is_active=True).all()}
        for course in default_courses:
            if course not in existing:
                session.add(
                    Group(
                        name=course,
                        course=course,
                        schedule="",
                    )
                )


@contextmanager

def get_session():

    session = SessionLocal()

    try:

        yield session

        session.commit()

    except Exception:

        session.rollback()

        raise

    finally:

        session.close()


