# routes/routes.py
from __future__ import annotations

from collections import defaultdict

from flask import Blueprint, render_template, jsonify, request, abort
from sqlalchemy import func, or_

from models.models import (
    db,
    User,
    CourseCatalog,
    StudentSemester,
    StudentCourse,
    DegreeProgram,
    CoursePrereq,
    CourseTypicalOffering,
)

bp = Blueprint("routes", __name__)

MAX_CLASSES_PER_SEM = 8
MAX_CREDITS_PER_SEM = 18.0


# ----------------- helpers -----------------
def get_current_user() -> User:
    uid = request.args.get("user_id", type=int)
    if uid:
        u = db.session.get(User, uid)
        if not u:
            abort(404, "user not found")
        return u
    u = User.query.filter_by(email="demo@example.com").first()
    if not u:
        u = User(email="demo@example.com", name="Demo User")
        db.session.add(u)
        db.session.flush()
    return u


def sc_to_dict(sc: StudentCourse):
    c = sc.course
    return {
        "id": sc.id,
        "code": c.code,
        "title": c.title,
        "description": c.description,
        "credits": sc.credits,
        "department": c.department,
        "level": c.level,
        "section": sc.section,
        "status": getattr(sc, "status", None),
        "grade": getattr(sc, "grade", None),
        "instructor": None,
        "location": None,
        "days_of_week": None,
        "start_time": None,
        "end_time": None,
        "capacity": None,
        "enrollment_count": None,
        "prerequisites": None,
        "semester_id": sc.semester_id,
        "position": sc.position,
        "catalog_id": c.id,
    }


def sem_to_dict(s: StudentSemester):
    return {
        "id": s.id,
        "name": s.name,
        "term": s.term,
        "year": s.year,
        "classes": [sc_to_dict(sc) for sc in s.courses],
    }


def semester_load_for_user(user_id: int):
    return (
        StudentSemester.query.filter_by(student_id=user_id)
        .order_by(
            StudentSemester.year.asc().nullsfirst(),
            StudentSemester.id.asc(),
        )
        .all()
    )


def semester_credits(semester_id: int, exclude_id: int | None = None) -> float:
    q = (
        db.session.query(func.coalesce(func.sum(StudentCourse.credits), 0.0))
        .filter(StudentCourse.semester_id == semester_id)
    )
    if exclude_id:
        q = q.filter(StudentCourse.id != exclude_id)
    return float(q.scalar() or 0.0)


def semester_count(semester_id: int) -> int:
    return int(
        db.session.query(func.count(StudentCourse.id))
        .filter(StudentCourse.semester_id == semester_id)
        .scalar()
        or 0
    )


def _grade_ok(grade: str | None, min_grade: str | None) -> bool:
    if not min_grade:
        return True
    if not grade:
        return False
    rank = {
        "A": 12, "A-": 11,
        "B+": 10, "B": 9, "B-": 8,
        "C+": 7, "C": 6, "C-": 5,
        "D": 3, "F": 0,
    }
    return rank.get(grade.upper(), -1) >= rank.get(min_grade.upper(), 99)


# ----------------- pages -----------------
@bp.route("/")
def planner():
    return render_template("planner.html")


# ----------------- semesters -----------------
@bp.get("/api/semesters")
def api_list_semesters():
    user = get_current_user()
    items = semester_load_for_user(user.id)
    return jsonify([sem_to_dict(s) for s in items])


