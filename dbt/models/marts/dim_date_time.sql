{{ config(materialized='table') }}

WITH hourly_points AS (
    SELECT pickup_hour AS hour_ts
    FROM {{ ref('stg_taxi_trips') }}
    UNION ALL
    SELECT weather_ts_hour AS hour_ts
    FROM {{ ref('stg_weather_hourly') }}
),
bounds AS (
    SELECT
        MIN(hour_ts) AS min_hour,
        MAX(hour_ts) AS max_hour
    FROM hourly_points
),
series AS (
    SELECT GENERATE_SERIES(min_hour, max_hour, INTERVAL '1 hour') AS hour_ts
    FROM bounds
)
SELECT
    TO_CHAR(hour_ts, 'YYYYMMDDHH24')::BIGINT AS date_hour_key,
    TO_CHAR(hour_ts::date, 'YYYYMMDD')::BIGINT AS date_key,
    hour_ts,
    hour_ts::date AS calendar_date,
    EXTRACT(YEAR FROM hour_ts) AS year_number,
    EXTRACT(MONTH FROM hour_ts) AS month_number,
    TO_CHAR(hour_ts, 'Month') AS month_name,
    EXTRACT(DAY FROM hour_ts) AS day_of_month,
    EXTRACT(HOUR FROM hour_ts) AS hour_of_day,
    EXTRACT(ISODOW FROM hour_ts) AS iso_weekday_number,
    TO_CHAR(hour_ts, 'Dy') AS weekday_name,
    CASE WHEN EXTRACT(ISODOW FROM hour_ts) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM series
