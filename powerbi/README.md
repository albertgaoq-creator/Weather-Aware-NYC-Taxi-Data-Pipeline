# Power BI Build Guide

Use PostgreSQL as the Power BI source and connect to the `mart` schema. The marts are already shaped for dashboarding, so the main Power BI work is relationship setup, measures, and page design.

Read these files in order:

1. `powerbi/data_model.md`
2. `powerbi/measures.md`
3. `powerbi/dashboard_spec.md`

Recommended tables for import:

- `mart.dim_date_time`
- `mart.dim_location`
- `mart.dim_weather`
- `mart.fct_hourly_demand`
- `mart.fct_fare_revenue`
- `mart.fct_weather_impact`

Optional direct-query detail table:

- `mart.fct_taxi_trips`

If the dataset becomes large for desktop import, keep the three aggregated fact tables imported and use `fct_taxi_trips` only for drillthrough or refresh validation.
