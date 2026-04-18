{{ config(materialized='table') }}

SELECT
    MD5(
        date_hour_key::TEXT
        || '|'
        || pickup_location_id::TEXT
        || '|'
        || weather_key
    ) AS hourly_demand_key,
    date_hour_key,
    date_key,
    pickup_hour,
    pickup_location_id,
    pickup_borough,
    pickup_zone,
    weather_key,
    weather_severity,
    is_weekend,
    COUNT(*) AS trip_count,
    SUM(passenger_count) AS passenger_count_total,
    AVG(trip_distance) AS avg_trip_distance,
    AVG(trip_duration_min) AS avg_trip_duration_min,
    AVG(fare_amount) AS avg_fare_amount,
    AVG(total_amount) AS avg_total_amount
FROM {{ ref('fct_taxi_trips') }}
GROUP BY
    date_hour_key,
    date_key,
    pickup_hour,
    pickup_location_id,
    pickup_borough,
    pickup_zone,
    weather_key,
    weather_severity,
    is_weekend