@bp.post("/api/semesters")
def api_create_semester():
    user = get_current_user()
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    term = (data.get("term") or "").strip() or None
    year = data.get("year")
    if not name:
        abort(400, "name required")
    max_order = (
        db.session.query(func.coalesce(func.max(StudentSemester.order), -1))
        .filter_by(student_id=user.id)
        .scalar()
    )
    s = StudentSemester(
        student_id=user.id, name=name, term=term, year=year, order=int(max_order) + 1
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(sem_to_dict(s)), 201


# ----------------- catalog search (unassigned by default) -----------------
@bp.get("/api/courses")
def api_search_courses():
    user = get_current_user()
    q = (request.args.get("q") or "").strip()
    unassigned = request.args.get("unassigned", "1") != "0"

    base = CourseCatalog.query
    if q:
        like = f"%{q}%"
        base = base.filter(
            or_(CourseCatalog.code.ilike(like), CourseCatalog.title.ilike(like))
        )

    if unassigned:
        sub = (
            db.session.query(StudentCourse.course_id)
            .filter(StudentCourse.student_id == user.id)
        )
        base = base.filter(~CourseCatalog.id.in_(sub))

    items = base.order_by(CourseCatalog.code.asc()).limit(50).all()
    return jsonify(
        [{"id": c.id, "code": c.code, "title": c.title, "credits": c.credits} for c in items]
    )


# ----------------- add a course to a semester -----------------
@bp.post("/api/classes")
def api_add_class():
    """
    Body: { "course_id": <catalog id>, "semester_id": <student_semester id>, "section": "A1" }
    Enforces:
      - per-user course uniqueness
      - <= 8 classes per semester
      - <= 18 credits per semester
    """
    user = get_current_user()
    data = request.get_json(force=True) or {}
    course_id = data.get("course_id")
    semester_id = data.get("semester_id")
    section = data.get("section")

    if not course_id or not semester_id:
        abort(400, "course_id and semester_id required")

    sem = StudentSemester.query.filter_by(id=semester_id, student_id=user.id).first()
    if not sem:
        abort(404, "semester not found")

    exists = StudentCourse.query.filter_by(
        student_id=user.id, course_id=course_id
    ).first()
    if exists:
        abort(409, "course already planned for this student")

    if semester_count(semester_id) >= MAX_CLASSES_PER_SEM:
        abort(409, f"target semester is full ({MAX_CLASSES_PER_SEM})")

    cat = db.session.get(CourseCatalog, course_id)
    if not cat:
        abort(404, "course not found")

    cur = semester_credits(semester_id)
    if cur + float(cat.credits or 0) > MAX_CREDITS_PER_SEM:
        abort(409, f"credit limit {MAX_CREDITS_PER_SEM}) would be exceeded")

    maxpos = (
        db.session.query(func.coalesce(func.max(StudentCourse.position), -1))
        .filter(StudentCourse.semester_id == semester_id)
        .scalar()
    )
    sc = StudentCourse(
        student_id=user.id,
        semester_id=semester_id,
        course_id=course_id,
        credits=float(cat.credits or 0),
        section=section,
        position=int(maxpos) + 1,
    )
    db.session.add(sc)
    db.session.commit()
    return jsonify(sc_to_dict(sc)), 201


# ----------------- requirement-aware catalog for modal -----------------
@bp.get("/api/requirements")
def api_requirements():
    """
    Returns requirement groups with per-course availability.
    Adds planned-aware fields using current semester order:
      - prereq_ok_planned
      - unmet_prereqs_planned
    """
    user = get_current_user()
    program_code = request.args.get("program") or "BS-CS-Core-2025"
    q = (request.args.get("q") or "").strip().lower()
    current_term = (request.args.get("current_term") or "").strip().upper()
    current_order = request.args.get("current_order", type=int)

    prog = db.session.query(DegreeProgram).filter_by(code=program_code).first()
    if not prog:
        abort(404, "degree program not found")

    # student status
    sc_rows = db.session.query(StudentCourse).filter_by(student_id=user.id).all()
    completed_ids = {
        r.course_id
        for r in sc_rows
        if getattr(r, "status", None) == "COMPLETED" and _grade_ok(getattr(r, "grade", None), "C")
    }
    assigned_ids = {r.course_id for r in sc_rows}

    # planned-before set from semester.order
    planned_before_ids: set[int] = set()
    if current_order is not None:
        for r in sc_rows:
            sem = db.session.get(StudentSemester, r.semester_id)
            if sem and sem.order is not None and sem.order < current_order:
                planned_before_ids.add(r.course_id)

    # prereqs map
    prereq_rows = db.session.query(CoursePrereq).all()
    req_map: dict[int, dict[int, list[CoursePrereq]]] = defaultdict(lambda: defaultdict(list))
    for r in prereq_rows:
        req_map[r.course_id][r.group_key].append(r)

    # offerings map
    off_rows = db.session.query(CourseTypicalOffering).all()
    off_map: dict[int, set[str]] = defaultdict(set)
    for o in off_rows:
        off_map[o.course_id].add(o.term)

    # id->code
    cat_rows = db.session.query(CourseCatalog.id, CourseCatalog.code).all()
    id_to_code = {cid: code for cid, code in cat_rows}

    groups_out = []
    for g in prog.groups:
        # candidates
        if g.kind in ("ALL", "ANY_COUNT"):
            listed_ids = [rc.course_id for rc in g.courses]
            cats = (
                db.session.query(CourseCatalog)
                .filter(CourseCatalog.id.in_(listed_ids))
                .order_by(CourseCatalog.code.asc())
                .all()
            )
        else:
            cats = []
            for c in db.session.query(CourseCatalog).all():
                parts = (c.code or "").strip().upper().split()
                if len(parts) != 2:
                    continue
                dept, num_s = parts
                try:
                    num = int(num_s)
                except ValueError:
                    continue
                if g.dept_prefix and dept != g.dept_prefix:
                    continue
                if g.min_number is not None and num < g.min_number:
                    continue
                cats.append(c)
            cats.sort(key=lambda x: x.code)

        if q:
            cats = [c for c in cats if q in c.code.lower() or (c.title and q in c.title.lower())]

        items = []
        for c in cats:
            groups_for_course = req_map.get(c.id, {})

            # completed-only check
            missing_ids_completed: list[int] = []
            if not groups_for_course:
                prereq_ok_completed = True
            else:
                satisfied_any = False
                union_missing = []
                for _gkey, rules in groups_for_course.items():
                    all_ok = True
                    these_missing = []
                    for r in rules:
                        if r.prereq_course_id not in completed_ids:
                            all_ok = False
                            these_missing.append(r.prereq_course_id)
                    if all_ok:
                        satisfied_any = True
                        union_missing = []
                        break
                    else:
                        union_missing.extend(these_missing)
                prereq_ok_completed = satisfied_any
                missing_ids_completed = sorted(set(union_missing))

            # planned-aware check
            missing_ids_planned: list[int] = []
            if not groups_for_course:
                prereq_ok_planned = True
            else:
                satisfied_any = False
                union_missing = []
                for _gkey, rules in groups_for_course.items():
                    all_ok = True
                    these_missing = []
                    for r in rules:
                        if r.prereq_course_id not in completed_ids and r.prereq_course_id not in planned_before_ids:
                            all_ok = False
                            these_missing.append(r.prereq_course_id)
                    if all_ok:
                        satisfied_any = True
                        union_missing = []
                        break
                    else:
                        union_missing.extend(these_missing)
                prereq_ok_planned = satisfied_any
                missing_ids_planned = sorted(set(union_missing))

            offered_terms = sorted(list(off_map.get(c.id, set())))
            offered_this_term = current_term in off_map.get(c.id, set()) if current_term else False

            taken = c.id in completed_ids
            assigned = c.id in assigned_ids

            items.append(
                {
                    "id": c.id,
                    "code": c.code,
                    "title": c.title,
                    "credits": c.credits,
                    "taken": taken,
                    "assigned": assigned,
                    "offered_terms": offered_terms,
                    "offered_this_term": offered_this_term,
                    "prereq_ok": prereq_ok_completed,
                    "unmet_prereqs": [id_to_code.get(i, f"ID {i}") for i in missing_ids_completed],
                    "prereq_ok_planned": prereq_ok_planned,
                    "unmet_prereqs_planned": [id_to_code.get(i, f"ID {i}") for i in missing_ids_planned],
                    "disabled": taken or assigned or (not prereq_ok_planned),
                }
            )

        if g.kind == "ALL":
            required_count = len(items)
            completed_count = sum(1 for x in items if x["taken"])
        else:
            required_count = g.min_count or 0
            completed_count = min(sum(1 for x in items if x["taken"]), required_count)

        groups_out.append(
            {
                "group_id": g.id,
                "title": g.title,
                "kind": g.kind,
                "required_count": required_count,
                "completed_count": completed_count,
                "courses": items,
            }
        )

    return jsonify(
        {
            "program": {"code": prog.code, "name": prog.name},
            "groups": groups_out,
        }
    )
