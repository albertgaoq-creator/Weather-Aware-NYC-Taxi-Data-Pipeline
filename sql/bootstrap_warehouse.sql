CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS raw.taxi_zone_lookup (
    location_id INTEGER PRIMARY KEY,
    borough TEXT NOT NULL,
    zone TEXT NOT NULL,
    service_zone TEXT,
    source_file TEXT NOT NULL,
    ingested_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.taxi_trips_yellow (
    record_hash TEXT PRIMARY KEY,
    vendor_id INTEGER,
    pickup_datetime TIMESTAMP,
    dropoff_datetime TIMESTAMP,
    passenger_count NUMERIC(10, 2),
    trip_distance NUMERIC(12, 3),
    rate_code_id INTEGER,
    store_and_fwd_flag TEXT,
    pickup_location_id INTEGER,
    dropoff_location_id INTEGER,
    payment_type INTEGER,
    fare_amount NUMERIC(12, 2),
    extra NUMERIC(12, 2),
    mta_tax NUMERIC(12, 2),
    tip_amount NUMERIC(12, 2),
    tolls_amount NUMERIC(12, 2),
    improvement_surcharge NUMERIC(12, 2),
    total_amount NUMERIC(12, 2),
    congestion_surcharge NUMERIC(12, 2),
    airport_fee NUMERIC(12, 2),
    cbd_congestion_fee NUMERIC(12, 2),
    pickup_hour TIMESTAMP,
    pickup_date DATE,
    ingestion_month DATE NOT NULL,
    source_file TEXT NOT NULL,
    ingested_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_taxi_trips_yellow_ingestion_month
    ON raw.taxi_trips_yellow (ingestion_month);

CREATE INDEX IF NOT EXISTS idx_raw_taxi_trips_yellow_pickup_hour
    ON raw.taxi_trips_yellow (pickup_hour);

CREATE INDEX IF NOT EXISTS idx_raw_taxi_trips_yellow_pickup_location_id
    ON raw.taxi_trips_yellow (pickup_location_id);

CREATE TABLE IF NOT EXISTS raw.weather_hourly (
    weather_record_id TEXT PRIMARY KEY,
    borough TEXT NOT NULL,
    weather_ts_hour TIMESTAMP NOT NULL,
    temperature_2m NUMERIC(8, 2),
    precipitation_mm NUMERIC(8, 2),
    rain_mm NUMERIC(8, 2),
    snowfall_cm NUMERIC(8, 2),
    wind_speed_10m NUMERIC(8, 2),
    weathercode INTEGER,
    source_month DATE NOT NULL,
    source_file TEXT NOT NULL,
    ingested_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_weather_hourly_source_month
    ON raw.weather_hourly (source_month);

CREATE INDEX IF NOT EXISTS idx_raw_weather_hourly_borough_hour
    ON raw.weather_hourly (borough, weather_ts_hour);
