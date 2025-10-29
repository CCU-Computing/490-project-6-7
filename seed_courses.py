from __future__ import annotations

from sqlalchemy import text, func

from models.models import (
    db,
    User,
    CourseCatalog,
    StudentSemester,
    CoursePrereq,
    CourseTypicalOffering,
    DegreeProgram,
    ReqGroup,
    ReqGroupCourse,
)

# -----------------------------
# Planner semesters
# -----------------------------
SEMESTERS = [
    ("Fall 2024",   "FALL",   2024),
    ("Spring 2025", "SPRING", 2025),
    ("Fall 2025",   "FALL",   2025),
    ("Spring 2026", "SPRING", 2026),
    ("Fall 2026",   "FALL",   2026),
    ("Spring 2027", "SPRING", 2027),
    ("Fall 2027",   "FALL",   2027),
    ("Spring 2028", "SPRING", 2028),
]

# -----------------------------
# Course catalog
# -----------------------------
COURSES = [
    # CSCI
    ("CSCI 120", "Introduction to Web Interface Development", 3),
    ("CSCI 135", "Introduction to Programming", 3),
    ("CSCI 145", "Intermediate Programming", 3),
    ("CSCI 210", "Computer Organization and Programming", 3),
    ("CSCI 220", "Data Structures", 3),
    ("CSCI 225", "Introduction to Relational Database and SQL", 3),
    ("CSCI 250", "Q* Information Management", 3),
    ("CSCI 270", "Data Communication Systems and Networks", 3),
    ("CSCI 303", "Introduction to Server-side Web Application Development", 3),
    ("CSCI 310", "Introduction to Computer Architecture", 3),
    ("CSCI 330", "Systems Analysis & Software Engineering", 3),
    ("CSCI 350", "Organization of Programming Languages", 3),
    ("CSCI 356", "Operating Systems", 3),
    ("CSCI 380", "Introduction to the Analysis of Algorithms", 3),
    ("CSCI 385", "Introduction to Information Systems Security", 3),
    ("CSCI 390", "Theory of Computation", 3),
    ("CSCI 401", "Ethics and Professional Issues in Computing", 3),
    ("CSCI 407", "Coding Theory", 3),
    ("CSCI 408", "Cryptography", 3),
    ("CSCI 425", "Database Systems Design", 3),
    ("CSCI 440", "Introduction to Computer Graphics", 3),
    ("CSCI 445", "Image Processing and Analysis", 3),
    ("CSCI 473", "Introduction to Parallel Systems", 3),
    ("CSCI 480", "Introduction to Artificial Intelligence", 3),
    ("CSCI 484", "Machine Learning", 3),
    ("CSCI 485", "Introduction to Robotics", 3),
    ("CSCI 490", "Software Engineering II", 3),
    ("CSCI 207", "Programming in C++", 3),
    ("CSCI 208", "Programming in Visual Basic", 3),
    ("CSCI 209", "Programming in Java", 3),

    # Math / Stat
    ("MATH 160",  "Calculus I", 4),
    ("MATH 160A", "Calculus I A", 2),
    ("MATH 160B", "Calculus I B", 2),
    ("MATH 161",  "Calculus II", 4),
    ("MATH 161A", "Calculus II A", 2),
    ("MATH 161B", "Calculus II B", 2),
    ("MATH 174",  "Introduction to Discrete Mathematics", 3),
    ("STAT 201",  "Elementary Statistics", 3),
    ("STAT 201L", "Elementary Statistics Computer Laboratory", 1),
    ("MATH 242",  "Modeling for Scientists I", 3),
    ("MATH 242L", "Modeling for Scientists I Laboratory", 1),
    ("MATH 220",  "Mathematical Proofs and Problem Solving", 3),
    ("MATH 260",  "Calculus III", 4),
    ("MATH 307",  "Combinatorics", 3),
    ("MATH 308",  "Graph Theory", 3),
    ("MATH 320",  "Elementary Differential Equations", 3),
    ("MATH 344",  "Linear Algebra", 3),
    ("MATH 407",  "Coding Theory", 3),
    ("MATH 408",  "Cryptography", 3),

    # Sciences + labs
    ("BIOL 121",  "Biological Science I", 3),
    ("BIOL 121L", "Biological Science I Laboratory", 1),
    ("BIOL 122",  "Biological Science II", 3),
    ("BIOL 122L", "Biological Science II Laboratory", 1),
    ("CHEM 111",  "General Chemistry I", 3),
    ("CHEM 111L", "General Chemistry I Laboratory", 1),
    ("CHEM 112",  "General Chemistry II", 3),
    ("CHEM 112L", "General Chemistry II Laboratory", 1),
    ("MSCI 111",  "Introduction to Marine Science", 3),
    ("MSCI 111L", "Introduction to Marine Science Laboratory", 1),
    ("MSCI 112",  "Introduction to Earth and Marine Geology", 3),
    ("MSCI 112L", "Introduction to Earth and Marine Geology Laboratory", 1),
    ("PHYS 137",  "Models in Physics", 3),
    ("PHYS 137L", "Models in Physics Laboratory", 1),
    ("PHYS 211",  "Essentials of Physics I", 3),
    ("PHYS 211L", "Essentials of Physics I Laboratory", 1),
    ("PHYS 212",  "Essentials of Physics II", 3),
    ("PHYS 212L", "Essentials of Physics II Laboratory", 1),
    ("PHYS 235",  "Electric Circuits", 3),

    # Communication
    ("COMM 140",  "Communication and Public Speaking", 3),
    ("ENGL 290",  "Introduction to Business Communication", 3),
    ("ENGL 390",  "Business and Professional Communication", 3),
]

