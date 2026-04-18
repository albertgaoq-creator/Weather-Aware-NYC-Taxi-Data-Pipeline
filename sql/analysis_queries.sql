-- Hourly demand under different weather conditions
SELECT
    pickup_hour,
    pickup_borough,
    weather_severity,
    trip_count,
    avg_total_amount,
    avg_trip_duration_min
FROM mart.fct_weather_impact
ORDER BY pickup_hour, pickup_borough, weather_severity;

-- Top pickup zones by revenue
SELECT
    location.zone AS pickup_zone,
    revenue.trip_count,
    revenue.total_revenue_amount,
    revenue.avg_fare_amount
FROM mart.fct_fare_revenue AS revenue
JOIN mart.dim_location AS location
    ON revenue.pickup_location_id = location.location_id
ORDER BY revenue.total_revenue_amount DESC
LIMIT 20;

-- Rain vs clear trip volume comparison by borough
SELECT
    pickup_borough,
    weather_severity,
    SUM(trip_count) AS trip_count
FROM mart.fct_weather_impact
WHERE weather_severity IN ('clear', 'light', 'moderate', 'severe')
GROUP BY pickup_borough, weather_severity
ORDER BY pickup_borough, weather_severity;
