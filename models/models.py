# models.py
from __future__ import annotations

from typing import Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    UniqueConstraint,
    CheckConstraint,
    ForeignKey,
    Enum as SAEnum,
    Integer,
    String,
    Boolean,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

db = SQLAlchemy()

# ---------------------------------
# Enums
# ---------------------------------
TermEnum = SAEnum("SPRING", "SUMMER", "FALL", name="term_enum")
ReqKind = SAEnum("ALL", "ANY_COUNT", "FILTER", name="req_kind")
CourseStatus = SAEnum("PLANNED", "IN_PROGRESS", "COMPLETED", name="course_status")


# ---------------------------------
# Core user + planning
# ---------------------------------
class User(db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)

    semesters: Mapped[list["StudentSemester"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="StudentSemester.order.asc()",
    )
    enrollments: Mapped[list["StudentCourse"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
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

    prereq_rules: Mapped[list["CoursePrereq"]] = relationship(
        "CoursePrereq",
        back_populates="course",
        cascade="all, delete-orphan",
        foreign_keys="CoursePrereq.course_id",
    )
    required_by: Mapped[list["CoursePrereq"]] = relationship(
        "CoursePrereq",
        primaryjoin="CourseCatalog.id == CoursePrereq.prereq_course_id",
        back_populates="prereq_course",
        viewonly=True,
        foreign_keys="CoursePrereq.prereq_course_id",
    )
    typical_offerings: Mapped[list["CourseTypicalOffering"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("code", name="uq_catalog_code"),)


class StudentSemester(db.Model):
    """A student’s planning bucket for a term."""
    __tablename__ = "student_semester"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(db.String(64), nullable=False)  # e.g., "Fall 2025"
    term: Mapped[str | None] = mapped_column(db.String(16))
    year: Mapped[int | None] = mapped_column(db.Integer)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)

    student: Mapped["User"] = relationship(back_populates="semesters")
    courses: Mapped[list["StudentCourse"]] = relationship(
        back_populates="semester",
        cascade="all, delete-orphan",
        order_by="StudentCourse.position.asc()",
    )

    __table_args__ = (
        UniqueConstraint("student_id", "name", name="uq_student_semester_name"),
    )


class StudentCourse(db.Model):
    """A catalog course planned or taken in a specific student semester."""
    __tablename__ = "student_course"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    semester_id: Mapped[int] = mapped_column(
        ForeignKey("student_semester.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("course_catalog.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    # snapshot fields
    credits: Mapped[float] = mapped_column(db.Float, nullable=False)
    section: Mapped[str | None] = mapped_column(db.String(16))
    position: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)

    # progress fields
    status: Mapped[str] = mapped_column(CourseStatus, nullable=False, default="PLANNED")
    grade: Mapped[str | None] = mapped_column(db.String(4))  # e.g., A, B+, C

    student: Mapped["User"] = relationship(back_populates="enrollments")
    semester: Mapped["StudentSemester"] = relationship(back_populates="courses")
    course: Mapped["CourseCatalog"] = relationship()

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_once"),
        UniqueConstraint("semester_id", "course_id", name="uq_semester_course_once"),
        UniqueConstraint("semester_id", "position", name="uq_semester_position"),
        CheckConstraint("credits >= 0", name="ck_studentcourse_credits_nonneg"),
    )


# ---------------------------------
# Catalog enrichments
# ---------------------------------
class CoursePrereq(db.Model):
    """Prerequisite rule rows using OR-of-groups across group_key and AND within a group."""
    __tablename__ = "course_prereq"
    id: Mapped[int] = mapped_column(primary_key=True)

    course_id: Mapped[int] = mapped_column(
        ForeignKey("course_catalog.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    prereq_course_id: Mapped[int] = mapped_column(
        ForeignKey("course_catalog.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    group_key: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    min_grade: Mapped[str | None] = mapped_column(db.String(4))  # e.g., "C"
    allow_concurrent: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)

    course: Mapped["CourseCatalog"] = relationship(
        "CourseCatalog",
        foreign_keys=[course_id],
        back_populates="prereq_rules",
    )
    prereq_course: Mapped["CourseCatalog"] = relationship(
        "CourseCatalog",
        foreign_keys=[prereq_course_id],
        back_populates="required_by",
    )

    __table_args__ = (
        UniqueConstraint("course_id", "prereq_course_id", "group_key",
                         name="uq_course_prereq_unique"),
        CheckConstraint("group_key >= 1", name="ck_prereq_groupkey_positive"),
    )


class CourseTypicalOffering(db.Model):
    """Terms this course is typically offered (not year-specific)."""
    __tablename__ = "course_typical_offering"
    id: Mapped[int] = mapped_column(primary_key=True)

    course_id: Mapped[int] = mapped_column(
        ForeignKey("course_catalog.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    term: Mapped[str] = mapped_column(TermEnum, nullable=False)

    course: Mapped["CourseCatalog"] = relationship(
        back_populates="typical_offerings",
    )

    __table_args__ = (
        UniqueConstraint("course_id", "term", name="uq_course_term_once"),
    )


# ---------------------------------
# Degree program requirements schema
# ---------------------------------
class DegreeProgram(db.Model):
    __tablename__ = "degree_program"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # e.g., "BS-CS-Core-2025"
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    total_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    groups: Mapped[list["ReqGroup"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
        order_by="ReqGroup.sort_order.asc()",
    )

    # audit helper
    @staticmethod
    def audit_program(session, student_id: int, program_code: str, include_planned: bool = True) -> dict[str, Any]:
        prog = session.query(DegreeProgram).filter_by(code=program_code).one()
        # pull student courses
        q = session.query(StudentCourse).filter_by(student_id=student_id)
        if not include_planned:
            q = q.filter(StudentCourse.status == "COMPLETED")
        scs = q.all()

        # grade comparisons
        grade_rank = {"A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8, "C+": 7, "C": 6, "C-": 5, "D": 3, "F": 0}
        def meets_min(sc: StudentCourse, min_grade: str | None) -> bool:
            if min_grade is None:
                return True
            if not sc.grade:
                return False
            return grade_rank.get(sc.grade.upper(), -1) >= grade_rank.get(min_grade.upper(), 99)

        by_course_id = {sc.course_id: sc for sc in scs}
        taken_ids = set(by_course_id.keys())
        used: set[int] = set()
        catalog = {c.id: c for c in session.query(CourseCatalog).all()}

        out = {
            "program": {"code": prog.code, "name": prog.name, "total_credits": prog.total_credits},
            "groups": [],
            "summary": {"credits_applied": 0, "courses_applied": 0},
        }

        for g in prog.groups:
            applied: list[int] = []
            missing: list[int] = []
            options: list[int] = []

            if g.kind == "ALL":
                listed = [rc.course_id for rc in g.courses]
                for cid in listed:
                    sc = by_course_id.get(cid)
                    if sc and meets_min(sc, "C") and (cid not in used or g.allow_double_count):
                        applied.append(cid)
                        if not g.allow_double_count:
                            used.add(cid)
                    else:
                        missing.append(cid)
                satisfied = len(missing) == 0
                need = len(listed)

            elif g.kind == "ANY_COUNT":
                listed = [rc.course_id for rc in g.courses]
                options = list(listed)
                eligible = []
                for cid in listed:
                    sc = by_course_id.get(cid)
                    if not sc:
                        continue
                    # find per-course min grade if specified
                    rc = next((x for x in g.courses if x.course_id == cid), None)
                    min_g = rc.min_grade if rc else None
                    if (cid not in used or g.allow_double_count) and meets_min(sc, min_g or "C"):
                        eligible.append(cid)
                applied = eligible[: g.min_count]
                for cid in applied:
                    if not g.allow_double_count:
                        used.add(cid)
                satisfied = len(applied) >= g.min_count
                need = g.min_count

            else:  # FILTER
                eligible = []
                for cid in taken_ids:
                    if cid in used and not g.allow_double_count:
                        continue
                    course = catalog[cid]
                    code = course.code.strip().upper()
                    parts = code.split()
                    if len(parts) != 2:
                        continue
                    dept, num_s = parts
                    try:
                        num = int(num_s)
                    except ValueError:
                        continue
                    if (g.dept_prefix and dept == g.dept_prefix) and (g.min_number is None or num >= g.min_number):
                        eligible.append(cid)
                applied = eligible[: g.min_count]
                for cid in applied:
                    if not g.allow_double_count:
                        used.add(cid)
                satisfied = len(applied) >= g.min_count
                need = g.min_count

            credits = sum(catalog[cid].credits for cid in applied)
            out["groups"].append({
                "group_id": g.id,
                "title": g.title,
                "kind": g.kind,
                "required_count": need,
                "applied_course_ids": applied,
                "missing_course_ids": missing,
                "options_course_ids": options,
                "satisfied": satisfied,
                "credits_applied": credits,
            })
            out["summary"]["credits_applied"] += credits
            out["summary"]["courses_applied"] += len(applied)

        return out


class ReqGroup(db.Model):
    __tablename__ = "req_group"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(
        ForeignKey("degree_program.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    kind: Mapped[str] = mapped_column(ReqKind, nullable=False)  # ALL | ANY_COUNT | FILTER
    min_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allow_double_count: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # FILTER params
    dept_prefix: Mapped[str | None] = mapped_column(String(16))
    min_number: Mapped[int | None] = mapped_column(Integer)

    program: Mapped["DegreeProgram"] = relationship(back_populates="groups")
    courses: Mapped[list["ReqGroupCourse"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("(kind <> 'FILTER') OR (dept_prefix IS NOT NULL OR min_number IS NOT NULL)", name="ck_filter_params"),
    )


class ReqGroupCourse(db.Model):
    __tablename__ = "req_group_course"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("req_group.id", ondelete="CASCADE"), index=True, nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("course_catalog.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    min_grade: Mapped[str | None] = mapped_column(String(4))  # optional override

    group: Mapped["ReqGroup"] = relationship(back_populates="courses")
    course: Mapped["CourseCatalog"] = relationship()

    __table_args__ = (UniqueConstraint("group_id", "course_id", name="uq_group_course_once"),)
