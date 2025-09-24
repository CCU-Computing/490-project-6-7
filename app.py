from __future__ import annotations
import os
from flask import Flask
from flask_migrate import Migrate
from models.models import db

def create_app() -> Flask:
    app = Flask(__name__)

    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(base_dir, 'planner.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    Migrate(app, db)

    from routes.routes import bp  # your Blueprint with routes
    app.register_blueprint(bp)

    # Build tables and seed on startup (safe if they already exist)
    with app.app_context():
        db.create_all()
        try:
            from seed_courses import seed as seed_courses
            seed_courses(db.session)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