# -----------------------------
# Typical offerings
# -----------------------------
TYPICAL_OFFERINGS = {
    # CSCI
    "CSCI 120": ["FALL", "SPRING", "SUMMER"],
    "CSCI 135": ["FALL", "SPRING"],
    "CSCI 145": ["FALL", "SPRING"],
    "CSCI 210": ["FALL"],
    "CSCI 220": ["FALL", "SPRING"],
    "CSCI 225": ["FALL", "SPRING"],
    "CSCI 250": ["FALL", "SPRING"],
    "CSCI 270": ["FALL", "SPRING"],
    "CSCI 303": ["SPRING"],
    "CSCI 310": ["SPRING"],
    "CSCI 330": ["FALL", "SPRING"],
    "CSCI 350": ["FALL"],
    "CSCI 356": ["FALL"],
    "CSCI 380": ["FALL"],
    "CSCI 385": ["FALL", "SPRING"],
    "CSCI 390": ["SPRING"],
    "CSCI 401": ["FALL", "SPRING"],
    "CSCI 407": ["SPRING"],
    "CSCI 408": ["FALL"],
    "CSCI 425": ["FALL"],
    "CSCI 440": ["FALL", "SPRING"],
    "CSCI 445": ["FALL", "SPRING"],
    "CSCI 473": ["FALL", "SPRING"],
    "CSCI 480": ["FALL", "SPRING"],
    "CSCI 484": ["FALL", "SPRING"],
    "CSCI 485": ["FALL", "SPRING"],
    "CSCI 490": ["FALL"],

    # Math / Stat
    "MATH 160":  ["FALL", "SPRING", "SUMMER"],
    "MATH 160A": ["FALL", "SPRING", "SUMMER"],
    "MATH 160B": ["FALL", "SPRING", "SUMMER"],
    "MATH 161":  ["FALL", "SPRING", "SUMMER"],
    "MATH 161A": ["FALL", "SPRING", "SUMMER"],
    "MATH 161B": ["FALL", "SPRING", "SUMMER"],
    "MATH 174":  ["FALL", "SPRING"],
    "STAT 201":  ["FALL", "SPRING", "SUMMER"],
    "STAT 201L": ["FALL", "SPRING", "SUMMER"],
    "MATH 242":  ["FALL", "SPRING"],
    "MATH 242L": ["FALL", "SPRING"],
    "MATH 220":  ["SPRING"],
    "MATH 260":  ["FALL", "SPRING"],
    "MATH 307":  ["SPRING"],
    "MATH 308":  ["FALL"],
    "MATH 320":  ["FALL", "SPRING"],
    "MATH 344":  ["FALL", "SPRING"],
    "MATH 407":  ["SPRING"],
    "MATH 408":  ["FALL"],

    # Sciences
    "BIOL 121":  ["FALL", "SPRING", "SUMMER"],
    "BIOL 121L": ["FALL", "SPRING", "SUMMER"],
    "BIOL 122":  ["FALL", "SPRING"],
    "BIOL 122L": ["FALL", "SPRING"],
    "CHEM 111":  ["FALL", "SPRING", "SUMMER"],
    "CHEM 111L": ["FALL", "SPRING", "SUMMER"],
    "CHEM 112":  ["FALL", "SPRING", "SUMMER"],
    "CHEM 112L": ["FALL", "SPRING", "SUMMER"],
    "MSCI 111":  ["FALL", "SPRING"],
    "MSCI 111L": ["FALL", "SPRING"],
    "MSCI 112":  ["FALL", "SPRING"],
    "MSCI 112L": ["FALL", "SPRING"],
    "PHYS 137":  ["FALL", "SPRING"],
    "PHYS 137L": ["FALL", "SPRING"],
    "PHYS 211":  ["FALL", "SPRING", "SUMMER"],
    "PHYS 211L": ["FALL", "SPRING", "SUMMER"],
    "PHYS 212":  ["FALL", "SPRING", "SUMMER"],
    "PHYS 212L": ["FALL", "SPRING", "SUMMER"],
    "PHYS 235":  ["FALL"],

    # Communication
    "COMM 140":  ["FALL", "SPRING"],
    "ENGL 290":  ["FALL", "SPRING", "SUMMER"],
    "ENGL 390":  ["FALL", "SPRING"],
}

