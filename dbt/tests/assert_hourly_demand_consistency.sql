WITH detailed AS (
    SELECT COUNT(*) AS trip_count
    FROM {{ ref('fct_taxi_trips') }}
),
aggregated AS (
    SELECT COALESCE(SUM(trip_count), 0) AS trip_count
    FROM {{ ref('fct_hourly_demand') }}
)
SELECT
    detailed.trip_count AS detailed_trip_count,
    aggregated.trip_count AS aggregated_trip_count
FROM detailed
CROSS JOIN aggregated
WHERE detailed.trip_count <> aggregated.trip_count
