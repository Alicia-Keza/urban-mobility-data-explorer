import os

from flask import Flask
from flask_cors import CORS

from backend.config import Config
from backend.routes.api import api


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


def create_app():
    # Serve the frontend folder as static files at the website root.

    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    CORS(app)
    # All data endpoints live under /api (see backend/routes/api.py).
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/")
    def index():
        # The home page is the dashboard itself.
        return app.send_static_file("index.html")
    
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=Config.APP_PORT, debug=False)