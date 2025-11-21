# Backlog — Semester Planner (CSCI 490)

Below is a short, practical backlog based on the current code. It includes **potential user stories** and **bug fixes / cleanups**

---

## User stories

1. **Move a class to another semester**
   As a student, I want to move a planned class to a different semester so that my plan stays organized when things change.
   *Notes:* Add a `PATCH /api/classes/<id>` route, wire it to the context menu.
   *Files:* `routes/routes.py`, `static/js/semesters/state_nav.js`, `static/js/semesters/render.js`, `static/js/context_menu/menu.js`.

2. **Reorder semesters**
   As a student, I want to reorder my semester cards so that they match my real timeline.
   *Notes:* Add simple arrows or drag-and-drop to change `StudentSemester.order`.
   *Files:* `routes/routes.py` (new endpoint), `static/js/semesters/render.js`.

3. **Create a new semester from the UI**
   As a student, I want a button to add a new semester card so that I can extend my plan.
   *Notes:* Call `POST /api/semesters`; small modal with name/term/year.
   *Files:* `static/js/semesters/render.js`, `templates/planner.html`.

4. **Stronger prereq guidance**
   As a student, I want to see exactly which courses unlock a blocked class so that I know what to add next.
   *Notes:* In the modal card, make unmet prereqs clickable to filter the list to those courses.
   *Files:* `static/js/class_modal/search.js`, `static/js/class_modal/actions.js`.

5. **Credit cap warning before submit**
   As a student, I want a gentle warning when I’m near or over 18 credits so that I don’t get surprised.
   *Notes:* Use current total + selected courses to show a banner before POST.
   *Files:* `static/js/class_modal/actions.js`.

6. **Filter catalog by term**
   As a student, I want to filter by “offered in Fall/Spring/Summer” so that I only see relevant options.
   *Notes:* Client-side filter from `offered_terms`; keep server as-is.
   *Files:* `static/js/class_modal/search.js`.

7. **Notes on a class**
   As a student, I want to add a short note to a planned class so that I remember details (section or time).
   *Notes:* Add a `note` field to `StudentCourse`; small edit popover.
   *Files:* `models/models.py`, `routes/routes.py`, `static/js/semesters/render.js`.

8. **Export my plan**
   As a student, I want to export my plan to a simple file so that I can share it.
   *Notes:* Start with JSON; later a PDF.
   *Files:* new route in `routes/routes.py`.

9. **Show success toasts**
   As a student, I want a small success toast when I add or move a class so that I know it worked.
   *Notes:* We already have `toast.js`; add success path (green).
   *Files:* `static/js/context_menu/toast.js`, call sites.

10. **Program picker**
    As a student, I want to pick a degree program so that requirements and progress match my track.
    *Notes:* Keep data model (it exists), add a simple dropdown.
    *Files:* `routes/routes.py` (query param), `templates/planner.html`, `static/js/class_modal/actions.js`.

11. **Simple onboarding**
    As a new user, I want a short walkthrough so that I understand how to build my first plan.
    *Notes:* 3-step overlay with arrows.
    *Files:* small new JS module + light CSS.

12. **Delete confirmation**
    As a student, I want a quick confirm when deleting a class so that I don’t remove by mistake.
    *Files:* `static/js/semesters/render.js`.

---

## Bug fixes

1. **String trim in Python**
   `routes/routes.py` → `api_create_semester`: use `.strip()` instead of `.trim()`.

2. **Implement move endpoint to match the UI**
   Front end calls `PATCH /api/classes/<id>` in `state_nav.js`, but the route doesn’t exist. Add a `PATCH` handler to move a `StudentCourse` between semesters and reindex positions.

3. **Context menu “Move…” mismatch**
   `static/js/semesters/render.js` builds a **Move…** item, but `static/js/context_menu/menu.js` drops items with `icon: "move"`. Either implement Move or remove the item from the caller so menus match what’s possible.

4. **Credits in add‑modal fallback to 0**
   `static/js/class_modal/actions.js` → `fetchCourseLocalOrServerByCatalogId` returns `{credits: 0}` if the chip isn’t found, which can under‑block on the client. Fix by adding a tiny endpoint (e.g., `GET /api/catalog/<id>`) or including `credits` as a data‑attribute on each card so the client always knows the value.

5. **Duplicate prereq flags**
   `routes/routes.py` → `/api/requirements` returns both `prereq_ok` and `prereq_ok_planned` with the same meaning. Keep one to simplify the client.

6. **Term validation**
   `models/models.py` / `routes/routes.py`: `StudentSemester.term` is a free string. Consider a small enum check (`SPRING/SUMMER/FALL`) so data stays clean.

7. **Magic numbers for limits**
   `max 8 classes` and `18 credits` live in both client and server. Provide them from the server (e.g., `/api/config`) so the UI and API never drift.

8. **Search pagination**
    `/api/courses` caps at 50. If the catalog grows, add `page/limit`.

---