# -----------------------------
# Prereqs: OR of AND groups
# -----------------------------
PREREQS = {
    # CSCI
    "CSCI 145": [["CSCI 135"]],
    "CSCI 210": [["CSCI 145"]],
    "CSCI 220": [["CSCI 145"]],
    "CSCI 330": [["CSCI 145"]],
    "CSCI 350": [["CSCI 220"]],
    "CSCI 356": [["CSCI 220"]],
    "CSCI 380": [["CSCI 220"]],
    "CSCI 385": [["CSCI 270"]],
    "CSCI 390": [["CSCI 220"]],
    "CSCI 407": [["MATH 344"]],
    "CSCI 408": [["MATH 220"], ["MATH 174"]],
    "CSCI 425": [["CSCI 225"]],
    "CSCI 440": [["CSCI 220"]],
    "CSCI 445": [["CSCI 145","MATH 160"]],
    "CSCI 473": [["CSCI 210","CSCI 270","CSCI 330","CSCI 356"]],
    "CSCI 480": [["CSCI 220"]],
    "CSCI 484": [["CSCI 220","MATH 160"]],
    "CSCI 485": [["CSCI 220"]],
    "CSCI 490": [["CSCI 330"]],

    # MATH / STAT
    "MATH 160":  [["MATH 131"], ["MATH 135"], ["Mathematics Placement"]],
    "MATH 160A": [["MATH 131"], ["MATH 135"], ["Mathematics Placement"]],
    "MATH 160B": [["MATH 160A"]],
    "MATH 161":  [["MATH 160"], ["MATH 160B"]],
    "MATH 161A": [["MATH 160"], ["MATH 160B"]],
    "MATH 161B": [["MATH 161A"]],
    "MATH 174":  [["MATH 130"], ["MATH 130B"], ["MATH 130I"], ["MATH 135"]],
    "STAT 201":  [["Any MATH except MATH 130A"]],
    "STAT 201L":[["STAT 201"]],
    "MATH 242":  [["MATH 160"], ["MATH 160B"]],
    "MATH 242L": [["MATH 242"]],
    "MATH 220":  [["MATH 160"], ["MATH 160B"]],
    "MATH 260":  [["MATH 161"], ["MATH 161B"]],
    "MATH 307":  [["MATH 220"], ["MATH 174"]],
    "MATH 308":  [["MATH 220"], ["MATH 174"]],
    "MATH 320":  [["MATH 161"], ["MATH 161B"]],
    "MATH 344":  [["MATH 161"], ["MATH 161B"], ["MATH 160","CSCI 220"]],

    # Sciences + labs
    "BIOL 121":  [["MATH 131 or above"], ["MATH 130"], ["MATH 130B"]],
    "BIOL 121L": [["BIOL 121"]],
    "BIOL 122":  [["BIOL 121","BIOL 121L"]],
    "BIOL 122L": [["BIOL 122"]],
    "CHEM 111":  [[]],
    "CHEM 111L": [["CHEM 111"]],
    "CHEM 112":  [["CHEM 111","CHEM 111L"]],
    "CHEM 112L": [["CHEM 112"]],
    "MSCI 111":  [["MATH 131 or above"], ["SAT 550+"], ["ACT 24+"]],
    "MSCI 111L": [["MSCI 111"]],
    "MSCI 112":  [["MATH 131 or above"], ["SAT 550+"], ["ACT 24+"]],
    "MSCI 112L": [["MSCI 112"]],
    "PHYS 137":  [[]],
    "PHYS 137L": [["PHYS 137"]],
    "PHYS 211":  [["MATH 160"], ["MATH 160B"]],
    "PHYS 211L": [["PHYS 211"]],
    "PHYS 212":  [["MATH 160","PHYS 211","PHYS 211L"]],
    "PHYS 212L": [["PHYS 212"]],
    "PHYS 235":  [["PHYS 137","MATH 160"], ["MATH 160B"], ["PHYS 212"]],
}

