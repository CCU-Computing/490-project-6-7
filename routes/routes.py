from __future__ import annotations
from flask import Blueprint, render_template, jsonify, request, abort
from sqlalchemy import func, or_, select
from models.models import (
    db, User, CourseCatalog, StudentSemester, StudentCourse
)

bp = Blueprint("routes", __name__)

MAX_CLASSES_PER_SEM = 8
MAX_CREDITS_PER_SEM = 18.0

# ----------------- helpers -----------------
def get_current_user() -> User:
    # allow ?user_id=, else demo user
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
        "id": sc.id,                           # association id for PATCH/DELETE
        "code": c.code,
        "title": c.title,
        "description": c.description,
        "credits": sc.credits,                 # snapshot used for credit math
        "department": c.department,
        "level": c.level,
        "section": sc.section,
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
    return (StudentSemester.query
            .filter_by(student_id=user_id)
            .order_by(StudentSemester.year.asc().nullsfirst(),
                      StudentSemester.id.asc())
            .all())

def semester_credits(semester_id: int, exclude_id: int | None = None) -> float:
    q = db.session.query(func.coalesce(func.sum(StudentCourse.credits), 0.0))\
                  .filter(StudentCourse.semester_id == semester_id)
    if exclude_id:
        q = q.filter(StudentCourse.id != exclude_id)
    return float(q.scalar() or 0.0)

def semester_count(semester_id: int) -> int:
    return int(db.session.query(func.count(StudentCourse.id))
               .filter(StudentCourse.semester_id == semester_id)
               .scalar() or 0)

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
    max_order = db.session.query(func.coalesce(func.max(StudentSemester.order), -1))\
                          .filter_by(student_id=user.id).scalar()
    s = StudentSemester(student_id=user.id, name=name, term=term, year=year, order=int(max_order) + 1)
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
        base = base.filter(or_(CourseCatalog.code.ilike(like),
                               CourseCatalog.title.ilike(like)))

    if unassigned:
        # filter out any course already chosen by this user
        sub = db.session.query(StudentCourse.course_id)\
                        .filter(StudentCourse.student_id == user.id)
        base = base.filter(~CourseCatalog.id.in_(sub))

    items = base.order_by(CourseCatalog.code.asc()).limit(50).all()
    return jsonify([{
        "id": c.id, "code": c.code, "title": c.title, "credits": c.credits
    } for c in items])

# ----------------- add a course to a semester -----------------
@bp.post("/api/classes")
def api_add_class():
    """
    Body: { "course_id": <catalog id>, "semester_id": <student_semester id>, "section": "A1" }
    Creates StudentCourse. Enforces:
      - course unique per user across semesters
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

    # unique per user
    exists = StudentCourse.query.filter_by(student_id=user.id, course_id=course_id).first()
    if exists:
        abort(409, "course already planned for this student")

    # max 8 classes
    if semester_count(semester_id) >= MAX_CLASSES_PER_SEM:
        abort(409, f"target semester is full ({MAX_CLASSES_PER_SEM})")

    cat = db.session.get(CourseCatalog, course_id)
    if not cat:
        abort(404, "course not found")

    # credit cap
    cur = semester_credits(semester_id)
    if cur + float(cat.credits or 0) > MAX_CREDITS_PER_SEM:
        abort(409, f"credit limit {MAX_CREDITS_PER_SEM} would be exceeded")

    maxpos = db.session.query(func.coalesce(func.max(StudentCourse.position), -1))\
                       .filter(StudentCourse.semester_id == semester_id).scalar()
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

# ----------------- move/update a planned course -----------------
@bp.patch("/api/classes/<int:sc_id>")
def api_move_or_update_class(sc_id: int):
    """
    Accepts fields: semester_id, section, position (optional).
    Moving enforces class-count and credit cap.
    """
    user = get_current_user()
    sc = StudentCourse.query.filter_by(id=sc_id, student_id=user.id).first_or_404()
    data = request.get_json(force=True) or {}

    # update section/position if provided
    if "section" in data:
        sc.section = data["section"]

    # handle move between semesters
    if "semester_id" in data and data["semester_id"] != sc.semester_id:
        target_sem_id = data["semester_id"]
        # check ownership
        sem = StudentSemester.query.filter_by(id=target_sem_id, student_id=user.id).first()
        if not sem:
            abort(404, "target semester not found")

        # class count
        if semester_count(target_sem_id) >= MAX_CLASSES_PER_SEM:
            abort(409, f"target semester is full ({MAX_CLASSES_PER_SEM})")

        # credit cap on target
        cur_target = semester_credits(target_sem_id)
        if cur_target + float(sc.credits) > MAX_CREDITS_PER_SEM:
            abort(409, f"credit limit {MAX_CREDITS_PER_SEM} would be exceeded")

        # assign new position at end
        maxpos = db.session.query(func.coalesce(func.max(StudentCourse.position), -1))\
                           .filter(StudentCourse.semester_id == target_sem_id).scalar()
        sc.semester_id = target_sem_id
        sc.position = int(maxpos) + 1

    db.session.commit()
    return jsonify(sc_to_dict(sc))

# ----------------- delete a planned course -----------------
@bp.delete("/api/classes/<int:sc_id>")
def api_delete_class(sc_id: int):
    user = get_current_user()
    sc = StudentCourse.query.filter_by(id=sc_id, student_id=user.id).first_or_404()
    db.session.delete(sc)
    db.session.commit()
    return "", 204
