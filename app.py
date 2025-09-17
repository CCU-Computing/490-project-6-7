from __future__ import annotations
import os
from flask import Flask

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # Default config
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
    )

    # Optional instance config
    app.config.from_pyfile("config.py", silent=True)

    # Blueprints / routes
    from routes.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