# -----------------------------
# Programs and groups
# -----------------------------
CORE_CODE  = "BS-CS-Core-2025"
CORE_NAME  = "Major Requirements (60 Credits)"

FOUND_CODE = "BS-CS-Foundations-2025"
FOUND_NAME = "Foundation Requirements (28-30 Credits) *"

CSCI_CORE_ALL = [
    "CSCI 120","CSCI 135","CSCI 145","CSCI 210","CSCI 220",
    "CSCI 250","CSCI 270","CSCI 330","CSCI 350","CSCI 356",
    "CSCI 380","CSCI 385","CSCI 390","CSCI 401","CSCI 473",
]
ADV_ELECTIVES_PICK_THREE = ["CSCI 310","CSCI 425","CSCI 440","CSCI 445","CSCI 480","CSCI 484","CSCI 485"]
SCI_LECTURE_LAB_PAIRS = [
    ("BIOL 121","BIOL 121L"),
    ("BIOL 122","BIOL 122L"),
    ("CHEM 111","CHEM 111L"),
    ("CHEM 112","CHEM 112L"),
    ("MSCI 111","MSCI 111L"),
    ("MSCI 112","MSCI 112L"),
    ("PHYS 137","PHYS 137L"),
    ("PHYS 211","PHYS 211L"),
    ("PHYS 212","PHYS 212L"),
]


def _get_catalog_map(session):
    rows = session.query(CourseCatalog).all()
    return {c.code.strip().upper(): c for c in rows}


def _purge_invalid_offerings(session):
    session.execute(text("DELETE FROM course_typical_offering WHERE term NOT IN ('SPRING','SUMMER','FALL')"))
    session.flush()


def _ensure_typical_offerings(session, catalog_by_code):
    for code, terms in TYPICAL_OFFERINGS.items():
        course = catalog_by_code.get(code.upper())
        if not course:
            continue
        existing = {to.term for to in session.query(CourseTypicalOffering).filter_by(course_id=course.id)}
        for term in terms:
            if term not in {"SPRING", "SUMMER", "FALL"}:
                continue
            if term not in existing:
                session.add(CourseTypicalOffering(course_id=course.id, term=term))


