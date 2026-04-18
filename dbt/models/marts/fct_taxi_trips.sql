{{ config(materialized='table') }}

WITH trips AS (
    SELECT *
    FROM {{ ref('stg_taxi_trips') }}
),
pickup_location AS (
    SELECT *
    FROM {{ ref('dim_location') }}
),
dropoff_location AS (
    SELECT *
    FROM {{ ref('dim_location') }}
),
weather AS (
    SELECT
        borough,
        weather_ts_hour,
        MD5(
            COALESCE(weathercode::TEXT, 'na')
            || '|'
            || weather_severity
            || '|'
            || is_rain::TEXT
            || '|'
            || is_snow::TEXT
        ) AS weather_key,
        temperature_2m,
        precipitation_mm,
        rain_mm,
        snowfall_cm,
        wind_speed_10m,
        weathercode,
        weather_severity,
        is_rain,
        is_snow
    FROM {{ ref('stg_weather_hourly') }}
)
SELECT
    trips.trip_id,
    TO_CHAR(trips.pickup_hour, 'YYYYMMDDHH24')::BIGINT AS date_hour_key,
    TO_CHAR(trips.pickup_date, 'YYYYMMDD')::BIGINT AS date_key,
    trips.pickup_ts_local,
    trips.dropoff_ts_local,
    trips.pickup_hour,
    trips.pickup_date,
    trips.pickup_location_id,
    trips.dropoff_location_id,
    pickup_location.borough AS pickup_borough,
    pickup_location.zone AS pickup_zone,
    dropoff_location.borough AS dropoff_borough,
    dropoff_location.zone AS dropoff_zone,
    trips.vendor_id,
    trips.passenger_count,
    trips.rate_code_id,
    trips.payment_type,
    trips.payment_type_name,
    trips.store_and_fwd_flag,
    trips.trip_distance,
    trips.trip_duration_min,
    trips.fare_amount,
    trips.extra,
    trips.mta_tax,
    trips.tip_amount,
    trips.tolls_amount,
    trips.improvement_surcharge,
    trips.total_amount,
    trips.congestion_surcharge,
    trips.airport_fee,
    trips.cbd_congestion_fee,
    trips.fare_per_mile,
    trips.weekday_number,
    trips.is_weekend,
    trips.is_rush_hour,
    COALESCE(weather.weather_key, 'unknown') AS weather_key,
    weather.temperature_2m,
    weather.precipitation_mm,
    weather.rain_mm,
    weather.snowfall_cm,
    weather.wind_speed_10m,
    weather.weathercode,
    COALESCE(weather.weather_severity, 'unknown') AS weather_severity,
    COALESCE(weather.is_rain, FALSE) AS is_rain,
    COALESCE(weather.is_snow, FALSE) AS is_snow,
    trips.ingestion_month,
    trips.source_file,
    trips.ingested_at
FROM trips
INNER JOIN pickup_location
    ON trips.pickup_location_id = pickup_location.location_id
INNER JOIN dropoff_location
    ON trips.dropoff_location_id = dropoff_location.location_id
LEFT JOIN weather
    ON trips.pickup_hour = weather.weather_ts_hour
   AND pickup_location.borough = weather.borough
