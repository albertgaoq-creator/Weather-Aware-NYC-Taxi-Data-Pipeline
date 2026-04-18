{{ config(materialized='view') }}

WITH source AS (
    SELECT *
    FROM {{ source('raw', 'taxi_trips_yellow') }}
),
base AS (
    SELECT
        record_hash AS trip_id,
        vendor_id,
        pickup_datetime,
        dropoff_datetime,
        COALESCE(passenger_count, 1) AS passenger_count,
        trip_distance,
        rate_code_id,
        store_and_fwd_flag,
        pickup_location_id,
        dropoff_location_id,
        payment_type,
        CASE payment_type
            WHEN 1 THEN 'Credit card'
            WHEN 2 THEN 'Cash'
            WHEN 3 THEN 'No charge'
            WHEN 4 THEN 'Dispute'
            WHEN 5 THEN 'Unknown'
            WHEN 6 THEN 'Voided trip'
            ELSE 'Unknown'
        END AS payment_type_name,
        COALESCE(fare_amount, 0) AS fare_amount,
        COALESCE(extra, 0) AS extra,
        COALESCE(mta_tax, 0) AS mta_tax,
        COALESCE(tip_amount, 0) AS tip_amount,
        COALESCE(tolls_amount, 0) AS tolls_amount,
        COALESCE(improvement_surcharge, 0) AS improvement_surcharge,
        COALESCE(total_amount, 0) AS total_amount,
        COALESCE(congestion_surcharge, 0) AS congestion_surcharge,
        COALESCE(airport_fee, 0) AS airport_fee,
        COALESCE(cbd_congestion_fee, 0) AS cbd_congestion_fee,
        ingestion_month,
        source_file,
        ingested_at
    FROM source
),
cleaned AS (
    SELECT
        trip_id,
        vendor_id,
        pickup_datetime AS pickup_ts_local,
        dropoff_datetime AS dropoff_ts_local,
        DATE_TRUNC('hour', pickup_datetime) AS pickup_hour,
        pickup_datetime::date AS pickup_date,
        passenger_count,
        trip_distance,
        rate_code_id,
        store_and_fwd_flag,
        pickup_location_id,
        dropoff_location_id,
        payment_type,
        payment_type_name,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        total_amount,
        congestion_surcharge,
        airport_fee,
        cbd_congestion_fee,
        EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime)) / 60.0 AS trip_duration_min,
        fare_amount / NULLIF(trip_distance, 0) AS fare_per_mile,
        EXTRACT(ISODOW FROM pickup_datetime) AS weekday_number,
        CASE WHEN EXTRACT(ISODOW FROM pickup_datetime) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend,
        CASE
            WHEN pickup_datetime::time >= TIME '07:00' AND pickup_datetime::time < TIME '10:00' THEN TRUE
            WHEN pickup_datetime::time >= TIME '16:00' AND pickup_datetime::time < TIME '20:00' THEN TRUE
            ELSE FALSE
        END AS is_rush_hour,
        ingestion_month,
        source_file,
        ingested_at
    FROM base
    WHERE pickup_datetime IS NOT NULL
      AND dropoff_datetime IS NOT NULL
      AND dropoff_datetime > pickup_datetime
      AND pickup_location_id IS NOT NULL
      AND dropoff_location_id IS NOT NULL
      AND trip_distance > 0
      AND trip_distance <= 200
      AND fare_amount >= 0
      AND total_amount >= 0
      AND passenger_count BETWEEN 0 AND 8
      AND fare_amount <= 1000
      AND total_amount <= 1500
)
SELECT *
FROM cleaned
