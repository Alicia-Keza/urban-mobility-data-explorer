CREATE DATABASE IF NOT EXISTS urban_mobility;
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE urban_mobility;

CREATE TABLE IF NOT EXISTS zones (
    zone_id SMALLINT UNSIGNED PRIMARY KEY,
    borough VARCHAR(32) NOT NULL,
    zone_name VARCHAR(64) NOT NULL,
    service_zone VARCHAR(32) NOT NULL,
    INDEX idx_zones_borough (borough)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TINYINT UNSIGNED PRIMARY KEY,
    vendor_name VARCHAR(64) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rate_codes (
    rate_code_id TINYINT UNSIGNED PRIMARY KEY,
    description VARCHAR(64) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payment_types (
    payment_type_id TINYINT UNSIGNED PRIMARY KEY,
    description VARCHAR(32) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS trips (
    trip_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    vendor_id TINYINT UNSIGNED NOT NULL,
    pickup_datetime DATETIME NOT NULL,
    dropoff_datetime DATETIME NOT NULL,
    passenger_count TINYINT UNSIGNED NOT NULL,
    trip_distance DECIMAL(7,2) NOT NULL,
    rate_code_id TINYINT UNSIGNED NOT NULL,
    store_and_fwd_flag CHAR(1) NOT NULL,
    pu_location_id SMALLINT UNSIGNED NOT NULL,
    do_location_id SMALLINT UNSIGNED NOT NULL,
    payment_type_id TINYINT UNSIGNED NOT NULL,
    fare_amount DECIMAL(8,2) NOT NULL,
    extra DECIMAL(7,2) NOT NULL,
    mta_tax DECIMAL(6,2) NOT NULL,
    tip_amount DECIMAL(7,2) NOT NULL,
    tolls_amount DECIMAL(7,2) NOT NULL,
    improvement_surcharge DECIMAL(6,2) NOT NULL,
    congestion_surcharge DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(9,2) NOT NULL,
    -- Derived features (computed in pipelines/clean_data.py)
    trip_duration_min  DECIMAL(7,2) NOT NULL, --dropoff - pickup 
    avg_speed_mph DECIMAL(6,2) NOT NULL, -- distance /duration 
    fare_per_mile DECIMAL(8,2) NOT NULL, -- fare / distance
    tip_pct DECIMAL(6,2) NOT NULL, -- tip / fare * 100
    pickup_day TINYINT UNSIGNED NOT NULL, -- day of month 1..31
    pickup_hour TINYINT UNSIGNED NOT NULL, -- 0..23
    day_of_week TINYINT UNSIGNED NOT NULL, -- 0=Mon ..6=Sun
    is_weekend TINYINT(1) NOT NULL,
    CONSTRAINT fk_trips_vendor FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id),
    CONSTRAINT fk_trips_rate FOREIGN KEY (rate_code_id) REFERENCES rate_codes (rate_code_id),
    CONSTRAINT fk_trips_pu_zone FOREIGN KEY (pu_location_id) REFERENCES zones (zone_id),
    CONSTRAINT fk_trips_do_zone FOREIGN KEY (do_location_id) REFERENCES zones (zone_id),
    CONSTRAINT fk_trips_payment FOREIGN KEY (payment_type_id) REFERENCES payment_types (payment_type_id)
) ENGINE=InnoDB;

