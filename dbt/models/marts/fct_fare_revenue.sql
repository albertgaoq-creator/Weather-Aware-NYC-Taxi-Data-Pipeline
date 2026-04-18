{{ config(materialized='table') }}

SELECT
    MD5(
        date_key::TEXT
        || '|'
        || pickup_location_id::TEXT
        || '|'
        || payment_type_name
    ) AS fare_revenue_key,
    date_key,
    pickup_date,
    pickup_location_id,
    pickup_borough,
    pickup_zone,
    payment_type_name,
    COUNT(*) AS trip_count,
    SUM(fare_amount) AS gross_fare_amount,
    SUM(total_amount) AS total_revenue_amount,
    SUM(tip_amount) AS total_tip_amount,
    AVG(fare_amount) AS avg_fare_amount,
    AVG(total_amount) AS avg_total_amount,
    AVG(fare_per_mile) AS avg_fare_per_mile
FROM {{ ref('fct_taxi_trips') }}
GROUP BY
    date_key,
    pickup_date,
    pickup_location_id,
    pickup_borough,
    pickup_zone,
    payment_type_name
