from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)

    semesters: Mapped[list["StudentSemester"]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="StudentSemester.order.asc()"
    )
    enrollments: Mapped[list["StudentCourse"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )

class CourseCatalog(db.Model):
    """Master list of courses."""
    __tablename__ = "course_catalog"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(db.String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(db.Text)
    credits: Mapped[float] = mapped_column(db.Float, nullable=False, default=3.0)
    department: Mapped[str | None] = mapped_column(db.String(64))
    level: Mapped[str | None] = mapped_column(db.String(16))

    __table_args__ = (UniqueConstraint("code", name="uq_catalog_code"),)

class StudentSemester(db.Model):
    """A student’s planning bucket for a term."""
    __tablename__ = "student_semester"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(64), nullable=False)  # e.g., "Fall 2025"
    term: Mapped[str | None] = mapped_column(db.String(16))
    year: Mapped[int | None] = mapped_column(db.Integer)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)

    student: Mapped["User"] = relationship(back_populates="semesters")
    courses: Mapped[list["StudentCourse"]] = relationship(
        back_populates="semester", cascade="all, delete-orphan", order_by="StudentCourse.position.asc()"
    )

    __table_args__ = (
        UniqueConstraint("student_id", "name", name="uq_student_semester_name"),  # optional nicety
    )

class StudentCourse(db.Model):
    """Association: a catalog course planned in a specific student semester."""
    __tablename__ = "student_course"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("student_semester.id", ondelete="CASCADE"), index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("course_catalog.id", ondelete="RESTRICT"), index=True, nullable=False)

    # snapshot fields (avoid surprises if catalog changes)
    credits: Mapped[float] = mapped_column(db.Float, nullable=False)
    section: Mapped[str | None] = mapped_column(db.String(16))
    position: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)

    student: Mapped["User"] = relationship(back_populates="enrollments")
    semester: Mapped["StudentSemester"] = relationship(back_populates="courses")
    course: Mapped["CourseCatalog"] = relationship()

    __table_args__ = (
        # Prevent the same catalog course being used twice by the same student across ANY semester
        UniqueConstraint("student_id", "course_id", name="uq_student_course_once"),
        # Prevent duplicates inside a semester
        UniqueConstraint("semester_id", "course_id", name="uq_semester_course_once"),
        # Keep position unique per semester for clean ordering (optional)
        UniqueConstraint("semester_id", "position", name="uq_semester_position"),
        CheckConstraint("credits >= 0", name="ck_studentcourse_credits_nonneg"),
    )
