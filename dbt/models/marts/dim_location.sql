{{ config(materialized='table') }}

SELECT
    location_id,
    borough,
    zone,
    service_zone,
    is_nyc_borough
FROM {{ ref('stg_locations') }}
