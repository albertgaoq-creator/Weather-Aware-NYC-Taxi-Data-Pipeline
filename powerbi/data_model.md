# Power BI Data Model

## Recommended Relationships

- `dim_date_time[date_hour_key]` 1:* `fct_hourly_demand[date_hour_key]`
- `dim_date_time[date_key]` 1:* `fct_fare_revenue[date_key]`
- `dim_date_time[date_hour_key]` 1:* `fct_weather_impact[date_hour_key]`
- `dim_location[location_id]` 1:* `fct_hourly_demand[pickup_location_id]`
- `dim_location[location_id]` 1:* `fct_fare_revenue[pickup_location_id]`
- `dim_weather[weather_key]` 1:* `fct_hourly_demand[weather_key]`
- `dim_weather[weather_key]` 1:* `fct_weather_impact[weather_key]`

## Recommended Star Schema

### Dimensions

- `dim_date_time`
  - use `calendar_date`, `month_name`, `weekday_name`, `hour_of_day`, `is_weekend`
- `dim_location`
  - use `borough`, `zone`, `service_zone`
- `dim_weather`
  - use `weather_group`, `weather_severity`, `weathercode`

### Facts

- `fct_hourly_demand`
  - main source for volume trend visuals
- `fct_fare_revenue`
  - main source for revenue and average fare visuals
- `fct_weather_impact`
  - main source for weather comparison visuals

## Modeling Notes

- Use single-direction filter flow from dimensions to facts.
- Hide technical keys from the report view.
- Prefer aggregated facts over `fct_taxi_trips` in visuals to keep the PBIX responsive.
- Keep `dim_date_time` marked as a date table using `calendar_date`.
