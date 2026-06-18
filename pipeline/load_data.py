
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

def connect(database=None):
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=database,
        allow_local_infile=True,
    )

def run_schema(conn):
    with open(SCHEMA_SQL) as f:
        statements = [s.strip() for s in f.read().split(";") if s.strip()]
    cursor = conn.cursor()
    for statement in statements:
        cursor.execute(statement)
    conn.commit()
    cursor.close()

def load_lookups(conn):
    cursor = conn.cursor()

    # Read the zone names from the lookup CSV.
    with open(ZONE_LOOKUP, newline="") as f:
        rows = [(int(r["LocationID"]), r["Borough"], r["Zone"], r["service_zone"])
                for r in csv.DictReader(f)]

        cursor.executemany(
            "INSERT IGNORE INTO zones (zone_id, borough, zone_name, service_zone) " 
            "VALUES (%s, %s, %s, %s)", rows)
        cursor.executemany(
        "INSERT IGNORE INTO vendors (vendor_id, vendor_name) VALUES (%s, %s)", VENDORS
        )
        cursor.executemany(
            "INSERT IGNORE INTO rate_codes (rate_code_id, description) VALUES (%s, %s)", RATE_CODES
        )
        cursor.executemany(
            "INSERT IGNORE INTO payment_types (payment_type_id, description) VALUES (%s, %s)", PAYMENT_TYPES
        )
        conn.commit()
        cursor.close()
        print(f"Lookup tables loaded: {len(rows)} zones, {len(VENDORS)} vendors, "
              f"{len(RATE_CODES)} rate codes, {len(PAYMENT_TYPES)} payment types")
        

                         