def _ensure_prereqs(session, catalog_by_code):
    """
    Upserts prereq rows. If a (course_id, prereq_course_id, group_key) already exists,
    update its fields; else insert. Default allow_concurrent=True.
    """
    for target_code, groups in PREREQS.items():
        target = catalog_by_code.get(target_code.upper())
        if not target:
            continue

        existing_rows = session.query(CoursePrereq).filter_by(course_id=target.id).all()
        existing = {(pr.prereq_course_id, pr.group_key): pr for pr in existing_rows}

        gk = 1
        for group in groups:
            ids = []
            ok = True
            for prereq_code in group:
                pc = catalog_by_code.get(prereq_code.upper())
                if not pc:
                    ok = False
                    break
                ids.append(pc.id)
            if not ok:
                gk += 1
                continue

            for pid in ids:
                key = (pid, gk)
                row = existing.get(key)
                if row:
                    row.min_grade = row.min_grade or "C"
                    row.allow_concurrent = True
                else:
                    session.add(
                        CoursePrereq(
                            course_id=target.id,
                            prereq_course_id=pid,
                            group_key=gk,
                            min_grade="C",
                            allow_concurrent=True,
                        )
                    )
            gk += 1
    session.flush()


def _ensure_program(session, code: str, name: str, total_credits: int):
    prog = session.query(DegreeProgram).filter_by(code=code).first()
    if not prog:
        prog = DegreeProgram(code=code, name=name, total_credits=total_credits)
        session.add(prog)
        session.flush()
    else:
        prog.name = name
        prog.total_credits = total_credits
        session.flush()
    return prog


def _ensure_req_group(
    session,
    program_id: int,
    title: str,
    kind: str,
    sort_order: int,
    min_count: int = 0,
    course_codes: list[str] | None = None,
    dept: str | None = None,
    min_number: int | None = None,
    allow_double: bool = False,
):
    g = session.query(ReqGroup).filter_by(program_id=program_id, title=title, kind=kind).first()
    if not g:
        g = ReqGroup(
            program_id=program_id,
            title=title,
            kind=kind,
            min_count=min_count,
            dept_prefix=dept,
            min_number=min_number,
            sort_order=sort_order,
            allow_double_count=allow_double,
        )
        session.add(g)
        session.flush()
    else:
        g.min_count = min_count
        g.dept_prefix = dept
        g.min_number = min_number
        g.sort_order = sort_order
        g.allow_double_count = allow_double
        session.flush()

    if course_codes:
        existing = {rc.course_id for rc in session.query(ReqGroupCourse).filter_by(group_id=g.id)}
        for code in course_codes:
            c = session.query(CourseCatalog).filter_by(code=code).first()
            if c and c.id not in existing:
                session.add(ReqGroupCourse(group_id=g.id, course_id=c.id, min_grade="C"))
    return g


def _seed_core(session, prog):
    order = 0
    _ensure_req_group(session, prog.id, "CSCI Core • Take all", "ALL", order, course_codes=CSCI_CORE_ALL); order += 1
    _ensure_req_group(
        session,
        prog.id,
        "CSCI Programming Language • Pick one",
        "ANY_COUNT",
        order,
        min_count=1,
        course_codes=["CSCI 207", "CSCI 208", "CSCI 209"],
    ); order += 1
    _ensure_req_group(
        session,
        prog.id,
        "Advanced CSCI Electives • Pick three",
        "ANY_COUNT",
        order,
        min_count=3,
        course_codes=ADV_ELECTIVES_PICK_THREE,
    ); order += 1
    _ensure_req_group(
        session, prog.id, "CSCI 200+ • Pick one", "FILTER", order, min_count=1, dept="CSCI", min_number=200
    ); order += 1


