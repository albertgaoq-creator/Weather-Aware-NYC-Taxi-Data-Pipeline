{{ config(materialized='table') }}

WITH distinct_weather AS (
    SELECT DISTINCT
        MD5(
            COALESCE(weathercode::TEXT, 'na')
            || '|'
            || weather_severity
            || '|'
            || is_rain::TEXT
            || '|'
            || is_snow::TEXT
        ) AS weather_key,
        weathercode,
        weather_severity,
        is_rain,
        is_snow,
        CASE
            WHEN is_rain AND is_snow THEN 'mixed'
            WHEN is_snow THEN 'snow'
            WHEN is_rain THEN 'rain'
            WHEN weather_severity = 'clear' THEN 'clear'
            ELSE 'other'
        END AS weather_group
    FROM {{ ref('stg_weather_hourly') }}
)
SELECT
    'unknown' AS weather_key,
    NULL::INTEGER AS weathercode,
    'unknown' AS weather_severity,
    FALSE AS is_rain,
    FALSE AS is_snow,
    'unknown' AS weather_group
UNION ALL
SELECT
    weather_key,
    weathercode,
    weather_severity,
    is_rain,
    is_snow,
    weather_group
FROM distinct_weather
