import os

from dotenv import load_dotenv

# The project root is one folder up from this file (backend/ -> project/).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    # Where MySQL is running.
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    # Which user, password and database to use.
    DB_USER = os.getenv("DB_USER", "um_app")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "urban_mobility")
    # Port the website runs on.
    APP_PORT = int(os.getenv("APP_PORT", "5001"))
    # The map-shapes file the API hands to the frontend.
    GEOJSON_PATH = os.path.join(BASE_DIR, "data", "processed",
                                "taxi_zones.geojson")