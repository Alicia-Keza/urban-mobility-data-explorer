import json
import os
import zipfile

import shapefile
from pyproj import Transformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONES_ZIP = os.path.join(BASE_DIR, "data", "taxi_zones.zip")
EXTRACT_DIR = os.path.join(BASE_DIR, "data", "taxi_zones_shp")
OUT_PATH = os.path.join(BASE_DIR, "data", "processed", "taxi_zones.geojson")

