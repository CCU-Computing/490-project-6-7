# routes/routes.py
from __future__ import annotations

from typing import Any
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
    ReqGroup,
)

bp = Blueprint("routes", __name__)

MAX_CLASSES_PER_SEM = 8
MAX_CREDITS_PER_SEM = 18.0


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


def _term_weight(term: str | None) -> int:
    t = (term or "").upper()
    return 1 if t == "SPRING" else 2 if t == "SUMMER" else 3 if t == "FALL" else 0


def normalize_semester_orders(student_id: int) -> None:
    rows = (
        db.session.query(StudentSemester)
        .filter(StudentSemester.student_id == student_id)
        .all()
    )
    if not rows:
        return
    sortable = []
    for s in rows:
        if s.order is not None:
            sortable.append((0, int(s.order), 0, 0, s.id, s))
        else:
            sortable.append((1, 0, int(s.year or 0), _term_weight(s.term), s.id, s))
    sortable.sort()
    changed = False
    for new_order, (_, _, _, _, _sid, s) in enumerate(sortable):
        if s.order != new_order:
            s.order = new_order
            changed = True
    if changed:
        db.session.commit()


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
        "order": s.order,
        "classes": [sc_to_dict(sc) for sc in s.courses],
    }


def semester_load_for_user(user_id: int):
    normalize_semester_orders(user_id)
    return (
        StudentSemester.query.filter_by(student_id=user_id)
        .order_by(StudentSemester.order.asc(), StudentSemester.id.asc())
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


# kept for other views; not used in prereq gating anymore
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


@bp.route("/")
def planner():
    return render_template("planner.html")


@bp.get("/api/semesters")
def api_list_semesters():
    user = get_current_user()
    items = semester_load_for_user(user.id)
    return jsonify([sem_to_dict(s) for s in items])


@bp.post("/api/semesters")
def api_create_semester():
    user = get_current_user()
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").trim()
    term = (data.get("term") or "").strip() or None
    year = data.get("year")
    if not name:
        abort(400, "name required")

    normalize_semester_orders(user.id)
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


@bp.post("/api/classes")
def api_add_class():
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
        abort(409, f"credit limit {MAX_CREDITS_PER_SEM} would be exceeded")

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


@bp.delete("/api/classes/<int:sc_id>")
def api_delete_class(sc_id: int):
    user = get_current_user()
    sc = (
        db.session.query(StudentCourse)
        .filter_by(id=sc_id, student_id=user.id)
        .first()
    )
    if not sc:
        abort(404, "class not found")

    sem_id = sc.semester_id
    db.session.delete(sc)
    db.session.flush()

    rows = (
        db.session.query(StudentCourse)
        .filter_by(semester_id=sem_id, student_id=user.id)
        .order_by(StudentCourse.position.asc(), StudentCourse.id.asc())
        .all()
    )
    for i, row in enumerate(rows):
        row.position = i

    db.session.commit()
    return ("", 204)


@bp.get("/api/requirements")
def api_requirements():
    """
    Prereq policy used for gating:
      - Earlier terms (< anchor): any status {PLANNED, IN_PROGRESS, COMPLETED} counts.
      - Same term (== anchor): counts only if allow_concurrent=True.
      - Later terms (> anchor): does not count.
      - Grade is ignored entirely.
    """
    user = get_current_user()
    program_code = request.args.get("program") or "BS-CS-Core-2025"
    q = (request.args.get("q") or "").strip().lower()
    current_term = (request.args.get("current_term") or "").strip().upper()

    normalize_semester_orders(user.id)

    current_sem_id = request.args.get("current_semester_id", type=int)
    current_order = request.args.get("current_order", type=int)

    prog = db.session.query(DegreeProgram).filter_by(code=program_code).first()
    if not prog:
        abort(404, "degree program not found")

    sc_rows = db.session.query(StudentCourse).filter_by(student_id=user.id).all()

    user_sems = semester_load_for_user(user.id)
    ranks_by_id: dict[int, int] = {s.id: int(s.order) for s in user_sems}
    if current_sem_id and current_sem_id in ranks_by_id:
        anchor_rank = ranks_by_id[current_sem_id]
    elif current_order is not None:
        anchor_rank = int(current_order)
    else:
        anchor_rank = 10**9

    course_state: dict[int, dict[str, Any]] = {}
    for r in sc_rows:
        rk = ranks_by_id.get(r.semester_id)
        status_val = getattr(r, "status", None) or "PLANNED"
        grade_val = getattr(r, "grade", None)
        course_state[r.course_id] = {
            "status": status_val,
            "grade": grade_val,
            "order": rk,
        }

    off_rows = db.session.query(CourseTypicalOffering).all()
    off_map: dict[int, set[str]] = {}
    for o in off_rows:
        off_map.setdefault(o.course_id, set()).add(o.term)

    prereq_rows = db.session.query(CoursePrereq).all()
    req_map: dict[int, dict[int, list[CoursePrereq]]] = {}
    for r in prereq_rows:
        req_map.setdefault(r.course_id, {}).setdefault(r.group_key, []).append(r)

    cat_rows = db.session.query(CourseCatalog.id, CourseCatalog.code, CourseCatalog.title, CourseCatalog.credits).all()
    id_to_code = {cid: code for cid, code, _, _ in cat_rows}
    catalog_by_id = {cid: (code, title, credits) for cid, code, title, credits in cat_rows}

    def prereq_rule_satisfied(rule: CoursePrereq) -> bool:
        st = course_state.get(rule.prereq_course_id)
        if not st:
            return False
        ord_ = st.get("order")
        if ord_ is None:
            return False
        status = st.get("status") or "PLANNED"
        if ord_ < anchor_rank:
            return status in {"PLANNED", "IN_PROGRESS", "COMPLETED"}
        if ord_ == anchor_rank:
            return bool(rule.allow_concurrent) and status in {"PLANNED", "IN_PROGRESS", "COMPLETED"}
        return False

    def prereq_eval_for_course(course_id: int) -> tuple[bool, list[int], bool, list[int]]:
        groups = req_map.get(course_id, {})
        if not groups:
            return True, [], True, []
        satisfied = False
        missing: list[int] = []
        for _gk, rules in groups.items():
            if all(prereq_rule_satisfied(r) for r in rules):
                satisfied = True
                missing = []
                break
            else:
                for r in rules:
                    if not prereq_rule_satisfied(r):
                        missing.append(r.prereq_course_id)
        missing = sorted(set(missing))
        return satisfied, missing, satisfied, missing

    groups_out = []
    for g in prog.groups:
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
            ql = q.lower()
            cats = [c for c in cats if ql in c.code.lower() or (c.title and ql in c.title.lower())]

        items = []
        for c in cats:
            ok_completed, missing_completed, ok_planned, missing_planned = prereq_eval_for_course(c.id)

            offered_terms_set = off_map.get(c.id, set())
            offered_terms = sorted(list(offered_terms_set))
            taken = (course_state.get(c.id, {}).get("status") == "COMPLETED")
            assigned = c.id in course_state
            offered_this_term = bool(current_term and offered_terms_set and current_term in offered_terms_set)

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
                    "prereq_ok": ok_planned,
                    "unmet_prereqs": [id_to_code.get(i, f"ID {i}") for i in missing_planned],
                    "prereq_ok_planned": ok_planned,
                    "unmet_prereqs_planned": [id_to_code.get(i, f"ID {i}") for i in missing_planned],
                    "prereq_groups": [
                        [id_to_code.get(r.prereq_course_id, f"ID {r.prereq_course_id}") for r in sorted(rules, key=lambda x: x.prereq_course_id)]
                        for _gk, rules in sorted(req_map.get(c.id, {}).items(), key=lambda x: x[0])
                    ],
                    "prereq_complexity": min(
                        (len(group_rules) for group_rules in req_map.get(c.id, {}).values()),
                        default=0
                    ),
                    "disabled": taken or assigned or (not ok_planned),
                }
            )

        def sort_key(it):
            has_pr = (it.get("prereq_complexity") or 0) > 0
            tier = 2 if has_pr else 0
            return (tier, it.get("prereq_complexity") or 0, it.get("code") or "")

        items.sort(key=sort_key)

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

    return jsonify({"program": {"code": prog.code, "name": prog.name}, "groups": groups_out})


