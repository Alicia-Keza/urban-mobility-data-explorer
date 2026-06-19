import json
import os
import sys
import time

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "yellow_tripdata_2019-01.csv")
ZONE_LOOKUP_DIR = os.path.join(BASE_DIR, "data", "taxi_zone_lookup.csv")
OUT_DIR = os.path.join(BASE_DIR, "data", "processed")
LOG_DIR = os.path.join(BASE_DIR, "logs")
CLEAN_OUT = os.path.join(OUT_DIR, "trips_clean.csv")
EXCLUDED_OUT = os.path.join(LOG_DIR, "excluded_records.csv")
SUMMARY_OUT = os.path.join(LOG_DIR, "pipeline_summary.json")

CHUNK_SIZE = 250_000

JAN_START = pd.Timestamp("2019-01-01 00:00:00")
FEB_START = pd.Timestamp("2019-02-01 00:00:00")

MAX_DISTANCE_MI = 100.0  # miles
MAX_DURATION_MIN = 480.0  # minutes
MAX_SPEED_MPH = 90.0
MAX_TOTAL_USD = 500.0
MAX_FARE_USD = 2.50