def _seed_foundations(session, prog):
    order = 0
    _ensure_req_group(session, prog.id, "Math Core • Calculus I • Pick one", "ANY_COUNT", order, min_count=1, course_codes=["MATH 160"]); order += 1
    _ensure_req_group(session, prog.id, "Math Core • Calculus I Split • Take all", "ALL", order, course_codes=["MATH 160A", "MATH 160B"]); order += 1
    _ensure_req_group(session, prog.id, "Math Core • Calculus II • Pick one", "ANY_COUNT", order, min_count=1, course_codes=["MATH 161"]); order += 1
    _ensure_req_group(session, prog.id, "Math Core • Calculus II Split • Take all", "ALL", order, course_codes=["MATH 161A", "MATH 161B"]); order += 1
    _ensure_req_group(session, prog.id, "Math Core • Discrete Mathematics • Take all", "ALL", order, course_codes=["MATH 174"]); order += 1
    _ensure_req_group(session, prog.id, "Math Core • Statistics + Lab • Take all", "ALL", order, course_codes=["STAT 201", "STAT 201L"]); order += 1

    _ensure_req_group(
        session,
        prog.id,
        "Math Path • Pick one",
        "ANY_COUNT",
        order,
        min_count=1,
        course_codes=["MATH 220", "MATH 260", "MATH 307", "MATH 308", "MATH 320", "MATH 344", "MATH 407", "MATH 408"],
    ); order += 1
    _ensure_req_group(session, prog.id, "Math Path • Modeling I + Lab • Take all", "ALL", order, course_codes=["MATH 242", "MATH 242L"]); order += 1

    # Science: one lecture required; matching lab required (UI merges)
    lec_codes = [lec for (lec, _lab) in SCI_LECTURE_LAB_PAIRS]
    _ensure_req_group(session, prog.id, "Science Core • Pick one lecture", "ANY_COUNT", order, min_count=1, course_codes=lec_codes); order += 1
    for (lec, lab) in SCI_LECTURE_LAB_PAIRS:
        _ensure_req_group(session, prog.id, f"Science Core • Lab for {lec} • Take all", "ALL", order, course_codes=[lab]); order += 1

    _ensure_req_group(session, prog.id, "Communication • Pick one", "ANY_COUNT", order, min_count=1, course_codes=["COMM 140", "ENGL 290", "ENGL 390"]); order += 1


def seed(session):
    # Ensure demo user
    user = session.query(User).filter_by(email="demo@example.com").first()
    if not user:
        user = User(email="demo@example.com", name="Demo User")
        session.add(user)
        session.flush()

    # --- Insert missing semesters with unique temporary orders (avoid NULL + UNIQUE collisions) ---
    max_order = session.query(func.max(StudentSemester.order)).filter_by(student_id=user.id).scalar()
    max_order = int(max_order) if max_order is not None else -1
    TEMP_OFFSET = 1000  # keep temp orders disjoint from final 0..N-1

    existing = {(s.term, s.year) for s in session.query(StudentSemester.term, StudentSemester.year).filter_by(student_id=user.id)}
    to_insert = []
    for name, term, year in SEMESTERS:
        if (term, year) not in existing:
            max_order += 1
            to_insert.append(
                StudentSemester(
                    student_id=user.id,
                    name=name,
                    term=term,
                    year=year,
                    order=max_order + TEMP_OFFSET,  # unique temp slot
                )
            )
    if to_insert:
        session.add_all(to_insert)
        session.flush()

    # --- Normalize per-student order to dense 0..N-1 using two-phase disjoint assignment ---
    rows = session.query(StudentSemester).filter(StudentSemester.student_id == user.id).all()

    def tweight(t: str | None) -> int:
        t = (t or "").upper()
        return 1 if t == "SPRING" else 2 if t == "SUMMER" else 3 if t == "FALL" else 0

    # Sort: prefer existing explicit order; else by (year, term, id)
    sortable = sorted(
        rows,
        key=lambda s: (0 if s.order is not None else 1, s.order or 0, int(s.year or 0), tweight(s.term), s.id),
    )

    # Phase A: move all orders into a far-away band to ensure no collisions when assigning 0..N-1
    for s in rows:
        s.order = (s.order or 0) + TEMP_OFFSET
    session.flush()

    # Phase B: assign canonical 0..N-1
    for idx, s in enumerate(sortable):
        s.order = idx
    session.flush()

    # --- Catalog (idempotent) ---
    existing_codes = {code for (code,) in session.query(CourseCatalog.code).all()}
    to_add = [CourseCatalog(code=code, title=title, credits=credits) for code, title, credits in COURSES if code not in existing_codes]
    if to_add:
        session.add_all(to_add)
        session.flush()

    catalog_by_code = _get_catalog_map(session)

    _purge_invalid_offerings(session)
    _ensure_typical_offerings(session, catalog_by_code)
    _ensure_prereqs(session, catalog_by_code)

    core = _ensure_program(session, CORE_CODE, CORE_NAME, 60)
    found = _ensure_program(session, FOUND_CODE, FOUND_NAME, 30)

    _seed_core(session, core)
    _seed_foundations(session, found)

    session.commit()
