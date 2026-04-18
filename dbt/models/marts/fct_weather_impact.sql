{{ config(materialized='table') }}

SELECT
    MD5(
        date_hour_key::TEXT
        || '|'
        || pickup_borough
        || '|'
        || weather_severity
    ) AS weather_impact_key,
    date_hour_key,
    date_key,
    pickup_hour,
    pickup_borough AS borough,
    weather_key,
    weather_severity,
    COUNT(*) AS trip_count,
    AVG(fare_amount) AS avg_fare_amount,
    AVG(total_amount) AS avg_total_amount,
    AVG(trip_duration_min) AS avg_trip_duration_min,
    AVG(trip_distance) AS avg_trip_distance,
    AVG(precipitation_mm) AS avg_precipitation_mm,
    AVG(temperature_2m) AS avg_temperature_2m,
    SUM(CASE WHEN is_rush_hour THEN 1 ELSE 0 END) AS rush_hour_trip_count
FROM {{ ref('fct_taxi_trips') }}
GROUP BY
    date_hour_key,
    date_key,
    pickup_hour,
    pickup_borough,
    weather_key,
    weather_severity
