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

RAW_COLUMNS = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "RatecodeID",
    "store_and_fwd_flag",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "improvement_surcharge",
    "total_amount", "congestion_surcharge"

]

OUT_COLUMNS = [
    "VendorID",
    "tpep_pickup_datetime",
    "dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "rate_code_id",
    "store_and_fwd_flag",
    "pu-location_id",
    "do-location_id",
    "payment_type_id",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "improvement_surcharge",
    "total_amount",
    "congestion_surcharge",
    "trip_duration_min",
    "avg_speed_mph", "fare_per_mile", "tip_pct",
    "pickup_day", "pickup_hour", "day_of_week", "is_weekend",

]

def load_known_zone_ids():
    zones = pd.read_csv(ZONE_LOOKUP)
    return set(zones["LocationID"].astype(int))
