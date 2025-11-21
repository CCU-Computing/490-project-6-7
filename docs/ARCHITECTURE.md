# Architecture — Semester Planner (CSCI 490)

## 1) What the app does

This is a small web app where a student builds out future semesters. You can search the catalog, add classes to a semester, see if prerequisites are met, and watch progress bars for degree groups. We keep things simple: Flask on the back end, SQLite for data, and plain JavaScript + CSS on the front end.

```
Browser (JS + CSS)  ⇄  Flask routes  ⇄  SQLite file (planner.db)
```

## 2) How the code is organized

```
app.py                         # Starts Flask, sets up the DB, runs the seed script
seed_courses.py                # Loads demo data (safe to run more than once)
models/models.py               # Database tables (SQLAlchemy models)
routes/routes.py               # All API routes + the main page

static/css/planner.css         # Styles (cards, chips, modal, progress bars)
static/js/index.js             # Frontend entry
static/js/semesters/state_nav.js
static/js/semesters/render.js  # Timeline cards, navigation, delete wiring
static/js/class_modal/actions.js
static/js/class_modal/search.js
static/js/context_menu/menu.js
static/js/context_menu/toast.js

templates/planner.html         # Page layout + modal markup
```

## 3) The database (plain English)

* **User**: one row for the demo user.
* **StudentSemester**: each semester card you see in the UI. Fields include name (like “Fall 2025”), term, year, and an `order` number so we can sort them.
* **CourseCatalog**: every course in the catalog (code, title, credits, etc.).
* **StudentCourse**: a course placed into a specific semester for the current student. Also stores credits and the position inside the semester.
* **CoursePrereq**: which courses are required before (or alongside) another course. We support groups like “(A and B) **or** (C)”. There’s also a switch for “can take concurrently”.
* **CourseTypicalOffering**: which terms a course usually runs (Spring, Summer, Fall).
* **DegreeProgram / ReqGroup / ReqGroupCourse**: the requirement groups that drive the progress bars (e.g., “CSCI Core • Take all”).

**Notes we keep in mind**

* We avoid duplicate rows with a few uniqueness rules (for example, you can’t add the same course twice to the same semester).
* We keep semester order clean as `0,1,2...` with no gaps.

## 4) How the seed works

On first run, the app creates tables and loads demo data: the user, semesters, catalog, typical offerings, prereqs, and degree requirement groups. Running the seed again is fine—it won’t create duplicates. We temporarily park new semester orders in a “high range” and then renumber to keep the `0..N-1` order clean.

## 5) The API (in simple terms)

* `GET /` — serves the main page.
* `GET /api/semesters` — returns all semesters with their classes.
* `POST /api/semesters` — creates a new semester card.
* `POST /api/classes` — adds a catalog course to a semester (stops you from adding too many classes or credits).
* `DELETE /api/classes/<id>` — removes a class and keeps the list’s order tidy.
* `GET /api/courses?q=&unassigned=1` — searches the catalog, with an option to hide courses you already planned.
* `GET /api/requirements?...` — returns course lists for each requirement group with flags like “prereqs ok”, “already in plan”, and “offered this term”.
* `GET /api/requirements/progress?program=` — returns counts for the progress bars.

## 6) Frontend pieces (what each file does)

* **state_nav.js**: holds in‑page state (the list of semesters, the current index) and tiny helpers to call the API.
* **render.js**: draws the semester cards, the dots, and handles scrolling, arrows, touch, and delete.
* **search.js**: builds the course cards in the modal (title, credits, offering chips, prereq warnings) and handles expanding/collapsing groups.
* **actions.js**: loads requirement data, updates progress bars, and adds selected courses while respecting credit limits and duplicates.
* **menu.js** + **toast.js**: small context menu for actions and simple pop‑up messages.
* **planner.css**: all the look‑and‑feel (3→2→1 column grid, colors for planned/blocked, sticky group headers, two‑line titles, buttons).
* **planner.html**: the page shell with the header, viewport track, dots, and the modal structure.

## 7) How prerequisite checks work

* We treat the “current semester” as the anchor.
* Courses in **earlier** semesters count toward prereqs.
* Courses in the **same** semester only count if the rule says “can take concurrently”.
* Courses in **later** semesters never count.
* Some courses have multiple ways to qualify (e.g., “(A and B) or (C)”). If you meet any one path, the target course is allowed.

## 8) Rules we enforce

* Max **8 classes** per semester.
* Max **18 credits** per semester.
* You can’t add the same course twice for the same student or the same semester.
* Offering chips are just info; the prereq and “already planned” flags control whether a card is enabled.

## 9) Errors and messages

When something goes wrong (like going over 18 credits), the API returns a helpful code and message, and the UI shows a small toast explaining what happened.

## 10) A quick note on speed

We send course flags from the server (like “prereqs ok”) so the browser doesn’t have to do a bunch of heavy work. The modal reuses its grid container and only re‑orders cards to keep scrolling smooth. The seed script avoids slow lookups by caching codes in maps.

## 11) Accessibility and UX

* Keyboard navigation works on the timeline.
* Sticky headers keep you oriented in long lists.
* We use clear colors and short text to explain blocked vs planned states.

## 12) Future ideas

* Add an endpoint to **move** a class to a different semester.
* Write unit tests for prereq checks and progress counts.
* Let a student choose between multiple degree programs.
* Add pagination for very large catalogs.

## 13) How to run

1. Start the app (`flask run` or `python app.py`).
2. Visit the main page. The seed will create the demo data on first run.
3. Add and remove classes, open the modal, try the prereq cases, and watch the progress bars update.
