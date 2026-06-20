import json
import os
import zipfile

import shapefile
from pyproj import Transformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONES_ZIP = os.path.join(BASE_DIR, "data", "taxi_zones.zip")
EXTRACT_DIR = os.path.join(BASE_DIR, "data", "taxi_zones_shp")
OUT_PATH = os.path.join(BASE_DIR, "data", "processed", "taxi_zones.geojson")

to_latlon = Transformer.from_crs("EPSG:2263", "EPSG:4326", always_xy=True)

def convert_ring(ring):
    points = []
    for x, y in ring:
        lon, lat = to_latlon.transform(x,y)
        points.append([round(lon, 6), round(lat,6)])
    return points

def main():
    os.makedirs(EXTRACT_DIR, exist_ok=True) 
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    with zipfile.ZipFile(ZONES_ZIP) as zf:
        zf.extractall(EXTRA_DIR)

    reader = shapefile.Reader(os.path.join(EXTRACT_DIR, "taxi_zones.shp"))
    field_names = [f[0] for f in reader.fields[1:]]

    features = []
    for shape_record in reader.shapeRecords():
        record = dict(zip(field_names, shape_record.record))
        shape = shape_record.shape.__geo_interface__       


