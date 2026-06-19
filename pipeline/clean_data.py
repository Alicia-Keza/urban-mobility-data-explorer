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

def clean_chunk (df, known_zones):
    df = df.copy()

    df["tpep_pickup_datetime"]= pd.to_datetime(
        df["tpep_pickup_datetime"], errors="coerce")

    df["tpep_dropoff_datetime"] = pd.to_datetime(
        df["tpep_dropoff_datetime"], errors="coerce")
    df["store_and_fwd_flag"] =( df["store_and_fwd_flag"].astype(str).str.strip().str.upper())

    df["congestion_surcharge"] = df["congestion_surcharge"].fillna(0.0)

    duration_min = (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 60.0
    speed_mph = df["trip_distance"] / (duration / 60.0) 
    
    money_cols = [
        "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge", "total_amount", "congestion_surcharge"
    ]
    must_be-present = ["VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime", "passenger_count", "trip_distance", "RatecodeID", "PULocationID", "DOLocationID", "payment_type", "fare_amount", "total_amount"]     
 
    id_cols = ["VendorID", "tpep_pickup_datetime","tpep_dropoff_datetime", "PULocationID", "DOLocationID", "RatecodeID", "trip_distance","total_amount"]

    rules = [ 
        ("missing_important_value", df[must_be_present].isnull().any(axis=1)),
        ("duplicate_row", df.duplicated(subset=id_cols)),
        ("pickup_not_in_january",
            (df["tpep_pickup_datetime"] < JAN_START) | (df["tpep_pickup_datetime"] >= FEB_START)
        ),("dropoff_before_pickup", duration_min <=0),
        ("trip_too_long", duration_min > MAX_DURATION_MIN),
        ("distance_zero_or_less", df["trip_distance"] <= 0),
        ("distance-too-long", df["trip_distance"] > MAX_DISTANCE_MI),
        ("speed-too-high", speed_mph > MAX_SPEED_MPH)&(duration_min > 0),
        ("fare-below_minimum", df["fare_amount"] < MIN_FARE_USD),
        ("total_zero_or_less", df["total_amount"] <= 0),
        ("total-too-high", df["total_amount"] > MAX_TOTAL_USD),
        ("negative_money", (df[money_cols] < 0).any(axis=1)),
        ("bad_passenger_count", (df["passenger_count"] <= 0) | (df["passenger_count"] > 6)),
        ("unknown_pickup_zone", ~df["PULocationID"].isin(known_zones)),
        ("unknown_dropoff_zone", ~df["DOLocationID"].isin(known_zones)),
        ("bad_rate_code", ~df["RatecodeID"].isin([1, 2, 3, 4, 5, 6])),
        ("bad_payment_type", ~df["payment_type"].isin([1, 2, 3, 4, 5, 6])),
        ("bad_store_flag", ~df["store_and_fwd_flag"].isin(["Y", "N"])),
    ]