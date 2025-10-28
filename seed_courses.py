from models.models import db, User, CourseCatalog, StudentSemester

SEMESTERS = [
    ("Fall 2024",   "Fall",   2024),
    ("Spring 2025", "Spring", 2025),
    ("Fall 2025",   "Fall",   2025),
    ("Spring 2026", "Spring", 2026),
    ("Fall 2026",   "Fall",   2026),
    ("Spring 2027", "Spring", 2027),
    ("Fall 2027",   "Fall",   2027),
    ("Spring 2028", "Spring", 2028),
]

COURSES = [
    ("CSCI 101", "Introduction to the Internet and World Wide Web", 3),
    ("CSCI 110", "Enterprise Business Applications", 3),
    ("CSCI 120", "Introduction to Web Interface Development", 3),
    ("CSCI 130", "Introduction to Computer Science", 3),
    ("CSCI 135", "Introduction to Programming", 3),
    ("CSCI 140", "Introduction to Algorithmic Design I", 3),
    ("CSCI 140L", "Introduction to Algorithmic Design I Laboratory", 1),
    ("CSCI 145", "Intermediate Programming", 3),
    ("CSCI 150", "Introduction to Algorithmic Design II", 3),
    ("CSCI 150L", "Introduction to Algorithmic Design II Laboratory", 1),
    ("CSCI 170", "Ethics in Computer Science", 1),
    ("CSCI 207", "Programming in C++", 3),
    ("CSCI 208", "Programming in Visual Basic", 3),
    ("CSCI 209", "Programming in Java", 3),
    ("CSCI 210", "Computer Organization and Programming", 3),
    ("CSCI 211", "Computer Infrastructure", 3),
    ("CSCI 216", "Linux Fundamentals I", 3),
    ("CSCI 220", "Data Structures", 3),
    ("CSCI 225", "Introduction to Relational Database and SQL", 3),
    ("CSCI 250", "Q* Information Management", 3),
    ("CSCI 270", "Data Communication Systems and Networks", 3),
    ("CSCI 280", "Strategies in Problem Solving", 1),
    ("CSCI 303", "Introduction to Server-side Web Application Development", 3),
    ("CSCI 310", "Introduction to Computer Architecture", 3),
    ("CSCI 311", "System Architecture", 3),
    ("CSCI 316", "Linux Fundamentals II", 3),
    ("CSCI 330", "Systems Analysis & Software Engineering", 3),
    ("CSCI 335", "Project Management", 3),
    ("CSCI 343", "Introduction to Mobile Application Development", 3),
    ("CSCI 350", "Organization of Programming Languages", 3),
    ("CSCI 356", "Operating Systems", 3),
    ("CSCI 375", "Introduction to Multimedia Applications", 3),
    ("CSCI 380", "Introduction to the Analysis of Algorithms", 3),
    ("CSCI 385", "Introduction to Information Systems Security", 3),
    ("CSCI 386", "Offensive Security", 3),
    ("CSCI 390", "Theory of Computation", 3),
    ("CSCI 399", "Independent Study", 1),
    ("CSCI 400", "Senior Assessment", 0),
    ("CSCI 401", "Ethics and Professional Issues in Computing", 3),
    ("CSCI 407", "Coding Theory", 3),
    ("CSCI 408", "Cryptography", 3),
    ("CSCI 409", "Advanced Web Application Development", 3),
    ("CSCI 415", "Windows System Administration", 3),
    ("CSCI 416", "Linux System Administration", 3),
    ("CSCI 425", "Database Systems Design", 3),
    ("CSCI 427", "Systems Integration", 3),
    ("CSCI 434", "Digital Forensics", 3),
    ("CSCI 435", "Anti-Forensics and Digital Privacy", 3),
    ("CSCI 440", "Introduction to Computer Graphics", 3),
    ("CSCI 444", "Human Computer Interaction", 3),
    ("CSCI 445", "Image Processing and Analysis", 3),
    ("CSCI 450", "Principles of Compiler Design", 3),
    ("CSCI 455", "Data Science and Analytics", 3),
    ("CSCI 466", "Informatics and Knowledge Discovery", 3),
    ("CSCI 473", "Introduction to Parallel Systems", 3),
    ("CSCI 475", "Decision Support Systems", 3),
    ("CSCI 480", "Introduction to Artificial Intelligence", 3),
    ("CSCI 484", "Machine Learning", 3),
    ("CSCI 485", "Introduction to Robotics", 3),
    ("CSCI 490", "Software Engineering II", 3),
    ("CSCI 495", "Information Systems Capstone Course and Project", 3),
    ("CSCI 497", "Computer Science Internship", 1),
    ("CSCI 498", "Cooperative Education", 1),
    ("CSCI 499", "Topics in Computer Science", 1),
]

def seed(session):
    """Idempotent seed for default user, semesters, and catalog."""
    # Default user
    user = session.query(User).filter_by(email="demo@example.com").first()
    if not user:
        user = User(email="demo@example.com", name="Demo User")
        session.add(user)
        session.flush()

    # Student semesters for that user
    existing = {(s.term, s.year) for s in session.query(StudentSemester.term, StudentSemester.year).filter_by(student_id=user.id)}
    order = 0
    for name, term, year in SEMESTERS:
        if (term, year) not in existing:
            session.add(StudentSemester(student_id=user.id, name=name, term=term, year=year, order=order))
        order += 1
    session.flush()

    # Catalog
    existing_codes = {code for (code,) in session.query(CourseCatalog.code).all()}
    to_add = [CourseCatalog(code=code, title=title, credits=credits)
              for code, title, credits in COURSES if code not in existing_codes]
    if to_add:
        session.add_all(to_add)
        session.commit()
