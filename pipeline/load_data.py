
import csv
import os
import time

import mysql.connector
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SCHEMA_SQL = os.path.join(BASE_DIR, "pipeline", "schema.sql")
ZONE_LOOKUP = os.path.join(BASE_DIR, "data", "taxi_zone_lookup.csv")
CLEAN_CSV = os.path.join(BASE_DIR, "data", "processed", "trips_clean.csv")

VENDORS = [
    (1, "Creative Mobile Technologies, LLC"),
    (2, "VeriFone Inc."),
    (4, "Unspecified (not in TLC dictionary)"),
]
RATE_CODES = [
    (1, "Standard rate"), (2, "JFK"), (3, "Newark"),
    (4, "Nassau or Westchester"), (5, "Negotiated fare"), (6, "Group ride"),
]
PAYMENT_TYPES = [
    (1, "Credit card"), (2, "Cash"), (3,"No charge"),
    (4, "Dispute"), (5, "Unknown"), (6, "Voided trip"),
]

INDEXES = [
    ("idx_trips_pickup_dt", "trips (pickup_datetime)"),
    ("idx_trips_pu_zone", "trips (pu_location_id)"),
    ("idx_trips_do_zone", "trips (do_location_id)"),
    ("idx_trips_payment", "trips (payment_type_id)"),
    ("idx_trips_day_hour", "trips (pickup_day, pickup_hour)"),
    ("idx_trips_distance", "trips (trip_distance)"),
    ("idx_trips_total", "trips (total_amount)")
]