@bp.get("/api/requirements/progress")
def api_requirements_progress():
    """
    Return planned_count and required_count per group for a program,
    computed from current StudentCourse rows.
    """
    user = get_current_user()
    program_code = request.args.get("program")
    if not program_code:
        abort(400, "program required")

    prog = db.session.query(DegreeProgram).filter_by(code=program_code).first()
    if not prog:
        abort(404, "degree program not found")

    planned_ids = {
        cid for (cid,) in db.session.query(StudentCourse.course_id)
        .filter(StudentCourse.student_id == user.id)
        .all()
    }
    catalog = {c.id: c for c in db.session.query(CourseCatalog).all()}

    def code_ok_for_filter(course_id: int, g: ReqGroup) -> bool:
        c = catalog.get(course_id)
        if not c or not c.code:
            return False
        parts = c.code.strip().upper().split()
        if len(parts) != 2:
            return False
        dept, num_s = parts
        try:
            num = int(num_s)
        except ValueError:
            return False
        if g.dept_prefix and dept != g.dept_prefix:
            return False
        if g.min_number is not None and num < g.min_number:
            return False
        return True

    groups_out = []
    for g in prog.groups:
        if g.kind in ("ALL", "ANY_COUNT"):
            listed = [rc.course_id for rc in g.courses]
            planned = sum(1 for cid in listed if cid in planned_ids)
            required = len(listed) if g.kind == "ALL" else int(g.min_count or 0)
            if g.kind == "ANY_COUNT":
                planned = min(planned, required)
        else:  # FILTER
            eligible = [cid for cid in planned_ids if code_ok_for_filter(cid, g)]
            required = int(g.min_count or 0)
            planned = min(len(eligible), required)

        groups_out.append({
            "group_id": g.id,
            "title": g.title,
            "required_count": required,
            "planned_count": planned,
        })

    return jsonify({"program": {"code": prog.code}, "groups": groups_out})
