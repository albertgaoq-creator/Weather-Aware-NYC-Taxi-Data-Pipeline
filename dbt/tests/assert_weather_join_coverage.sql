WITH coverage AS (
    SELECT AVG(CASE WHEN weather_key <> 'unknown' THEN 1.0 ELSE 0.0 END) AS weather_join_coverage
    FROM {{ ref('fct_taxi_trips') }}
)
SELECT *
FROM coverage
WHERE weather_join_coverage < {{ env_var('MIN_WEATHER_JOIN_COVERAGE', '0.95') }}
