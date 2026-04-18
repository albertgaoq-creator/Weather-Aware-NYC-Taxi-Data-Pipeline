{{ config(materialized='view') }}

WITH source AS (
    SELECT *
    FROM {{ source('raw', 'weather_hourly') }}
),
deduplicated AS (
    SELECT *
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY borough, weather_ts_hour
                ORDER BY ingested_at DESC
            ) AS row_num
        FROM source
    ) ranked
    WHERE row_num = 1
),
cleaned AS (
    SELECT
        weather_record_id,
        borough,
        weather_ts_hour,
        temperature_2m,
        GREATEST(COALESCE(precipitation_mm, 0), 0) AS precipitation_mm,
        GREATEST(COALESCE(rain_mm, 0), 0) AS rain_mm,
        GREATEST(COALESCE(snowfall_cm, 0), 0) AS snowfall_cm,
        GREATEST(COALESCE(wind_speed_10m, 0), 0) AS wind_speed_10m,
        weathercode,
        CASE WHEN COALESCE(rain_mm, 0) > 0 THEN TRUE ELSE FALSE END AS is_rain,
        CASE WHEN COALESCE(snowfall_cm, 0) > 0 THEN TRUE ELSE FALSE END AS is_snow,
        CASE
            WHEN COALESCE(precipitation_mm, 0) >= 8 OR COALESCE(snowfall_cm, 0) >= 3 THEN 'severe'
            WHEN COALESCE(precipitation_mm, 0) >= 2 OR COALESCE(snowfall_cm, 0) >= 1 THEN 'moderate'
            WHEN COALESCE(precipitation_mm, 0) > 0 OR COALESCE(snowfall_cm, 0) > 0 THEN 'light'
            ELSE 'clear'
        END AS weather_severity,
        source_month,
        source_file,
        ingested_at
    FROM deduplicated
    WHERE weather_ts_hour IS NOT NULL
      AND temperature_2m BETWEEN -50 AND 60
      AND wind_speed_10m BETWEEN 0 AND 200
)
SELECT *
FROM cleaned
