# Setup — Semester Planner (CSCI 490)

This guide help new people set up the environment.

---

## Quick start (about 5 minutes)

1. **Install Python 3.10+** (3.11 recommended).
2. **Clone the repo** and move into it:

   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```
3. **Create a virtual environment**:

   ```bash
   python -m venv .venv
   ```
4. **Activate the virtual environment**:

   * macOS/Linux:

     ```bash
     source .venv/bin/activate
     ```
   * Windows (PowerShell):

     ```powershell
     .venv\Scripts\Activate.ps1
     ```
5. **Install packages**:

   * If the repo has `requirements.txt`:

     ```bash
     pip install -r requirements.txt
     ```
   * If not, install by name:

     ```bash
     pip install Flask Flask-SQLAlchemy Flask-Migrate
     ```
6. **Run the app**:

   ```bash
   python app.py
   ```
7. Open **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)** in your browser. You should see **Semester Planner**. Click **Add class** to open the modal.

> First run will create the database file `planner.db` and load demo data automatically.

---

## Full setup details

### Folder map you’ll touch most

```
app.py                          # starts Flask and seeds the database on boot
models/models.py                # database tables (SQLAlchemy)
routes/routes.py                # API routes + planner page
seed_courses.py                 # demo data (catalog, prereqs, groups)
static/css/planner.css          # styles
static/js/...                   # frontend JS modules
templates/planner.html          # page layout
```

### Running with the Flask CLI (optional)

If you prefer `flask run` instead of `python app.py`:

```bash
# macOS/Linux
export FLASK_APP=app.py
flask run

# Windows (PowerShell)
$env:FLASK_APP = "app.py"
flask run
```

Both ways do the same thing for this project.

---

## What the seed does (auto on first run)

* Creates a demo user and a few semesters (Fall/Spring, etc.).
* Loads the course catalog, typical offerings (Spring/Summer/Fall), and prerequisite rules.
* Sets up degree requirement groups that power the progress bars.
* Safe to run again — it won’t create duplicates.

Database file: **`planner.db`** (same folder as `app.py`).

---

## Common tasks

* **Restart the server**: stop it with Ctrl+C, then run `python app.py` again.
* **Reset the database** (fresh start):

  1. stop the server, 2) delete `planner.db`, 3) run `python app.py`.
* **See server logs**: they appear in your terminal; useful for errors.
* **Change the port** (Flask CLI): `flask run -p 5001`.

> Migrations (`flask db ...`) are set up but not required for the demo since we create tables on boot.

---

## Verify it works

1. Load the page at **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**.
2. Use the left/right arrows or scroll to switch semester cards.
3. Click **Add class**, search for a course (e.g., **CSCI 135**), and add it.
4. Try adding a course that needs a prereq; the card should be disabled with a short note.
5. Delete a class with the three‑dots menu and watch the list stay tidy.

---

## Troubleshooting

* **“Module not found” or imports failing**

  * Make sure the virtual environment is active (your shell prompt usually shows `(.venv)`).
* **“Port is already in use”**

  * Close other servers or run `flask run -p 5001`.
* **“Permission denied” / DB locked** (mostly on Windows)

  * Stop the server before deleting `planner.db`. Re‑run after deletion.
* **Blank page or 404s**

  * Check the terminal for errors. Confirm you’re on `http://127.0.0.1:5000/` and that `python app.py` is running.

---

## Next steps for new contributors

* Skim **ARCHITECTURE.md** to see how pieces fit together.
* Make a tiny change (like a small CSS tweak) and confirm the page live‑reloads (debug is on).
* If you add new tables, consider using Flask‑Migrate commands later to create a migration.
