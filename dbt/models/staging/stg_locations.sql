{{ config(materialized='view') }}

SELECT
    location_id,
    borough,
    zone,
    service_zone,
    CASE
        WHEN borough IN ('Bronx', 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island') THEN TRUE
        ELSE FALSE
    END AS is_nyc_borough
FROM {{ source('raw', 'taxi_zone_lookup') }}
