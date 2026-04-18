SELECT *
FROM {{ ref('fct_taxi_trips') }}
WHERE trip_duration_min <= 0
   OR trip_distance <= 0
   OR fare_amount < 0
   OR total_amount < 0
   OR passenger_count < 0
   OR passenger_count > 8
