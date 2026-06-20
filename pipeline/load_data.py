
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
        
def load_trips(conn):
    cursor = conn.cursor()
    start_time = time.time()
    cursor.execute("SELECT COUNT(*) FROM trips")
    existing = cursor.fetchone()[0]
    if existing:
        print(f"trips already has {existing:,} rows, emptying it first")
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        cursor.execute("TRUNCATE TABLE trips")
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    print("Loading trips (this is the slow part)...")
    start = time.time()
    cursor.execute(f"""
        LOAD DATA LOCAL INFILE '{CLEAN_CSV}'
        INTO TABLE trips 
        FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\\n'
        (vendor_id, pickup_datetime, dropoff_datetime, passenger_count, 
        trip_distance, rate_code_id, store_and_fwd_flag, pu_location_id, 
        do_location_id, payment_type_id, fare_amount, extra, mta_tax,
        tip_amount, tolls_amount, improvement_surcharge,
        congestion_surcharge, total_amount, trip_duration_min,
        avg_speed_mph, fare_per_mile, tip_pct, pickup_day, pickup_hour,
        day_of_week, is_weekend)
    """)

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM trips")
    loaded = cursor.fetchone()[0]
    print(f"Loaded {loaded:,} trips in {time.time()  - start:.1f} s")

    with open(CLEAN_CSV) as f:
        csv_rows = sum(1 for _ in f) 
    if loaded != csv_rows:
        print(f"WARNING: csv has {csv_rows:,} rows but only {loaded:,} loaded"
              f" - check the lookup tables")    
    cursor.close()

def add_indexes(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT INDEX_NAME FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trips'
    """)

    existing = {row[0] for row in cursor.fetchall()}

    for name, definition in INDEXES:
        if name in existing:
            print(f"index {name} already exists, skipping")
            continue
        print(f"creating index {name}...")
        start = time.time()
        cursor.execute(f"CREATE INDEX {name} ON {definition}")
        print(f" done in {time.time() - start:.1f}s")

        cursor.execute("ANALYZE TABLE trips")
        cursor.fetchall()
        conn.commit()
        cursor.close()

def build_summary_table(conn):
    cursor = conn.cursor()
    print("Building the summary table (agg_zone_time)...")
    start = time.time()
    cursor.execute("""
      CREATE TABLE IF NOT EXISTS agg_zone_time (
          pickup_day TINYINT UNSIGNGED NOT NULL,
          pickup_hour TINYINT UNSIGNED NOT NULL, 
          is_weekend TINYINT(1)
          pu_location_id SMALLINT UNSIGNED NOT NULL,
          payment_type_id TINYINT UNSIGNED NOT NULL,
          trips_n INT UNSIGNED NOT NULL,
          sum_total DDECIMAL(14,2) NOT NULL,
          sum_fare DECIMAL(14,2) NOT NULL,
          sum_distance DECIMAL(12,2) NOT NULL, 
          sum_duration DECIMAL(12,2) NOT NULL, 
          sum_speed  DECIMAL(12,2) NOT NULL, 
          sum_tip_pct DECIMAL(12,2) NOT NULL,
          PRIMARY KEY (pickup_day, pickup_hour, pu_location_id, payment_type_id),
          INDEX idx_agg_zone (pu_location_id),
          INDEX idx_agg_payment (payment_type_id) ENGINE=InnoDB                                                                                                                                       ) 
                   
    """
    )

    cursor.execute("TRUNCATE TABLE agg_zone_time")
    cursor.execute("""
       INSERT INTO agg_zone_time
       SELECT pickup_day, pickup_hour, MAX(is_weekend), pu_location,
              payment_type_id, COUNT(*), SUM(fare_amount),
               SUM(trip_distance, SUM(trip_duration_min), SUM(avg_speed_mph),
                   SUM(tip_pct)
        FROM trips
        GROUPS BY pickup_day, pickup_hour, pu_location_id, payment_type_id                                        
    """)
    conn.commit()
    cursor.execute( "SELECT COUNT(*) FROM agg_zone_time")
    print(f" {cursor.fetchone()[0]:,} summary rows in {time.time() - start:.1f}s")
    cursor.close()

def main():
    conn = connect()
    run_schema(conn)
    conn.close()

    conn = connect(database=os.getenv("DB_NAME" , "uraban_mobility"))
    load_lookups(conn)
    load_trips(conn)
    add_indexes(conn)
    build_summary_table(conn)
    conn.close()
    print("Database load complete.")

if __name__ == "__main__":
    main()



    



    
    
                         
